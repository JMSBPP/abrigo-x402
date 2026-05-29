"""PANEL-04: Drop Transfer events involving Celo fee-abstraction adapters.

Celo's CIP-64 mechanism replaced the pre-2024 FeeCurrencyWrapper pattern with
direct ERC-20 fee currencies. When an EOA pays gas in USDT/USDC, the Celo
client emits a Transfer on the underlying token contract from the sender to a
protocol-reserved dispatcher pseudo-address (``0x000…Ce106A5``). The dispatcher
then re-emits Transfers to the FeeHandler, the OP-Stack SequencerFeeVault, and
the block proposer. None of those Transfers represent swap-related cashflows;
all would inflate the arrival counts that Phase 3 DGP estimation consumes.

The pre-CIP-64 FeeCurrencyWrapper addresses (``USDC_FEE_ADAPTER`` /
``USDT_FEE_ADAPTER`` constants below) are retained but confirmed dead via
Blockscout (``has_token_transfers:false`` on the wrapper as of 2026-05-26).

Scope is intentionally narrow per CONTEXT.md / 02-RESEARCH §D:
- Filter applies ONLY to event_name == 'Transfer' rows.
- Swap, Mint, Burn, Deposit, Withdraw events pass through unchanged.
- User → counterparty Transfer in the same fee-abstraction tx is PRESERVED
  (only legs touching an adapter address are removed).
- Address matching is case-insensitive (Blockscout sometimes emits checksummed
  addresses; ADAPTERS is the lowercase canonical form).
- Broader structural heuristic (Transfer-without-paired-Swap-in-same-tx) is
  NOT applied here — deferred to Phase 7 cross-iteration synthesis.

CIP-64 live fee-distribution pseudo-addresses (empirically confirmed):
- CELO_CIP64_DISPATCHER       = 0x000000000000000000000000000000000ce106a5
- CELO_FEE_HANDLER            = 0xcd437749e43a154c07f3553504c68fbfd56b8778
- OP_SEQUENCER_FEE_VAULT      = 0x4200000000000000000000000000000000000011

Retired pre-CIP-64 wrappers (kept for safety; zero Transfer activity):
- USDC_FEE_ADAPTER = 0x2f25deb3848c207fc8e0c34035b3ba7fc157602b
- USDT_FEE_ADAPTER = 0x0e2a3e05bc9a16f5292a6170456a710cb89c6f72
"""
import polars as pl

CELO_CIP64_DISPATCHER: str = "0x000000000000000000000000000000000ce106a5"
CELO_FEE_HANDLER: str = "0xcd437749e43a154c07f3553504c68fbfd56b8778"
OP_SEQUENCER_FEE_VAULT: str = "0x4200000000000000000000000000000000000011"

USDC_FEE_ADAPTER: str = "0x2f25deb3848c207fc8e0c34035b3ba7fc157602b"
USDT_FEE_ADAPTER: str = "0x0e2a3e05bc9a16f5292a6170456a710cb89c6f72"

USDC_FEE_ABSTRACTION_ADAPTER: str = USDC_FEE_ADAPTER
USDT_FEE_ABSTRACTION_ADAPTER: str = USDT_FEE_ADAPTER

ADAPTERS: frozenset[str] = frozenset([
    CELO_CIP64_DISPATCHER,
    CELO_FEE_HANDLER,
    OP_SEQUENCER_FEE_VAULT,
    USDC_FEE_ADAPTER,
    USDT_FEE_ADAPTER,
])


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
