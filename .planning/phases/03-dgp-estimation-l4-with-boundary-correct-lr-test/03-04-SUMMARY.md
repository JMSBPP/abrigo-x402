---
phase: 03-dgp-estimation-l4-with-boundary-correct-lr-test
plan: 04
subsystem: dgp
tags: [held-out, wall-clock-split, hawkes, nhpp, log-likelihood, stationarity, dgp-04, sc-4, pitfalls-3, pitfalls-4]

# Dependency graph
requires:
  - phase: 03-dgp-estimation-l4-with-boundary-correct-lr-test
    provides: "Wave-0 scaffold (03-00) — held_out.py + stationarity.py stubs, WallClockSplit frozen dataclass forward-declared, InsufficientEvaluationError exception class, HELD_OUT_FRACTION_DEFAULT and STATIONARITY_RATIO_THRESHOLD constants locked at scaffold time"
provides:
  - "wall_clock_split() — DGP-04 wall-clock 80/20 temporal split returning frozen WallClockSplit dataclass with t_split = window_start + (1 - held_out_fraction) * (window_end - window_start). NOT event-count split (Pitfall 3)."
  - "WallClockSplit.to_metadata() — emits fit_report.json :: held_out_loglik :: split_metadata block with t_split, window bounds, per-leg event counts, train/held_out window seconds."
  - "InsufficientEvaluationError raised on held_out_fraction <= 0 (SC-4) AND on None test window bounds in both *_loglik functions AND on zero-event held-out segment."
  - "compute_held_out_loglik_hawkes() — closed-form Hawkes log-likelihood on the test window with train-fitted parameters; full pre-test history feeds the exponential-kernel sum (self-excitation continuity through W_start); closed-form integral term."
  - "compute_held_out_loglik_nhpp() — homogeneous-baseline NHPP log-likelihood on the test window: N*log(mu) - mu*duration per leg."
  - "baseline_stationarity_check(WallClockSplit) — SC-4 +/-25% rate-ratio decision rule; returns fit_report.json :: baseline_stationarity_check block with {train_rate, held_out_rate, ratio, decision, threshold, per_leg_decision}."
  - "9 passing DGP-04 tests (5 held_out + 4 stationarity); wall-clock semantics, in-sample-only-raises, closed-form sanity, metadata key shape, stationary/piecewise_required branches, zero-rate safety branch."
