# Archival pointer — run_id `ae9e3ba17900` (LS-fallback evidence; SUPERSEDED)

**Status: SUPERSEDED. Do NOT cite this run as the v1.0 result.**

This run is the **least-squares fallback** fit on the real ICHI cKES/USDT panel
(dataHash `a72a4ee…`, n=778 = 382 leg-0 + 396 leg-1). It is retained as audit
history of the LS-fallback degeneracy, NOT as a scientific deliverable.

## Why this run is an artifact

The tick `HawkesExpKern` likelihood mode failed silently on this panel, so the
fit cascaded to the least-squares fallback:

- `input_diagnostics.hawkes_fit_method_used = "least-squares"`
- `hawkes_mv_params.branching_ratio = 0.0003072` (LS-degenerate η)
- `hawkes_mv_params.decays = 0.1` (kernel-blind β — never AIC-selected)
- `lr_test.observed_stat = 6,048,633` (epoch-inflated: LS-fallback params scored
  through the canonical Hawkes LL on an absolute-epoch origin)
- `lr_test.p_value = 0.58` → did NOT reject NHPP → `firing_condition = "null_lr"`

**The `null_lr` here was an artifact, not a finding.** The degenerate η, the
kernel-blind β, and the epoch-inflated LR statistic are all consequences of the
silent likelihood-mode failure + absolute-epoch LL scoring.

The v1 profile-likelihood band `[0.283, 0.371]` reported off this run was a
constrained-**projection** artifact (projection trick at the LS-degenerate β=0.1
point — NOT a joint-MLE CI) and has been **RETRACTED**.

## Superseded by

**`data/fits/ichi/bdaf5c7ba5a2/`** — `fit_method_used = scipy_canonical_ll`
(free-β AIC-selected joint-MLE, common-`t0=0` LL, stationarity-rejecting,
genuine `constrained_mle_profile` CI). On the corrected estimator:

- η = **0.600** (reported as a LOWER BOUND; AIC-min β=0.001)
- LR **rejects** NHPP (observed_stat=561.29, p=0.0)
- held-out Hawkes **wins** by 114 nats (reversed vs this LS run)
- four-criterion gate: **`gate_passes = FALSE (3/4)`** — KS held-out leg-0
  p=0.0474 knife-edge miss on the locked min-leg aggregator
- DERIVED `firing_condition = null_strip_unavailable` (convexity-justified,
  calibration-caveated; Carr-Madan strip unbuildable on the n_min=79<101
  degenerate joint_dist)

See `.planning/phases/04-…/04-VERIFICATION-pre.md` § "04.1.1 LL-Fit Rerun (v2)"
and `.planning/phases/04.1.1-…/_artifacts/DISPOSITION_MEMO_04_1_1_ks_halt.md`.

`fit_report.json` and `residuals.parquet` in this directory are preserved
byte-identical (audit history only).
