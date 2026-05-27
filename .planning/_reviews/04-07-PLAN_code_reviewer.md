## VERDICT

PASS

## Scope

Code-reviewer pass on Plan 04-07 (Wave 2: `run_three_way_stress` (independence + fitted_joint + comonotone-Fréchet-upper-bound) + divergence_flag at 30% + `comonotone_method="empirical_body_parametric_tail"`; 7 tests).

## Findings

- Frontmatter: `wave: 2`, `depends_on: [pre, "00", "05"]` — wave-bumped to 2 because of the `key_links` import edge to `compute_strip` from Plan 04-05 (wave 1). The plan body explicitly calls out the sequencing per `wave = max(deps_wave) + 1`. Honors wave graph acyclicity
- `files_modified` is `hedge/stress_test.py` + 2 test files — disjoint from sibling Wave-2 plan 04-02 (which only touches `dependence/permutation_null.py`)
- Three scenarios implemented as Monte-Carlo via shared seed + inverse empirical CDF — CONTEXT.md lock for comonotone (U_1 ~ U(0,1), U_2 = U_1) preserved verbatim in the third branch
- `DIVERGENCE_FLAG_THRESHOLD_PCT = 30.0` constant + flag-only-no-hard-fail semantics — HEDGE-04 framing of divergence as a finding (not a failure) is preserved; acceptance grep `grep -q "DIVERGENCE_FLAG_THRESHOLD_PCT.*=.*30"` enforces
- `comonotone_method = "empirical_body_parametric_tail"` label set per RESEARCH Pitfall 6 — v1.0 uses pure empirical body (NO parametric tail extension); the label is forward-compatible and the SUMMARY output explicitly states "Plan 04-08 orchestrator may extend the tail via the BIC-winning copula's marginal model". Some risk of label/behaviour drift (label says parametric tail; impl uses only empirical) — acceptable because the documentation is honest about it
- Test 3 (comonotone is the upper bound on a positive-dependence payoff with x*y or x^2 super-additive payoffs) is mathematically sound — Fréchet upper bound dominates independence for super-additive payoffs by the Hoeffding identity
- Empirical inverse CDF via `np.interp(uniforms, np.linspace(0,1,n), np.sort(observed))` — standard rank-transform; n_samples=10_000 default Monte-Carlo size
- divergence_pct uses `abs(mean_price)` denominator and short-circuits to 0.0 when mean is exactly zero — defensible numerical guard
- Test 4 (divergence_flag thresholding) tests BOTH >30 and <30 cases — symmetric coverage of the flag boundary
- Reproducibility: same seed → identical price triple (Test 5) — same byte-identity discipline as Plan 04-02

## Recommendation

Accept.
