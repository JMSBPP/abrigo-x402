"""DGP-04: wall-clock 80/20 temporal split + held-out log-likelihood evaluation.

LOCKED INVARIANTS (PRE_REGISTRATION + CONTEXT.md + SC-4):
- Wall-clock split: t_split = window_start + (1 - held_out_fraction) * (window_end - window_start)
- NOT event-count split (Pitfall 3: couples test set to realized event density)
- In-sample-only attempt raises InsufficientEvaluationError (SC-4)
- Hawkes held-out log-likelihood uses train-fitted parameters on test window (Pitfall 5:
  in-sample passes misspecified models)
- For exponential kernel, the integral of the intensity over the test window has a
  closed form; full pre-test history feeds the kernel sum (self-excitation carries
  through W_start).

This module exposes the surface consumed by:
  - analysis/src/abrigo_x402/dgp/stationarity.py via WallClockSplit
  - analysis/src/abrigo_x402/dgp/orchestrator.py (03-07) via split.t_split / split.to_metadata()
  - fit_report.json :: held_out_loglik (orchestrator builds this from compute_held_out_loglik_*).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

HELD_OUT_FRACTION_DEFAULT: float = 0.20


class InsufficientEvaluationError(RuntimeError):
    """Raised when caller attempts to evaluate a fit without a held-out segment (SC-4 lock)."""


@dataclass(frozen=True)
class WallClockSplit:
    """Frozen dataclass returned by wall_clock_split.

    Orchestrator 03-07 consumes split.t_split / split.to_metadata() — NOT a dict.
    """

    t_split: float
    train_leg_0: np.ndarray
    train_leg_1: np.ndarray
    held_out_leg_0: np.ndarray
    held_out_leg_1: np.ndarray
    window_start: float
    window_end: float
    held_out_fraction: float

    def to_metadata(self) -> dict:
        """Return the fit_report.json :: held_out_loglik :: split_metadata block."""
        return {
            "t_split": float(self.t_split),
            "window_start": float(self.window_start),
            "window_end": float(self.window_end),
            "held_out_fraction": float(self.held_out_fraction),
            "train_events_per_leg": [
                int(self.train_leg_0.size),
                int(self.train_leg_1.size),
            ],
            "held_out_events_per_leg": [
                int(self.held_out_leg_0.size),
                int(self.held_out_leg_1.size),
            ],
            "train_window_seconds": float(self.t_split - self.window_start),
            "held_out_window_seconds": float(self.window_end - self.t_split),
        }


def wall_clock_split(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    window_start: float,
    window_end: float,
    held_out_fraction: float = HELD_OUT_FRACTION_DEFAULT,
) -> WallClockSplit:
    """Split panel at wall-clock t_split = window_start + (1 - held_out_fraction) * total_seconds.

    Raises InsufficientEvaluationError if held_out_fraction <= 0 (SC-4) or if the held-out
    window contains zero events on BOTH legs (degenerate evaluation).
    """
    if held_out_fraction <= 0.0:
        raise InsufficientEvaluationError(
            f"In-sample-only evaluation forbidden (SC-4); got held_out_fraction={held_out_fraction}"
        )
    leg_0_times = np.asarray(leg_0_times, dtype=np.float64)
    leg_1_times = np.asarray(leg_1_times, dtype=np.float64)
    t_split = float(window_start) + (1.0 - float(held_out_fraction)) * (
        float(window_end) - float(window_start)
    )
    train_0 = leg_0_times[leg_0_times < t_split]
    train_1 = leg_1_times[leg_1_times < t_split]
    held_0 = leg_0_times[leg_0_times >= t_split]
    held_1 = leg_1_times[leg_1_times >= t_split]
    if held_0.size == 0 and held_1.size == 0:
        raise InsufficientEvaluationError(
            f"Held-out segment [{t_split}, {window_end}] contains zero events on both legs"
        )
    return WallClockSplit(
        t_split=float(t_split),
        train_leg_0=train_0.astype(np.float64),
        train_leg_1=train_1.astype(np.float64),
        held_out_leg_0=held_0.astype(np.float64),
        held_out_leg_1=held_1.astype(np.float64),
        window_start=float(window_start),
        window_end=float(window_end),
        held_out_fraction=float(held_out_fraction),
    )


def _hawkes_intensity_at(
    t: float,
    leg_idx: int,
    baseline: np.ndarray,
    adjacency: np.ndarray,
    decays: float,
    leg_0_history: np.ndarray,
    leg_1_history: np.ndarray,
) -> float:
    """lambda_i(t) = mu_i + sum_j alpha_ij sum_{t_jk < t} exp(-beta (t - t_jk))."""
    lam = float(baseline[leg_idx])
    for j, hist in enumerate((leg_0_history, leg_1_history)):
        past = hist[hist < t]
        if past.size > 0:
            lam += float(adjacency[leg_idx, j]) * float(
                np.sum(np.exp(-decays * (t - past)))
            )
    return lam


def _hawkes_integrated_intensity(
    leg_idx: int,
    baseline: np.ndarray,
    adjacency: np.ndarray,
    decays: float,
    leg_0_full: np.ndarray,
    leg_1_full: np.ndarray,
    W_start: float,
    W_end: float,
) -> float:
    """Closed-form integral of intensity over [W_start, W_end] for exponential kernel.

    For each past event at t_jk with t_jk < W_end, contribution is:
      alpha_ij * (exp(-beta (max(W_start, t_jk) - t_jk))
                - exp(-beta (W_end - t_jk))) / beta
    plus baseline * (W_end - W_start).
    """
    integral = float(baseline[leg_idx]) * (W_end - W_start)
    for j, hist in enumerate((leg_0_full, leg_1_full)):
        # hist is sorted by wall_clock_split; np.sort defensively in caller.
        for tjk in hist:
            tjk_f = float(tjk)
            if tjk_f >= W_end:
                break
            lo = max(W_start, tjk_f)
            integral += (
                float(adjacency[leg_idx, j])
                * (np.exp(-decays * (lo - tjk_f)) - np.exp(-decays * (W_end - tjk_f)))
                / decays
            )
    return float(integral)


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
    """log L = sum log(lambda_i(t_ik)) - integral lambda_i(s) ds on the test window per leg.

    full_history_leg_* MUST include train events as well — Hawkes self-excitation carries
    through W_start (the kernel sum at time t in the test window references ALL past events,
    not just those in the test window).

    Raises InsufficientEvaluationError if test_window_start or test_window_end is None (SC-4).
    """
    if test_window_start is None or test_window_end is None:
        raise InsufficientEvaluationError(
            "Hawkes held-out log-likelihood requires explicit test window bounds (SC-4)"
        )
    baseline = np.asarray(baseline, dtype=np.float64)
    adjacency = np.asarray(adjacency, dtype=np.float64)
    full_0 = np.sort(np.asarray(full_history_leg_0, dtype=np.float64))
    full_1 = np.sort(np.asarray(full_history_leg_1, dtype=np.float64))

    total_ll = 0.0
    for leg_idx, test_times in enumerate((test_leg_0, test_leg_1)):
        leg_ll = 0.0
        degenerate = False
        for t in test_times:
            lam = _hawkes_intensity_at(
                float(t),
                leg_idx,
                baseline,
                adjacency,
                float(decays),
                full_0,
                full_1,
            )
            if lam <= 0.0:
                degenerate = True
                break
            leg_ll += float(np.log(lam))
        if degenerate:
            return float("-inf")
        leg_ll -= _hawkes_integrated_intensity(
            leg_idx,
            baseline,
            adjacency,
            float(decays),
            full_0,
            full_1,
            float(test_window_start),
            float(test_window_end),
        )
        total_ll += leg_ll
    return float(total_ll)


def compute_held_out_loglik_nhpp(
    nhpp_baseline_per_sec: np.ndarray,
    test_leg_0: np.ndarray,
    test_leg_1: np.ndarray,
    test_window_start: float | None,
    test_window_end: float | None,
) -> float:
    """log L for homogeneous-baseline NHPP on test window: N * log(mu) - mu * duration per leg.

    Raises InsufficientEvaluationError if either window bound is None (SC-4).
    """
    if test_window_start is None or test_window_end is None:
        raise InsufficientEvaluationError(
            "NHPP held-out log-likelihood requires explicit test window bounds (SC-4)"
        )
    duration = float(test_window_end) - float(test_window_start)
    nhpp_baseline_per_sec = np.asarray(nhpp_baseline_per_sec, dtype=np.float64)
    ll = 0.0
    for leg_idx, test_times in enumerate((test_leg_0, test_leg_1)):
        mu = float(nhpp_baseline_per_sec[leg_idx])
        if mu <= 0.0:
            return float("-inf")
        ll += float(np.asarray(test_times).size) * float(np.log(mu)) - mu * duration
    return float(ll)
