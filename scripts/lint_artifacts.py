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

# Phase 3 fit_report.json SC-1 schema. Plan 03-07 (orchestrator) lands the
# artifact at data/fits/**/fit_report.json. The schema is mirrored verbatim
# from analysis/src/abrigo_x402/dgp/orchestrator.py :: REQUIRED_FIT_REPORT_KEYS;
# both sources are kept in sync manually.
#
# The six top-level metadata-header keys (PANEL-02 baseline carried into SC-1):
FIT_REPORT_REQUIRED_KEYS = frozenset({
    "chainId",
    "contractAddress",
    "blockRange",
    "fetchTimestamp",
    "dataHash",
    "gitCommit",
})

# The full SC-1 top-level key set (12 additional Phase-3 result keys on top of
# the six PANEL-02 metadata keys). `make lint-artifacts` exits non-zero on any
# fit_report.json missing one or more of these.
FIT_REPORT_SC1_KEYS = frozenset({
    # Inherited PANEL-02 + Phase-3 provenance
    "chainId",
    "contractAddress",
    "blockRange",
    "fetchTimestamp",
    "dataHash",
    "gitCommit",
    "run_id",
    "tick_lib_version",
    # DGP-01..06 result blocks
    "nhpp_inar_params",
    "hawkes_mv_params",
    "lr_test",
    "ks_rescaled_time",
    "held_out_loglik",
    "branching_ratio_ci",
    "baseline_stationarity_check",
    "input_diagnostics",
    # Four-criterion gate output (CONTEXT.md <specifics>: present even on FAIL)
    "gate_passes",
    "gate_criteria",
})


def lint_fit_report_json(path: Path) -> list[str]:
    """Verify the SC-1 fit_report.json schema at the given path.

    Checks BOTH the PANEL-02 metadata-header subset AND the full SC-1 top-level
    key set. Returns list of error strings (empty on success). Caller aggregates
    into the failure count + exit code.
    """
    import json
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return [f"{path}: invalid JSON ({exc})"]
    if not isinstance(payload, dict):
        return [f"{path}: fit_report.json root must be an object, got {type(payload).__name__}"]
    errors: list[str] = []
    missing_header = FIT_REPORT_REQUIRED_KEYS - set(payload.keys())
    if missing_header:
        errors.append(
            f"{path}: missing required PANEL-02 metadata-header keys: {sorted(missing_header)}"
        )
    missing_sc1 = FIT_REPORT_SC1_KEYS - set(payload.keys())
    if missing_sc1:
        errors.append(
            f"{path}: missing required SC-1 keys: {sorted(missing_sc1)}"
        )
    return errors


def lint_fit_reports(root: Path) -> list[tuple[Path, list[str]]]:
    """Glob `data/fits/**/fit_report.json` under `root` and lint each.

    Returns list of (path, errors) tuples; an empty list means every fit_report.json
    passed (or none were found, which is also a pass — the loop is dormant pre-
    Wave-2).
    """
    failures: list[tuple[Path, list[str]]] = []
    for fit_report in sorted(root.glob("data/fits/**/fit_report.json")):
        errs = lint_fit_report_json(fit_report)
        if errs:
            failures.append((fit_report, errs))
    return failures


def _find_repo_root(start: Path) -> Path:
    """Walk up from `start` until a directory containing `data/` is found.

    Phase 2's `make lint-artifacts` cd's into `analysis/` before running this
    script (so the polars import resolves under the uv-managed venv). The fit
    report sweep must scan the repo's top-level `data/fits/**`, NOT the
    nested `analysis/data/fits/**`. Walking up from CWD or from the script
    file resolves the ambiguity.
    """
    for parent in (start, *start.parents):
        # Heuristic: repo root contains data/ AND .planning/ (or .git/).
        if (parent / "data").is_dir() and (
            (parent / ".planning").is_dir() or (parent / ".git").exists()
        ):
            return parent
    # Fall back to CWD so the previous behavior is preserved when neither marker exists.
    return start


def main(argv: list[str]) -> int:
    # Resolve globs (shells like dash don't expand patterns the way bash/zsh do,
    # and Makefile recipes may pass an unexpanded glob if no files match). Empty
    # argv is OK — the script still runs the fit_report.json sweep so that the
    # Makefile lint-artifacts target can be invoked when only fit artifacts exist.
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
    # under the REPO ROOT (walking up from CWD so the sweep works from both the
    # repo root and from analysis/ where Makefile cd's before invoking us).
    repo_root = _find_repo_root(Path.cwd())
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
            # One row per failing file; the errors list may have multiple
            # entries (e.g. both missing header keys AND missing SC-1 keys).
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
