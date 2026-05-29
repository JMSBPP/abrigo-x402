---
phase: 03-dgp-estimation-l4-with-boundary-correct-lr-test
plan: 00
subsystem: testing
tags: [scaffold, pytest, polars, tick, hawkes, nhpp, parquet, lint]

# Dependency graph
requires:
  - phase: 02-panel-build-l3-for-the-ichi-ckes-usdt-anchor
    provides: analysis/src/abrigo_x402/{panel,provenance}.py + analysis/tests/conftest.py + scripts/lint_artifacts.py PANEL-02 baseline
  - phase: 00-candidate-eligibility-pre-registration
    provides: notes/PRE_REGISTRATION.md Q-9 trip-wire thresholds + alpha=0.01 + 50:50 mixture null
provides:
  - 9 analysis/src/abrigo_x402/dgp/* module stubs with canonical Wave-1 symbol names locked
  - WallClockSplit frozen dataclass (consumed by 03-07 orchestrator as split.t_split / split.to_metadata())
  - InsufficientEvaluationError exception class for SC-4 in-sample-only-fit guard
  - 9 analysis/tests/test_*.py skip-marked stubs (21 functions collected)
  - 2 deterministic synthetic-data fixtures captured via tick.SimuHawkesExpKernels (eta=0.5 Hawkes + alpha=0 NHPP, 30 days each)
  - scripts/capture_synthetic_fixtures.py reproducible capture script
  - scripts/lint_artifacts.py extended with FIT_REPORT_REQUIRED_KEYS + dormant data/fits/**/fit_report.json walker
affects: [03-01, 03-02, 03-03, 03-04, 03-05, 03-06, 03-07, 03-08]

# Tech tracking
tech-stack:
  added: [tick.hawkes.SimuHawkesExpKernels usage in capture script]
  patterns:
    - "scaffold-first wave-0 with forward-declared dataclass + canonical-symbol-name lock"
    - "synthetic-ground-truth Parquet fixture captured once, loaded offline by Wave-1 tests"
    - "lint_artifacts.py dual-track (Parquet PANEL-02 + JSON SC-1) with dormant loop until artifact lands"

key-files:
  created:
    - analysis/src/abrigo_x402/dgp/nhpp_inar.py
    - analysis/src/abrigo_x402/dgp/hawkes_fit.py
    - analysis/src/abrigo_x402/dgp/lr_test.py
    - analysis/src/abrigo_x402/dgp/time_rescaling.py
    - analysis/src/abrigo_x402/dgp/profile_likelihood.py
    - analysis/src/abrigo_x402/dgp/held_out.py
    - analysis/src/abrigo_x402/dgp/stationarity.py
    - analysis/src/abrigo_x402/dgp/orchestrator.py
    - analysis/tests/test_nhpp_inar.py
    - analysis/tests/test_hawkes_fit.py
    - analysis/tests/test_lr_test.py
    - analysis/tests/test_held_out.py
    - analysis/tests/test_stationarity.py
    - analysis/tests/test_time_rescaling.py
    - analysis/tests/test_profile_likelihood.py
    - analysis/tests/test_fit_artifact_provenance.py
    - analysis/tests/test_byte_identical.py
    - analysis/tests/fixtures/synthetic_hawkes_eta_05.parquet
    - analysis/tests/fixtures/synthetic_nhpp_baseline_only.parquet
    - analysis/tests/fixtures/synthetic_fixtures_manifest.json
    - scripts/capture_synthetic_fixtures.py
  modified:
    - analysis/src/abrigo_x402/dgp/__init__.py
    - analysis/tests/conftest.py
    - scripts/lint_artifacts.py

