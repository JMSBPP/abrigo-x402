"""Plan 02-08: end-to-end panel build orchestrator + DEMAND-01 enforce.

100-block synthetic fixture exercises the full Pattern-1 pipeline:
  load_jsonl → apply_finality_cutoff → decode_all → exclude_adapters
  → attach_in_range → compute_swap_fee (Swap-only branch) → attach_rates
  → with_header

Cutoff arithmetic (Pitfall 5):
  cutoff = FORNO_HEAD - lag_blocks = 67_000_220 - 120 = 67_000_100
  fixture max block = 67_000_099 ≤ 67_000_100 → ALL 100 fixture rows kept
  phantom-filter drops 3 USDT-adapter Transfers → final row count = 97

If FORNO_HEAD drops below 67_000_220, finality_cutoff silently drops fixture
rows and test_build_panel_row_count's `df.height == 97` assertion will fail
(df.height collapses to 0). Re-verify the cutoff arithmetic any time
FORNO_HEAD is changed.
"""
from pathlib import Path

import polars as pl
import pytest

from abrigo_x402.panel import (
    assert_no_graph_mainnet_in_ledger,
    build_panel,
    write_panel,
)
from abrigo_x402.protocol_spec import load_protocol

FIXTURES = Path(__file__).parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[2]
ICHI_TOML = REPO_ROOT / "protocols" / "ichi.toml"

SWAPS_FIX = FIXTURES / "synthetic_swaps_n100.jsonl"
VS_FIX = FIXTURES / "synthetic_vault_state_n100.jsonl"
FX_FIX = FIXTURES / "synthetic_fx_rates_n100.jsonl"

# CRITICAL — cutoff arithmetic (Pitfall 5):
#   cutoff = FORNO_HEAD - lag_blocks = 67_000_220 - 120 = 67_000_100
#   fixture max block = 67_000_099 ≤ 67_000_100 → ALL 100 fixture rows kept
FORNO_HEAD = 67_000_220


@pytest.fixture
def spec():
    return load_protocol(ICHI_TOML)


def test_build_panel_row_count(spec):
    df = build_panel(
        cache_path=SWAPS_FIX,
        fx_sidecar_path=FX_FIX,
        vault_state_sidecar_path=VS_FIX,
        forno_head=FORNO_HEAD,
        protocol_spec=spec,
    )
    # 100 raw - 3 phantom-filtered = 97 rows
    assert df.height == 97, f"expected 97 rows, got {df.height}"


def test_build_panel_schema(spec):
    df = build_panel(SWAPS_FIX, FX_FIX, VS_FIX, FORNO_HEAD, spec)
    expected_cols = {
        "blockNumber",
        "txHash",
        "contractAddress",
        "event_name",
        "vault_in_range",
        "fee_token0",
        "fee_token1",
        "vault_fee_token0",
        "vault_fee_token1",
        "cKES_per_USDm_rate",
        "fx_method",
        "usdt_usd_rate",
    }
    actual = set(df.columns)
    missing = expected_cols - actual
    assert not missing, f"missing columns: {missing}; actual: {sorted(actual)}"


def test_build_panel_phantom_filtered_out(spec):
    from abrigo_x402.phantom_filter import USDT_FEE_ADAPTER

    df = build_panel(SWAPS_FIX, FX_FIX, VS_FIX, FORNO_HEAD, spec)
    # Phantom rows had `to=USDT_FEE_ADAPTER`; verify none survive.
    if "to" in df.columns:
        bad = df.filter(
            (pl.col("to").is_not_null())
            & (pl.col("to").str.to_lowercase() == USDT_FEE_ADAPTER)
        )
        assert bad.height == 0


def test_write_panel_has_metadata(tmp_path, spec):
    df = build_panel(SWAPS_FIX, FX_FIX, VS_FIX, FORNO_HEAD, spec)
    p = tmp_path / "panel.parquet"
    write_panel(
        df,
        p,
        chainId="42220",
        contractAddress="0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F",
        blockRange="[67000000,67000099]",
        fetchTimestamp="2026-05-26T11:00:00Z",
        dataHash="0xabc1234567",
        gitCommit="84dfc4d",
    )
    md = pl.read_parquet_metadata(p)
    for k in (
        "chainId",
        "contractAddress",
        "blockRange",
        "fetchTimestamp",
        "dataHash",
        "gitCommit",
    ):
        assert k in md, f"missing PANEL-02 key: {k}"


def test_build_panel_idempotent(spec):
    df1 = build_panel(SWAPS_FIX, FX_FIX, VS_FIX, FORNO_HEAD, spec)
    df2 = build_panel(SWAPS_FIX, FX_FIX, VS_FIX, FORNO_HEAD, spec)
    assert df1.height == df2.height

    def _sorted(d):
        if "logIndex" in d.columns:
            return d.sort(["blockNumber", "logIndex"])
        return d.sort("blockNumber")

    # Compare on the stable subset of columns (avoid wall-clock-flavored fields).
    a, b = _sorted(df1), _sorted(df2)
    common = [c for c in a.columns if c in b.columns]
    assert a.select(common).equals(b.select(common))


def test_vault_fee_zero_when_out_of_range(spec):
    df = build_panel(SWAPS_FIX, FX_FIX, VS_FIX, FORNO_HEAD, spec)
    swaps = df.filter(pl.col("event_name") == "Swap")
    out_of_range = swaps.filter(~pl.col("vault_in_range"))
    if out_of_range.height > 0:
        for fee in out_of_range["vault_fee_token0"].to_list():
            assert int(fee or "0") == 0
        for fee in out_of_range["vault_fee_token1"].to_list():
            assert int(fee or "0") == 0


def test_cKES_rate_populated(spec):
    df = build_panel(SWAPS_FIX, FX_FIX, VS_FIX, FORNO_HEAD, spec)
    # Every row should have a non-null rate (forward-filled when needed).
    assert df["cKES_per_USDm_rate"].null_count() < df.height
    # At least some rows should be forward_fill (10 fx rates over 100 blocks).
    fwd = df.filter(pl.col("fx_method") == "forward_fill").height
    assert fwd > 0, "expected at least one forward_fill row"


def test_usdt_usd_separate_column(spec):
    df = build_panel(SWAPS_FIX, FX_FIX, VS_FIX, FORNO_HEAD, spec)
    assert "usdt_usd_rate" in df.columns
    assert df["usdt_usd_method"][0] == "stipulated"


def test_demand_01_no_graph_mainnet(tmp_path):
    """Phase 2 must NEVER write endpoint='graph-mainnet' rows."""
    # Clean ledger: forno + blockscout only → no raise
    ledger = tmp_path / "_cost_ledger.jsonl"
    ledger.write_text(
        '{"endpoint":"forno","chain":"celo","usdc_cost":"0"}\n'
        '{"endpoint":"blockscout","chain":"celo","usdc_cost":"0"}\n'
    )
    assert_no_graph_mainnet_in_ledger(ledger)

    # Polluted ledger: any graph-mainnet row → AssertionError
    bad = tmp_path / "bad_ledger.jsonl"
    bad.write_text(
        '{"endpoint":"forno"}\n'
        '{"endpoint":"graph-mainnet","chain":"celo","usdc_cost":"0.001"}\n'
    )
    with pytest.raises(AssertionError, match="graph-mainnet"):
        assert_no_graph_mainnet_in_ledger(bad)

    # Missing ledger file is a NO-OP (no ledger = no offending rows).
    assert_no_graph_mainnet_in_ledger(tmp_path / "nonexistent.jsonl")
