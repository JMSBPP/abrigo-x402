"""SC-5: Byte-identical fit_report.json + residuals.parquet across two runs. Implemented by Wave 2 plan 03-07."""
import pytest

WAVE_PLAN = "03-07"
SKIP_REASON = f"Wave 2 plan {WAVE_PLAN} (SC-5) implements"


@pytest.mark.skip(reason=SKIP_REASON)
def test_deterministic_fit():
    """Two runs with identical input panel + git commit produce byte-identical fit_report.json + residuals.parquet (modulo wall-clock fields)."""
