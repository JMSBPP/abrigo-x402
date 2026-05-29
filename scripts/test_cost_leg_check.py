"""Contract tests for scripts/cost_leg_check.py (REPRO-03 first-step tool).

Verifies the emitted notes/steer_cost_leg_bound.md satisfies the HEDGE-05
parser contract (verdict FAIL -> null_cost) on the real pre-committed Steer
band, and that the conservative-fail rule is symmetric (a strictly-above
synthetic band yields PASS).

The import of `_parse_cost_leg_bound_verdict` is TEST-ONLY — it pins the
script's output to the exact frontmatter contract the production decision tree
consumes. It does NOT make scripts/cost_leg_check.py itself depend on
analysis/src (the script is stdlib-only; this test merely cross-checks).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# Repo root: scripts/ is a direct child of the repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]

# Load the stdlib-only script as a module without requiring it on sys.path.
_spec = importlib.util.spec_from_file_location(
    "cost_leg_check", REPO_ROOT / "scripts" / "cost_leg_check.py"
)
assert _spec is not None and _spec.loader is not None
cost_leg_check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cost_leg_check)

# Test-only import of the production parser contract.
sys.path.insert(0, str(REPO_ROOT / "analysis" / "src"))
from abrigo_x402.hedge.null_result import _parse_cost_leg_bound_verdict  # noqa: E402


def test_steer_band_yields_fail_and_null_cost(tmp_path: Path) -> None:
    out = tmp_path / "steer_cost_leg_bound.md"
    rc = cost_leg_check.main(
        ["--protocol", str(REPO_ROOT / "protocols" / "steer.toml"), "--out", str(out)]
    )
    assert rc == 0
    # (1) the production parser reads verdict == FAIL.
    assert _parse_cost_leg_bound_verdict(out) == "FAIL"
    text = out.read_text()
    # (2) the firing condition is wired to null_cost.
    assert "firing_condition: null_cost" in text
    # (4) the file begins with `---` on line 1 (regex-match safe).
    assert text.splitlines()[0] == "---"


def test_strictly_above_band_yields_pass() -> None:
    # (3) rule symmetry: a band STRICTLY ABOVE 100k -> PASS.
    assert (
        cost_leg_check.adjudicate(
            lower_bound=120_000, upper_bound=200_000, demand_window_lower_bound=100_000
        )
        == "PASS"
    )


def test_straddle_band_yields_fail() -> None:
    # The Steer case: 30k-100k is NOT strictly above 100k -> FAIL.
    assert (
        cost_leg_check.adjudicate(
            lower_bound=30_000, upper_bound=100_000, demand_window_lower_bound=100_000
        )
        == "FAIL"
    )


def test_band_at_ceiling_is_fail() -> None:
    # Boundary: lower == ceiling is NOT strictly above -> FAIL (conservative).
    assert (
        cost_leg_check.adjudicate(
            lower_bound=100_000, upper_bound=150_000, demand_window_lower_bound=100_000
        )
        == "FAIL"
    )
