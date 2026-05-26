"""Pydantic mirror of fetch/src/protocol-spec.ts zod schema (subset Phase 2 needs).

Phase 2 reads `protocols/<protocol>.toml` from Python to surface the
`[protocol]`, `[protocol.anchor_pool]`, `[protocol.vaults.<id>]`, and
`[panel]` blocks. This module duplicates the zod typings just enough to
let the panel build assert structural invariants without round-tripping
through the TypeScript layer.
"""
import re
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

HEX_ADDR_RE = r"^0x[0-9a-fA-F]{40}$"


def _validate_hex_addr(v: str) -> str:
    if not re.match(HEX_ADDR_RE, v):
        raise ValueError(f"not a valid hex address: {v}")
    return v


class AnchorPool(BaseModel):
    address: str
    fee_tier: int = Field(ge=0, le=1_000_000)  # bps; 100 for cKES/USDT 0.01% pool
    token0: str
    token1: str

    @field_validator("address", "token0", "token1")
    @classmethod
    def _hex_addr(cls, v: str) -> str:
        return _validate_hex_addr(v)


class Vault(BaseModel):
    address: str
    active: bool = False
    pool_address: str | None = None

    @field_validator("address")
    @classmethod
    def _hex_addr(cls, v: str) -> str:
        return _validate_hex_addr(v)


class PanelConfig(BaseModel):
    finality_lag_blocks: int = 120


class Protocol(BaseModel):
    name: str
    cold_backfill_from_block: int = Field(ge=0)
    anchor_pool: AnchorPool


class ProtocolSpec(BaseModel):
    protocol: Protocol
    panel: PanelConfig = Field(default_factory=PanelConfig)
    vaults: dict[str, Vault] = Field(default_factory=dict)


def load_protocol(path: str | Path) -> ProtocolSpec:
    """Read protocols/*.toml and validate via pydantic.

    Raises pydantic ValidationError on schema drift (missing required fields,
    bad address format, out-of-range fee_tier).
    """
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    # TOML nests vaults under [protocol.vaults.<id>]; pydantic flattens
    proto = dict(raw.get("protocol", {}))
    vaults = proto.pop("vaults", {})
    # Strip per-protocol fields that aren't on the Protocol pydantic model.
    # ichi.toml carries chain_id, factory_address, blockscout urls, iteration, etc.
    # The pydantic model only validates the subset Phase 2 needs; extras are dropped
    # to avoid ValidationError on extra='forbid' (default is 'ignore', kept explicit).
    payload = {
        "protocol": proto,
        "panel": raw.get("panel", {}),
        "vaults": vaults,
    }
    return ProtocolSpec.model_validate(payload)
