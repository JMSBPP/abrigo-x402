"""Falsification gate + Carr-Madan replicating strip + null-result rendering (Phase 4 L6)."""
from abrigo_x402.hedge.falsification import (
    evaluate_condition_1_vol_of_vol,
    evaluate_condition_2_skew_fat_tails,
    evaluate_condition_3_hawkes_self_excitation,
    evaluate_condition_4_usdt_depeg,
    evaluate_four_conditions,
    REQUIRED_GATE_REPORT_KEYS,
)
from abrigo_x402.hedge.carr_madan_strip import (
    compute_strip,
    REQUIRED_STRIP_KEYS,
    STRIP_DEGENERATE_KEYS,
    POSITIVITY_TOLERANCE,
)
from abrigo_x402.hedge.stress_test import (
    run_three_way_stress,
    REQUIRED_STRESS_REPORT_KEYS,
    DIVERGENCE_FLAG_THRESHOLD_PCT,
)
from abrigo_x402.hedge.usdt_depeg import (
    load_calibration,
    generate_lhs_samples,
    run_lhs_sensitivity,
    DEFAULT_LAMBDA_J,
    DEFAULT_MU_J,
    DEFAULT_SIGMA_J,
    LHS_N_SAMPLES,
    JUMP_PARAMS_DEFAULT,
)
from abrigo_x402.hedge.null_result import (
    decide_firing_condition,
    render_null_result_pdf,
    HEDGE05_SIGNATURE,
)
from abrigo_x402.hedge.orchestrator import (
    run_hedge,
    _build_char_func_from_winner,
    CHAR_FUNC_SOBOL_N,
)

__all__ = [
    "evaluate_condition_1_vol_of_vol", "evaluate_condition_2_skew_fat_tails",
    "evaluate_condition_3_hawkes_self_excitation", "evaluate_condition_4_usdt_depeg",
    "evaluate_four_conditions",
    "REQUIRED_GATE_REPORT_KEYS",
    "compute_strip", "REQUIRED_STRIP_KEYS", "STRIP_DEGENERATE_KEYS", "POSITIVITY_TOLERANCE",
    "run_three_way_stress", "REQUIRED_STRESS_REPORT_KEYS", "DIVERGENCE_FLAG_THRESHOLD_PCT",
    "load_calibration", "generate_lhs_samples", "run_lhs_sensitivity",
    "DEFAULT_LAMBDA_J", "DEFAULT_MU_J", "DEFAULT_SIGMA_J",
    "LHS_N_SAMPLES", "JUMP_PARAMS_DEFAULT",
    "decide_firing_condition", "render_null_result_pdf", "HEDGE05_SIGNATURE",
    "run_hedge", "_build_char_func_from_winner", "CHAR_FUNC_SOBOL_N",
]
