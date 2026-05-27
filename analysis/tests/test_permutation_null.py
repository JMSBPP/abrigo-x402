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
    path = FIXTURES / "synthetic_hawkes_eta_05.parquet"
    if not path.exists():
        pytest.skip("Phase 3 fixture missing")
    df = pl.read_parquet(path)
    leg_0_times = (
        df.filter(pl.col("leg") == 0)
        .get_column("event_time")
        .to_numpy()
        .ravel()
        .astype(np.float64)
    )
    leg_1_times = (
        df.filter(pl.col("leg") == 1)
        .get_column("event_time")
        .to_numpy()
        .ravel()
        .astype(np.float64)
    )
    leg_0 = np.diff(leg_0_times)
    leg_1 = np.diff(leg_1_times)
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
