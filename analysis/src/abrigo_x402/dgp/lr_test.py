"""Boundary-correct parametric bootstrap LR test (50:50 mixture null at the parameter boundary).

PROHIBITED IMPORTS (SC-3 grep gate enforced by scripts/ + Makefile):
  - statsmodels diagnostic LR helper (asymptotic-only)
  - any scipy chi-squared survival-function call for the null distribution
Use ONLY the bootstrap rig (Pattern 3, Cavaliere et al. 2022 arxiv:2104.03122).
The mixture is 50% point-mass at zero plus 50% chi-squared with one degree of freedom; see PRE_REGISTRATION.md.
"""
from __future__ import annotations
import numpy as np


def parametric_bootstrap_lr(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    panel_data_hash: str,
    window_start: float,
    window_end: float,
    n_reps: int = 1000,
    alpha: float = 0.01,
    diagnostic_plot_path: str | None = None,
) -> dict:
    """Parametric bootstrap LR. Simulates UNDER THE NULL (NHPP, not Hawkes).

    Deterministic seed: sha256(panel_data_hash + "phase-3-bootstrap").digest()[:4] as uint32.
    Returns dict: observed_stat, bootstrap_null_dist_50_50_chi2_0_chi2_1 (list), p_value,
    rejects_at_alpha (bool), n_reps, n_successful_bootstrap, n_failed, seed, alpha.
    """
    raise NotImplementedError("Wave 1 plan 03-03 implements this (DGP-03)")
