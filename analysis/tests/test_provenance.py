"""PANEL-02 provenance helpers — round-trip + missing-key detection.

Validates polars 1.41 native Parquet-footer metadata API (runtime-probed per
.planning/phases/02-.../02-RESEARCH.md §I): df.write_parquet(path, metadata={...})
and pl.read_parquet_metadata(path) -> dict[str, str].
"""
import polars as pl
import pytest

from abrigo_x402.provenance import (
    REQUIRED_KEYS,
    assert_has_header,
    git_commit_short,
    with_header,
)

VALID_META = {
    "chainId": "42220",
    "contractAddress": "0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F",
    "blockRange": "[60000000,67896653]",
    "fetchTimestamp": "2026-05-26T11:00:00Z",
    "dataHash": "0xabc1234567890",
    "gitCommit": "84dfc4d",
}


def test_with_header_round_trip(tmp_path):
    df = pl.DataFrame({"a": [1, 2, 3]})
    out = with_header(df, tmp_path / "panel.parquet", **VALID_META)
    md = pl.read_parquet_metadata(out)
    for k in REQUIRED_KEYS:
        assert k in md, f"missing required key: {k}"
        assert md[k] == VALID_META[k]


def test_with_header_missing_key_raises(tmp_path):
    df = pl.DataFrame({"a": [1]})
    incomplete = {k: v for k, v in VALID_META.items() if k != "dataHash"}
    with pytest.raises(ValueError, match="dataHash"):
        with_header(df, tmp_path / "panel.parquet", **incomplete)


def test_assert_has_header_pass(tmp_path):
    df = pl.DataFrame({"a": [1]})
    p = with_header(df, tmp_path / "panel.parquet", **VALID_META)
    assert_has_header(p)  # no raise


def test_assert_has_header_fail(tmp_path):
    df = pl.DataFrame({"a": [1]})
    p = tmp_path / "bad.parquet"
    # Write without metadata via raw polars to simulate a non-compliant artifact
    df.write_parquet(p)
    with pytest.raises(AssertionError, match="PANEL-02"):
        assert_has_header(p)


def test_with_header_coerces_to_string(tmp_path):
    df = pl.DataFrame({"a": [1]})
    coerced = {**VALID_META, "chainId": 42220}  # int — must be coerced
    out = with_header(df, tmp_path / "panel.parquet", **coerced)
    md = pl.read_parquet_metadata(out)
    assert md["chainId"] == "42220"


def test_git_commit_short_returns_hex():
    sha = git_commit_short()
    assert len(sha) >= 7
    int(sha, 16)  # raises ValueError if not hex
