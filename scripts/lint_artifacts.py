#!/usr/bin/env python3
"""PANEL-02 artifact linter — scan Parquet files for required metadata-header keys.

Usage:
  python scripts/lint_artifacts.py <path>...
  python scripts/lint_artifacts.py data/raw/ichi/panels/*.parquet

Exits 0 if every file has all six PANEL-02 required keys in its Parquet footer.
Exits non-zero with a diagnostic listing missing keys per file.

Standalone (no abrigo_x402 import) so the script can run from repo-root via
`uv run python scripts/lint_artifacts.py ...` without configuring sys.path.
"""
import glob
import sys
from pathlib import Path

REQUIRED_KEYS = (
    "chainId",
    "contractAddress",
    "blockRange",
    "fetchTimestamp",
    "dataHash",
    "gitCommit",
)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: lint_artifacts.py <path>...", file=sys.stderr)
        return 1

    # Resolve globs (shells like dash don't expand patterns the way bash/zsh do,
    # and Makefile recipes may pass an unexpanded glob if no files match).
    paths: list[Path] = []
    for arg in argv[1:]:
        matched = glob.glob(arg)
        if not matched:
            # Literal path (may not exist — handled below).
            paths.append(Path(arg))
        else:
            paths.extend(Path(m) for m in matched)

    # Filter to existing .parquet files only.
    paths = [p for p in paths if p.suffix == ".parquet" and p.exists()]
    if not paths:
        print("lint_artifacts: no .parquet files found to lint (this is OK pre-panel-build)")
        return 0

    try:
        import polars as pl
    except ImportError:
        print(
            "lint_artifacts: polars not available — run inside "
            "`cd analysis && uv run python ../scripts/lint_artifacts.py ...`",
            file=sys.stderr,
        )
        return 2

    failures: list[tuple[Path, list[str]]] = []
    for p in paths:
        try:
            md = pl.read_parquet_metadata(p)
        except Exception as e:
            failures.append((p, [f"FAILED TO READ METADATA: {e}"]))
            continue
        missing = [k for k in REQUIRED_KEYS if k not in md]
        if missing:
            failures.append((p, missing))

    if failures:
        print(
            f"lint_artifacts: {len(failures)} of {len(paths)} files FAILED PANEL-02:",
            file=sys.stderr,
        )
        for p, missing in failures:
            print(f"  {p}: missing {missing}", file=sys.stderr)
        return 1

    print(f"lint_artifacts: {len(paths)} file(s) PASS PANEL-02")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
