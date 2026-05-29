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

# Phase 04.1 extension: column-presence requirements for ICHI panel parquets.
# The single required column (initially) is `block_timestamp` — Phase 3 DGP fit
# input contract (analysis/src/abrigo_x402/dgp/orchestrator.py :: _extract_legs_from_panel).
# Frozenset form for forward-compat (additional required columns may follow in v2).
ICHI_PANEL_REQUIRED_COLUMNS = frozenset({
    "block_timestamp",
})

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


# ----- Phase 4 extensions (mirror REQUIRED_*_KEYS tuples from owning modules) -----
#
# These frozensets MUST stay in sync with the corresponding REQUIRED_*_KEYS tuples
# in analysis/src/abrigo_x402/{dependence,hedge}/*.py. The scaffold-time test
# analysis/tests/test_required_keys_sync.py asserts the equality at every run;
# any drift will fail that test before Wave 1 can land.

# Sync source: analysis/src/abrigo_x402/dependence/copula.py :: REQUIRED_JOINT_DIST_KEYS
JOINT_DIST_REQUIRED_KEYS = frozenset({
    "chainId", "contractAddress", "blockRange",
    "fetchTimestamp", "dataHash", "gitCommit", "run_id",
    "cross_correlogram", "permutation_null", "empirical_copula", "vine_fallback_used",
})

# Sync source: analysis/src/abrigo_x402/hedge/falsification.py :: REQUIRED_GATE_REPORT_KEYS
GATE_REPORT_REQUIRED_KEYS = frozenset({
    "chainId", "contractAddress", "blockRange",
    "fetchTimestamp", "dataHash", "gitCommit", "run_id",
    "vol_of_vol_gt_zero", "positive_skew_fat_tails",
    "hawkes_self_excitation", "usdt_depeg_basis_jump",
    "any_condition_passed",
})

# Sync source: analysis/src/abrigo_x402/hedge/stress_test.py :: REQUIRED_STRESS_REPORT_KEYS
STRESS_REPORT_REQUIRED_KEYS = frozenset({
    "chainId", "contractAddress", "blockRange",
    "fetchTimestamp", "dataHash", "gitCommit", "run_id",
    "independence_price", "fitted_joint_price", "comonotone_price",
    "divergence_pct", "divergence_flag", "comonotone_method",
})

# Sync source: analysis/src/abrigo_x402/hedge/carr_madan_strip.py :: REQUIRED_STRIP_KEYS
STRIP_REQUIRED_KEYS = frozenset({
    "chainId", "contractAddress", "blockRange",
    "fetchTimestamp", "dataHash", "gitCommit", "run_id",
    "strip_prices", "strikes", "n_grid_used", "escalated_to_2_12",
    "negative_mass_fraction", "positivity_tolerance",
})

# Sync source: analysis/src/abrigo_x402/hedge/carr_madan_strip.py :: STRIP_DEGENERATE_KEYS
# iter-3 Issue 1: `reason` field added for fourth-firing-condition routing
# (null_strip_unavailable) in null_result.decide_firing_condition.
STRIP_DEGENERATE_REQUIRED_KEYS = frozenset({
    "chainId", "contractAddress", "blockRange",
    "fetchTimestamp", "dataHash", "gitCommit", "run_id",
    "max_negative_value", "total_negative_mass",
    "characteristic_function_decay_rate", "recommended_method",
    "reason",
})


def _lint_json_against_keys(path: Path, required: frozenset[str], artifact_name: str) -> list[str]:
    """Shared helper: parse JSON at `path`, verify all `required` keys are present."""
    import json
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return [f"{path}: invalid JSON ({exc})"]
    if not isinstance(payload, dict):
        return [f"{path}: {artifact_name} root must be an object, got {type(payload).__name__}"]
    missing = required - set(payload.keys())
    if missing:
        return [f"{path}: missing required {artifact_name} keys: {sorted(missing)}"]
    return []


def lint_joint_dist_json(path: Path) -> list[str]:
    """Verify a joint_dist.json against REQUIRED_JOINT_DIST_KEYS (mirror)."""
    return _lint_json_against_keys(path, JOINT_DIST_REQUIRED_KEYS, "joint_dist.json")


def lint_gate_report_json(path: Path) -> list[str]:
    """Verify a gate_report.json against REQUIRED_GATE_REPORT_KEYS (mirror)."""
    return _lint_json_against_keys(path, GATE_REPORT_REQUIRED_KEYS, "gate_report.json")


def lint_stress_report_json(path: Path) -> list[str]:
    """Verify a stress_report.json against REQUIRED_STRESS_REPORT_KEYS (mirror)."""
    return _lint_json_against_keys(path, STRESS_REPORT_REQUIRED_KEYS, "stress_report.json")


