"""PANEL-01: Load Phase 1 Blockscout JSONL cache → polars DataFrame; apply finality cutoff.

Reads the content-addressed JSONL cache emitted by Phase 1's
`fetch/src/cache/parquet-writer.ts` (data/raw/<protocol>/<hash[0:2]>/<hash>.jsonl)
and surfaces a polars DataFrame with the minimum panel row schema:
  blockNumber, blockHash, logIndex, txHash, contractAddress, topics, data

Finality cutoff: events on blocks > (forno_head - finality_lag_blocks) are
EXCLUDED. Default lag = 120 blocks (~2min Celo soft-finality).
Per-protocol override at `protocols/<protocol>.toml [panel] finality_lag_blocks`.

Pipeline contract (RESEARCH §E + Pitfall 5): apply_finality_cutoff MUST be the
FIRST transform after load_jsonl, before any join or decode pass; downstream
modules consume the finality-filtered DataFrame.
"""
import json
from pathlib import Path

import polars as pl

DEFAULT_FINALITY_LAG = 120

PROVENANCE_COLS = ("blockNumber", "blockHash", "logIndex", "txHash", "contractAddress")


def _hex_to_int(s: str | int | None) -> int:
    if s is None:
        raise ValueError("null blockNumber/logIndex in JSONL row (PANEL-01 zero-null invariant)")
    if isinstance(s, int):
        return s
    return int(s, 16)


def load_jsonl(cache_path: str | Path) -> pl.DataFrame:
    """Read Phase 1 JSONL cache (one JSON object per line; Blockscout v1 etherscan-compat shape).

    Returns a polars DataFrame with typed provenance columns:
      blockNumber: Int64 (parsed from hex)
      blockHash: String
      logIndex: Int64
      txHash: String           (renamed from `transactionHash` for panel-row schema parity)
      contractAddress: String  (renamed from `address`)
      topics: List[String]
      data: String

    Raises ValueError if any row has null blockNumber (zero-null invariant per
    PANEL-01 must-have).
    """
    cache_path = Path(cache_path)
    rows: list[dict] = []
    with open(cache_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            rows.append(
                {
                    "blockNumber": _hex_to_int(row.get("blockNumber")),
                    "blockHash": row.get("blockHash") or "",
                    "logIndex": _hex_to_int(row.get("logIndex", "0x0")),
                    "txHash": row.get("transactionHash") or row.get("txHash") or "",
                    "contractAddress": (
                        row.get("address") or row.get("contractAddress") or ""
                    ).lower(),
                    "topics": row.get("topics", []),
                    "data": row.get("data", ""),
                }
            )
    df = pl.DataFrame(
        rows,
        schema={
            "blockNumber": pl.Int64,
            "blockHash": pl.String,
            "logIndex": pl.Int64,
            "txHash": pl.String,
            "contractAddress": pl.String,
            "topics": pl.List(pl.String),
            "data": pl.String,
        },
    )
    # Enforce zero-null invariant on blockNumber (PANEL-01 must-have).
    if df["blockNumber"].null_count() > 0:
        raise ValueError("PANEL-01: null blockNumber in ingested DataFrame")
    return df


def apply_finality_cutoff(
    df: pl.DataFrame, forno_head: int, lag_blocks: int = DEFAULT_FINALITY_LAG
) -> pl.DataFrame:
    """Drop events on blocks > forno_head - lag_blocks (Celo PoS soft-finality buffer).

    Applied as the FIRST transform after JSONL load to guarantee downstream
    modules receive a finality-filtered DataFrame (per RESEARCH §E + Pitfall 5).

    Args:
      df: polars DataFrame with `blockNumber` Int64 column (from load_jsonl).
      forno_head: latest Forno head block number (snapshot or live).
      lag_blocks: finality buffer in blocks; default 120 (~2min at Celo 1s/block).

    Returns:
      Filtered DataFrame; row count is monotonically non-increasing.
    """
    cutoff = forno_head - lag_blocks
    return df.filter(pl.col("blockNumber") <= cutoff)
