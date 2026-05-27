"""DGP-03: boundary-correct parametric bootstrap LR test for NHPP vs bivariate Hawkes.

Reference:
- Cavaliere et al. 2022 arxiv:2104.03122 (fixed intensity bootstrap for Hawkes).
- Filimonov & Sornette 2014 arxiv:1403.5227 (boundary correction).
- Self & Liang 1987 (asymptotic 50:50 mixture at the parameter boundary).
- arxiv:2410.05008 (LR over-rejection under naive plug-in).

LOCKED INVARIANTS (PRE_REGISTRATION.md and CONTEXT.md decisions):
- Production n_reps = 1000 (AF-04 hand-tuning hazard — never override at production-fit time).
  Dev-only override via the `n_reps` argument is permitted for unit-test smoke runs.
- alpha = 0.01 single-tier headline.
- Null distribution = 50:50 mixture of (point mass at 0) and (chi-squared with one degree of
  freedom) — empirically realized via the bootstrap, never invoked as an asymptotic helper.
- Deterministic seed: sha256(panel_data_hash + "phase-3-bootstrap").digest()[:4] as uint32.
  Same panel + same code -> byte-identical null distribution (SC-5 extension).

PROHIBITED HELPERS (SC-3 grep gate enforced by tests/test_lr_test.py and Makefile):
- The statsmodels diagnostic LR helper (asymptotic-only; boundary-blind).
- Any scipy chi-squared survival-function call for the null distribution.
Use ONLY the bootstrap rig (Pattern 3, Cavaliere et al. 2022).

CRITICAL: the bootstrap simulates from the FITTED NHPP (PITFALLS Pitfall 2), NOT from the
fitted Hawkes. Simulating from the alternative would calibrate the test under the alternative
and silently destroy size control. The simulator is `SimuHawkesExpKernels` with the adjacency
matrix set to a 2x2 of zeros (Research Open Q 2) — this reduces tick's Hawkes simulator to a
bivariate inhomogeneous Poisson process with the supplied baseline rate vector, i.e. pure NHPP.

CRITICAL: never pass the tick force-simulation override flag (Pitfall 9 — silently allows
non-stationary draws that would corrupt the size-calibration baseline). Bootstrap reps that
generate degenerate draws (fewer than 10 events on either leg) are skipped and counted under
n_failed for fit_report.json provenance.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import numpy as np

# Headless matplotlib — MUST be set BEFORE pyplot import (Pitfall: import order matters).
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from tick.hawkes import SimuHawkesExpKernels  # noqa: E402

from abrigo_x402.dgp.hawkes_fit import fit_hawkes_expkern  # noqa: E402
from abrigo_x402.dgp.nhpp_inar import fit_nhpp_inar  # noqa: E402

PRODUCTION_N_REPS: int = 1000
DEFAULT_ALPHA: float = 0.01

# Minimum events per leg below which a bootstrap replicate is discarded as degenerate.
_MIN_EVENTS_PER_LEG: int = 10


def _hawkes_loglik_vectorized(
    baseline: np.ndarray,
    adjacency: np.ndarray,
    decays: float,
    leg_0: np.ndarray,
    leg_1: np.ndarray,
) -> float:
    """Vectorized bivariate exp-kernel Hawkes log-likelihood (O(N^2 / 2) with broadcasting).

    Replaces the Python-level double loop in hawkes_fit._compute_hawkes_loglik_at_params
    for the inner bootstrap loop where it is called 2 * n_reps times. Same closed-form
    formula:
        LL = sum_i log(lambda_i(t)) - integral_0^T lambda(t) dt
    with the exponential-kernel closed-form integral.
    """
    legs = [leg_0, leg_1]
    if any(arr.size == 0 for arr in legs):
        return float("-inf")
    t_end = float(max(leg_0.max(), leg_1.max()))
    log_intensity_sum = 0.0
    for i, leg_i in enumerate(legs):
        lam = np.full(leg_i.size, float(baseline[i]), dtype=np.float64)
        for j, leg_j in enumerate(legs):
            a_ij = float(adjacency[i, j])
            if a_ij == 0.0 or leg_j.size == 0:
                continue
            # For each event t in leg_i, sum exp(-beta * (t - t')) over t' in leg_j with t' < t.
            # Broadcast: rows = leg_i events, cols = leg_j events.
            dt = leg_i[:, None] - leg_j[None, :]  # shape (n_i, n_j)
            mask = dt > 0.0
            # Mask before exp to avoid overflow on the negative-dt half of the matrix.
            dt_pos = np.where(mask, dt, 0.0)
            contrib = np.where(mask, np.exp(-decays * dt_pos), 0.0)
            lam += a_ij * contrib.sum(axis=1)
        if np.any(lam <= 0.0):
            return float("-inf")
        log_intensity_sum += float(np.log(lam).sum())
    # Closed-form integral for exp kernel: integral_0^T lambda_i(t) dt
    integral = 0.0
    for i in range(2):
        integral += float(baseline[i]) * t_end
        for j in range(2):
            a_ij = float(adjacency[i, j])
            if a_ij == 0.0 or legs[j].size == 0:
                continue
            hist = legs[j][legs[j] < t_end]
            integral += a_ij * float(np.sum(1.0 - np.exp(-decays * (t_end - hist)))) / decays
    return float(log_intensity_sum - integral)


def _derive_seed(panel_data_hash: str) -> int:
    """sha256(panel_data_hash + 'phase-3-bootstrap').digest()[:4] as big-endian uint32.

    Locked by CONTEXT.md (`<decisions>`: "Random seed"); the 4-byte truncation gives a uint32
    that numpy's `default_rng` accepts directly. Same panel -> same seed -> byte-identical
    null distribution.
    """
    digest = hashlib.sha256((panel_data_hash + "phase-3-bootstrap").encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


def _nhpp_baseline_per_sec(nhpp_fit: dict) -> np.ndarray:
    """Kirchner -> NHPP rate scaling: VAR(p) unconditional mean / bin_width = events/sec/leg.

    For a VAR(p) `y_t = c + sum_l A_l y_{t-l} + eps_t`, the unconditional mean is
    `mu = (I - sum_l A_l)^(-1) * c` (events/bin). Dividing by `bin_width_seconds` gives the
    NHPP intensity in events/sec per leg, which is what tick's SimuHawkesExpKernels takes
    as `baseline`.

    PITFALL: using `intercept / bin_width` directly under-estimates the rate because the
    intercept `c` in a VAR(p) absorbs only the residual mean after AR feedback, not the
    total unconditional mean. With `mu = (I - sum_l A_l)^{-1} c`, the recovered rate is
    correct on a degenerate-AR fit (sum A_l == 0 -> mu = c) AND on a non-degenerate fit.
    """
    intercept = np.asarray(nhpp_fit["intercept"], dtype=np.float64)  # shape (2,)
    bw = float(nhpp_fit["bin_width_seconds"])
    coefs = np.asarray(nhpp_fit["coefs"], dtype=np.float64)  # shape (p, 2, 2) or empty
    if coefs.size == 0:
        # Degenerate-leg path (zero-variance bin width) — fall back to intercept-only.
        mean_per_bin = intercept
    else:
        a_sum = coefs.sum(axis=0)  # shape (2, 2)
        eye = np.eye(2)
        try:
            mean_per_bin = np.linalg.solve(eye - a_sum, intercept)
        except np.linalg.LinAlgError:
            # Singular (I - sum A_l) — fall back to intercept-only.
            mean_per_bin = intercept
    # Numerical floor: SimuHawkesExpKernels requires strictly positive baseline.
    return np.maximum(mean_per_bin / bw, 1e-12)


def _nhpp_pointprocess_loglik(
    nhpp_fit: dict,
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    decays: float,
) -> float:
    """Continuous-time NHPP point-process log-likelihood at the Kirchner-fitted baseline.

    Pitfall fix (Rule 1): the LR statistic 2*(LL_hawkes - LL_nhpp) requires both log-
    likelihoods to live on the same probability space. The Kirchner INAR(p) fit returns
    `loglik_in_sample` from statsmodels VAR — a Gaussian likelihood on bin counts, NOT the
    NHPP point-process likelihood on continuous timestamps. Using it as `LL_nhpp` makes the
    LR statistic dimensionally meaningless (Hawkes LL is on continuous-time space).

    The clean fix: compute the NHPP point-process LL via the same closed-form Hawkes
    log-likelihood formula with adjacency = zeros. This evaluates a pure-Poisson process
    at the Kirchner baseline rate against the continuous-time event sequence, putting both
    LL_nhpp and LL_hawkes on the same probability space. The `decays` argument is only
    passed for kernel-formula symmetry — with adjacency = 0 it never enters the result.
    """
    baseline = _nhpp_baseline_per_sec(nhpp_fit)
    zero_adjacency = np.zeros((2, 2), dtype=np.float64)
    return _hawkes_loglik_vectorized(
        baseline, zero_adjacency, float(decays), leg_0_times, leg_1_times,
    )


def _simulate_nhpp_under_null(
    nhpp_baseline_per_sec: np.ndarray,
    end_time: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Simulate bivariate inhomogeneous Poisson via tick with adjacency = zeros.

    Setting `adjacency` to a 2x2 of zeros reduces SimuHawkesExpKernels to a bivariate
    inhomogeneous Poisson process with the supplied baseline rate vector — i.e. pure NHPP.
    This is the Research Open Q 2 simulator path: one simulator handles both null (zero
    adjacency) and alternative (nonzero adjacency) data-generating processes.

    NEVER pass the tick force-simulation override flag (Pitfall 9 — see module docstring).
    """
    sim = SimuHawkesExpKernels(
        adjacency=np.zeros((2, 2), dtype=np.float64),
        decays=0.1,  # ignored when adjacency = 0
        baseline=np.asarray(nhpp_baseline_per_sec, dtype=np.float64),
        end_time=float(end_time),
        seed=int(seed),
        verbose=False,
    )
    sim.simulate()
    return (
        np.asarray(sim.timestamps[0], dtype=np.float64),
        np.asarray(sim.timestamps[1], dtype=np.float64),
    )


