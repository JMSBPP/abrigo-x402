"""Plan 02-02 — PANEL-01 decoder tests.

Covers Uniswap V3 Swap/Mint/Burn + ICHI vault Deposit/Withdraw decoding via
`decode_all`. Includes drift-proof bulwark tests that re-compute DEPOSIT_TOPIC0
and WITHDRAW_TOPIC0 from the captured ABI fixture and assert the module-load
values match (so a future ICHI vault version with different event signatures
breaks loudly, not silently).
"""
import polars as pl
from eth_utils import keccak

from abrigo_x402.decoders import (
    decode_all,
    TOPIC0_TO_EVENT,
    SWAP_TOPIC0,
    MINT_TOPIC0,
    BURN_TOPIC0,
    DEPOSIT_TOPIC0,
    WITHDRAW_TOPIC0,
    ICHI_VAULT_ABI,
)


def _make_row(topic0: str, topics_tail: list[str], data: str) -> dict:
    return {
        "blockNumber": 67_000_000,
        "blockHash": "0xaa",
        "logIndex": 0,
        "txHash": "0xtx",
        "contractAddress": "0x61ef8708fc240dc7f9f2c0d81c3124df2fd8829f",
        "topics": [topic0] + topics_tail,
        "data": data,
    }


def test_topic0_registry_complete():
    """All 5 Phase-2 event topic0s are registered."""
    expected = {SWAP_TOPIC0, MINT_TOPIC0, BURN_TOPIC0, DEPOSIT_TOPIC0, WITHDRAW_TOPIC0}
    assert expected.issubset(TOPIC0_TO_EVENT.keys())
    assert set(TOPIC0_TO_EVENT.values()) >= {"Swap", "Mint", "Burn", "Deposit", "Withdraw"}


def test_decode_all_event_name_swap():
    """Swap row gets event_name='Swap' and payload columns (amount0, amount1, tick)."""
    df = pl.DataFrame([_make_row(
        SWAP_TOPIC0,
        # sender, recipient (indexed addresses)
        ["0x" + "0" * 24 + "11" * 20, "0x" + "0" * 24 + "22" * 20],
        # data: amount0(int256)=1e18, amount1(int256)=-998000 (two's complement),
        # sqrtPriceX96(uint160)=1<<96, liquidity(uint128)=5e18, tick(int24)=12345
        "0x"
        + format(1_000_000_000_000_000_000, "064x")
        + format((1 << 256) - 998_000, "064x")  # -998000 two's-complement
        + format(1 << 96, "064x")
        + format(5_000_000_000_000_000_000, "064x")
        + format(12_345, "064x"),
    )])
    out = decode_all(df)
    assert out["event_name"][0] == "Swap"
    assert "amount0" in out.columns
    assert "amount1" in out.columns
    assert "tick" in out.columns
    # Hand-crafted round-trip: amount0 = 1e18, amount1 = -998000, tick = 12345
    assert out["amount0"][0] == str(1_000_000_000_000_000_000)
    assert out["amount1"][0] == str(-998_000)
    assert out["tick"][0] == 12_345


def test_decode_all_event_name_mint():
    """Mint row gets typed payload + indexed-topic decoding (tickLower/tickUpper)."""
    df = pl.DataFrame([_make_row(
        MINT_TOPIC0,
        # owner (indexed), tickLower (indexed int24), tickUpper (indexed int24)
        ["0x" + "0" * 24 + "33" * 20, "0x" + format(100, "064x"), "0x" + format(200, "064x")],
        # data: sender(address)=0x44..44, amount(uint128)=1e18, amount0(uint256)=1e18, amount1(uint256)=2e18
        "0x"
        + "0" * 24 + "44" * 20
        + format(1_000_000_000_000_000_000, "064x")
        + format(1_000_000_000_000_000_000, "064x")
        + format(2_000_000_000_000_000_000, "064x"),
    )])
    out = decode_all(df)
    assert out["event_name"][0] == "Mint"
    assert out["tickLower"][0] == 100
    assert out["tickUpper"][0] == 200
    assert out["amount0"][0] == str(1_000_000_000_000_000_000)
    assert out["amount1"][0] == str(2_000_000_000_000_000_000)


def test_decode_all_event_name_burn():
    """Burn row mirrors Mint structure but with no `sender` in data (owner is indexed)."""
    df = pl.DataFrame([_make_row(
        BURN_TOPIC0,
        # owner (indexed), tickLower (indexed int24), tickUpper (indexed int24)
        ["0x" + "0" * 24 + "55" * 20, "0x" + format(300, "064x"), "0x" + format(400, "064x")],
        # data: amount(uint128)=2e18, amount0(uint256)=2e18, amount1(uint256)=3e18
        "0x"
        + format(2_000_000_000_000_000_000, "064x")
        + format(2_000_000_000_000_000_000, "064x")
        + format(3_000_000_000_000_000_000, "064x"),
    )])
    out = decode_all(df)
    assert out["event_name"][0] == "Burn"
    assert out["tickLower"][0] == 300
    assert out["tickUpper"][0] == 400
    assert out["amount0"][0] == str(2_000_000_000_000_000_000)