affects: [03-03 (LR-test bootstrap rig consumes held-out segment), 03-05 (time-rescaling KS test runs on held-out leg), 03-06 (profile-likelihood may consume held-out for CV), 03-07 (orchestrator builds fit_report.json from these functions)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pattern D: frozen-dataclass return value (NOT dict) for cross-plan surface contracts — orchestrator consumes split.t_split / split.to_metadata() per the scaffold lock from 03-00"
    - "Pattern E: closed-form Hawkes log-likelihood with full pre-test history continuity — self-excitation kernel sums reference ALL prior events, not just the test-window events"
    - "Pattern F: safety-branch decision rule on degenerate input — train_rate=0 -> ratio=inf -> piecewise_required so a leg with all events in the held-out segment forces piecewise refit rather than crashing the diagnostic"

key-files:
  created: []
  modified:
    - analysis/src/abrigo_x402/dgp/held_out.py
    - analysis/src/abrigo_x402/dgp/stationarity.py
    - analysis/tests/test_held_out.py
    - analysis/tests/test_stationarity.py

key-decisions:
  - "Wall-clock split uses strict less-than on t_split (events at exactly t_split land in held-out segment). Symmetric to the test assertion `assert split.train_leg_0.tolist() == [100.0, 700.0]; assert split.held_out_leg_0.tolist() == [850.0]` from PLAN.md."
  - "Hawkes held-out log-likelihood requires full pre-test history (not just held-out events) — exponential kernel sum at any t in [W_start, W_end] references ALL prior events. Closed-form integral handles two cases: t_jk < W_start (kernel decays from W_start to W_end) and W_start <= t_jk < W_end (kernel decays from t_jk to W_end). NEVER drop the train history when scoring held-out."
  - "Degenerate Hawkes intensity (lambda <= 0 at any test event) short-circuits to log-likelihood = -inf — surfacing the misspecified-fit signal rather than crashing on log(0). Used by 03-03 bootstrap-LR rig to flag failed-fit replicates."
  - "Empty held-out segment (zero events on BOTH legs after split) raises InsufficientEvaluationError. A leg with all events in held-out (other leg has events in train) is permitted and triggers the stationarity safety branch (ratio=inf -> piecewise_required) rather than the InsufficientEvaluationError gate."
  - "STATIONARITY_RATIO_THRESHOLD = 0.25 literal preserved verbatim from PRE_REGISTRATION + SC-4; threshold is exposed in the return dict so downstream consumers can sanity-check against the locked constant."

patterns-established:
  - "Pattern D: frozen-dataclass return value for cross-plan surface contracts. Pattern usable by 03-07 orchestrator (consumes WallClockSplit) and any future plan emitting structured cross-plan data (PRE_REGISTRATION discipline: surfaces locked at scaffold time)."
  - "Pattern E: closed-form Hawkes log-likelihood with full pre-test history continuity. Pattern usable by 03-03 bootstrap-LR rig (refit on train, score on test with train-fitted params) and 03-05 time-rescaling (compensator integral on held-out segment uses train-fitted alpha/beta)."

requirements-completed: [DGP-04]

# Metrics
duration: 22 min
completed: 2026-05-27
---

# Phase 3 Plan 04: DGP-04 Wall-Clock Held-Out + Stationarity Diagnostic Summary

**Wall-clock 80/20 temporal split returning a frozen WallClockSplit dataclass + closed-form Hawkes/NHPP held-out log-likelihood with full pre-test history continuity + SC-4 +/-25% rate-ratio stationarity diagnostic — defends against Pitfall 3 (event-count splits couple test set to event density) and Pitfall 5 (in-sample optimism passes misspecified models).**

## Performance

- **Duration:** 22 min
- **Started:** 2026-05-27T02:46:44Z
- **Completed:** 2026-05-27T03:08:57Z
- **Tasks:** 2 (both TDD; RED-GREEN cycle each)
- **Files modified:** 4 (`analysis/src/abrigo_x402/dgp/held_out.py`, `analysis/src/abrigo_x402/dgp/stationarity.py`, `analysis/tests/test_held_out.py`, `analysis/tests/test_stationarity.py`)

## Accomplishments

- `wall_clock_split(leg_0_times, leg_1_times, window_start, window_end, held_out_fraction=0.20)` returning frozen `WallClockSplit` dataclass with `t_split = window_start + (1 - held_out_fraction) * (window_end - window_start)`. Raises `InsufficientEvaluationError` on `held_out_fraction <= 0` (SC-4) and on zero-event held-out segment (degenerate evaluation). NOT event-count split — anti-pattern grep gate `! grep -E "iloc\[|np\.array_split" held_out.py` passes (Pitfall 3 locked out).
- `WallClockSplit.to_metadata()` returns the `fit_report.json :: held_out_loglik :: split_metadata` block with keys `t_split`, `window_start`, `window_end`, `held_out_fraction`, `train_events_per_leg`, `held_out_events_per_leg`, `train_window_seconds`, `held_out_window_seconds`.
- `compute_held_out_loglik_hawkes(baseline, adjacency, decays, test_leg_0, test_leg_1, full_history_leg_0, full_history_leg_1, test_window_start, test_window_end)`: closed-form Hawkes log-likelihood `log L = Σ log(λ_i(t_ik)) - ∫_{W_start}^{W_end} λ_i(s) ds`. Full pre-test history feeds the exponential-kernel sum (self-excitation continuity through W_start). Closed-form integral handles past events both before W_start (contribute `α * (exp(-β(W_start - t_jk)) - exp(-β(W_end - t_jk))) / β`) and inside [W_start, W_end] (contribute `α * (1 - exp(-β(W_end - t_jk))) / β`). Degenerate `λ <= 0` short-circuits to `-inf`. Raises `InsufficientEvaluationError` when test window bounds are None (SC-4).
- `compute_held_out_loglik_nhpp(nhpp_baseline_per_sec, test_leg_0, test_leg_1, test_window_start, test_window_end)`: homogeneous-baseline NHPP log-likelihood `N * log(mu) - mu * duration` per leg. Raises `InsufficientEvaluationError` on None bounds (SC-4).
- `baseline_stationarity_check(split: WallClockSplit) -> dict`: SC-4 +/-25% decision rule. Computes per-leg `train_rate` / `held_out_rate` from the split, evaluates `|ho - tr| / tr` per leg, decides `'piecewise_required'` if either leg exceeds `STATIONARITY_RATIO_THRESHOLD = 0.25` else `'stationary'`. Safety branch: `train_rate = 0` on either leg → `ratio = inf` → `'piecewise_required'`. Returns dict with keys `train_rate`, `held_out_rate`, `ratio`, `decision`, `threshold`, `per_leg_decision` (all consumed by `fit_report.json :: baseline_stationarity_check`).
- **9 DGP-04 tests pass**: 5 in `test_held_out.py` (`test_wallclock_split`, `test_wallclock_NOT_event_count_split`, `test_in_sample_only_raises`, `test_held_out_loglik_hawkes_finite`, `test_split_metadata_keys`) + 4 in `test_stationarity.py` (`test_stationary_decision`, `test_piecewise_required_on_drifted_synthetic`, `test_handles_zero_train_rate`, `test_dict_keys_match_fit_report`).
- **Upstream regression clean**: `pytest tests/test_held_out.py tests/test_stationarity.py tests/test_nhpp_inar.py tests/test_hawkes_fit.py` → **16 passed** (9 DGP-04 + 3 DGP-01 + 4 DGP-02; no NHPP/Hawkes regression).
- `dgp/__init__.py` re-export surface unchanged (per success criterion: do NOT touch `dgp/__init__.py`).
- Pre-commit hooks AF-01..AF-12 PASS on all 4 task commits.

## Task Commits

This plan executed as two TDD features (RED-GREEN per task; no REFACTOR needed — implementations already clean):

1. **Task 1 RED:** `test(03-04): add failing DGP-04 wall-clock split + held-out log-likelihood tests` — `318c2f6`
2. **Task 1 GREEN:** `feat(03-04): implement DGP-04 wall-clock split + held-out log-likelihood` — `bad619a`
3. **Task 2 RED:** `test(03-04): add failing DGP-04 stationarity diagnostic tests` — `1c223c3`
4. **Task 2 GREEN:** `feat(03-04): implement DGP-04 baseline stationarity diagnostic` — `309c49f`

**Plan metadata commit:** (appended after STATE.md / ROADMAP.md / REQUIREMENTS.md updates)

## Files Modified

- `analysis/src/abrigo_x402/dgp/held_out.py` — replaced the 03-00 `NotImplementedError` stubs with the full DGP-04 implementation. `WallClockSplit.to_metadata()` body implemented; `wall_clock_split` validates `held_out_fraction > 0` and zero-event held-out before constructing the dataclass; `compute_held_out_loglik_hawkes` + `compute_held_out_loglik_nhpp` validate window bounds. Private helpers `_hawkes_intensity_at` and `_hawkes_integrated_intensity` implement the closed-form exponential-kernel scoring. Public surface unchanged from 03-00 stub (canonical Wave-1 names locked).
- `analysis/src/abrigo_x402/dgp/stationarity.py` — replaced the 03-00 `NotImplementedError` stub with `baseline_stationarity_check` body + private `_rate` helper. `STATIONARITY_RATIO_THRESHOLD = 0.25` literal preserved verbatim. Imports `WallClockSplit` from `held_out.py` (within-package dependency, no `dgp/__init__.py` cycle).
- `analysis/tests/test_held_out.py` — replaced 2 skip-marked stubs with 5 active tests covering all DGP-04 must-have invariants.
- `analysis/tests/test_stationarity.py` — replaced 1 skip-marked stub with 4 active tests covering stationary branch, piecewise_required branch, zero-rate safety branch, and dict-key contract.

## Decisions Made

- **Wall-clock split uses strict less-than at t_split**: events at exactly `t = t_split` land in the held-out segment per `train_leg = times[times < t_split]; held_out_leg = times[times >= t_split]`. Aligns with PLAN.md `test_wallclock_split` assertions (event at t=850 with t_split=800 lands in held_out, not train).
- **Hawkes held-out log-likelihood requires full pre-test history**: the kernel sum at any `t ∈ [W_start, W_end]` references ALL prior events including those before `W_start`. Dropping train history would break the self-excitation continuity invariant and produce a biased held-out score (too low because the test-window intensity would underestimate the true λ).
- **Degenerate intensity short-circuits to `-inf`** (rather than raising): the bootstrap-LR rig (Plan 03-03) generates many replicate fits, some of which may produce a fitted `λ(t) ≤ 0` at a test event (numerical edge case from optimizer convergence to the boundary). Returning `-inf` surfaces the bad-fit signal without crashing the bootstrap loop. Plan 03-03 filters NaN/-inf replicates per Pitfall 9 (RESEARCH.md).
- **Empty held-out segment on both legs → InsufficientEvaluationError**: the held-out segment carrying zero events on both legs is a degenerate evaluation; the LL would be `0` (no sum term) minus `μ * duration` (just baseline integral) which is a fixed-offset score, not a meaningful held-out metric. Raising honours the SC-4 lock.
- **Single-leg empty-train branch handled by stationarity, not by held_out**: a leg with all events in held-out (other leg has events in train) is permitted in `wall_clock_split` and routes through `baseline_stationarity_check`'s safety branch (`train_rate = 0` → `ratio = inf` → `piecewise_required`). This separates the SC-4 gate (in-sample-only forbidden) from the PITFALLS §4 diagnostic (non-stationarity rule-out).

## Deviations from Plan

None — plan executed exactly as written. The plan-supplied action code (in `<action>` blocks) was followed verbatim with only mechanical adaptations for the dataclass+function organization and the closed-form integral implementation details.

## Authentication Gates

None — DGP-04 is pure-compute (no network, no auth).

## Issues Encountered

**Concurrent peer-agent activity in Wave-1 working directory.** During Task 2 execution, concurrent peer agents (working on plans 03-03, 03-05, 03-06) landed their commits in `master`, advancing HEAD between my Task 2 RED and Task 2 GREEN commits. Additionally, peer-agent uncommitted work-in-progress on `lr_test.py`, `time_rescaling.py`, and `test_time_rescaling.py` was visible in my working directory after a pre-commit-hook stash/unstash cycle.

**Resolution:** Pre-commit hooks correctly stashed/restored unrelated changes around each commit. I committed ONLY my 03-04 scope (`held_out.py`, `stationarity.py`, `test_held_out.py`, `test_stationarity.py`) and left the peer-agent in-flight files unstaged. All 9 DGP-04 tests pass + 7 upstream NHPP/Hawkes tests pass (16 total in `pytest tests/test_held_out.py tests/test_stationarity.py tests/test_nhpp_inar.py tests/test_hawkes_fit.py`).

**Out-of-scope test failure (deferred):** `tests/test_lr_test.py::test_null_distribution_mixture_shape` fails with `NotImplementedError`. This is Plan 03-03's RED test (peer-agent landed `824ace1 test(03-03): add failing DGP-03 bootstrap LR tests` but their GREEN implementation has not yet committed). The failure is in `dgp/lr_test.py` which my 03-04 changes do not touch; it is OUT OF SCOPE per the deviation-rules scope boundary ("only auto-fix issues DIRECTLY caused by current task's changes"). Plan 03-03 owns this resolution.

## Next Phase Readiness

- **Plan 03-03 (bootstrap LR test)** unblocked: `compute_held_out_loglik_hawkes` + `compute_held_out_loglik_nhpp` are the held-out scoring functions the bootstrap rig uses to evaluate LR statistic on the held-out segment. The `InsufficientEvaluationError` gate guards against accidental in-sample LR computation.
- **Plan 03-05 (time-rescaling KS)** unblocked: `wall_clock_split` returns the `held_out_leg_0` / `held_out_leg_1` arrays the compensator integral is evaluated against. Plan 03-05's compensator uses train-fitted parameters on these held-out events.
- **Plan 03-06 (profile-likelihood)** unblocked: held-out CV across an eta grid can call `compute_held_out_loglik_hawkes` per candidate eta after refitting with `fit_hawkes_with_fixed_branching_ratio` on the train segment. (Plan 03-06 may or may not use held-out CV — the projection-trick spike from 03-02 is the primary path.)
- **Plan 03-07 (orchestrator)** unblocked: `WallClockSplit.to_metadata()` directly feeds `fit_report.json :: held_out_loglik :: split_metadata`; `baseline_stationarity_check(split)` directly feeds `fit_report.json :: baseline_stationarity_check`. Orchestrator reads these dicts and embeds them in the SC-1 metadata-wrapped fit report.
- **Four-criterion gate completion**: DGP-04 contributes (a) held-out log-likelihood for both NHPP and Hawkes (LR test gate consumes), and (b) the stationarity-rule-out leg of the gate. Combined with DGP-01 (NHPP fit), DGP-02 (Hawkes fit + η ≥ 0.2), DGP-03 (LR bootstrap p < 0.01), DGP-05 (KS p > 0.05), the four-criterion gate now has all five inputs available.

## Self-Check

Verifying claims before declaring complete.

### Files modified exist on disk with expected content

- `analysis/src/abrigo_x402/dgp/held_out.py` — FOUND (264 lines per `wc -l`; `wall_clock_split` body implemented; `compute_held_out_loglik_hawkes` body implemented; `compute_held_out_loglik_nhpp` body implemented; `WallClockSplit.to_metadata()` body implemented; NotImplementedError count = 0)
- `analysis/src/abrigo_x402/dgp/stationarity.py` — FOUND (88 lines; `baseline_stationarity_check` body implemented; `STATIONARITY_RATIO_THRESHOLD = 0.25` literal present; NotImplementedError count = 0)
- `analysis/tests/test_held_out.py` — FOUND (5 active test functions, 0 skip marks)
- `analysis/tests/test_stationarity.py` — FOUND (4 active test functions, 0 skip marks)

### Commits exist in history

- `318c2f6` — FOUND (Task 1 RED)
- `bad619a` — FOUND (Task 1 GREEN)
- `1c223c3` — FOUND (Task 2 RED)
- `309c49f` — FOUND (Task 2 GREEN)

### Verification commands executed

- `cd analysis && uv run pytest tests/test_held_out.py -v` → exit 0, **5 passed**
- `cd analysis && uv run pytest tests/test_stationarity.py -v` → exit 0, **4 passed**
- `cd analysis && uv run pytest tests/test_held_out.py tests/test_stationarity.py tests/test_nhpp_inar.py tests/test_hawkes_fit.py -v` → exit 0, **16 passed** (no upstream regression)
- `grep -c "class InsufficientEvaluationError" analysis/src/abrigo_x402/dgp/held_out.py` → **1** (acceptance: 1)
- `grep -c "def wall_clock_split" analysis/src/abrigo_x402/dgp/held_out.py` → **1** (acceptance: 1)
- `grep -c "def compute_held_out_loglik_hawkes" analysis/src/abrigo_x402/dgp/held_out.py` → **1** (acceptance: 1)
- `grep -c "def compute_held_out_loglik_nhpp" analysis/src/abrigo_x402/dgp/held_out.py` → **1** (acceptance: 1)
- `grep -c "held_out_fraction" analysis/src/abrigo_x402/dgp/held_out.py` → **10** (acceptance: ≥ 2)
- `grep -c "to_metadata" analysis/src/abrigo_x402/dgp/held_out.py` → **3** (acceptance: ≥ 1; method defined + docstring mentions)
- `! grep -E "iloc\[|np\.array_split" analysis/src/abrigo_x402/dgp/held_out.py` → exit 0 (Pitfall-3 anti-pattern ABSENT)
- `grep -c "STATIONARITY_RATIO_THRESHOLD: float = 0.25" analysis/src/abrigo_x402/dgp/stationarity.py` → **1** (acceptance: 1)
- `grep -c "def baseline_stationarity_check" analysis/src/abrigo_x402/dgp/stationarity.py` → **1** (acceptance: 1)
- `grep -c "piecewise_required" analysis/src/abrigo_x402/dgp/stationarity.py` → **8** (acceptance: ≥ 2)
- `grep -c '"decision"' analysis/src/abrigo_x402/dgp/stationarity.py` → **1** (acceptance: ≥ 1)
- Pre-commit hooks AF-01..AF-12 → PASS on all 4 task commits

## Self-Check: PASSED

---
*Phase: 03-dgp-estimation-l4-with-boundary-correct-lr-test*
*Completed: 2026-05-27*
