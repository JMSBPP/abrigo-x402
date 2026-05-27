---
phase: 04-cross-leg-dependence-l5-falsification-carr-madan-strip-l6
plan: 04
subsystem: hedge-falsification
tags: [wave-1, hedge, falsification, HEDGE-01, gate_report, pattern-F, sc-2, literature_range_stipulation, tdd]
dependency-graph:
  requires:
    - "04-00 scaffold (REQUIRED_GATE_REPORT_KEYS forward-declared; pre-commit grep gates installed)"
    - "Phase 3 dgp.lr_test._hawkes_loglik_vectorized (Pattern F canonical-LL source)"
    - "Phase 3 fit_report.json substrate (hawkes_mv_params.branching_ratio + gate_criteria.eta_floor_met)"
    - "04-06 hedge.usdt_depeg.load_calibration / generate_lhs_samples (stub call surface — Plan 04-06 implements)"
    - "AF-03 PRE_REGISTRATION amendment (commit 2dc3877; predates this commit)"
  provides:
    - "evaluate_condition_1_vol_of_vol, evaluate_condition_2_skew_fat_tails, evaluate_condition_3_hawkes_self_excitation, evaluate_condition_4_usdt_depeg, evaluate_four_conditions"
    - "REQUIRED_GATE_REPORT_KEYS verbatim against scripts/lint_artifacts.py mirror"
    - "Pluggable per-cell gate decision hook (gate_decision_func) for Plan 04-06 LHS sensitivity injection"
  affects:
    - "Plan 04-08 (Wave 2 orchestrator) — consumes evaluate_four_conditions to assemble gate_report.json"
    - "Plan 04-09 (Wave 3 acceptance) — HEDGE-01 row in acceptance grid resolves via SC-2 grep + 12-test pass"
tech-stack:
  added: []
  patterns:
    - "Pattern F (canonical-LL contract) — import _hawkes_loglik_vectorized from dgp.lr_test; no tick.score / loglik_in_sample_raw"
    - "Pattern G (REQUIRED_*_KEYS tuple + lint frozenset mirror) — gate_report.json schema sync invariant"
    - "Pluggable-decision-rule hook — gate_decision_func parameter allows Plan 04-06 strip-price-driven injection without re-touching falsification.py"
key-files:
  created:
    - .planning/phases/04-cross-leg-dependence-l5-falsification-carr-madan-strip-l6/04-04-SUMMARY.md
  modified:
    - analysis/src/abrigo_x402/hedge/falsification.py
    - analysis/tests/test_falsification.py
    - analysis/tests/test_gate_report_provenance.py
decisions:
  - "VOL_OF_VOL_THRESHOLD = 0.6 applied to coefficient of variation (std/mean) of rolling-window variances, NOT raw std. CoV normalizes away iid sampling-variance scale: under iid Exp(1) with window=50 and N=1000 the rolling-variance vector has CoV ~0.4 (sampling noise floor); under deliberately heteroscedastic regime swap CoV climbs above 1.0. 0.6 is the midpoint."
  - "KURTOSIS_EXCESS_THRESHOLD = 0.0 (standard fat-tail floor; Fisher convention via scipy.stats.kurtosis(fisher=True))"
  - "BRANCHING_RATIO_FLOOR = 0.2 (mirrors PRE_REGISTRATION §Acceptance Regions branching-ratio floor convention)"
  - "gate_decision_func default in condition 4 is permissive (always-True). Plan 04-06 supplies the real per-cell decision rule when wiring HEDGE-03 strip prices into the LHS sensitivity sweep."
  - "Composite evaluate_four_conditions accepts either polars DataFrame (production residuals.parquet path) or dict-like {'leg_0': ..., 'leg_1': ...} (test path tolerance) — runtime isinstance check on polars.DataFrame"
metrics:
  duration: "4 min 29 s (RED + GREEN + verification + commit)"
  completed: "2026-05-27"
  files-created: 1
  files-modified: 3
  tests-passing: "12/12 (10 falsification + 2 gate_report_provenance)"
  red-failures: 8
---

# Phase 04 Plan 04: HEDGE-01 Four-Condition Convex-Dominance Gate Summary

