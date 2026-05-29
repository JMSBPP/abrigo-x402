"""PANEL-03: Read Mento TS sidecar JSONL; asof-join panel to FX rates; forward-fill.

The TS sidecar at `fetch/src/mento/historical-rate.ts` (Plan 02-06) snaps
the Mento Broker mid-rate at each event-block requested via raw viem
readContract({ blockNumber }) — Mento SDK 3.2.8 QuoteService cannot
historical-block-query (RESEARCH §B + Pitfall 1).

This module ingests the JSONL sidecar and applies a polars `join_asof`
(strategy="backward") so every panel event row receives the most recent
prior 'exact' FX rate. Sidecar rows with method='unavailable' are excluded
BEFORE the asof join so the forward-fill takes the most recent EXACT rate
(not a zero from an unavailable Broker quote).

USDT/USD is a SEPARATE column (`usdt_usd_rate`) — NEVER collapsed to 1.0
(CLAUDE.md non-negotiable). Phase 2 default: `usdt_usd_rate='1.0'`,
`usdt_usd_method='stipulated'`. Phase 4 USDT-depeg sensitivity may
overwrite specific rows with depeg-event data without touching this module.

`fx_method` enum committed to PRE_REGISTRATION before any Phase 3 fit:
  "exact"        → Mento Broker quoted at the event block directly
  "forward_fill" → fell back to the most recent prior 'exact' quote
  "unavailable"  → event block precedes any 'exact' quote in the window
"""
from __future__ import annotations

import json
from pathlib import Path

import polars as pl

FX_METHODS: tuple[str, str, str] = ("exact", "forward_fill", "unavailable")

FX_SIDECAR_SCHEMA: dict[str, pl.DataType] = {
    "block": pl.Int64,
    "source": pl.String,
    "rate_x1e18": pl.String,
    "method": pl.String,
    "provenance_url": pl.String,
}


def load_fx_sidecar(sidecar_path: Path | str) -> pl.DataFrame:
    """Read TS-sidecar JSONL of Mento broker historical-block FX rates.

    Schema: {block: Int64, source: String, rate_x1e18: String, method: String,
             provenance_url: String}.

    rate_x1e18 stays a String (decimal-string representation of uint256 scaled
    1e18) to preserve precision across the language boundary — polars Decimal
    is not yet round-trip stable for >38-digit values.
    """
    sidecar_path = Path(sidecar_path)
    rows: list[dict] = []
    with open(sidecar_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    if not rows:
        return pl.DataFrame(schema=FX_SIDECAR_SCHEMA)
    return pl.DataFrame(rows, schema=FX_SIDECAR_SCHEMA)


def attach_rates(panel_df: pl.DataFrame, fx_df: pl.DataFrame) -> pl.DataFrame:
    """asof-join each panel row to the most recent prior 'exact' FX rate.

    Adds columns:
      cKES_per_USDm_rate (String; decimal-string from uint256 1e18-scaled)
      fx_method          (String; one of FX_METHODS)
      fx_provenance_url  (String; Blockscout block URL)
      usdt_usd_rate      (String; default "1.0" — NEVER absent — CLAUDE.md)
      usdt_usd_method    (String; "stipulated" Phase 2 default; Phase 4 may
                          overwrite to "oracle" or "depeg-event")

    Forward-fill semantics:
      - Sidecar rows with method='unavailable' are EXCLUDED before the
        asof join so forward-fill takes the most recent 'exact' rate.
      - Panel event at block < smallest exact-rate block → fx_method='unavailable'.

    The asof join uses strategy="backward" (most recent block ≤ event block).
    """
    if "blockNumber" not in panel_df.columns:
        raise ValueError("panel_df must have blockNumber column")

    # Exclude unavailable rows so forward-fill skips them.
    exact_fx = fx_df.filter(pl.col("method") == "exact").sort("block")
    panel_sorted = panel_df.sort("blockNumber")

    if exact_fx.height == 0:
        # No exact rates at all — every panel row is unavailable.
        out = panel_sorted.with_columns(
            pl.lit(None, dtype=pl.String).alias("cKES_per_USDm_rate"),
            pl.lit("unavailable").alias("fx_method"),
            pl.lit(None, dtype=pl.String).alias("fx_provenance_url"),
        )
    else:
        # Rename sidecar columns BEFORE the join so we can detect exact-vs-
        # forward_fill by comparing event block vs joined fx block.
        fx_for_join = exact_fx.rename(
            {
                "block": "_fx_block",
                "rate_x1e18": "cKES_per_USDm_rate",
                "provenance_url": "fx_provenance_url",
            }
        )
        # Drop the residual 'source' + 'method' so they don't shadow downstream.
        fx_for_join = fx_for_join.drop(["source", "method"], strict=False)

        joined = panel_sorted.join_asof(
            fx_for_join,
            left_on="blockNumber",
            right_on="_fx_block",
            strategy="backward",  # most recent _fx_block <= blockNumber
        )

        out = joined.with_columns(
            pl.when(pl.col("cKES_per_USDm_rate").is_null())
            .then(pl.lit("unavailable"))
            .when(pl.col("_fx_block") == pl.col("blockNumber"))
            .then(pl.lit("exact"))
            .otherwise(pl.lit("forward_fill"))
            .alias("fx_method"),
        ).drop("_fx_block", strict=False)

    # USDT/USD — ALWAYS present (CLAUDE.md non-negotiable).
    # Default '1.0' with method='stipulated'; Phase 4 may overwrite specific
    # rows with depeg-event data without touching this module.
    out = out.with_columns(
        pl.lit("1.0").alias("usdt_usd_rate"),
        pl.lit("stipulated").alias("usdt_usd_method"),
    )
    return out
