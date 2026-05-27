"""Brown 2002 time-rescaling KS test on held-out segment with train-fitted parameters."""
from __future__ import annotations
import numpy as np


def compute_compensator_exp_kernel(
    event_times: np.ndarray,
    leg_idx: int,
    baseline: np.ndarray,
    adjacency: np.ndarray,
    decays: float,
    full_history_leg_0: np.ndarray,
    full_history_leg_1: np.ndarray,
    window_start: float,
) -> np.ndarray:
    """Closed-form Lambda_i(t) for exponential kernel. Returns Lambda_at_events shape (n_events,)."""
    raise NotImplementedError("Wave 1 plan 03-05 implements this (DGP-05)")


def time_rescaling_ks_test_leg(
    event_times: np.ndarray,
    leg_idx: int,
    baseline: np.ndarray,
    adjacency: np.ndarray,
    decays: float,
    full_history_leg_0: np.ndarray,
    full_history_leg_1: np.ndarray,
    window_start: float,
    window_end: float,
) -> dict:
    """Returns dict: ks_statistic, p_value, n_events, rescaled_dt (list), Lambda_at_events (list)."""
    raise NotImplementedError("Wave 1 plan 03-05 implements this (DGP-05)")
