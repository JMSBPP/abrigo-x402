"""Plan 04-05 (Wave 1) implements; Wave-0 stub validates symbol surface only."""
import pytest

pytestmark = pytest.mark.skip(reason="Plan 04-05 (Wave 1) implements HEDGE-02 Carr-Madan strip")


def test_smoke_imports():
    from abrigo_x402.hedge.carr_madan_strip import (  # noqa: F401
        compute_strip,
        REQUIRED_STRIP_KEYS,
        STRIP_DEGENERATE_KEYS,
        POSITIVITY_TOLERANCE,
    )
