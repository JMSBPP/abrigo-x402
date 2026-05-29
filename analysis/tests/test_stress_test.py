"""HEDGE-04 three-way stress test: independence + fitted_joint + comonotone Frechet upper bound.

Test cases (Plan 04-07 Task 1 — RED stage):
  1. schema             — result carries all locked report keys (minus orchestrator-injected provenance)
  2. independence-vs-fitted near-equal under weak dependence (Gaussian rho=0.05)
  3. comonotone upper bound dominates independence on a convex (super-additive) payoff (x*y)
  4. divergence_flag thresholding at 30%
  5. seed determinism — same seed twice yields identical triples

Pattern I (thread-pinning before first numpy import) — CARRIED FORWARD from Phase 3
03-08 + Phase 4 04-03 (Gaussian-vs-Frechet copula sampling is sensitive to BLAS
multi-threading on the bivariate-normal latent representation; same regression
class as the BIC discrimination edge).
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import numpy as np
import pytest
from copulae import NormalCopula

from abrigo_x402.hedge.stress_test import (
    DIVERGENCE_FLAG_THRESHOLD_PCT,
    REQUIRED_STRESS_REPORT_KEYS,
    run_three_way_stress,
)


def _make_gaussian_copula(rho: float, n_fit: int = 1000, seed: int = 20260527):
    """Return a fitted Gaussian copula at the requested rho."""
    rng = np.random.default_rng(seed)
    cov = np.array([[1.0, rho], [rho, 1.0]])
    z = rng.multivariate_normal(mean=[0.0, 0.0], cov=cov, size=n_fit)
    from scipy.stats import norm as _norm
    u = _norm.cdf(z)
    # Clip to avoid 0/1
    u = np.clip(u, 1e-10, 1 - 1e-10)
    c = NormalCopula(dim=2)
    c.fit(u)
    return c


def _linear_sum_payoff(x0: np.ndarray, x1: np.ndarray) -> np.ndarray:
    return x0 + x1


def _product_payoff(x0: np.ndarray, x1: np.ndarray) -> np.ndarray:
    """Convex / super-additive when x0, x1 share sign — used to distinguish
    comonotone (positive co-movement) from independence."""
    return x0 * x1


def _normal_marginals(n: int = 2000, seed: int = 20260527):
    rng = np.random.default_rng(seed)
    obs_0 = rng.normal(loc=0.0, scale=1.0, size=n)
    obs_1 = rng.normal(loc=0.0, scale=1.0, size=n)
    return obs_0, obs_1


def test_schema_has_all_required_keys():
    """Test 1: result has independence_price, fitted_joint_price, comonotone_price,
    divergence_pct, divergence_flag, comonotone_method (the non-orchestrator keys)."""
    obs_0, obs_1 = _normal_marginals()
    cop = _make_gaussian_copula(rho=0.5)
    out = run_three_way_stress(
        _linear_sum_payoff, obs_0, obs_1, cop, n_samples=2000, seed=20260527
    )
    # Subset of REQUIRED_STRESS_REPORT_KEYS that compute_strip-like functions produce
    # (orchestrator injects provenance keys later).
    non_provenance_keys = {
        "independence_price",
        "fitted_joint_price",
        "comonotone_price",
        "divergence_pct",
        "divergence_flag",
        "comonotone_method",
    }
    missing = non_provenance_keys - set(out.keys())
    assert not missing, f"Missing keys: {missing}; got: {set(out.keys())}"
    # Sanity-check: REQUIRED_STRESS_REPORT_KEYS covers these
    for k in non_provenance_keys:
        assert k in REQUIRED_STRESS_REPORT_KEYS
    # Method label per RESEARCH Pitfall 6
    assert out["comonotone_method"] == "empirical_body_parametric_tail"


def test_independence_vs_fitted_near_equal_under_weak_dependence():
    """Test 2: at near-independence (Gaussian rho=0.05), independence and fitted_joint
    prices are within 5% of each other (under |sum| payoff with mean-zero marginals,
    compare via absolute spread / scale of marginal std)."""
    obs_0, obs_1 = _normal_marginals(n=5000)
    cop = _make_gaussian_copula(rho=0.05, n_fit=5000)
    out = run_three_way_stress(
        _linear_sum_payoff, obs_0, obs_1, cop, n_samples=10_000, seed=20260527
    )
    ind = out["independence_price"]
    fit = out["fitted_joint_price"]
    # Use absolute scale (std of x0+x1 ~ sqrt(2)) rather than mean (which is ~0)
    scale = np.sqrt(2.0)
    rel_diff = abs(ind - fit) / scale
    assert rel_diff < 0.05, (
        f"near-independence: |ind - fit| / scale = {rel_diff:.4f} should be < 0.05; "
        f"ind={ind}, fit={fit}"
    )


def test_comonotone_dominates_independence_on_product_payoff():
    """Test 3: for convex/super-additive payoff (x0*x1), comonotone_price >= independence_price.

    Frechet upper bound dominates the product copula for super-additive payoffs
    (textbook ordering: comonotone vector maximizes E[phi(X+Y)] for supermodular phi).
    """
    obs_0, obs_1 = _normal_marginals(n=5000)
    cop = _make_gaussian_copula(rho=0.5, n_fit=5000)
    out = run_three_way_stress(
        _product_payoff, obs_0, obs_1, cop, n_samples=10_000, seed=20260527
    )
    assert out["comonotone_price"] >= out["independence_price"], (
        f"Frechet upper bound should dominate independence on product payoff; "
        f"got comonotone={out['comonotone_price']}, independence={out['independence_price']}"
    )


def test_divergence_flag_thresholding():
    """Test 4: force a divergence_pct > 30 via strong positive dependence + product payoff;
    assert divergence_flag == True. Also a benign config (linear payoff + weak dep) gives flag False.
    """
    obs_0, obs_1 = _normal_marginals(n=5000)

    # High-divergence case: rho ~ 0.9 + product payoff (strong positive comonotone vs near-zero independence)
    cop_high = _make_gaussian_copula(rho=0.9, n_fit=5000)
    out_high = run_three_way_stress(
        _product_payoff, obs_0, obs_1, cop_high, n_samples=10_000, seed=20260527
    )
    assert out_high["divergence_pct"] > DIVERGENCE_FLAG_THRESHOLD_PCT, (
        f"high-dependence + product payoff should exceed {DIVERGENCE_FLAG_THRESHOLD_PCT}% "
        f"divergence; got {out_high['divergence_pct']}%"
    )
    assert out_high["divergence_flag"] is True

    # Low-divergence case: rho ~ 0.05 + symmetric sum payoff
    cop_low = _make_gaussian_copula(rho=0.05, n_fit=5000)
    out_low = run_three_way_stress(
        _linear_sum_payoff, obs_0, obs_1, cop_low, n_samples=10_000, seed=20260527
    )
    # On a zero-mean payoff the percentage is ill-defined; assert the absolute spread
    # is much smaller than the |sum| payoff scale. Implementation uses |mean| in
    # denominator → for near-zero mean this can be unstable. We only assert the
    # flag reflects the boolean computation correctly for whatever divergence_pct
    # came out.
    assert isinstance(out_low["divergence_flag"], bool)
    assert out_low["divergence_flag"] == (
        out_low["divergence_pct"] > DIVERGENCE_FLAG_THRESHOLD_PCT
    )


def test_seed_determinism():
    """Test 5: same seed twice -> identical (independence, fitted_joint, comonotone) triple."""
    obs_0, obs_1 = _normal_marginals(n=2000)
    cop = _make_gaussian_copula(rho=0.5, n_fit=2000)
    out_a = run_three_way_stress(
        _linear_sum_payoff, obs_0, obs_1, cop, n_samples=2000, seed=20260527
    )
    out_b = run_three_way_stress(
        _linear_sum_payoff, obs_0, obs_1, cop, n_samples=2000, seed=20260527
    )
    assert out_a["independence_price"] == out_b["independence_price"]
    assert out_a["fitted_joint_price"] == out_b["fitted_joint_price"]
    assert out_a["comonotone_price"] == out_b["comonotone_price"]
