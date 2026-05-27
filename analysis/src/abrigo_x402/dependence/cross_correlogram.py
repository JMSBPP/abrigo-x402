"""Bowsher-2007 event-index lag-domain cross-correlogram.

Substrate: residuals.parquet :: rescaled_dt per leg (Phase 3 DGP-05 output).
CONTEXT.md locks max_lag=50 and the substrate convention per PITFALLS §4
stationarity discipline.
"""
import numpy as np


def cross_correlogram_event_index(
    leg_0_rescaled_dt: np.ndarray,
    leg_1_rescaled_dt: np.ndarray,
    max_lag: int = 50,
) -> dict:
    """Return {lags: list[int] of length 2*max_lag+1, values: list[float] of pearson rho per lag}.

    Bowsher-2007 event-index convention: for each event in leg_0, look at index-h-shifted
    event in leg_1, compute Pearson rho across the shifted pairs.
    """
    raise NotImplementedError("Plan 04-01 implements DEPEND-01 cross-correlogram")
