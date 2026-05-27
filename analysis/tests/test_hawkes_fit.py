"""DGP-02: tick.HawkesExpKern fit tests."""
import numpy as np
import pytest

from abrigo_x402.dgp.hawkes_fit import (
    DECAY_GRID,
    compute_branching_ratio,
    fit_hawkes_expkern,
)


def test_full_offdiag(synthetic_hawkes_eta_05_legs):
    """Fit produces 2x2 adjacency with off-diagonal NOT forced to 0 (Pitfall §5 — diagonal-only Hawkes anti-pattern)."""
    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    fit = fit_hawkes_expkern(leg_0, leg_1, decays=0.1)
    adjacency = np.asarray(fit["adjacency"])
    assert adjacency.shape == (2, 2)
    # Full off-diagonal: at least one off-diagonal element strictly positive (not forced to 0)
    assert adjacency[0, 1] > 0.0 or adjacency[1, 0] > 0.0, (
        f"Off-diagonal forced to 0 — diagonal-only Hawkes anti-pattern detected: {adjacency}"
    )


def test_branching_ratio_spectral():
    """Branching ratio = spectral radius of alpha/beta, not max element (Pitfall 6)."""
    # Adjacency where max element (0.4) differs from spectral radius (0.3)
    adjacency = np.array([[0.3, 0.0], [0.4, 0.0]], dtype=np.float64)
    decays = 1.0
    eta = compute_branching_ratio(adjacency, decays)
    # Eigenvalues of [[0.3, 0], [0.4, 0]] are 0.3 and 0.0 -> spectral radius = 0.3
    assert eta == pytest.approx(0.3, rel=1e-6), (
        f"Got {eta} — likely returned max element 0.4 (Pitfall 6)"
    )


def test_simultaneous_events():
    """Same-block timestamps handled without logIndex tie-breaking (Pitfall 7).

    Construct two legs with several identical timestamps (same-block ties); tick must
    accept them natively without raising and produce a well-formed adjacency."""
    rng = np.random.default_rng(42)
    base_times = np.sort(rng.uniform(100.0, 2_000_000.0, 350))
    leg_0 = base_times.copy()
    leg_1 = base_times.copy()
    # Add unique timestamps to each leg so the streams aren't perfectly identical
    leg_0 = np.sort(np.concatenate([leg_0, rng.uniform(100.0, 2_000_000.0, 30)]))
    leg_1 = np.sort(np.concatenate([leg_1, rng.uniform(100.0, 2_000_000.0, 30)]))
    # Should fit without raising — tick handles ties natively
    fit = fit_hawkes_expkern(leg_0, leg_1, decays=0.1)
    adjacency = np.asarray(fit["adjacency"])
    assert np.isfinite(adjacency).all(), "NaN/inf in adjacency — tick failed to handle ties"
    assert fit["branching_ratio"] >= 0.0


def test_decay_grid_constant():
    """DECAY_GRID is the locked Wheatley-thesis decay search grid."""
    assert DECAY_GRID == (0.01, 0.1, 1.0, 10.0)
