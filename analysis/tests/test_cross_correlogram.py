"""Plan 04-01 (Wave 1) implements; Wave-0 stub validates symbol surface only."""
import pytest

pytestmark = pytest.mark.skip(reason="Plan 04-01 (Wave 1) implements DEPEND-01 cross-correlogram")


def test_smoke_imports():
    from abrigo_x402.dependence.cross_correlogram import cross_correlogram_event_index  # noqa: F401
