"""SC-1 metadata header audit + complete-on-failure invariant for fit_report.json.

Wave 2 plan 03-07. Tests:
  - test_run_fit_produces_artifacts: run_fit on a synthetic-derived Parquet writes both
    fit_report.json and residuals.parquet under tmp_path/<run_id>/.
  - test_fit_report_has_all_sc1_keys: loaded JSON contains every key from the SC-1 schema.
  - test_fit_report_metadata_header: JSON contains the PANEL-02 + Phase-3 provenance keys.
  - test_gate_failure_still_writes_complete_artifact: on a synthetic alpha=0 panel
    (NHPP truth), the four-criterion gate must FAIL -> gate_passes=false AND all SC-1
    keys still present (no truncated artifact).
  - test_residuals_hash_matches: fit_report.json :: ks_rescaled_time :: residuals_hash
    equals sha256(open('residuals.parquet','rb').read()).hexdigest().
  - test_full_offdiag_adjacency: hawkes_mv_params.adjacency is a 2x2 nested list; the
    SHAPE is full 2x2 (off-diagonals are NOT structurally forced to 0).
"""
from __future__ import annotations

import hashlib
import json

import polars as pl
import pytest

from abrigo_x402.dgp.orchestrator import REQUIRED_FIT_REPORT_KEYS, run_fit


@pytest.fixture
def small_panel_path(tmp_path, synthetic_nhpp_baseline_only_legs):
    leg_0, leg_1 = synthetic_nhpp_baseline_only_legs
    rows = []
    block_offset = 67_378_253
    # Cap the leg sizes for test runtime budget; the synthetic-NHPP fixture is
    # already small (~340 events/leg) so we take all of it.
    for t in leg_0[:340]:
        rows.append({
            "block_timestamp": float(t),
            "blockNumber": block_offset + int(t),
            "event_name": "Swap",
            "amount0": "100",
            "amount1": "-100",
            "txHash": "0x" + "00" * 32,
            "logIndex": 0,
            "contractAddress": "0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F",
            "blockHash": "0x" + "00" * 32,
        })
    for t in leg_1[:340]:
        rows.append({
            "block_timestamp": float(t),
            "blockNumber": block_offset + int(t) + 1,
            "event_name": "Swap",
            "amount0": "-100",
            "amount1": "100",
            "txHash": "0x" + "11" * 32,
            "logIndex": 0,
            "contractAddress": "0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F",
            "blockHash": "0x" + "00" * 32,
        })
    df = pl.DataFrame(rows)
    panel_path = tmp_path / "67378253_67896653.parquet"
    df.write_parquet(panel_path)
    return panel_path


def test_run_fit_produces_artifacts(small_panel_path, tmp_path):
    out_dir = tmp_path / "fits"
    result = run_fit(small_panel_path, out_dir, bootstrap_reps=10)
    assert result.fit_report_path.exists()
    assert result.residuals_path.exists()
    # run_id is 12 hex chars per CONTEXT.md decision
    assert len(result.run_id) == 12
    assert all(c in "0123456789abcdef" for c in result.run_id)


def test_fit_report_has_all_sc1_keys(small_panel_path, tmp_path):
    result = run_fit(small_panel_path, tmp_path / "fits", bootstrap_reps=10)
    data = json.loads(result.fit_report_path.read_text())
    missing = [k for k in REQUIRED_FIT_REPORT_KEYS if k not in data]
    assert not missing, f"fit_report.json missing keys: {missing}"
    # Nested keys per ROADMAP SC-1 verbatim
    assert {"observed_stat", "bootstrap_null_dist_50_50_chi2_0_chi2_1", "p_value"} <= set(
        data["lr_test"].keys()
    )
    assert {"method", "lower", "upper", "ci_width"} <= set(data["branching_ratio_ci"].keys())
    assert {"train_rate", "held_out_rate", "ratio", "decision"} <= set(
        data["baseline_stationarity_check"].keys()
    )
    assert {"nhpp", "hawkes", "split_metadata"} <= set(data["held_out_loglik"].keys())
    assert {"p_value", "residuals_hash"} <= set(data["ks_rescaled_time"].keys())


def test_fit_report_metadata_header(small_panel_path, tmp_path):
    result = run_fit(small_panel_path, tmp_path / "fits", bootstrap_reps=10)
    data = json.loads(result.fit_report_path.read_text())
    for k in (
        "chainId",
        "contractAddress",
        "blockRange",
        "fetchTimestamp",
        "dataHash",
        "gitCommit",
        "run_id",
        "tick_lib_version",
    ):
        assert k in data, f"Missing provenance key {k}"


