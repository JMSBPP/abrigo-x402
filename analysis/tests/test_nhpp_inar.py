"""DGP-01: Kirchner INAR(p) NHPP fit tests. Implemented by Wave 1 plan 03-01."""
import numpy as np
import pytest

from abrigo_x402.dgp.nhpp_inar import BIN_WIDTH_GRID_SECONDS, fit_nhpp_inar

WINDOW_START = 0.0
WINDOW_END = 2_592_000.0  # 30 days


def test_aic_bin_selection(synthetic_nhpp_baseline_only_legs):
    """AIC-min selects bin width from the locked grid {60, 300, 900, 3600}s.

    PRE_REGISTRATION lock: bin width grid is {1m, 5m, 15m, 1h}; AF-04 forbids any
    hand-tuned off-grid bin width. The selection must be AIC-min over exactly these
    four candidate widths.
    """
    leg_0, leg_1 = synthetic_nhpp_baseline_only_legs
    fit = fit_nhpp_inar(leg_0, leg_1, WINDOW_START, WINDOW_END)
    assert fit["bin_width_seconds"] in BIN_WIDTH_GRID_SECONDS, (
        f"AIC selected off-grid bin width {fit['bin_width_seconds']}"
    )
    assert "bin_width_aic_table" in fit
    assert set(fit["bin_width_aic_table"].keys()) == {"60.0", "300.0", "900.0", "3600.0"}


def test_nonneg_projection():
    """Negative VAR coefficients clamped to 0 (Kirchner non-negativity projection step).

    Anti-correlated independent Poisson legs produce small negative cross-coefficients
    in the VAR(p) fit; the Kirchner projection sends those to zero, preserving the
    NHPP positivity invariant.
    """
    rng = np.random.default_rng(42)
    n_events = 400
    leg_0 = np.sort(rng.uniform(0.0, WINDOW_END, n_events))
    leg_1 = np.sort(rng.uniform(0.0, WINDOW_END, n_events))
    fit = fit_nhpp_inar(leg_0, leg_1, WINDOW_START, WINDOW_END, bin_width_seconds=3600.0)
    coefs_array = np.asarray(fit["coefs"])
    intercept_array = np.asarray(fit["intercept"])
    assert (coefs_array >= 0.0).all(), "Coefficients contain negative entries after projection"
    assert (intercept_array >= 0.0).all(), "Intercept contains negative entries after projection"


def test_recovers_synthetic_ground_truth():
    """Synthetic-ground-truth: SimuHawkesExpKernels(alpha=0) -> bivariate Poisson; INAR(p) recovers baseline.

    NB: reduced from 1000 paths (RESEARCH spec) to 50 for test-suite runtime; tolerance loosened
    correspondingly from +/-10% to +/-15%. The 1000-path/+/-10% production validation runs in Plan 03-08
    as a once-per-phase manual sanity check.
    """
    from tick.hawkes import SimuHawkesExpKernels

    n_paths = 50
    true_baseline = np.array([0.00013, 0.00013], dtype=np.float64)
    true_adjacency = np.zeros((2, 2), dtype=np.float64)
    rng = np.random.default_rng(20260526)
    recovered = np.empty((n_paths, 2))
    for k in range(n_paths):
        sim = SimuHawkesExpKernels(
            adjacency=true_adjacency,
            decays=0.1,
            baseline=true_baseline,
            end_time=WINDOW_END,
            seed=int(rng.integers(0, 2**31)),
            verbose=False,
        )
        # NEVER force_simulation=True (Pitfall 9)
        sim.simulate()
        leg_0 = sim.timestamps[0].astype(np.float64)
        leg_1 = sim.timestamps[1].astype(np.float64)
        fit = fit_nhpp_inar(leg_0, leg_1, WINDOW_START, WINDOW_END, bin_width_seconds=3600.0)
        # Kirchner scaling: per-bin intercept / bin_width = events/sec baseline rate
        recovered[k, 0] = fit["intercept"][0] / fit["bin_width_seconds"]
        recovered[k, 1] = fit["intercept"][1] / fit["bin_width_seconds"]
    mean_recovered = recovered.mean(axis=0)
    rel_err = np.abs(mean_recovered - true_baseline) / true_baseline
    assert (rel_err < 0.15).all(), (
        f"Recovery mean {mean_recovered} differs from truth {true_baseline} by {rel_err} (> 15% tolerance)"
    )
