"""HEDGE-01 four-condition convex-dominance gate tests (Plan 04-04).

Coverage per CONTEXT.md + RESEARCH §Anti-Patterns:
- Conditions 1–4 positive + negative controls
- SC-2 grep gate (no `usdc` non-comment literals in falsification.py)
- Canonical-LL Pattern F enforcement (`_hawkes_loglik_vectorized` imported; never
  `tick.score` / `loglik_in_sample_raw`)
- Condition-4 evidence source = `literature_range_stipulation` (NOT
  `methodological_port`, NOT `Hernandez Cruz 2024`).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
FALSIFICATION_PATH = REPO_ROOT / "analysis" / "src" / "abrigo_x402" / "hedge" / "falsification.py"


# -------- Condition 1: vol-of-vol > 0 -----------------------------------------


def test_condition_1_positive_heteroscedastic() -> None:
    """Deliberately heteroscedastic rescaled_dt -> condition 1 passes."""
    from abrigo_x402.hedge.falsification import evaluate_condition_1_vol_of_vol

    rng = np.random.default_rng(20260527)
    first_half = rng.exponential(scale=1.0, size=500)
    second_half = rng.exponential(scale=0.1, size=500)
    leg_0 = np.concatenate([first_half, second_half])
    leg_1 = np.concatenate([second_half, first_half])  # mirror

    result = evaluate_condition_1_vol_of_vol({"leg_0": leg_0, "leg_1": leg_1})

    assert result["passed"] is True
    assert "evidence" in result
    # at least one leg must report a vol-of-vol value above the threshold
    per_leg = result["evidence"]["per_leg"]
    assert any(
        (entry.get("vol_of_vol") is not None and entry["vol_of_vol"] > 0.0)
        for entry in per_leg.values()
    )


def test_condition_1_negative_iid_exp() -> None:
    """iid Exp(1) -> condition 1 fails (vol-of-vol ~ 0 on long iid sample)."""
    from abrigo_x402.hedge.falsification import evaluate_condition_1_vol_of_vol

    rng = np.random.default_rng(20260528)
    leg_0 = rng.exponential(scale=1.0, size=1000)
    leg_1 = rng.exponential(scale=1.0, size=1000)

    result = evaluate_condition_1_vol_of_vol({"leg_0": leg_0, "leg_1": leg_1})

    assert result["passed"] is False, (
        f"iid Exp(1) should not exhibit vol-of-vol > threshold; got evidence={result['evidence']}"
    )


# -------- Condition 2: positive skew / fat tails ------------------------------


def test_condition_2_positive_pareto() -> None:
    """Pareto (positive skew + fat tails) -> condition 2 passes."""
    from abrigo_x402.hedge.falsification import evaluate_condition_2_skew_fat_tails

    rng = np.random.default_rng(20260529)
    leg_0 = rng.pareto(a=2.5, size=1000) + 1.0
    leg_1 = rng.pareto(a=2.5, size=1000) + 1.0

    result = evaluate_condition_2_skew_fat_tails({"leg_0": leg_0, "leg_1": leg_1})

    assert result["passed"] is True
    per_leg = result["evidence"]["per_leg"]
    assert any(
        (entry.get("skew") is not None and entry["skew"] > 0.0 and entry["excess_kurt"] > 0.0)
        for entry in per_leg.values()
    )


def test_condition_2_negative_normal() -> None:
    """Normal(0, 1) -> condition 2 fails (skew ~ 0, kurt ~ 0)."""
    from abrigo_x402.hedge.falsification import evaluate_condition_2_skew_fat_tails

    rng = np.random.default_rng(20260530)
    leg_0 = rng.standard_normal(size=2000)
    leg_1 = rng.standard_normal(size=2000)

    result = evaluate_condition_2_skew_fat_tails({"leg_0": leg_0, "leg_1": leg_1})

    assert result["passed"] is False, (
        f"Normal(0,1) should not exhibit positive skew + fat tails; got {result['evidence']}"
    )


# -------- Condition 3: Hawkes self-excitation ---------------------------------


def test_condition_3_positive_high_branching() -> None:
    """branching_ratio=0.5 + eta_floor_met -> condition 3 passes."""
    from abrigo_x402.hedge.falsification import evaluate_condition_3_hawkes_self_excitation

    fit_report = {
        "hawkes_mv_params": {
            "branching_ratio": 0.5,
            "adjacency": [[0.2, 0.05], [0.04, 0.21]],
        },
        "gate_criteria": {
            "lr_rejects": True,
            "eta_floor_met": True,
            "ks_passes": True,
            "ci_width_ok": True,
        },
    }
    result = evaluate_condition_3_hawkes_self_excitation(fit_report)

    assert result["passed"] is True
    assert result["evidence"]["branching_ratio"] == 0.5
    assert result["evidence"]["eta_floor_met"] is True
    assert "canonical_ll_source" in result["evidence"]
    # Canonical-LL contract reference (Pattern F)
    assert "_hawkes_loglik_vectorized" in result["evidence"]["canonical_ll_source"]


def test_condition_3_negative_low_branching() -> None:
    """branching_ratio=0.05 + eta_floor_met=False -> condition 3 fails."""
    from abrigo_x402.hedge.falsification import evaluate_condition_3_hawkes_self_excitation

    fit_report = {
        "hawkes_mv_params": {
            "branching_ratio": 0.05,
            "adjacency": [[0.025, 0.0], [0.0, 0.025]],
        },
        "gate_criteria": {
            "lr_rejects": False,
            "eta_floor_met": False,
            "ks_passes": True,
            "ci_width_ok": False,
        },
    }
    result = evaluate_condition_3_hawkes_self_excitation(fit_report)

    assert result["passed"] is False


# -------- Condition 4: USDT depeg + literature_range_stipulation --------------


def test_condition_4_source_is_literature_range_stipulation() -> None:
    """Evidence source MUST be 'literature_range_stipulation' (CONTEXT.md commit e600d3a)."""
    from abrigo_x402.hedge.falsification import evaluate_condition_4_usdt_depeg

    calibration = {
        "evidence_source": "literature_range_stipulation",
        "base_triple": {"lambda_J": 0.05, "mu_J": -0.05, "sigma_J": 0.02},
    }
    rng = np.random.default_rng(20260531)
    lhs_samples = np.column_stack(
        [
            rng.uniform(0.025, 0.075, size=64),
            rng.uniform(-0.075, -0.025, size=64),
            rng.uniform(0.01, 0.03, size=64),
        ]
    )

    result = evaluate_condition_4_usdt_depeg(calibration, lhs_samples)

    assert result["evidence"]["source"] == "literature_range_stipulation"
    assert result["evidence"]["source"] != "methodological_port"
    assert "sensitivity_summary" in result["evidence"]
    assert result["evidence"]["sensitivity_summary"]["n_samples"] == 64
    assert "sensitivity_fragile" in result["evidence"]
    assert "base_triple" in result["evidence"]


# -------- SC-2 grep gate ------------------------------------------------------


def test_sc2_no_usdc_literals_outside_comments() -> None:
    """grep -i '^[^#]*usdc' must exit non-zero on falsification.py."""
    result = subprocess.run(
        ["grep", "-i", "^[^#]*usdc", str(FALSIFICATION_PATH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, (
        f"SC-2 violation: found `usdc` literal in non-comment code path of "
        f"{FALSIFICATION_PATH}:\n{result.stdout}"
    )


# -------- Pattern F canonical-LL contract -------------------------------------


def test_canonical_ll_contract_pattern_F() -> None:
    """falsification.py MUST import _hawkes_loglik_vectorized + NOT use tick.score / loglik_in_sample_raw."""
    src = FALSIFICATION_PATH.read_text()

    assert "_hawkes_loglik_vectorized" in src, (
        "Condition 3 must reference canonical Hawkes LL per Pattern F"
    )
    assert "from abrigo_x402.dgp.lr_test import" in src, (
        "Pattern F: condition-3 canonical-LL source must be imported from dgp.lr_test"
    )
    assert "tick.score" not in src, (
        "Pattern F violation: tick.score is wrong probability space under LS fallback"
    )
    assert "loglik_in_sample_raw" not in src, (
        "Pattern F violation: raw LL is upstream LS-fallback objective, not canonical"
    )


# -------- Condition-4 anti-pattern: no Hernandez Cruz citation ----------------


def test_condition_4_does_not_cite_hernandez_cruz() -> None:
    """Hernandez Cruz 2024 / Wu & Liu 2026 MUST NOT appear as parameter source (RESEARCH Pitfall 1)."""
    src = FALSIFICATION_PATH.read_text()
    assert "Hernandez Cruz" not in src, (
        "AF-03 violation: Hernandez Cruz 2024 does not publish jump-diffusion params"
    )
    assert "methodological_port" not in src, (
        "CONTEXT.md commit e600d3a: source field is 'literature_range_stipulation', "
        "NOT 'methodological_port'"
    )
