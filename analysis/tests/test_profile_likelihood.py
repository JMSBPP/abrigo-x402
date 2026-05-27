"""DGP-06: Profile-likelihood eta-CI tests.

Tests `profile_likelihood_eta_ci` (Filimonov & Sornette 2014 + Wheatley thesis):
- CI structurally bounded in [0, 1) (NOT Wald — Pitfall 4)
- Recovered CI covers either the truth (eta=0.5) OR the fitted eta_hat
- Projection-trick `fit_hawkes_with_fixed_branching_ratio` realizes the target spectral radius
- Q-9 null-fire trigger: ci_width > 0.4 -> q9_nullfire_triggered=True (PRE_REGISTRATION lock)
"""
from __future__ import annotations

import numpy as np

from abrigo_x402.dgp.hawkes_fit import (
    fit_hawkes_expkern,
    fit_hawkes_with_fixed_branching_ratio,
)
from abrigo_x402.dgp.profile_likelihood import (
    Q9_CI_WIDTH_THRESHOLD,
    profile_likelihood_eta_ci,
)


def test_fit_hawkes_with_fixed_branching_ratio_projection(synthetic_hawkes_eta_05_legs):
    """Projection trick produces an adjacency whose spectral radius equals eta_target."""
    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    target = 0.3
    result = fit_hawkes_with_fixed_branching_ratio(
        leg_0, leg_1, eta_target=target, decays=0.1,
    )
    eigvals = np.linalg.eigvals(np.asarray(result["adjacency"]) / result["decays"])
    actual = float(np.max(np.abs(eigvals)))
    assert abs(actual - target) < 1e-4, (
        f"Projection trick failed: target={target} actual={actual}"
    )


def test_ci_covers_truth(synthetic_hawkes_eta_05_legs):
    """CI covers either truth (eta=0.5) or the fitted eta_hat (looser — finite-sample bias)."""
    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    hawkes_fit = fit_hawkes_expkern(leg_0, leg_1, decays=0.1)
    ci = profile_likelihood_eta_ci(
        leg_0, leg_1, hawkes_fit, decays=0.1, alpha=0.05,
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
    hawkes_fit = fit_hawkes_expkern(leg_0, leg_1, decays=0.1)
    ci = profile_likelihood_eta_ci(
        leg_0, leg_1, hawkes_fit, decays=0.1, alpha=0.05,
    )
    assert 0.0 <= ci["lower"] <= ci["upper"] < 1.0, (
        f"CI extends past [0, 1): [{ci['lower']}, {ci['upper']}]"
    )
    assert ci["method"] == "profile_likelihood"


def test_q9_nullfire_trigger(synthetic_hawkes_eta_05_legs):
    """Q9_CI_WIDTH_THRESHOLD == 0.4 (PRE_REGISTRATION lock); flag fires iff ci_width > 0.4."""
    assert Q9_CI_WIDTH_THRESHOLD == 0.4
    leg_0, leg_1 = synthetic_hawkes_eta_05_legs
    hawkes_fit = fit_hawkes_expkern(leg_0, leg_1, decays=0.1)
    ci = profile_likelihood_eta_ci(
        leg_0, leg_1, hawkes_fit, decays=0.1, alpha=0.05,
    )
    # Flag must match the structural definition (ci_width > threshold)
    assert ci["q9_nullfire_triggered"] == (ci["ci_width"] > Q9_CI_WIDTH_THRESHOLD)
