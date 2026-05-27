"""Shared pytest fixtures for Phase 2 + Phase 3."""
from pathlib import Path

import numpy as np
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


# === Phase 3 synthetic-data fixtures ===

SYNTHETIC_END_TIME_SECONDS: float = 2_592_000.0  # 30 days


@pytest.fixture(scope="session")
def synthetic_hawkes_eta_05_path() -> Path:
    """Path to the Wave-0-captured Hawkes(eta=0.5) 30-day panel fixture."""
    return Path(__file__).parent / "fixtures" / "synthetic_hawkes_eta_05.parquet"


@pytest.fixture(scope="session")
def synthetic_nhpp_baseline_only_path() -> Path:
    """Path to the Wave-0-captured pure-NHPP (alpha=0) 30-day panel fixture."""
    return Path(__file__).parent / "fixtures" / "synthetic_nhpp_baseline_only.parquet"


@pytest.fixture(scope="session")
def synthetic_hawkes_eta_05_legs(synthetic_hawkes_eta_05_path):
    """Returns (leg_0_times, leg_1_times) as np.ndarray from the Hawkes(eta=0.5) fixture."""
    df = pl.read_parquet(synthetic_hawkes_eta_05_path)
    leg_0 = df.filter(pl.col("leg") == 0).select("event_time").to_numpy().ravel().astype(np.float64)
    leg_1 = df.filter(pl.col("leg") == 1).select("event_time").to_numpy().ravel().astype(np.float64)
    return leg_0, leg_1


@pytest.fixture(scope="session")
def synthetic_nhpp_baseline_only_legs(synthetic_nhpp_baseline_only_path):
    """Returns (leg_0_times, leg_1_times) as np.ndarray from the pure-NHPP fixture."""
    df = pl.read_parquet(synthetic_nhpp_baseline_only_path)
    leg_0 = df.filter(pl.col("leg") == 0).select("event_time").to_numpy().ravel().astype(np.float64)
    leg_1 = df.filter(pl.col("leg") == 1).select("event_time").to_numpy().ravel().astype(np.float64)
    return leg_0, leg_1


@pytest.fixture(scope="session")
def synthetic_end_time() -> float:
    return SYNTHETIC_END_TIME_SECONDS


def make_synthetic_hawkes_fixture(
    adjacency: np.ndarray,
    baseline: np.ndarray,
    decays: float,
    end_time: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Helper: simulate via tick.SimuHawkesExpKernels and return (leg_0_times, leg_1_times)."""
    from tick.hawkes import SimuHawkesExpKernels
    sim = SimuHawkesExpKernels(
        adjacency=adjacency, decays=decays, baseline=baseline,
        end_time=end_time, seed=seed, verbose=False,
    )
    # NEVER set force_simulation=True (Pitfall 9)
    sim.simulate()
    return sim.timestamps[0].astype(np.float64), sim.timestamps[1].astype(np.float64)