**One-liner:** Implemented HEDGE-01 four-condition gate at canonical signatures with Pattern F canonical-LL import from `dgp.lr_test`, condition-4 evidence locked to `source='literature_range_stipulation'` per CONTEXT.md commit `e600d3a` (no `methodological_port`, no `Hernandez Cruz` citation), all four 04-00 pre-commit grep gates (SC-2 USDC, canonical-LL, hardcoded-jump-params, Carr-Madan anti-pattern) clean, 12/12 tests green.

## Commits

| Commit  | Subject |
| ------- | ------- |
| dd866fe | test(04-04): RED — four-condition falsification gate + gate_report provenance tests |
| 557a811 | feat(04-04): GREEN — four-condition convex-dominance gate (USDT-reparameterized, literature_range_stipulation, Pattern F canonical-LL) |

## What Landed

### Source module: `analysis/src/abrigo_x402/hedge/falsification.py`

Four canonical-signature condition functions + composite evaluator:

- **`evaluate_condition_1_vol_of_vol(rescaled_dt_per_leg)`** — coefficient of variation (std/mean) of rolling-window variances; threshold `VOL_OF_VOL_THRESHOLD = 0.6`; passes if EITHER leg exceeds threshold; evidence dict per leg with `vol_of_vol`, `rolling_var_mean`, `rolling_var_std`, `window`.
- **`evaluate_condition_2_skew_fat_tails(rescaled_dt_per_leg)`** — `scipy.stats.skew` + `kurtosis(fisher=True)`; threshold `KURTOSIS_EXCESS_THRESHOLD = 0.0`; passes if EITHER leg satisfies skew > 0 AND excess_kurt > 0.
- **`evaluate_condition_3_hawkes_self_excitation(fit_report)`** — reads `hawkes_mv_params.branching_ratio` + `gate_criteria.eta_floor_met` from Phase 3; threshold `BRANCHING_RATIO_FLOOR = 0.2`; passes iff `branching_ratio >= 0.2` AND `eta_floor_met`; evidence dict declares `canonical_ll_source = "abrigo_x402.dgp.lr_test._hawkes_loglik_vectorized"` (Pattern F).
- **`evaluate_condition_4_usdt_depeg(calibration, lhs_samples, gate_decision_func=None)`** — verifies per-cell decision stability across LHS samples; `sensitivity_fragile = True` iff any cell flips relative to base decision; evidence dict carries `source: "literature_range_stipulation"` (verbatim) + `base_triple` + `sensitivity_summary {n_samples, n_flips, flip_examples}`. Pluggable `gate_decision_func` default is permissive (always True); Plan 04-06 supplies the real strip-price-driven decision rule.
- **`evaluate_four_conditions(residuals_df, fit_report, calibration, lhs_samples)`** — composite. Accepts polars DataFrame (production residuals.parquet schema: leg int, event_time float64, rescaled_dt float64) OR dict-like input (test path). Returns dict with four condition payloads + `any_condition_passed` (HEDGE-05 firing condition (c) consumer).

### Tests

`analysis/tests/test_falsification.py` (10 tests, all PASS):

| # | Test | Asserts |
| - | ---- | ------- |
| 1 | `test_condition_1_positive_heteroscedastic` | Exp(1) -> Exp(0.1) regime swap triggers passed=True with vol_of_vol > 0 on at least one leg |
| 2 | `test_condition_1_negative_iid_exp` | iid Exp(1) N=1000 yields passed=False (CoV ~0.4 below threshold 0.6) |
| 3 | `test_condition_2_positive_pareto` | Pareto(a=2.5) N=1000 yields passed=True with skew>0 and excess_kurt>0 |
| 4 | `test_condition_2_negative_normal` | Normal(0,1) N=2000 yields passed=False |
| 5 | `test_condition_3_positive_high_branching` | branching_ratio=0.5 + eta_floor_met=True yields passed=True; evidence includes canonical_ll_source pointing at _hawkes_loglik_vectorized |
| 6 | `test_condition_3_negative_low_branching` | branching_ratio=0.05 + eta_floor_met=False yields passed=False |
| 7 | `test_condition_4_source_is_literature_range_stipulation` | evidence['source'] == 'literature_range_stipulation' (verbatim); n_samples == 64; sensitivity_fragile present |
| 8 | `test_sc2_no_usdc_literals_outside_comments` | `grep -i "^[^#]*usdc" falsification.py` exits non-zero (SC-2 gate) |
| 9 | `test_canonical_ll_contract_pattern_F` | imports `_hawkes_loglik_vectorized` from `abrigo_x402.dgp.lr_test`; does NOT contain `tick.score` or `loglik_in_sample_raw` |
| 10 | `test_condition_4_does_not_cite_hernandez_cruz` | `Hernandez Cruz` and `methodological_port` absent from source (AF-03 + CONTEXT.md commit e600d3a) |

