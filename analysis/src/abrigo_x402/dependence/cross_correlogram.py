"""Bowsher-2007 event-index lag-domain cross-correlogram on rescaled-time residuals.

Substrate: residuals.parquet :: rescaled_dt per leg (PITFALLS §4 — NOT raw timestamps).
Output: rho(h) for h in -max_lag..+max_lag where rho(h) is the Pearson correlation of
(leg_0[i], leg_1[i+h]) over the index-overlap range.

CONTEXT.md DEPEND-01 lock: max_lag=50 events (event-index, not wall-clock); the
statistic is well-defined on the event-rank domain even when the underlying arrival
rates are non-stationary (the rescaled_dt transform absorbs the non-stationarity).
"""
import numpy as np


def cross_correlogram_event_index(
    leg_0_rescaled_dt: np.ndarray,
    leg_1_rescaled_dt: np.ndarray,
    max_lag: int = 50,
) -> dict:
    """Return {lags: list[int] (2*max_lag+1), values: list[float] (Pearson rho per lag)}.

    For lag h: pairs are (leg_0[i], leg_1[i+h]) over the index range where both are
    defined. Each leg is mean-centered on its full-sample mean (NOT per-shift mean)
    and the denominator uses full-sample norms (Bowsher-2007 convention) so that the
    statistic is directly comparable across lags h.

    Parameters
    ----------
    leg_0_rescaled_dt, leg_1_rescaled_dt : np.ndarray
        Per-leg rescaled inter-arrival times (`rescaled_dt` column of
        `residuals.parquet`). Unequal lengths are accepted; the function truncates
        both legs to `min(len(leg_0), len(leg_1))` to fix a common shift basis.
    max_lag : int, default 50
        Lag radius in event-index units. Output covers h in [-max_lag, +max_lag].

    Returns
    -------
    dict
        Keys ``lags`` (list[int], length 2*max_lag+1, zero-lag at the center) and
        ``values`` (list[float], Pearson rho at each lag).

    Raises
    ------
    ValueError
        If the common sample size is too small to support the requested lag radius
        (need n > 2*max_lag+1 events; fail-loud per CONTEXT.md DEPEND-01).
    """
    leg_0 = np.asarray(leg_0_rescaled_dt, dtype=np.float64).ravel()
    leg_1 = np.asarray(leg_1_rescaled_dt, dtype=np.float64).ravel()
    n_min = min(len(leg_0), len(leg_1))
    if n_min <= 2 * max_lag + 1:
        raise ValueError(
            f"sample size {n_min} insufficient for max_lag={max_lag}; "
            f"need n > 2*max_lag+1 = {2 * max_lag + 1}"
        )

    # Truncate to common length to fix the shift basis.
    a = leg_0[:n_min]
    b = leg_1[:n_min]
    a_centered = a - a.mean()
    b_centered = b - b.mean()
    a_norm = float(np.sqrt(np.sum(a_centered ** 2)))
    b_norm = float(np.sqrt(np.sum(b_centered ** 2)))
    denom = a_norm * b_norm

    lags = list(range(-max_lag, max_lag + 1))
    values: list[float] = []
    for h in lags:
        if h >= 0:
            aa = a_centered[: n_min - h]
            bb = b_centered[h:]
        else:
            aa = a_centered[-h:]
            bb = b_centered[: n_min + h]
        num = float(np.sum(aa * bb))
        # Bowsher-2007 full-sample-norm denominator keeps rho(h) comparable across h.
        rho = num / denom if denom > 0.0 else 0.0
        values.append(rho)

    return {"lags": lags, "values": values}
