"""Q96 LP-fee math tests — RESEARCH §A formula verbatim.

Plan 02-05 / PANEL-01.
"""
import polars as pl
from abrigo_x402.revenue_leg import compute_swap_fee

FEE_TIER = 100  # 0.01% for cKES/USDT per protocols/ichi.toml


def _make_swap(
    amount0: int,
    amount1: int,
    liquidity: int,
    vault_in_range: bool = True,
    vault_liquidity: int = 5_000_000_000_000_000_000,
) -> pl.DataFrame:
    return pl.DataFrame({
        "event_name": ["Swap"],
        "amount0": [str(amount0)],
        "amount1": [str(amount1)],
        "liquidity": [str(liquidity)],
        "tick": [12345],
        "vault_in_range": [vault_in_range],
        "vault_liquidity": [str(vault_liquidity)],
        "lowerTick": [10000],
        "upperTick": [20000],
    })


def test_zero_for_one_swap_fee_on_token0():
    df = _make_swap(
        amount0=1_000_000_000_000_000_000,
        amount1=-998_000,
        liquidity=5_000_000_000_000_000_000,
    )
    out = compute_swap_fee(df, fee_tier_bps=FEE_TIER)
    # fee_token0 = 1e18 * 100 / (1e6 - 100) = 100010001000100010 wei (Python int division)
    expected_fee_token0 = (1_000_000_000_000_000_000 * 100) // (1_000_000 - 100)
    assert int(out["fee_token0"][0]) == expected_fee_token0
    assert int(out["fee_token1"][0]) == 0


def test_one_for_zero_swap_fee_on_token1():
    df = _make_swap(
        amount0=-1_000_000_000_000_000_000,
        amount1=2_000_000,
        liquidity=5_000_000_000_000_000_000,
    )
    out = compute_swap_fee(df, fee_tier_bps=FEE_TIER)
    expected_fee_token1 = (2_000_000 * 100) // (1_000_000 - 100)
    assert int(out["fee_token1"][0]) == expected_fee_token1
    assert int(out["fee_token0"][0]) == 0


def test_vault_in_range_half_share():
    df = _make_swap(
        amount0=1_000_000_000_000_000_000,
        amount1=-998_000,
        liquidity=5_000_000_000_000_000_000,
        vault_in_range=True,
        vault_liquidity=2_500_000_000_000_000_000,  # half of swap.liquidity
    )
    out = compute_swap_fee(df, fee_tier_bps=FEE_TIER)
    fee_t0 = int(out["fee_token0"][0])
    vault_fee_t0 = int(out["vault_fee_token0"][0])
    # vault_share = vault_liquidity / swap.liquidity = 0.5
    assert abs(vault_fee_t0 * 2 - fee_t0) <= 1  # within integer-floor rounding


def test_vault_out_of_range_zero_fee():
    df = _make_swap(
        amount0=1_000_000_000_000_000_000,
        amount1=-998_000,
        liquidity=5_000_000_000_000_000_000,
        vault_in_range=False,
    )
    out = compute_swap_fee(df, fee_tier_bps=FEE_TIER)
    assert int(out["vault_fee_token0"][0]) == 0
    assert int(out["vault_fee_token1"][0]) == 0


def test_worked_example_from_research():
    """RESEARCH §A worked example: in-range Swap with full vault-share.

    fee_token0 = 1e18 * 100 / 999900 = 100010001000100010 wei
    vault_fee_token0 = fee_token0 * 5e18 / 5e18 = fee_token0 (full share)
    """
    df = _make_swap(
        amount0=1_000_000_000_000_000_000,
        amount1=-998_000,
        liquidity=5_000_000_000_000_000_000,
        vault_in_range=True,
        vault_liquidity=5_000_000_000_000_000_000,  # FULL share (vault == pool)
    )
    out = compute_swap_fee(df, fee_tier_bps=FEE_TIER)
    assert int(out["fee_token0"][0]) == 100_010_001_000_100_010
    assert int(out["vault_fee_token0"][0]) == int(out["fee_token0"][0])
    assert int(out["vault_fee_token0"][0]) == 100_010_001_000_100_010


def test_zero_input_edge_case():
    # amount0=0, amount1=-5 (no positive input side)
    df = _make_swap(
        amount0=0,
        amount1=-5,
        liquidity=5_000_000_000_000_000_000,
    )
    out = compute_swap_fee(df, fee_tier_bps=FEE_TIER)
    assert int(out["fee_token0"][0]) == 0
    assert int(out["fee_token1"][0]) == 0
    assert int(out["vault_fee_token0"][0]) == 0
    assert int(out["vault_fee_token1"][0]) == 0


def test_zero_swap_liquidity_returns_zero_vault_fee():
    """Defense against div-by-zero if Swap event has liquidity=0 (degenerate)."""
    df = _make_swap(
        amount0=1_000_000_000_000_000_000,
        amount1=-998_000,
        liquidity=0,
        vault_in_range=True,
        vault_liquidity=5_000_000_000_000_000_000,
    )
    out = compute_swap_fee(df, fee_tier_bps=FEE_TIER)
    assert int(out["vault_fee_token0"][0]) == 0
    assert int(out["vault_fee_token1"][0]) == 0
