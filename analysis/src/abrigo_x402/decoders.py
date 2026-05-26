"""PANEL-01: ABI-decoders for Uniswap V3 Mint/Burn + ICHI vault Deposit/Withdraw.

Extends the Phase 1 Swap decoder pattern from
fetch/src/decoders/uniswap-v3-swap.ts. Phase 2 keeps decoding in Python
against raw `topics` + `data` hex strings already cached by Phase 1.

Canonical topic0 values for Uniswap V3 events (keccak256 of canonical signature):
  Swap     0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67
  Mint     0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde
  Burn     0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c

ICHI vault topic0 values are populated by Plan 02-02 after computing keccak256
of the canonical signatures from analysis/tests/fixtures/ichi_vault_abi.json.
"""
import polars as pl

UNISWAP_V3_SWAP_TOPIC0 = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
UNISWAP_V3_MINT_TOPIC0 = "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde"
UNISWAP_V3_BURN_TOPIC0 = "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c"

# Populated by Plan 02-02 after ABI fixture is consumed:
ICHI_VAULT_DEPOSIT_TOPIC0 = ""
ICHI_VAULT_WITHDRAW_TOPIC0 = ""


def decode_all(df: pl.DataFrame) -> pl.DataFrame:
    """Decode every row's raw `topics` + `data` into typed payload columns per event_name."""
    raise NotImplementedError("Plan 02-02")
