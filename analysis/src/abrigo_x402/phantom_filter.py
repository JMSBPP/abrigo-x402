"""PANEL-04: Drop Transfer events involving Celo fee-abstraction adapters.

Per Celo's fee-abstraction mechanism (USDC=6 decimals, USDT=6 decimals; cannot
be registered as FeeCurrency directly), adapter contracts wrap them for
18-decimal gas accounting. Transfer events where `from` OR `to` is one of the
two known adapter addresses are gas-payment artifacts — NOT user-meaningful
cashflows — and would inflate the arrival counts that Phase 3 DGP estimation
(NHPP / Hawkes) consumes.

Scope is intentionally narrow per CONTEXT.md / 02-RESEARCH §D:
- Filter applies ONLY to event_name == 'Transfer' rows.
- Swap, Mint, Burn, Deposit, Withdraw events pass through unchanged (even if
  `from` / `to` happen to match an adapter address — those columns are not
  load-bearing for non-Transfer event types).
- User → counterparty Transfer in the same fee-abstraction tx is PRESERVED
  (only the user → adapter gas-leg is removed).
- Address matching is case-insensitive (Blockscout sometimes emits checksummed
  addresses; ADAPTERS is the lowercase canonical form).
- Broader structural heuristic (Transfer-without-paired-Swap-in-same-tx) is
  NOT applied here — deferred to Phase 7 cross-iteration synthesis.

Adapter addresses (verified against Celo fee-abstraction docs + CONTEXT.md):
- USDC_FEE_ADAPTER = 0x2f25deb3848c207fc8e0c34035b3ba7fc157602b
- USDT_FEE_ADAPTER = 0x0e2a3e05bc9a16f5292a6170456a710cb89c6f72
"""
import polars as pl

# Lowercase canonical form for case-insensitive matching.
USDC_FEE_ADAPTER: str = "0x2f25deb3848c207fc8e0c34035b3ba7fc157602b"
USDT_FEE_ADAPTER: str = "0x0e2a3e05bc9a16f5292a6170456a710cb89c6f72"

# Aliases retained for legacy plan-frontmatter naming (PANEL-04 must_haves.artifacts.exports).
USDC_FEE_ABSTRACTION_ADAPTER: str = USDC_FEE_ADAPTER
USDT_FEE_ABSTRACTION_ADAPTER: str = USDT_FEE_ADAPTER

ADAPTERS: frozenset[str] = frozenset([USDC_FEE_ADAPTER, USDT_FEE_ADAPTER])


def exclude_adapters(df: pl.DataFrame) -> pl.DataFrame:
    """Drop Transfer rows where ``from`` ∈ ADAPTERS OR ``to`` ∈ ADAPTERS.

    Non-Transfer rows pass through unchanged. Address comparison is
    case-insensitive against the lowercase canonical ``ADAPTERS`` set.

    Args:
        df: Decoded event DataFrame with at minimum ``event_name``, ``from``,
            ``to`` columns (per Plan 02-02 ``decode_all`` output schema).

    Returns:
        A new DataFrame with adapter-Transfer rows removed. Input is not
        mutated. If the expected columns are absent (e.g., upstream did not
        decode any Transfers), the input is returned unchanged.
    """
    if df.height == 0:
        return df
    required = {"event_name", "from", "to"}
    if not required.issubset(df.columns):
        return df
    adapter_list = list(ADAPTERS)
    return df.filter(
        ~(
            (pl.col("event_name") == "Transfer")
            & (
                pl.col("from").str.to_lowercase().is_in(adapter_list)
                | pl.col("to").str.to_lowercase().is_in(adapter_list)
            )
        )
    )
