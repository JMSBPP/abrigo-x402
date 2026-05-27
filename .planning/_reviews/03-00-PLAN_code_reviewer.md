## VERDICT

PASS

## Scope

Code-reviewer pass on Phase 3 Wave-0 scaffold plan (dgp/* module stubs + conftest + synthetic fixtures + lint_artifacts hook), revised after iteration-1 NEEDS WORK on scaffold symbol drift.

## Findings

- Iteration 1 surfaced systemic naming drift between 03-00 stubs and the canonical Wave-1 names locked in 03-04/05/06. Revision iteration 2 reconciled all six rename pairs in 03-00's scaffold side (the Wave-1 names are canonical because 03-07 orchestrator already consumes them):
  - `wallclock_split` → `wall_clock_split`
  - `hawkes_loglik_on_test` → `compute_held_out_loglik_hawkes`
  - `nhpp_loglik_on_test` → `compute_held_out_loglik_nhpp`
  - `compute_compensator_exp_hawkes` → `compute_compensator_exp_kernel`
  - `Q9_CI_WIDTH_NULL_FIRE_THRESHOLD` → `Q9_CI_WIDTH_THRESHOLD`
  - `STATIONARITY_RATIO_TOLERANCE` → `STATIONARITY_RATIO_THRESHOLD`
- 03-00's `held_out.wallclock_split` dict-returning stub replaced with a frozen `WallClockSplit` dataclass forward declaration consistent with 03-04's surface and the orchestrator's `split.t_split` / `split.to_metadata()` usage in 03-07.
- New must-have truths lock the symbol-name match invariant and the dataclass surface; new acceptance grep gates verify NEW names present AND OLD names absent in scaffold files.
- Updated import-check on Task 1 verify block exercises the full canonical surface (incl. `WallClockSplit`).
- Otherwise: file tree right, fixture-capture script deterministic + Pitfall-9-safe, lint_artifacts hook reservation correct, test stubs use skip-with-reason, frontmatter acyclic.

## Recommendation

Accept. Iteration-1 BLOCKER closed. Plans ready for `/gsd:execute-phase 3`.
