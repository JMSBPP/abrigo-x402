"""PANEL-01: protocol_spec.load_protocol tests."""
from pathlib import Path

import pytest
from pydantic import ValidationError

from abrigo_x402.protocol_spec import ProtocolSpec, load_protocol

REPO_ROOT = Path(__file__).resolve().parents[2]
ICHI_TOML = REPO_ROOT / "protocols" / "ichi.toml"


def test_load_ichi_top_level():
    spec = load_protocol(ICHI_TOML)
    assert isinstance(spec, ProtocolSpec)
    assert spec.protocol.name == "ichi"
    assert spec.protocol.cold_backfill_from_block == 60_000_000
    assert spec.protocol.anchor_pool.fee_tier == 100
    assert spec.panel.finality_lag_blocks == 120


def test_load_ichi_anchor_vault():
    spec = load_protocol(ICHI_TOML)
    anchor = spec.vaults["cKES_USDT_anchor"]
    assert anchor.address.lower() == "0xe304b980535c29869983bc58d129f984fec4176f"
    assert anchor.active is True


def test_missing_required_field_raises(tmp_path):
    bad = tmp_path / "bad.toml"
    bad.write_text("[protocol]\nname = 'x'\n")  # missing cold_backfill_from_block + anchor_pool
    with pytest.raises(ValidationError):
        load_protocol(bad)


def test_missing_panel_block_defaults_to_120(tmp_path):
    t = tmp_path / "no_panel.toml"
    t.write_text(
        """
[protocol]
name = "x"
cold_backfill_from_block = 60000000
[protocol.anchor_pool]
address = "0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F"
fee_tier = 100
token0 = "0x456a3D042C0DbD3db53D5489e98dFb038553B0d0"
token1 = "0x48065fbBE25f71C9282ddf5e1cD6D6A887483D5e"
"""
    )
    spec = load_protocol(t)
    assert spec.panel.finality_lag_blocks == 120  # pydantic default


def test_invalid_address_raises(tmp_path):
    t = tmp_path / "bad_addr.toml"
    t.write_text(
        """
[protocol]
name = "x"
cold_backfill_from_block = 60000000
[protocol.anchor_pool]
address = "not-an-address"
fee_tier = 100
token0 = "0x456a3D042C0DbD3db53D5489e98dFb038553B0d0"
token1 = "0x48065fbBE25f71C9282ddf5e1cD6D6A887483D5e"
"""
    )
    with pytest.raises(ValidationError):
        load_protocol(t)
