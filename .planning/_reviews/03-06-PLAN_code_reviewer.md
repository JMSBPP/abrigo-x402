## VERDICT

PASS

## Scope

Code-reviewer pass on Plan 03-06 (DGP-06: profile-likelihood η-CI + concrete fit_hawkes_with_fixed_branching_ratio via projection trick + Q-9 nullfire trigger).

## Findings

- Frontmatter clean: wave 1, depends_on=["03-00","03-02"], requirement DGP-06; modifies hawkes_fit.py (shared with 03-02 — sequenced by depends_on, not a parallel conflict)
- Pitfall 4 (Wald/Hessian CI forbidden) grep-gated: acceptance criterion "File does NOT contain `Hessian` or `Wald` substrings"
- `scipy.stats.chi2(1)` use is explicitly documented as legitimate in the file docstring AND inline at the threshold computation — explanation distinguishes interior-parameter CI from the boundary LR-test null; SC-3 grep gate is correctly scoped to lr_test.py only (per CONTEXT)
- Q-9 lock: `Q9_CI_WIDTH_THRESHOLD: float = 0.4` declared as module constant, fired via `bool(ci_width > Q9_CI_WIDTH_THRESHOLD)`, and verified by `test_q9_nullfire_trigger`
- CI bounded in [0, 1) by `max(0.0, ci_lower)` / `min(0.999, ci_upper)` clamps; `test_ci_bounded` checks `0.0 <= lower <= upper < 1.0`
- Projection trick implementation: spectral-radius rescaling of α with degenerate-fallback when η_hat≈0; `test_fit_hawkes_with_fixed_branching_ratio_projection` checks attained spectral radius matches target to 1e-4
- Direct `scorer.coeffs = np.concatenate([baseline, adjacency.ravel()])` assignment depends on tick 0.8.0.2 internals — fragile but documented; CONTEXT pins the library version
- Constant naming `Q9_CI_WIDTH_THRESHOLD` differs from 03-00 stub's `Q9_CI_WIDTH_NULL_FIRE_THRESHOLD` — flagged in 03-00 review
- Both bare-except branches around brentq fall back to grid bounds — acceptable robustness fallback

## Recommendation

Accept.
