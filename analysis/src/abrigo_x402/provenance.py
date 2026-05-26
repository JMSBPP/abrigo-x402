"""PANEL-02: Inject Parquet-footer metadata via polars 1.41 native write_parquet(metadata=...).

Every Parquet output emitted by Phase 2 carries the metadata header:
  chainId, contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit

`make lint-artifacts` (Phase 1 Makefile stub, Phase 2 fills the body) greps
each output file for the header fields and exits non-zero on any missing
field. `assert_has_header` is the unit-test-callable equivalent.
"""
import subprocess
from pathlib import Path

import polars as pl

REQUIRED_KEYS = (
    "chainId",
    "contractAddress",
    "blockRange",
    "fetchTimestamp",
    "dataHash",
    "gitCommit",
)


def git_commit_short() -> str:
    """Return the short HEAD git commit hash (7 chars)."""
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()


def with_header(df: pl.DataFrame, output_path: Path, **meta: str) -> Path:
    """Write df to output_path; metadata dict[str,str] embedded in Parquet footer.

    Raises ValueError if any of REQUIRED_KEYS missing.
    """
    raise NotImplementedError("Plan 02-07")


def assert_has_header(path: Path) -> None:
    """Read parquet metadata via pl.read_parquet_metadata; raise AssertionError if any required key absent."""
    raise NotImplementedError("Plan 02-07")
