"""Four-condition convex-dominance gate per SOMNIA_DRAFT §FUNCTIONAL FORM.

Condition 4 is depeg + basis jump (SC-2). The pegged stablecoin is referenced by
the calibration document (notes/usdt_depeg_calibration.md), not by literal in this
module — anti-pattern grep gates would trip otherwise.
"""

REQUIRED_GATE_REPORT_KEYS: tuple[str, ...] = (
    "chainId", "contractAddress", "blockRange",
    "fetchTimestamp", "dataHash", "gitCommit", "run_id",
    "vol_of_vol_gt_zero",         # {passed: bool, evidence: dict}
    "positive_skew_fat_tails",    # {passed: bool, evidence: dict}
    "hawkes_self_excitation",     # {passed: bool, evidence: dict}
    "usdt_depeg_basis_jump",      # {passed: bool, evidence: dict (incl. sensitivity_fragile + sensitivity_summary)}
    "any_condition_passed",       # bool — HEDGE-05 firing condition (c) consumes this
)


def evaluate_condition_1_vol_of_vol(residuals_df) -> dict:
    """Return {passed: bool, evidence: {...}}. Condition 1: vol-of-vol > 0 per leg."""
    raise NotImplementedError("Plan 04-04 implements HEDGE-01 condition 1")


def evaluate_condition_2_skew_fat_tails(residuals_df) -> dict:
    """Return {passed: bool, evidence: {...}}. Condition 2: positive skew / fat tails per leg."""
    raise NotImplementedError("Plan 04-04 implements HEDGE-01 condition 2")


def evaluate_condition_3_hawkes_self_excitation(fit_report: dict) -> dict:
    """Return {passed: bool, evidence: {...}}.

    Reads fit_report :: hawkes_mv_params :: branching_ratio + gate_criteria.eta_floor_met
    from Phase 3. Reuses canonical _hawkes_loglik_vectorized for any re-evaluation
    (Pattern F — NOT tick.score()).
    """
    raise NotImplementedError("Plan 04-04 implements HEDGE-01 condition 3")


def evaluate_condition_4_usdt_depeg(calibration: dict, lhs_samples) -> dict:
    """Return {passed: bool, evidence: {source: 'literature_range_stipulation', base_triple: {...},
    sensitivity_fragile: bool, sensitivity_summary: {n_samples: 64, n_flips: int, flip_examples: [...]}}}.

    DEPEG framing per SC-2: pegged-stablecoin depeg + basis-leg jump. Calibration is
    sourced from notes/usdt_depeg_calibration.md (literature-range stipulation, NOT
    a port from any specific paper — see CONTEXT.md commit e600d3a).
    """
    raise NotImplementedError("Plan 04-04 implements HEDGE-01 condition 4")


def evaluate_four_conditions(residuals_df, fit_report: dict, calibration: dict, lhs_samples) -> dict:
    """Composite evaluator. Returns a dict matching REQUIRED_GATE_REPORT_KEYS shape
    (sans the PANEL-02 header — the orchestrator merges that on write).

    `any_condition_passed`: True iff at least one of the four `passed` booleans is True.
    HEDGE-05 firing condition (c) — zero-convex-condition — consumes this flag.
    """
    raise NotImplementedError("Plan 04-04 implements HEDGE-01 composite gate")