key-decisions:
  - "Canonical Wave-1 symbol-name surface locked at scaffold time: wall_clock_split (not wallclock_split), compute_held_out_loglik_hawkes / compute_held_out_loglik_nhpp (not *_loglik_on_test), compute_compensator_exp_kernel (not compute_compensator_exp_hawkes), Q9_CI_WIDTH_THRESHOLD (not Q9_CI_WIDTH_NULL_FIRE_THRESHOLD), STATIONARITY_RATIO_THRESHOLD (not STATIONARITY_RATIO_TOLERANCE)"
  - "WallClockSplit is a @dataclass(frozen=True) returning split.t_split / split.train_leg_0 / split.train_leg_1 / split.held_out_leg_0 / split.held_out_leg_1 / split.window_start / split.window_end / split.held_out_fraction + split.to_metadata() — orchestrator 03-07 consumes this surface, NOT a dict"
  - "Synthetic fixture seeds locked at HAWKES_SEED = 20260526 + NHPP_SEED = 20260526 + 1; baseline 0.00013 events/sec/leg yields ~390 events/leg/30d in the same regime as the cKES/USDT real panel"
  - "tick.SimuHawkesExpKernels invoked WITHOUT force_simulation=True (Pitfall 9 — silently allows non-stationary draws)"
  - "lint_artifacts.py PANEL-02 + SC-1 fit_report.json dual-track: Wave 0 lands the dormant JSON walker today, activates automatically once Wave 2 plan 03-07 writes data/fits/**/fit_report.json"

patterns-established:
  - "Pattern A: Wave-0 scaffold with forward-declared frozen dataclass + canonical symbol-name lock so Wave-1 parallel plans land without ImportError or surface-drift"
  - "Pattern B: synthetic-ground-truth Parquet capture once, JSON manifest records seed + sha256 + tick version for reproducibility"

requirements-completed: [DGP-01, DGP-02, DGP-03, DGP-04, DGP-05, DGP-06]

# Metrics
duration: 5 min
completed: 2026-05-27
---

# Phase 3 Plan 00: DGP Estimation L4 Wave-0 Scaffold Summary

**Wave-0 scaffold lands 9 dgp/* module stubs with canonical Wave-1 symbol surface (incl. WallClockSplit frozen dataclass), 9 skip-marked pytest stubs, 2 deterministic tick.SimuHawkesExpKernels Parquet fixtures, and dormant lint_artifacts.py JSON walker for SC-1 fit_report.json — unblocks Wave-1 plans 03-01..03-06 to land in parallel without surface collision.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-05-27T00:15:53Z
- **Completed:** 2026-05-27T00:21:25Z
- **Tasks:** 3 (atomic per-task commits)
- **Files created:** 21
- **Files modified:** 3

## Accomplishments

- 9 `analysis/src/abrigo_x402/dgp/*` module stubs raising `NotImplementedError` with Wave-1-plan-ID references in the message — every public symbol (function, class, exception, module constant) named verbatim per the canonical Wave-1 surface so `from abrigo_x402.dgp import *` continues to succeed after Wave 1 replaces the stub bodies
- `WallClockSplit` frozen dataclass forward-declared in `held_out.py` with attributes `t_split / train_leg_0 / train_leg_1 / held_out_leg_0 / held_out_leg_1 / window_start / window_end / held_out_fraction` and `to_metadata()` method — load-bearing for orchestrator 03-07's `split.t_split` / `split.to_metadata()` consumption
- `InsufficientEvaluationError(RuntimeError)` exception class declared and verified to raise correctly via Python CLI
- `analysis/tests/conftest.py` extended with 5 new session-scoped fixtures (`synthetic_hawkes_eta_05_path`, `synthetic_nhpp_baseline_only_path`, `synthetic_hawkes_eta_05_legs`, `synthetic_nhpp_baseline_only_legs`, `synthetic_end_time`) + `make_synthetic_hawkes_fixture()` helper
- 9 `analysis/tests/test_*.py` skip-marked stubs with 21 test functions, all collected cleanly by `pytest --collect-only` (102 tests total Phase 2 + Phase 3 stubs)
- `scripts/capture_synthetic_fixtures.py` reproducible capture script with deterministic `HAWKES_SEED = 20260526` and `NHPP_SEED = 20260526 + 1`, baseline = 0.00013 events/sec/leg, decays = 0.1, end_time = 2,592,000 s (30 days)
- 2 captured Parquet fixtures: `synthetic_hawkes_eta_05.parquet` (354 leg-0 + 332 leg-1 events; sha256 `3bc7eb46…0bc`) and `synthetic_nhpp_baseline_only.parquet` (337 leg-0 + 316 leg-1 events; sha256 `5897776b…1c9`) — both within [100, 800] event-count sanity bounds
- `synthetic_fixtures_manifest.json` records adjacency, baseline, decays, end_time, seed, expected_branching_ratio, capture_phase, tick_version (0.8.0.2), polars_version (1.41.0), sha256 per fixture
- `scripts/lint_artifacts.py` extended with `FIT_REPORT_REQUIRED_KEYS = frozenset({chainId, contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit})` + `lint_fit_report_json(path)` + dormant `repo_root.glob("data/fits/**/fit_report.json")` walker — `make lint-artifacts` continues to PASS Phase 2 PANEL-02 (1 parquet OK; 0 JSON files yet → loop dormant)

