"""DGP-05: Brown 2002 time-rescaling KS test. Implemented by Wave 1 plan 03-05."""
import pytest

WAVE_1_PLAN = "03-05"
SKIP_REASON = f"Wave 1 plan {WAVE_1_PLAN} (DGP-05) implements"


@pytest.mark.skip(reason=SKIP_REASON)
def test_passes_on_true_model(synthetic_hawkes_eta_05_legs):
    """KS test on correctly-specified Hawkes synthetic passes (p > 0.05)."""


@pytest.mark.skip(reason=SKIP_REASON)
def test_fails_on_misspecified():
    """NHPP rescaling of true-Hawkes data fails KS (p < 0.05)."""


@pytest.mark.skip(reason=SKIP_REASON)
def test_compensator_closed_form():
    """Closed-form Lambda(t) for exponential kernel matches numerical integration to 1e-9."""
