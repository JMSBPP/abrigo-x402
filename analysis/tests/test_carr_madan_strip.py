"""Plan 04-05 (Wave 1) — HEDGE-02 Carr-Madan strip tests.

Covers: schema (success), schema (degenerate), Gaussian-baseline-passes-2^11,
fat-tail-escalation, anti-pattern grep guards, iter-3 reason field for
fourth-firing-condition routing, and iter-3 Carr-Madan-2001 citation grep.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import pytest

from abrigo_x402.hedge.carr_madan_strip import (
    POSITIVITY_TOLERANCE,
    REQUIRED_STRIP_KEYS,
    STRIP_DEGENERATE_KEYS,
    compute_strip,
)


# ---------------------------------------------------------------------------
# Test fixtures: characteristic functions and payoffs
# ---------------------------------------------------------------------------

# Provenance keys are injected by the orchestrator (Plan 04-08), not by
# compute_strip itself; this set is excluded from the per-call schema check.
_PROVENANCE_KEYS = {
    "chainId", "contractAddress", "blockRange",
    "fetchTimestamp", "dataHash", "gitCommit", "run_id",
}


def gaussian_char_func(sigma: float = 1.0):
    """Well-behaved Gaussian phi(u) = exp(-sigma^2 u^2 / 2)."""
    def phi(u):
        return np.exp(-0.5 * sigma**2 * u**2)
    return phi


def slow_decay_char_func(alpha: float = 0.3):
    """Slow-decay surrogate: phi(u) = exp(-|u|^alpha).

    For alpha < 2, this is a Bochner-positive-definite function (stable-law-
    like characteristic function); its iFFT remains non-negative and so does
    NOT exercise the abort-to-degenerate path. Used here for the escalation
    test (the inverse may still ride the 2^11/2^12 boundary depending on
    DEFAULT_U_MAX truncation).
    """
    def phi(u):
        return np.exp(-(np.abs(u)) ** alpha)
    return phi


def pathological_non_psd_char_func():
    """Non-positive-definite phi: phi(u) = exp(-|u|^0.3) - 0.5 * exp(-|u|^0.1).

    Because this is a *difference* of two slow-decay envelopes, Bochner's
    theorem does NOT guarantee a non-negative iFFT — empirically the inverse
    transform exhibits ~10% negative mass at both 2^11 and 2^12 with the
    locked DEFAULT_U_MAX = 200, exhausting the single escalation and forcing
    the abort-to-strip_degenerate.json path. This is the canonical fixture
    for the fourth HEDGE-05 firing condition `null_strip_unavailable`.
    """
    def phi(u):
        return np.exp(-(np.abs(u)) ** 0.3) - 0.5 * np.exp(-(np.abs(u)) ** 0.1)
    return phi


def linear_payoff(x):
    return x


def call_option_payoff(x, strike=1.0):
    return np.maximum(x - strike, 0.0)


# ---------------------------------------------------------------------------
# Test 1 — Gaussian + linear payoff: schema success on 2^11 grid
# ---------------------------------------------------------------------------

def test_strip_schema_success_gaussian_baseline():
    result = compute_strip(
        payoff=linear_payoff,
        char_func=gaussian_char_func(1.0),
    )
    # Schema check (excluding orchestrator-injected provenance keys)
    for k in REQUIRED_STRIP_KEYS:
        if k in _PROVENANCE_KEYS:
            continue
        assert k in result, f"missing required strip key: {k}"
    assert result["n_grid_used"] == 2**11
    assert result["escalated_to_2_12"] is False
    assert result["negative_mass_fraction"] < POSITIVITY_TOLERANCE
    assert result["positivity_tolerance"] == POSITIVITY_TOLERANCE


# ---------------------------------------------------------------------------
# Test 2 — Borderline fat-tail (alpha=1.5): escalation OR degenerate
# ---------------------------------------------------------------------------

def test_strip_escalation_to_2_12():
    char = slow_decay_char_func(alpha=1.5)
    result = compute_strip(payoff=linear_payoff, char_func=char)
    # Plan-locked behavior: either success on 2^11 or 2^12, OR degenerate.
    if "n_grid_used" in result:
        assert result["n_grid_used"] in (2**11, 2**12)
        # If we escalated, the escalation flag must be set.
        if result["n_grid_used"] == 2**12:
            assert result["escalated_to_2_12"] is True
    else:
        # degenerate result has different schema
        for k in STRIP_DEGENERATE_KEYS:
            if k in _PROVENANCE_KEYS:
                continue
            assert k in result


# ---------------------------------------------------------------------------
# Test 3 — Pathological fat-tail (alpha=0.3): abort to strip_degenerate
# ---------------------------------------------------------------------------

def test_strip_degenerate_path():
    char = pathological_non_psd_char_func()
    result = compute_strip(payoff=linear_payoff, char_func=char)
    # Expect strip_degenerate schema:
    for k in STRIP_DEGENERATE_KEYS:
        if k in _PROVENANCE_KEYS:
            continue
        assert k in result, f"missing degenerate key: {k}"
    assert result["recommended_method"] in {"COS", "PROJ", "none"}


# ---------------------------------------------------------------------------
# Test 4 — Polymorphic payoff (RESEARCH Pattern 5)
# ---------------------------------------------------------------------------

def test_polymorphic_payoff_call_option():
    result = compute_strip(
        payoff=lambda x: call_option_payoff(x, 1.0),
        char_func=gaussian_char_func(1.0),
    )
    # Either success (strip_prices) or graceful degenerate (max_negative_value).
    assert "strip_prices" in result or "max_negative_value" in result


# ---------------------------------------------------------------------------
# Test 5 — Anti-pattern grep gate: no scipy quadrature / np trapezoid
# ---------------------------------------------------------------------------

def test_anti_pattern_grep_no_scipy_quad_no_trapz():
    repo_root = Path(__file__).resolve().parents[2]
    target = repo_root / "analysis" / "src" / "abrigo_x402" / "hedge" / "carr_madan_strip.py"
    r = subprocess.run(
        [
            "grep",
            "-E",
            r"scipy\.integrate\.(quad|fixed_quad|romberg)|np\.trapz",
            str(target),
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode != 0, f"Anti-pattern hit:\n{r.stdout}"


# ---------------------------------------------------------------------------
# Test 6 — iter-3 Issue 1: strip_degenerate carries `reason` field
# ---------------------------------------------------------------------------

def test_strip_degenerate_reason_field():
    """null_result.decide_firing_condition (Plan 04-08) reads `reason` to route
    the fourth firing condition `null_strip_unavailable`. compute_strip injects
    `positivity_fail_after_2_12` when FFT inversion exhausts escalation."""
    char = pathological_non_psd_char_func()
    result = compute_strip(payoff=linear_payoff, char_func=char)
    assert "reason" in result
    assert result["reason"] == "positivity_fail_after_2_12"


# ---------------------------------------------------------------------------
# Test 7 — iter-3 Issue 1: Carr & Madan 2001 citation present in module
# ---------------------------------------------------------------------------

def test_carr_madan_citation_grep():
    repo_root = Path(__file__).resolve().parents[2]
    target = repo_root / "analysis" / "src" / "abrigo_x402" / "hedge" / "carr_madan_strip.py"
    r = subprocess.run(
        ["grep", "-q", "Carr & Madan 2001", str(target)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, "Module docstring must cite 'Carr & Madan 2001' as canonical strip-formula source"
