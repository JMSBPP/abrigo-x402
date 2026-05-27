"""USDT depeg jump-leg calibration: literature-range stipulation (Merton 1976 ballpark) + N=64 LHS.

CONTEXT.md (commit e600d3a): evidence_source = 'literature_range_stipulation'.
Hernandez Cruz 2024 and Wu & Liu 2026 do NOT publish jump-diffusion parameters and
MUST NOT be cited as parameter sources.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import qmc

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

# Canonical evidence_source label — fail-loud if a doc carries a different value.
EXPECTED_EVIDENCE_SOURCE: str = "literature_range_stipulation"


def _resolve_calibration_path(calibration_path: str | Path) -> Path:
    """Resolve a calibration path, falling back to a repo-root-relative lookup.

    The default ``notes/usdt_depeg_calibration.md`` is repo-root-relative; when
    callers (pytest from ``analysis/``, the orchestrator from anywhere) provide
    a relative path that does not resolve against the current cwd, walk up from
    this module to find the repo root (the parent containing ``notes/``).
    """
    p = Path(calibration_path)
    if p.is_absolute() or p.exists():
        return p
    # Walk up from this module to find a directory containing the target.
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / p
        if candidate.exists():
            return candidate
    return p  # let the caller's open() raise FileNotFoundError with the original path


def load_calibration(calibration_path: str | Path = "notes/usdt_depeg_calibration.md") -> dict:
    """Return {evidence_source, base_triple: {lambda_J, mu_J, sigma_J}}.

    Parses YAML frontmatter delimited by ``---`` from the markdown doc. Raises
    ValueError if frontmatter is missing or if ``evidence_source`` is not the
    canonical ``literature_range_stipulation`` label (no silent fallback to
    different evidence sources, per CONTEXT.md commit e600d3a).
    """
    resolved = _resolve_calibration_path(calibration_path)
    text = resolved.read_text()
    m = re.match(r"---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        raise ValueError(
            f"{resolved}: missing YAML frontmatter delimited by ---"
        )
    fm = yaml.safe_load(m.group(1))
    evidence_source = fm.get("evidence_source")
    if evidence_source != EXPECTED_EVIDENCE_SOURCE:
        raise ValueError(
            f"{resolved}: evidence_source must be "
            f"{EXPECTED_EVIDENCE_SOURCE!r} per CONTEXT.md commit e600d3a "
            f"(got {evidence_source!r})"
        )
    bt = fm.get("base_triple", {}) or {}
    return {
        "evidence_source": evidence_source,
        "base_triple": {
            "lambda_J": float(bt.get("lambda_J", DEFAULT_LAMBDA_J)),
            "mu_J": float(bt.get("mu_J", DEFAULT_MU_J)),
            "sigma_J": float(bt.get("sigma_J", DEFAULT_SIGMA_J)),
        },
    }


def generate_lhs_samples(
    base_lambda_J: float = DEFAULT_LAMBDA_J,
    base_mu_J: float = DEFAULT_MU_J,
    base_sigma_J: float = DEFAULT_SIGMA_J,
    n_samples: int = LHS_N_SAMPLES,
    bound_ratio: float = LHS_BOUND_RATIO,
    seed: int = LHS_SEED,
) -> np.ndarray:
    """Return (n_samples, 3) float64 LHS samples of (lambda_J, mu_J, sigma_J).

    Bounds per dimension are ``[base*(1-bound_ratio), base*(1+bound_ratio)]``,
    normalized via min/max so a negative base (e.g., mu_J = -0.05) yields
    ``[base*(1+bound_ratio), base*(1-bound_ratio)] = [-0.075, -0.025]`` rather
    than an inverted interval. Sampling uses ``scipy.stats.qmc.LatinHypercube``
    with the user-supplied seed for byte-identical reproducibility.
    """
    sampler = qmc.LatinHypercube(d=3, seed=seed)
    unit = sampler.random(n=n_samples)
    bases = np.array([base_lambda_J, base_mu_J, base_sigma_J], dtype=np.float64)
    lo_raw = bases * (1.0 - bound_ratio)
    hi_raw = bases * (1.0 + bound_ratio)
    l_bounds = np.minimum(lo_raw, hi_raw)
    u_bounds = np.maximum(lo_raw, hi_raw)
    scaled = qmc.scale(unit, l_bounds=l_bounds, u_bounds=u_bounds)
    return scaled.astype(np.float64)


def run_lhs_sensitivity(
    calibration: dict,
    base_passes: bool,
    n_samples: int = LHS_N_SAMPLES,
    seed: int = LHS_SEED,
) -> dict:
    """Return {n_samples, n_flips, flip_examples, sensitivity_fragile}.

    sensitivity_fragile follows literal any-cell-flip semantics per CONTEXT.md
    commit e600d3a — even a single LHS cell whose condition-4 verdict differs
    from ``base_passes`` flips the flag to True. The caller (Plan 04-04's
    evaluate_condition_4_usdt_depeg) supplies the gate-decision callable and
    threads it through this scaffold in Plan 04-08.
    """
    raise NotImplementedError("Plan 04-06 implements HEDGE-03 LHS sensitivity sweep")
