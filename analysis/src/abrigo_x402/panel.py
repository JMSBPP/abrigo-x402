"""End-to-end panel-build orchestrator (RESEARCH §H Pattern 1).

Pipeline order — CRITICAL (finality_cutoff FIRST after load, per Pitfall 5):
  load_jsonl
  → apply_finality_cutoff       (FIRST after load — Pitfall 5; drop volatile head)
  → decode_all                  (typed payload columns from topics + data)
  → exclude_adapters            (PANEL-04 phantom-filter Transfer rows)
  → attach_in_range             (vault state left-join + vault_in_range flag)
  → compute_swap_fee            (Q96 LP-fee — Swap-rows-only branch; see split rationale)
  → attach_rates                (Mento FX snap + USDT/USD column)
  → with_header                 (PANEL-02 Parquet metadata)

Split-and-rejoin rationale (Swap-only branch through compute_swap_fee):
  compute_swap_fee operates only on Swap rows because the Q96 fee math requires
  the swap-specific `tick` and `liquidity` payload columns decoded from the Swap
  event data — these columns are absent on Mint/Burn/Transfer rows.

  attach_in_range has ALREADY joined vault columns (lowerTick/upperTick/
  vault_in_range/totalAmounts_0/totalAmounts_1/totalSupply) onto every row before
  this split, so non-Swap rows correctly inherit those vault columns. After
  compute_swap_fee, we re-concatenate via `diagonal_relaxed` which reconciles
  heterogeneous schemas (the fee_token0/fee_token1/vault_fee_token0/
  vault_fee_token1 columns are absent on non-Swap rows and become null).

`vault_liquidity` alias: revenue_leg.compute_swap_fee expects a column named
`vault_liquidity` (Phase 2 sentinel = vault's `totalSupply` per RESEARCH §A
docstring). attach_in_range emits `totalSupply` (not `vault_liquidity`) — this
orchestrator bridges the naming gap by aliasing `totalSupply` → `vault_liquidity`
on the Swap branch before invoking compute_swap_fee. A precise
`pool.positions(vault, lower, upper).liquidity` computation is deferred per
RESEARCH §A's Phase-7 contingency note.
"""
import json
from pathlib import Path

import polars as pl

from . import (
    decoders,
    fx_snap,
    ingest,
    phantom_filter,
    provenance,
    revenue_leg,
    vault_state,
)
from .protocol_spec import ProtocolSpec


def build_panel(
    cache_path: str | Path,
    fx_sidecar_path: str | Path,
    vault_state_sidecar_path: str | Path,
    forno_head: int,
    protocol_spec: ProtocolSpec,
    tx_logs_jsonl: str | Path | None = None,
) -> pl.DataFrame:
    """Compose Wave 1 modules into the canonical Phase 2 panel.

    Parameters
    ----------
    cache_path
        Phase 1 Blockscout JSONL cache (content-addressed file). For real-data
        runs this is the pool-event sidecar `pool_events.jsonl` containing
        Swap/Mint/Burn logs only (the pool contract emits no Transfer events).
    fx_sidecar_path
        Mento broker historical-rate JSONL sidecar (Plan 02-06).
    vault_state_sidecar_path
        TS vault-state-snap JSONL sidecar (Plan 02-04).
    forno_head
        Forno head block number used for finality cutoff
        (cutoff = forno_head - lag_blocks).
    protocol_spec
        Validated ProtocolSpec from `protocol_spec.load_protocol`.
    tx_logs_jsonl
        Optional Transfer-companion sidecar (Plan 02-10). The build_panel_real
        driver pulls every log from each Swap-tx via Blockscout v2
        /transactions/{hash}/logs and filters to topic0 == ERC-20 Transfer.
        When provided, the rows are concatenated with the pool-event stream
        BEFORE the phantom-filter step so adapter-Transfer rows can be dropped
        by `exclude_adapters`. Pre-existing synthetic-fixture call sites that
        embed Transfer rows directly in `cache_path` continue to work unchanged
        (this parameter defaults to None).

    Returns
    -------
    pl.DataFrame
        Final panel with provenance columns, decoded event payload, vault-state
        join, Q96 LP-fees (on Swap rows; null on others), and Mento FX rates.
    """
    df = ingest.load_jsonl(Path(cache_path))
    if tx_logs_jsonl is not None:
        tx_df = ingest.load_jsonl(Path(tx_logs_jsonl))
        if tx_df.height > 0:
            df = pl.concat([df, tx_df], how="vertical")
    df = ingest.apply_finality_cutoff(
        df,
        forno_head,
        lag_blocks=protocol_spec.panel.finality_lag_blocks,
    )
    df = decoders.decode_all(df)
    df = phantom_filter.exclude_adapters(df)

    vs = vault_state.load_vault_state(Path(vault_state_sidecar_path))
    df = vault_state.attach_in_range(df, vs)

    # Swap-only branch through compute_swap_fee (see module docstring).
    swap_mask = pl.col("event_name") == "Swap"
    swap_rows = df.filter(swap_mask)
    non_swap = df.filter(~swap_mask)

    if swap_rows.height > 0:
        # Compute proper V3 virtual liquidity L for each Swap row from the
        # vault's totalAmounts + tick range + swap's sqrtPriceX96. This replaces
        # the prior totalSupply alias (totalSupply is share-token count, NOT a
        # V3 L value — using it as a proxy understated vault fee share by ~9
        # orders of magnitude on real vaults). See vault_state.attach_vault_liquidity.
        swap_rows = vault_state.attach_vault_liquidity(swap_rows)
        swap_rows = revenue_leg.compute_swap_fee(
            swap_rows,
            fee_tier_bps=protocol_spec.protocol.anchor_pool.fee_tier,
        )

    df = pl.concat([swap_rows, non_swap], how="diagonal_relaxed")

    fx = fx_snap.load_fx_sidecar(Path(fx_sidecar_path))
    df = fx_snap.attach_rates(df, fx)
    return df


def write_panel(
    df: pl.DataFrame, output_path: str | Path, **metadata: str
) -> Path:
    """Write panel to Parquet with PANEL-02 metadata embedded in the footer.

    Thin wrapper over `provenance.with_header`. All 6 PANEL-02 required keys
    (chainId, contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit)
    must be provided via `metadata` kwargs or `with_header` raises ValueError.
    """
    return provenance.with_header(df, output_path, **metadata)


def assert_no_graph_mainnet_in_ledger(ledger_path: str | Path) -> None:
    """DEMAND-01 enforce: Phase 2 cost-ledger MUST have zero endpoint='graph-mainnet' rows.

    Phase 2 only writes `endpoint='forno'` (vault state reads) or
    `endpoint='blockscout'` (event log fetches) rows. Any `graph-mainnet` row
    in the ledger after Phase-2 operations indicates a budget-policy violation
    and must fail the panel-build pipeline.

    A missing ledger file is treated as a no-op (no ledger = no offending rows).

    Raises
    ------
    AssertionError
        If any line in `ledger_path` decodes to `{"endpoint": "graph-mainnet", ...}`.
    """
    ledger_path = Path(ledger_path)
    if not ledger_path.exists():
        return
    bad_rows: list[tuple[int, dict]] = []
    with open(ledger_path, "r") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("endpoint") == "graph-mainnet":
                bad_rows.append((ln, row))
    if bad_rows:
        raise AssertionError(
            f"DEMAND-01 violation: {len(bad_rows)} graph-mainnet rows in "
            f"{ledger_path}: first offender line {bad_rows[0][0]}"
        )
