## VERDICT

PASS

## Scope

Code-reviewer pass on Plan 04-04 (Wave 1: four convex-dominance condition functions in `hedge/falsification.py` + SC-2 USDT-not-USDC framing + Pattern F canonical-LL contract + `literature_range_stipulation` discipline; 11 tests).

## Findings

- Frontmatter: `wave: 1`, `depends_on: [pre, "00"]`, `files_modified` is `hedge/falsification.py` + 2 test files — disjoint from Wave-1 siblings 04-01/03/05/06
- SC-2 grep gate operationalized as Test 8 (`! grep -i "^[^#]*usdc" falsification.py` via subprocess) + an acceptance-criterion bullet; the gate scopes to non-comment lines (the `^[^#]*` regex prefix), correctly permitting "USDT/USDC basis jump" framing in docstrings/comments which is the CONTEXT.md wording
- Pattern F operationalized in Test 9: greps `_hawkes_loglik_vectorized` IN, `tick.score` and `loglik_in_sample_raw` OUT — the dual-positive/dual-negative grep is the canonical-LL contract enforcement
- `evidence['source'] = 'literature_range_stipulation'` verbatim per CONTEXT.md commit e600d3a (the iter-2 framing correction) — the negative grep `! grep -E "methodological_port|Hernandez Cruz" falsification.py` enforces the corrected framing at this plan
- Hardcoded-jump-params gate: `! grep -rE "lambda_J\s*=\s*0\.|mu_J\s*=\s*-?0\.|sigma_J\s*=\s*0\." falsification.py` — falsification.py loads via `hedge.usdt_depeg.load_calibration()`, never hardcodes; usdt_depeg.py is the only legitimate home for the constants (Plan 04-06)
- Four functions implemented at canonical surface; condition-3 reads `fit_report :: hawkes_mv_params :: branching_ratio` + `gate_criteria.eta_floor_met` from Phase 3 (no re-fit); condition-4 receives calibration + LHS samples as injected dependencies (not loaded inline) — clean dependency injection that keeps the LHS computation in `usdt_depeg.py`
- `gate_decision_func` default is "permissive lambda" (always True) — explicitly flagged in the docstring: "Plan 04-06 may inject a real decision rule." Honest scaffolding; the v1.0 headline is the sensitivity bracket, not the gate decision, per CONTEXT.md
- `any_condition_passed` is computed in Plan 04-08 orchestrator (`bool(c1["passed"] or c2["passed"] or c3["passed"] or c4["passed"])`) — not in this plan's individual condition functions; clean separation of concerns
- `flips[:5]` cap on `flip_examples` keeps the gate_report.json payload bounded — sensible defensive coding
- Thresholds (`VOL_OF_VOL_THRESHOLD=0.05`, `KURTOSIS_EXCESS_THRESHOLD=0.0`, condition-3 branching-ratio floor 0.2) are planner's-discretion within CONTEXT.md envelope, documented in the SUMMARY output

## Recommendation

Accept.
