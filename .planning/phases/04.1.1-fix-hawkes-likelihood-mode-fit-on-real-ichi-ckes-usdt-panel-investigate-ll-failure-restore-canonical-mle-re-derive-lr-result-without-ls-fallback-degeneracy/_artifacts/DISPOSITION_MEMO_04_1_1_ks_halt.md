# Disposition Memo: 04.1.1 real-panel gate HALT 2026-05-29

## Pre-registration locked
- Pre-reg doc: `notes/PRE_REGISTRATION.md` §Prior Parameters + §Test Statistics + §Phase 04.1.1 (v1/v2/02b/02c amendments)
- Four-criterion verdict gate (AF-03 locked, UNCHANGED across all 04.1.1 amendments):
  1. `lr_rejects` — bootstrap LR rejects NHPP at **α = 0.01**
  2. `ks_held_out_passes` — time-rescaling KS on held-out (last 20% temporal block), **p > 0.05**, **min-leg aggregator**
  3. `eta_floor_met` — branching ratio **η ≥ 0.2**
  4. `branching_ci_excludes_zero` — profile-likelihood CI lower bound **> 0**
- gate_passes := AND of all four
- Canonical estimator (v2): free-β AIC scipy_canonical_ll; common-t0 LL; stationarity ρ(α/β)<1; genuine constrained-MLE CI
- Locked dates: base 2026-05-25; v2 supersession `fda5905` 2026-05-28; 02c correctness fixes `801cd41` 2026-05-28
- Run: `data/fits/ichi/bdaf5c7ba5a2/fit_report.json` (commit `12cf99f`)

## Realized
- N: 778 events (leg-0 = 382, leg-1 = 396); train 299+317; held-out 83+79
- η̂ (branching_ratio): 0.600 at AIC-min β=0.001 (reported as lower bound per ~13% downward n≈700 finite-sample bias)
- LR: observed_stat = 561.29, p = 0.0 → **lr_rejects = TRUE**
- η-floor: 0.600 ≥ 0.2 → **eta_floor_met = TRUE**
- branching CI: [0.001, 0.95] (constrained_mle_profile; lower > 0 but grid-clamped/wide) → **branching_ci_excludes_zero = TRUE**
- KS held-out: leg-0 p = 0.0474, leg-1 p = 0.0564; min-leg = 0.0474 < 0.05 → **ks_held_out_passes = FALSE**
- held-out LL: Hawkes −1206.23 vs NHPP −1320.63 (Hawkes wins by 114.4 nats)
- **gate: 3/4 → gate_passes = FALSE**

## Trigger fired
**p > threshold** on the KS held-out criterion: leg-0 KS p = 0.0474 vs pre-registered α = 0.05 (knife-edge miss, 0.0026 below). The min-leg aggregator (locked) sets ks_held_out_passes = FALSE → gate_passes = FALSE.

## Status of the gate_passes=FALSE outcome (not itself a violation)
The pre-registration ANTICIPATED gate_passes=FALSE as a valid branch: a null / HEDGE-05 firing_condition fires and the deliverable is a faithful null/near-miss report. PROJECT.md: "Treating null results as project failures is itself an AF-03 violation." Therefore shipping the realized 3/4 result via the LOCKED handling (Wave 4 firing_condition derivation + Wave 5 verification + Phase 5 PDF) requires NO pivot and is the pre-registered path. The descriptive findings (η≈0.6, LR rejects NHPP, held-out Hawkes reversal) are real and fully reportable AS DESCRIPTIVE EVIDENCE; the VERDICT remains gate-did-not-pass.

This memo exists to block the TEMPTATION created by the knife-edge, not to relabel the outcome.

## What was NOT done
Explicit list of post-hoc changes considered (because the KS miss is 0.0026 from passing) and REJECTED — none applied:
- ❌ NOT relaxed KS α from 0.05 to 0.04 (or any value) to clear leg-0 p=0.0474
- ❌ NOT switched the KS aggregator from min-leg to leg-average / max-leg / leg-0-only / leg-1-only (leg-average ≈ 0.0519 would "pass" — explicitly NOT taken; the min-leg aggregator is locked)
- ❌ NOT changed the held-out split fraction (0.2) or the temporal-block definition to reshape the held-out sample
- ❌ NOT dropped or down-weighted leg-0 (the failing leg)
- ❌ NOT switched the time-rescaling residual test (KS → Anderson-Darling / CvM / Ljung-Box) to find a test that passes
- ❌ NOT re-seeded / re-fit to perturb the held-out KS p across the 0.05 line
- ❌ NOT added a "one more robustness" KS variant
- ❌ NOT relabeled gate_passes=FALSE as "pass with caveat", "near-miss positive", "exploratory positive", or "directionally positive"
- ❌ NOT footnoted the KS miss to present the result as confirmatory

## Awaiting user-enumerated pivot

<!-- LEFT INTENTIONALLY EMPTY per anti-fishing-replication halt-procedure.md.
The user enumerates any pivot. The analyst does NOT enumerate — not as examples,
not unranked, not "for the user to pick from". Empty section. Wait.

Note: a pivot is only needed if the user wants to ATTEMPT TO CHANGE the verdict.
Shipping the realized gate_passes=FALSE result faithfully via the pre-registered
null/near-miss handling needs NO pivot — that path is already locked. -->
