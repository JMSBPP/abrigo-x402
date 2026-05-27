"""Plan 04-06 (Wave 1) implements; Wave-0 stub validates symbol surface only."""
import pytest

pytestmark = pytest.mark.skip(reason="Plan 04-06 (Wave 1) implements HEDGE-03 LHS sensitivity")


def test_smoke_imports():
    from abrigo_x402.hedge.usdt_depeg import (  # noqa: F401
        load_calibration,
        generate_lhs_samples,
        run_lhs_sensitivity,
        DEFAULT_LAMBDA_J,
        DEFAULT_MU_J,
        DEFAULT_SIGMA_J,
        LHS_N_SAMPLES,
        JUMP_PARAMS_DEFAULT,
    )