`analysis/tests/test_gate_report_provenance.py` (2 tests, all PASS):

| # | Test | Asserts |
| - | ---- | ------- |
| 1 | `test_gate_report_fixture_has_all_required_keys` | `gate_report_fixture` (conftest) has every REQUIRED_GATE_REPORT_KEYS entry |
| 2 | `test_lint_gate_report_catches_missing_key` | `lint_gate_report_json` flags a fixture missing `any_condition_passed` |

### Pre-commit grep gates (all four installed by 04-00)

| Gate | Result |
| ---- | ------ |
| SC-2 USDC literal gate (no `usdc` non-comment in falsification.py) | PASS |
| Carr-Madan anti-pattern gate (carr_madan_strip.py — out of scope here) | PASS |
| Canonical-LL gate (no `loglik_in_sample_raw` in hedge/) | PASS |
| Hardcoded-jump-params gate (no `lambda_J=0.* / mu_J=-0.* / sigma_J=0.*` in falsification.py / carr_madan_strip.py) | PASS |

## Planner Thresholds (locked)

| Constant | Value | Rationale |
| -------- | ----- | --------- |
| `VOL_OF_VOL_THRESHOLD` | 0.6 | Coefficient-of-variation form. iid Exp(1) baseline noise floor CoV ~0.4 (N=1000, window=50); heteroscedastic regime swap CoV >1.0; 0.6 = midpoint. |
| `KURTOSIS_EXCESS_THRESHOLD` | 0.0 | Standard fat-tail floor under Fisher convention. |
| `BRANCHING_RATIO_FLOOR` | 0.2 | Mirrors PRE_REGISTRATION §Acceptance Regions branching-ratio floor convention. |
| `gate_decision_func` default | permissive (always True) | Plan 04-06 injects real per-cell decision when HEDGE-03 strip prices are wired. |

## Verification Output

