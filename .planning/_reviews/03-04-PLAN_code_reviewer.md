## VERDICT

PASS

## Scope

Code-reviewer pass on Plan 03-04 (DGP-04: wall-clock 80/20 split + held-out log-likelihood + stationarity diagnostic).

## Findings

- Frontmatter clean: wave 1, depends_on=["03-00","03-01","03-02"], two-task plan modifies four files cleanly (held_out.py, stationarity.py, two test files), non-overlapping with sibling Wave-1 plans
- Pitfall 3 (event-count split forbidden) verified two ways: dedicated `test_wallclock_NOT_event_count_split` AND acceptance criterion "File does NOT contain `iloc[` or `np.array_split`"
- SC-4 InsufficientEvaluationError fires on `held_out_fraction <= 0.0` AND on `test_window_start/end is None` paths — both have unit tests
- Closed-form exponential-kernel integral in `_hawkes_integrated_intensity` handles both train-history-tail-into-test and held-out events correctly; manual derivation in inline comments matches RESEARCH §Pattern 4
- WallClockSplit is a `@dataclass(frozen=True)` with a `to_metadata()` serializer — clean API for the orchestrator (03-07 consumes `split.t_split`, `split.to_metadata()`)
- Stationarity diagnostic: zero-train-rate safety branch (`tr == 0.0 or np.isnan(tr) → 'piecewise_required'`) is correct and tested
- Naming/constant choice (`STATIONARITY_RATIO_THRESHOLD`, `wall_clock_split`, `compute_held_out_loglik_*`) differs from the 03-00 scaffold stubs — flagged in the 03-00 review, not a 03-04 defect
- All acceptance criteria grep/pytest-verifiable

## Recommendation

Accept.
