"""Tests for `abrigo_x402.vault_state` — Plan 02-04 Python reader.

Verifies:
  * `load_vault_state(jsonl_path)` reads TS sidecar JSONL into a typed polars frame
  * `attach_in_range(swap_df, vault_df)` left-joins on blockNumber and computes
    `vault_in_range = (lowerTick <= tick <= upperTick)` with conservative-False
    semantics when the vault state is missing for a Swap's block.
"""
from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import pytest

from abrigo_x402.vault_state import attach_in_range, load_vault_state


@pytest.fixture
def vault_jsonl(tmp_path: Path) -> Path:
    rows = [
        {
            "blockNumber": 100,
            "totalAmounts_0": "1000000000000000000",
            "totalAmounts_1": "2000000000000000000",
            "totalSupply": "5000000000000000000",
            "currentTick": 12345,
            "lowerTick": 10000,
            "upperTick": 20000,
        },
        {
            "blockNumber": 200,
            "totalAmounts_0": "1100000000000000000",
            "totalAmounts_1": "2100000000000000000",
            "totalSupply": "5000000000000000000",
            "currentTick": 14000,
            "lowerTick": 10000,
            "upperTick": 20000,
        },
        {
            "blockNumber": 300,
            "totalAmounts_0": "1200000000000000000",
            "totalAmounts_1": "2200000000000000000",
            "totalSupply": "5100000000000000000",
            "currentTick": 25000,
            "lowerTick": 10000,
            "upperTick": 20000,
        },
    ]
    p = tmp_path / "vault_state.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return p


def test_load_vault_state_schema(vault_jsonl: Path) -> None:
    df = load_vault_state(vault_jsonl)
    assert df.height == 3
    assert df.schema["blockNumber"] == pl.Int64
    assert df.schema["currentTick"] == pl.Int32
    assert df.schema["lowerTick"] == pl.Int32
    assert df.schema["upperTick"] == pl.Int32
    assert df.schema["totalAmounts_0"] == pl.String
    assert df.schema["totalSupply"] == pl.String


def test_attach_in_range_true(vault_jsonl: Path) -> None:
    vs = load_vault_state(vault_jsonl)
    swap_df = pl.DataFrame(
        {"blockNumber": [100], "tick": [12345], "event_name": ["Swap"]},
        schema={"blockNumber": pl.Int64, "tick": pl.Int32, "event_name": pl.String},
    )
    out = attach_in_range(swap_df, vs)
    assert out["vault_in_range"][0] is True


def test_attach_in_range_false_above(vault_jsonl: Path) -> None:
    vs = load_vault_state(vault_jsonl)
    swap_df = pl.DataFrame(
        {"blockNumber": [300], "tick": [25000], "event_name": ["Swap"]},
        schema={"blockNumber": pl.Int64, "tick": pl.Int32, "event_name": pl.String},
    )
    out = attach_in_range(swap_df, vs)
    # tick = upperTick (25000 vs upper=20000) → out-of-range
    assert out["vault_in_range"][0] is False


def test_attach_in_range_missing_vault_state_block(vault_jsonl: Path) -> None:
    vs = load_vault_state(vault_jsonl)
    swap_df = pl.DataFrame(
        {"blockNumber": [999], "tick": [15000], "event_name": ["Swap"]},
        schema={"blockNumber": pl.Int64, "tick": pl.Int32, "event_name": pl.String},
    )
    out = attach_in_range(swap_df, vs)
    # No vault state at block 999 → conservative False (NULL → False).
    assert out["vault_in_range"][0] is False


def test_attach_in_range_brings_vault_columns(vault_jsonl: Path) -> None:
    vs = load_vault_state(vault_jsonl)
    swap_df = pl.DataFrame(
        {"blockNumber": [100], "tick": [12345], "event_name": ["Swap"]},
        schema={"blockNumber": pl.Int64, "tick": pl.Int32, "event_name": pl.String},
    )
    out = attach_in_range(swap_df, vs)
    # Vault state columns appear on the swap row after join.
    assert "lowerTick" in out.columns
    assert "upperTick" in out.columns
    assert "totalSupply" in out.columns
    # Vault's own currentTick is renamed to avoid clashing with swap.tick.
    assert "vault_currentTick" in out.columns
    assert out["lowerTick"][0] == 10000
    assert out["upperTick"][0] == 20000


def test_attach_in_range_boundary_inclusive(vault_jsonl: Path) -> None:
    vs = load_vault_state(vault_jsonl)
    # tick == lowerTick → in-range (closed interval)
    swap_df = pl.DataFrame(
        {"blockNumber": [100], "tick": [10000], "event_name": ["Swap"]},
        schema={"blockNumber": pl.Int64, "tick": pl.Int32, "event_name": pl.String},
    )
    out = attach_in_range(swap_df, vs)
    assert out["vault_in_range"][0] is True
    # tick == upperTick → in-range (closed interval)
    swap_df = pl.DataFrame(
        {"blockNumber": [100], "tick": [20000], "event_name": ["Swap"]},
        schema={"blockNumber": pl.Int64, "tick": pl.Int32, "event_name": pl.String},
    )
    out = attach_in_range(swap_df, vs)
    assert out["vault_in_range"][0] is True
