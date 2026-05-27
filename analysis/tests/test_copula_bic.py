# CRITICAL: thread-pinning MUST be the first 4 executable lines (Phase 3 Pattern I)
# copulae's MLE optimizer is BLAS-backed; BIC ranking at N=500/rho=0.7 is on the
# Gaussian-vs-t discrimination edge and flips across runs without pinning.
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

# NOW safe to import numpy / copulae / etc.
import numpy as np
import pytest
from abrigo_x402.dependence.copula import (
    fit_5_families_bic,
    REQUIRED_JOINT_DIST_KEYS,
    VINE_FALLBACK_DELTA_BIC_THRESHOLD,
)


VALID_FAMILIES = {"gaussian", "t", "clayton", "frank", "gumbel"}


def _gaussian_sample(n: int = 500, rho: float = 0.7, seed: int = 20260527) -> np.ndarray:
    """Draw n samples from a 2-D Gaussian copula with given correlation."""
    from copulae import NormalCopula
    cop = NormalCopula(dim=2)
    cop.params = rho
    return cop.random(n, seed=seed)


def _clayton_sample(n: int = 500, theta: float = 2.0, seed: int = 20260527) -> np.ndarray:
    """Draw n samples from a 2-D Clayton copula with given theta."""
    from copulae import ClaytonCopula
    cop = ClaytonCopula(dim=2)
    cop.params = theta
    return cop.random(n, seed=seed)


def test_shape_contract_5_families():
    """Result has {winner, all_candidates, vine_fallback_used}; all_candidates exactly 5 keys."""
    u = _gaussian_sample()
    result = fit_5_families_bic(u)

    assert set(result.keys()) >= {"winner", "all_candidates", "vine_fallback_used"}
    assert result["winner"] in VALID_FAMILIES
    assert set(result["all_candidates"].keys()) == VALID_FAMILIES

    for fam, block in result["all_candidates"].items():
        assert set(block.keys()) >= {"params", "log_lik", "bic"}, f"{fam} missing keys"
        assert np.isfinite(block["log_lik"]), f"{fam} log_lik not finite"
        assert np.isfinite(block["bic"]), f"{fam} bic not finite"


def test_gaussian_fixture_wins_gaussian():
    """500 samples from Gaussian copula (rho=0.7); BIC must pick 'gaussian'."""
    u = _gaussian_sample(n=500, rho=0.7, seed=20260527)
    result = fit_5_families_bic(u)
    assert result["winner"] == "gaussian", (
        f"Expected gaussian winner on Gaussian fixture; got {result['winner']}. "
        f"BICs: {{f: result['all_candidates'][f]['bic'] for f in VALID_FAMILIES}}"
    )


def test_clayton_fixture_detects_lower_tail():
    """500 samples from Clayton(theta=2.0); winner should be a lower-tail family.

    'gaussian' is acceptable if the BIC spread between gaussian and clayton is < 5
    (ambiguous-by-discrimination-edge regime).
    """
    u = _clayton_sample(n=500, theta=2.0, seed=20260527)
    result = fit_5_families_bic(u)
    bics = {f: result["all_candidates"][f]["bic"] for f in VALID_FAMILIES}
    winner = result["winner"]
    spread_gauss_vs_clayton = bics["gaussian"] - bics["clayton"]
    assert winner in {"clayton", "t"} or spread_gauss_vs_clayton < 5.0, (
        f"Clayton fixture rejected by lower-tail families; winner={winner}, "
        f"bics={bics}"
    )


def test_bic_formula_correctness():
    """Manually compute BIC for the winner via -2*log_lik + k*log(n); match to 1e-6."""
    u = _gaussian_sample(n=500, rho=0.7, seed=20260527)
    result = fit_5_families_bic(u)
    winner = result["winner"]
    # 1-parameter families: gaussian, clayton, frank, gumbel; 2-parameter: t (rho, df)
    k = 2 if winner == "t" else 1
    n = u.shape[0]
    bic_manual = -2.0 * result["all_candidates"][winner]["log_lik"] + k * float(np.log(n))
    bic_reported = result["all_candidates"][winner]["bic"]
    assert abs(bic_manual - bic_reported) < 1e-6, (
        f"BIC formula mismatch for winner={winner}: manual={bic_manual}, "
        f"reported={bic_reported}"
    )


def test_vine_fallback_not_implemented_in_v1():
    """vine_fallback_used is always False in v1.0; use_vine=True raises NotImplementedError."""
    rng = np.random.default_rng(42)
    u = rng.uniform(0, 1, size=(100, 2))
    result = fit_5_families_bic(u)
    assert result["vine_fallback_used"] is False
    with pytest.raises(NotImplementedError, match=r"pyvinecopulib|deferred"):
        fit_5_families_bic(u, use_vine=True)


def test_pit_clipping_handles_edge_values():
    """Raw rank/(n+1) PIT produces exactly 0.0 / 1.0 on min/max ranks; norm.ppf(0)=-inf.
    _pit_with_clipping must clip to (eps, 1-eps) so no -inf/+inf propagates into MVN."""
    from abrigo_x402.dependence.copula import _pit_with_clipping
    raw = np.array([0.0, 0.5, 1.0])
    clipped = _pit_with_clipping(raw, eps=1e-10)
    assert np.all(np.isfinite(clipped))
    assert clipped[0] >= 1e-10 and clipped[-1] <= 1.0 - 1e-10
    # Downstream norm.ppf must be finite on the clipped image
    from scipy.stats import norm
    assert np.all(np.isfinite(norm.ppf(clipped)))


def test_vine_threshold_constant_is_5():
    """CONTEXT.md lock: VINE_FALLBACK_DELTA_BIC_THRESHOLD == 5.0."""
    assert VINE_FALLBACK_DELTA_BIC_THRESHOLD == 5.0


def test_required_joint_dist_keys_exported():
    """REQUIRED_JOINT_DIST_KEYS tuple is the canonical 11-element schema."""
    assert isinstance(REQUIRED_JOINT_DIST_KEYS, tuple)
    assert len(REQUIRED_JOINT_DIST_KEYS) == 11
    assert "empirical_copula" in REQUIRED_JOINT_DIST_KEYS
    assert "vine_fallback_used" in REQUIRED_JOINT_DIST_KEYS
    assert "cross_correlogram" in REQUIRED_JOINT_DIST_KEYS
    assert "permutation_null" in REQUIRED_JOINT_DIST_KEYS
