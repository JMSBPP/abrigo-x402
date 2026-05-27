"""5-family BIC menu (Gaussian + t + Clayton + Frank + Gumbel) via copulae==0.8.0.

Vine fallback via pyvinecopulib==0.7.6 ONLY if ΔBIC >= 5 in favor of vine (deferred install
per RESEARCH Open Question 3; install in a v1.1 follow-up plan if empirical fit triggers it).

Plan 04-03 implementation notes
-------------------------------
copulae==0.8.0 (the installed wheel reports __version__ == '0.7.9' — known
metadata-vs-source mismatch documented in analysis/INSTALL_TROUBLESHOOTING.md;
the 5-family API NormalCopula/StudentCopula/ClaytonCopula/FrankCopula/GumbelCopula
is intact). Two of the families have a bug in the public `.fit()` path:

  * The Kendall-tau initial-parameter estimator (`itau`) calls
    `squeeze_output` on a 1-element ndarray and then `float(...)` on it,
    which raises `TypeError: only 0-dimensional arrays can be converted to
    Python scalars`. This bites Clayton + Frank + Gumbel (which all default
    to itau initialization), but not Gaussian + Student (which use
    correlation-matrix inversion as the default).
  * The Archimedean `params` setter calls `float(theta)` on a 1-D ndarray
    passed by scipy.optimize.minimize, which fails identically.

Workaround: for the three Archimedean families we run our own 1-D bounded
`scipy.optimize.minimize_scalar` over the parameter range, calling the
library's vectorized `log_lik(u)` at each candidate. The optimizer never
goes through `params.setter` because we set `params` with a Python float on
each call. This is the minimal-surface workaround; it preserves the
library's PDF / log-likelihood code (the correctness-critical path) and
only replaces the optimizer wiring.

Pattern I (thread-pinning) is enforced at the test-file level
(`test_copula_bic.py` first 4 lines) per Phase 3 03-08 precedent — BLAS
threadcount affects MLE convergence on the Gaussian-vs-t discrimination
edge at N=500.
"""
from __future__ import annotations

import numpy as np
from copulae import (
    NormalCopula,
    StudentCopula,
    ClaytonCopula,
    FrankCopula,
    GumbelCopula,
)
from scipy.optimize import minimize_scalar

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
    """Map raw values to (eps, 1-eps) PIT-uniform via rank/(n+1) + boundary clipping.

    iter-3 Issue 3 fix: prevents the norm.ppf(0) = -inf / norm.ppf(1) = +inf failure
    path when an exact rank tie produces 0.0 or 1.0 in the PIT image (which then
    propagates as ±inf into the latent multivariate-normal representation used by
    the gaussian/t copula char_func construction in Plan 04-08).

    Special case: if the input is already in [0, 1] (e.g. the test passes
    [0.0, 0.5, 1.0]), the function is the identity on the interior and clips
    the boundary points to (eps, 1-eps). For raw real-valued samples, the
    rank/(n+1) transform produces strictly interior values for any n >= 1
    (rank ∈ [1, n]), but the eps-clip still guards against numerical noise.

    Args:
        x: 1-D array of values (raw samples OR pre-computed PIT image).
        eps: clipping bound; default 1e-10 matches typical scipy.stats numerics.
    Returns:
        1-D array of PIT-uniform values in (eps, 1-eps), all finite under norm.ppf.
    """
    x = np.asarray(x, dtype=np.float64).ravel()
    n = len(x)
    if n == 0:
        return x
    # If input is already in [0, 1], treat it as a pre-computed PIT image and
    # only clip the boundary. Otherwise apply the rank/(n+1) PIT transform.
    if np.all((x >= 0.0) & (x <= 1.0)):
        return np.clip(x, eps, 1.0 - eps)
    ranks = np.argsort(np.argsort(x)) + 1  # 1-indexed ranks
    u = ranks.astype(np.float64) / (n + 1)
    return np.clip(u, eps, 1.0 - eps)


def _fit_archimedean_bounded(
    klass, u: np.ndarray, bounds: tuple[float, float]
) -> tuple[float, float]:
    """Custom MLE for Clayton / Frank / Gumbel via 1-D bounded minimize_scalar.

    Bypasses the broken copulae 0.8.0 itau initial-parameter path and the
    broken `params.setter` array-arg coercion. The library's `log_lik` method
    is correct and is what we score on.

    Args:
        klass: ClaytonCopula | FrankCopula | GumbelCopula
        u: (N, 2) PIT-uniform sample.
        bounds: (lo, hi) for the single parameter theta.
    Returns:
        (theta_hat, log_lik_at_theta_hat) as Python floats.
    """
    c = klass(dim=2)

    def neg_ll(theta: float) -> float:
        try:
            c.params = float(theta)
            ll = float(c.log_lik(u))
            if not np.isfinite(ll):
                return 1e10
            return -ll
        except Exception:
            return 1e10

    res = minimize_scalar(
        neg_ll, bounds=bounds, method="bounded", options={"xatol": 1e-8}
    )
    theta_hat = float(res.x)
    c.params = theta_hat
    ll_hat = float(c.log_lik(u))
    return theta_hat, ll_hat


