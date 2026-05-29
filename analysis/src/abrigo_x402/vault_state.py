"""PANEL-01 vault-state component: read TS sidecar JSONL, compute vault_in_range per Swap.

The TS sidecar (`fetch/src/vault/state-snap.ts`) writes JSONL with one row per
deduplicated block in the panel's Swap-event range. This module reads it as polars,
left-joins on `blockNumber`, and computes
`vault_in_range = (lowerTick <= tick <= upperTick)`.

Conservative semantics: if a Swap has no matching vault-state block (left-join NULL),
`vault_in_range` is False — the vault accrues zero LP-fees for that Swap. Missing
vault state is treated as "no info" → no fee credit, which keeps revenue_leg's
Q96 LP-fee calculation safe against gaps in sidecar coverage.

The TS sidecar's `currentTick` (the vault's notion of pool tick at the snap block)
is renamed to `vault_currentTick` in the joined frame to avoid collision with the
Swap event payload's own `tick` field — that latter is the comparison anchor for
the in-range check (it's per-event, not per-block).

Vault liquidity L (Uniswap V3 virtual liquidity) is computed from the vault's
``totalAmounts_{0,1}`` and tick range via the canonical V3 ``getLiquidityForAmounts``
algorithm (TickMath + LiquidityAmounts ports below). This replaces the Phase-2
``totalSupply`` sentinel — ``totalSupply`` is the vault's share-token issuance
count, NOT a V3 L value, and using it as an L proxy underestimates vault fee
share by ~9 orders of magnitude on real vaults (totalSupply ≪ L typically).

The TickMath port matches Uniswap V3 ``TickMath.getSqrtRatioAtTick`` exactly
(magic constants from the Solidity source; integer-precision, no float64
truncation). The LiquidityAmounts port matches
``LiquidityAmounts.getLiquidityForAmounts`` modulo the uint128 truncation step
(we return the full uint256 since polars Int128 holds it without overflow for
realistic vault sizes).
"""
from __future__ import annotations

import json
from pathlib import Path

import polars as pl

Q96: int = 1 << 96
MAX_TICK: int = 887272
MIN_TICK: int = -887272


def get_sqrt_ratio_at_tick(tick: int) -> int:
    """Port of Uniswap V3 ``TickMath.getSqrtRatioAtTick``.

    Returns the sqrt of the price ratio (token1/token0) at the given tick,
    represented as a Q64.96 fixed-point integer. Exact match to the on-chain
    implementation — uses the same magic constants and bit-shifts.

    Raises ValueError if abs(tick) > MAX_TICK.
    """
    abs_tick = -tick if tick < 0 else tick
    if abs_tick > MAX_TICK:
        raise ValueError(f"tick out of range: {tick}")

    ratio = (
        0xFFFCB933BD6FAD37AA2D162D1A594001
        if (abs_tick & 0x1) != 0
        else 0x100000000000000000000000000000000
    )
    if abs_tick & 0x2:
        ratio = (ratio * 0xFFF97272373D413259A46990580E213A) >> 128
    if abs_tick & 0x4:
        ratio = (ratio * 0xFFF2E50F5F656932EF12357CF3C7FDCC) >> 128
    if abs_tick & 0x8:
        ratio = (ratio * 0xFFE5CACA7E10E4E61C3624EAA0941CD0) >> 128
    if abs_tick & 0x10:
        ratio = (ratio * 0xFFCB9843D60F6159C9DB58835C926644) >> 128
    if abs_tick & 0x20:
        ratio = (ratio * 0xFF973B41FA98C081472E6896DFB254C0) >> 128
    if abs_tick & 0x40:
        ratio = (ratio * 0xFF2EA16466C96A3843EC78B326B52861) >> 128
    if abs_tick & 0x80:
        ratio = (ratio * 0xFE5DEE046A99A2A811C461F1969C3053) >> 128
    if abs_tick & 0x100:
        ratio = (ratio * 0xFCBE86C7900A88AEDCFFC83B479AA3A4) >> 128
    if abs_tick & 0x200:
        ratio = (ratio * 0xF987A7253AC413176F2B074CF7815E54) >> 128
    if abs_tick & 0x400:
        ratio = (ratio * 0xF3392B0822B70005940C7A398E4B70F3) >> 128
    if abs_tick & 0x800:
        ratio = (ratio * 0xE7159475A2C29B7443B29C7FA6E889D9) >> 128
    if abs_tick & 0x1000:
        ratio = (ratio * 0xD097F3BDFD2022B8845AD8F792AA5825) >> 128
    if abs_tick & 0x2000:
        ratio = (ratio * 0xA9F746462D870FDF8A65DC1F90E061E5) >> 128
    if abs_tick & 0x4000:
        ratio = (ratio * 0x70D869A156D2A1B890BB3DF62BAF32F7) >> 128
    if abs_tick & 0x8000:
        ratio = (ratio * 0x31BE135F97D08FD981231505542FCFA6) >> 128
    if abs_tick & 0x10000:
        ratio = (ratio * 0x9AA508B5B7A84E1C677DE54F3E99BC9) >> 128
    if abs_tick & 0x20000:
        ratio = (ratio * 0x5D6AF8DEDB81196699C329225EE604) >> 128
    if abs_tick & 0x40000:
        ratio = (ratio * 0x2216E584F5FA1EA926041BEDFE98) >> 128
    if abs_tick & 0x80000:
        ratio = (ratio * 0x48A170391F7DC42444E8FA2) >> 128

    if tick > 0:
        ratio = ((1 << 256) - 1) // ratio

    sqrt_price_x96 = ratio >> 32
    if ratio & ((1 << 32) - 1):
        sqrt_price_x96 += 1
    return sqrt_price_x96


