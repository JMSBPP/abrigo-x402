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


# === Phase 4 fixtures (Wave 0 scaffold) ===

@pytest.fixture
def joint_dist_fixture() -> dict:
    """Minimal valid joint_dist.json dict for provenance + lint tests (Plan 04-03 consumers)."""
    return {
        "chainId": 42220,
        "contractAddress": "0x" + "00" * 20,
        "blockRange": [0, 100],
        "fetchTimestamp": "2026-05-27T00:00:00+00:00",
        "dataHash": "sha256:" + "0" * 64,
        "gitCommit": "0" * 40,
        "run_id": "0" * 12,
        "cross_correlogram": {"lags": [-1, 0, 1], "values": [0.1, 1.0, 0.1]},
        "permutation_null": {"n_reps": 1000, "p_value": 0.5, "max_abs_rho_observed": 0.1},
        "empirical_copula": {
            "family": "gaussian",
            "params": [0.1],
            "bic": -100.0,
            "all_candidates_bic": {
                "gaussian": -100.0, "t": -98.0,
                "clayton": -90.0, "frank": -85.0, "gumbel": -80.0,
            },
        },
        "vine_fallback_used": False,
    }


@pytest.fixture
def gate_report_fixture() -> dict:
    """Minimal valid gate_report.json dict for provenance + lint tests (Plan 04-04 consumers)."""
    return {
        "chainId": 42220,
        "contractAddress": "0x" + "00" * 20,
        "blockRange": [0, 100],
        "fetchTimestamp": "2026-05-27T00:00:00+00:00",
        "dataHash": "sha256:" + "0" * 64,
        "gitCommit": "0" * 40,
        "run_id": "0" * 12,
        "vol_of_vol_gt_zero": {"passed": False, "evidence": {}},
        "positive_skew_fat_tails": {"passed": False, "evidence": {}},
        "hawkes_self_excitation": {"passed": False, "evidence": {}},
        "usdt_depeg_basis_jump": {
            "passed": False,
            "evidence": {
                "source": "literature_range_stipulation",
                "base_triple": {"lambda_J": 0.05, "mu_J": -0.05, "sigma_J": 0.02},
                "sensitivity_fragile": False,
                "sensitivity_summary": {"n_samples": 64, "n_flips": 0, "flip_examples": []},
            },
        },
        "any_condition_passed": False,
    }


@pytest.fixture(params=["null_cost", "null_lr", "null_convex"])
def null_result_fixture_triplet(request) -> Path:
    """Parametrized fixture yielding paths to the three hedge_05_* fixture triplets.

    Each triplet (fit_report.json + gate_report.json + cost_leg_bound.md) forces exactly
    one HEDGE-05 firing condition via decide_firing_condition's sequential decision tree.
    """
    return FIXTURES / f"hedge_05_{request.param}"
