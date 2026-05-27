"""DGP-06: Profile-likelihood eta-CI. Implemented by Wave 1 plan 03-06."""
import pytest

WAVE_1_PLAN = "03-06"
SKIP_REASON = f"Wave 1 plan {WAVE_1_PLAN} (DGP-06) implements"


@pytest.mark.skip(reason=SKIP_REASON)
def test_ci_covers_truth(synthetic_hawkes_eta_05_legs):
    """Profile-likelihood eta-CI on synthetic Hawkes(eta=0.5) covers 0.5."""


@pytest.mark.skip(reason=SKIP_REASON)
def test_ci_bounded():
    """eta-CI is bounded in [0, 1) -- never extends past 1."""


@pytest.mark.skip(reason=SKIP_REASON)
def test_q9_nullfire_trigger():
    """CI width > 0.4 sets q9_nullfire_triggered=True."""
