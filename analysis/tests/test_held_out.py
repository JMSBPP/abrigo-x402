"""DGP-04: held-out wall-clock split tests (PRE_REGISTRATION + SC-4 locks).

Locked invariants tested:
- Wall-clock split (NOT event-count split — Pitfall 3).
- InsufficientEvaluationError raised on in-sample-only attempts (SC-4).
- Closed-form Hawkes held-out log-likelihood finite on synthetic data.
- Split metadata dict carries the keys consumed by fit_report.json :: held_out_loglik.
"""
import numpy as np
import pytest

from abrigo_x402.dgp.held_out import (
    InsufficientEvaluationError,
    compute_held_out_loglik_hawkes,
    compute_held_out_loglik_nhpp,
    wall_clock_split,
)


def test_wallclock_split():
    """t_split = window_start + (1 - held_out_fraction) * (window_end - window_start)."""
    leg_0 = np.array([100.0, 700.0, 850.0], dtype=np.float64)
    leg_1 = np.array([200.0, 900.0], dtype=np.float64)
    split = wall_clock_split(
        leg_0, leg_1, window_start=0.0, window_end=1000.0, held_out_fraction=0.20
    )
    assert split.t_split == 800.0
    assert split.train_leg_0.tolist() == [100.0, 700.0]
    assert split.held_out_leg_0.tolist() == [850.0]
    assert split.train_leg_1.tolist() == [200.0]
    assert split.held_out_leg_1.tolist() == [900.0]


def test_wallclock_NOT_event_count_split():
    """Front-loaded panel: 90% of events in first half → wall-clock split puts < 20% in held-out."""
    rng = np.random.default_rng(42)
    front_loaded = np.concatenate(
        [
            np.sort(rng.uniform(0.0, 500.0, 900)),
            np.sort(rng.uniform(500.0, 1000.0, 100)),
        ]
    )
    split = wall_clock_split(
        front_loaded,
        front_loaded.copy(),
        window_start=0.0,
        window_end=1000.0,
        held_out_fraction=0.20,
    )
    # Wall-clock split at 800.0; FAR fewer than 20% of events in held-out
    assert split.held_out_leg_0.size < 0.20 * front_loaded.size, (
        "Split appears to be event-count not wall-clock"
    )


def test_in_sample_only_raises():
    """held_out_fraction=0.0 OR None test window bounds → InsufficientEvaluationError (SC-4)."""
    leg_0 = np.array([100.0, 200.0], dtype=np.float64)
    leg_1 = np.array([150.0], dtype=np.float64)
    with pytest.raises(InsufficientEvaluationError):
        wall_clock_split(
            leg_0, leg_1, window_start=0.0, window_end=1000.0, held_out_fraction=0.0
        )
    with pytest.raises(InsufficientEvaluationError):
        compute_held_out_loglik_hawkes(
            baseline=np.array([0.001, 0.001]),
            adjacency=np.zeros((2, 2)),
            decays=0.1,
            test_leg_0=leg_0,
            test_leg_1=leg_1,
            full_history_leg_0=leg_0,
            full_history_leg_1=leg_1,
            test_window_start=None,
            test_window_end=None,
        )
    with pytest.raises(InsufficientEvaluationError):
        compute_held_out_loglik_nhpp(
            nhpp_baseline_per_sec=np.array([0.001, 0.001]),
            test_leg_0=leg_0,
            test_leg_1=leg_1,
            test_window_start=None,
            test_window_end=None,
        )


def test_held_out_loglik_hawkes_finite():
    """Sanity: closed-form Hawkes held-out log-likelihood is finite on a synthetic panel."""
    rng = np.random.default_rng(20260526)
    leg_0 = np.sort(rng.uniform(0.0, 1000.0, 100))
    leg_1 = np.sort(rng.uniform(0.0, 1000.0, 100))
    ll = compute_held_out_loglik_hawkes(
        baseline=np.array([0.05, 0.05], dtype=np.float64),
        adjacency=np.array([[0.1, 0.05], [0.05, 0.1]], dtype=np.float64),
        decays=0.1,
        test_leg_0=leg_0[leg_0 >= 800.0],
        test_leg_1=leg_1[leg_1 >= 800.0],
        full_history_leg_0=leg_0,
        full_history_leg_1=leg_1,
        test_window_start=800.0,
        test_window_end=1000.0,
    )
    assert np.isfinite(ll), f"Expected finite log-likelihood, got {ll}"


def test_split_metadata_keys():
    """WallClockSplit.to_metadata() carries the keys consumed by fit_report.json."""
    leg_0 = np.array([100.0, 500.0, 900.0])
    leg_1 = np.array([200.0, 800.0])
    split = wall_clock_split(leg_0, leg_1, 0.0, 1000.0, 0.20)
    meta = split.to_metadata()
    assert {
        "t_split",
        "train_events_per_leg",
        "held_out_events_per_leg",
        "train_window_seconds",
        "held_out_window_seconds",
        "window_start",
        "window_end",
        "held_out_fraction",
    } <= set(meta.keys())
