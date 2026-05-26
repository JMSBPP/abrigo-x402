"""PANEL-01: Load Phase 1 Blockscout JSONL cache → polars DataFrame; apply finality cutoff.

Reads the content-addressed JSONL cache emitted by Phase 1's
`fetch/src/cache/parquet-writer.ts` (data/raw/<protocol>/<hash[0:2]>/<hash>.jsonl)
and surfaces a polars DataFrame with the minimum panel row schema:
  blockNumber, blockHash, logIndex, txHash, contractAddress, event_name, ...payload

Finality cutoff: events on blocks > (forno_head - finality_lag_blocks) are
EXCLUDED. Default lag = 120 blocks (~2min Celo soft-finality).
Per-protocol override at `protocols/<protocol>.toml [panel] finality_lag_blocks`.
"""
from pathlib import Path

import polars as pl


def load_jsonl(cache_path: Path) -> pl.DataFrame:
    """Read Phase 1 JSONL cache and return a polars DataFrame with raw event columns."""
    raise NotImplementedError("Plan 02-01")


def apply_finality_cutoff(
    df: pl.DataFrame, forno_head: int, lag_blocks: int = 120
) -> pl.DataFrame:
    """Drop events on blocks > forno_head - lag_blocks. Returns finalized subset."""
    raise NotImplementedError("Plan 02-01")
