"""Plan 04-03 (Wave 1) implements; Wave-0 stub validates symbol surface only."""
import pytest

pytestmark = pytest.mark.skip(reason="Plan 04-03 (Wave 1) implements DEPEND-01 5-family BIC")


def test_smoke_imports():
    from abrigo_x402.dependence.copula import (  # noqa: F401
        fit_5_families_bic,
        REQUIRED_JOINT_DIST_KEYS,
        VINE_FALLBACK_DELTA_BIC_THRESHOLD,
        _pit_with_clipping,
    )
