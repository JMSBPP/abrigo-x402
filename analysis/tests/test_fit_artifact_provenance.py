"""SC-1: fit_report.json metadata header. Implemented by Wave 2 plan 03-07."""
import pytest

WAVE_PLAN = "03-07"
SKIP_REASON = f"Wave 2 plan {WAVE_PLAN} (SC-1) implements"


@pytest.mark.skip(reason=SKIP_REASON)
def test_metadata_keys():
    """fit_report.json carries chainId, contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit."""
