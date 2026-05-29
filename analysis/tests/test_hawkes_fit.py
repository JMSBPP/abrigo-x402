"""DGP-02: tick.HawkesExpKern fit tests."""
import numpy as np
import pytest

from abrigo_x402.dgp.hawkes_fit import (
    DECAY_GRID,
    compute_branching_ratio,
    fit_hawkes_expkern,
)


def test_full_offdiag(synthetic_hawkes_eta_05_legs):
    """Fit produces 2x2 adjacency with off-diagonal NOT forced to 0 (Pitfall §5 — diagonal-only Hawkes anti-pattern)."""
    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    fit = fit_hawkes_expkern(leg_0, leg_1, decays=0.1)
    adjacency = np.asarray(fit["adjacency"])
    assert adjacency.shape == (2, 2)
    # Full off-diagonal: at least one off-diagonal element strictly positive (not forced to 0)
    assert adjacency[0, 1] > 0.0 or adjacency[1, 0] > 0.0, (
        f"Off-diagonal forced to 0 — diagonal-only Hawkes anti-pattern detected: {adjacency}"
    )


def test_branching_ratio_spectral():
    """Branching ratio = spectral radius of alpha/beta, not max element (Pitfall 6)."""
    # Adjacency where max element (0.4) differs from spectral radius (0.3)
    adjacency = np.array([[0.3, 0.0], [0.4, 0.0]], dtype=np.float64)
    decays = 1.0
    eta = compute_branching_ratio(adjacency, decays)
    # Eigenvalues of [[0.3, 0], [0.4, 0]] are 0.3 and 0.0 -> spectral radius = 0.3
    assert eta == pytest.approx(0.3, rel=1e-6), (
        f"Got {eta} — likely returned max element 0.4 (Pitfall 6)"
    )


def test_simultaneous_events():
    """Same-block timestamps handled without logIndex tie-breaking (Pitfall 7).

    Construct two legs with several identical timestamps (same-block ties); tick must
    accept them natively without raising and produce a well-formed adjacency."""
    rng = np.random.default_rng(42)
    base_times = np.sort(rng.uniform(100.0, 2_000_000.0, 350))
    leg_0 = base_times.copy()
    leg_1 = base_times.copy()
    # Add unique timestamps to each leg so the streams aren't perfectly identical
    leg_0 = np.sort(np.concatenate([leg_0, rng.uniform(100.0, 2_000_000.0, 30)]))
    leg_1 = np.sort(np.concatenate([leg_1, rng.uniform(100.0, 2_000_000.0, 30)]))
    # Should fit without raising — tick handles ties natively
    fit = fit_hawkes_expkern(leg_0, leg_1, decays=0.1)
    adjacency = np.asarray(fit["adjacency"])
    assert np.isfinite(adjacency).all(), "NaN/inf in adjacency — tick failed to handle ties"
    assert fit["branching_ratio"] >= 0.0


def test_decay_grid_constant():
    """DECAY_GRID is the locked decay search grid.

    Extended in Plan 04.1.1-01 to (0.0001, 0.001, 0.01, 0.1, 1.0, 10.0) per
    Pitfall 3 (real-panel mean inter-arrival ~666s; original min grid value
    beta=0.01/s decays in 100s, 6x too fast). Locked by Plan 04.1.1-00
    PRE_REGISTRATION Phase 04.1.1.
    """
    assert DECAY_GRID == (0.0001, 0.001, 0.01, 0.1, 1.0, 10.0)


# ---- Phase 04.1.1 (v2) LL-fit tests (AF-03 pre-registered acceptance, corrected) ----
#
# AF-12 OUT-OF-SCOPE list (verbatim - silent-rescope defense; v2 EXPANSION noted):
# - v2 EXPANSION (IN scope, Plans 02-v2 — NOT this test file): lr_test.py Option A
#   null-replicate estimator + observed-LL-scale fix + profile_likelihood.py
#   genuine constrained-MLE CI are now IN scope, but land in Plan 04.1.1-02-v2.
# - STILL OUT: NO new Hawkes kernel forms (still exponential decay)
# - STILL OUT: NO new firing conditions (still the existing 4)
# - STILL OUT: NO new gate criteria (still the 4)
# - STILL OUT: NO new requirements (cross-references DGP-02, DGP-06 only)
# - STILL OUT: NO change to AF-03 pre-registered thresholds (eta floor 0.2, LR
#   alpha 0.01, KS alpha 0.05, Q-9 floor 300)
# - STILL OUT: NO re-fetch from Forno/Blockscout
# - STILL OUT: NO PANEL-02 metadata header changes
# - STILL OUT: NO Phase 5 PDF wave-1 scaffolding
# - STILL OUT: NO synthetic-substrate deletion (0afc6af38e24 archived)
# - STILL OUT: NO overwrite of ae9e3ba17900 (archived; new run_id is canonical)

