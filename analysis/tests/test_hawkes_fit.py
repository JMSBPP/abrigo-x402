"""DGP-02: tick.HawkesExpKern fit tests. Implemented by Wave 1 plan 03-02."""
import pytest

WAVE_1_PLAN = "03-02"
SKIP_REASON = f"Wave 1 plan {WAVE_1_PLAN} (DGP-02) implements"


@pytest.mark.skip(reason=SKIP_REASON)
def test_full_offdiag(synthetic_hawkes_eta_05_legs):
    """Fit produces 2x2 adjacency with off-diagonal NOT forced to 0."""


@pytest.mark.skip(reason=SKIP_REASON)
def test_branching_ratio_spectral():
    """Branching ratio = spectral radius of alpha/beta, not max element (Pitfall 6)."""


@pytest.mark.skip(reason=SKIP_REASON)
def test_simultaneous_events():
    """Same-block timestamps handled without logIndex tie-breaking (Pitfall 7)."""
