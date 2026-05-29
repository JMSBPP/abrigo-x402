"""Q96 LP-fee math from raw Uniswap V3 Swap events.

Per UniswapV3Pool.sol L718-719 (verified live via WebFetch 2026-05-26):
    state.feeGrowthGlobalX128 += FullMath.mulDiv(step.feeAmount, FixedPoint128.Q128, state.liquidity)

Direct decomposition (RESEARCH §A — HIGH confidence; verbatim formula):
    step.feeAmount   = abs(swap_input) × fee_tier_bps / (1_000_000 - fee_tier_bps)
    vault_fee_token  = step.feeAmount × (vault_in_range_liquidity / swap.liquidity)

The Swap event emits NET amounts (amount0, amount1); the input side has the POSITIVE
sign (zeroForOne ⇒ amount0 > 0; else amount1 > 0). Recover gross-input via
fee_tier_bps / (1_000_000 - fee_tier_bps) factor — see Pitfall 2 in RESEARCH.

Vault liquidity: ``vault_liquidity`` column is the proper Uniswap V3 virtual
liquidity L, computed upstream by ``vault_state.attach_vault_liquidity`` via
the canonical ``getLiquidityForAmounts(sqrtP, sqrtA, sqrtB, amount0, amount1)``
algorithm. Inputs are taken from the vault's ``totalAmounts_{0,1}`` + tick
range + the Swap event's ``sqrtPriceX96`` (post-swap; within-block drift is
negligible at this pool's scale). The earlier Phase-2 ``totalSupply`` sentinel
was wrong by ~9 orders of magnitude on real vaults and is removed.

Pitfall 6 mitigation: explicit ``Int128`` casts — arithmetic stays in
fixed-width BigInt land, never silently coerced to Float64. Int128 range
(~1.7e38) safely holds ``abs(amount) * fee_tier_bps`` for Uniswap V3
realistic amounts (uint256 input × 1e6 fee_tier → ≤ ~6e25 << 1.7e38).
Decimal[38, 0] is avoided because polars 1.41 does not implement
``floor_div`` on the Decimal dtype.
"""
import polars as pl

Q128: int = 2**128


def compute_swap_fee(df: pl.DataFrame, fee_tier_bps: int) -> pl.DataFrame:
    """Add fee_token0, fee_token1, vault_fee_token0, vault_fee_token1 columns.

    Parameters
    ----------
    df : pl.DataFrame
        Output of ``decoders.decode_all`` + ``vault_state.attach_in_range``.
        Required columns: ``amount0``, ``amount1``, ``liquidity``,
        ``vault_in_range``, ``vault_liquidity`` (all decimal-strings except
        ``vault_in_range`` which is Boolean).
    fee_tier_bps : int
        Pool fee tier in 1/1e6 units (e.g. 100 = 0.01% for cKES/USDT).

    Returns
    -------
    pl.DataFrame
        Input ``df`` with four new String-dtype columns appended:
        ``fee_token0``, ``fee_token1``, ``vault_fee_token0``,
        ``vault_fee_token1``. Decimal-strings (not Float64) so downstream
        aggregation in Plan 02-08 + Plan 03 chooses Int / Decimal arithmetic
        explicitly without silent precision loss (Pitfall 6).

    Notes
    -----
    Encoded verbatim from RESEARCH §A. Out-of-range Swaps
    (``vault_in_range == False``) accrue zero vault_fee_token{0,1}
    regardless of the pool-wide fee amount (canonical ICHI auto-rebalance
    semantics). Degenerate ``swap.liquidity == 0`` also yields zero
    vault_fee — div-by-zero defense.
    """
    fee_factor_num = fee_tier_bps
    fee_factor_den = 1_000_000 - fee_tier_bps

    # Cast text → Int128 for safe fixed-width BigInt arithmetic.
    # (polars 1.41 Decimal[38,0] does not support floor_div; Int128 does.)
    work = df.with_columns(
        pl.col("amount0").cast(pl.Int128).alias("_amt0_i"),
        pl.col("amount1").cast(pl.Int128).alias("_amt1_i"),
        pl.col("liquidity").cast(pl.Int128).alias("_swap_L_i"),
        pl.col("vault_liquidity").cast(pl.Int128).alias("_vault_L_i"),
    )

    # fee_token0: when amount0 > 0 (zeroForOne) → abs(amount0) * fee_tier / (1e6 - fee_tier); else 0
    # fee_token1: when amount1 > 0 (oneForZero) → abs(amount1) * fee_tier / (1e6 - fee_tier); else 0
    zero_i = pl.lit(0, dtype=pl.Int128)
    work = work.with_columns(
        pl.when(pl.col("_amt0_i") > 0)
          .then((pl.col("_amt0_i") * fee_factor_num) // fee_factor_den)
          .otherwise(zero_i)
          .alias("_fee_token0_i"),
        pl.when(pl.col("_amt1_i") > 0)
          .then((pl.col("_amt1_i") * fee_factor_num) // fee_factor_den)
          .otherwise(zero_i)
          .alias("_fee_token1_i"),
    )

    # vault_fee_token{0,1} = fee_token{0,1} * vault_L / swap.L when vault_in_range AND swap.L > 0; else 0
    work = work.with_columns(
        pl.when(pl.col("vault_in_range") & (pl.col("_swap_L_i") > 0))
          .then((pl.col("_fee_token0_i") * pl.col("_vault_L_i")) // pl.col("_swap_L_i"))
          .otherwise(zero_i)
          .alias("_vault_fee_token0_i"),
        pl.when(pl.col("vault_in_range") & (pl.col("_swap_L_i") > 0))
          .then((pl.col("_fee_token1_i") * pl.col("_vault_L_i")) // pl.col("_swap_L_i"))
          .otherwise(zero_i)
          .alias("_vault_fee_token1_i"),
    )

    # Emit as decimal-strings for downstream stability (Pitfall 6)
    out = work.with_columns(
        pl.col("_fee_token0_i").cast(pl.String).alias("fee_token0"),
        pl.col("_fee_token1_i").cast(pl.String).alias("fee_token1"),
        pl.col("_vault_fee_token0_i").cast(pl.String).alias("vault_fee_token0"),
        pl.col("_vault_fee_token1_i").cast(pl.String).alias("vault_fee_token1"),
    ).drop([
        "_amt0_i", "_amt1_i", "_swap_L_i", "_vault_L_i",
        "_fee_token0_i", "_fee_token1_i",
        "_vault_fee_token0_i", "_vault_fee_token1_i",
    ])
    return out