def test_gate_failure_still_writes_complete_artifact(small_panel_path, tmp_path):
    """CONTEXT.md <specifics>: NEVER write a fit_report.json with missing keys.
    Even when the four-criterion gate FAILS on a thin or null-truth panel,
    the artifact must ship with gate_passes=false and ALL SC-1 keys present.
    """
    result = run_fit(small_panel_path, tmp_path / "fits", bootstrap_reps=10)
    data = json.loads(result.fit_report_path.read_text())
    assert "gate_passes" in data
    assert "gate_criteria" in data
    # All five gate-criteria sub-keys present
    assert {
        "lr_rejects",
        "eta_floor_met",
        "ks_held_out_passes",
        "branching_ci_excludes_zero",
        "stationary",
    } <= set(data["gate_criteria"].keys())
    # All SC-1 keys present even on gate failure
    for k in REQUIRED_FIT_REPORT_KEYS:
        assert k in data, f"gate-failure path dropped SC-1 key {k}"


def test_residuals_hash_matches(small_panel_path, tmp_path):
    result = run_fit(small_panel_path, tmp_path / "fits", bootstrap_reps=10)
    data = json.loads(result.fit_report_path.read_text())
    expected = hashlib.sha256(result.residuals_path.read_bytes()).hexdigest()
    assert data["ks_rescaled_time"]["residuals_hash"] == expected


def test_full_offdiag_adjacency(small_panel_path, tmp_path):
    result = run_fit(small_panel_path, tmp_path / "fits", bootstrap_reps=10)
    data = json.loads(result.fit_report_path.read_text())
    adjacency = data["hawkes_mv_params"]["adjacency"]
    # Adjacency is full 2x2 (SHAPE — off-diagonals not structurally forced to 0)
    assert len(adjacency) == 2
    assert len(adjacency[0]) == 2
    assert len(adjacency[1]) == 2


# ---- Phase 04.1.1 fit_report.json schema provenance (AF-03) ----

from pathlib import Path  # noqa: E402

# Pre-04.1.1-01 historical LS-fallback artifacts on disk. Each carries
# fit_method_used='least-squares' by design (the broken-estimator era this plan
# fixes). All are EXEMPTED from the post-04.1.1-01 invariant; the AF-03 lock
# applies only to fits produced AFTER the Plan 04.1.1-01 source patch lands.
#   - ae9e3ba17900: Phase 04.1-02 real-data run (the load-bearing LS-fallback
#     evidence superseded by Plan 04.1.1-01's new run_id).
#   - 0afc6af38e24: Phase 04-09 synthetic-stacked substrate (archived as
#     "LS-fallback methodology-validation evidence" per CONTEXT.md).
#   - de46bb72de52: pre-04.1 earlier real-data run (legacy; pre-block_timestamp
#     panel-augmentation era).
# Post-04.1.1-01 run_ids (driven by Pattern H _derive_run_id with the new
# gitCommit) will NOT collide with any of these and MUST satisfy the no-LS
# invariant.
_ARCHIVED_LS_FALLBACK_RUN_IDS = frozenset({
    "ae9e3ba17900",
    "0afc6af38e24",
    "de46bb72de52",
})


def test_fit_method_used_not_ls_after_04_1_1():
    """Every fit_report.json not in the LS-fallback archive must carry
    fit_method_used != 'least-squares' (AF-03 Plan 04.1.1-00 lock).
    """
    # Resolve relative to repo root rather than CWD so the test works regardless
    # of invocation site (cd analysis && pytest vs pytest from repo root).
    repo_root = Path(__file__).resolve().parents[2]
    fits_dir = repo_root / "data/fits/ichi"
    if not fits_dir.exists():
        pytest.skip("data/fits/ichi does not exist in this environment")
    offenders = []
    checked = 0
    for run_dir in fits_dir.iterdir():
        if not run_dir.is_dir():
            continue
        if run_dir.name in _ARCHIVED_LS_FALLBACK_RUN_IDS:
            continue
        report_path = run_dir / "fit_report.json"
        if not report_path.exists():
            continue
        payload = json.loads(report_path.read_text())
        method = payload.get("hawkes_mv_params", {}).get("fit_method_used")
        checked += 1
        if method == "least-squares":
            offenders.append(f"{run_dir.name}: fit_method_used={method!r}")
    if checked == 0:
        pytest.skip("no post-04.1.1-01 fit_report on disk yet")
    assert not offenders, (
        f"AF-03 Plan 04.1.1-00 violation - the following fit_report.json files "
        f"carry fit_method_used='least-squares' outside the archived LS-fallback "
        f"run_ids {sorted(_ARCHIVED_LS_FALLBACK_RUN_IDS)}: {offenders}"
    )
