"""Hedge CLI entry: wires dependence + falsification + strip + stress + null_result modules.

Single `hedge` subcommand with --stage flag per CONTEXT.md Claude's Discretion.
"""
from pathlib import Path

CHAR_FUNC_SOBOL_N: int = 2**16  # quasi-MC grid size for char-func construction from copula winner


def _build_char_func_from_winner(copula_winner: dict, marginals: dict):
    """Build a callable char_func(u: ndarray) -> ndarray from the 5-family BIC winner.

    Uses CHAR_FUNC_SOBOL_N-point Sobol quasi-Monte-Carlo on (U_1, U_2) ~ winner-copula,
    inverse-transformed through the empirical marginals.
    """
    raise NotImplementedError("Plan 04-08 implements char-func construction from copula winner")


def run_hedge(run_id: str, stage: str = "all", run_dir_root: Path = Path("data/fits/ichi")) -> dict:
    """stage ∈ {'dependence', 'gate', 'strip', 'stress', 'null', 'all'}.

    Writes (per stage): joint_dist.json | gate_report.json | (strip.json | strip_degenerate.json) |
    stress_report.json | reports/ichi.pdf.
    Returns a dict with paths to all written artifacts + firing_condition (None if no fire).
    """
    raise NotImplementedError("Plan 04-08 implements hedge orchestrator + CLI subcommand")
