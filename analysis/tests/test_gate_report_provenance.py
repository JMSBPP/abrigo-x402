"""gate_report.json provenance + schema completeness tests (Plan 04-04).

Mirrors the Phase 3 fit_report.json provenance test pattern.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_gate_report_fixture_has_all_required_keys(gate_report_fixture: dict) -> None:
    """gate_report_fixture (from conftest) MUST contain every REQUIRED_GATE_REPORT_KEYS entry."""
    from abrigo_x402.hedge.falsification import REQUIRED_GATE_REPORT_KEYS

    missing = [k for k in REQUIRED_GATE_REPORT_KEYS if k not in gate_report_fixture]
    assert missing == [], (
        f"gate_report_fixture is missing required keys: {missing}. "
        f"REQUIRED_GATE_REPORT_KEYS = {REQUIRED_GATE_REPORT_KEYS}"
    )


def test_lint_gate_report_catches_missing_key(tmp_path: Path, gate_report_fixture: dict) -> None:
    """lint_gate_report_json must flag a fixture missing `any_condition_passed`."""
    import sys

    # Import the lint helper via direct path append (scripts/ is not a package).
    repo_root = Path(__file__).resolve().parents[2]
    scripts_dir = repo_root / "scripts"
    sys.path.insert(0, str(scripts_dir))
    try:
        from lint_artifacts import lint_gate_report_json  # type: ignore[import-not-found]
    finally:
        sys.path.remove(str(scripts_dir))

    corrupted = dict(gate_report_fixture)
    corrupted.pop("any_condition_passed")
    corrupted_path = tmp_path / "gate_report.json"
    corrupted_path.write_text(json.dumps(corrupted))

    errors = lint_gate_report_json(corrupted_path)
    assert errors, "lint_gate_report_json must report at least one error on missing key"
    assert any("any_condition_passed" in e for e in errors), (
        f"Expected `any_condition_passed` in error messages, got: {errors}"
    )
