"""PANEL-01 (vault state component): Read TS sidecar `data/raw/ichi/vault_state/*.parquet`.

The TS sidecar at `fetch/src/vault/state-snap.ts` (Plan 02-04) generates a
per-block Parquet snapshot of the ICHI anchor vault state. This module
ingests that Parquet into the panel and computes the `vault_in_range` flag
needed for the LP-fee accrual leg.

Schema written by the TS sidecar:
  blockNumber, totalAmounts_0, totalAmounts_1, totalSupply,
  currentTick, lowerTick, upperTick
"""
from pathlib import Path

import polars as pl


def load_vault_state(sidecar_path: Path) -> pl.DataFrame:
    """Read the TS-sidecar-generated Parquet of vault state per block.

    Schema: blockNumber, totalAmounts_0, totalAmounts_1, totalSupply,
    currentTick, lowerTick, upperTick.
    """
    raise NotImplementedError("Plan 02-04")


def attach_in_range(df: pl.DataFrame, vault_state: pl.DataFrame) -> pl.DataFrame:
    """Left-join vault_state on blockNumber; compute `vault_in_range = lowerTick <= tick <= upperTick`."""
    raise NotImplementedError("Plan 02-04")
