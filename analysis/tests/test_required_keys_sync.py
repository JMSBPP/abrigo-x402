"""Wave-0 scaffold-time invariant: every REQUIRED_*_KEYS tuple in
analysis/src/abrigo_x402/{dependence,hedge}/*.py MUST equal the corresponding
frozenset in scripts/lint_artifacts.py.

This test is NOT skip-marked — it runs at Wave 0 to catch the mismatched-tuple
regression class BEFORE Wave 1 lands real artifacts.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from abrigo_x402.dependence.copula import REQUIRED_JOINT_DIST_KEYS  # noqa: E402
from abrigo_x402.hedge.falsification import REQUIRED_GATE_REPORT_KEYS  # noqa: E402
from abrigo_x402.hedge.stress_test import REQUIRED_STRESS_REPORT_KEYS  # noqa: E402
from abrigo_x402.hedge.carr_madan_strip import (  # noqa: E402
    REQUIRED_STRIP_KEYS,
    STRIP_DEGENERATE_KEYS,
)
from lint_artifacts import (  # noqa: E402
    JOINT_DIST_REQUIRED_KEYS,
    GATE_REPORT_REQUIRED_KEYS,
    STRESS_REPORT_REQUIRED_KEYS,
    STRIP_REQUIRED_KEYS,
    STRIP_DEGENERATE_REQUIRED_KEYS,
)


def test_joint_dist_keys_sync():
    assert frozenset(REQUIRED_JOINT_DIST_KEYS) == JOINT_DIST_REQUIRED_KEYS


def test_gate_report_keys_sync():
    assert frozenset(REQUIRED_GATE_REPORT_KEYS) == GATE_REPORT_REQUIRED_KEYS


def test_stress_report_keys_sync():
    assert frozenset(REQUIRED_STRESS_REPORT_KEYS) == STRESS_REPORT_REQUIRED_KEYS


def test_strip_keys_sync():
    assert frozenset(REQUIRED_STRIP_KEYS) == STRIP_REQUIRED_KEYS


def test_strip_degenerate_keys_sync():
    assert frozenset(STRIP_DEGENERATE_KEYS) == STRIP_DEGENERATE_REQUIRED_KEYS
