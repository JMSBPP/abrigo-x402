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


# -----------------------------------------------------------------------------
# V3 TickMath + getLiquidityForAmounts — Bug-1 fix tests
# -----------------------------------------------------------------------------

from abrigo_x402.vault_state import (
    Q96,
    MAX_TICK,
    MIN_TICK,
    get_sqrt_ratio_at_tick,
    get_liquidity_for_amounts,
    attach_vault_liquidity,
)


def test_get_sqrt_ratio_at_tick_anchors():
    # Anchor: tick=0 → sqrt(1.0) × 2^96 = exactly Q96
    assert get_sqrt_ratio_at_tick(0) == Q96
    # Anchor: tick=MIN_TICK → known V3 constant 4295128739
    assert get_sqrt_ratio_at_tick(MIN_TICK) == 4295128739
    # Anchor: tick=MAX_TICK → known V3 constant
    assert get_sqrt_ratio_at_tick(MAX_TICK) == 1461446703485210103287273052203988822378723970342


def test_get_sqrt_ratio_at_tick_symmetry():
    # sqrt(p(t)) × sqrt(p(-t)) ≈ Q96 (since p(t) × p(-t) = 1)
    for t in (1, 100, 10_000, 100_000, 324_987):
        s_pos = get_sqrt_ratio_at_tick(t)
        s_neg = get_sqrt_ratio_at_tick(-t)
        product = (s_pos * s_neg) // Q96
        # Within 1 part in 1e10 of Q96 (rounding-bound)
        assert abs(product - Q96) / Q96 < 1e-10


def test_get_sqrt_ratio_at_tick_out_of_range():
    with pytest.raises(ValueError):
        get_sqrt_ratio_at_tick(MAX_TICK + 1)
    with pytest.raises(ValueError):
        get_sqrt_ratio_at_tick(MIN_TICK - 1)


def test_get_liquidity_for_amounts_in_range_min_branch():
    # Symmetric case: sqrt_p halfway between sqrt_a and sqrt_b (in ratio space)
    # with amount0 large and amount1 small → L should be determined by amount1.
    sqrt_a = get_sqrt_ratio_at_tick(-1000)
    sqrt_b = get_sqrt_ratio_at_tick(1000)
    sqrt_p = get_sqrt_ratio_at_tick(0)  # midpoint
    L = get_liquidity_for_amounts(sqrt_p, sqrt_a, sqrt_b, amount0=10**30, amount1=10**6)
    # L should equal liquidity_for_amount1(sqrt_a, sqrt_p, 10^6) because that's the binding side
    expected_L1 = (10**6 * Q96) // (sqrt_p - sqrt_a)
    assert L == expected_L1


def test_get_liquidity_for_amounts_all_token0_below_range():
    sqrt_a = get_sqrt_ratio_at_tick(-1000)
    sqrt_b = get_sqrt_ratio_at_tick(1000)
    sqrt_p = get_sqrt_ratio_at_tick(-2000)  # below lower
    # amount1 should be ignored; L derived from amount0 alone over [sqrt_a, sqrt_b]
    L = get_liquidity_for_amounts(sqrt_p, sqrt_a, sqrt_b, amount0=10**18, amount1=0)
    intermediate = (sqrt_a * sqrt_b) // Q96
    expected = (10**18 * intermediate) // (sqrt_b - sqrt_a)
    assert L == expected


def test_get_liquidity_for_amounts_all_token1_above_range():
    sqrt_a = get_sqrt_ratio_at_tick(-1000)
    sqrt_b = get_sqrt_ratio_at_tick(1000)
    sqrt_p = get_sqrt_ratio_at_tick(2000)  # above upper
    L = get_liquidity_for_amounts(sqrt_p, sqrt_a, sqrt_b, amount0=0, amount1=10**18)
    expected = (10**18 * Q96) // (sqrt_b - sqrt_a)
    assert L == expected


def test_get_liquidity_for_amounts_zero_amounts():
    sqrt_a = get_sqrt_ratio_at_tick(-1000)
    sqrt_b = get_sqrt_ratio_at_tick(1000)
    sqrt_p = get_sqrt_ratio_at_tick(0)
    assert get_liquidity_for_amounts(sqrt_p, sqrt_a, sqrt_b, 0, 0) == 0


def test_attach_vault_liquidity_real_vault_values():
    """Real cKES/USDT vault values from materialized panel (block 67,382,070).

    Bug-1 regression: prior `vault_liquidity = totalSupply` produced
    L ≈ 5.85e10 (= 58.5B share tokens) — meaningless as a V3 L. The proper
    computation must produce an L commensurate with the pool's swap.liquidity
    (~4.87e19), so the vault_L / pool_L ratio reflects actual fee share, not
    a 9-order-of-magnitude error.
    """
    df = pl.DataFrame({
        "totalAmounts_0": ["3471972750244298049277479"],  # ~3.47M cKES wei
        "totalAmounts_1": ["30221215163"],                # ~30k USDT wei
        "sqrtPriceX96": ["6951915929841657563186"],      # pool sqrt at swap
        "lowerTick": [-887272],                           # MIN_TICK
        "upperTick": [-324987],
    }, schema={
        "totalAmounts_0": pl.String,
        "totalAmounts_1": pl.String,
        "sqrtPriceX96": pl.String,
        "lowerTick": pl.Int32,
        "upperTick": pl.Int32,
    })
    out = attach_vault_liquidity(df)
    L = int(out["vault_liquidity"][0])
    # L must be > 10^11 (way larger than totalSupply 5.85e10) and < pool L (4.87e19)
    assert L > 10**11, f"vault_L {L} suspiciously small — bug-1 not fixed"
    assert L < 5 * 10**19, f"vault_L {L} larger than pool L — math broken"


def test_attach_vault_liquidity_missing_inputs_emits_zero():
    df = pl.DataFrame({
        "totalAmounts_0": [None],
        "totalAmounts_1": [None],
        "sqrtPriceX96": [None],
        "lowerTick": [None],
        "upperTick": [None],
    }, schema={
        "totalAmounts_0": pl.String,
        "totalAmounts_1": pl.String,
        "sqrtPriceX96": pl.String,
        "lowerTick": pl.Int32,
        "upperTick": pl.Int32,
    })
    out = attach_vault_liquidity(df)
    assert out["vault_liquidity"][0] == "0"


def test_attach_vault_liquidity_passthrough_when_columns_missing():
    df = pl.DataFrame({"x": [1, 2, 3]})
    out = attach_vault_liquidity(df)
    assert "vault_liquidity" in out.columns
    assert out["vault_liquidity"].to_list() == ["0", "0", "0"]
