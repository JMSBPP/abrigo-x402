"""DGP-03: parametric bootstrap LR test.

Tests the boundary-correct bootstrap rig in `abrigo_x402.dgp.lr_test.parametric_bootstrap_lr`:
- Null distribution mixture shape (point mass at 0 + continuous right tail)
- Power on synthetic Hawkes (eta=0.5)
- Size calibration (p-value in [0, 1] sanity, loose bound)
- Diagnostic PNG renders headless under matplotlib Agg
- SC-3 grep gate: source contains zero hits for forbidden helpers
- Deterministic seed: same panel_data_hash -> byte-identical null distribution
- Phase 04.1.1-v2 Option A: scipy observed fit + tick-LS null replicates;
  observed_stat on a self-consistent canonical-LL scale (6.05M pathology resolved)
"""
# Pattern I thread-pinning — MUST precede any numpy/scipy/tick import (SC-5 byte-identity).
import os  # noqa: E402

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import subprocess  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

from abrigo_x402.dgp.lr_test import (  # noqa: E402
    _fit_hawkes_ls_for_null,
    parametric_bootstrap_lr,
)

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
WINDOW_START = 0.0
WINDOW_END = 2_592_000.0  # 30 days


def test_null_distribution_mixture_shape(synthetic_nhpp_baseline_only_legs):
    """Bootstrap null distribution shows the 50:50 mixture (point mass at 0 + continuous tail).

    Structural signature: NOT all-zero AND NOT continuous-only.
    """
    leg_0, leg_1 = synthetic_nhpp_baseline_only_legs
    result = parametric_bootstrap_lr(
        leg_0,
        leg_1,
        panel_data_hash="test-nhpp-mixture-shape",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        n_reps=200,
    )
    null = np.asarray(result["bootstrap_null_dist_50_50_chi2_0_chi2_1"])
    assert null.size > 0, "Bootstrap null distribution is empty"
    near_zero_frac = float(np.mean(null <= 1e-6))
    continuous_frac = float(np.mean(null > 1e-3))
    # Mixture signature: NOT all-zero AND NOT continuous-only
    assert near_zero_frac < 1.0, (
        f"All values at zero — bootstrap is broken (continuous tail missing); "
        f"near_zero_frac={near_zero_frac:.3f}"
    )
    assert continuous_frac < 1.0, (
        f"All values continuous — bootstrap is broken (point mass at 0 missing); "
        f"continuous_frac={continuous_frac:.3f}"
    )


def test_power_on_synthetic_hawkes(synthetic_hawkes_eta_05_legs):
    """Bootstrap LR should detect Hawkes departure from NHPP null on the eta=0.5 fixture."""
    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    result = parametric_bootstrap_lr(
        leg_0,
        leg_1,
        panel_data_hash="test-hawkes-power",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        n_reps=200,
        alpha=0.05,
    )
    p_value = result["p_value"]
    assert p_value < 0.10 or result["rejects_at_alpha"], (
        f"Expected power on eta=0.5 synthetic Hawkes; got p_value={p_value}"
    )


def test_size_calibration(synthetic_nhpp_baseline_only_legs):
    """Loose sanity: p_value lives in [0, 1] on synthetic NHPP at alpha=0.01.

    Reduced from 1000-rep production to 50 inner reps for runtime; the
    production-rep size sweep runs once in Plan 03-08.
    """
    leg_0, leg_1 = synthetic_nhpp_baseline_only_legs
    result = parametric_bootstrap_lr(
        leg_0,
        leg_1,
        panel_data_hash="test-size-cal",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        n_reps=50,
        alpha=0.01,
    )
    assert 0.0 <= result["p_value"] <= 1.0


def test_diagnostic_plot_renders(synthetic_nhpp_baseline_only_legs, tmp_path):
    """`reports/_diagnostics/lr_null_dist.png`-shaped PNG renders headless with nonzero size."""
    leg_0, leg_1 = synthetic_nhpp_baseline_only_legs
    plot_path = tmp_path / "lr_null_dist.png"
    parametric_bootstrap_lr(
        leg_0,
        leg_1,
        panel_data_hash="test-plot",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        n_reps=50,
        diagnostic_plot_path=str(plot_path),
    )
    assert plot_path.exists(), "Diagnostic PNG was not written"
    assert plot_path.stat().st_size > 1024, "Diagnostic PNG suspiciously small"


