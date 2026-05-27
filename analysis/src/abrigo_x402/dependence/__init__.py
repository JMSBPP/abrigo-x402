"""Cross-leg dependence inference (Phase 4 L5)."""
from abrigo_x402.dependence.cross_correlogram import cross_correlogram_event_index
from abrigo_x402.dependence.permutation_null import permutation_null_max_abs_rho
from abrigo_x402.dependence.copula import (
    fit_5_families_bic,
    REQUIRED_JOINT_DIST_KEYS,
    VINE_FALLBACK_DELTA_BIC_THRESHOLD,
    _pit_with_clipping,
)

__all__ = [
    "cross_correlogram_event_index",
    "permutation_null_max_abs_rho",
    "fit_5_families_bic",
    "REQUIRED_JOINT_DIST_KEYS",
    "VINE_FALLBACK_DELTA_BIC_THRESHOLD",
    "_pit_with_clipping",
]
