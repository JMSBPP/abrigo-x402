"""Orchestrator production-path tests (Plan 04.1.1-02b).

Asserts that the production fit path (`run_fit` with the default `decays`) runs the
free-β AIC grid — the canonical v2 estimator (`scipy_canonical_ll`, AIC-min over the
6-point DECAY_GRID) — rather than the kernel-blind hardcoded β=0.1 that the Plan
04.1.1-03 BLOCKER surfaced.

THREAD PINNING (Pattern I — carried from test_byte_identical.py):
statsmodels VAR.select_order AIC drifts in the last bits under multi-thread BLAS, and the
free-β AIC selection itself depends on deterministic LL evaluation. Pin BLAS / OMP / MKL /
OpenBLAS / NumExpr to 1 thread BEFORE the first numpy import (transitive via run_fit). The
os.environ.setdefault block MUST be the first executable code in the file.
"""
# === THREAD PINNING — must run BEFORE any numpy/statsmodels import (transitive via run_fit) ===
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
# === end thread pinning ===

import json

import polars as pl
import pytest

from abrigo_x402.dgp.hawkes_fit import DECAY_GRID
from abrigo_x402.dgp.orchestrator import run_fit


@pytest.fixture
def small_panel_path(tmp_path, synthetic_hawkes_eta_05_legs):
    """A small two-leg synthetic panel in the Phase-2 PANEL-02 column shape.

    Built from the regenerated Hawkes(η=0.5) fixture legs so the production fit has
    genuine self-excitation to select a β over — the AIC grid then has a real minimum,
    not a flat tie. Truncated to keep the bootstrap-free run tractable.
    """
    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    rows = []
    block_offset = 67_378_253
    for t in leg_0[:250]:
        rows.append({
            "block_timestamp": float(t),
            "blockNumber": block_offset + int(t),
            "event_name": "Swap",
            "amount0": "100", "amount1": "-100",
            "txHash": "0x" + "00" * 32, "logIndex": 0,
            "contractAddress": "0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F",
            "blockHash": "0x" + "00" * 32,
        })
    for t in leg_1[:250]:
        rows.append({
            "block_timestamp": float(t),
            "blockNumber": block_offset + int(t) + 1,
            "event_name": "Swap",
            "amount0": "-100", "amount1": "100",
            "txHash": "0x" + "11" * 32, "logIndex": 0,
            "contractAddress": "0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F",
            "blockHash": "0x" + "00" * 32,
        })
    df = pl.DataFrame(rows)
    panel_path = tmp_path / "67378253_67896653.parquet"
    df.write_parquet(panel_path)
    return panel_path


def test_run_fit_uses_free_beta_aic_grid(small_panel_path, tmp_path):
    """The production fit path must run the free-β AIC grid (all 6 DECAY_GRID points),
    NOT the kernel-blind single-β β=0.1 the Plan 04.1.1-03 BLOCKER surfaced.

    RED against `decays: float = 0.1` (1-point decay_aic_table); GREEN once the default
    is `decays=None` (6-point grid). Calls run_fit WITHOUT passing decays so it exercises
    the production default.
    """
    # Sanity guard: thread pinning must be in effect (deterministic AIC selection).
    assert os.environ.get("OMP_NUM_THREADS") == "1", "OMP_NUM_THREADS not pinned to 1"

    result = run_fit(small_panel_path, tmp_path / "run", bootstrap_reps=10)
    report = json.loads(result.fit_report_path.read_text())

    hawkes = report["hawkes_mv_params"]

    # The free-β AIC grid evaluated all 6 DECAY_GRID points.
    aic_table = hawkes["decay_aic_table"]
    assert len(aic_table) == len(DECAY_GRID), (
        f"decay_aic_table has {len(aic_table)} entries, expected {len(DECAY_GRID)} "
        f"(the full DECAY_GRID). A 1-entry table means run_fit pinned a single β "
        f"(the kernel-blind β=0.1 BLOCKER) instead of the free-β AIC grid."
    )
    # Every DECAY_GRID value is present as a key.
    for d in DECAY_GRID:
        assert str(d) in aic_table, f"DECAY_GRID value {d} missing from decay_aic_table"

    # The canonical v2 estimator ran.
    assert hawkes["fit_method_used"] == "scipy_canonical_ll", (
        f"fit_method_used={hawkes['fit_method_used']!r}, expected 'scipy_canonical_ll'"
    )

    # The selected β is the AIC-min over the grid (sanity: the chosen β minimizes the table).
    selected = float(hawkes["decays"])
    aic_min_beta = float(min(aic_table, key=lambda k: aic_table[k]))
    assert selected == pytest.approx(aic_min_beta), (
        f"selected β={selected} is not the AIC-min β={aic_min_beta} of the grid"
    )
