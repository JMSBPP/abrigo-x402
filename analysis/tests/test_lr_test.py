"""DGP-03: Boundary-correct parametric bootstrap LR test. Implemented by Wave 1 plan 03-03."""
import pytest

WAVE_1_PLAN = "03-03"
SKIP_REASON = f"Wave 1 plan {WAVE_1_PLAN} (DGP-03) implements"


@pytest.mark.skip(reason=SKIP_REASON)
def test_null_distribution_mixture_shape(synthetic_nhpp_baseline_only_legs, synthetic_end_time):
    """Bootstrap null distribution shows the 50:50 mixture (point mass at 0 + continuous tail)."""


@pytest.mark.skip(reason=SKIP_REASON)
def test_power_on_synthetic_hawkes(synthetic_hawkes_eta_05_legs, synthetic_end_time):
    """Bootstrap LR rejects at alpha=0.01 on synthetic Hawkes with eta=0.5 (power test, n_reps=200)."""


@pytest.mark.skip(reason=SKIP_REASON)
def test_size_calibration(synthetic_nhpp_baseline_only_legs, synthetic_end_time):
    """Bootstrap LR ~1% rejection on synthetic NHPP (size calibration at alpha=0.01, n_reps=200)."""


@pytest.mark.skip(reason=SKIP_REASON)
def test_diagnostic_plot_renders(synthetic_nhpp_baseline_only_legs, synthetic_end_time, tmp_path):
    """reports/_diagnostics/lr_null_dist.png renders headless with nonzero size."""
