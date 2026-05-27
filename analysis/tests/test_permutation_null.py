"""Plan 04-02 (Wave 1) implements; Wave-0 stub validates symbol surface only."""
import pytest

pytestmark = pytest.mark.skip(reason="Plan 04-02 (Wave 1) implements DEPEND-01 permutation null")


def test_smoke_imports():
    from abrigo_x402.dependence.permutation_null import permutation_null_max_abs_rho  # noqa: F401
