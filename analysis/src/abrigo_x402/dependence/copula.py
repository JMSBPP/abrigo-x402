"""5-family BIC menu (Gaussian + t + Clayton + Frank + Gumbel) via copulae==0.8.0.

Vine fallback via pyvinecopulib==0.7.6 ONLY if ΔBIC >= 5 in favor of vine (deferred install
per RESEARCH Open Question 3; install in a v1.1 follow-up plan if empirical fit triggers it).
"""
import numpy as np

REQUIRED_JOINT_DIST_KEYS: tuple[str, ...] = (
    "chainId", "contractAddress", "blockRange",
    "fetchTimestamp", "dataHash", "gitCommit", "run_id",
    "cross_correlogram",   # {lags: [...], values: [...]}
    "permutation_null",    # {n_reps: int, p_value: float, max_abs_rho_observed: float}
    "empirical_copula",    # {family, params, bic, all_candidates_bic: {gaussian, t, clayton, frank, gumbel}}
    "vine_fallback_used",  # bool
)

VINE_FALLBACK_DELTA_BIC_THRESHOLD: float = 5.0  # CONTEXT.md locked


def _pit_with_clipping(x: np.ndarray, eps: float = 1e-10) -> np.ndarray:
    """Probability Integral Transform with boundary clipping.

    Returns the empirical CDF of `x` clipped away from {0, 1} by `eps` to prevent
    Archimedean log-likelihood blow-ups (iter-3 fix). Clayton/Frank/Gumbel generators
    have singularities at the boundary; clipping is mandatory before MLE.
    """
    raise NotImplementedError("Plan 04-03 implements DEPEND-01 PIT + 5-family BIC ranking")


def fit_5_families_bic(u_data: np.ndarray) -> dict:
    """Fit Gaussian + Student-t + Clayton + Frank + Gumbel copulae on PIT-uniform (N,2) data.

    Returns: {winner: str, all_candidates: {family: {params, log_lik, bic}}, vine_fallback_used: bool}.
    BIC = -2 * log_lik + k * log(n). Winner = argmin(bic).
    vine_fallback_used: only True if a vine pair-copula construction yields bic <= bivariate_bic_min - 5
    (per PITFALLS Pitfall 2 — vine library defer per RESEARCH Open Question 3).
    """
    raise NotImplementedError("Plan 04-03 implements DEPEND-01 5-family BIC ranking")
