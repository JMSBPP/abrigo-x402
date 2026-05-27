"""1000-rep within-window shuffle on rescaled_dt; max|rho(h)| statistic; deterministic seed.

Substrate: residuals.parquet :: rescaled_dt per leg (PITFALLS §4 — NOT raw timestamps).
Per PRE_REGISTRATION §Test Statistics: n_reps=1000 is the locked size.
Per CONTEXT.md DEPEND-01: max_lag=50 events; within-window shuffle of leg_1; max|rho(h)|.
p_value uses standard one-sided permutation convention with +1 continuity correction:
``p = (1 + sum(perm_max >= observed_max)) / (n_reps + 1)`` — non-zero even when no
permutation exceeds the observed statistic, which is the standard finite-sample
correction (Phipson & Smyth 2010) for permutation tests.
"""
import numpy as np

from abrigo_x402.dependence.cross_correlogram import cross_correlogram_event_index


def permutation_null_max_abs_rho(
    leg_0_rescaled_dt: np.ndarray,
    leg_1_rescaled_dt: np.ndarray,
    max_lag: int = 50,
    n_reps: int = 1000,
    seed: int = 20260527,
) -> dict:
    """Return {n_reps, p_value, max_abs_rho_observed, max_abs_rho_null_dist}.

    Observed statistic: max|rho(h)| over h in [-max_lag, +max_lag] computed on the
    unpermuted (leg_0, leg_1) pair via :func:`cross_correlogram_event_index`.
    Null distribution: ``n_reps`` shuffles of ``leg_1`` via
    ``np.random.default_rng(seed).permutation``; recompute the cross-correlogram per
    shuffle; record max|rho(h)| per rep.
    p_value: ``(1 + sum(perm_max >= observed_max)) / (n_reps + 1)`` — one-sided
    permutation test with continuity correction.

    Parameters
    ----------
    leg_0_rescaled_dt, leg_1_rescaled_dt : np.ndarray
        Per-leg rescaled inter-arrival times (`rescaled_dt` column of
        `residuals.parquet`). Under correctly-specified Hawkes these are iid Exp(1),
        which is the invariant the within-window shuffle preserves (PITFALLS §4).
    max_lag : int, default 50
        Lag radius in event-index units (CONTEXT.md DEPEND-01 lock).
    n_reps : int, default 1000
        Number of permutation replicates (PRE_REGISTRATION §Test Statistics lock).
    seed : int, default 20260527
        Deterministic seed for ``np.random.default_rng`` — same input + same seed
        yields byte-identical ``p_value``.

    Returns
    -------
    dict
        Keys ``n_reps`` (int), ``p_value`` (float in [0, 1]), ``max_abs_rho_observed``
        (float), ``max_abs_rho_null_dist`` (list[float], length ``n_reps``).
    """
    leg_0 = np.asarray(leg_0_rescaled_dt, dtype=np.float64).ravel()
    leg_1 = np.asarray(leg_1_rescaled_dt, dtype=np.float64).ravel()

    observed = cross_correlogram_event_index(leg_0, leg_1, max_lag=max_lag)
    observed_max = float(max(abs(v) for v in observed["values"]))

    rng = np.random.default_rng(seed)
    null_dist: list[float] = []
    for _ in range(n_reps):
        shuffled = rng.permutation(leg_1)
        perm = cross_correlogram_event_index(leg_0, shuffled, max_lag=max_lag)
        null_dist.append(float(max(abs(v) for v in perm["values"])))

    null_arr = np.asarray(null_dist, dtype=np.float64)
    p_value = float((1 + int(np.sum(null_arr >= observed_max))) / (n_reps + 1))

    return {
        "n_reps": int(n_reps),
        "p_value": p_value,
        "max_abs_rho_observed": observed_max,
        "max_abs_rho_null_dist": null_dist,
    }
