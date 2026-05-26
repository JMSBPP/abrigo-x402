"""PANEL-04: Drop Transfer events involving Celo fee-abstraction adapters.

Hardcoded exclusion set per ROADMAP. Any Transfer with `from ∈ ADAPTERS` OR
`to ∈ ADAPTERS` is excluded from arrival counts. All other event_names
(Swap, Mint, Burn, Deposit, Withdraw) pass through untouched.

Broader structural heuristic (Transfer-without-paired-Swap-in-same-tx) is
NOT applied here — deferred to Phase 7 cross-iteration synthesis.
"""
import polars as pl

USDC_FEE_ADAPTER = "0x2f25deb3848c207fc8e0c34035b3ba7fc157602b"
USDT_FEE_ADAPTER = "0x0e2a3e05bc9a16f5292a6170456a710cb89c6f72"
ADAPTERS = frozenset([USDC_FEE_ADAPTER, USDT_FEE_ADAPTER])


def exclude_adapters(df: pl.DataFrame) -> pl.DataFrame:
    """Filter out Transfer rows where `from` ∈ ADAPTERS or `to` ∈ ADAPTERS.

    Other event_names (Swap, Mint, Burn, Deposit, Withdraw) pass through.
    """
    raise NotImplementedError("Plan 02-03")