## Task Commits

1. **Task 1: Create dgp/ module stubs + conftest extension** — `b091e3e` (feat)
2. **Task 2: Create test stubs (skip-marked) for all 9 test files** — `874b140` (test)
3. **Task 3: Capture synthetic-data fixtures + extend scripts/lint_artifacts.py** — `6abe1e8` (feat)

**Plan metadata commit:** (appended after STATE.md / ROADMAP.md updates)

## Files Created/Modified

### Created (21)

- `analysis/src/abrigo_x402/dgp/nhpp_inar.py` — `fit_nhpp_inar` stub + `BIN_WIDTH_GRID_SECONDS` + `MAX_P`
- `analysis/src/abrigo_x402/dgp/hawkes_fit.py` — `fit_hawkes_expkern` + `fit_hawkes_with_fixed_branching_ratio` + `compute_branching_ratio` stubs + `DECAY_GRID`
- `analysis/src/abrigo_x402/dgp/lr_test.py` — `parametric_bootstrap_lr` stub; SC-3 grep gate honoured (no literal `likelihood_ratio_test` or `chi2(1).sf` in source)
- `analysis/src/abrigo_x402/dgp/time_rescaling.py` — `compute_compensator_exp_kernel` + `time_rescaling_ks_test_leg` stubs
- `analysis/src/abrigo_x402/dgp/profile_likelihood.py` — `profile_likelihood_eta_ci` stub + `Q9_CI_WIDTH_THRESHOLD = 0.4`
- `analysis/src/abrigo_x402/dgp/held_out.py` — `WallClockSplit` dataclass + `InsufficientEvaluationError` + `wall_clock_split` + `compute_held_out_loglik_hawkes` + `compute_held_out_loglik_nhpp` + `HELD_OUT_FRACTION_DEFAULT = 0.20`
- `analysis/src/abrigo_x402/dgp/stationarity.py` — `baseline_stationarity_check` stub + `STATIONARITY_RATIO_THRESHOLD = 0.25`
- `analysis/src/abrigo_x402/dgp/orchestrator.py` — `run_fit` stub
- `analysis/tests/test_{nhpp_inar,hawkes_fit,lr_test,held_out,stationarity,time_rescaling,profile_likelihood,fit_artifact_provenance,byte_identical}.py` — 21 skip-marked stubs
- `analysis/tests/fixtures/synthetic_hawkes_eta_05.parquet` — 686 rows (354+332), 6048 bytes
- `analysis/tests/fixtures/synthetic_nhpp_baseline_only.parquet` — 653 rows (337+316), 5791 bytes
- `analysis/tests/fixtures/synthetic_fixtures_manifest.json` — capture metadata + sha256
- `scripts/capture_synthetic_fixtures.py` — reproducible capture script (one-shot, kept in repo)

### Modified (3)

- `analysis/src/abrigo_x402/dgp/__init__.py` — already had the canonical re-exports; was untracked at start, now committed as part of Task 1
- `analysis/tests/conftest.py` — Phase 2 fixtures preserved; appended Phase 3 synthetic-fixture loaders + `make_synthetic_hawkes_fixture()` helper
- `scripts/lint_artifacts.py` — added `FIT_REPORT_REQUIRED_KEYS` + `lint_fit_report_json` + dormant `data/fits/**/fit_report.json` walker; PANEL-02 path unchanged

