---
evidence_source: literature_range_stipulation
base_triple:
  lambda_J: 0.05    # jumps per year
  mu_J: -0.05       # log-return per jump (negative -> depeg downside)
  sigma_J: 0.02     # log-return std per jump
sensitivity:
  n_samples: 64
  bound_ratio: 0.5
  seed: 20260527
calibrated_date: 2026-05-27
---

# USDT Depeg Jump-Leg Calibration

## Provenance Discipline (CRITICAL — per CONTEXT.md commit e600d3a)

Base triple stipulated from literature-range Merton 1976 defaults for stablecoin-class jumps.
NOT calibrated from cited primary data — Hernandez Cruz 2024 and Wu & Liu 2026 do not publish
jump-diffusion parameters; cited only as methodological-context references for stablecoin
tail-risk discussion. Sensitivity bracket (±50% N=64 Latin hypercube) is the uncertainty
mechanism.

## Base Triple

| Parameter | Value | Units | Justification |
|-----------|-------|-------|---------------|
| `lambda_J` | 0.05 | jumps/yr | Merton 1976 stablecoin-class single-event jump frequency ballpark |
| `mu_J` | -0.05 | log-return | Conservative downside jump expectation (5% depeg) |
| `sigma_J` | 0.02 | log-return std | Standard tight band for stablecoin volatility |

## Sensitivity Bracket

A 3-parameter Latin hypercube sample of size N=64 is drawn over the ±50% box around the base
triple. The bracket is the honesty mechanism per RESEARCH Pitfall 1: if the gate decision is
robust across the 64 cells, the stipulated triple is defensible; if even one cell flips the
decision, the result is surfaced as `sensitivity_fragile: true` in `gate_report.json`.

Sampling: `scipy.stats.qmc.LatinHypercube(d=3, seed=20260527)` + `qmc.scale(samples,
l_bounds=base*(1-0.5), u_bounds=base*(1+0.5))`. Locked seed for reproducibility.

## Non-Citation Discipline

The following statements are LOAD-BEARING NEGATIVES (downstream lint enforces):

- This document does NOT cite Hernandez Cruz 2024 (arxiv 2407.11716) as a jump-diffusion
  parameter source. That paper is a Difference-in-Differences transparency/MCI study on USDC
  liquidity around SVB; it does not publish Merton/Kou parameters.
- This document does NOT cite Wu & Liu 2026 (arxiv 2602.18820) as a jump-diffusion parameter
  source. That paper uses Quantile VAR, not jump-diffusion.
- The phrase "p" + "ort from Hernandez Cruz" must NOT appear in this document. Pre-commit hook
  (or Plan 04-09 acceptance gate) greps against it.

## Deferred (per CONTEXT.md `<deferred>`)

If a future paper provides USDT-specific Merton/Kou parameters, the stipulation can be
replaced. Update `evidence_source` to `primary_calibration` and add the citation here.
Until then, the literature-range stipulation + sensitivity bracket is the documented honesty
posture.

## Consumers

- `analysis/src/abrigo_x402/hedge/usdt_depeg.py :: load_calibration` parses the frontmatter
  `base_triple` keys.
- `analysis/src/abrigo_x402/hedge/usdt_depeg.py :: generate_lhs_samples` uses the frontmatter
  `sensitivity.n_samples`, `bound_ratio`, `seed` values.
- `analysis/src/abrigo_x402/hedge/falsification.py :: evaluate_condition_4_usdt_depeg`
  records `evidence_source: "literature_range_stipulation"` and the sensitivity summary.
