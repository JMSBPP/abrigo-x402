"""FFT-based Carr-Madan static-replication strip on convergence-tested grid.

Math route (Carr & Madan 2001, "Towards a Theory of Volatility Trading"):

  Strip price = f(F) + ∫_0^F p(K) f''(K) dK + ∫_F^∞ c(K) f''(K) dK

  where:
    F           = forward (here taken as the mean / centre of the density)
    p(K)/c(K)   = OTM put/call prices implied from the characteristic function
                  via Fourier inversion on the FFT grid
    f''(K)      = second derivative of the payoff f(S_T)

  For the v1.0 linear-forward payoff f(S)=S, f(F)=F and f''=delta(K-F) collapse
  both integrals — the FFT therefore computes a single density quadrature
  that we label `strip_prices` (f''(K)-weighted price contribution per strike).
  For v2.0 streaming-PV payoffs the integrals contribute non-trivially and the
  same FFT density kernel is reused (RESEARCH Pattern 5 — polymorphic payoff).

Per PRE_REGISTRATION §Carr-Madan Grid Numerical Tolerances (amendment 2026-05-27):
  * POSITIVITY_TOLERANCE = 0.001 (0.1% negative mass relative to total |q|)
  * Grid start: 2^11. Escalate to 2^12 EXACTLY ONCE. Abort to strip_degenerate
    on failure.
  * NEVER silently switch to COS or PROJ methods (CONTEXT.md HEDGE-02 lock).

Per iter-3 revision (2026-05-27): a fourth HEDGE-05 firing condition
`null_strip_unavailable` routes the gate-passed + strip-not-emittable hybrid
state. compute_strip emits a `reason` field on strip_degenerate with value
"positivity_fail_after_2_12"; the orchestrator (Plan 04-08) injects
"build_failed_upstream" when the upstream characteristic-function builder
raises. null_result.decide_firing_condition reads this field and returns
"null_strip_unavailable".

Integration: Fourier inversion via numpy FFT primitives only. Numerical-
quadrature anti-patterns (scipy quadrature routines, numpy trapezoidal
integration) are forbidden by the carr-madan-anti-pattern-gate pre-commit
hook — those names are the literal regex the gate matches, so they must not
appear in source even in docstrings or comments.
"""
from __future__ import annotations

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
    "reason",                 # iter-3: "positivity_fail_after_2_12" | "build_failed_upstream"
)

POSITIVITY_TOLERANCE: float = 0.001  # PRE_REGISTRATION amendment 2026-05-27
DEFAULT_N_GRID: int = 2**11
ESCALATED_N_GRID: int = 2**12
DEFAULT_U_MAX: float = 200.0          # Fourier-domain truncation upper bound

# iter-3: reason values surfaced to null_result.decide_firing_condition for
# the fourth firing condition `null_strip_unavailable`.
REASON_POSITIVITY_FAIL: str = "positivity_fail_after_2_12"
REASON_BUILD_FAILED_UPSTREAM: str = "build_failed_upstream"  # set by orchestrator


