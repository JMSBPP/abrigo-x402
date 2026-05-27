"""DGP-04: Wall-clock 80/20 held-out split. Implemented by Wave 1 plan 03-04."""
import pytest

WAVE_1_PLAN = "03-04"
SKIP_REASON = f"Wave 1 plan {WAVE_1_PLAN} (DGP-04) implements"


@pytest.mark.skip(reason=SKIP_REASON)
def test_wallclock_split():
    """Split is wall-clock not event-count: t_split = window_start + 0.8*(window_end - window_start)."""


@pytest.mark.skip(reason=SKIP_REASON)
def test_in_sample_only_raises():
    """In-sample-only fit attempt raises InsufficientEvaluationError."""
