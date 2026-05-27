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
The locked methodology calls for gofit="likelihood" (RESEARCH §Standard Stack), but the C++
ModelHawkesExpKernLogLik kernel raises "The sum of the influence on someone cannot be negative"
during MLE optimization on tick 0.8.0.2 under Python 3.13 / numpy 2.x. The code requests the
MLE path first (preserving the PRE_REGISTRATION intent + grep-gate codification) and falls back
to gofit="least-squares" — also penalty="none" → ProxPositive — when MLE init fails. The fit
dict exposes fit_method_used so downstream lr_test / fit_report.json provenance records which
estimator actually ran. Least-squares biases eta downward (RESEARCH §Standard Stack), which only
strengthens — never weakens — the four-criterion gate's eta >= 0.2 discipline (PRE_REGISTRATION).
"""
from __future__ import annotations

import numpy as np
from tick.hawkes import HawkesExpKern

DECAY_GRID: tuple[float, ...] = (0.01, 0.1, 1.0, 10.0)
BOUNDARY_WARNING_TOLERANCE: float = 0.05
# Free parameter count for AIC: baseline (2) + adjacency (4) + decay (1) = 7
_K_PARAMS: int = 7
# Locked-intent gofit (PRE_REGISTRATION + RESEARCH §Standard Stack); runtime falls back if broken.
_GOFIT_PRIMARY: str = "likelihood"
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


def _fit_with_gofit(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    decays: float,
    gofit: str,
) -> "HawkesExpKern":
    """Construct + fit a HawkesExpKern at the requested gofit. Raises on solver failure."""
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
    learner.fit([leg_0_times, leg_1_times])
    return learner


def _fit_at_decay(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    decays: float,
) -> dict:
    """Fit tick.HawkesExpKern at a single decay value and assemble a fit dict.

    Tries gofit="likelihood" first (PRE_REGISTRATION intent), falls back to
    gofit="least-squares" if MLE solver init fails. Records which estimator
    actually ran in fit_method_used so downstream provenance is honest.
    """
    fit_method_used = _GOFIT_PRIMARY
    try:
        learner = _fit_with_gofit(leg_0_times, leg_1_times, decays, gofit=_GOFIT_PRIMARY)
    except RuntimeError:
        # tick 0.8.0.2 ModelHawkesExpKernLogLik C++ kernel raises during MLE init under
        # Python 3.13 / numpy 2.x (known upstream issue). Fall back to least-squares,
        # which biases eta downward (conservative for the four-criterion gate).
        learner = _fit_with_gofit(leg_0_times, leg_1_times, decays, gofit=_GOFIT_FALLBACK)
        fit_method_used = _GOFIT_FALLBACK

    baseline = np.asarray(learner.baseline, dtype=np.float64)  # shape (2,)
    adjacency = np.asarray(learner.adjacency, dtype=np.float64)  # shape (2, 2)
    loglik = float(learner.score())
    eta = compute_branching_ratio(adjacency, decays)
    aic = 2.0 * _K_PARAMS - 2.0 * loglik

    boundary_warning = bool(
        eta < BOUNDARY_WARNING_TOLERANCE or eta > 1.0 - BOUNDARY_WARNING_TOLERANCE
    )

    return {
        "baseline": baseline.tolist(),
        "adjacency": adjacency.tolist(),
        "decays": float(decays),
        "branching_ratio": eta,
        "loglik_in_sample": loglik,
        "aic": float(aic),
        "boundary_warning": boundary_warning,
        "fit_method_used": fit_method_used,
    }


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
      - fit_method_used: "likelihood" | "least-squares"
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
