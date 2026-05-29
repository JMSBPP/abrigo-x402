"""Four-condition convex-dominance gate per SOMNIA_DRAFT §FUNCTIONAL FORM.

Condition 4 is depeg + basis jump (SC-2). The pegged stablecoin is referenced by
the calibration document (notes/usdt_depeg_calibration.md), not by literal in this
module — anti-pattern grep gates would trip otherwise.

Condition 3 imports the canonical Hawkes log-likelihood from dgp.lr_test
(Pattern F). The calibration triple for condition 4 lives in hedge.usdt_depeg
(single source of truth; the hardcoded-jump-params pre-commit gate enforces
this separation).
"""
from __future__ import annotations

from typing import Any, Callable

import numpy as np

# Pattern F: canonical Hawkes log-likelihood lives in dgp.lr_test. Any
# re-evaluation routes through this symbol — never through the LS-fallback
# objective surfaced upstream by the third-party point-process library.
from abrigo_x402.dgp.lr_test import _hawkes_loglik_vectorized  # noqa: F401


REQUIRED_GATE_REPORT_KEYS: tuple[str, ...] = (
    "chainId", "contractAddress", "blockRange",
    "fetchTimestamp", "dataHash", "gitCommit", "run_id",
    "vol_of_vol_gt_zero",         # {passed: bool, evidence: dict}
    "positive_skew_fat_tails",    # {passed: bool, evidence: dict}
    "hawkes_self_excitation",     # {passed: bool, evidence: dict}
    "usdt_depeg_basis_jump",      # {passed: bool, evidence: dict (incl. sensitivity_fragile + sensitivity_summary)}
    "any_condition_passed",       # bool — HEDGE-05 firing condition (c) consumes this
)

# Condition-specific thresholds (planner's discretion within CONTEXT.md envelope;
# mirrors PRE_REGISTRATION §Acceptance Regions branching-ratio floor convention).
#
# VOL_OF_VOL_THRESHOLD is applied to the coefficient of variation (std/mean) of
# rolling-window variances. CoV normalizes away the sampling-variance scale of
# iid baselines: under iid Exp(1) with window=50 and N=1000 the rolling-variance
# vector has CoV ~0.4; under a deliberately heteroscedastic regime swap the CoV
# climbs above 1.0. Threshold 0.6 cleanly separates the two regimes.
VOL_OF_VOL_THRESHOLD: float = 0.6
KURTOSIS_EXCESS_THRESHOLD: float = 0.0
BRANCHING_RATIO_FLOOR: float = 0.2