def test_decode_all_event_name_deposit():
    """ICHI Deposit row: sender + to indexed; shares/amount0/amount1 in data."""
    df = pl.DataFrame([_make_row(
        DEPOSIT_TOPIC0,
        ["0x" + "0" * 24 + "66" * 20, "0x" + "0" * 24 + "77" * 20],
        "0x"
        + format(10_000_000_000_000_000_000, "064x")  # shares=1e19
        + format(1_000_000_000_000_000_000, "064x")   # amount0=1e18
        + format(5_000_000, "064x"),                  # amount1=5e6 (USDT 6-dec)
    )])
    out = decode_all(df)
    assert out["event_name"][0] == "Deposit"
    assert out["shares"][0] == str(10_000_000_000_000_000_000)
    assert out["amount0"][0] == str(1_000_000_000_000_000_000)
    assert out["amount1"][0] == str(5_000_000)


def test_decode_all_event_name_withdraw():
    """ICHI Withdraw mirrors Deposit shape."""
    df = pl.DataFrame([_make_row(
        WITHDRAW_TOPIC0,
        ["0x" + "0" * 24 + "88" * 20, "0x" + "0" * 24 + "99" * 20],
        "0x"
        + format(5_000_000_000_000_000_000, "064x")
        + format(500_000_000_000_000_000, "064x")
        + format(2_500_000, "064x"),
    )])
    out = decode_all(df)
    assert out["event_name"][0] == "Withdraw"
    assert out["shares"][0] == str(5_000_000_000_000_000_000)


def test_decode_all_unknown_topic_preserves_row():
    """Unknown topic0 → event_name='Unknown'; row preserved (no silent drop, no raise)."""
    df = pl.DataFrame([_make_row("0x" + "ff" * 32, [], "0x00")])
    out = decode_all(df)
    assert out.height == 1
    assert out["event_name"][0] == "Unknown"


def test_decode_all_mixed_events():
    """A mix of Swap/Mint/Burn rows all decode in one decode_all call."""
    df = pl.DataFrame([
        _make_row(
            SWAP_TOPIC0,
            ["0x" + "0" * 24 + "11" * 20, "0x" + "0" * 24 + "22" * 20],
            "0x"
            + format(1, "064x")
            + format(1, "064x")
            + format(1, "064x")
            + format(1, "064x")
            + format(1, "064x"),
        ),
        _make_row(
            MINT_TOPIC0,
            ["0x" + "0" * 24 + "33" * 20, "0x" + format(1, "064x"), "0x" + format(2, "064x")],
            "0x"
            + "0" * 24 + "44" * 20
            + format(1, "064x") * 3,
        ),
        _make_row(
            BURN_TOPIC0,
            ["0x" + "0" * 24 + "55" * 20, "0x" + format(3, "064x"), "0x" + format(4, "064x")],
            "0x" + format(1, "064x") * 3,
        ),
    ])
    out = decode_all(df)
    assert out["event_name"].to_list() == ["Swap", "Mint", "Burn"]


# --- M7 drift-proof bulwark: topic0 computed from captured ABI ---


def test_deposit_topic0_computed_from_abi_fixture():
    """DEPOSIT_TOPIC0 == keccak256 of canonical signature parsed from the captured ABI.

    If a future ICHI vault version emits Deposit with different inputs, the module-load
    computation will yield a new topic0 — this test catches paste-and-hope drift.
    """
    deposit_event = next(
        e for e in ICHI_VAULT_ABI
        if e.get("type") == "event" and e.get("name") == "Deposit"
    )
    inputs = ",".join(inp["type"] for inp in deposit_event["inputs"])
    sig = f"Deposit({inputs})".encode()
    expected = "0x" + keccak(sig).hex()
    assert DEPOSIT_TOPIC0 == expected, (
        f"DEPOSIT_TOPIC0 drift: module value {DEPOSIT_TOPIC0} != "
        f"keccak256({sig.decode()!r}) = {expected}"
    )


def test_withdraw_topic0_computed_from_abi_fixture():
    """Mirror bulwark test for Withdraw."""
    withdraw_event = next(
        e for e in ICHI_VAULT_ABI
        if e.get("type") == "event" and e.get("name") == "Withdraw"
    )
    inputs = ",".join(inp["type"] for inp in withdraw_event["inputs"])
    sig = f"Withdraw({inputs})".encode()
    expected = "0x" + keccak(sig).hex()
    assert WITHDRAW_TOPIC0 == expected
