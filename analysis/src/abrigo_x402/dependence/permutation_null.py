"""1000-rep within-window shuffle on rescaled_dt; max|rho(h)| statistic; deterministic seed."""
import numpy as np


def permutation_null_max_abs_rho(
    leg_0_rescaled_dt: np.ndarray,
    leg_1_rescaled_dt: np.ndarray,
    max_lag: int = 50,
    n_reps: int = 1000,
    seed: int = 20260527,
) -> dict:
    """Return {n_reps, p_value, max_abs_rho_observed, max_abs_rho_null_dist: list[float]}.

    Test statistic: max|rho(h)| over h in -max_lag..+max_lag.
    Permutation: within-window shuffle of leg_1_rescaled_dt via default_rng(seed).
    p_value: empirical fraction of perm-max exceeding observed-max.
    """
    raise NotImplementedError("Plan 04-02 implements DEPEND-01 permutation null")
