"""PANEL-01: ABI-decoders for Uniswap V3 Swap/Mint/Burn + ICHI vault Deposit/Withdraw.

Python-side decode using eth_abi against the raw `topics` + `data` columns
emitted by ingest.load_jsonl. Mirrors the Phase 1 TS decoder pattern in
fetch/src/decoders/uniswap-v3-swap.ts.

Topic0 derivation:
  - Uniswap V3 Swap/Mint/Burn: hardcoded canonical hex (Phase 1 verified;
    verbatim in fetch/src/constants.ts + RESEARCH §D).
  - ICHI vault Deposit/Withdraw: computed at module-load via keccak256 of the
    canonical event signature parsed from analysis/tests/fixtures/ichi_vault_abi.json
    (captured by Plan 02-00). Drift-proof: if a future ICHI vault version emits
    Deposit/Withdraw with different inputs, the module-load computation yields
    a new topic0 and the test_*_topic0_computed_from_abi_fixture tests catch
    paste-and-hope drift loudly.

Numeric encoding: amount fields are emitted as decimal-string (polars String dtype)
to preserve uint256 / int256 precision across the Python ↔ polars boundary.
Plan 02-05 (revenue_leg) casts to Decimal[38,18] as needed for Q96 arithmetic.
"""
from __future__ import annotations

import json as _json
from pathlib import Path
from typing import Any

import polars as pl
from eth_abi import decode as abi_decode
from eth_utils import keccak

# --- Canonical Uniswap V3 topic0s (verified Phase 1; verbatim from fetch/src/constants.ts) ---
SWAP_TOPIC0 = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
MINT_TOPIC0 = "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde"
BURN_TOPIC0 = "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c"
# ERC-20 Transfer (canonical keccak256 of "Transfer(address,address,uint256)") —
# required for PANEL-04 phantom-filter (exclude_adapters expects event_name='Transfer'
# rows carrying `from` + `to` columns). Phase 2 use is narrow: fee-abstraction
# Transfer gas-leg detection. Plan 02-08 Rule-3 integration patch.
TRANSFER_TOPIC0 = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def _compute_topic0_from_abi(abi: list, event_name: str) -> str:
    """Return keccak256(canonical_signature) for the named event in the ABI."""
    for entry in abi:
        if entry.get("type") == "event" and entry.get("name") == event_name:
            inputs = ",".join(inp["type"] for inp in entry.get("inputs", []))
            sig = f"{event_name}({inputs})".encode()
            return "0x" + keccak(sig).hex()
    raise KeyError(f"event {event_name!r} not found in captured ABI")


# Load the captured ICHI vault ABI once at module-load time.
# Path: analysis/src/abrigo_x402/decoders.py -> parents[2] = analysis/
#       so fixture = analysis/tests/fixtures/ichi_vault_abi.json
_ABI_FIXTURE_PATH = (
    Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "ichi_vault_abi.json"
)

with open(_ABI_FIXTURE_PATH, "r") as _f:
    _ABI_RAW = _json.load(_f)
# Capture-time wrap is {"_meta": ..., "abi": [...]}; tolerate plain-list form too.
if isinstance(_ABI_RAW, dict) and "abi" in _ABI_RAW:
    ICHI_VAULT_ABI = _ABI_RAW["abi"]
else:
    ICHI_VAULT_ABI = _ABI_RAW

DEPOSIT_TOPIC0 = _compute_topic0_from_abi(ICHI_VAULT_ABI, "Deposit")
WITHDRAW_TOPIC0 = _compute_topic0_from_abi(ICHI_VAULT_ABI, "Withdraw")


TOPIC0_TO_EVENT: dict[str, str] = {
    SWAP_TOPIC0: "Swap",
    MINT_TOPIC0: "Mint",
    BURN_TOPIC0: "Burn",
    DEPOSIT_TOPIC0: "Deposit",
    WITHDRAW_TOPIC0: "Withdraw",
    TRANSFER_TOPIC0: "Transfer",
}


# --- Low-level helpers ---

def _hex_to_bytes(h: str) -> bytes:
    return bytes.fromhex(h[2:] if h.startswith("0x") else h)


def _topic_to_int(t: str, signed: bool = False, bits: int = 256) -> int:
    """Decode a 32-byte topic into an int. For signed types narrower than 256
    bits (e.g. int24), the value is right-justified in 32 bytes; we read the
    full 256-bit two's complement and re-narrow if it represents a negative
    in the source `bits`-wide type.
    """
    v = int(t, 16)
    if signed:
        # The topic is a 256-bit big-endian word containing the sign-extended value.
        if v >= (1 << 255):
            v -= 1 << 256
    return v


def _topic_to_addr(t: str) -> str:
    """Last 20 bytes of a 32-byte topic, lowercase hex."""
    return "0x" + t[-40:].lower()


# --- Per-event decoders ---

def decode_swap(topics: list[str], data: str) -> dict[str, Any]:
    """Uniswap V3 Swap:
    Swap(address indexed sender, address indexed recipient, int256 amount0,
         int256 amount1, uint160 sqrtPriceX96, uint128 liquidity, int24 tick)
    """
    sender = _topic_to_addr(topics[1])
    recipient = _topic_to_addr(topics[2])
    (amount0, amount1, sqrtPriceX96, liquidity, tick) = abi_decode(
        ["int256", "int256", "uint160", "uint128", "int24"],
        _hex_to_bytes(data),
    )
    return {
        "sender": sender,
        "recipient": recipient,
        "amount0": str(amount0),
        "amount1": str(amount1),
        "sqrtPriceX96": str(sqrtPriceX96),
        "liquidity": str(liquidity),
        "tick": int(tick),
    }


