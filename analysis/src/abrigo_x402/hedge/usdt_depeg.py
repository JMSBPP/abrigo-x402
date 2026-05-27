"""USDT depeg jump-leg calibration: literature-range stipulation (Merton 1976 ballpark) + N=64 LHS.

CONTEXT.md (commit e600d3a): evidence_source = 'literature_range_stipulation'.
Hernandez Cruz 2024 and Wu & Liu 2026 do NOT publish jump-diffusion parameters and
MUST NOT be cited as parameter sources.
"""
import numpy as np

# Default jump-diffusion triple — Merton 1976 stablecoin-class ballpark.
# These constants are the SINGLE source of truth in the codebase; the pre-commit
# hardcoded-jump-params-gate enforces that no other module re-declares them.
DEFAULT_LAMBDA_J: float = 0.05        # jumps per year
DEFAULT_MU_J: float = -0.05           # log-return per jump
DEFAULT_SIGMA_J: float = 0.02         # log-return std per jump

JUMP_PARAMS_DEFAULT: dict = {
    "lambda": DEFAULT_LAMBDA_J,
    "mu_J": DEFAULT_MU_J,
    "sigma_J": DEFAULT_SIGMA_J,
}

LHS_N_SAMPLES: int = 64
LHS_BOUND_RATIO: float = 0.5          # ±50% per CONTEXT.md
LHS_SEED: int = 20260527


def load_calibration(calibration_path: str = "notes/usdt_depeg_calibration.md") -> dict:
    """Return {evidence_source: 'literature_range_stipulation', base_triple: {lambda_J, mu_J, sigma_J}}.

    Reads the markdown doc and extracts the stipulated triple.
    """
    raise NotImplementedError("Plan 04-06 implements HEDGE-03 calibration loader")


def generate_lhs_samples(
    base_lambda_J: float = DEFAULT_LAMBDA_J,
    base_mu_J: float = DEFAULT_MU_J,
    base_sigma_J: float = DEFAULT_SIGMA_J,
    n_samples: int = LHS_N_SAMPLES,
    bound_ratio: float = LHS_BOUND_RATIO,
    seed: int = LHS_SEED,
) -> np.ndarray:
    """Return (n_samples, 3) array of (lambda_J, mu_J, sigma_J) samples on ±bound_ratio bracket.

    Implementation: scipy.stats.qmc.LatinHypercube(d=3, seed=seed) + qmc.scale(samples,
    l_bounds=base*(1-bound_ratio), u_bounds=base*(1+bound_ratio)).
    """
    raise NotImplementedError("Plan 04-06 implements HEDGE-03 LHS sampler")


def run_lhs_sensitivity(
    calibration: dict,
    base_passes: bool,
    n_samples: int = LHS_N_SAMPLES,
    seed: int = LHS_SEED,
) -> dict:
    """Return {n_samples, n_flips, flip_examples, sensitivity_fragile}.

    sensitivity_fragile is True iff > 5% of LHS samples flip the condition-4 verdict
    relative to the base_passes baseline (CONTEXT.md locked threshold).
    """
    raise NotImplementedError("Plan 04-06 implements HEDGE-03 LHS sensitivity sweep")
