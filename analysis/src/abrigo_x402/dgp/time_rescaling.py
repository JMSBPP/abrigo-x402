"""DGP-05: Brown et al. 2002 time-rescaling KS test on held-out Hawkes residuals.

LOCKED INVARIANTS (PRE_REGISTRATION + PITFALLS §4):
- Compensator Lambda_i(t) for exponential-kernel Hawkes computed in CLOSED FORM
  (Don't-Hand-Roll table: any numerical-integration shortcut — adaptive
  quadrature, trapezoidal rules, Simpson's rule, etc. — would introduce
  step-size error and is explicitly prohibited).
- KS test applied on HELD-OUT segment with TRAIN-FITTED parameters
  (Pitfall 5: in-sample optimism passes misspecified models).
- Acceptance threshold: p > 0.05 (PRE_REGISTRATION §Test Statistics).
- scipy.stats.kstest(rescaled_dt, 'expon') is the test statistic.

Closed-form recursion for the exponential kernel
-------------------------------------------------
For leg i on the held-out window [W_start, W_end], the conditional intensity is
    lambda_i(t) = mu_i + sum_j alpha_ij * sum_{t_jk < t} exp(-beta * (t - t_jk)),
so the cumulative compensator from W_start to t is
    Lambda_i(t) - Lambda_i(W_start)
        = mu_i * (t - W_start)
          + sum_j alpha_ij *
            sum_{t_jk < t}
              [exp(-beta * max(W_start - t_jk, 0)) - exp(-beta * (t - t_jk))] / beta
because the integral of alpha_ij * exp(-beta * (s - t_jk)) over
s in [max(W_start, t_jk), t] yields the bracketed difference divided by beta.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
import polars as pl
from scipy.stats import kstest


def compute_compensator_exp_kernel(
    event_times: np.ndarray,
    leg_idx: int,
    baseline: np.ndarray,         # shape (2,)
    adjacency: np.ndarray,        # shape (2, 2)
    decays: float,
    full_history_leg_0: np.ndarray,
    full_history_leg_1: np.ndarray,
    window_start: float,
) -> np.ndarray:
    """Closed-form Lambda_i(t) - Lambda_i(window_start) at each event time.

    Parameters
    ----------
    event_times : np.ndarray
        Event timestamps in the held-out window (or any target evaluation set).
    leg_idx : int
        Which leg's compensator to compute (0 or 1).
    baseline : np.ndarray, shape (2,)
        Baseline intensities (mu_0, mu_1).
    adjacency : np.ndarray, shape (2, 2)
        Excitation matrix alpha.
    decays : float
        Scalar decay beta.
    full_history_leg_0, full_history_leg_1 : np.ndarray
        FULL event-time histories for both legs (train + earlier held-out events).
        Both train and held-out events contribute via the same closed-form integral.
    window_start : float
        Lower bound of the compensator integral (typically t_split).

    Returns
    -------
    np.ndarray, shape (event_times.size,)
        Lambda_i(t) - Lambda_i(window_start) at each event_time.
    """
    baseline = np.asarray(baseline, dtype=np.float64)
    adjacency = np.asarray(adjacency, dtype=np.float64)
    mu_i = float(baseline[leg_idx])
    beta = float(decays)
    if beta <= 0.0:
        raise ValueError(f"decays must be strictly positive, got {beta}")

    Lambda_at_events = np.empty(event_times.size, dtype=np.float64)
    histories = (
        np.sort(np.asarray(full_history_leg_0, dtype=np.float64)),
        np.sort(np.asarray(full_history_leg_1, dtype=np.float64)),
    )
    W_start = float(window_start)
    for idx, t_raw in enumerate(event_times):
        t = float(t_raw)
        L_baseline = mu_i * (t - W_start)
        L_exc = 0.0
        for j, hist in enumerate(histories):
            if hist.size == 0:
                continue
            # Events strictly before t contribute. Integration lower bound is
            # max(W_start, t_jk): exp(-beta * max(W_start - t_jk, 0)).
            past = hist[hist < t]
            if past.size == 0:
                continue
            lower = np.maximum(W_start - past, 0.0)
            term = (np.exp(-beta * lower) - np.exp(-beta * (t - past))) / beta
            L_exc += float(adjacency[leg_idx, j]) * float(np.sum(term))
        Lambda_at_events[idx] = L_baseline + L_exc
    return Lambda_at_events


def time_rescaling_ks_test_leg(
    held_out_event_times: np.ndarray,
    leg_idx: int,
    baseline: np.ndarray,
    adjacency: np.ndarray,
    decays: float,
    full_history_leg_0: np.ndarray,
    full_history_leg_1: np.ndarray,
    window_start: float,
    window_end: float,
) -> dict:
    """Brown 2002 KS test on rescaled inter-arrival times.

    Per Brown 2002, under correct specification the rescaled inter-arrival
    times Lambda_i(t_{i+1}) - Lambda_i(t_i) are i.i.d. Exp(1). We compute the
    compensator via the closed-form recursion, anchor the cumulative
    transformation at 0 (so the first held-out arrival's rescaled gap is its
    compensator), and apply scipy.stats.kstest against the 'expon' distribution.

    Returns
    -------
    dict
        ks_statistic, p_value, n_events, rescaled_dt (list[float]),
        Lambda_at_events (list[float]). On insufficient events the test is
        skipped and skipped_reason is set with NaN statistics.
    """
    held_out_event_times = np.asarray(held_out_event_times, dtype=np.float64)
    if held_out_event_times.size < 2:
        return {
            "ks_statistic": float("nan"),
            "p_value": float("nan"),
            "n_events": int(held_out_event_times.size),
            "rescaled_dt": [],
            "Lambda_at_events": [],
            "skipped_reason": "insufficient_events",
        }

    Lambda = compute_compensator_exp_kernel(
        held_out_event_times,
        leg_idx,
        baseline,
        adjacency,
        decays,
        full_history_leg_0,
        full_history_leg_1,
        window_start,
    )

    rescaled_dt = np.diff(np.concatenate([[0.0], Lambda]))
    # Drop non-positive rescaled gaps (numerical edge cases / ties).
    positive_mask = rescaled_dt > 0.0
    rescaled_dt_pos = rescaled_dt[positive_mask]

    if rescaled_dt_pos.size < 2:
        return {
            "ks_statistic": float("nan"),
            "p_value": float("nan"),
            "n_events": int(held_out_event_times.size),
            "rescaled_dt": rescaled_dt_pos.tolist(),
            "Lambda_at_events": Lambda.tolist(),
            "skipped_reason": "non_positive_rescaling",
        }

    ks_stat, ks_pvalue = kstest(rescaled_dt_pos, "expon")
    return {
        "ks_statistic": float(ks_stat),
        "p_value": float(ks_pvalue),
        "n_events": int(held_out_event_times.size),
        "rescaled_dt": rescaled_dt_pos.tolist(),
        "Lambda_at_events": Lambda.tolist(),
    }


def build_residuals_dataframe(
    per_leg_results: Sequence[dict],
    held_out_event_times_per_leg: Sequence[np.ndarray],
) -> pl.DataFrame:
    """Combine per-leg time-rescaling outputs into a single residuals DataFrame.

    The orchestrator (Plan 03-07) writes this to
    `data/fits/ichi/<run_id>/residuals.parquet`, where Phase 4's empirical
    copula consumes the rescaled_dt column directly.

    Columns
    -------
    leg : UInt8                — 0 or 1
    event_time : Float64       — held-out event timestamp (seconds)
    Lambda_at_event : Float64  — compensator value at the event
    rescaled_dt : Float64      — Lambda(t_i) - Lambda(t_{i-1}); NaN at the
                                  first event of each leg (no preceding event)
    """
    rows: list[dict] = []
    for leg_idx, (result, event_times) in enumerate(
        zip(per_leg_results, held_out_event_times_per_leg)
    ):
        event_times = np.asarray(event_times, dtype=np.float64)
        Lambdas = np.asarray(result.get("Lambda_at_events", []), dtype=np.float64)
        rescaled = np.asarray(result.get("rescaled_dt", []), dtype=np.float64)
        # rescaled_dt may be shorter than events (insufficient-rescaling skip or
        # positivity filter). Align to the per-event length, padding with NaN.
        rescaled_aligned = np.full(event_times.size, float("nan"), dtype=np.float64)
        n_aligned = min(event_times.size, rescaled.size)
        rescaled_aligned[:n_aligned] = rescaled[:n_aligned]
        # Lambda may be shorter than events on the skipped path; pad with NaN.
        Lambda_aligned = np.full(event_times.size, float("nan"), dtype=np.float64)
        n_lam = min(event_times.size, Lambdas.size)
        Lambda_aligned[:n_lam] = Lambdas[:n_lam]
        for t, Lam, rdt in zip(event_times, Lambda_aligned, rescaled_aligned):
            rows.append(
                {
                    "leg": int(leg_idx),
                    "event_time": float(t),
                    "Lambda_at_event": float(Lam),
                    "rescaled_dt": float(rdt),
                }
            )
    if not rows:
        return pl.DataFrame(
            schema={
                "leg": pl.UInt8,
                "event_time": pl.Float64,
                "Lambda_at_event": pl.Float64,
                "rescaled_dt": pl.Float64,
            }
        )
    return pl.DataFrame(rows).with_columns(pl.col("leg").cast(pl.UInt8))