import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
# Pattern I thread-pinning prelude - Phase 3 SC-5 byte-identity discipline carried
# forward. MUST appear before any numpy / scipy / tick / polars import in this
# module if those imports are not already at module top. If existing imports at
# top of file already set these env vars, this block is idempotent (setdefault
# is a no-op when key is present).

from pathlib import Path  # noqa: E402
import polars as pl  # noqa: E402

# Phase 04.1.1-v2: the v1 bands are RETRACTED. The v1 real-panel projection band
# was a constrained-projection artifact (profile_likelihood.py projection trick at
# the LS-degenerate kernel-blind beta=0.1 point — NOT a joint-MLE CI); the v1
# synthetic band tested a MISLABELED fixture (true eta=0.05 via tick's normalized
# kernel, ρ(α) not ρ(α/β)). Source: notes/PRE_REGISTRATION.md
# §Phase 04.1.1 (v2) — Supersession of the LL-fit acceptance bands.
_V2_ETA_BAND_SYNTH = (0.40, 0.60)   # regenerated fixture (true η=0.5); ~13% downward-bias band at n≈700
_V2_ETA_FLOOR_REAL = 0.2            # real panel: η is a LOWER BOUND ≥ η-floor; NO fixed band (post-hoc fishing)


def test_hawkes_likelihood_mode_succeeds_on_synthetic(synthetic_hawkes_eta_05_legs):
    """Canonical scipy_canonical_ll fit MUST succeed on the synthetic eta=0.5 substrate.

    AF-03 (v2): fit_method_used is EXACTLY 'scipy_canonical_ll' — tick.likelihood is
    DEAD (removed from the live path; DIAGNOSTIC §1) and LS is the BROKEN estimator
    being retired. PRE_REGISTRATION §Phase 04.1.1 (v2).
    """
    from abrigo_x402.dgp.hawkes_fit import fit_hawkes_expkern

    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    result = fit_hawkes_expkern(leg_0, leg_1)
    assert result["fit_method_used"] != "least-squares", (
        f"AF-03 violation: fit_method_used={result['fit_method_used']!r} on synthetic; "
        f"PRE_REGISTRATION §Phase 04.1.1 (v2) — LS is the BROKEN estimator being retired."
    )
    assert result["fit_method_used"] == "scipy_canonical_ll", (
        f"fit_method_used={result['fit_method_used']!r} is not the pre-registered v2 "
        f"canonical estimator 'scipy_canonical_ll' (tick.likelihood removed from live path)"
    )


def test_likelihood_mode_eta_recovers_synthetic_ground_truth(synthetic_hawkes_eta_05_legs):
    """eta_hat in [0.40, 0.60] on the REGENERATED synthetic_hawkes_eta_05.parquet (true eta=0.5).

    The regenerated fixture sets a GENUINE eta=0.5 via tick.adjust_spectral_radius(0.5)
    at a matched beta. The band accommodates the measured ~13% downward finite-sample
    bias at n≈700. PRE_REGISTRATION §Phase 04.1.1 (v2) synthetic-regression band.
    """
    from abrigo_x402.dgp.hawkes_fit import fit_hawkes_expkern

    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    result = fit_hawkes_expkern(leg_0, leg_1)
    eta = float(result["branching_ratio"])
    lo, hi = _V2_ETA_BAND_SYNTH
    assert lo <= eta <= hi, (
        f"Synthetic-regression band violation: eta={eta} not in [{lo}, {hi}]. "
        f"PRE_REGISTRATION §Phase 04.1.1 (v2) synthetic-regression band [0.40, 0.60]."
    )


@pytest.mark.parametrize("fixture_kind", ["synthetic", "real_panel"])
def test_likelihood_mode_eta_within_v2_acceptance(
    fixture_kind, synthetic_hawkes_eta_05_legs
):
    """v2 acceptance (PRE_REGISTRATION §Phase 04.1.1 (v2)):

    - synthetic → fit_method_used == 'scipy_canonical_ll' AND eta ∈ [0.40, 0.60]
    - real_panel → fit_method_used == 'scipy_canonical_ll' AND eta ≥ η-floor 0.2
      (LOWER BOUND only; NO fixed real-panel band — registering one after seeing
      the η(β) profile would itself be AF-03 fishing).

    The retracted v1 projection-CI real-panel band is GONE.
    """
    from abrigo_x402.dgp.hawkes_fit import fit_hawkes_expkern

    if fixture_kind == "synthetic":
        leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    else:
        # The repo layout places tests under analysis/tests/; the real panel
        # parquet lives at <repo-root>/data/raw/... Resolve relative to this
        # test file rather than CWD so the test works from either invocation
        # site (cd analysis && pytest, or pytest from repo root).
        repo_root = Path(__file__).resolve().parents[2]
        panel_path = (
            repo_root
            / "data/raw/ichi/0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F/"
            / "67378253_67896653.parquet"
        )
        if not panel_path.exists():
            pytest.skip(
                f"real panel parquet not on disk (gitignored): {panel_path}"
            )
        from abrigo_x402.dgp.orchestrator import _extract_legs_from_panel

        panel = pl.read_parquet(panel_path)
        leg_0, leg_1, _ws, _we = _extract_legs_from_panel(panel)
    result = fit_hawkes_expkern(leg_0, leg_1)
    assert result["fit_method_used"] == "scipy_canonical_ll", (
        f"v2 violation on {fixture_kind}: fit_method_used="
        f"{result['fit_method_used']!r}; expected 'scipy_canonical_ll'."
    )
    eta = float(result["branching_ratio"])
    if fixture_kind == "synthetic":
        lo, hi = _V2_ETA_BAND_SYNTH
        assert lo <= eta <= hi, (
            f"synthetic η={eta} not in {_V2_ETA_BAND_SYNTH} "
            f"(PRE_REGISTRATION §Phase 04.1.1 (v2) synthetic-regression band)"
        )
    else:
        assert eta >= _V2_ETA_FLOOR_REAL, (
            f"real-panel η={eta} below η-floor {_V2_ETA_FLOOR_REAL} (LOWER BOUND; "
            f"NO fixed real-panel band per PRE_REGISTRATION §Phase 04.1.1 (v2))"
        )