def lint_strip_json(path: Path) -> list[str]:
    """Verify a strip.json against REQUIRED_STRIP_KEYS (mirror)."""
    return _lint_json_against_keys(path, STRIP_REQUIRED_KEYS, "strip.json")


def lint_strip_degenerate_json(path: Path) -> list[str]:
    """Verify a strip_degenerate.json against STRIP_DEGENERATE_REQUIRED_KEYS (mirror)."""
    return _lint_json_against_keys(path, STRIP_DEGENERATE_REQUIRED_KEYS, "strip_degenerate.json")


def lint_ichi_panel_columns(path: Path) -> list[str]:
    """Verify an ICHI panel parquet carries all ICHI_PANEL_REQUIRED_COLUMNS.

    Reads only the parquet schema (no row materialization). Empty list on PASS;
    one error string per missing column on FAIL.

    Phase 04.1 contract: the single required column is `block_timestamp`.
    """
    try:
        import polars as pl
    except ImportError:
        return [f"{path}: polars not available (run via `cd analysis && uv run`)"]
    try:
        cols = set(pl.read_parquet_schema(path).keys())
    except Exception as exc:
        return [f"{path}: failed to read parquet schema: {exc}"]
    missing = ICHI_PANEL_REQUIRED_COLUMNS - cols
    if missing:
        return [f"{path}: missing required ICHI panel columns: {sorted(missing)}"]
    return []


_PHASE_4_ARTIFACT_LINTERS: dict[str, callable] = {
    "joint_dist.json": lint_joint_dist_json,
    "gate_report.json": lint_gate_report_json,
    "stress_report.json": lint_stress_report_json,
    "strip.json": lint_strip_json,
    "strip_degenerate.json": lint_strip_degenerate_json,
}


def lint_phase_4_artifacts(root: Path) -> list[tuple[Path, list[str]]]:
    """Walk data/fits/**/{joint_dist,gate_report,stress_report,strip,strip_degenerate}.json
    under `root` and apply the corresponding linter to each.

    Returns aggregated (path, errors) failures. Dormant pre-Wave-2 (no artifacts yet).
    """
    failures: list[tuple[Path, list[str]]] = []
    for artifact_name, linter in _PHASE_4_ARTIFACT_LINTERS.items():
        for artifact_path in sorted(root.glob(f"data/fits/**/{artifact_name}")):
            errs = linter(artifact_path)
            if errs:
                failures.append((artifact_path, errs))
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

    # Phase 4 artifact sweep: joint_dist / gate_report / stress_report / strip / strip_degenerate.
    # Dormant pre-Wave-2 (no artifacts on disk yet).
    phase_4_failures = lint_phase_4_artifacts(repo_root)
    phase_4_paths_found = sum(
        1 for _ in repo_root.glob("data/fits/**/joint_dist.json")
    ) + sum(
        1 for _ in repo_root.glob("data/fits/**/gate_report.json")
    ) + sum(
        1 for _ in repo_root.glob("data/fits/**/stress_report.json")
    ) + sum(
        1 for _ in repo_root.glob("data/fits/**/strip.json")
    ) + sum(
        1 for _ in repo_root.glob("data/fits/**/strip_degenerate.json")
    )

    if not parquet_paths and not fit_report_paths and phase_4_paths_found == 0:
        print("lint_artifacts: no .parquet, fit_report.json, or Phase-4 artifacts found to lint (this is OK pre-panel-build)")
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
            # Phase 04.1: ICHI panel column-presence check (block_timestamp required).
            # Scope to data/raw/ichi/ panels only; non-ICHI panels (synthetic, Steer in
            # future iter-2) are out of scope for this contract.
            if "data/raw/ichi" in str(p):
                col_errs = lint_ichi_panel_columns(p)
                if col_errs:
                    failures.append((p, col_errs))

    for fit_json_path in fit_report_paths:
        errors = lint_fit_report_json(fit_json_path)
        if errors:
            # One row per failing file; the errors list may have multiple
            # entries (e.g. both missing header keys AND missing SC-1 keys).
            failures.append((fit_json_path, errors))

    # Aggregate Phase-4 artifact failures (dormant pre-Wave-2)
    failures.extend(phase_4_failures)

    total_files = len(parquet_paths) + len(fit_report_paths) + phase_4_paths_found

    if failures:
        print(
            f"lint_artifacts: {len(failures)} of {total_files} files FAILED schema check:",
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
    if phase_4_paths_found:
        parts.append(f"{phase_4_paths_found} phase-4 artifacts PASS")
    print("lint_artifacts: " + "; ".join(parts))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
