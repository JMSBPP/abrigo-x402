"""Provenance / lint tests for stress_report.json (Plan 04-07 Task 1 — RED stage).

Test cases:
  1. fixture-matches-schema: synthetic stress_report.json with all REQUIRED_STRESS_REPORT_KEYS
     round-trips through json.load + has all keys.
  2. lint_stress_report_json catches a missing key (corrupt the report by removing
     `divergence_flag`, assert at least one error mentions `divergence_flag`).
"""
import json
from pathlib import Path

from abrigo_x402.hedge.stress_test import REQUIRED_STRESS_REPORT_KEYS

# Import the linter from scripts/lint_artifacts.py via the established Plan 04-00 pattern.
import sys
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))
from lint_artifacts import lint_stress_report_json  # noqa: E402


def _build_valid_stress_report(tmp_path: Path) -> Path:
    """Synthesize a stress_report.json carrying all REQUIRED_STRESS_REPORT_KEYS."""
    report = {
        "chainId": "eip155:42220",
        "contractAddress": "0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F",
        "blockRange": [67_000_000, 67_100_000],
        "fetchTimestamp": "2026-05-27T18:00:00Z",
        "dataHash": "0" * 64,
        "gitCommit": "0" * 40,
        "run_id": "ichi-test-20260527",
        "independence_price": 1.0,
        "fitted_joint_price": 1.05,
        "comonotone_price": 1.10,
        "divergence_pct": 10.0,
        "divergence_flag": False,
        "comonotone_method": "empirical_body_parametric_tail",
    }
    path = tmp_path / "stress_report.json"
    path.write_text(json.dumps(report))
    return path


def test_fixture_matches_required_keys_schema(tmp_path):
    """Test 1: a synthetic report with REQUIRED_STRESS_REPORT_KEYS parses cleanly + all
    keys present after round-trip."""
    path = _build_valid_stress_report(tmp_path)
    data = json.loads(path.read_text())
    missing = set(REQUIRED_STRESS_REPORT_KEYS) - set(data.keys())
    assert not missing, f"fixture is missing locked keys: {missing}"
    # And the linter passes on the well-formed fixture:
    errors = lint_stress_report_json(path)
    assert errors == [], f"linter on valid fixture should return no errors; got {errors}"


def test_lint_catches_missing_divergence_flag(tmp_path):
    """Test 2: remove `divergence_flag` from the report; lint_stress_report_json returns
    at least one error mentioning that key."""
    path = _build_valid_stress_report(tmp_path)
    data = json.loads(path.read_text())
    del data["divergence_flag"]
    path.write_text(json.dumps(data))
    errors = lint_stress_report_json(path)
    assert len(errors) >= 1, "expected at least one error from a corrupted report"
    assert any("divergence_flag" in e for e in errors), (
        f"expected error to mention 'divergence_flag'; got: {errors}"
    )
