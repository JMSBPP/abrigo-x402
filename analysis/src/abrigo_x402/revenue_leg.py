"""Q96 LP-fee math from raw Uniswap V3 Swap events. Per UniswapV3Pool.sol L718-719.

Direct decomposition (RESEARCH §A):
    vault_fee_in_token = abs(swap_input_amount)
                         * fee_tier_bps / (1_000_000 - fee_tier_bps)
                         * (vault_in_range_liquidity / swap.liquidity)

The Swap event emits NET amounts; recover gross-input via fee_tier/(1e6-fee_tier).
Out-of-range Swaps accrue zero LP-fees to the vault (verified per ICHI's
auto-rebalance mechanics).
"""
import polars as pl


def compute_swap_fee(df: pl.DataFrame, fee_tier_bps: int) -> pl.DataFrame:
    """Add fee_token0, fee_token1, vault_fee_token0, vault_fee_token1 columns."""
    raise NotImplementedError("Plan 02-05")
