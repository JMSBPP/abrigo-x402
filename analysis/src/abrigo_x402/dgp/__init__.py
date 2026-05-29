"""DGP estimation submodule (Phase 3): NHPP-INAR(p) null + bivariate Hawkes alt + boundary-correct LR + time-rescaling KS + profile-likelihood eta-CI + held-out + stationarity diagnostic."""
from .nhpp_inar import fit_nhpp_inar
from .hawkes_fit import fit_hawkes_expkern, fit_hawkes_with_fixed_branching_ratio, compute_branching_ratio
from .lr_test import parametric_bootstrap_lr
from .time_rescaling import time_rescaling_ks_test_leg, compute_compensator_exp_kernel
from .profile_likelihood import profile_likelihood_eta_ci
from .held_out import (
    wall_clock_split,
    compute_held_out_loglik_hawkes,
    compute_held_out_loglik_nhpp,
    InsufficientEvaluationError,
    WallClockSplit,
)
from .stationarity import baseline_stationarity_check
from .orchestrator import run_fit

__all__ = [
    "fit_nhpp_inar", "fit_hawkes_expkern", "fit_hawkes_with_fixed_branching_ratio", "compute_branching_ratio",
    "parametric_bootstrap_lr", "time_rescaling_ks_test_leg", "compute_compensator_exp_kernel",
    "profile_likelihood_eta_ci",
    "wall_clock_split", "compute_held_out_loglik_hawkes", "compute_held_out_loglik_nhpp",
    "InsufficientEvaluationError", "WallClockSplit",
    "baseline_stationarity_check", "run_fit",
]
