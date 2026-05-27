"""Plan 04-08 (Wave 2) implements; Wave-0 stub validates symbol surface only."""
import pytest

pytestmark = pytest.mark.skip(reason="Plan 04-08 (Wave 2) implements HEDGE-05 null-result rendering")


def test_smoke_imports():
    from abrigo_x402.hedge.null_result import (  # noqa: F401
        decide_firing_condition,
        render_null_result_pdf,
        HEDGE05_SIGNATURE,
    )
