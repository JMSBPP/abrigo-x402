"""SC-4 + PITFALLS section 4: baseline stationarity diagnostic tests.

Tests the +/-25% rate-ratio decision rule locked by PRE_REGISTRATION + SC-4.
"""
import numpy as np

from abrigo_x402.dgp.held_out import wall_clock_split
from abrigo_x402.dgp.stationarity import (
    STATIONARITY_RATIO_THRESHOLD,
    baseline_stationarity_check,
)


def test_stationary_decision():
    """Balanced uniform draws on both legs → decision='stationary' + ratio < threshold."""
    rng = np.random.default_rng(20260526)
    leg_0 = np.sort(rng.uniform(0.0, 1000.0, 10_000))
    leg_1 = np.sort(rng.uniform(0.0, 1000.0, 10_000))
    split = wall_clock_split(leg_0, leg_1, 0.0, 1000.0, 0.20)
    result = baseline_stationarity_check(split)
    assert result["decision"] == "stationary", result
    assert all(r < STATIONARITY_RATIO_THRESHOLD for r in result["ratio"])


def test_piecewise_required_on_drifted_synthetic():
    """Rate doubled in second half → decision='piecewise_required' + at least one ratio > threshold."""
    rng = np.random.default_rng(20260526)
    leg_0 = np.concatenate(
        [
            np.sort(rng.uniform(0.0, 500.0, 500)),
            np.sort(rng.uniform(500.0, 1000.0, 2000)),
        ]
    )
    leg_1 = leg_0.copy()
    split = wall_clock_split(leg_0, leg_1, 0.0, 1000.0, 0.20)
    result = baseline_stationarity_check(split)
    assert result["decision"] == "piecewise_required", result
    assert any(r > STATIONARITY_RATIO_THRESHOLD for r in result["ratio"])


def test_handles_zero_train_rate():
    """Empty train on a leg → ratio=inf, decision='piecewise_required' (safety branch)."""
    # leg_0 events all in the held-out segment; train segment for leg_0 is empty.
    leg_0 = np.array([950.0, 970.0, 990.0])
    leg_1 = np.array([100.0, 500.0, 900.0])
    split = wall_clock_split(leg_0, leg_1, 0.0, 1000.0, 0.20)
    result = baseline_stationarity_check(split)
    assert result["decision"] == "piecewise_required"
    assert result["ratio"][0] == float("inf")


def test_dict_keys_match_fit_report():
    """Return dict contains the keys consumed by fit_report.json :: baseline_stationarity_check."""
    rng = np.random.default_rng(42)
    leg_0 = np.sort(rng.uniform(0.0, 1000.0, 500))
    leg_1 = np.sort(rng.uniform(0.0, 1000.0, 500))
    split = wall_clock_split(leg_0, leg_1, 0.0, 1000.0, 0.20)
    result = baseline_stationarity_check(split)
    assert {
        "train_rate",
        "held_out_rate",
        "ratio",
        "decision",
        "threshold",
        "per_leg_decision",
    } <= set(result.keys())
