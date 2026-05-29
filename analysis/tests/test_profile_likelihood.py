"""DGP-06: Profile-likelihood eta-CI tests.

Tests `profile_likelihood_eta_ci` (Filimonov & Sornette 2014 + Wheatley thesis):
- CI structurally bounded in [0, 1) (NOT Wald — Pitfall 4)
- Recovered CI covers either the truth (eta=0.5) OR the fitted eta_hat
- Q-9 null-fire trigger: ci_width > 0.4 -> q9_nullfire_triggered=True (PRE_REGISTRATION lock)
- Phase 04.1.1-v2: GENUINE constrained MLE (re-optimize LL s.t. rho(alpha/beta)=eta at
  each grid point), method == "constrained_mle_profile"; the projection-trick reference
  (LL_max = max over the projected family; eta_hat = grid argmax) is RETRACTED.
"""
from __future__ import annotations

# Pattern I thread-pinning — MUST precede any numpy/scipy/tick import (SC-5 byte-identity).
import os  # noqa: E402

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import numpy as np  # noqa: E402

from abrigo_x402.dgp.hawkes_fit import fit_hawkes_expkern  # noqa: E402
from abrigo_x402.dgp.profile_likelihood import (  # noqa: E402
    ETA_GRID_DEFAULT,
    Q9_CI_WIDTH_THRESHOLD,
    profile_likelihood_eta_ci,
)


def test_ci_covers_truth(synthetic_hawkes_eta_05_legs):
    """CI covers either truth (eta=0.5) or the fitted eta_hat (looser — finite-sample bias).

    Phase 04.1.1-v2: fit at the AIC-min beta (free-beta scipy canonical) — the genuine
    joint-MLE eta is the reference, NOT the kernel-blind beta=0.1 projection.
    """
    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    hawkes_fit = fit_hawkes_expkern(leg_0, leg_1)
    decays = float(hawkes_fit["decays"])
    ci = profile_likelihood_eta_ci(
        leg_0, leg_1, hawkes_fit, decays=decays, alpha=0.05,
    )
    truth = 0.5
    eta_hat = ci["eta_hat"]
    covers_truth = ci["lower"] <= truth <= ci["upper"]
    covers_hat = ci["lower"] <= eta_hat <= ci["upper"]
    assert covers_truth or covers_hat, (
        f"CI [{ci['lower']}, {ci['upper']}] covers neither truth=0.5 nor eta_hat={eta_hat}"
    )


def test_ci_bounded(synthetic_hawkes_eta_05_legs):
    """CI structurally bounded in [0, 1) — never extends past the stationarity boundary."""
    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    hawkes_fit = fit_hawkes_expkern(leg_0, leg_1)
    decays = float(hawkes_fit["decays"])
    ci = profile_likelihood_eta_ci(
        leg_0, leg_1, hawkes_fit, decays=decays, alpha=0.05,
    )
    assert 0.0 <= ci["lower"] <= ci["upper"] < 1.0, (
        f"CI extends past [0, 1): [{ci['lower']}, {ci['upper']}]"
    )
    assert ci["method"] == "constrained_mle_profile"


