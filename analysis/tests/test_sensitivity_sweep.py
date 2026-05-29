# Pattern I — thread-pin BLAS BEFORE any numpy import (Phase 3 SC-5 invariant).
import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

"""Phase 5 REPORT-03 — cost-prior sensitivity-sweep tests (Plan 05-01, GREEN).

The sweep re-evaluates the FOUR QUALITATIVE convex-dominance conditions
(vol-of-vol>0, skew/kurtosis fat-tails, η ≥ threshold, USDT-depeg jump) plus the
firing_condition across the PRE-REGISTERED 3×3 grid (AF-03 lock):

    rate_per_event  ∈ {1, 5, 10}            (pre-reg §Prior Parameters — NOT 2.5/5/7.5)
    USD_per_query   ∈ {2.5e-6, 5e-6, 7.5e-6} (pre-reg ±50% of $5e-6)

→ 9 cells. The primary metric is the BOOLEAN condition set (NOT a dollar margin):
does the convex-demand call survive ±cost-prior perturbation? NO new cost-leg
model, NO dominance-Δ, NO κ index (AF-12 + CLAUDE.md non-negotiable). The grid
axes ``rate_per_event`` / ``USD_per_query`` are legitimate pre-reg DATA LABELS,
not a cost model — they are deliberately NOT in the forbidden-regex set.

HONESTY (reviewer MAJOR-D): the 4 conditions are parameter-free w.r.t. the cost
priors (they derive from the DGP density / residuals on disk, not the cost leg),
so the honest implementation EVALUATES the gate once (sources the booleans from
the gate's own evidence dict in ``gate_report.json``) and BROADCASTS to the grid,
labeling each cell ``evaluated_once / broadcast_to_grid / depends_on_cost_priors:
false`` — it does NOT attach a fabricated ``recomputed: true`` to a constant copy.
Test 2 ties each cell's booleans to the gate's OWN evidence values so a hardcoded
inline copy that drifted from the gate would fail.
"""
import json
import subprocess
from pathlib import Path

import pytest

from abrigo_x402.report.sensitivity_sweep import compute_sensitivity_sweep

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_DIR = REPO_ROOT / "data/fits/ichi/bdaf5c7ba5a2"
SWEEP_JSON = RUN_DIR / "sensitivity_sweep.json"

# CANONICAL forbidden-regex — byte-identical to Wave-0 (05-00) so the two cannot
# diverge. Reused verbatim in the acceptance one-liner.
FORBIDDEN_COST_MODEL_REGEX = r"kappa|κ|dominance_delta|def +cost_leg|cost_of_convexity"


@pytest.fixture(scope="module")
def sweep():
    """Run compute_sensitivity_sweep once against the real run dir and read back
    the JSON it writes."""
    compute_sensitivity_sweep(RUN_DIR)
    return json.loads(SWEEP_JSON.read_text())


@pytest.fixture(scope="module")
def gate_report():
    return json.loads((RUN_DIR / "gate_report.json").read_text())


def test_schema_and_grid(sweep):
    """sensitivity_sweep.json has 9 cells over the PRE-REG-LOCKED grid."""
    assert set(
        ["run_id", "grid", "all_cells_any_condition_passed",
         "conditions_cost_prior_invariant", "caveat"]
    ).issubset(sweep.keys())
    grid = sweep["grid"]
    assert isinstance(grid, list)
    assert len(grid) == 9
    rates = {c["rate_per_event"] for c in grid}
    queries = {c["USD_per_query"] for c in grid}
    assert rates == {1, 5, 10}
    assert queries == {2.5e-6, 5e-6, 7.5e-6}
    assert sweep["run_id"] == "bdaf5c7ba5a2"


def test_per_cell_evaluated_and_broadcast(sweep, gate_report):
    """Each of the 9 cells carries the 4 qualitative convex-dominance booleans
    (nested under ``conditions``) + the firing_condition, sourced from a REAL
    gate evaluation (the gate's own evidence dict) and broadcast HONESTLY.

    The booleans MUST equal the gate's OWN evidence values — a hardcoded inline
    copy that drifted from the gate source would fail this. No cell may carry a
    bare ``recomputed: true`` literal."""
    cond_keys = {
        "vol_of_vol_gt_zero",
        "positive_skew_fat_tails",
        "hawkes_self_excitation",
        "usdt_depeg_basis_jump",
    }
    grid = sweep["grid"]
    assert len(grid) == 9
    for cell in grid:
        assert {"rate_per_event", "USD_per_query", "conditions",
                "any_condition_passed", "firing_condition",
                "evaluated_once", "broadcast_to_grid",
                "depends_on_cost_priors"}.issubset(cell.keys())
        conditions = cell["conditions"]
        assert cond_keys == set(conditions.keys())
        # conditions are booleans
        for k in cond_keys:
            assert isinstance(conditions[k], bool)
        # firing_condition per cell
        assert cell["firing_condition"] == "null_strip_unavailable"
        # honest broadcast labels
        assert cell["evaluated_once"] is True
        assert cell["broadcast_to_grid"] is True
        assert cell["depends_on_cost_priors"] is False
        # NO fabricated recompute flag anywhere in the cell
        assert "recomputed" not in cell
        # THE INVOCATION WAS REAL: each boolean equals the gate's own evidence.
        for k in cond_keys:
            assert conditions[k] == gate_report[k]["passed"]
        assert cell["any_condition_passed"] == gate_report["any_condition_passed"]


def test_invariance_reported_honestly(sweep):
    """The 4 conditions are parameter-free w.r.t. the cost priors → the sweep is
    cost-prior-INVARIANT, reported honestly as the convexity-driven finding."""
    assert sweep["conditions_cost_prior_invariant"] is True
    assert sweep["all_cells_any_condition_passed"] is True
    assert all(c["any_condition_passed"] is True for c in sweep["grid"])
    caveat = sweep["caveat"]
    assert "modeled-not-paid" in caveat
    assert "convexity-driven" in caveat


def test_no_new_cost_model_introduced():
    """NOT a recompute test — runs NOW and MUST PASS. No cost-MODEL token may
    appear in analysis/src/ (κ / dominance_delta / cost_leg / cost_of_convexity).
    The grid axes rate_per_event / USD_per_query are DATA LABELS, not forbidden.
    Canonical forbidden-regex (byte-identical to 05-00)."""
    result = subprocess.run(
        ["grep", "-rIE", FORBIDDEN_COST_MODEL_REGEX, "analysis/src/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    # returncode 1 == grep found NO match (the desired clean state).
    assert result.returncode == 1, f"forbidden cost-model token found:\n{result.stdout}"