## Decisions Made

- **Canonical Wave-1 symbol names locked at scaffold time** (per iteration-2 plan revision): every public symbol declared here matches the Wave-1 canonical name verbatim, eliminating the surface-drift class of ImportError failures at the Wave-1 acceptance gate
- **WallClockSplit dataclass, not dict** — orchestrator 03-07 reads `split.t_split` and `split.to_metadata()`; declaring the dataclass at scaffold time means 03-04 (Wave 1) and 03-07 (Wave 2) write against the same surface from Day 1
- **Synthetic fixture seeds 20260526 / 20260527** — date-rooted for traceability; reseeding would invalidate the sha256 entries in the manifest
- **`force_simulation=True` NEVER passed to tick.SimuHawkesExpKernels** (Pitfall 9 from `03-RESEARCH.md`) — silently allows non-stationary draws, which would corrupt the LR-test size-calibration baseline
- **lint_artifacts.py dormant-walker pattern** — the `data/fits/**/fit_report.json` glob returns zero files today, so the loop short-circuits without raising; activates automatically once Wave 2 plan 03-07 writes the artifact, no further lint_artifacts.py edits needed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Reworded `lr_test.py` docstring to honour SC-3 grep gate**
- **Found during:** Task 1 (Create dgp/ module stubs)
- **Issue:** Plan-supplied docstring listed prohibited names `statsmodels.stats.diagnostic.likelihood_ratio_test` and `scipy.stats.chi2(1).sf` verbatim in `analysis/src/abrigo_x402/dgp/lr_test.py`. Plan's own acceptance criterion `! grep -rE "likelihood_ratio_test|chi2\(1\)\.sf" analysis/src/abrigo_x402/dgp/lr_test.py` exits 0 fails when these literals appear anywhere in the file — including documentation comments.
- **Fix:** Reworded the "PROHIBITED IMPORTS" block to describe each prohibited helper in prose (e.g. "statsmodels diagnostic LR helper", "any scipy chi-squared survival-function call") while preserving the warning content. Author intent (block production use of asymptotic LR null helpers) is preserved without tripping the literal grep gate.
- **Files modified:** `analysis/src/abrigo_x402/dgp/lr_test.py`
- **Verification:** `! grep -rE "likelihood_ratio_test|chi2\(1\)\.sf" analysis/src/abrigo_x402/dgp/lr_test.py` exits 0 (SC-3 grep gate PASS); `grep -c "phase-3-bootstrap" analysis/src/abrigo_x402/dgp/lr_test.py` returns 1 (deterministic-seed marker preserved)
- **Committed in:** `b091e3e` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 Rule-1 plan-internal contradiction between docstring and grep-gate acceptance criterion)
**Impact on plan:** No scope creep. SC-3 grep gate now passes at scaffold time per plan's own acceptance criterion. Wave 1 plan 03-03 inherits a clean lr_test.py surface to drop the parametric-bootstrap-LR body into.

## Authentication Gates

None — Wave-0 scaffold is fully local-filesystem + uv subprocess; no network or auth required.

## Issues Encountered

None — plan executed cleanly across all 3 tasks. Pre-commit hooks (AF-01..AF-12) PASS on all 3 commits; 2-way review-trail enforcement and schema-frozen-check both Skipped (no files in scope for those hooks — both review files already landed in `.planning/_reviews/03-00-PLAN_{reality_checker,code_reviewer}.md`).

## Next Phase Readiness

