"""Bivariate exponential-kernel Hawkes fit via tick.HawkesExpKern with full off-diagonal alpha matrix.

Reference: tick 0.8.0.2 docs + Daw & Pender 2017 arxiv:1707.05143v3 (bivariate spec).

Key invariants (PITFALLS):
- Decay grid (beta): {0.01, 0.1, 1.0, 10.0} per Wheatley thesis; AIC-min selection.
- Solver: accelerated gradient descent ('agd'), MLE objective ('likelihood'), no regularization (penalty='none').
- Full off-diagonal 2x2 adjacency — NEVER diagonal-only (PITFALLS §5 cross-leg dependence).
- Branching ratio: spectral radius of (alpha / beta) (Pitfall 6 — NOT max element).
- Same-block ties: shared continuous t = block_timestamp; tick handles natively (Pitfall 7 — NO logIndex tie-breaking).
- boundary_warning: True when fitted eta lands within BOUNDARY_WARNING_TOLERANCE of 0 or of 1.

Runtime deviation (recorded in fit_report.json provenance):
As of Phase 04.1.1-v2 the live estimator is **scipy_canonical_ll** — a scipy
L-BFGS-B joint-MLE over (lambda_0, alpha) at fixed beta wrapping
_hawkes_loglik_vectorized (the same canonical LL the LR statistic uses; Pattern F
preserved). The locked-v1 methodology called for tick gofit="likelihood", but the
C++ ModelHawkesExpKernLogLik kernel raises "The sum of the influence on someone
cannot be negative" at EVERY DECAY_GRID value, even with timestamp rescaling
(04.1.1-DIAGNOSTIC.md §1). tick.likelihood is therefore DEAD and removed from the
live path. On scipy failure across all multi-starts at every DECAY_GRID value,
fit_hawkes_expkern RAISES (BLOCKER per PRE_REGISTRATION §Phase 04.1.1 (v2)) — there
is NO silent least-squares fallback (LS is the broken estimator being retired). The
fit dict exposes fit_method_used so downstream lr_test / fit_report.json provenance
records the estimator that ran (always "scipy_canonical_ll" on the live path).
"""
from __future__ import annotations

import numpy as np
from tick.hawkes import HawkesExpKern

DECAY_GRID: tuple[float, ...] = (0.0001, 0.001, 0.01, 0.1, 1.0, 10.0)
BOUNDARY_WARNING_TOLERANCE: float = 0.05
# Free parameter count for AIC: baseline (2) + adjacency (4) + decay (1) = 7
_K_PARAMS: int = 7
# Locked-intent gofit (PRE_REGISTRATION + RESEARCH §Standard Stack); runtime falls back if broken.
_GOFIT_PRIMARY: str = "likelihood"
# _GOFIT_FALLBACK retained for grep-discoverability of the pre-04.1.1 fallback
# name; LIVE code path removed per Plan 04.1.1-00 PRE_REGISTRATION §Phase 04.1.1
# lock (BLOCKER on double-failure; no silent LS reintroduction).
_GOFIT_FALLBACK: str = "least-squares"
_PENALTY: str = "none"


def compute_branching_ratio(adjacency: np.ndarray, decays: float) -> float:
    """Spectral radius of (adjacency / decays) for scalar beta.

    Branching ratio eta = max |eigenvalue(alpha / beta)|. NOT max(alpha) (Pitfall 6).
    For univariate Hawkes the two coincide, but for the bivariate case the univariate
    intuition leaks and produces spurious eta values that ignore cross-leg structure.
    """
    adjacency = np.asarray(adjacency, dtype=np.float64)
    if adjacency.shape != (2, 2):
        raise ValueError(f"Expected 2x2 adjacency, got shape {adjacency.shape}")
    kernel_integral = adjacency / float(decays)
    eigvals = np.linalg.eigvals(kernel_integral)
    return float(np.max(np.abs(eigvals)))