def test_scipy_fit_rejects_nonstationary(synthetic_hawkes_eta_05_legs):
    """Plan 04.1.1-02c (NEEDS WORK #2a): the scipy canonical fit must reject the
    non-stationary region rho(alpha/beta) >= 1, enforcing the pre-registered
    §Kernel Forms condition ||alpha/beta||_inf < 1.

    Two checks:
      1. UNIT: the stationarity guard `_reject_nonstationary` returns the +inf-class
         penalty (1e18) for an explosive alpha and 0.0 for a stationary one. FAILS now
         (the symbol does not exist — neg_ll has no stationarity rejection).
      2. INTEGRATION: a real-Hawkes panel fit returns a stationary branching_ratio < 1.0
         (the guard keeps the optimizer inside the stationary region).
    """
    from abrigo_x402.dgp import hawkes_fit as hf

    # 1. UNIT — the guard predicate must exist and reject the explosive region.
    beta = 0.5
    explosive_alpha = np.array([[0.9, 0.1], [0.1, 0.9]], dtype=np.float64)
    # rho(explosive_alpha / 0.5) = (~1.0)/0.5 = ~2.0 >= 1 -> non-stationary.
    assert hf.compute_branching_ratio(explosive_alpha, beta) >= 1.0
    assert hf._reject_nonstationary(explosive_alpha, beta) >= 1e18, (
        "stationarity guard must penalize the explosive region (rho(alpha/beta) >= 1)"
    )
    stationary_alpha = np.array([[0.1, 0.02], [0.02, 0.1]], dtype=np.float64)
    assert hf.compute_branching_ratio(stationary_alpha, beta) < 1.0
    assert hf._reject_nonstationary(stationary_alpha, beta) == 0.0, (
        "stationarity guard must NOT penalize the stationary region (rho < 1)"
    )

    # 2. INTEGRATION — the real-Hawkes fit lands stationary.
    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    result = fit_hawkes_expkern(leg_0, leg_1)
    eta = float(result["branching_ratio"])
    assert eta < 1.0, (
        f"fit returned non-stationary branching_ratio={eta} (>= 1.0); the scipy neg_ll "
        f"stationarity rejection is not enforcing ||alpha/beta||<1"
    )


def test_scipy_canonical_ll_is_primary_path(synthetic_hawkes_eta_05_legs):
    """_fit_at_decay uses scipy_canonical_ll as the PRIMARY (and only) live estimator.

    Phase 04.1.1-v2: tick.HawkesExpKern likelihood mode is DEAD — removed from the
    live path (DIAGNOSTIC §1). No mock is needed: a direct call to _fit_at_decay
    must return fit_method_used == 'scipy_canonical_ll' with a well-formed,
    in-bounds branching_ratio. No 'why_not_likelihood' field is set on the live
    path (there is no tick attempt to explain). LS is never returnable.
    """
    from abrigo_x402.dgp import hawkes_fit as hf

    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    result = hf._fit_at_decay(leg_0, leg_1, decays=0.1)

    assert result["fit_method_used"] == "scipy_canonical_ll", (
        f"scipy-primary wiring failure: fit_method_used={result['fit_method_used']!r}; "
        f"expected 'scipy_canonical_ll'."
    )
    assert result["fit_method_used"] != "least-squares", (
        "LS is the retired broken estimator — must never be returned on the live path"
    )
    eta = float(result["branching_ratio"])
    assert 0.0 <= eta <= 0.999, (
        f"scipy canonical fit returned out-of-bounds branching_ratio={eta} "
        f"(expected [0.0, 0.999] - stationarity band)"
    )
