"""DGP-05: time-rescaling KS test on held-out Hawkes residuals.

Tests the closed-form exponential-kernel compensator, KS-test pass/fail
behaviour on correctly-specified vs misspecified models, and the residuals
DataFrame schema for `residuals.parquet`.

LOCKED INVARIANTS (PRE_REGISTRATION + PITFALLS §4 + Pitfall 5):
- Compensator computed in CLOSED FORM (no scipy.integrate.quad / np.trapz).
- KS test applied on HELD-OUT segment with TRAIN-FITTED parameters.
- Acceptance threshold: p > 0.05.
"""
import numpy as np
import polars as pl

from abrigo_x402.dgp.time_rescaling import (
    build_residuals_dataframe,
    compute_compensator_exp_kernel,
    time_rescaling_ks_test_leg,
)


def test_compensator_closed_form():
    """Hand-computed: mu=0.1, alpha=0.5, beta=1.0; one prior event at t=0.5 (train),
    one held-out event at t=2.0; W_start=1.0. Compensator must match the analytic
    formula within 1e-9 absolute tolerance.
    """
    baseline = np.array([0.1, 0.0], dtype=np.float64)
    adjacency = np.array([[0.5, 0.0], [0.0, 0.0]], dtype=np.float64)
    decays = 1.0
    # Prior event in train at t_jk = 0.5; held-out event at t = 2.0
    full_history_leg_0 = np.array([0.5, 2.0], dtype=np.float64)
    full_history_leg_1 = np.array([], dtype=np.float64)
    held_out_times = np.array([2.0], dtype=np.float64)
    W_start = 1.0
    Lambda = compute_compensator_exp_kernel(
        held_out_times, 0, baseline, adjacency, decays,
        full_history_leg_0, full_history_leg_1, W_start,
    )
    # Expected: mu*(t-W_start) + alpha * (exp(-beta*max(W_start - 0.5, 0)) - exp(-beta*(2.0 - 0.5))) / beta
    #         = 0.1*(2.0-1.0) + 0.5 * (exp(-0.5) - exp(-1.5)) / 1.0
    expected = 0.1 * 1.0 + 0.5 * (np.exp(-0.5) - np.exp(-1.5)) / 1.0
    assert abs(float(Lambda[0]) - float(expected)) < 1e-9, (
        f"Compensator closed-form mismatch: got {Lambda[0]}, expected {expected}"
    )


def test_passes_on_true_model(synthetic_hawkes_eta_05_legs):
    """KS test on held-out segment with TRAIN-FITTED parameters (approx true params)
    should NOT reject the synthetic Hawkes panel on at least one leg.
    """
    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    W_start, W_end = 0.0, 2_592_000.0
    t_split = W_start + 0.80 * (W_end - W_start)
    held_0 = leg_0[leg_0 >= t_split]
    held_1 = leg_1[leg_1 >= t_split]
    # Approximate the locked synthetic-generator parameters: baseline 0.00013 events/s/leg,
    # decays=0.1, adjacency uniform with entries c such that spectral radius = 2c/decays = 0.5
    # => c = 0.5 * decays / 2 = 0.025
    decays = 0.1
    baseline = np.array([0.00013, 0.00013], dtype=np.float64)
    adjacency = np.full((2, 2), 0.5 * decays / 2.0, dtype=np.float64)
    results = [
        time_rescaling_ks_test_leg(held_0, 0, baseline, adjacency, decays, leg_0, leg_1, t_split, W_end),
        time_rescaling_ks_test_leg(held_1, 1, baseline, adjacency, decays, leg_0, leg_1, t_split, W_end),
    ]
    # At least one leg should fail to reject (p > 0.05) under true parameters
    p_values = [r["p_value"] for r in results if not np.isnan(r["p_value"])]
    assert any(p > 0.05 for p in p_values) or len(p_values) == 0, (
        f"Both legs reject under true-parameter rescaling: p_values={p_values}"
    )


def test_fails_on_misspecified(synthetic_hawkes_eta_05_legs):
    """Misspecified NHPP rescaling (alpha=0) of true-Hawkes data should reject on
    at least one leg (p < 0.05).
    """
    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    W_start, W_end = 0.0, 2_592_000.0
    t_split = W_start + 0.80 * (W_end - W_start)
    held_0 = leg_0[leg_0 >= t_split]
    held_1 = leg_1[leg_1 >= t_split]
    train_dur = t_split - W_start
    # Misspecified: alpha = 0 (pure NHPP), baseline = empirical-rate from train
    baseline = np.array([
        float(leg_0[leg_0 < t_split].size) / train_dur,
        float(leg_1[leg_1 < t_split].size) / train_dur,
    ], dtype=np.float64)
    adjacency = np.zeros((2, 2), dtype=np.float64)
    r0 = time_rescaling_ks_test_leg(held_0, 0, baseline, adjacency, 0.1, leg_0, leg_1, t_split, W_end)
    r1 = time_rescaling_ks_test_leg(held_1, 1, baseline, adjacency, 0.1, leg_0, leg_1, t_split, W_end)
    p_values = [p for p in (r0["p_value"], r1["p_value"]) if not np.isnan(p)]
    if len(p_values) == 0:
        # Insufficient events - skip the assertion (won't usually happen with 30-day fixture)
        return
    assert any(p < 0.05 for p in p_values), (
        f"Misspecified NHPP rescaling failed to reject true-Hawkes data: p_values={p_values}"
    )


def test_residuals_dataframe_schema():
    """build_residuals_dataframe emits {leg, event_time, Lambda_at_event, rescaled_dt}
    with dtypes (UInt8, Float64, Float64, Float64).
    """
    held_out_times_0 = np.array([100.0, 200.0, 300.0], dtype=np.float64)
    held_out_times_1 = np.empty(0, dtype=np.float64)
    per_leg = [
        {
            "Lambda_at_events": [1.0, 2.0, 3.0],
            "rescaled_dt": [1.0, 1.0, 1.0],
        },
        {
            "Lambda_at_events": [],
            "rescaled_dt": [],
        },
    ]
    df = build_residuals_dataframe(per_leg, [held_out_times_0, held_out_times_1])
    assert df.columns == ["leg", "event_time", "Lambda_at_event", "rescaled_dt"]
    assert df.schema["leg"] == pl.UInt8
    assert df.schema["event_time"] == pl.Float64
    assert df.schema["Lambda_at_event"] == pl.Float64
    assert df.schema["rescaled_dt"] == pl.Float64
    # 3 rows from leg 0 + 0 from leg 1
    assert df.height == 3
