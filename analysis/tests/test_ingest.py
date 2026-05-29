"""PANEL-01: ingest.load_jsonl + apply_finality_cutoff tests."""
from pathlib import Path

import polars as pl
import pytest

from abrigo_x402.ingest import apply_finality_cutoff, load_jsonl

FIXTURES = Path(__file__).parent / "fixtures"
JSONL = FIXTURES / "ichi_anchor_block_67000000_67001000.jsonl"


def test_load_jsonl_row_count():
    df = load_jsonl(JSONL)
    assert df.height == 10
    assert df.null_count().sum_horizontal()[0] == 0


def test_load_jsonl_schema():
    df = load_jsonl(JSONL)
    # blockNumber must be Int64; hex strings parsed
    assert df.schema["blockNumber"] == pl.Int64
    # blockHash, txHash, contractAddress must be String
    for col in ("blockHash", "txHash", "contractAddress"):
        assert df.schema[col] == pl.String, f"{col} schema = {df.schema[col]}"


def test_load_jsonl_hex_block_decoded():
    df = load_jsonl(JSONL)
    # 0x3FED320 = 67_000_000 (decimal); 0x40BF545 = 67_896_645 (decimal)
    assert df["blockNumber"].min() == 67_000_000
    assert df["blockNumber"].max() == 67_896_645


def test_load_jsonl_provenance_columns():
    df = load_jsonl(JSONL)
    for col in ("blockNumber", "blockHash", "logIndex", "txHash", "contractAddress"):
        assert col in df.columns


def test_finality_cutoff_drops_above():
    df = load_jsonl(JSONL)
    out = apply_finality_cutoff(df, forno_head=67_896_653, lag_blocks=120)
    # cutoff = 67896653 - 120 = 67896533; rows at 67896641+ MUST be dropped
    assert out.height == 5
    assert out["blockNumber"].max() <= 67_896_533


def test_finality_cutoff_default_lag():
    df = load_jsonl(JSONL)
    out_default = apply_finality_cutoff(df, forno_head=67_896_653)
    out_explicit = apply_finality_cutoff(df, forno_head=67_896_653, lag_blocks=120)
    assert out_default.equals(out_explicit)


def test_finality_cutoff_empty_input():
    empty = pl.DataFrame({"blockNumber": pl.Series([], dtype=pl.Int64)})
    out = apply_finality_cutoff(empty, forno_head=67_896_653, lag_blocks=120)
    assert out.height == 0


def test_finality_cutoff_monotonic():
    df = load_jsonl(JSONL)
    out = apply_finality_cutoff(df, forno_head=67_896_653, lag_blocks=120)
    assert out.height <= df.height  # cutoff never adds rows


def test_load_jsonl_raises_on_null_blocknumber(tmp_path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text('{"blockNumber":null,"blockHash":"0x1"}\n')
    with pytest.raises((ValueError, AssertionError)):
        load_jsonl(bad)


def test_block_timestamp_present_and_int64():
    """PANEL-01 ext (Phase 04.1): block_timestamp column is materialized as Int64."""
    df = load_jsonl(JSONL)
    assert "block_timestamp" in df.columns
    assert df.schema["block_timestamp"] == pl.Int64
    assert df["block_timestamp"].null_count() == 0


def test_block_timestamp_hex_parse_raises_on_null(tmp_path):
    """PANEL-01 ext (Phase 04.1): null timeStamp in JSONL raises ValueError at the
    upstream `_hex_to_int(None)` raise path (BEFORE DataFrame construction).
    Exercises the FIRST of two defense-in-depth code paths."""
    bad = tmp_path / "bad_timestamp.jsonl"
    bad.write_text('{"blockNumber":"0x1","blockHash":"0x1","transactionHash":"0x1","logIndex":"0x0","address":"0x1","topics":[],"data":"0x","timeStamp":null}\n')
    with pytest.raises(ValueError):
        load_jsonl(bad)


def test_block_timestamp_post_df_null_count_raises(tmp_path, monkeypatch):
    """PANEL-01 ext (Phase 04.1): defense-in-depth — even if `_hex_to_int` is bypassed
    and a null `block_timestamp` slips into the constructed DataFrame, the post-DataFrame
    `df["block_timestamp"].null_count() > 0` guard fires with the exact zero-null-invariant
    error string. Exercises the SECOND defense-in-depth code path (the post-DF guard),
    NOT the upstream `_hex_to_int(None)` raise. Monkeypatches `pl.DataFrame` in the
    ingest module to inject a null cell into the `block_timestamp` column AFTER row-dict
    construction; the post-DF guard MUST fire with the canonical error string."""
    import polars as pl
    from abrigo_x402 import ingest as ingest_mod

    real_df_ctor = pl.DataFrame

    def df_with_injected_null(rows, schema=None, **kwargs):
        df = real_df_ctor(rows, schema=schema, **kwargs)
        if "block_timestamp" in df.columns and df.height > 0:
            new_col = pl.Series(
                "block_timestamp",
                [None] + df["block_timestamp"].to_list()[1:],
                dtype=pl.Int64,
            )
            df = df.with_columns(new_col)
        return df

    monkeypatch.setattr(ingest_mod.pl, "DataFrame", df_with_injected_null)
    with pytest.raises(ValueError, match=r"null block_timestamp in JSONL row .PANEL-01 zero-null invariant."):
        ingest_mod.load_jsonl(JSONL)
