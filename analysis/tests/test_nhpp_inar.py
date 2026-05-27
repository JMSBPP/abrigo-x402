"""DGP-01: Kirchner INAR(p) NHPP fit tests. Implemented by Wave 1 plan 03-01."""
import pytest

WAVE_1_PLAN = "03-01"
SKIP_REASON = f"Wave 1 plan {WAVE_1_PLAN} (DGP-01) implements"


@pytest.mark.skip(reason=SKIP_REASON)
def test_recovers_synthetic_ground_truth(synthetic_nhpp_baseline_only_legs, synthetic_end_time):
    """1000 paths from SimuHawkesExpKernels(alpha=0), refit Kirchner INAR(p), assert recovered baseline within +/-10%."""


@pytest.mark.skip(reason=SKIP_REASON)
def test_aic_bin_selection(synthetic_nhpp_baseline_only_legs, synthetic_end_time):
    """AIC-min selects bin width from {60, 300, 900, 3600}s."""


@pytest.mark.skip(reason=SKIP_REASON)
def test_nonneg_projection():
    """Negative VAR coefficients clamped to 0 (Kirchner step)."""
