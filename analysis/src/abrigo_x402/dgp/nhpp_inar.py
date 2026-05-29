"""Kirchner 2015 INAR(p) NHPP fit via statsmodels.tsa.api.VAR with non-negativity projection.

Reference: Kirchner 2015 arxiv:1509.02017 §6 (consistency + asymptotic normality of
conditional least-squares VAR(p) estimator for INAR(p)).

Key invariants (PRE_REGISTRATION lock + PITFALLS):
- Bin width selection: AIC-min over the LOCKED grid {60, 300, 900, 3600} seconds.
  AF-04 forbids any hand-tuned off-grid bin width.
- Order p selection: AIC over {1, ..., max_p=10}.
- Non-negativity projection: any negative VAR coefficient / intercept entry -> 0
  (Kirchner's projection step preserves the NHPP intensity positivity invariant).
- Bivariate count sequence: (leg_0_count, leg_1_count) per bin.
  NEVER fit two univariate INAR(p) and sum (PITFALLS §5 — leaks cross-leg covariance
  into spurious Hawkes self-excitation downstream).
"""
from __future__ import annotations

import numpy as np
from statsmodels.tsa.api import VAR

BIN_WIDTH_GRID_SECONDS: tuple[float, ...] = (60.0, 300.0, 900.0, 3600.0)
MAX_P: int = 10


def _bin_counts(times: np.ndarray, bin_edges: np.ndarray) -> np.ndarray:
    counts, _ = np.histogram(times, bins=bin_edges)
    return counts


def _fit_at_bin_width(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    window_start: float,
    window_end: float,
    bin_width_seconds: float,
    max_p: int,
) -> dict:
    n_bins = int(np.ceil((window_end - window_start) / bin_width_seconds))
    bin_edges = window_start + np.arange(n_bins + 1) * bin_width_seconds
    counts_0 = _bin_counts(leg_0_times, bin_edges)
    counts_1 = _bin_counts(leg_1_times, bin_edges)

    # Bivariate count matrix (NOT summed univariate — PITFALLS §5)
    count_matrix = np.column_stack([counts_0, counts_1]).astype(np.float64)

    # statsmodels VAR requires per-column variability; if a leg has zero variance at
    # this bin width, return a degenerate (AIC=+inf) candidate so the grid-search
    # picks a different bin width.
    if count_matrix.std(axis=0).min() < 1e-12:
        return {
            "p": 0,
            "bin_width_seconds": float(bin_width_seconds),
            "coefs": [],
            "intercept": count_matrix.mean(axis=0).tolist(),
            "aic": float("inf"),
            "loglik_in_sample": float("-inf"),
            "n_bins": int(n_bins),
            "raw_coefs_had_negatives": False,
        }

    model = VAR(count_matrix)

    # AIC order selection over p in {1, ..., min(max_p, n_bins // 3)}.
    # The n_bins // 3 cap protects statsmodels from over-parameterized fits when
    # bin_width is large relative to the window.
    p_cap = max(1, min(max_p, n_bins // 3))
    try:
        sel = model.select_order(maxlags=p_cap)
        p_star = max(int(sel.aic), 1)
    except Exception:
        p_star = 1

    fit = model.fit(p_star)

    # Kirchner non-negativity projection: any negative VAR coefficient -> 0.
    # Track whether the raw fit had negatives (provenance for downstream LR rig).
    raw_coefs = fit.coefs.copy()  # shape (p, k, k)
    coefs = np.maximum(raw_coefs, 0.0)
    intercept = np.maximum(fit.intercept, 0.0)

    return {
        "p": int(p_star),
        "bin_width_seconds": float(bin_width_seconds),
        "coefs": coefs.tolist(),
        "intercept": intercept.tolist(),
        "aic": float(fit.aic),
        "loglik_in_sample": float(fit.llf),
        "n_bins": int(n_bins),
        "raw_coefs_had_negatives": bool(np.any(raw_coefs < 0.0)),
    }


def fit_nhpp_inar(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    window_start: float,
    window_end: float,
    bin_width_seconds: float | None = None,
    max_p: int = MAX_P,
) -> dict:
    """Fit bivariate INAR(p) NHPP via Kirchner 2015 VAR(p) least-squares + nonneg projection.

    Args:
        leg_0_times: event timestamps for leg 0 (token0-inflow Swaps), seconds.
        leg_1_times: event timestamps for leg 1 (token1-inflow Swaps), seconds.
        window_start: window start time, seconds.
        window_end: window end time, seconds.
        bin_width_seconds: if None, AIC-min over BIN_WIDTH_GRID_SECONDS = {60, 300, 900, 3600}s
            (PRE_REGISTRATION lock). If pinned (e.g. by orchestrator after grid-search, or by tests),
            fit at that single bin width only.
        max_p: max VAR(p) order considered by AIC selection. Default 10 (Kirchner standard).

    Returns:
        dict with keys:
          p (int), bin_width_seconds (float), coefs (list, shape (p, 2, 2)),
          intercept (list, shape (2,)), aic (float), loglik_in_sample (float),
          n_bins (int), raw_coefs_had_negatives (bool),
          bin_width_aic_table (dict[str -> float]).
    """
    if bin_width_seconds is not None:
        # Caller pinned the bin width (orchestrator post-grid-search, or test).
        fit = _fit_at_bin_width(
            leg_0_times, leg_1_times, window_start, window_end, bin_width_seconds, max_p
        )
        fit["bin_width_aic_table"] = {str(float(bin_width_seconds)): fit["aic"]}
        return fit

    # AIC bin-width selection across the LOCKED grid (PRE_REGISTRATION).
    candidates: list[dict] = []
    aic_table: dict[str, float] = {}
    for bw in BIN_WIDTH_GRID_SECONDS:
        candidate = _fit_at_bin_width(
            leg_0_times, leg_1_times, window_start, window_end, bw, max_p
        )
        candidates.append(candidate)
        aic_table[str(bw)] = candidate["aic"]

    best = min(candidates, key=lambda c: c["aic"])
    best["bin_width_aic_table"] = aic_table
    return best
