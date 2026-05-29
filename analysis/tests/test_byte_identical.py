"""SC-5: byte-identical fit_report.json + residuals.parquet across two runs.

Allowed difference: fetchTimestamp (wall-clock) is excluded from the byte-identity check
per ROADMAP SC-5 verbatim: "byte-identically across two runs ... modulo wall-clock fields".

THREAD PINNING (Reality Checker BLOCKER fix):
statsmodels.tsa.api.VAR.select_order is called by nhpp_inar.py for AIC-based lag/bin-width
selection. Under variable BLAS thread count (multi-core CI), AIC values drift in the last
few bits -> different p_star -> different nhpp_inar_params -> byte divergence in fit_report.json.
Pin BLAS / OMP / MKL / OpenBLAS / NumExpr to 1 thread BEFORE the first numpy import
(transitive via run_fit). The os.environ.setdefault block MUST be the first executable code
in the file — once numpy/statsmodels load with a multi-thread BLAS backend, the per-process
thread setting is sticky and resetting env vars later has no effect.

NOTE on subprocess invocation: if any byte-identity test grows to call `run_fit` via a
subprocess CLI (`python -m abrigo_x402.cli fit ...`) instead of in-process, the thread-pinning
env vars MUST be passed via the subprocess `env=` argument — the parent-process
os.environ.setdefault does NOT propagate to a fresh child process unless explicitly forwarded.
Today the test calls `run_fit` in-process so the env-var setdefault above is sufficient; this
note is documentary in case a future revision migrates to subprocess.
"""
# === THREAD PINNING — must run BEFORE any numpy/statsmodels import (transitive via run_fit) ===
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
# === end thread pinning ===

import hashlib
import json

import polars as pl
import pytest

from abrigo_x402.dgp.orchestrator import run_fit


@pytest.fixture
def small_panel_path(tmp_path, synthetic_nhpp_baseline_only_legs):
    leg_0, leg_1 = synthetic_nhpp_baseline_only_legs
    rows = []
    block_offset = 67_378_253
    for t in leg_0[:200]:
        rows.append({
            "block_timestamp": float(t),
            "blockNumber": block_offset + int(t),
            "event_name": "Swap",
            "amount0": "100", "amount1": "-100",
            "txHash": "0x" + "00" * 32, "logIndex": 0,
            "contractAddress": "0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F",
            "blockHash": "0x" + "00" * 32,
        })
    for t in leg_1[:200]:
        rows.append({
            "block_timestamp": float(t),
            "blockNumber": block_offset + int(t) + 1,
            "event_name": "Swap",
            "amount0": "-100", "amount1": "100",
            "txHash": "0x" + "11" * 32, "logIndex": 0,
            "contractAddress": "0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F",
            "blockHash": "0x" + "00" * 32,
        })
    df = pl.DataFrame(rows)
    panel_path = tmp_path / "67378253_67896653.parquet"
    df.write_parquet(panel_path)
    return panel_path


def _scrub_wallclock(d: dict) -> dict:
    out = dict(d)
    out.pop("fetchTimestamp", None)
    return out


def test_deterministic_fit(small_panel_path, tmp_path):
    # Sanity guard: confirm thread pinning is in effect (defensive — if any earlier import in the
    # test session beat us to numpy, this assert still catches the mis-pinned regime).
    assert os.environ.get("OMP_NUM_THREADS") == "1", (
        "OMP_NUM_THREADS not pinned to 1; SC-5 byte-identity will drift under multi-core BLAS"
    )
    assert os.environ.get("MKL_NUM_THREADS") == "1", "MKL_NUM_THREADS not pinned to 1"
    assert os.environ.get("OPENBLAS_NUM_THREADS") == "1", "OPENBLAS_NUM_THREADS not pinned to 1"
    assert os.environ.get("NUMEXPR_NUM_THREADS") == "1", "NUMEXPR_NUM_THREADS not pinned to 1"

    out_dir_a = tmp_path / "run_a"
    out_dir_b = tmp_path / "run_b"

    result_a = run_fit(small_panel_path, out_dir_a, bootstrap_reps=30)
    result_b = run_fit(small_panel_path, out_dir_b, bootstrap_reps=30)

    # SC-5 byte-identity (modulo wall-clock fetchTimestamp)
    json_a = _scrub_wallclock(json.loads(result_a.fit_report_path.read_text()))
    json_b = _scrub_wallclock(json.loads(result_b.fit_report_path.read_text()))
    assert json_a == json_b, "fit_report.json differs across runs (modulo fetchTimestamp)"

    # residuals.parquet must be byte-identical
    bytes_a = result_a.residuals_path.read_bytes()
    bytes_b = result_b.residuals_path.read_bytes()
    assert hashlib.sha256(bytes_a).hexdigest() == hashlib.sha256(bytes_b).hexdigest(), (
        "residuals.parquet bytes differ across runs (SC-5 violation)"
    )


def test_deterministic_run_id(small_panel_path, tmp_path):
    result_a = run_fit(small_panel_path, tmp_path / "a", bootstrap_reps=30)
    result_b = run_fit(small_panel_path, tmp_path / "b", bootstrap_reps=30)
    assert result_a.run_id == result_b.run_id, (
        f"run_id non-deterministic: {result_a.run_id} vs {result_b.run_id}"
    )


def test_different_panel_different_run_id(small_panel_path, tmp_path):
    result_a = run_fit(small_panel_path, tmp_path / "a", bootstrap_reps=30)

    # Perturb the panel by appending one row
    df = pl.read_parquet(small_panel_path)
    extra = df.head(1)
    perturbed = pl.concat([df, extra])
    perturbed_path = tmp_path / "perturbed.parquet"
    perturbed.write_parquet(perturbed_path)
    result_b = run_fit(perturbed_path, tmp_path / "b", bootstrap_reps=30)
    assert result_a.run_id != result_b.run_id, (
        "run_id collision on perturbed panel: dataHash isn't actually included in derivation"
    )
