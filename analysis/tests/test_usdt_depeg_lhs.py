"""HEDGE-03 USDT depeg calibration loader + N=64 Latin hypercube sensitivity tests.

Per CONTEXT.md commit e600d3a: evidence_source must be 'literature_range_stipulation';
Hernandez Cruz 2024 / Wu & Liu 2026 are NOT jump-diffusion parameter sources.
"""
import numpy as np

from abrigo_x402.hedge.usdt_depeg import (
    DEFAULT_LAMBDA_J,
    DEFAULT_MU_J,
    DEFAULT_SIGMA_J,
    LHS_BOUND_RATIO,
    LHS_N_SAMPLES,
    generate_lhs_samples,
    load_calibration,
)


def test_load_calibration_roundtrip():
    """Round-trip: doc on disk -> dict with evidence_source + base_triple."""
    cal = load_calibration("notes/usdt_depeg_calibration.md")
    assert cal["evidence_source"] == "literature_range_stipulation"
    assert cal["base_triple"]["lambda_J"] == DEFAULT_LAMBDA_J
    assert cal["base_triple"]["mu_J"] == DEFAULT_MU_J
    assert cal["base_triple"]["sigma_J"] == DEFAULT_SIGMA_J


def test_lhs_shape():
    """(64, 3) float64 — N=64 samples, 3 dimensions (lambda_J, mu_J, sigma_J)."""
    samples = generate_lhs_samples()
    assert samples.shape == (LHS_N_SAMPLES, 3)
    assert samples.dtype == np.float64


def test_lhs_bounds_within_50pct():
    """Every cell within ±50% per dimension (negative-base mu_J handled via min/max normalization)."""
    samples = generate_lhs_samples()
    # Column 0: lambda_J — positive base, [base*0.5, base*1.5]
    assert (samples[:, 0] >= DEFAULT_LAMBDA_J * (1 - LHS_BOUND_RATIO)).all()
    assert (samples[:, 0] <= DEFAULT_LAMBDA_J * (1 + LHS_BOUND_RATIO)).all()
    # Column 1: mu_J — negative base, bounds normalized via min/max
    lo1 = min(DEFAULT_MU_J * (1 - LHS_BOUND_RATIO), DEFAULT_MU_J * (1 + LHS_BOUND_RATIO))
    hi1 = max(DEFAULT_MU_J * (1 - LHS_BOUND_RATIO), DEFAULT_MU_J * (1 + LHS_BOUND_RATIO))
    assert (samples[:, 1] >= lo1).all()
    assert (samples[:, 1] <= hi1).all()
    # Column 2: sigma_J — positive base
    assert (samples[:, 2] >= DEFAULT_SIGMA_J * (1 - LHS_BOUND_RATIO)).all()
    assert (samples[:, 2] <= DEFAULT_SIGMA_J * (1 + LHS_BOUND_RATIO)).all()


def test_lhs_seed_determinism():
    """Same seed twice -> byte-identical samples (reproducibility contract)."""
    s1 = generate_lhs_samples(seed=12345)
    s2 = generate_lhs_samples(seed=12345)
    assert np.array_equal(s1, s2)


def test_lhs_different_seed_differs():
    """Different seeds produce different sample sets."""
    s1 = generate_lhs_samples(seed=12345)
    s2 = generate_lhs_samples(seed=67890)
    assert not np.array_equal(s1, s2)
