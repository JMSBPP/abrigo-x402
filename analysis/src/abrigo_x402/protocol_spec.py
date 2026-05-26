"""Pydantic mirror of fetch/src/protocol-spec.ts zod schema (subset Phase 2 needs).

Phase 2 reads `protocols/<protocol>.toml` from Python to surface the
`[protocol]`, `[protocol.anchor_pool]`, `[protocol.vaults.<id>]`, and
`[panel]` blocks. This module duplicates the zod typings just enough to
let the panel build assert structural invariants without round-tripping
through the TypeScript layer.
"""
from pydantic import BaseModel, Field


class AnchorPool(BaseModel):
    address: str
    fee_tier: int  # bps; 100 for cKES/USDT 0.01% pool
    token0: str
    token1: str


class Vault(BaseModel):
    address: str
    active: bool
    pool_address: str | None = None


class PanelConfig(BaseModel):
    finality_lag_blocks: int = 120


class Protocol(BaseModel):
    name: str
    cold_backfill_from_block: int
    anchor_pool: AnchorPool


class ProtocolSpec(BaseModel):
    protocol: Protocol
    panel: PanelConfig
    vaults: dict[str, Vault] = Field(default_factory=dict)


def load_protocol(path) -> ProtocolSpec:  # noqa: ANN001
    """Read protocols/*.toml; validate via pydantic. NotImplementedError until Wave 1."""
    raise NotImplementedError("Plan 02-01")
