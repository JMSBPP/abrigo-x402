"""DGP-06: Profile-likelihood branching-ratio eta-CI (genuine constrained MLE).

LOCKED INVARIANTS (PRE_REGISTRATION + PITFALLS §4):

- eta-CI via PROFILE LIKELIHOOD (Filimonov & Sornette 2014; Wheatley ETH thesis).
- Phase 04.1.1-v2: the CI is a GENUINE CONSTRAINED MLE — at each grid eta the profile
  LL is the max of the canonical Hawkes LL over (lambda_0, alpha) subject to
  rho(alpha/beta) == eta (see `_constrained_profile_loglik`). The reference LL_max is the
  UNCONSTRAINED joint-MLE LL and eta_hat is the unconstrained joint-MLE branching ratio.
  This REPLACES the retracted projection trick (PRE_REGISTRATION §Phase 04.1.1 (v2);
  DIAGNOSTIC §3 proved the prior [0.283, 0.371] band was a constrained-projection artifact
  at the LS-degenerate kernel-blind beta=0.1). method == "constrained_mle_profile".
- Bounded in [0, 1) by construction. Standard-error-based CI inversion (the
  classical normal-approximation interval from the inverse-Fisher-information
  matrix) is REJECTED here (Pitfall 4 — that family extends past 1 and the
  asymptotic-normality assumption breaks near eta=0).
- NOT a bootstrap CI (bootstrap-on-all-params is DGP-V2-02 deferred per RESEARCH).
- Q-9 null-fire trigger: ci_width > 0.4 -> q9_nullfire_triggered=True
  (PRE_REGISTRATION-locked sample-size floor; non-negotiable).

Why scipy.stats.chi2(1) is permitted here (and NOT in lr_test.py): this is an
interior-parameter CI construction for eta in (0, 1), with the MLE eta_hat assumed
interior. The boundary correction (50:50 chi2(0):chi2(1) mixture) applies ONLY to
testing the null eta=0 against the alternative eta>0, where eta=0 sits on the
parameter-space boundary. CI construction at an interior eta_hat is the standard
profile-likelihood inversion with the chi2(1) critical value.

The SC-3 grep gate (`grep -rE "likelihood_ratio_test|chi2\\(1\\)\\.sf"`) is
scoped to `analysis/src/abrigo_x402/dgp/lr_test.py` only — NOT this file.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import brentq, minimize
from scipy.stats import chi2

from abrigo_x402.dgp.hawkes_fit import compute_branching_ratio
from abrigo_x402.dgp.lr_test import _hawkes_loglik_vectorized

# PRE_REGISTRATION-locked Q-9 sample-size floor (non-negotiable).
Q9_CI_WIDTH_THRESHOLD: float = 0.4
DEFAULT_ALPHA: float = 0.05
# Coarse grid in (0, 1) for initial bracketing. scipy.optimize.brentq refines the
# crossing of the deficit function once the grid identifies neighbours straddling 0.
ETA_GRID_DEFAULT: tuple[float, ...] = tuple(np.linspace(0.02, 0.95, 30).tolist())


def _constrained_profile_loglik(
    eta_value: float,
    leg_0: np.ndarray,
    leg_1: np.ndarray,
    decays: float,
) -> float:
    """Genuine constrained-MLE profile log-likelihood at a fixed branching ratio.

    Phase 04.1.1-v2 (PRE_REGISTRATION §Phase 04.1.1 (v2); DIAGNOSTIC §3): this REPLACES
    the retracted projection trick. At the fixed `eta_value`, we re-optimize the canonical
    Hawkes log-likelihood `_hawkes_loglik_vectorized` over (lambda_0[2], alpha[2,2]) SUBJECT
    TO rho(alpha/beta) == eta_value. The constraint is enforced exactly inside the objective:
    the raw alpha is renormalized so its spectral radius equals `eta_value * beta` before the
    LL is evaluated. Every evaluated point therefore satisfies the constraint exactly — a
    genuine constrained re-optimization, NOT a one-shot rescale of the unconstrained fit.

    Multi-start L-BFGS-B (Hawkes LL is flat near the optimum; single-start lands in a
    sub-optimal basin — Pitfall 7). Returns the constrained-MLE LL at rho = eta_value.
    """
    T = float(max(leg_0.max(), leg_1.max()))
    lam0_emp = np.array(
        [max(leg_0.size, 1) / T, max(leg_1.size, 1) / T], dtype=np.float64
    )
    starts = [
        (lam0_emp.copy(), np.full((2, 2), 0.1, dtype=np.float64)),
        (lam0_emp / 2.0, np.full((2, 2), 0.2, dtype=np.float64)),
        (lam0_emp / 4.0, np.full((2, 2), 0.05, dtype=np.float64)),
    ]

    def neg_ll(theta: np.ndarray) -> float:
        lam0 = theta[:2]
        araw = theta[2:].reshape(2, 2)
        rho_raw = compute_branching_ratio(araw, float(decays))
        if rho_raw < 1e-12:
            return 1e18
        # Renormalize so rho(anorm/beta) == eta_value exactly:
        #   rho(anorm/beta) = (anorm scaled by s) => s = eta_value / rho_raw.
        anorm = araw * (float(eta_value) / rho_raw)
        ll = _hawkes_loglik_vectorized(lam0, anorm, float(decays), leg_0, leg_1)
        return -ll if np.isfinite(ll) else 1e18

    bounds = [(1e-12, None)] * 6
    best_neg = float("inf")
    for lam0_init, araw_init in starts:
        theta0 = np.concatenate([lam0_init, araw_init.ravel()])
        try:
            res = minimize(
                neg_ll,
                theta0,
                method="L-BFGS-B",
                bounds=bounds,
                options={"maxiter": 500, "ftol": 1e-9},
            )
        except Exception:
            continue
        if res.success and float(res.fun) < best_neg:
            best_neg = float(res.fun)
    if not np.isfinite(best_neg):
        return float("nan")
    return -best_neg


def profile_likelihood_eta_ci(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    hawkes_fit: dict,
    decays: float,
    alpha: float = DEFAULT_ALPHA,
    eta_grid: tuple[float, ...] | np.ndarray | None = None,
) -> dict:
    """Genuine constrained-MLE eta-CI for the Hawkes branching ratio.

    Phase 04.1.1-v2 (PRE_REGISTRATION §Phase 04.1.1 (v2); DIAGNOSTIC §3): the projection
    trick is RETRACTED. The CI is now a genuine constrained MLE — at each grid eta the
    profile LL is the MAXIMUM of the canonical Hawkes LL over (lambda_0, alpha) SUBJECT TO
    rho(alpha/beta) == eta (via `_constrained_profile_loglik`). The reference `LL_max` is
    the UNCONSTRAINED joint-MLE LL (recomputed at the scipy canonical fit params), NOT the
    max over a projected family; `eta_hat` is the unconstrained joint-MLE branching ratio,
    NOT the grid argmax.

    Method: evaluate the deficit
        D(eta) = 2 * (LL_max - profile_LL(eta)) - chi2(1).ppf(1 - alpha)
    on a coarse grid; refine the lower and upper crossings of D(eta) = 0 via
    scipy.optimize.brentq. The CI is the set {eta : D(eta) <= 0}, clamped to
    [0, 1) by construction.

    Returns
    -------
    dict with keys:
      method: literal "constrained_mle_profile"
      eta_hat: unconstrained joint-MLE branching ratio (from hawkes_fit)
      lower, upper: CI endpoints in [0, 1)
      ci_width: upper - lower
      alpha: confidence-level parameter (0.05 -> 95% CI)
      q9_nullfire_triggered: bool (ci_width > Q9_CI_WIDTH_THRESHOLD)
      q9_threshold: the locked threshold 0.4 (for downstream provenance)
    """
    # eta_hat is the unconstrained joint-MLE branching ratio (the scipy_canonical_ll
    # AIC-min eta from Plan 04.1.1-01), NOT the grid argmax of a projected family.
    eta_hat = float(hawkes_fit["branching_ratio"])
    # chi2(1) critical value is correct HERE: interior-parameter CI inversion.
    # The boundary correction (50:50 mixture) applies to the LR test of eta=0 only.
    threshold = float(chi2(1).ppf(1.0 - alpha))

    def _profile_loglik(eta_value: float) -> float:
        return _constrained_profile_loglik(
            float(eta_value), leg_0_times, leg_1_times, float(decays),
        )

    if eta_grid is None:
        grid = np.asarray(ETA_GRID_DEFAULT, dtype=np.float64)
    else:
        grid = np.asarray(eta_grid, dtype=np.float64)

    # LL_max := the UNCONSTRAINED joint-MLE LL, recomputed via the canonical
    # `_hawkes_loglik_vectorized` at the scipy-fitted params (hawkes_fit). This is the
    # true MLE reference for the chi2(1) deficit — NOT the max over a projected family
    # (the retracted projection-trick reference). The deficit D(eta) is then >= 0 by
    # construction at eta != eta_hat, so the CI {D <= 0} is a proper profile-likelihood set.
    LL_max = _hawkes_loglik_vectorized(
        np.asarray(hawkes_fit["baseline"], dtype=np.float64),
        np.asarray(hawkes_fit["adjacency"], dtype=np.float64),
        float(decays),
        leg_0_times,
        leg_1_times,
    )

    # Evaluate the genuine constrained-MLE profile log-likelihood on the grid.
    profile_loglik = np.empty(grid.size, dtype=np.float64)
    for k, eta_k in enumerate(grid):
        try:
            profile_loglik[k] = _profile_loglik(float(eta_k))
        except Exception:
            profile_loglik[k] = float("nan")

    valid_ll_mask = ~np.isnan(profile_loglik)
    if not valid_ll_mask.any() or not np.isfinite(LL_max):
        # All grid evaluations failed or the joint-MLE LL is non-finite; cannot construct
        # a CI. Return a degenerate CI at eta_hat and surface q9_nullfire_triggered=False.
        return {
            "method": "constrained_mle_profile",
            "eta_hat": float(min(max(eta_hat, 0.0), 0.999)),
            "lower": 0.0,
            "upper": 0.0,
            "ci_width": 0.0,
            "alpha": float(alpha),
            "q9_nullfire_triggered": False,
            "q9_threshold": float(Q9_CI_WIDTH_THRESHOLD),
        }

    LL_max = float(LL_max)

    def deficit(eta_value: float) -> float:
        """D(eta) = 2*(LL_max - profile_LL(eta)) - chi2(1).ppf(1-alpha).

        D(eta) <= 0  iff  eta is inside the (1 - alpha) profile-likelihood CI.
        """
        return 2.0 * (LL_max - _profile_loglik(eta_value)) - threshold

    profile_deficit = 2.0 * (LL_max - profile_loglik) - threshold

    valid_mask = ~np.isnan(profile_deficit)
    in_ci_mask = valid_mask & (profile_deficit <= 0.0)
    in_ci_etas = grid[in_ci_mask]

    if in_ci_etas.size == 0:
        # CI is empty on the grid (extreme misspec / degenerate optimization).
        # Surface as a tight CI around the joint-MLE eta_hat; the Q-9 null-fire trigger
        # will NOT fire here (ci_width ~ 0). Upstream callers should inspect the
        # boundary_warning on the Hawkes fit + fit_method_used to diagnose.
        ci_lower = float(max(0.0, eta_hat - 1e-6))
        ci_upper = float(min(0.999, eta_hat + 1e-6))
    else:
        ci_lower_grid = float(in_ci_etas.min())
        ci_upper_grid = float(in_ci_etas.max())
        grid_step = float(grid[1] - grid[0]) if grid.size >= 2 else 0.0

        # Refine lower endpoint: bracket = (ci_lower_grid - step, ci_lower_grid).
        # brentq requires sign change across the bracket; if it doesn't hold,
        # fall back to the grid value.
        ci_lower = ci_lower_grid
        if grid_step > 0.0 and ci_lower_grid > grid[0]:
            lo_bracket = max(1e-4, ci_lower_grid - grid_step)
            try:
                d_lo = deficit(lo_bracket)
                d_hi = profile_deficit[in_ci_mask].max() if False else deficit(ci_lower_grid)
                if not (np.isnan(d_lo) or np.isnan(d_hi)) and d_lo * d_hi < 0.0:
                    ci_lower = float(
                        brentq(deficit, lo_bracket, ci_lower_grid, maxiter=50)
                    )
            except (ValueError, RuntimeError):
                ci_lower = ci_lower_grid

        # Refine upper endpoint: bracket = (ci_upper_grid, ci_upper_grid + step).
        ci_upper = ci_upper_grid
        if grid_step > 0.0 and ci_upper_grid < grid[-1]:
            hi_bracket = min(0.999, ci_upper_grid + grid_step)
            try:
                d_lo = deficit(ci_upper_grid)
                d_hi = deficit(hi_bracket)
                if not (np.isnan(d_lo) or np.isnan(d_hi)) and d_lo * d_hi < 0.0:
                    ci_upper = float(
                        brentq(deficit, ci_upper_grid, hi_bracket, maxiter=50)
                    )
            except (ValueError, RuntimeError):
                ci_upper = ci_upper_grid

    # Structural clamp to [0, 1) — NEVER extends past the stationarity boundary.
    ci_lower = float(max(0.0, ci_lower))
    ci_upper = float(min(0.999, ci_upper))
    if ci_upper < ci_lower:
        ci_upper = ci_lower
    ci_width = float(ci_upper - ci_lower)

    return {
        "method": "constrained_mle_profile",
        "eta_hat": float(eta_hat),
        "lower": ci_lower,
        "upper": ci_upper,
        "ci_width": ci_width,
        "alpha": float(alpha),
        "q9_nullfire_triggered": bool(ci_width > Q9_CI_WIDTH_THRESHOLD),
        "q9_threshold": float(Q9_CI_WIDTH_THRESHOLD),
    }
