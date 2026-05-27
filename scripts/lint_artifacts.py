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

# Phase 3 fit_report.json SC-1 metadata header — same six keys as the
# Parquet panel footer, surfaced at top-level of the JSON document.
# Wave 2 plan 03-07 lands the artifact at data/fits/**/fit_report.json;
# until then this loop is dormant (no JSON files to find -> no errors).
FIT_REPORT_REQUIRED_KEYS = frozenset({
    "chainId",
    "contractAddress",
    "blockRange",
    "fetchTimestamp",
    "dataHash",
    "gitCommit",
})


def lint_fit_report_json(path: Path) -> list[str]:
    """Verify SC-1 metadata-header keys exist at top level of fit_report.json.
    Returns list of missing-key / invalid-JSON errors.
    """
    import json
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return [f"{path}: invalid JSON ({exc})"]
    if not isinstance(payload, dict):
        return [f"{path}: fit_report.json root must be an object, got {type(payload).__name__}"]
    missing = FIT_REPORT_REQUIRED_KEYS - set(payload.keys())
    if missing:
        return [f"{path}: missing required SC-1 metadata keys: {sorted(missing)}"]
    return []


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
    parquet_paths = [p for p in paths if p.suffix == ".parquet" and p.exists()]

    # Phase 3 fit_report.json sweep: discover any data/fits/**/fit_report.json
    # under the current working directory. Loop is dormant until Wave 2 plan
    # 03-07 lands the artifact (no JSON files -> no errors raised).
    repo_root = Path.cwd()
    fit_report_paths = sorted(repo_root.glob("data/fits/**/fit_report.json"))

    if not parquet_paths and not fit_report_paths:
        print("lint_artifacts: no .parquet or fit_report.json files found to lint (this is OK pre-panel-build)")
        return 0

    failures: list[tuple[Path, list[str]]] = []

    if parquet_paths:
        try:
            import polars as pl
        except ImportError:
            print(
                "lint_artifacts: polars not available — run inside "
                "`cd analysis && uv run python ../scripts/lint_artifacts.py ...`",
                file=sys.stderr,
            )
            return 2

        for p in parquet_paths:
            try:
                md = pl.read_parquet_metadata(p)
            except Exception as e:
                failures.append((p, [f"FAILED TO READ METADATA: {e}"]))
                continue
            missing = [k for k in REQUIRED_KEYS if k not in md]
            if missing:
                failures.append((p, missing))

    for fit_json_path in fit_report_paths:
        errors = lint_fit_report_json(fit_json_path)
        if errors:
            failures.append((fit_json_path, errors))

    if failures:
        print(
            f"lint_artifacts: {len(failures)} of {len(parquet_paths) + len(fit_report_paths)} files FAILED PANEL-02 / SC-1:",
            file=sys.stderr,
        )
        for p, missing in failures:
            print(f"  {p}: {missing}", file=sys.stderr)
        return 1

    parts = []
    if parquet_paths:
        parts.append(f"{len(parquet_paths)} parquet PASS PANEL-02")
    if fit_report_paths:
        parts.append(f"{len(fit_report_paths)} fit_report.json PASS SC-1")
    print("lint_artifacts: " + "; ".join(parts))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
