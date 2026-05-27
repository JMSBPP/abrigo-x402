"""Plan 04-01 DEPEND-01 cross-correlogram tests.

Substrate: residuals.parquet :: rescaled_dt per leg (Bowsher-2007 event-index domain
on rescaled time per PITFALLS §4).
"""
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from abrigo_x402.dependence.cross_correlogram import cross_correlogram_event_index

FIXTURES = Path(__file__).parent / "fixtures"


def test_shape_contract() -> None:
    """Output dict carries lags + values; both have length 2*max_lag+1 with zero-lag centered."""
    rng = np.random.default_rng(20260527)
    leg_0 = rng.exponential(scale=1.0, size=300)
    leg_1 = rng.exponential(scale=1.0, size=300)
    result = cross_correlogram_event_index(leg_0, leg_1, max_lag=50)
    assert "lags" in result and "values" in result
    assert len(result["lags"]) == 101
    assert len(result["values"]) == 101
    assert result["lags"][50] == 0  # zero-lag at center


def test_independence_baseline_near_zero() -> None:
    """Two independent exp(1) samples yield max|rho(h)| concentrated near zero."""
    rng = np.random.default_rng(42)
    leg_0 = rng.exponential(scale=1.0, size=1000)
    leg_1 = rng.exponential(scale=1.0, size=1000)
    result = cross_correlogram_event_index(leg_0, leg_1, max_lag=50)
    assert max(abs(v) for v in result["values"]) < 0.15


def test_cross_excitation_positive_control() -> None:
    """Synthetic Hawkes fixture (eta=0.5, off-diagonal alpha > 0) yields max|rho(h)|
    elevated above the independence baseline, with the argmax lag near zero."""
    path = FIXTURES / "synthetic_hawkes_eta_05.parquet"
    if not path.exists():
        pytest.skip("Phase 3 synthetic_hawkes_eta_05 fixture missing")
    # Fixture stores raw event times; Plan 04-08 integration test exercises the
    # full residuals.parquet :: rescaled_dt path. For the unit-test sanity check
    # we use per-leg inter-arrival times as a proxy substrate.
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
    result = cross_correlogram_event_index(leg_0, leg_1, max_lag=50)
    max_idx = int(np.argmax(np.abs(result["values"])))
    assert max(abs(v) for v in result["values"]) > 0.05
    assert abs(result["lags"][max_idx]) <= 5


def test_unequal_leg_lengths() -> None:
    """Unequal-length legs collapse to min-length shift basis without error."""
    rng = np.random.default_rng(100)
    leg_0 = rng.exponential(scale=1.0, size=500)
    leg_1 = rng.exponential(scale=1.0, size=750)
    result = cross_correlogram_event_index(leg_0, leg_1, max_lag=50)
    assert len(result["values"]) == 101