def _reject_nonstationary(adjacency: np.ndarray, decays: float) -> float:
    """Stationarity guard for the scipy canonical MLE (Plan 04.1.1-02c, NEEDS WORK #2a).

    Returns the +inf-class penalty 1e18 if rho(alpha/beta) >= 1 (the non-stationary /
    explosive region), else 0.0. Wired into `_fit_with_scipy_canonical_ll.neg_ll` BEFORE
    the LL computation so the optimizer cannot evaluate or settle in the explosive region.

    This ENFORCES the pre-registered §Kernel Forms condition ||alpha/beta||_inf < 1
    (PRE_REGISTRATION §Phase 04.1.1 (v2) §02c). It is NOT a new gate criterion — the
    existing `stationary` gate input is reused; explosive fits are simply rejected at fit
    time so an artifactual eta >= 1 cannot pass the eta-floor gate.
    """
    if compute_branching_ratio(adjacency, float(decays)) >= 1.0:
        return 1e18
    return 0.0


def _fit_with_gofit(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    decays: float,
    gofit: str,
) -> "HawkesExpKern":
    """Construct + fit a HawkesExpKern at the requested gofit. Raises on solver failure.

    Phase 04.1.1-v2: retained for grep-discoverability of the tick interface; NOT on
    the live path (tick.likelihood removed — DIAGNOSTIC §1). Kept so the
    pre-registered estimator name remains codified and so a future tick fix can be
    wired back without re-introducing the symbol.

    Rescales to t=0-origin to keep tick's C++ optimizer in a well-conditioned regime.
    Hawkes LL is shift-invariant in absolute time: log(lambda) and integral both
    depend only on inter-event differences. Returned baseline + adjacency are
    unchanged in value (verified by test_full_offdiag + test_branching_ratio_spectral).
    Plan 04.1.1-00 PRE_REGISTRATION Phase 04.1.1 lock; tick-local, do NOT hoist
    (Pitfall 1 - premature DRY refactor would break residuals.parquet rescaled_dt
    timing in Phase 4 cross-correlogram).
    """
    t0 = float(min(leg_0_times.min(), leg_1_times.min()))
    leg_0_rs = (leg_0_times - t0).astype(np.float64)
    leg_1_rs = (leg_1_times - t0).astype(np.float64)
    learner = HawkesExpKern(
        decays=float(decays),
        gofit=gofit,
        penalty=_PENALTY,  # ProxPositive — preserves alpha >= 0 invariant
        solver="agd",
        max_iter=1000,
        tol=1e-7,
        verbose=False,
    )
    # tick accepts list[np.ndarray] of timestamp arrays — one per node.
    # Same-block ties handled natively (Pitfall 7 — NO logIndex tie-breaking).
    learner.fit([leg_0_rs, leg_1_rs])
    return learner


def _fit_with_scipy_canonical_ll(
    leg_0_rs: np.ndarray,
    leg_1_rs: np.ndarray,
    decays: float,
) -> dict:
    """Library-bug-isolated MLE: scipy.L-BFGS-B over (lambda_0[2], alpha[2,2]) at fixed beta.

    Wraps _hawkes_loglik_vectorized (the same closed-form LL trusted by the LR
    statistic - Pattern F canonical-LL contract preserved). Positivity enforced
    via per-parameter bounds (1e-12, None); stationarity enforced post-fit via
    boundary_warning. Multi-start over 3 initial points per Pitfall 7 (Hawkes
    LL is flat near optimum; single-start lands in sub-optimal basin).
    Pre-registered in Plan 04.1.1-00 PRE_REGISTRATION Phase 04.1.1 as Fallback A.
    """
    from scipy.optimize import minimize

    from .lr_test import _hawkes_loglik_vectorized

    T = float(max(leg_0_rs.max(), leg_1_rs.max()))
    lam0_emp = np.array(
        [max(leg_0_rs.size, 1) / T, max(leg_1_rs.size, 1) / T], dtype=np.float64
    )
    # Pitfall 7 multi-start: 3 initial points.
    starts = [
        (lam0_emp.copy(), np.full((2, 2), 0.01, dtype=np.float64)),
        (lam0_emp / 2.0, np.full((2, 2), 0.1, dtype=np.float64)),
        (lam0_emp / 4.0, np.full((2, 2), 0.3, dtype=np.float64)),
    ]

    def neg_ll(theta):
        lam0 = theta[:2]
        alpha = theta[2:].reshape(2, 2)
        # Plan 04.1.1-02c (NEEDS WORK #2a): reject the non-stationary region rho(alpha/beta)
        # >= 1 BEFORE the LL computation — enforces the pre-registered ||alpha/beta|| < 1
        # (§Kernel Forms). bounds stay (1e-12, None); this is the stationarity guard.
        penalty = _reject_nonstationary(alpha, float(decays))
        if penalty:
            return penalty
        ll = _hawkes_loglik_vectorized(
            lam0, alpha, float(decays), leg_0_rs, leg_1_rs
        )
        return -ll if np.isfinite(ll) else 1e18

    bounds = [(1e-12, None)] * 6
    best_result = None
    best_neg_ll = float("inf")
    for lam0_init, alpha_init in starts:
        theta0 = np.concatenate([lam0_init, alpha_init.ravel()])
        try:
            result = minimize(
                neg_ll,
                theta0,
                method="L-BFGS-B",
                bounds=bounds,
                options={"maxiter": 1000, "ftol": 1e-9},
            )
        except Exception:
            continue
        if result.success and float(result.fun) < best_neg_ll:
            best_neg_ll = float(result.fun)
            best_result = result
    if best_result is None:
        raise RuntimeError(
            "scipy L-BFGS-B failed across all 3 multi-start initial points"
        )
    lam0_hat = best_result.x[:2]
    alpha_hat = best_result.x[2:].reshape(2, 2)
    ll_hat = -float(best_result.fun)
    eta = compute_branching_ratio(alpha_hat, float(decays))
    aic = 2.0 * _K_PARAMS - 2.0 * ll_hat
    return {
        "baseline": lam0_hat.tolist(),
        "adjacency": alpha_hat.tolist(),
        "decays": float(decays),
        "branching_ratio": float(eta),
        "loglik_in_sample": ll_hat,
        "aic": float(aic),
        "boundary_warning": bool(
            eta < BOUNDARY_WARNING_TOLERANCE
            or eta > 1.0 - BOUNDARY_WARNING_TOLERANCE
        ),
        "fit_method_used": "scipy_canonical_ll",
    }


