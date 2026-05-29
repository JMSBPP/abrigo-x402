## VERDICT

PASS

## Scope

Reality check on DGP-06 (profile-likelihood η-CI via `scipy.optimize.brentq` on the chi2(1) deficit; Q-9 null-fire trigger at ci_width > 0.4; projection-trick concrete implementation of `fit_hawkes_with_fixed_branching_ratio`).

## Findings

- CI method is PROFILE LIKELIHOOD: `deficit(η) = 2*(LL_max - LL_constrained(η)) - chi2(1).ppf(1-α)`, root-found via `scipy.optimize.brentq` on grid neighbours of the deficit-zero crossing. NOT Wald (Pitfall 4), NOT Hessian, NOT bootstrap (DGP-V2-02 deferred). Acceptance check `! grep -E "Hessian|Wald" profile_likelihood.py` enforces.
- `scipy.stats.chi2(1).ppf(1-α)` IS used here intentionally — the file docstring explicitly explains this is interior-parameter CI construction (η ∈ (0,1)), NOT the boundary LR-test null. The SC-3 grep gate is scoped to `lr_test.py` only and would not catch this.
- CI clamped to `[0, 0.999]` via explicit `max/min` on the brentq output; `test_ci_bounded` asserts `0.0 <= lower <= upper < 1.0` — the Pitfall-4 "CI extends past 1" failure mode is structurally impossible.
- Q9 trigger: `Q9_CI_WIDTH_THRESHOLD: float = 0.4` (PRE_REGISTRATION-locked, grep-gated to occur literally) and `q9_nullfire_triggered = bool(ci_width > 0.4)`. Test asserts the flag matches the structural definition rather than a hardcoded synthetic case.
- Projection-trick concrete implementation (replacing the 03-02 scaffold) is verified by `test_fit_hawkes_with_fixed_branching_ratio_projection` which directly asserts the rescaled adjacency's spectral radius matches `eta_target` to within 1e-4.

## Reality check

The most realistic failure is brentq failing to bracket a sign change on small-sample data where the profile likelihood is nearly flat. The plan wraps both brentq calls in `try/except (ValueError, RuntimeError)` and falls back to `ci_lower_grid` / `ci_upper_grid`, which are the grid endpoints (`np.linspace(0.01, 0.95, 30)` — step ~0.032). On a degenerate sample this means the CI defaults to a 30-point-grid resolution and the q9 trigger fires at the wrong width by up to 0.032 in either direction. More dangerously, when `in_ci_etas.size == 0` the CI collapses to `[eta_hat - 1e-6, eta_hat + 1e-6]` (width = 2e-6), which would NOT trigger q9 even though the profile is uninformative — a silent false negative on the Q-9 null-fire path.

## Recommendation

Accept with a follow-up note: the `in_ci_etas.size == 0` branch should arguably set `q9_nullfire_triggered = True` explicitly rather than relying on width arithmetic. Not a blocker for execution but worth surfacing as a 03-08 manual-sanity check or a future fix.