def decode_mint(topics: list[str], data: str) -> dict[str, Any]:
    """Uniswap V3 Mint:
    Mint(address sender, address indexed owner, int24 indexed tickLower,
         int24 indexed tickUpper, uint128 amount, uint256 amount0, uint256 amount1)

    Note: `sender` is NOT indexed (per canonical Uniswap V3 ABI) but appears in data.
    """
    owner = _topic_to_addr(topics[1])
    tickLower = _topic_to_int(topics[2], signed=True)
    tickUpper = _topic_to_int(topics[3], signed=True)
    (sender, amount, amount0, amount1) = abi_decode(
        ["address", "uint128", "uint256", "uint256"],
        _hex_to_bytes(data),
    )
    return {
        "sender": sender,
        "owner": owner,
        "tickLower": int(tickLower),
        "tickUpper": int(tickUpper),
        "amount": str(amount),
        "amount0": str(amount0),
        "amount1": str(amount1),
    }


def decode_burn(topics: list[str], data: str) -> dict[str, Any]:
    """Uniswap V3 Burn:
    Burn(address indexed owner, int24 indexed tickLower, int24 indexed tickUpper,
         uint128 amount, uint256 amount0, uint256 amount1)
    """
    owner = _topic_to_addr(topics[1])
    tickLower = _topic_to_int(topics[2], signed=True)
    tickUpper = _topic_to_int(topics[3], signed=True)
    (amount, amount0, amount1) = abi_decode(
        ["uint128", "uint256", "uint256"],
        _hex_to_bytes(data),
    )
    return {
        "owner": owner,
        "tickLower": int(tickLower),
        "tickUpper": int(tickUpper),
        "amount": str(amount),
        "amount0": str(amount0),
        "amount1": str(amount1),
    }


def decode_deposit(topics: list[str], data: str) -> dict[str, Any]:
    """ICHI vault Deposit (per captured ABI):
    Deposit(address indexed sender, address indexed to,
            uint256 shares, uint256 amount0, uint256 amount1)
    """
    sender = _topic_to_addr(topics[1])
    to = _topic_to_addr(topics[2])
    (shares, amount0, amount1) = abi_decode(
        ["uint256", "uint256", "uint256"],
        _hex_to_bytes(data),
    )
    return {
        "sender": sender,
        "to": to,
        "shares": str(shares),
        "amount0": str(amount0),
        "amount1": str(amount1),
    }


def decode_withdraw(topics: list[str], data: str) -> dict[str, Any]:
    """ICHI vault Withdraw (per captured ABI):
    Withdraw(address indexed sender, address indexed to,
             uint256 shares, uint256 amount0, uint256 amount1)
    """
    sender = _topic_to_addr(topics[1])
    to = _topic_to_addr(topics[2])
    (shares, amount0, amount1) = abi_decode(
        ["uint256", "uint256", "uint256"],
        _hex_to_bytes(data),
    )
    return {
        "sender": sender,
        "to": to,
        "shares": str(shares),
        "amount0": str(amount0),
        "amount1": str(amount1),
    }


def decode_transfer(topics: list[str], data: str) -> dict[str, Any]:
    """ERC-20 Transfer:
    Transfer(address indexed from, address indexed to, uint256 value)

    Required by PANEL-04 phantom_filter.exclude_adapters which expects rows
    carrying `from` + `to` columns to match against the USDC/USDT fee-abstraction
    adapter set. Non-adapter Transfers pass through unchanged.
    """
    sender = _topic_to_addr(topics[1])
    to = _topic_to_addr(topics[2])
    (value,) = abi_decode(["uint256"], _hex_to_bytes(data))
    return {
        "from": sender,
        "to": to,
        "value": str(value),
    }


_DECODER_FUNCS = {
    "Swap": decode_swap,
    "Mint": decode_mint,
    "Burn": decode_burn,
    "Deposit": decode_deposit,
    "Withdraw": decode_withdraw,
    "Transfer": decode_transfer,
}


# --- Top-level decode_all ---

def decode_all(df: pl.DataFrame) -> pl.DataFrame:
    """Decode every row's raw `topics` + `data` into typed payload columns.

    Adds `event_name` from topics[0] via TOPIC0_TO_EVENT lookup; unknown
    topic0 → `event_name='Unknown'` with the row preserved (no silent drop).

    For each known event_name, decodes the payload via the corresponding
    decode_* function and adds the resulting fields as columns. Numeric
    fields are emitted as decimal-strings (polars String dtype) to preserve
    uint256 precision; Plan 02-05 casts to Decimal[38,18] as needed.
    """
    rows = df.to_dicts()
    enriched = []
    for r in rows:
        topics = r.get("topics") or []
        topic0 = topics[0] if topics else ""
        event_name = TOPIC0_TO_EVENT.get(topic0, "Unknown")
        out: dict[str, Any] = dict(r)
        out["event_name"] = event_name
        decoder = _DECODER_FUNCS.get(event_name)
        if decoder is not None:
            try:
                out.update(decoder(topics, r.get("data", "0x")))
            except Exception as e:
                # Surface decode failures explicitly per row but don't raise —
                # Plan 02-08 (acceptance grid) audits decode_error column.
                out["decode_error"] = str(e)
        enriched.append(out)
    return pl.DataFrame(enriched)