def _liquidity_for_amount0(sqrt_a: int, sqrt_b: int, amount0: int) -> int:
    if sqrt_a > sqrt_b:
        sqrt_a, sqrt_b = sqrt_b, sqrt_a
    if sqrt_b == sqrt_a:
        return 0
    intermediate = (sqrt_a * sqrt_b) // Q96
    return (amount0 * intermediate) // (sqrt_b - sqrt_a)


def _liquidity_for_amount1(sqrt_a: int, sqrt_b: int, amount1: int) -> int:
    if sqrt_a > sqrt_b:
        sqrt_a, sqrt_b = sqrt_b, sqrt_a
    if sqrt_b == sqrt_a:
        return 0
    return (amount1 * Q96) // (sqrt_b - sqrt_a)


def get_liquidity_for_amounts(
    sqrt_p: int, sqrt_a: int, sqrt_b: int, amount0: int, amount1: int
) -> int:
    """Port of Uniswap V3 ``LiquidityAmounts.getLiquidityForAmounts``.

    Returns the V3 virtual liquidity L for a position spanning [sqrt_a, sqrt_b]
    holding (amount0, amount1) at current price sqrt_p. All sqrt values are
    Q64.96 fixed-point integers.

    When sqrt_p < sqrt_a: position is all token0 → L = liquidity_for_amount0(a,b,amount0)
    When sqrt_p > sqrt_b: position is all token1 → L = liquidity_for_amount1(a,b,amount1)
    Else (in-range): L = min(liquidity_for_amount0(p,b,amount0), liquidity_for_amount1(a,p,amount1))
    """
    if sqrt_a > sqrt_b:
        sqrt_a, sqrt_b = sqrt_b, sqrt_a
    if sqrt_p <= sqrt_a:
        return _liquidity_for_amount0(sqrt_a, sqrt_b, amount0)
    if sqrt_p < sqrt_b:
        l0 = _liquidity_for_amount0(sqrt_p, sqrt_b, amount0)
        l1 = _liquidity_for_amount1(sqrt_a, sqrt_p, amount1)
        return l0 if l0 < l1 else l1
    return _liquidity_for_amount1(sqrt_a, sqrt_b, amount1)


def _compute_vault_liquidity_row(
    amount0: str | None,
    amount1: str | None,
    sqrt_price_x96: str | None,
    lower_tick: int | None,
    upper_tick: int | None,
) -> str:
    """Row-level V3 liquidity computation. Returns decimal-string for polars
    Int128/String round-trip stability. Returns "0" when any input is missing or
    when the math degenerates (zero amounts, equal bounds)."""
    if (
        amount0 is None
        or amount1 is None
        or sqrt_price_x96 is None
        or lower_tick is None
        or upper_tick is None
    ):
        return "0"
    try:
        a0 = int(amount0)
        a1 = int(amount1)
        sp = int(sqrt_price_x96)
        sa = get_sqrt_ratio_at_tick(int(lower_tick))
        sb = get_sqrt_ratio_at_tick(int(upper_tick))
    except (ValueError, TypeError):
        return "0"
    return str(get_liquidity_for_amounts(sp, sa, sb, a0, a1))


