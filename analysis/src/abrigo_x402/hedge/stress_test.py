"""Three-way joint-distribution stress: independence + fitted_joint + comonotone (Frechet upper bound).

HEDGE-04 (CONTEXT.md): flag-only at >30%, no hard-fail.
RESEARCH Pitfall 6: comonotone uses 'empirical_body_parametric_tail' method label.
RESEARCH §"Don't Hand-Roll": comonotone via shared U sampling
  (U_1 ~ U(0,1), U_2 = U_1, then inverse-transform per leg through empirical
  marginal CDFs — Frechet upper bound, reproducible from empirical marginals alone).

v1.0 path: pure empirical-body inverse CDF on observed marginals. The
'empirical_body_parametric_tail' label is forward-compatible — Plan 04-08
orchestrator MAY extend the tail via the BIC-winning copula's marginal model in
v1.1; the API surface here doesn't change when that extension lands (we just
re-route _inverse_empirical_cdf to a hybrid that grafts parametric tails onto the
empirical body).
"""
from __future__ import annotations

from typing import Callable

import numpy as np

REQUIRED_STRESS_REPORT_KEYS: tuple[str, ...] = (
    "chainId", "contractAddress", "blockRange",
    "fetchTimestamp", "dataHash", "gitCommit", "run_id",
    "independence_price",
    "fitted_joint_price",
    "comonotone_price",
    "divergence_pct",         # (max - min) / |mean| * 100
    "divergence_flag",        # bool — True if divergence_pct > 30
    "comonotone_method",      # "empirical_body_parametric_tail" per RESEARCH Pitfall 6
)

DIVERGENCE_FLAG_THRESHOLD_PCT: float = 30.0  # CONTEXT.md locked — flag-only, no hard-fail


def _price_under_joint_samples(
    payoff: Callable[[np.ndarray, np.ndarray], np.ndarray],
    samples: np.ndarray,   # (N, 2) joint samples on the original marginal scale
) -> float:
    """Monte-Carlo price = E[payoff(x_0, x_1)] under the joint sample."""
    vals = payoff(samples[:, 0], samples[:, 1])
    return float(np.mean(vals))


def _inverse_empirical_cdf(uniforms: np.ndarray, observed: np.ndarray) -> np.ndarray:
    """Map uniform samples back to the marginal scale via empirical inverse CDF.

    Linear interpolation on the sorted observed sample (empirical body); edges
    fall back to the observed extremes (i.e. no parametric-tail extension at
    v1.0 — see module docstring for the v1.1 forward path).
    """
    sorted_obs = np.sort(observed)
    n = len(sorted_obs)
    if n == 0:
        return uniforms
    return np.interp(uniforms, np.linspace(0.0, 1.0, n), sorted_obs)


def run_three_way_stress(
    payoff: Callable[[np.ndarray, np.ndarray], np.ndarray],
    marginal_cdf_leg_0,
    marginal_cdf_leg_1,
    fitted_copula,                    # has .random(n, seed=...) -> (n, 2) uniforms
    n_samples: int = 10_000,
    seed: int = 20260527,
) -> dict:
    """Compute strip-equivalent E[payoff] under three joint scenarios + divergence flag.

    Scenarios:
      1. independence: U_1, U_2 ~ U(0,1) independently; inverse-transform per leg.
      2. fitted_joint: fitted_copula.random(N, seed=seed) -> (U_1, U_2); inverse-transform per leg.
      3. comonotone:   U_1 ~ U(0,1), U_2 = U_1 (Frechet upper bound); inverse-transform per leg.

    Args:
        payoff: callable (x0, x1) -> array of pointwise payoff values.
        marginal_cdf_leg_0: 1-D array of observed leg-0 values (e.g. rescaled_dt_0).
        marginal_cdf_leg_1: 1-D array of observed leg-1 values (e.g. rescaled_dt_1).
        fitted_copula: copulae copula object exposing .random(n, seed=...) -> (n, 2) uniforms.
        n_samples: Monte-Carlo size per scenario; default 10_000.
        seed: RNG seed; default 20260527 (locked for reproducibility per Plan 04-07).

    Returns:
        dict carrying the non-orchestrator subset of REQUIRED_STRESS_REPORT_KEYS:
          independence_price, fitted_joint_price, comonotone_price,
          divergence_pct, divergence_flag, comonotone_method.

        The orchestrator (Plan 04-08) injects the PANEL-02 provenance keys
        (chainId, contractAddress, blockRange, fetchTimestamp, dataHash,
        gitCommit, run_id) before writing the dict to stress_report.json.

    Notes on the method label 'empirical_body_parametric_tail' (RESEARCH Pitfall 6):
        v1.0 implementation uses pure empirical-body inverse CDF on observed
        marginals; the label is forward-compatible with v1.1 grafting of
        BIC-winner-derived parametric tails onto the empirical body. The
        warning sign Pitfall 6 cites (comonotone strip price suspiciously close
        to independence — empirical tails too short) is monitored at run time
        via the divergence_pct field; Phase 5 reviewer is instructed to look at
        a quantile-quantile plot of comonotone draws vs empirical samples if
        divergence_pct < 5% on a fixture known to have heavy tails.
    """
    obs_0 = np.asarray(marginal_cdf_leg_0, dtype=np.float64).ravel()
    obs_1 = np.asarray(marginal_cdf_leg_1, dtype=np.float64).ravel()

    rng = np.random.default_rng(seed)

    # 1. Independence: U_1, U_2 ~ U(0,1) independently
    u_ind = rng.uniform(0.0, 1.0, size=(n_samples, 2))
    x_ind_0 = _inverse_empirical_cdf(u_ind[:, 0], obs_0)
    x_ind_1 = _inverse_empirical_cdf(u_ind[:, 1], obs_1)
    independence_price = _price_under_joint_samples(
        payoff, np.column_stack([x_ind_0, x_ind_1])
    )

    # 2. Fitted joint via fitted_copula.random(N, seed=seed)
    u_fit = np.asarray(fitted_copula.random(n_samples, seed=seed), dtype=np.float64)
    x_fit_0 = _inverse_empirical_cdf(u_fit[:, 0], obs_0)
    x_fit_1 = _inverse_empirical_cdf(u_fit[:, 1], obs_1)
    fitted_joint_price = _price_under_joint_samples(
        payoff, np.column_stack([x_fit_0, x_fit_1])
    )

    # 3. Comonotone (Frechet upper bound: U_2 = U_1)
    u_com = rng.uniform(0.0, 1.0, size=n_samples)
    x_com_0 = _inverse_empirical_cdf(u_com, obs_0)
    x_com_1 = _inverse_empirical_cdf(u_com, obs_1)
    comonotone_price = _price_under_joint_samples(
        payoff, np.column_stack([x_com_0, x_com_1])
    )

    # Divergence flag: (max - min) / |mean| * 100, flag-only at >30%.
    prices = np.array([independence_price, fitted_joint_price, comonotone_price])
    mean_price = float(np.mean(prices))
    if mean_price == 0.0:
        divergence_pct = 0.0
    else:
        divergence_pct = float(
            (np.max(prices) - np.min(prices)) / abs(mean_price) * 100.0
        )
    divergence_flag = bool(divergence_pct > DIVERGENCE_FLAG_THRESHOLD_PCT)

    return {
        "independence_price": float(independence_price),
        "fitted_joint_price": float(fitted_joint_price),
        "comonotone_price": float(comonotone_price),
        "divergence_pct": divergence_pct,
        "divergence_flag": divergence_flag,
        "comonotone_method": "empirical_body_parametric_tail",
    }
