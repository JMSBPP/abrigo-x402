"""Plan 02-03 PANEL-04: tests for exclude_adapters phantom-transfer filter.

Synthetic fixture (phantom_transfer_synthetic.json) is the load-bearing test
input. The real fixture (phantom_transfer_usdt_real.json) is exercised
conditionally — it gracefully skips when `_meta.status == 'no-adapter-traffic-found'`
(the documented Plan 02-00 fallback). When real adapter traffic is eventually
captured, the same test exercises the filter against on-chain payload shape.
"""
import json
import pytest
import polars as pl
from pathlib import Path
from abrigo_x402.phantom_filter import (
    exclude_adapters,
    ADAPTERS,
    USDC_FEE_ADAPTER,
    USDT_FEE_ADAPTER,
)

FIXTURES = Path(__file__).parent / "fixtures"
SYNTHETIC = FIXTURES / "phantom_transfer_synthetic.json"
REAL = FIXTURES / "phantom_transfer_usdt_real.json"

TRANSFER_TOPIC0 = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def _df_from_logs(logs: list[dict]) -> pl.DataFrame:
    """Convert fixture log dicts into the panel-row shape phantom_filter expects."""
    rows = []
    for i, lg in enumerate(logs):
        rows.append({
            "blockNumber": lg.get("blockNumber", 67_000_000),
            "logIndex": lg.get("logIndex", i),
            "event_name": lg.get("event_name", "Unknown"),
            "from": (lg.get("from") or "").lower(),
            "to": (lg.get("to") or "").lower(),
            "value": str(lg.get("value", "0")),
            "contractAddress": (lg.get("address") or "").lower(),
            "txHash": "0xtx",
        })
    return pl.DataFrame(rows, schema_overrides={
        "blockNumber": pl.Int64,
        "logIndex": pl.Int64,
        "event_name": pl.String,
        "from": pl.String,
        "to": pl.String,
        "value": pl.String,
        "contractAddress": pl.String,
        "txHash": pl.String,
    })


def test_adapters_constant_matches_individual_exports():
    assert {USDC_FEE_ADAPTER, USDT_FEE_ADAPTER} == set(ADAPTERS)
    assert USDC_FEE_ADAPTER == "0x2f25deb3848c207fc8e0c34035b3ba7fc157602b"
    assert USDT_FEE_ADAPTER == "0x0e2a3e05bc9a16f5292a6170456a710cb89c6f72"


def test_drops_usdc_adapter_from():
    df = _df_from_logs([
        {"event_name": "Transfer", "from": USDC_FEE_ADAPTER, "to": "0xuser", "value": 1},
    ])
    out = exclude_adapters(df)
    assert out.height == 0


def test_drops_usdt_adapter_to():
    df = _df_from_logs([
        {"event_name": "Transfer", "from": "0xuser", "to": USDT_FEE_ADAPTER, "value": 1},
    ])
    out = exclude_adapters(df)
    assert out.height == 0


def test_drops_usdt_adapter_user_gas_leg():
    df = _df_from_logs([
        {"event_name": "Transfer",
         "from": "0xuser000000000000000000000000000000000001",
         "to": USDT_FEE_ADAPTER, "value": 1000},
    ])
    out = exclude_adapters(df)
    assert out.height == 0


def test_preserves_user_counterparty_transfer():
    df = _df_from_logs([
        {"event_name": "Transfer",
         "from": "0xuser000000000000000000000000000000000001",
         "to": "0xcounterparty00000000000000000000000000000",
         "value": 998000},
    ])
    out = exclude_adapters(df)
    assert out.height == 1
    assert out["to"][0] == "0xcounterparty00000000000000000000000000000"


def test_preserves_swap_event_with_adapter_address():
    """Adapter-address can appear on non-Transfer events; filter scope is Transfer-only."""
    df = _df_from_logs([
        {"event_name": "Swap", "from": USDT_FEE_ADAPTER, "to": USDT_FEE_ADAPTER},
    ])
    out = exclude_adapters(df)
    assert out.height == 1  # Swap passes through even though from/to look adapter-like


def test_preserves_mint_burn_deposit_withdraw():
    df = _df_from_logs([
        {"event_name": "Mint"},
        {"event_name": "Burn"},
        {"event_name": "Deposit"},
        {"event_name": "Withdraw"},
    ])
    out = exclude_adapters(df)
    assert out.height == 4


def test_case_insensitive_matching():
    # Uppercase variant of USDT adapter
    df = _df_from_logs([
        {"event_name": "Transfer",
         "from": "0x0E2A3E05BC9A16F5292A6170456A710CB89C6F72",
         "to": "0xuser"},
    ])
    out = exclude_adapters(df)
    assert out.height == 0


def test_synthetic_fixture_full_roundtrip():
    fx = json.loads(SYNTHETIC.read_text())
    df = _df_from_logs(fx["logs"])
    out = exclude_adapters(df)
    # Per synthetic fixture: 3 logs;
    # log 0 (Swap) + log 2 (user→counterparty Transfer) preserved
    # log 1 (user→USDT_FEE_ADAPTER Transfer) is dropped
    # → 2 rows
    assert out.height == 2
    event_names = set(out["event_name"].to_list())
    assert "Swap" in event_names
    assert "Transfer" in event_names
    # Verify the surviving Transfer is the user→counterparty leg (NOT the adapter leg)
    transfers = out.filter(pl.col("event_name") == "Transfer")
    assert transfers.height == 1
    assert transfers["to"][0] == "0xcounterparty00000000000000000000000000000"


def test_real_fixture_roundtrip_when_captured():
    fx = json.loads(REAL.read_text())
    if fx.get("_meta", {}).get("status") == "no-adapter-traffic-found":
        pytest.skip("Real fixture not captured (Blockscout returned empty per Plan 02-00 fallback)")
    logs = fx.get("logs", [])
    if not logs:
        pytest.skip("Real fixture has empty logs array")
    # Normalize Blockscout v1 getLogs shape to the panel-row shape.
    # ERC-20 Transfer topics: topics[1]=from (32-byte padded), topics[2]=to (32-byte padded).
    normalized = []
    for lg in logs:
        topics = lg.get("topics", []) or []
        topic0 = topics[0] if topics else None
        is_transfer = topic0 == TRANSFER_TOPIC0
        ev = "Transfer" if is_transfer else "Unknown"
        from_addr = "0x" + topics[1][-40:].lower() if len(topics) > 1 and topics[1] else ""
        to_addr = "0x" + topics[2][-40:].lower() if len(topics) > 2 and topics[2] else ""
        normalized.append({"event_name": ev, "from": from_addr, "to": to_addr})
    df = _df_from_logs(normalized)
    in_count = df.height
    out = exclude_adapters(df)
    # Filter MUST drop at least one row (the adapter Transfer we captured).
    assert out.height < in_count, (
        f"phantom filter didn't drop any rows from real fixture (in={in_count}, out={out.height})"
    )


def test_empty_dataframe():
    df = pl.DataFrame(schema={
        "event_name": pl.String,
        "from": pl.String,
        "to": pl.String,
    })
    out = exclude_adapters(df)
    assert out.height == 0


def test_missing_columns_passthrough():
    """If upstream didn't decode Transfers (no `from`/`to` columns), filter is a no-op."""
    df = pl.DataFrame({"event_name": ["Swap", "Mint"]})
    out = exclude_adapters(df)
    assert out.height == 2
