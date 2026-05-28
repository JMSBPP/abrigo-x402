"""Top-level Phase 3 fit pipeline (Wave 2, DGP-07).

Integrates every Wave-1 module (DGP-01..DGP-06) into a single deterministic invocation
and emits the SC-1 metadata-wrapped `fit_report.json` + `residuals.parquet` pair under
`data/fits/<protocol>/<run_id>/`.

LOCKED INVARIANTS:

- `run_id = sha256(panel_dataHash + fit_code_gitCommit + tick_lib_version)[:12]`
  (CONTEXT.md `<decisions>` -> "`<run_id>` path scheme"). Deterministic.

- `fit_report.json` carries the PANEL-02 metadata header at top level: chainId,
  contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit, plus the
  Phase-3 provenance keys run_id + tick_lib_version (SC-1 verbatim).

- ALL SC-1 keys present even when the four-criterion gate FAILS
  (CONTEXT.md `<specifics>`: "NEVER write a fit_report.json with missing keys").

- residuals.parquet sidecar written via `build_residuals_dataframe`; the JSON
  records `residuals_hash = sha256(residuals.parquet bytes)`.

- Hawkes / NHPP log-likelihoods are canonicalized via the closed-form Hawkes LL
  in `lr_test.py` (`_hawkes_loglik_vectorized` + `_nhpp_pointprocess_loglik`).
  Both `nhpp_inar_params['loglik_in_sample']` (statsmodels VAR.llf, Gaussian on
  bin counts) and `hawkes_mv_params['loglik_in_sample']` (tick.score() under
  the LS fallback documented in 03-02) are NOT on the continuous-time point-
  process probability space and therefore are unsuitable for the SC-1
  `loglik` field. The orchestrator overrides both with the canonical closed-
  form values; `input_diagnostics.hawkes_loglik_source` records the canonical
  function name for audit-trail clarity.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import tick

from abrigo_x402.dgp.held_out import (
    HELD_OUT_FRACTION_DEFAULT,
    compute_held_out_loglik_hawkes,
    compute_held_out_loglik_nhpp,
    wall_clock_split,
)
from abrigo_x402.dgp.hawkes_fit import fit_hawkes_expkern
from abrigo_x402.dgp.lr_test import (
    PRODUCTION_N_REPS,
    _hawkes_loglik_vectorized,
    _nhpp_baseline_per_sec,
    _nhpp_pointprocess_loglik,
    parametric_bootstrap_lr,
)
from abrigo_x402.dgp.nhpp_inar import fit_nhpp_inar
from abrigo_x402.dgp.profile_likelihood import profile_likelihood_eta_ci
from abrigo_x402.dgp.stationarity import baseline_stationarity_check
from abrigo_x402.dgp.time_rescaling import (
    build_residuals_dataframe,
    time_rescaling_ks_test_leg,
)


# SC-1 verbatim — fit_report.json top-level required keys. Mirror in
# scripts/lint_artifacts.py FIT_REPORT_REQUIRED_KEYS (kept in sync manually).
REQUIRED_FIT_REPORT_KEYS: tuple[str, ...] = (
    "chainId",
    "contractAddress",
    "blockRange",
    "fetchTimestamp",
    "dataHash",
    "gitCommit",
    "run_id",
    "tick_lib_version",
    "nhpp_inar_params",
    "hawkes_mv_params",
    "lr_test",
    "ks_rescaled_time",
    "held_out_loglik",
    "branching_ratio_ci",
    "baseline_stationarity_check",
    "input_diagnostics",
    "gate_passes",
    "gate_criteria",
)

# Four-criterion gate thresholds (PRE_REGISTRATION lock).
ETA_FLOOR: float = 0.2
LR_ALPHA: float = 0.01
KS_ALPHA: float = 0.05

# Default chain + contract for the cKES/USDT ICHI pool. Phase 3 v1 fits only this
# pool; multi-pool support is deferred to v2. Overridable via run_fit kwargs.
_DEFAULT_CHAIN_ID: int = 42220
_DEFAULT_CONTRACT: str = "0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F"


def _git_commit() -> str:
    """Current HEAD as 40-hex-char SHA, or 'unknown' if git unavailable."""
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


def _derive_run_id(panel_data_hash: str, git_commit: str, tick_version: str) -> str:
    """run_id = sha256(panel_dataHash + fit_code_gitCommit + tick_lib_version)[:12].

    Locked by CONTEXT.md `<decisions>` -> "`<run_id>` path scheme". Deterministic so
    same panel + same code -> same run_id. Different code or panel -> different run_id.
    """
    h = hashlib.sha256(
        (str(panel_data_hash) + str(git_commit) + str(tick_version)).encode("utf-8")
    ).hexdigest()
    return h[:12]


def _extract_legs_from_panel(
    panel_df: pl.DataFrame,
) -> tuple[np.ndarray, np.ndarray, float, float]:
    """Project the Phase-2 panel onto leg_0 / leg_1 timestamp arrays.

    leg_0 = token0-inflow Swaps (amount0 > 0; token0 entering pool).
    leg_1 = token1-inflow Swaps (amount1 > 0; token1 entering pool).
    Per CONTEXT.md `<decisions>` -> "Bivariate leg definition".
    """
    swaps = panel_df.filter(pl.col("event_name") == "Swap")
    if "block_timestamp" not in swaps.columns:
        raise KeyError(
            "panel parquet lacks 'block_timestamp' column required for DGP fit"
        )
    # Phase 2 panel stores amount0/amount1 as String (decimal-int); cast via Int128.
    amount0_int = swaps.get_column("amount0").cast(pl.Int128)
    amount1_int = swaps.get_column("amount1").cast(pl.Int128)
    ts = swaps.get_column("block_timestamp").cast(pl.Float64).to_numpy()
    leg_0_mask = amount0_int.gt(0).to_numpy()
    leg_1_mask = amount1_int.gt(0).to_numpy()
    leg_0 = np.sort(ts[leg_0_mask]).astype(np.float64)
    leg_1 = np.sort(ts[leg_1_mask]).astype(np.float64)
    if leg_0.size == 0 and leg_1.size == 0:
        raise ValueError("panel produced zero events on both legs")
    window_start = float(ts.min())
    window_end = float(ts.max())
    return leg_0, leg_1, window_start, window_end


def _compute_data_hash(panel_path: Path) -> str:
    """sha256 over the Parquet bytes — the canonical Phase-3 panel dataHash."""
    return hashlib.sha256(panel_path.read_bytes()).hexdigest()


def _panel_provenance(
    panel_path: Path,
    chain_id: int,
    contract_address: str,
) -> dict[str, Any]:
    """Build the PANEL-02 metadata header for this fit run.

    blockRange is inferred from the Parquet filename `<from>_<to>.parquet`
    (Phase-2 convention); on parse failure it falls back to [0, 0] so the
    artifact still ships with all keys present.
    """
    stem = panel_path.stem
    try:
        from_block, to_block = stem.split("_", 1)
        block_range = [int(from_block), int(to_block)]
    except Exception:
        block_range = [0, 0]
    return {
        "chainId": int(chain_id),
        "contractAddress": str(contract_address),
        "blockRange": block_range,
        "fetchTimestamp": datetime.now(timezone.utc).isoformat(),
        "dataHash": _compute_data_hash(panel_path),
        "gitCommit": _git_commit(),
    }


@dataclass(frozen=True)
class FitOutput:
    """Return shape for run_fit. CLI subcommand consumes run_id + paths + gate_passes."""

    run_id: str
    fit_report_path: Path
    residuals_path: Path
    fit_report: dict[str, Any]


def _strip_per_leg_for_json(per_leg: list[dict]) -> list[dict]:
    """Trim time_rescaling per-leg dicts to JSON-serializable scalars.

    The residual arrays (Lambda_at_events, rescaled_dt) live in residuals.parquet;
    fit_report.json carries the per-leg ks_statistic / p_value / n_events scalars
    plus the optional skipped_reason flag.
    """
    out: list[dict] = []
    for r in per_leg:
        compact = {
            "ks_statistic": float(r["ks_statistic"])
            if r.get("ks_statistic") is not None
            else None,
            "p_value": float(r["p_value"]) if r.get("p_value") is not None else None,
            "n_events": int(r["n_events"]),
        }
        if "skipped_reason" in r:
            compact["skipped_reason"] = str(r["skipped_reason"])
        out.append(compact)
    return out


def run_fit(
    panel_path: str | Path,
    out_dir: str | Path,
    bootstrap_reps: int = PRODUCTION_N_REPS,
    decays: float | None = None,
    chain_id: int = _DEFAULT_CHAIN_ID,
    contract_address: str = _DEFAULT_CONTRACT,
) -> FitOutput:
    """Top-level Phase 3 fit pipeline.

    Sequential pipeline:
      1. Load Phase-2 panel + extract leg_0 / leg_1 timestamps.
      2. Build the PANEL-02 provenance header.
      3. wall_clock_split -> 80/20 train + held-out.
      4. Fit NHPP (INAR(p) on TRAIN) + Hawkes (tick.HawkesExpKern on TRAIN).
      5. Bootstrap LR test (FULL panel — observed-data statistic + null sim from
         the train-fitted NHPP rate; matches lr_test.py contract).
      6. Held-out log-likelihood for both models (closed-form on test window
         with full pre-test history continuity for the Hawkes intensity).
      7. Stationarity diagnostic on the split (PRE_REGISTRATION +/-25% rule).
      8. Time-rescaling KS test per leg on the held-out segment with train-
         fitted parameters; build residuals DataFrame; write residuals.parquet.
      9. Profile-likelihood eta-CI (DGP-06).
     10. Evaluate the four-criterion gate; assemble fit_report.json with full
         SC-1 metadata header + all required keys present whether the gate
         passes OR fails.

    Args:
        panel_path: path to data/raw/<protocol>/<pool>/<from>_<to>.parquet.
        out_dir: parent directory. Output lands at <out_dir>/<run_id>/.
        bootstrap_reps: bootstrap LR replicate count. Defaults to PRE_REGISTRATION
            lock 1000. Unit tests may pass 10..50 to stay within timeout budget.
        decays: Hawkes exponential-kernel decay. Default None -> free-β AIC-min
            over DECAY_GRID (the canonical v2 estimator; Plan 04.1.1-02b). The
            AIC-selected β propagates to the CI / KS / held-out-LL legs via
            hawkes_train["decays"]. Pass a float to pin β (diagnostics only).
        chain_id: EIP-155 chain ID. Default 42220 (Celo mainnet).
        contract_address: pool address. Default cKES/USDT ICHI vault.

    Returns:
        FitOutput dataclass with run_id, fit_report_path, residuals_path,
        and the parsed fit_report dict (for callers that want to inspect
        without re-reading the JSON).
    """
    panel_path = Path(panel_path)
    panel_df = pl.read_parquet(panel_path)
    provenance = _panel_provenance(panel_path, chain_id, contract_address)

    leg_0, leg_1, window_start, window_end = _extract_legs_from_panel(panel_df)

    # run_id (CONTEXT.md decision) -- deterministic under (panel, code, tick).
    run_id = _derive_run_id(provenance["dataHash"], provenance["gitCommit"], tick.__version__)
    run_dir = Path(out_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Step 3 — wall-clock 80/20 split. WallClockSplit dataclass per 03-04 scaffold.
    split = wall_clock_split(leg_0, leg_1, window_start, window_end, HELD_OUT_FRACTION_DEFAULT)

    # Step 4 — fit NHPP + Hawkes on TRAIN segment (NOT the full panel — Pitfall 5).
    nhpp_train = fit_nhpp_inar(
        split.train_leg_0, split.train_leg_1, window_start, split.t_split
    )
    hawkes_train = fit_hawkes_expkern(
        split.train_leg_0, split.train_leg_1, decays=decays
    )

    # Step 5 — bootstrap LR on FULL panel (the LR statistic is the observed-data
    # 2*(LL_hawkes - LL_nhpp) and the bootstrap null simulates from the FULL-
    # panel NHPP rate; both are panel-level — train/test split is unrelated to
    # the bootstrap rig per lr_test.py contract).
    lr_result = parametric_bootstrap_lr(
        leg_0,
        leg_1,
        panel_data_hash=provenance["dataHash"],
        window_start=window_start,
        window_end=window_end,
        n_reps=bootstrap_reps,
        alpha=LR_ALPHA,
    )

    # Step 6 — held-out log-likelihoods. CRITICAL: both must be on the same
    # probability space (continuous-time point-process LL) so the comparison is
    # dimensionally meaningful. The NHPP held-out path uses the homogeneous-
    # baseline NHPP LL (compute_held_out_loglik_nhpp); the Hawkes held-out path
    # uses the closed-form Hawkes LL with train-fitted parameters + full pre-
    # test history (compute_held_out_loglik_hawkes from 03-04).
    nhpp_baseline_per_sec = _nhpp_baseline_per_sec(nhpp_train)
    nhpp_held_out_ll = compute_held_out_loglik_nhpp(
        nhpp_baseline_per_sec,
        split.held_out_leg_0,
        split.held_out_leg_1,
        split.t_split,
        window_end,
    )
    hawkes_baseline = np.asarray(hawkes_train["baseline"], dtype=np.float64)
    hawkes_adjacency = np.asarray(hawkes_train["adjacency"], dtype=np.float64)
    hawkes_decays_t = float(hawkes_train["decays"])
    hawkes_held_out_ll = compute_held_out_loglik_hawkes(
        hawkes_baseline,
        hawkes_adjacency,
        hawkes_decays_t,
        split.held_out_leg_0,
        split.held_out_leg_1,
        leg_0,
        leg_1,
        split.t_split,
        window_end,
    )

    # Step 7 — stationarity diagnostic (PRE_REGISTRATION +/-25%).
    stationarity = baseline_stationarity_check(split)

    # Step 8 — time-rescaling KS test per leg on the held-out segment with
    # TRAIN-fitted parameters (Pitfall 5: in-sample passes misspecified models).
    ks_per_leg: list[dict] = []
    held_out_legs = (split.held_out_leg_0, split.held_out_leg_1)
    for leg_idx, held_times in enumerate(held_out_legs):
        result = time_rescaling_ks_test_leg(
            held_times,
            leg_idx,
            hawkes_baseline,
            hawkes_adjacency,
            hawkes_decays_t,
            leg_0,
            leg_1,
            split.t_split,
            window_end,
        )
        ks_per_leg.append(result)

    # Combined held-out KS p-value: min across legs is a conservative aggregator
    # (rejecting either leg's exponentiality is sufficient to reject the joint
    # specification). NaN p-values arise on insufficient events or non-positive
    # rescaling; treated as "test skipped" so they don't contribute to the
    # combined p-value.
    valid_ks_pvalues = [
        float(r["p_value"])
        for r in ks_per_leg
        if r.get("p_value") is not None and not np.isnan(r["p_value"])
    ]
    ks_combined_pvalue = float(min(valid_ks_pvalues)) if valid_ks_pvalues else float("nan")

    # Build residuals DataFrame and write sidecar parquet.
    residuals_df = build_residuals_dataframe(ks_per_leg, list(held_out_legs))
    residuals_path = run_dir / "residuals.parquet"
    residuals_df.write_parquet(residuals_path)
    residuals_hash = hashlib.sha256(residuals_path.read_bytes()).hexdigest()

    # Step 9 — profile-likelihood eta-CI (DGP-06). Alpha defaults to the
    # PRE_REGISTRATION-aligned profile_likelihood.DEFAULT_ALPHA (95% CI).
    eta_ci = profile_likelihood_eta_ci(
        leg_0, leg_1, hawkes_train, decays=hawkes_decays_t
    )

    # Step 10 — canonicalize NHPP / Hawkes loglik on the SAME continuous-time
    # point-process probability space. The raw `loglik_in_sample` fields from
    # the upstream fit dicts are NOT on this space (VAR.llf is Gaussian on bin
    # counts; tick.score() under the LS fallback is the least-squares loss).
    # Recompute via the canonical closed-form Hawkes LL in lr_test.py; both
    # log-likelihoods now live on the same space.
    nhpp_train_ll_canonical = _nhpp_pointprocess_loglik(
        nhpp_train, split.train_leg_0, split.train_leg_1, hawkes_decays_t
    )
    hawkes_train_ll_canonical = _hawkes_loglik_vectorized(
        hawkes_baseline,
        hawkes_adjacency,
        hawkes_decays_t,
        split.train_leg_0,
        split.train_leg_1,
    )

    # Stamp the canonical LL back into the fit dicts that go into fit_report.
    # Preserve the upstream `loglik_in_sample` under `loglik_in_sample_raw` for
    # provenance audit (the raw value reflects the upstream objective — VAR.llf
    # for NHPP, tick.score() / LS loss for Hawkes — and is useful when comparing
    # the canonical orchestrator output to a direct upstream-module run).
    nhpp_inar_params = dict(nhpp_train)
    nhpp_inar_params["loglik_in_sample_raw"] = nhpp_inar_params.pop(
        "loglik_in_sample", None
    )
    nhpp_inar_params["loglik"] = float(nhpp_train_ll_canonical)

    hawkes_mv_params = dict(hawkes_train)
    hawkes_mv_params["loglik_in_sample_raw"] = hawkes_mv_params.pop(
        "loglik_in_sample", None
    )
    hawkes_mv_params["loglik"] = float(hawkes_train_ll_canonical)

    # Four-criterion gate (PRE_REGISTRATION §Acceptance Regions).
    eta_hat_unconstrained = float(hawkes_train["branching_ratio"])
    lr_rejects = bool(lr_result.get("rejects_at_alpha", False))
    eta_floor_met = bool(eta_hat_unconstrained >= ETA_FLOOR)
    ks_held_out_passes = bool(
        not np.isnan(ks_combined_pvalue) and ks_combined_pvalue > KS_ALPHA
    )
    branching_ci_excludes_zero = bool(float(eta_ci["lower"]) > 0.0)
    stationary = bool(stationarity["decision"] == "stationary")
    gate_passes = bool(
        lr_rejects
        and eta_floor_met
        and ks_held_out_passes
        and branching_ci_excludes_zero
        and stationary
    )

    # Assemble the fit_report.json payload. Every SC-1 key is populated; nothing
    # is conditional on gate_passes. CONTEXT.md `<specifics>` invariant: NEVER
    # write a fit_report.json with missing keys.
    fit_report: dict[str, Any] = {
        **provenance,
        "run_id": run_id,
        "tick_lib_version": str(tick.__version__),
        "nhpp_inar_params": nhpp_inar_params,
        "hawkes_mv_params": hawkes_mv_params,
        "lr_test": lr_result,
        "ks_rescaled_time": {
            "p_value": ks_combined_pvalue,
            "residuals_hash": residuals_hash,
            "per_leg": _strip_per_leg_for_json(ks_per_leg),
            "ks_alpha": KS_ALPHA,
        },
        "held_out_loglik": {
            "nhpp": float(nhpp_held_out_ll),
            "hawkes": float(hawkes_held_out_ll),
            "split_metadata": split.to_metadata(),
        },
        "branching_ratio_ci": eta_ci,
        "baseline_stationarity_check": stationarity,
        "input_diagnostics": {
            "total_events_per_leg": [int(leg_0.size), int(leg_1.size)],
            "simultaneous_event_pairs": int(np.sum(np.isin(leg_0, leg_1))),
            "tie_counts": {
                "block_level_ties_leg_0": int(np.sum(np.diff(leg_0) == 0.0))
                if leg_0.size >= 2
                else 0,
                "block_level_ties_leg_1": int(np.sum(np.diff(leg_1) == 0.0))
                if leg_1.size >= 2
                else 0,
            },
            # Audit trail for the canonical Hawkes / NHPP LL source. See the
            # module docstring's "LOCKED INVARIANTS" block for the rationale.
            "hawkes_loglik_source": (
                "abrigo_x402.dgp.lr_test._hawkes_loglik_vectorized"
            ),
            "nhpp_loglik_source": (
                "abrigo_x402.dgp.lr_test._nhpp_pointprocess_loglik"
            ),
            "hawkes_fit_method_used": str(hawkes_train.get("fit_method_used", "unknown")),
        },
        "gate_passes": gate_passes,
        "gate_criteria": {
            "lr_rejects": lr_rejects,
            "eta_floor_met": eta_floor_met,
            "ks_held_out_passes": ks_held_out_passes,
            "branching_ci_excludes_zero": branching_ci_excludes_zero,
            "stationary": stationary,
            "eta_floor_threshold": ETA_FLOOR,
            "lr_alpha": LR_ALPHA,
            "ks_alpha": KS_ALPHA,
        },
    }

    # Pre-write SC-1 invariant: every required key MUST be present (gate-pass OR
    # gate-fail). Raising here would prevent a malformed artifact from landing
    # on disk and corrupting downstream consumers.
    missing = [k for k in REQUIRED_FIT_REPORT_KEYS if k not in fit_report]
    if missing:
        raise KeyError(
            f"fit_report.json assembly bug: missing required SC-1 keys: {missing}"
        )

    fit_report_path = run_dir / "fit_report.json"
    fit_report_path.write_text(json.dumps(fit_report, indent=2, sort_keys=True))

    return FitOutput(
        run_id=run_id,
        fit_report_path=fit_report_path,
        residuals_path=residuals_path,
        fit_report=fit_report,
    )