def parametric_bootstrap_lr(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    panel_data_hash: str,
    window_start: float,
    window_end: float,
    n_reps: int = PRODUCTION_N_REPS,
    alpha: float = DEFAULT_ALPHA,
    diagnostic_plot_path: str | os.PathLike | None = None,
) -> dict:
    """Boundary-correct parametric bootstrap LR test for NHPP-vs-Hawkes.

    Procedure (Pattern 3, Cavaliere et al. 2022):
      1. Fit BOTH the NHPP null and the Hawkes alternative on the observed legs.
      2. Compute observed LR statistic = 2 * (LL_hawkes - LL_nhpp).
      3. For each of `n_reps` bootstrap replicates:
         a. Simulate a bivariate inhomogeneous Poisson panel from the FITTED NULL (Pitfall 2).
         b. Refit BOTH the NHPP null and the Hawkes alternative on the simulated panel.
         c. Record LR_b = 2 * (LL_hawkes_b - LL_nhpp_b).
      4. Empirical p-value = fraction of bootstrap LR_b at-or-above LR_observed.
      5. Render the diagnostic histogram showing the 50:50 mixture shape.

    Args:
        leg_0_times: event timestamps for leg 0 (token0-inflow Swaps), seconds, absolute.
        leg_1_times: event timestamps for leg 1 (token1-inflow Swaps), seconds, absolute.
        panel_data_hash: deterministic seed source (sha256 of panel bytes from Phase 2).
        window_start: window start time, seconds, absolute.
        window_end: window end time, seconds, absolute.
        n_reps: bootstrap replicates. Production lock = 1000 (AF-04). Tests use 30..200.
        alpha: rejection threshold. PRE_REGISTRATION lock = 0.01.
        diagnostic_plot_path: if provided, write the histogram PNG to this path (SC-3).

    Returns:
        dict with keys:
          observed_stat: 2 * (LL_hawkes_obs - LL_nhpp_obs)
          bootstrap_null_dist_50_50_chi2_0_chi2_1: list of finite bootstrap LR values
          p_value: empirical fraction of bootstrap LR >= observed_stat
          rejects_at_alpha: bool
          n_reps: replicate count requested
          n_successful_bootstrap: int (= len(bootstrap_null_dist_...))
          n_failed: int (degenerate draws + refit failures)
          seed: derived uint32 from panel_data_hash
          alpha: threshold used
    """
    seed = _derive_seed(panel_data_hash)
    rng = np.random.default_rng(seed)

    # 1. Fit BOTH models on the observed data.
    nhpp_obs = fit_nhpp_inar(leg_0_times, leg_1_times, window_start, window_end)
    hawkes_obs = fit_hawkes_expkern(leg_0_times, leg_1_times)
    # Both LL on the same probability space — continuous-time point-process LL via the
    # closed-form Hawkes formula (see _nhpp_pointprocess_loglik docstring). This is the
    # Rule-1 fix that makes the LR statistic dimensionally well-formed.
    #
    # Rule-1 fix #2: tick's HawkesExpKern.score() under gofit="least-squares" returns the
    # least-squares loss per unit time, NOT the log-likelihood (verified by reproducing
    # 0.0001 vs closed-form -6515 on the synthetic-NHPP fixture). The LR test requires a
    # log-likelihood, so we recompute the Hawkes LL at the fitted parameters via the same
    # closed-form formula used for the NHPP rate. Hawkes_LL and NHPP_LL therefore differ
    # only in the adjacency they integrate against (fitted alpha vs zeros).
    decays_obs = float(hawkes_obs["decays"])
    hawkes_baseline_obs = np.asarray(hawkes_obs["baseline"], dtype=np.float64)
    hawkes_adjacency_obs = np.asarray(hawkes_obs["adjacency"], dtype=np.float64)
    ll_nhpp_obs = _nhpp_pointprocess_loglik(
        nhpp_obs, leg_0_times, leg_1_times, decays_obs,
    )
    ll_hawkes_obs = _hawkes_loglik_vectorized(
        hawkes_baseline_obs, hawkes_adjacency_obs, decays_obs, leg_0_times, leg_1_times,
    )
    lr_observed = 2.0 * (ll_hawkes_obs - ll_nhpp_obs)

    # 2. Parametric bootstrap UNDER THE NULL (NHPP, NOT Hawkes — Pitfall 2).
    #
    # Performance: pin the AIC-selected hyperparameters from the observed-data fit so that
    # bootstrap replicates skip the bin-width / decay grid searches. The bootstrap is a
    # SIZE-CALIBRATION rig for the LR statistic *at the chosen hyperparameter regime*; the
    # grid search is for model selection on the observed data, not for each null replicate.
    # This drops per-rep cost from ~2s to ~0.3s (PRE_REGISTRATION 1000-rep production stays
    # tractable; SC-3 unit test smoke runs stay under the pytest timeout budget).
    #
    # Pinning the AR order to the observed-data p_star is the bootstrap convention for VAR
    # null calibration — refit with the same order so that the LR statistic compares the
    # SAME nested-model pair (Hawkes vs INAR(p)) on each replicate. The observed-data p_star
    # is recorded in nhpp_obs["p"] and used as max_p in the bootstrap refit (statsmodels
    # AIC-select will land back at p_star on a near-Poisson null sequence anyway, but
    # capping max_p drops the slow select_order call from ~1.5s to ~0.1s).
    nhpp_baseline = _nhpp_baseline_per_sec(nhpp_obs)
    nhpp_bin_width = float(nhpp_obs["bin_width_seconds"])
    nhpp_max_p_pinned = max(1, int(nhpp_obs["p"]))
    hawkes_decays_pinned = decays_obs
    sim_window = float(window_end - window_start)
    bootstrap_lr = np.full(n_reps, np.nan, dtype=np.float64)
    n_failed = 0
    for k in range(n_reps):
        rep_seed = int(rng.integers(0, 2**31))
        try:
            sim_0, sim_1 = _simulate_nhpp_under_null(nhpp_baseline, sim_window, rep_seed)
            if sim_0.size < _MIN_EVENTS_PER_LEG or sim_1.size < _MIN_EVENTS_PER_LEG:
                n_failed += 1
                continue
            # Shift simulated times back into the absolute window (Kirchner binning assumes
            # the times live in [window_start, window_end]).
            sim_0_abs = sim_0 + window_start
            sim_1_abs = sim_1 + window_start
            # Pin the same bin_width / decays selected on the observed data — the bootstrap
            # is a size-calibration rig at the chosen hyperparameter regime, not a re-doing
            # of model selection on each null replicate (see decision in step 2 above).
            nhpp_b = fit_nhpp_inar(
                sim_0_abs, sim_1_abs, window_start, window_end,
                bin_width_seconds=nhpp_bin_width,
                max_p=nhpp_max_p_pinned,
            )
            hawkes_b = fit_hawkes_expkern(sim_0_abs, sim_1_abs, decays=hawkes_decays_pinned)
            decays_b = float(hawkes_b["decays"])
            ll_nhpp_b = _nhpp_pointprocess_loglik(
                nhpp_b, sim_0_abs, sim_1_abs, decays_b,
            )
            ll_hawkes_b = _hawkes_loglik_vectorized(
                np.asarray(hawkes_b["baseline"], dtype=np.float64),
                np.asarray(hawkes_b["adjacency"], dtype=np.float64),
                decays_b,
                sim_0_abs,
                sim_1_abs,
            )
            if not (np.isfinite(ll_nhpp_b) and np.isfinite(ll_hawkes_b)):
                n_failed += 1
                continue
            # Self-Liang boundary: the projected NHPP nests Hawkes at alpha=0, so LR_b can
            # arrive at 0 from the projection clip (point mass) or as a positive continuous
            # draw (chi-squared(1) tail). Clip tiny negatives at 0 — they arise from numerical
            # noise in the projection clip and are not statistically meaningful at the boundary.
            lr_b = 2.0 * (ll_hawkes_b - ll_nhpp_b)
            if lr_b < 0.0 and abs(lr_b) < 1e-6:
                lr_b = 0.0
            bootstrap_lr[k] = lr_b
        except Exception:
            n_failed += 1
            bootstrap_lr[k] = np.nan

    valid = bootstrap_lr[~np.isnan(bootstrap_lr)]
    p_value = float(np.mean(valid >= lr_observed)) if valid.size > 0 else float("nan")

    # 3. Diagnostic plot (SC-3): histogram must visibly show point mass at 0 + continuous tail.
    if diagnostic_plot_path is not None:
        Path(diagnostic_plot_path).parent.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=(7, 4))
        # Log y-axis makes the point-mass-at-zero spike visible alongside the continuous tail.
        if valid.size > 0:
            ax.hist(valid, bins=60, color="#3a6ea5", edgecolor="black", alpha=0.85)
        ax.axvline(
            lr_observed,
            color="red",
            linestyle="--",
            linewidth=1.5,
            label=f"observed LR = {lr_observed:.3f}",
        )
        ax.set_yscale("log")
        ax.set_xlabel("Bootstrap LR statistic (2 * delta LL)")
        ax.set_ylabel("Frequency (log scale)")
        ax.set_title(
            "Bootstrap LR null distribution"
            f" (n_reps={n_reps}, n_failed={n_failed})\n"
            "point mass at 0 + continuous right tail (Self-Liang 1987 mixture)"
        )
        ax.legend(loc="upper right")
        fig.tight_layout()
        fig.savefig(diagnostic_plot_path, dpi=120)
        plt.close(fig)

    return {
        "observed_stat": float(lr_observed),
        "bootstrap_null_dist_50_50_chi2_0_chi2_1": valid.tolist(),
        "p_value": p_value,
        "rejects_at_alpha": bool(p_value < alpha) if not np.isnan(p_value) else False,
        "n_reps": int(n_reps),
        "n_successful_bootstrap": int(valid.size),
        "n_failed": int(n_failed),
        "seed": int(seed),
        "alpha": float(alpha),
    }