def _fit_at_decay(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    decays: float,
) -> dict:
    """Fit Hawkes at fixed decay via scipy_canonical_ll (PRIMARY).

    Phase 04.1.1-v2: tick.HawkesExpKern likelihood mode is DEAD — it raises
    "The sum of the influence on someone cannot be negative" at every decay,
    even with timestamp rescaling (04.1.1-DIAGNOSTIC.md §1). It is removed
    from the live path. The canonical estimator is scipy.L-BFGS-B over
    (lambda_0, alpha) wrapping _hawkes_loglik_vectorized (Pattern F
    canonical-LL preserved). On scipy failure across all multi-starts this
    RAISES (BLOCKER per PRE_REGISTRATION §Phase 04.1.1 (v2)); NO silent LS
    fallback (LS is the broken estimator being retired).
    """
    t0 = float(min(leg_0_times.min(), leg_1_times.min()))
    leg_0_rs = (leg_0_times - t0).astype(np.float64)
    leg_1_rs = (leg_1_times - t0).astype(np.float64)
    return _fit_with_scipy_canonical_ll(leg_0_rs, leg_1_rs, decays)


def fit_hawkes_expkern(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    decays: float | None = None,
) -> dict:
    """MLE fit via tick.HawkesExpKern. If decays is None, AIC-min over DECAY_GRID.

    Returns dict with:
      - baseline: list[float] shape (2,)
      - adjacency: list[list[float]] shape (2, 2) — full off-diagonal alpha matrix
      - decays: float (selected beta)
      - branching_ratio: float (spectral radius of alpha / beta)
      - loglik_in_sample: float
      - aic: float
      - boundary_warning: bool
      - fit_method_used: "scipy_canonical_ll" (the only live-path estimator as of
        Phase 04.1.1-v2; tick.likelihood removed, LS retired)
      - decay_aic_table: dict[str(decay) -> aic] (only when grid-searching)
    """
    if decays is not None:
        fit = _fit_at_decay(leg_0_times, leg_1_times, decays)
        fit["decay_aic_table"] = {str(decays): fit["aic"]}
        return fit

    candidates: list[dict] = []
    aic_table: dict[str, float] = {}
    for d in DECAY_GRID:
        try:
            cand = _fit_at_decay(leg_0_times, leg_1_times, d)
            candidates.append(cand)
            aic_table[str(d)] = cand["aic"]
        except Exception:
            # tick can throw on degenerate inputs at extreme decay values; mark inf and skip.
            aic_table[str(d)] = float("inf")
            continue

    if not candidates:
        raise RuntimeError("All decay grid candidates failed to fit")

    best = min(candidates, key=lambda c: c["aic"])
    best["decay_aic_table"] = aic_table
    return best


