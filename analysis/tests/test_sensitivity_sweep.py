# Pattern I — thread-pin BLAS BEFORE any numpy import (Phase 3 SC-5 invariant).
import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

"""Phase 5 REPORT-03 — cost-prior sensitivity-sweep scaffold (Wave-0 RED/skip).

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

Underlying ``sensitivity_sweep.json`` lives at
``data/fits/ichi/bdaf5c7ba5a2/sensitivity_sweep.json`` (authored by Plan 05-01).
Wave 1 (Plan 05-01) implements ``abrigo_x402.report.sensitivity_sweep``;
the schema/grid stubs are xfail(strict=False).
"""
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SWEEP_JSON = REPO_ROOT / "data/fits/ichi/bdaf5c7ba5a2/sensitivity_sweep.json"


@pytest.mark.xfail(
    reason="Wave 1 (Plan 05-01) implements abrigo_x402.report.sensitivity_sweep",
    strict=False,
)
def test_schema_and_grid():
    """sensitivity_sweep.json has 9 cells over the PRE-REG-LOCKED grid."""
    import json

    sweep = json.loads(SWEEP_JSON.read_text())
    cells = sweep["cells"]
    assert len(cells) == 9
    rates = sorted({c["rate_per_event"] for c in cells})
    queries = sorted({c["USD_per_query"] for c in cells})
    assert rates == [1, 5, 10]
    assert queries == [2.5e-6, 5e-6, 7.5e-6]


@pytest.mark.xfail(
    reason="Wave 1 (Plan 05-01) implements abrigo_x402.report.sensitivity_sweep",
    strict=False,
)
def test_per_cell_conditions_recomputed():
    """Each cell carries the 4 qualitative convex-dominance booleans +
    firing_condition, re-evaluated via the existing gate machinery.

    (05-01 finalizes the exact field semantics + the honest 'recomputed' field
    name; the Wave-0 stub only locks that the 4 booleans + firing_condition are
    present per cell — it does NOT bake in a ``recomputed: true`` literal.)
    """
    import json

    sweep = json.loads(SWEEP_JSON.read_text())
    required_booleans = {
        "vol_of_vol",
        "positive_skew_fat_tails",
        "hawkes_self_excitation",
        "usdt_depeg_basis_jump",
    }
    for cell in sweep["cells"]:
        assert required_booleans.issubset(cell.keys())
        assert "firing_condition" in cell
        for key in required_booleans:
            assert isinstance(cell[key], bool)


def test_no_new_cost_model_introduced():
    """NOT xfail — runs NOW and MUST PASS. No cost-MODEL token may appear in
    analysis/src/ (κ / dominance_delta / cost_leg / cost_of_convexity). The
    grid axes rate_per_event / USD_per_query are DATA LABELS, not forbidden.
    Canonical forbidden-regex (identical in 05-01)."""
    result = subprocess.run(
        [
            "grep",
            "-rIE",
            r"kappa|κ|dominance_delta|def +cost_leg|cost_of_convexity",
            "analysis/src/",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    # returncode 1 == grep found NO match (the desired clean state).
    assert result.returncode == 1, f"forbidden cost-model token found:\n{result.stdout}"
