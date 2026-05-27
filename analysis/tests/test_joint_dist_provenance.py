"""Plan 04-03 (Wave 1) implements; Wave-0 stub validates symbol surface only."""
import pytest

pytestmark = pytest.mark.skip(reason="Plan 04-03 (Wave 1) implements joint_dist.json provenance")


def test_smoke_imports():
    from abrigo_x402.dependence.copula import REQUIRED_JOINT_DIST_KEYS  # noqa: F401
    from abrigo_x402.provenance import assert_has_header  # noqa: F401