def fit_hawkes_with_fixed_branching_ratio(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    eta_target: float,
    decays: float,
) -> dict:
    """Constrained fit: spectral radius of alpha/beta = eta_target.

    Wave-1 spike implementation (projection trick): fit unconstrained, then rescale alpha
    to enforce the target spectral radius. Per RESEARCH §Open Questions Q1, this is the
    simpler path; scipy.optimize.minimize with an equality-constraint is the documented
    fallback if profile-likelihood values diverge meaningfully from a true constrained MLE
    (validated by Plan 03-06 cross-checking against an unconstrained refit at eta=eta_hat).

    Returns: dict with the same shape as fit_hawkes_expkern plus:
      - constraint_method: "projection"
      - achieved_branching_ratio: realized eta after projection
      - target_branching_ratio: requested eta
    """
    unconstrained = _fit_at_decay(leg_0_times, leg_1_times, decays)
    adjacency = np.asarray(unconstrained["adjacency"], dtype=np.float64)
    eta_current = unconstrained["branching_ratio"]
    if eta_current < 1e-12:
        # All alpha effectively 0; projection cannot scale up. Synthesize a uniform-alpha
        # stand-in that exactly realizes the target spectral radius (uniform 2x2 has
        # eigenvalues {2*c, 0}, so c = eta_target * decays / 2 for matrix entries c).
        # Caller (profile_likelihood) sees this as a degenerate edge case and is expected
        # to surface it via fit_report.json provenance.
        scaled_adjacency = np.full((2, 2), eta_target * decays / 2.0)
    else:
        scale = eta_target / eta_current
        scaled_adjacency = adjacency * scale
    # Recompute log-likelihood on the SCALED adjacency manually — tick exposes no
    # public re-score-with-params API, so use the closed-form Hawkes log-likelihood.
    baseline = np.asarray(unconstrained["baseline"], dtype=np.float64)
    loglik = _compute_hawkes_loglik_at_params(
        baseline, scaled_adjacency, decays, leg_0_times, leg_1_times,
    )
    eta_achieved = compute_branching_ratio(scaled_adjacency, decays)
    return {
        "baseline": baseline.tolist(),
        "adjacency": scaled_adjacency.tolist(),
        "decays": float(decays),
        "branching_ratio": eta_achieved,
        "loglik_in_sample": float(loglik),
        "aic": float(2.0 * _K_PARAMS - 2.0 * loglik),
        "boundary_warning": bool(
            eta_achieved < BOUNDARY_WARNING_TOLERANCE
            or eta_achieved > 1.0 - BOUNDARY_WARNING_TOLERANCE
        ),
        "constraint_method": "projection",
        "achieved_branching_ratio": float(eta_achieved),
        "target_branching_ratio": float(eta_target),
        "fit_method_used": unconstrained["fit_method_used"],
    }


def _compute_hawkes_loglik_at_params(
    baseline: np.ndarray,
    adjacency: np.ndarray,
    decays: float,
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
) -> float:
    """Standard Hawkes log-likelihood: sum_i log(lambda(t_i)) - integral_0^T lambda(t) dt.

    Closed-form integral for exponential kernel:
      integral_0^T lambda_i(t) dt = mu_i * T
        + sum_j sum_{k: t_jk < T} alpha_ij * (1 - exp(-beta (T - t_jk))) / beta
    """
    legs = [leg_0_times, leg_1_times]
    if not all(arr.size > 0 for arr in legs):
        return float("-inf")
    T_end = float(max(legs[0].max(), legs[1].max()))
    log_intensity_sum = 0.0
    for i, leg_i in enumerate(legs):
        for t in leg_i:
            lam_it = baseline[i]
            for j, leg_j in enumerate(legs):
                hist = leg_j[leg_j < t]
                if hist.size > 0:
                    lam_it += adjacency[i, j] * np.sum(np.exp(-decays * (t - hist)))
            if lam_it <= 0.0:
                return float("-inf")
            log_intensity_sum += np.log(lam_it)
    integral = 0.0
    for i in range(2):
        integral += baseline[i] * T_end
        for j in range(2):
            hist = legs[j][legs[j] < T_end]
            integral += (
                adjacency[i, j] * np.sum(1.0 - np.exp(-decays * (T_end - hist))) / decays
            )
    return float(log_intensity_sum - integral)
