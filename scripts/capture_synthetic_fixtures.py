"""Wave 0 capture script: generate two locked synthetic-data fixtures via tick.SimuHawkesExpKernels.

Both fixtures are 30-day panels (2,592,000 seconds) with deterministic seeds. The fixture binaries are
committed to analysis/tests/fixtures/ so Wave 1 tests load them without re-simulating.
"""
from __future__ import annotations
import json
import hashlib
from pathlib import Path

import numpy as np
import polars as pl
from tick.hawkes import SimuHawkesExpKernels

END_TIME_SECONDS = 2_592_000.0  # 30 days
DECAYS = 0.1

# Fixture 1: Hawkes with eta = 0.5 (clear positive case for power tests)
# Symmetric alpha = 0.025 in each cell so spectral radius = 0.025 * 2 / 0.1 = 0.5
HAWKES_ADJACENCY = np.array([[0.025, 0.025], [0.025, 0.025]], dtype=np.float64)
HAWKES_BASELINE = np.array([0.00013, 0.00013], dtype=np.float64)  # ~390 events/leg/30d (close to real panel)
HAWKES_SEED = 20260526

# Fixture 2: Pure NHPP (alpha = 0 -> bivariate Poisson with rate=baseline)
NHPP_ADJACENCY = np.zeros((2, 2), dtype=np.float64)
NHPP_BASELINE = np.array([0.00013, 0.00013], dtype=np.float64)  # same baseline as Hawkes for power-vs-size comparability
NHPP_SEED = 20260526 + 1


def _simulate_and_write(adjacency, baseline, decays, end_time, seed, out_path: Path):
    sim = SimuHawkesExpKernels(
        adjacency=adjacency,
        decays=decays,
        baseline=baseline,
        end_time=end_time,
        seed=seed,
        verbose=False,
    )
    # NEVER force_simulation=True (Pitfall 9 -- silently allows non-stationary draws)
    sim.simulate()
    leg_0 = sim.timestamps[0].astype(np.float64)
    leg_1 = sim.timestamps[1].astype(np.float64)
    df = pl.concat([
        pl.DataFrame({"leg": [0] * len(leg_0), "event_time": leg_0}),
        pl.DataFrame({"leg": [1] * len(leg_1), "event_time": leg_1}),
    ])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out_path)
    sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
    return {"path": str(out_path), "n_leg_0": int(leg_0.size), "n_leg_1": int(leg_1.size), "sha256": sha}


def main():
    here = Path(__file__).resolve().parent.parent
    fixtures_dir = here / "analysis" / "tests" / "fixtures"

    hawkes_meta = _simulate_and_write(
        HAWKES_ADJACENCY, HAWKES_BASELINE, DECAYS, END_TIME_SECONDS, HAWKES_SEED,
        fixtures_dir / "synthetic_hawkes_eta_05.parquet",
    )
    nhpp_meta = _simulate_and_write(
        NHPP_ADJACENCY, NHPP_BASELINE, DECAYS, END_TIME_SECONDS, NHPP_SEED,
        fixtures_dir / "synthetic_nhpp_baseline_only.parquet",
    )

    manifest = {
        "synthetic_hawkes_eta_05": {
            "adjacency": HAWKES_ADJACENCY.tolist(),
            "baseline": HAWKES_BASELINE.tolist(),
            "decays": DECAYS,
            "end_time_seconds": END_TIME_SECONDS,
            "seed": HAWKES_SEED,
            "expected_branching_ratio": 0.5,
            **hawkes_meta,
        },
        "synthetic_nhpp_baseline_only": {
            "adjacency": NHPP_ADJACENCY.tolist(),
            "baseline": NHPP_BASELINE.tolist(),
            "decays": DECAYS,
            "end_time_seconds": END_TIME_SECONDS,
            "seed": NHPP_SEED,
            "expected_branching_ratio": 0.0,
            **nhpp_meta,
        },
        "capture_phase": "03-00",
        "tick_version": "0.8.0.2",
        "polars_version": "1.41.0",
    }
    (fixtures_dir / "synthetic_fixtures_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
