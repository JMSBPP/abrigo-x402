"""Wall-clock 80/20 temporal split. NOT event-count split (Pitfall 3, CONTEXT.md decision).

Scaffold note: WallClockSplit dataclass + wall_clock_split + compute_held_out_loglik_{hawkes,nhpp}
declared here so the Wave-1 plan 03-04 surface is locked at scaffold time and 03-07 orchestrator
can write against `split.t_split` / `split.to_metadata()` (the dataclass methods) from Day 1.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

HELD_OUT_FRACTION_DEFAULT: float = 0.20


class InsufficientEvaluationError(RuntimeError):
    """Raised when an in-sample-only fit attempt is made without a held-out segment (SC-4)."""


@dataclass(frozen=True)
class WallClockSplit:
    """Forward declaration of the 03-04 dataclass surface. Real implementation lands in Wave 1."""
    t_split: float
    train_leg_0: np.ndarray
    train_leg_1: np.ndarray
    held_out_leg_0: np.ndarray
    held_out_leg_1: np.ndarray
    window_start: float
    window_end: float
    held_out_fraction: float

    def to_metadata(self) -> dict:
        raise NotImplementedError("Wave 1 plan 03-04 implements this (DGP-04)")


def wall_clock_split(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    window_start: float,
    window_end: float,
    held_out_fraction: float = HELD_OUT_FRACTION_DEFAULT,
) -> WallClockSplit:
    """Returns frozen WallClockSplit dataclass with t_split, train/held_out per-leg arrays,
    window bounds, and held_out_fraction. NOT a dict — orchestrator (03-07) consumes the
    `split.t_split` / `split.to_metadata()` dataclass surface.

    Raises InsufficientEvaluationError if held_out_fraction <= 0 (SC-4 lock).
    """
    raise NotImplementedError("Wave 1 plan 03-04 implements this (DGP-04)")


def compute_held_out_loglik_hawkes(
    baseline: np.ndarray,
    adjacency: np.ndarray,
    decays: float,
    test_leg_0: np.ndarray,
    test_leg_1: np.ndarray,
    full_history_leg_0: np.ndarray,
    full_history_leg_1: np.ndarray,
    test_window_start: float | None,
    test_window_end: float | None,
) -> float:
    """Hawkes log-likelihood on held-out window using train-fitted parameters (Pattern 4).

    Raises InsufficientEvaluationError if test_window_start or test_window_end is None.
    """
    raise NotImplementedError("Wave 1 plan 03-04 implements this (DGP-04)")


def compute_held_out_loglik_nhpp(
    nhpp_baseline_per_sec: np.ndarray,
    test_leg_0: np.ndarray,
    test_leg_1: np.ndarray,
    test_window_start: float | None,
    test_window_end: float | None,
) -> float:
    """NHPP log-likelihood on held-out window using train-fitted INAR(p) baseline."""
    raise NotImplementedError("Wave 1 plan 03-04 implements this (DGP-04)")