def _fft_inverse_density(
    char_func: Callable[[np.ndarray], np.ndarray],
    n_grid: int,
    u_max: float = DEFAULT_U_MAX,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (k_grid, q_density) from Fourier inversion of char_func on [-u_max, u_max].

      q(k) = (1 / 2π) ∫ φ(u) exp(-i u k) du

    Discretized exclusively via numpy FFT primitives (no scipy quadrature, no
    numpy trapezoidal helper — both are banned by the carr-madan-anti-pattern
    pre-commit gate).
    """
    du = (2.0 * u_max) / n_grid
    u_grid = np.linspace(-u_max, u_max - du, n_grid)
    phi_values = char_func(u_grid).astype(np.complex128, copy=False)
    # Centre the spectrum, run the inverse FFT, recover the real-valued
    # density. The (n_grid * du / (2π)) factor maps numpy's normalized iFFT
    # back to the canonical Carr–Madan 2001 Fourier-inversion convention.
    q_density = np.real(
        np.fft.fftshift(np.fft.ifft(np.fft.ifftshift(phi_values)))
    ) * n_grid * du / (2.0 * np.pi)
    # Reciprocal k-grid aligned with the FFT shift.
    dk = (2.0 * np.pi) / (n_grid * du)
    k_grid = np.linspace(-n_grid * dk / 2.0, n_grid * dk / 2.0 - dk, n_grid)
    return k_grid, q_density


def _negative_mass_fraction(q_density: np.ndarray) -> float:
    """Returns ∑ q(k)⁻ / ∑ |q(k)| — the locked Carr-Madan positivity metric."""
    total_abs = float(np.sum(np.abs(q_density)))
    if total_abs == 0.0:
        return 0.0
    neg = float(np.sum(np.where(q_density < 0.0, -q_density, 0.0)))
    return neg / total_abs


def _estimate_char_func_decay_rate(
    char_func: Callable[[np.ndarray], np.ndarray],
) -> float:
    """Crude log-log decay-rate proxy used in strip_degenerate.json provenance.

    Fits |φ(u)| ≈ C · |u|^slope on probes u ∈ {1, 10, 100}; the slope is
    surfaced so the Phase 5 report can publicly document why the strip was
    not emittable.
    """
    u_probe = np.array([1.0, 10.0, 100.0])
    phi_vals = np.abs(char_func(u_probe))
    with np.errstate(divide="ignore", invalid="ignore"):
        return float(
            np.polyfit(np.log(u_probe), np.log(np.maximum(phi_vals, 1e-30)), 1)[0]
        )


def _recommend_alternative_method(decay_rate: float) -> str:
    """Conservative routing of recommended_method per decay slope.

    Flat or near-flat decay (slope > -0.5)   => no realistic recovery: "none".
    Moderate decay   (-1.5 < slope ≤ -0.5)   => "PROJ" (projection methods
                                                handle moderate-tail char funcs
                                                better than COS in practice).
    Steeper decay    (slope ≤ -1.5)          => "COS" (COS converges where
                                                Fourier inversion struggled
                                                due to truncation rather than
                                                slow decay).
    """
    if decay_rate > -0.5:
        return "none"
    if decay_rate > -1.5:
        return "PROJ"
    return "COS"


def compute_strip(
    payoff: Callable[[np.ndarray], np.ndarray],  # f(S_T) — v2.0 polymorphism per RESEARCH Pattern 5
    char_func: Callable[[np.ndarray], np.ndarray],
    n_grid: int = DEFAULT_N_GRID,
    positivity_tolerance: float = POSITIVITY_TOLERANCE,
    max_escalations: int = 1,
) -> dict:
    """Carr-Madan replicating strip with 2^11 -> 2^12 escalation and abort-to-degenerate.

    Returns:
      * Success dict with REQUIRED_STRIP_KEYS (minus orchestrator-injected
        provenance keys) on positivity-pass.
      * Degenerate dict with STRIP_DEGENERATE_KEYS (minus orchestrator-injected
        provenance keys) on positivity-fail after max_escalations escalations.

    The signature is polymorphic in `payoff` per RESEARCH Pattern 5 — v1.0
    passes the linear-forward payoff (LP-fee revenue); v2.0 will pass the
    stream-PV payoff for streaming-tokenization. The FFT density kernel is
    reused unchanged across payoff classes.

    The implementation NEVER silently falls back to COS or PROJ methods; on
    exhausted escalation it returns a degenerate result whose
    `recommended_method` field merely flags which alternative the Phase 5
    report should document — the alternative method is NOT executed here
    (CONTEXT.md HEDGE-02 lock).
    """
    last_q_density: np.ndarray | None = None
    for attempt in range(max_escalations + 1):
        current_n = n_grid * (2 ** attempt)
        k_grid, q_density = _fft_inverse_density(char_func, current_n)
        neg_frac = _negative_mass_fraction(q_density)
        last_q_density = q_density
        if neg_frac < positivity_tolerance:
            payoffs = payoff(k_grid)
            # Normalize density (positive support only for pricing)
            q_pos = np.where(q_density > 0.0, q_density, 0.0)
            norm = float(np.sum(q_pos))
            strip_prices = (payoffs * q_pos / max(norm, 1e-30)).tolist()
            return {
                "strip_prices": strip_prices,
                "strikes": k_grid.tolist(),
                "n_grid_used": int(current_n),
                "escalated_to_2_12": bool(attempt > 0),
                "negative_mass_fraction": float(neg_frac),
                "positivity_tolerance": float(positivity_tolerance),
            }

    # Exhausted escalations -> degenerate (iter-3 Issue 1: emit `reason` for
    # the fourth-firing-condition routing in null_result.decide_firing_condition).
    assert last_q_density is not None  # by construction at least one pass ran
    max_neg = float(np.min(last_q_density))
    total_neg = float(np.sum(np.where(last_q_density < 0.0, -last_q_density, 0.0)))
    decay = _estimate_char_func_decay_rate(char_func)
    recommended = _recommend_alternative_method(decay)
    return {
        "max_negative_value": max_neg,
        "total_negative_mass": total_neg,
        "characteristic_function_decay_rate": decay,
        "recommended_method": recommended,
        "reason": REASON_POSITIVITY_FAIL,  # iter-3: routes to null_strip_unavailable (d)
    }
