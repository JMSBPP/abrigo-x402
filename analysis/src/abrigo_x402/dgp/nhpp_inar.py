"""Kirchner 2015 INAR(p) NHPP fit via statsmodels.tsa.api.VAR with non-negativity projection."""
from __future__ import annotations
import numpy as np

BIN_WIDTH_GRID_SECONDS: tuple[float, ...] = (60.0, 300.0, 900.0, 3600.0)
MAX_P: int = 10


def fit_nhpp_inar(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    window_start: float,
    window_end: float,
    bin_width_seconds: float | None = None,
    max_p: int = MAX_P,
) -> dict:
    """Fit bivariate INAR(p) NHPP. If bin_width_seconds is None, AIC-min over BIN_WIDTH_GRID_SECONDS.

    Returns a dict with keys: p, bin_width_seconds, coefs (list, shape (p,2,2)),
    intercept (list, shape (2,)), aic, loglik_in_sample, bin_width_aic_table (dict).
    """
    raise NotImplementedError("Wave 1 plan 03-01 implements this (DGP-01)")
