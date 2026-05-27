"""FFT-based Carr-Madan static-replication strip on convergence-tested grid.

Per RESEARCH Pattern 5 — polymorphic payoff signature for v2.0 streaming-tokenization.
Per PRE_REGISTRATION §Carr-Madan Grid Numerical Tolerances: 0.1% positivity tolerance,
2^11->2^12 escalation, abort to strip_degenerate.json after 2^12 fails.

Integration: np.fft.fft / np.fft.ifft ONLY. Numerical-quadrature anti-patterns
(scipy quadrature routines, numpy trapezoidal integration) are forbidden by a
pre-commit grep gate — those names are the literal regex the gate matches, so
they must not appear in source even in docstrings or comments.
"""
from typing import Callable
import numpy as np

REQUIRED_STRIP_KEYS: tuple[str, ...] = (
    "chainId", "contractAddress", "blockRange",
    "fetchTimestamp", "dataHash", "gitCommit", "run_id",
    "strip_prices",            # list[float] per strike
    "strikes",                 # list[float]
    "n_grid_used",             # int — 2^11 or 2^12
    "escalated_to_2_12",       # bool
    "negative_mass_fraction",  # float
    "positivity_tolerance",    # float — 0.001 from PRE_REG amendment
)

STRIP_DEGENERATE_KEYS: tuple[str, ...] = (
    "chainId", "contractAddress", "blockRange",
    "fetchTimestamp", "dataHash", "gitCommit", "run_id",
    "max_negative_value",
    "total_negative_mass",
    "characteristic_function_decay_rate",
    "recommended_method",     # "COS" | "PROJ" | "none"
)

POSITIVITY_TOLERANCE: float = 0.001  # PRE_REGISTRATION amendment 2026-05-27


def compute_strip(
    payoff: Callable[[np.ndarray], np.ndarray],   # f(S_T) — v2.0 polymorphism per RESEARCH Pattern 5
    char_func: Callable[[np.ndarray], np.ndarray],
    n_grid: int = 2**11,
    positivity_tolerance: float = POSITIVITY_TOLERANCE,
    max_escalations: int = 1,
) -> dict:
    """Return strip dict (REQUIRED_STRIP_KEYS) on positivity-pass OR strip_degenerate dict
    (STRIP_DEGENERATE_KEYS) on positivity-fail after max_escalations escalations.

    Uses np.fft.fft / np.fft.ifft ONLY. The pre-commit anti-pattern gate forbids
    naming the prohibited quadrature routines (see module docstring).
    """
    raise NotImplementedError("Plan 04-05 implements HEDGE-02 Carr-Madan strip")
