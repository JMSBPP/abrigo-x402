"""Profile-likelihood eta-CI per Filimonov & Sornette 2014 + Wheatley ETH thesis.

NOT Hessian/Wald CI (Pitfall 4 — extends past [0, 1) and assumes asymptotic normality near boundary).
Q-9 trip wire: ci_width > 0.4 -> set q9_nullfire_triggered=True (PRE_REGISTRATION-locked).
"""
from __future__ import annotations
import numpy as np

Q9_CI_WIDTH_THRESHOLD: float = 0.4


def profile_likelihood_eta_ci(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    hawkes_fit: dict,
    decays: float,
    alpha: float = 0.05,
    eta_grid: np.ndarray | None = None,
) -> dict:
    """Profile-likelihood eta-CI. Returns: method="profile_likelihood", eta_hat, lower, upper,
    ci_width, alpha, q9_nullfire_triggered (bool: ci_width > 0.4)."""
    raise NotImplementedError("Wave 1 plan 03-06 implements this (DGP-06)")
