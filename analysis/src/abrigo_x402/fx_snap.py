"""PANEL-03: Read Mento TS sidecar `data/raw/ichi/fx_rates/*.parquet`; forward-fill; USDT/USD separate.

The TS sidecar at `fetch/src/mento/historical-rate.ts` (Plan 02-06) snaps
the Mento Broker mid-rate at each event-block requested. This module
ingests that Parquet into the panel and applies a sort-then-forward-fill
join so every event row receives the most recent prior FX rate.

USDT/USD is a SEPARATE column (`usdt_usd_rate`) — NEVER collapsed to 1.0.
Phase 4 USDT-depeg sensitivity depends on this column existing in Phase 2.

`fx_snap_method` enum committed to PRE_REGISTRATION before any Phase 3 fit:
  "exact"        → Mento Broker quoted at the event block directly
  "forward_fill" → fell back to the most recent prior quote
  "unavailable"  → no prior quote in the window (drops/flags the row)
"""
from pathlib import Path

import polars as pl

FX_METHODS = ("exact", "forward_fill", "unavailable")


def load_fx_sidecar(sidecar_path: Path) -> pl.DataFrame:
    """Read the TS-sidecar-generated Parquet.

    Schema: {block: UInt64, source: Categorical, rate: Decimal[38,18],
             method: Categorical, provenance_url: String}.
    """
    raise NotImplementedError("Plan 02-06")


def attach_rates(df: pl.DataFrame, fx_df: pl.DataFrame) -> pl.DataFrame:
    """Join panel events to fx_df by event_block <= rate_block (max rate_block per event).

    Forward-fill via polars fill_null(strategy='forward') after sort.
    USDT/USD is a SEPARATE column (`usdt_usd_rate`) — NEVER collapsed to 1.0.
    """
    raise NotImplementedError("Plan 02-06")
