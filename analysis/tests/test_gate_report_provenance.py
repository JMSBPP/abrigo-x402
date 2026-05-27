"""Plan 04-04 (Wave 1) implements; Wave-0 stub validates symbol surface only."""
import pytest

pytestmark = pytest.mark.skip(reason="Plan 04-04 (Wave 1) implements gate_report.json provenance")


def test_smoke_imports():
    from abrigo_x402.hedge.falsification import REQUIRED_GATE_REPORT_KEYS  # noqa: F401
    from abrigo_x402.provenance import assert_has_header  # noqa: F401