```
$ cd analysis && uv run pytest tests/test_falsification.py tests/test_gate_report_provenance.py -v | tail -3
======================== 12 passed, 1 warning in 1.57s =========================

$ ! grep -i "^[^#]*usdc" analysis/src/abrigo_x402/hedge/falsification.py && echo PASS
PASS

$ grep -q "from abrigo_x402.dgp.lr_test import _hawkes_loglik_vectorized" analysis/src/abrigo_x402/hedge/falsification.py && echo PASS
PASS

$ ! grep -E "tick\.score|loglik_in_sample_raw" analysis/src/abrigo_x402/hedge/falsification.py && echo PASS
PASS

$ grep -q '"literature_range_stipulation"' analysis/src/abrigo_x402/hedge/falsification.py && echo PASS
PASS

$ ! grep -E "methodological_port|Hernandez Cruz" analysis/src/abrigo_x402/hedge/falsification.py && echo PASS
PASS

$ ! grep -E "lambda_J\s*=\s*0\.|mu_J\s*=\s*-?0\.|sigma_J\s*=\s*0\." analysis/src/abrigo_x402/hedge/falsification.py && echo PASS
PASS

$ grep -cE "^def evaluate_condition_[1234]" analysis/src/abrigo_x402/hedge/falsification.py
4

$ make lint-artifacts | tail -1
lint_artifacts: 1 parquet PASS PANEL-02
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Initial `VOL_OF_VOL_THRESHOLD=0.05` produced false-positive on iid Exp(1) baseline**

- **Found during:** Task 2 GREEN test run
- **Issue:** Raw `std(rolling_var)` of iid Exp(1) with window=50, N=1000 is ~0.4-0.6 by Monte Carlo sampling alone. The plan-body threshold 0.05 was an order of magnitude too aggressive and caused `test_condition_1_negative_iid_exp` to fail (passed=True when expected False).
- **Fix:** Switched the statistic from raw `std(rolling_var)` to coefficient of variation `std(rolling_var) / mean(rolling_var)`. CoV is scale-invariant in the underlying variance — under iid Exp(1) it reflects only sampling noise (~0.4), under deliberately heteroscedastic regime swap it climbs above 1.0. Threshold raised to 0.6 (midpoint). Added rationale block to module docstring.
- **Files modified:** `analysis/src/abrigo_x402/hedge/falsification.py` (one constant + one function body + module docstring rationale)
- **Commit:** Squashed into GREEN commit `557a811`
- **Pattern:** Same class as Phase 3 03-06 Rule-1 fix (LL_max derivation re-anchored when planner threshold underspecified the noise floor).

**2. [Rule 1 - Bug] Plan-body docstring text would have tripped its own anti-citation grep test**

- **Found during:** Task 2 GREEN test run (`test_condition_4_does_not_cite_hernandez_cruz` failed first iteration)
- **Issue:** Plan-body proposed docstring "NOT 'methodological_port', NOT 'Hernandez Cruz 2024'" literally contains the strings `methodological_port` and `Hernandez Cruz`, which the test forbids appearing anywhere in source.
- **Fix:** Rewrote docstring to describe the discipline without naming the prohibited tokens. Same regression class as 04-00 Carr-Madan docstring fix.
- **Files modified:** `analysis/src/abrigo_x402/hedge/falsification.py` (docstring only)
- **Commit:** Squashed into GREEN commit `557a811`

**3. [Rule 1 - Bug] `tick.score()` in plan-body docstring would have tripped Pattern F test**

- **Found during:** Task 2 GREEN test run
- **Issue:** Plan-body proposed docstring text referenced `tick.score()` as the wrong-LL alternative, which the Pattern F test (`assert "tick.score" not in src`) forbids.
- **Fix:** Removed `tick.score` literal from docstrings; described it descriptively ("the LS-fallback objective surfaced upstream by the third-party point-process library").
- **Files modified:** `analysis/src/abrigo_x402/hedge/falsification.py` (docstring only)
- **Commit:** Squashed into GREEN commit `557a811`

No other deviations — the plan executed substantively as written.

## Forward Reference

- **Plan 04-06 (HEDGE-03)** owns `hedge/usdt_depeg.py :: load_calibration` + `generate_lhs_samples` and is the supplier of `calibration` + `lhs_samples` to condition 4. The current condition-4 default `gate_decision_func` is permissive; Plan 04-06 will inject the strip-price-driven decision once Plan 04-05 lands Carr-Madan.
- **Plan 04-08 (Wave 2 orchestrator)** consumes `evaluate_four_conditions` to assemble `gate_report.json`, merges the PANEL-02 + run_id header via `provenance.with_header`, and writes to `data/fits/ichi/<run_id>/gate_report.json`. The composite return shape matches `REQUIRED_GATE_REPORT_KEYS` sans the header (the orchestrator merges the header on write).
- **Plan 04-09 (Wave 3 acceptance)** verifies HEDGE-01 via the 12-test pass + 6 grep-gate checks recorded in the Verification Output block above.

## Self-Check: PASSED

```
FOUND: analysis/src/abrigo_x402/hedge/falsification.py
FOUND: analysis/tests/test_falsification.py
FOUND: analysis/tests/test_gate_report_provenance.py
FOUND: commit dd866fe in git log (RED)
FOUND: commit 557a811 in git log (GREEN)
FOUND: Pattern F import (from abrigo_x402.dgp.lr_test import _hawkes_loglik_vectorized)
FOUND: literature_range_stipulation literal in falsification.py
FOUND: 4 evaluate_condition_N defs in falsification.py
12/12 tests passing
All 4 pre-commit grep gates clean
```
