"""PANEL-02: Inject Parquet-footer metadata via polars 1.41 native write_parquet(metadata=...).

Every Parquet output emitted by Phase 2 carries the metadata header:
  chainId, contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit

`make lint-artifacts` (Phase 1 Makefile stub, Phase 2 fills the body) reads each
output file's Parquet footer via `pl.read_parquet_metadata` and exits non-zero
on any missing key. `assert_has_header` is the unit-test-callable equivalent.

Runtime-probed per RESEARCH §I: polars 1.41 supports native dict[str,str]
metadata embedded in the Parquet footer; round-trip is byte-stable.
"""
import subprocess
from pathlib import Path

import polars as pl

REQUIRED_KEYS: tuple[str, ...] = (
    "chainId",
    "contractAddress",
    "blockRange",
    "fetchTimestamp",
    "dataHash",
    "gitCommit",
)


def git_commit_short() -> str:
    """Return current HEAD as short hex (whatever `git rev-parse --short HEAD` emits).

    Default git produces 7 chars but may be longer in repos with hash collisions
    at the short prefix; callers should assert `len >= 7` and `int(s, 16)`.
    """
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()


def with_header(df: pl.DataFrame, output_path: Path | str, **meta) -> Path:
    """Write df to output_path with PANEL-02 metadata embedded in the Parquet footer.

    All metadata values are coerced to `str` (polars metadata is `dict[str, str]`).
    Raises ValueError BEFORE the write if any of REQUIRED_KEYS is missing — this
    keeps the filesystem clean (no partial / header-less files left behind).

    Returns the output_path as a `Path` for caller chaining.
    """
    md = {k: str(v) for k, v in meta.items()}
    missing = [k for k in REQUIRED_KEYS if k not in md]
    if missing:
        raise ValueError(f"PANEL-02 metadata missing keys: {missing}")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(output_path, metadata=md)
    return output_path


def assert_has_header(path: Path | str) -> None:
    """Raise AssertionError if any PANEL-02 required key is absent from the Parquet footer.

    Reads via `pl.read_parquet_metadata(path)` which returns `dict[str, str]`.
    """
    path = Path(path)
    md = pl.read_parquet_metadata(path)
    missing = [k for k in REQUIRED_KEYS if k not in md]
    if missing:
        raise AssertionError(f"PANEL-02 header missing in {path}: {missing}")
