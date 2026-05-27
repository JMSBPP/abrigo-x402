"""DGP-04 + PITFALLS section 4: baseline stationarity diagnostic. Implemented by Wave 1 plan 03-04."""
import pytest

WAVE_1_PLAN = "03-04"
SKIP_REASON = f"Wave 1 plan {WAVE_1_PLAN} (DGP-04 stationarity) implements"


@pytest.mark.skip(reason=SKIP_REASON)
def test_piecewise_required_on_drifted_synthetic():
    """Non-stationary synthetic (rate drift > 25%) flags decision='piecewise_required'."""
