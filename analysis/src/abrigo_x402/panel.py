"""Orchestrator: composes ingest + decoders + phantom_filter + vault_state + revenue_leg + fx_snap + provenance.

See RESEARCH §H Pattern 1 for the canonical composition order.
End-to-end Phase 2 panel build, single-vault ICHI cKES/USDT microcosm.
"""
from pathlib import Path

import polars as pl

from .protocol_spec import ProtocolSpec


def build_panel(
    cache_path: Path,
    fx_sidecar_path: Path,
    vault_state_sidecar_path: Path,
    forno_head: int,
    protocol_spec: ProtocolSpec,
) -> pl.DataFrame:
    """End-to-end panel build. See RESEARCH §H Pattern 1."""
    raise NotImplementedError("Plan 02-08")
