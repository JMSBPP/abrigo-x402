"""DEPEND-01 permutation null for max|rho(h)| — within-window shuffle of leg_1 rescaled_dt.

Per PRE_REGISTRATION §Test Statistics: 1000-rep convention (test override n_reps=200/500).
Per PITFALLS §4: substrate is rescaled_dt (NOT raw timestamps).
"""
import numpy as np
import polars as pl
import pytest
from pathlib import Path

from abrigo_x402.dependence.permutation_null import permutation_null_max_abs_rho

FIXTURES = Path(__file__).parent / "fixtures"


def test_schema_keys():
    rng = np.random.default_rng(20260527)
    leg_0 = rng.exponential(scale=1.0, size=300)
    leg_1 = rng.exponential(scale=1.0, size=300)
    result = permutation_null_max_abs_rho(leg_0, leg_1, max_lag=50, n_reps=200, seed=20260527)
    assert set(result.keys()) == {
        "n_reps",
        "p_value",
        "max_abs_rho_observed",
        "max_abs_rho_null_dist",
    }
    assert result["n_reps"] == 200
    assert len(result["max_abs_rho_null_dist"]) == 200
    assert 0.0 <= result["p_value"] <= 1.0


def test_size_independence_cannot_reject():
    rng = np.random.default_rng(42)
    leg_0 = rng.exponential(scale=1.0, size=500)
    leg_1 = rng.exponential(scale=1.0, size=500)
    result = permutation_null_max_abs_rho(leg_0, leg_1, max_lag=50, n_reps=500, seed=20260527)
    assert result["p_value"] >= 0.10


def test_power_cross_excitation():
    """Strong-coupling synthetic substrate yields a permutation p-value
    rejecting independence at alpha=0.05.

    Why NOT the synthetic_hawkes_eta_05.parquet fixture in this test (unlike
    Plan 04-01's positive control): the locked Phase-3 fixture uses balanced-
    symmetric adjacency [[0.025,0.025],[0.025,0.025]] which produces a *diffuse*
    cross-leg signal in event-index rescaled-dt space — observed max|rho(h)|
    ≈ 0.118 across 101 lags sits AT the 2/sqrt(n)≈0.11 multi-lag noise floor
    for n≈350, so a max-over-lags permutation null centers around 0.14 (the
    multiple-comparisons noise floor) and the test under-detects. This is the
    expected statistical truth on a weak/diffuse positive-control fixture, not
    a permutation-test bug — confirmed via 50-rep diagnostic during Plan 04-02
    execution.

    To validate the function's POWER, this test uses an inline strong-coupling
    construction (leg_1 = sqrt(1-rho^2)*indep + rho*leg_0 in iid-Exp(1) PIT
    space) where the cross-correlation lag-0 signal cleanly dominates the
    noise floor. Plan 04-08 (Wave 2) on real-ICHI residuals will exercise the
    weak-coupling regime as part of its empirical run.
    """
    rng = np.random.default_rng(2026052701)
    n = 1000
    # Two iid Exp(1) streams; couple leg_1 at lag 0 to leg_0 through a strong
    # rank-correlation. Use Gaussian copula construction then PIT to exp(1):
    from scipy.stats import norm, expon
    z0 = rng.standard_normal(n)
    z_indep = rng.standard_normal(n)
    rho_couple = 0.5
    z1 = rho_couple * z0 + np.sqrt(1 - rho_couple**2) * z_indep
    leg_0 = expon.ppf(norm.cdf(z0))
    leg_1 = expon.ppf(norm.cdf(z1))
    result = permutation_null_max_abs_rho(leg_0, leg_1, max_lag=50, n_reps=500, seed=20260527)
    assert result["p_value"] <= 0.05


def test_reproducibility_same_seed_identical_p():
    rng = np.random.default_rng(100)
    leg_0 = rng.exponential(scale=1.0, size=300)
    leg_1 = rng.exponential(scale=1.0, size=300)
    r1 = permutation_null_max_abs_rho(leg_0, leg_1, max_lag=50, n_reps=200, seed=20260527)
    r2 = permutation_null_max_abs_rho(leg_0, leg_1, max_lag=50, n_reps=200, seed=20260527)
    assert r1["p_value"] == r2["p_value"]
    assert r1["max_abs_rho_observed"] == r2["max_abs_rho_observed"]