def attach_vault_liquidity(df: pl.DataFrame) -> pl.DataFrame:
    """Compute the ``vault_liquidity`` column from V3 math.

    Required inputs: ``totalAmounts_0``, ``totalAmounts_1``, ``sqrtPriceX96``,
    ``lowerTick``, ``upperTick``. The Swap event's ``sqrtPriceX96`` serves as
    the price anchor (post-swap snapshot — within-block drift is negligible for
    fee-share accounting at the cKES/USDT scale).

    Rows missing any input get ``vault_liquidity = "0"``. The downstream
    ``compute_swap_fee`` already gates fee accrual on ``vault_in_range``, so a
    zero vault_liquidity on out-of-range or non-Swap rows is consistent with
    the V3 fee-accrual semantics.
    """
    required = {"totalAmounts_0", "totalAmounts_1", "sqrtPriceX96", "lowerTick", "upperTick"}
    if not required.issubset(df.columns):
        return df.with_columns(pl.lit("0").alias("vault_liquidity"))

    return df.with_columns(
        pl.struct(
            ["totalAmounts_0", "totalAmounts_1", "sqrtPriceX96", "lowerTick", "upperTick"]
        )
        .map_elements(
            lambda s: _compute_vault_liquidity_row(
                s["totalAmounts_0"],
                s["totalAmounts_1"],
                s["sqrtPriceX96"],
                s["lowerTick"],
                s["upperTick"],
            ),
            return_dtype=pl.String,
        )
        .alias("vault_liquidity")
    )

VAULT_STATE_SCHEMA: dict[str, pl.DataType] = {
    "blockNumber": pl.Int64,
    "totalAmounts_0": pl.String,
    "totalAmounts_1": pl.String,
    "totalSupply": pl.String,
    "currentTick": pl.Int32,
    "lowerTick": pl.Int32,
    "upperTick": pl.Int32,
}


def load_vault_state(sidecar_path: Path) -> pl.DataFrame:
    """Read the TS-sidecar-generated JSONL of vault state per block.

    Schema: blockNumber (Int64), totalAmounts_0/1 (String, uint256 decimal),
    totalSupply (String), currentTick (Int32), lowerTick (Int32), upperTick (Int32).
    """
    sidecar_path = Path(sidecar_path)
    rows: list[dict] = []
    with open(sidecar_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return pl.DataFrame(rows, schema=VAULT_STATE_SCHEMA)


def attach_in_range(
    swap_df: pl.DataFrame, vault_state: pl.DataFrame
) -> pl.DataFrame:
    """Left-join vault_state onto swap_df by blockNumber; compute vault_in_range.

    Adds columns: totalAmounts_0, totalAmounts_1, totalSupply, vault_currentTick,
    lowerTick, upperTick, vault_in_range.

    vault_in_range = (lowerTick <= swap.tick <= upperTick) when vault state exists;
    False when vault state is missing for the swap's block (conservative-False
    semantics from the left-join NULL).
    """
    if "blockNumber" not in swap_df.columns:
        raise ValueError("swap_df must have a blockNumber column for the join")
    if "tick" not in swap_df.columns:
        raise ValueError(
            "swap_df must have a tick column for the in-range comparison"
        )

    # Rename vault's currentTick to avoid collision with the Swap event payload's
    # own tick column. The swap-side `tick` is the in-range comparison anchor.
    vd = vault_state.rename({"currentTick": "vault_currentTick"})
    out = swap_df.join(vd, on="blockNumber", how="left")

    # Closed-interval in-range check; null lowerTick/upperTick (no vault state at
    # this block) → conservative False via the is_not_null guard.
    out = out.with_columns(
        (
            pl.col("lowerTick").is_not_null()
            & pl.col("upperTick").is_not_null()
            & (pl.col("lowerTick") <= pl.col("tick"))
            & (pl.col("tick") <= pl.col("upperTick"))
        ).alias("vault_in_range")
    )
    return out