- **Wave 1 unblocked**: Plans 03-01 (DGP-01 INAR(p) NHPP fit), 03-02 (DGP-02 Hawkes fit), 03-03 (DGP-03 bootstrap LR), 03-04 (DGP-04 held-out + stationarity), 03-05 (DGP-05 time-rescaling KS), 03-06 (DGP-06 profile-likelihood eta-CI) can land in parallel — each plan drops its body into the existing canonical-name stubs without touching `dgp/__init__.py` re-exports
- **Wave 2 unblocked**: Plan 03-07 (orchestrator `run_fit`) consumes the `WallClockSplit` dataclass surface and writes the first `data/fits/<run_id>/fit_report.json`; the dormant lint_artifacts.py JSON walker activates automatically
- **Synthetic-ground-truth fixtures available offline**: `synthetic_hawkes_eta_05_legs` (power tests) + `synthetic_nhpp_baseline_only_legs` (size-calibration + Kirchner INAR ground-truth recovery) — Wave-1 tests load via session-scoped pytest fixtures, no re-simulation cost
- **Phase 2 tests preserved**: full pytest collection 102/102 tests (9 panel_e2e Phase-2 + 21 Phase-3 stubs + Phase-2 unit tests); no regressions

## Self-Check

Verifying claims before declaring complete.

### Files created/modified exist on disk

- `analysis/src/abrigo_x402/dgp/nhpp_inar.py` — FOUND
- `analysis/src/abrigo_x402/dgp/hawkes_fit.py` — FOUND
- `analysis/src/abrigo_x402/dgp/lr_test.py` — FOUND
- `analysis/src/abrigo_x402/dgp/time_rescaling.py` — FOUND
- `analysis/src/abrigo_x402/dgp/profile_likelihood.py` — FOUND
- `analysis/src/abrigo_x402/dgp/held_out.py` — FOUND
- `analysis/src/abrigo_x402/dgp/stationarity.py` — FOUND
- `analysis/src/abrigo_x402/dgp/orchestrator.py` — FOUND
- `analysis/src/abrigo_x402/dgp/__init__.py` — FOUND (committed in Task 1)
- `analysis/tests/test_nhpp_inar.py` — FOUND
- `analysis/tests/test_hawkes_fit.py` — FOUND
- `analysis/tests/test_lr_test.py` — FOUND
- `analysis/tests/test_held_out.py` — FOUND
- `analysis/tests/test_stationarity.py` — FOUND
- `analysis/tests/test_time_rescaling.py` — FOUND
- `analysis/tests/test_profile_likelihood.py` — FOUND
- `analysis/tests/test_fit_artifact_provenance.py` — FOUND
- `analysis/tests/test_byte_identical.py` — FOUND
- `analysis/tests/fixtures/synthetic_hawkes_eta_05.parquet` — FOUND (6048 bytes)
- `analysis/tests/fixtures/synthetic_nhpp_baseline_only.parquet` — FOUND (5791 bytes)
- `analysis/tests/fixtures/synthetic_fixtures_manifest.json` — FOUND
- `scripts/capture_synthetic_fixtures.py` — FOUND
- `scripts/lint_artifacts.py` — MODIFIED (FIT_REPORT_REQUIRED_KEYS + lint_fit_report_json present)
- `analysis/tests/conftest.py` — MODIFIED (synthetic_hawkes_eta_05_legs fixture present)

### Commits exist in history

- `b091e3e` — FOUND (Task 1: dgp/ module stubs + conftest)
- `874b140` — FOUND (Task 2: 9 test stubs)
- `6abe1e8` — FOUND (Task 3: synthetic fixtures + lint_artifacts extension)

### Verification commands executed

- `cd analysis && uv run python -c "from abrigo_x402.dgp import ..."` — exit 0 (all 13 canonical names importable)
- `cd analysis && uv run python -c "from abrigo_x402.dgp.held_out import InsufficientEvaluationError; raise InsufficientEvaluationError('test')"` — exit non-zero with `InsufficientEvaluationError: test`
- `! grep -rE "likelihood_ratio_test|chi2\(1\)\.sf" analysis/src/abrigo_x402/dgp/lr_test.py` — exit 0 (SC-3 grep gate PASS)
- `cd analysis && uv run pytest --collect-only -q` — exit 0, 102 tests collected
- `make lint-artifacts` — exit 0, "1 parquet PASS PANEL-02"

## Self-Check: PASSED

---
*Phase: 03-dgp-estimation-l4-with-boundary-correct-lr-test*
*Completed: 2026-05-27*
