"""PANEL-01 vault-state component: read TS sidecar JSONL, compute vault_in_range per Swap.

The TS sidecar (`fetch/src/vault/state-snap.ts`) writes JSONL with one row per
deduplicated block in the panel's Swap-event range. This module reads it as polars,
left-joins on `blockNumber`, and computes
`vault_in_range = (lowerTick <= tick <= upperTick)`.

Conservative semantics: if a Swap has no matching vault-state block (left-join NULL),
`vault_in_range` is False — the vault accrues zero LP-fees for that Swap. Missing
vault state is treated as "no info" → no fee credit, which keeps revenue_leg's
Q96 LP-fee calculation safe against gaps in sidecar coverage.

The TS sidecar's `currentTick` (the vault's notion of pool tick at the snap block)
is renamed to `vault_currentTick` in the joined frame to avoid collision with the
Swap event payload's own `tick` field — that latter is the comparison anchor for
the in-range check (it's per-event, not per-block).
"""
from __future__ import annotations

import json
from pathlib import Path

import polars as pl

VAULT_STATE_SCHEMA: dict[str, pl.DataType] = {
    "blockNumber": pl.Int64,
    "totalAmounts_0": pl.String,
    "totalAmounts_1": pl.String,
    "totalSupply": pl.String,
    "currentTick": pl.Int32,
    "lowerTick": pl.Int32,
    "upperTick": pl.Int32,
}


def load_vault_state(sidecar_path: Path) -> pl.DataFrame:
    """Read the TS-sidecar-generated JSONL of vault state per block.

    Schema: blockNumber (Int64), totalAmounts_0/1 (String, uint256 decimal),
    totalSupply (String), currentTick (Int32), lowerTick (Int32), upperTick (Int32).
    """
    sidecar_path = Path(sidecar_path)
    rows: list[dict] = []
    with open(sidecar_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return pl.DataFrame(rows, schema=VAULT_STATE_SCHEMA)


def attach_in_range(
    swap_df: pl.DataFrame, vault_state: pl.DataFrame
) -> pl.DataFrame:
    """Left-join vault_state onto swap_df by blockNumber; compute vault_in_range.

    Adds columns: totalAmounts_0, totalAmounts_1, totalSupply, vault_currentTick,
    lowerTick, upperTick, vault_in_range.

    vault_in_range = (lowerTick <= swap.tick <= upperTick) when vault state exists;
    False when vault state is missing for the swap's block (conservative-False
    semantics from the left-join NULL).
    """
    if "blockNumber" not in swap_df.columns:
        raise ValueError("swap_df must have a blockNumber column for the join")
    if "tick" not in swap_df.columns:
        raise ValueError(
            "swap_df must have a tick column for the in-range comparison"
        )

    # Rename vault's currentTick to avoid collision with the Swap event payload's
    # own tick column. The swap-side `tick` is the in-range comparison anchor.
    vd = vault_state.rename({"currentTick": "vault_currentTick"})
    out = swap_df.join(vd, on="blockNumber", how="left")

    # Closed-interval in-range check; null lowerTick/upperTick (no vault state at
    # this block) → conservative False via the is_not_null guard.
    out = out.with_columns(
        (
            pl.col("lowerTick").is_not_null()
            & pl.col("upperTick").is_not_null()
            & (pl.col("lowerTick") <= pl.col("tick"))
            & (pl.col("tick") <= pl.col("upperTick"))
        ).alias("vault_in_range")
    )
    return out