def test_constrained_mle_ci_not_projection(synthetic_hawkes_eta_05_legs):
    """Phase 04.1.1-v2: the eta-CI is a GENUINE constrained MLE, NOT the projection trick.

    - method literal is "constrained_mle_profile" (the retracted "projection" / the prior
      "profile_likelihood" projection-family literal does NOT appear)
    - eta_hat is the unconstrained joint-MLE branching ratio (from the scipy canonical fit),
      in a sane range for the regenerated true-eta=0.5 fixture at n~700 (downward-biased)
    - the CI excludes zero (lower > 0): the branching_ci_excludes_zero gate criterion
    """
    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    hawkes_fit = fit_hawkes_expkern(leg_0, leg_1)
    decays = float(hawkes_fit["decays"])
    ci = profile_likelihood_eta_ci(
        leg_0, leg_1, hawkes_fit, decays=decays, alpha=0.05,
    )
    assert ci["method"] == "constrained_mle_profile"
    assert ci["method"] != "projection"
    # eta_hat is the joint-MLE eta, not the grid argmax of a projected family.
    assert abs(ci["eta_hat"] - float(hawkes_fit["branching_ratio"])) < 1e-9, (
        f"eta_hat={ci['eta_hat']} must equal the joint-MLE eta "
        f"{hawkes_fit['branching_ratio']}"
    )
    assert 0.30 <= ci["eta_hat"] <= 0.70, (
        f"eta_hat={ci['eta_hat']} outside the sane [0.30, 0.70] range for true eta=0.5 "
        f"at n~700"
    )
    assert ci["lower"] > 0.0, (
        f"CI lower endpoint {ci['lower']} must exclude zero (branching_ci_excludes_zero)"
    )


def test_ci_lower_not_grid_floor(synthetic_hawkes_eta_05_legs):
    """Plan 04.1.1-02c (NEEDS WORK #2b): the eta-CI lower endpoint is a real LL crossing,
    NOT the ETA_GRID floor artifact.

    The default eta-grid floor must be lowered below 0.02 so `branching_ci_excludes_zero`
    (lower > 0) reflects a genuine D(eta)=0 crossing found by the brentq refinement, not the
    coarse grid floor. Two checks:
      1. CONSTANT: ETA_GRID_DEFAULT floor < 0.02. FAILS now (floor is 0.02).
      2. STABILITY: the CI lower endpoint is stable to further grid refinement (a real
         crossing does not move when the low-eta grid is densified) and strictly inside
         (0, 1).
    """
    # 1. CONSTANT — the grid floor must be lowered below 0.02.
    floor = float(min(ETA_GRID_DEFAULT))
    assert floor < 0.02, (
        f"ETA_GRID_DEFAULT floor={floor} is not below 0.02 — the CI lower endpoint can be "
        f"a grid-floor artifact rather than a real D(eta)=0 crossing (Plan 04.1.1-02c)"
    )

    # 2. STABILITY — the lower endpoint is a real crossing, stable to grid refinement.
    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    hawkes_fit = fit_hawkes_expkern(leg_0, leg_1)
    decays = float(hawkes_fit["decays"])
    ci_default = profile_likelihood_eta_ci(
        leg_0, leg_1, hawkes_fit, decays=decays, alpha=0.05,
    )
    dense_low_grid = tuple(np.linspace(1e-3, 0.95, 60).tolist())
    ci_dense = profile_likelihood_eta_ci(
        leg_0, leg_1, hawkes_fit, decays=decays, alpha=0.05, eta_grid=dense_low_grid,
    )
    assert 0.0 < ci_default["lower"] < 1.0, (
        f"CI lower={ci_default['lower']} not strictly inside (0, 1)"
    )
    assert abs(ci_default["lower"] - ci_dense["lower"]) < 0.05, (
        f"CI lower endpoint moved under grid refinement: default={ci_default['lower']} vs "
        f"dense-low-grid={ci_dense['lower']} — the lower bound is a grid artifact, not a "
        f"real crossing (Plan 04.1.1-02c)"
    )


def test_q9_nullfire_trigger(synthetic_hawkes_eta_05_legs):
    """Q9_CI_WIDTH_THRESHOLD == 0.4 (PRE_REGISTRATION lock); flag fires iff ci_width > 0.4."""
    assert Q9_CI_WIDTH_THRESHOLD == 0.4
    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    hawkes_fit = fit_hawkes_expkern(leg_0, leg_1)
    decays = float(hawkes_fit["decays"])
    ci = profile_likelihood_eta_ci(
        leg_0, leg_1, hawkes_fit, decays=decays, alpha=0.05,
    )
    # Flag must match the structural definition (ci_width > threshold)
    assert ci["q9_nullfire_triggered"] == (ci["ci_width"] > Q9_CI_WIDTH_THRESHOLD)
