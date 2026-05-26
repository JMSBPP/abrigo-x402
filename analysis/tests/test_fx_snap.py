"""Plan 02-06 — Tests for analysis.src.abrigo_x402.fx_snap.

Validates the JSONL sidecar reader, asof-join forward-fill semantics, and
USDT/USD-separate-column non-negotiable from CLAUDE.md.
"""
import json
from pathlib import Path

import polars as pl
import pytest

from abrigo_x402.fx_snap import FX_METHODS, attach_rates, load_fx_sidecar


@pytest.fixture
def fx_jsonl(tmp_path: Path) -> Path:
    rows = [
        {
            "block": 100,
            "source": "mento-broker",
            "rate_x1e18": "129000000000000000000",
            "method": "exact",
            "provenance_url": "https://celo.blockscout.com/block/100",
        },
        {
            "block": 102,
            "source": "mento-broker",
            "rate_x1e18": "0",
            "method": "unavailable",
            "provenance_url": "https://celo.blockscout.com/block/102",
        },
        {
            "block": 110,
            "source": "mento-broker",
            "rate_x1e18": "130000000000000000000",
            "method": "exact",
            "provenance_url": "https://celo.blockscout.com/block/110",
        },
    ]
    p = tmp_path / "fx.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return p


def test_fx_methods_enum():
    """The enum committed for PRE_REGISTRATION before any Phase 3 fit."""
    assert set(FX_METHODS) == {"exact", "forward_fill", "unavailable"}


def test_load_fx_sidecar(fx_jsonl):
    df = load_fx_sidecar(fx_jsonl)
    assert df.height == 3
    assert df.schema["block"] == pl.Int64
    assert df["method"].to_list() == ["exact", "unavailable", "exact"]


def test_attach_rates_exact_match(fx_jsonl):
    fx = load_fx_sidecar(fx_jsonl)
    panel = pl.DataFrame(
        {"blockNumber": [100, 110], "event_name": ["Swap", "Swap"]}
    )
    out = attach_rates(panel, fx)
    methods = out["fx_method"].to_list()
    assert methods == ["exact", "exact"]
    rates = out["cKES_per_USDm_rate"].to_list()
    # Rates correspond to blocks 100 and 110
    assert "129000000000000000000" in rates
    assert "130000000000000000000" in rates


def test_attach_rates_forward_fill(fx_jsonl):
    """Block 105 between exact-rates at 100 and 110 — forward-fills from 100.
    The unavailable row at block 102 is excluded so it does not contaminate
    the fill.
    """
    fx = load_fx_sidecar(fx_jsonl)
    panel = pl.DataFrame({"blockNumber": [105], "event_name": ["Swap"]})
    out = attach_rates(panel, fx)
    assert out["fx_method"][0] == "forward_fill"
    assert out["cKES_per_USDm_rate"][0] == "129000000000000000000"


def test_attach_rates_unavailable_when_before_any_rate(fx_jsonl):
    """Event at block 50 (BEFORE any rate snapshot) → fx_method='unavailable'."""
    fx = load_fx_sidecar(fx_jsonl)
    panel = pl.DataFrame({"blockNumber": [50], "event_name": ["Swap"]})
    out = attach_rates(panel, fx)
    assert out["fx_method"][0] == "unavailable"


def test_usdt_usd_separate_column(fx_jsonl):
    """CLAUDE.md non-negotiable: USDT/USD is a SEPARATE column.

    Default value is '1.0' but explicitly marked method='stipulated' so
    Phase 4 may overwrite with depeg-event data without touching panel
    construction. The column is NEVER absent.
    """
    fx = load_fx_sidecar(fx_jsonl)
    panel = pl.DataFrame({"blockNumber": [100], "event_name": ["Swap"]})
    out = attach_rates(panel, fx)
    assert "usdt_usd_rate" in out.columns
    assert "usdt_usd_method" in out.columns
    assert out["usdt_usd_method"][0] == "stipulated"
    assert out["usdt_usd_rate"][0] == "1.0"


def test_usdt_usd_column_present_for_every_row(fx_jsonl):
    """Even for unavailable / forward-filled rows, usdt_usd_rate is set."""
    fx = load_fx_sidecar(fx_jsonl)
    panel = pl.DataFrame(
        {"blockNumber": [50, 100, 105, 110], "event_name": ["Swap"] * 4}
    )
    out = attach_rates(panel, fx)
    assert out["usdt_usd_rate"].null_count() == 0
    assert out["usdt_usd_method"].null_count() == 0
    # all stipulated in Phase 2 default
    assert set(out["usdt_usd_method"].to_list()) == {"stipulated"}
