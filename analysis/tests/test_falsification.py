"""Plan 04-04 (Wave 1) implements; Wave-0 stub validates symbol surface only."""
import pytest

pytestmark = pytest.mark.skip(reason="Plan 04-04 (Wave 1) implements HEDGE-01 four-condition gate")


def test_smoke_imports():
    from abrigo_x402.hedge.falsification import (  # noqa: F401
        evaluate_condition_1_vol_of_vol,
        evaluate_condition_2_skew_fat_tails,
        evaluate_condition_3_hawkes_self_excitation,
        evaluate_condition_4_usdt_depeg,
        evaluate_four_conditions,
        REQUIRED_GATE_REPORT_KEYS,
    )