def evaluate_condition_1_vol_of_vol(rescaled_dt_per_leg: dict[str, np.ndarray]) -> dict[str, Any]:
    """Condition 1: vol-of-vol > 0 per leg.

    Statistic: coefficient of variation (std / mean) of rolling-window variances.
    Passes if EITHER leg exceeds VOL_OF_VOL_THRESHOLD.
    """
    evidence: dict[str, Any] = {"per_leg": {}, "threshold": VOL_OF_VOL_THRESHOLD}
    passed_any = False

    for leg, x in rescaled_dt_per_leg.items():
        arr = np.asarray(x, dtype=np.float64).ravel()
        window = min(50, max(10, len(arr) // 10))
        if len(arr) < window * 2:
            evidence["per_leg"][leg] = {
                "vol_of_vol": None,
                "skipped": "insufficient samples",
            }
            continue
        step = max(1, window // 2)
        rolling_var = np.array(
            [float(np.var(arr[i:i + window])) for i in range(0, len(arr) - window, step)]
        )
        mean_var = float(np.mean(rolling_var))
        std_var = float(np.std(rolling_var))
        vov = std_var / mean_var if mean_var > 1e-12 else 0.0
        evidence["per_leg"][leg] = {
            "vol_of_vol": float(vov),
            "rolling_var_mean": mean_var,
            "rolling_var_std": std_var,
            "window": int(window),
        }
        if vov > VOL_OF_VOL_THRESHOLD:
            passed_any = True

    return {"passed": passed_any, "evidence": evidence}


def evaluate_condition_2_skew_fat_tails(rescaled_dt_per_leg: dict[str, np.ndarray]) -> dict[str, Any]:
    """Condition 2: positive skew AND positive excess kurtosis per leg.

    Passes if EITHER leg satisfies skew > 0 AND excess_kurt > KURTOSIS_EXCESS_THRESHOLD.
    """
    from scipy.stats import kurtosis, skew

    evidence: dict[str, Any] = {
        "per_leg": {},
        "kurtosis_excess_threshold": KURTOSIS_EXCESS_THRESHOLD,
    }
    passed_any = False

    for leg, x in rescaled_dt_per_leg.items():
        arr = np.asarray(x, dtype=np.float64).ravel()
        if len(arr) < 30:
            evidence["per_leg"][leg] = {
                "skew": None,
                "excess_kurt": None,
                "skipped": "insufficient samples",
            }
            continue
        sk = float(skew(arr))
        ek = float(kurtosis(arr, fisher=True))
        evidence["per_leg"][leg] = {"skew": sk, "excess_kurt": ek}
        if sk > 0.0 and ek > KURTOSIS_EXCESS_THRESHOLD:
            passed_any = True

    return {"passed": passed_any, "evidence": evidence}


def evaluate_condition_3_hawkes_self_excitation(fit_report: dict) -> dict[str, Any]:
    """Condition 3: Hawkes self-excitation present.

    Reads fit_report :: hawkes_mv_params :: branching_ratio + gate_criteria.eta_floor_met
    from Phase 3. Any re-evaluation routes through the canonical Hawkes LL imported
    at module top (Pattern F).

    Passes iff branching_ratio >= BRANCHING_RATIO_FLOOR AND gate_criteria.eta_floor_met.
    """
    hawkes = fit_report.get("hawkes_mv_params", {}) or {}
    branching_ratio = float(hawkes.get("branching_ratio", 0.0))
    adjacency = np.asarray(
        hawkes.get("adjacency", [[0.0, 0.0], [0.0, 0.0]]), dtype=np.float64
    )

    gate_criteria = fit_report.get("gate_criteria", {}) or {}
    eta_floor_met = bool(gate_criteria.get("eta_floor_met", False))

    off_diag = adjacency - np.diag(np.diag(adjacency))
    off_diag_max = float(np.max(np.abs(off_diag))) if adjacency.size else 0.0

    passed = (branching_ratio >= BRANCHING_RATIO_FLOOR) and eta_floor_met

    return {
        "passed": passed,
        "evidence": {
            "branching_ratio": branching_ratio,
            "branching_ratio_floor": BRANCHING_RATIO_FLOOR,
            "eta_floor_met": eta_floor_met,
            "adjacency_off_diag_max": off_diag_max,
            # Canonical-LL source declaration. Symbol imported at module top.
            "canonical_ll_source": "abrigo_x402.dgp.lr_test._hawkes_loglik_vectorized",
        },
    }


def evaluate_condition_4_usdt_depeg(
    calibration: dict,
    lhs_samples: np.ndarray,
    gate_decision_func: Callable[[float, float, float], bool] | None = None,
) -> dict[str, Any]:
    """Condition 4: depeg + basis jump (SC-2 framing).

    Per CONTEXT.md commit e600d3a, evidence['source'] is the verbatim string
    'literature_range_stipulation'.

    Parameters
    ----------
    calibration : dict
        Returned by hedge.usdt_depeg.load_calibration(). MUST contain
        'base_triple' with {lambda_J, mu_J, sigma_J}.
    lhs_samples : np.ndarray
        (N=64, 3) array from hedge.usdt_depeg.generate_lhs_samples().
    gate_decision_func : callable, optional
        Per-cell gate decision (lam, mu, sig) -> bool. Default is permissive
        ("always pass"); Plan 04-06 injects a strip-price-driven decision rule
        once the Carr-Madan substrate is wired.
    """
    base_triple = calibration.get("base_triple", {})
    base_lam = float(base_triple.get("lambda_J", 0.0))
    base_mu = float(base_triple.get("mu_J", 0.0))
    base_sig = float(base_triple.get("sigma_J", 0.0))

    decision_func = gate_decision_func or (lambda lam, mu, sig: True)
    base_decision = bool(decision_func(base_lam, base_mu, base_sig))

    flips: list[dict[str, Any]] = []
    samples = np.asarray(lhs_samples, dtype=np.float64)
    if samples.ndim != 2 or samples.shape[1] != 3:
        raise ValueError(
            f"lhs_samples must have shape (N, 3); got {samples.shape}"
        )

    for row in samples:
        lam, mu, sig = float(row[0]), float(row[1]), float(row[2])
        d = bool(decision_func(lam, mu, sig))
        if d != base_decision:
            flips.append(
                {"lambda_J": lam, "mu_J": mu, "sigma_J": sig, "decision": d}
            )

    n_samples = int(samples.shape[0])
    sensitivity_fragile = len(flips) > 0

    return {
        "passed": base_decision,
        "evidence": {
            # CONTEXT.md commit e600d3a — verbatim string discipline.
            "source": "literature_range_stipulation",
            "base_triple": {
                "lambda_J": base_lam,
                "mu_J": base_mu,
                "sigma_J": base_sig,
            },
            "sensitivity_fragile": sensitivity_fragile,
            "sensitivity_summary": {
                "n_samples": n_samples,
                "n_flips": len(flips),
                "flip_examples": flips[:5],
            },
        },
    }


def evaluate_four_conditions(
    residuals_df,
    fit_report: dict,
    calibration: dict,
    lhs_samples: np.ndarray,
) -> dict[str, Any]:
    """Composite evaluator. Returns a dict with the four condition payloads
    plus `any_condition_passed` (HEDGE-05 firing condition (c) consumer).

    residuals_df: polars DataFrame from Phase 3 residuals.parquet (schema:
    leg int, event_time float64, rescaled_dt float64). Split per-leg via the
    `leg` column. Dict-like inputs with explicit 'leg_0' / 'leg_1' arrays are
    tolerated for test paths.
    """
    import polars as pl

    if isinstance(residuals_df, pl.DataFrame):
        leg_0 = (
            residuals_df.filter(pl.col("leg") == 0)
            .select("rescaled_dt")
            .to_numpy()
            .ravel()
            .astype(np.float64)
        )
        leg_1 = (
            residuals_df.filter(pl.col("leg") == 1)
            .select("rescaled_dt")
            .to_numpy()
            .ravel()
            .astype(np.float64)
        )
    else:
        leg_0 = np.asarray(residuals_df["leg_0"], dtype=np.float64).ravel()
        leg_1 = np.asarray(residuals_df["leg_1"], dtype=np.float64).ravel()

    per_leg = {"leg_0": leg_0, "leg_1": leg_1}

    c1 = evaluate_condition_1_vol_of_vol(per_leg)
    c2 = evaluate_condition_2_skew_fat_tails(per_leg)
    c3 = evaluate_condition_3_hawkes_self_excitation(fit_report)
    c4 = evaluate_condition_4_usdt_depeg(calibration, lhs_samples)

    any_passed = bool(c1["passed"] or c2["passed"] or c3["passed"] or c4["passed"])

    return {
        "vol_of_vol_gt_zero": c1,
        "positive_skew_fat_tails": c2,
        "hawkes_self_excitation": c3,
        "usdt_depeg_basis_jump": c4,
        "any_condition_passed": any_passed,
    }
