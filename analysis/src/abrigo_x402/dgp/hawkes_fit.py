"""Bivariate exponential-kernel Hawkes fit via tick.HawkesExpKern. Full off-diagonal alpha matrix."""
from __future__ import annotations
import numpy as np

DECAY_GRID: tuple[float, ...] = (0.01, 0.1, 1.0, 10.0)


def fit_hawkes_expkern(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    decays: float | None = None,
) -> dict:
    """MLE fit. If decays is None, AIC-min over DECAY_GRID. Returns dict with baseline (list[2]),
    adjacency (list[list[float]]), decays, branching_ratio, loglik_in_sample, boundary_warning (bool)."""
    raise NotImplementedError("Wave 1 plan 03-02 implements this (DGP-02)")


def fit_hawkes_with_fixed_branching_ratio(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    eta_target: float,
    decays: float,
) -> dict:
    """Constrained fit: spectral radius of alpha/beta = eta_target exactly. Profile-likelihood inner loop."""
    raise NotImplementedError("Wave 1 plan 03-06 implements this (DGP-06 profile likelihood)")


def compute_branching_ratio(adjacency: np.ndarray, decays: float) -> float:
    """Spectral radius of (adjacency / decays) for scalar beta. NOT max element (Pitfall 6)."""
    raise NotImplementedError("Wave 1 plan 03-02 implements this (DGP-02)")
