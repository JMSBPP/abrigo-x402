"""Shared pytest fixtures for Phase 2."""
from pathlib import Path

import polars as pl
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def tmp_panel(tmp_path: Path) -> Path:
    return tmp_path / "panel.parquet"


@pytest.fixture
def synthetic_swap_row_n10() -> pl.DataFrame:
    """10-row synthetic event panel covering edge cases (in-range, out-of-range,
    finality boundary, phantom-paired)."""
    return pl.DataFrame(
        {
            "blockNumber": list(range(67_000_000, 67_000_010)),
            "blockHash": [f"0x{i:064x}" for i in range(10)],
            "logIndex": [0] * 10,
            "txHash": [f"0xtx{i:062x}" for i in range(10)],
            "contractAddress": ["0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F"] * 10,
            "event_name": ["Swap"] * 10,
        }
    )
