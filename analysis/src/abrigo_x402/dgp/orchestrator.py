"""Top-level Phase 3 fit pipeline. Returns fit_report.json dict with full SC-1 metadata header + DGP-01..06 results."""
from __future__ import annotations
from pathlib import Path


def run_fit(
    panel_path: Path,
    out_dir: Path,
    chain_id: int = 42220,
    contract_address: str = "0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F",
    block_range: tuple[int, int] = (0, 0),
    bootstrap_reps: int = 1000,
    git_commit: str | None = None,
) -> dict:
    """Returns fit_report.json dict; also writes residuals.parquet to out_dir/<run_id>/."""
    raise NotImplementedError("Wave 2 plan 03-07 implements this (full orchestrator)")
