"""Three-way joint-distribution stress: independence + fitted_joint + comonotone.

Comonotone via shared uniform U_2 = U_1 (Frechet upper bound); reproducible from
empirical marginals alone (CONTEXT.md locked). Tail via empirical-body parametric-tail
per RESEARCH Pitfall 6.
"""
import numpy as np

REQUIRED_STRESS_REPORT_KEYS: tuple[str, ...] = (
    "chainId", "contractAddress", "blockRange",
    "fetchTimestamp", "dataHash", "gitCommit", "run_id",
    "independence_price",
    "fitted_joint_price",
    "comonotone_price",
    "divergence_pct",         # (max - min) / mean * 100
    "divergence_flag",        # bool — True if divergence_pct > 30
    "comonotone_method",      # "empirical_body_parametric_tail" per RESEARCH Pitfall 6
)

DIVERGENCE_FLAG_THRESHOLD_PCT: float = 30.0  # CONTEXT.md locked — flag-only, no hard-fail


def run_three_way_stress(
    payoff,
    marginal_cdf_leg_0,
    marginal_cdf_leg_1,
    fitted_copula,
    n_samples: int = 10_000,
    seed: int = 20260527,
) -> dict:
    """Independence: marginal CDF leg_0 x marginal CDF leg_1.
    Fitted joint: empirical copula sample (copulae.fit().random(N)).
    Comonotone: shared U ~ U(0,1), U_2 = U_1, inverse-transform per leg (Frechet upper bound).
    """
    raise NotImplementedError("Plan 04-07 implements HEDGE-04 three-way stress test")