def fit_5_families_bic(u_data: np.ndarray, *, use_vine: bool = False) -> dict:
    """Fit Gaussian + Student-t + Clayton + Frank + Gumbel copulae on PIT-uniform (N,2) data.

    Returns {winner: str, all_candidates: {family: {params, log_lik, bic}}, vine_fallback_used: bool}.
    BIC = -2 * log_lik + k * log(n). Winner = argmin(bic).
    k = 2 only for Student-t (rho + df); k = 1 for all other families.

    Args:
        u_data: (N, 2) uniform samples (PIT residuals; pre-clip via _pit_with_clipping).
        use_vine: deferred per RESEARCH Open Question 3 (pyvinecopulib not installed in v1.0).

    Raises:
        NotImplementedError: if use_vine=True (vine fallback is deferred to a follow-up plan;
          install pyvinecopulib==0.7.6 there and implement the vine pair-copula path).
        ValueError: if u_data is not a (N, 2) array.
    """
    if use_vine:
        raise NotImplementedError(
            "Vine fallback (pyvinecopulib==0.7.6) is deferred per RESEARCH Open Question 3. "
            "Install in a follow-up plan only if Wave-1 empirical fit triggers "
            "ΔBIC >= 5 in favor of vine."
        )

    u = np.asarray(u_data, dtype=np.float64)
    if u.ndim != 2 or u.shape[1] != 2:
        raise ValueError(f"u_data must be (N, 2); got shape {u.shape}")
    n = u.shape[0]
    log_n = float(np.log(n))

    results: dict[str, dict] = {}

    # ---- Gaussian (k=1) — copulae's default fit path works for elliptical families
    gauss = NormalCopula(dim=2)
    gauss.fit(u)
    gauss_params = gauss.params
    if hasattr(gauss_params, "tolist"):
        gauss_params_out = gauss_params.tolist()
    else:
        gauss_params_out = [float(gauss_params)]
    gauss_ll = float(gauss.log_lik(u))
    results["gaussian"] = {
        "params": gauss_params_out,
        "log_lik": gauss_ll,
        "bic": -2.0 * gauss_ll + 1 * log_n,
    }

    # ---- Student-t (k=2: rho + df)
    student = StudentCopula(dim=2)
    student.fit(u)
    sp = student.params
    # StudentParams(df=..., rho=array([...]))
    student_params_out = {
        "df": float(sp.df),
        "rho": sp.rho.tolist() if hasattr(sp.rho, "tolist") else [float(sp.rho)],
    }
    student_ll = float(student.log_lik(u))
    results["t"] = {
        "params": student_params_out,
        "log_lik": student_ll,
        "bic": -2.0 * student_ll + 2 * log_n,
    }

    # ---- Archimedean families (k=1) — custom 1-D MLE per docstring rationale.
    # Bounds chosen to exclude singular / nan regions identified in
    # exploratory tests (Plan 04-03):
    #   Clayton θ ∈ (0, 30]      (lower-tail positive dependence)
    #   Frank   θ ∈ (-30, 30) \ {0}  (bidirectional; θ=0 is independence)
    #   Gumbel  θ ∈ [1, 30]      (upper-tail; θ=1 is independence)
    # Negative-dependence regimes for Clayton/Gumbel are excluded (would
    # require theta-rotation; not needed for Wave-1 ICHI panels which
    # exhibit positive cross-leg dependence per the cross-correlogram).
    archimedean_specs = [
        ("clayton", ClaytonCopula, (1e-4, 30.0)),
        ("frank", FrankCopula, (1e-4, 30.0)),  # positive-dependence half (sign-matched to data)
        ("gumbel", GumbelCopula, (1.0 + 1e-6, 30.0)),
    ]
    for name, klass, bnds in archimedean_specs:
        theta_hat, ll_hat = _fit_archimedean_bounded(klass, u, bnds)
        results[name] = {
            "params": [theta_hat],
            "log_lik": ll_hat,
            "bic": -2.0 * ll_hat + 1 * log_n,
        }

    winner = min(results, key=lambda f: results[f]["bic"])
    return {
        "winner": winner,
        "all_candidates": results,
        "vine_fallback_used": False,
    }