def test_grep_gate_forbidden_calls_absent():
    """SC-3 grep gate: source must contain zero hits for `likelihood_ratio_test` or `chi2(1).sf`."""
    result = subprocess.run(
        [
            "grep",
            "-rE",
            r"likelihood_ratio_test|chi2\(1\)\.sf",
            "src/abrigo_x402/dgp/lr_test.py",
        ],
        cwd=ANALYSIS_ROOT,
        capture_output=True,
        text=True,
    )
    # grep exits 1 on no match (success for us), 0 on match (failure for us)
    assert result.returncode != 0, (
        f"Forbidden anti-pattern found in lr_test.py:\n{result.stdout}"
    )


def test_option_a_null_replicates_use_ls(synthetic_nhpp_baseline_only_legs):
    """Phase 04.1.1-v2 Option A: the null-replicate fitter is the cheap tick least-squares
    estimator, tagged `fit_method_used == "least-squares-null-replicate"`.

    The null is eta=0-by-construction (pure-NHPP sims), so LS bias on eta is irrelevant
    to the null LR distribution; tick-LS is ~178x cheaper than the scipy canonical fit
    (DIAGNOSTIC §Q4), making the 2x1000-replicate bootstrap tractable.
    """
    leg_0, leg_1 = synthetic_nhpp_baseline_only_legs
    fit = _fit_hawkes_ls_for_null(leg_0, leg_1, decays=0.001)
    assert fit["fit_method_used"] == "least-squares-null-replicate", (
        f"Option A null fitter must use tick-LS; got {fit['fit_method_used']!r}"
    )
    # Shape contract consumed by the bootstrap loop.
    assert np.asarray(fit["baseline"]).shape == (2,)
    assert np.asarray(fit["adjacency"]).shape == (2, 2)
    assert "branching_ratio" in fit
    assert "decays" in fit


def test_bootstrap_observed_stat_finite_scale(synthetic_nhpp_baseline_only_legs):
    """Phase 04.1.1-v2: the observed LR statistic is on a self-consistent canonical-LL
    scale — the prior 6.05M observed_stat (LS-params-into-canonical-LL pathology) is gone.

    Smoke run at n_reps=30 (Option A makes each null replicate cheap, so this completes
    in seconds, not minutes).
    """
    leg_0, leg_1 = synthetic_nhpp_baseline_only_legs
    result = parametric_bootstrap_lr(
        leg_0,
        leg_1,
        panel_data_hash="test-option-a-finite-scale",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        n_reps=30,
    )
    assert result["n_reps"] == 30
    assert abs(result["observed_stat"]) < 1e5, (
        f"observed_stat={result['observed_stat']} — the 6.05M LS-into-canonical-LL "
        f"pathology is NOT resolved"
    )
    assert np.isfinite(result["observed_stat"])


def test_deterministic_seed(synthetic_nhpp_baseline_only_legs):
    """Same panel_data_hash -> byte-identical bootstrap null distribution."""
    leg_0, leg_1 = synthetic_nhpp_baseline_only_legs
    h = "test-deterministic"
    a = parametric_bootstrap_lr(
        leg_0,
        leg_1,
        panel_data_hash=h,
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        n_reps=30,
    )
    b = parametric_bootstrap_lr(
        leg_0,
        leg_1,
        panel_data_hash=h,
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        n_reps=30,
    )
    assert a["seed"] == b["seed"], "Seed derivation is non-deterministic"
    a_null = np.asarray(a["bootstrap_null_dist_50_50_chi2_0_chi2_1"])
    b_null = np.asarray(b["bootstrap_null_dist_50_50_chi2_0_chi2_1"])
    assert np.array_equal(a_null, b_null), (
        "Same seed produced different null distributions"
    )
