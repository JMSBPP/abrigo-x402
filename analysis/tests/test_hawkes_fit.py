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
    """DECAY_GRID is the locked Wheatley-thesis decay search grid."""
    assert DECAY_GRID == (0.01, 0.1, 1.0, 10.0)


# ---- Phase 04.1.1 LL-fit RED-state tests (AF-03 pre-registered acceptance) ----
#
# AF-12 OUT-OF-SCOPE list (verbatim - silent-rescope defense):
# - NO new Hawkes kernel forms (still exponential decay)
# - NO new firing conditions (still the existing 4)
# - NO new gate criteria (still the 4)
# - NO new requirements (cross-references DGP-01..03, DEPEND-01/02, HEDGE-01..05 only)
# - NO change to AF-03 pre-registered thresholds (eta floor 0.2, LR alpha 0.01,
#   KS alpha 0.05, Q-9 floor 300) - the eta-coherence band [0.283, 0.371] is a
#   NEW lock, not a revision.
# - NO re-fetch from Forno/Blockscout
# - NO PANEL-02 metadata header changes
# - NO Phase 5 PDF wave-1 scaffolding
# - NO synthetic-substrate deletion (0afc6af38e24 archived as LS-fallback evidence)
# - NO overwrite of ae9e3ba17900 (archived; new run_id is canonical)

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

from unittest.mock import patch  # noqa: E402
from pathlib import Path  # noqa: E402
import polars as pl  # noqa: E402

# AF-03 pre-registered acceptance band (Plan 04.1.1-00 PRE_REGISTRATION amendment).
# Source: data/fits/ichi/ae9e3ba17900/fit_report.json :: branching_ratio_ci.{lower, upper}
# at alpha=0.05. method=profile_likelihood. Rounded to 3 sig figs.
_AF_03_ETA_BAND_REAL = (0.283, 0.371)
_AF_03_ETA_BAND_SYNTH = (0.45, 0.55)


def test_hawkes_likelihood_mode_succeeds_on_synthetic(synthetic_hawkes_eta_05_legs):
    """LL-fit (or scipy fallback) MUST succeed on synthetic eta=0.5 substrate.

    AF-03: fit_method_used NEVER 'least-squares' after Phase 04.1.1.
    """
    from abrigo_x402.dgp.hawkes_fit import fit_hawkes_expkern

    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    result = fit_hawkes_expkern(leg_0, leg_1)
    assert result["fit_method_used"] != "least-squares", (
        f"AF-03 violation: fit_method_used={result['fit_method_used']!r} on synthetic; "
        f"Plan 04.1.1-00 PRE_REGISTRATION locks scipy_canonical_ll fallback "
        f"as Fallback A - LS is the BROKEN estimator being retired."
    )
    assert result["fit_method_used"] in ("likelihood", "scipy_canonical_ll"), (
        f"fit_method_used={result['fit_method_used']!r} is not in the pre-registered set "
        f"{{'likelihood', 'scipy_canonical_ll'}}"
    )


def test_likelihood_mode_eta_recovers_synthetic_ground_truth(synthetic_hawkes_eta_05_legs):
    """eta_LL in [0.45, 0.55] on synthetic_hawkes_eta_05.parquet (eta_true=0.5)."""
    from abrigo_x402.dgp.hawkes_fit import fit_hawkes_expkern

    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    result = fit_hawkes_expkern(leg_0, leg_1)
    eta = float(result["branching_ratio"])
    lo, hi = _AF_03_ETA_BAND_SYNTH
    assert lo <= eta <= hi, (
        f"Synthetic-regression band violation: eta={eta} not in [{lo}, {hi}]. "
        f"Plan 04.1.1-00 PRE_REGISTRATION Phase 04.1.1 locks this tolerance."
    )


@pytest.mark.parametrize(
    "fixture_kind,expected_band",
    [
        ("synthetic", _AF_03_ETA_BAND_SYNTH),
        ("real_panel", _AF_03_ETA_BAND_REAL),
    ],
)
def test_likelihood_mode_eta_within_profile_ci(
    fixture_kind, expected_band, synthetic_hawkes_eta_05_legs
):
    """AF-03 acceptance band [0.283, 0.371] on real panel; [0.45, 0.55] on synthetic.

    Source-of-truth: notes/PRE_REGISTRATION.md Phase 04.1.1 - LL-fit acceptance
    & fallback chain (Plan 04.1.1-00 amendment). Bands rounded to 3 sig figs from
    data/fits/ichi/ae9e3ba17900/fit_report.json :: branching_ratio_ci.{lower, upper}.
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
    eta = float(result["branching_ratio"])
    lo, hi = expected_band
    assert lo <= eta <= hi, (
        f"AF-03 acceptance band violation on {fixture_kind}: "
        f"eta={eta} not in [{lo}, {hi}]. Plan 04.1.1-00 PRE_REGISTRATION lock."
    )


def test_scipy_fallback_path_isolated(synthetic_hawkes_eta_05_legs):
    """When tick.likelihood raises, scipy_canonical_ll fallback fires and succeeds.

    Mocks _fit_with_gofit at the primary call site (gofit='likelihood' branch) to
    raise a synthetic RuntimeError; asserts the scipy fallback path returns a
    well-formed dict with the correct fit_method_used + why_not_likelihood fields.
    Does NOT assert ground-truth eta recovery (that is the responsibility of
    test_likelihood_mode_eta_recovers_synthetic_ground_truth on the real path).
    """
    from abrigo_x402.dgp import hawkes_fit as hf

    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    real_fit_with_gofit = hf._fit_with_gofit

    def _raise_on_primary(l0, l1, decays, gofit):
        if gofit == "likelihood":
            raise RuntimeError("synthetic tick failure")
        return real_fit_with_gofit(l0, l1, decays, gofit=gofit)

    with patch.object(hf, "_fit_with_gofit", side_effect=_raise_on_primary):
        result = hf._fit_at_decay(leg_0, leg_1, decays=0.1)

    assert result["fit_method_used"] == "scipy_canonical_ll", (
        f"Fallback A wiring failure: fit_method_used={result['fit_method_used']!r}; "
        f"expected 'scipy_canonical_ll'."
    )
    assert "why_not_likelihood" in result, (
        "scipy fallback must record why_not_likelihood when it fires"
    )
    assert "synthetic tick failure" in result["why_not_likelihood"], (
        f"why_not_likelihood={result['why_not_likelihood']!r} does not record the "
        f"tick exception text"
    )
    eta = float(result["branching_ratio"])
    assert 0.0 <= eta <= 0.999, (
        f"scipy fallback returned out-of-bounds branching_ratio={eta} "
        f"(expected [0.0, 0.999] - stationarity band)"
    )
