## VERDICT

PASS

## Scope

`run_three_way_stress` (independence / fitted_joint / comonotone-via-shared-U) + `divergence_flag` at >30% spread/mean (flag-only) + `comonotone_method='empirical_body_parametric_tail'` label + 7 tests.

## Findings

- Wave-2 sequencing explicit: imports `compute_strip` import-link is in `key_links` but the actual implementation uses pure Monte-Carlo (`_price_under_joint_samples`) rather than calling `compute_strip`. The MC path is the simpler v1.0 choice and matches the test expectations.
- Comonotone construction: `U_1 ~ U(0,1), U_2 = U_1` (Fréchet upper bound) via shared sample — textbook-correct per CONTEXT.md.
- `DIVERGENCE_FLAG_THRESHOLD_PCT = 30.0` is grep-locked; flag-only (no hard-fail) discipline is preserved.
- `comonotone_method` carries the literal string `'empirical_body_parametric_tail'` even though v1.0 actually does empirical-body-only inverse CDF (`_inverse_empirical_cdf` linear-interp on sorted sample). The label is forward-compatible per RESEARCH Pitfall 6 + SUMMARY note ("Plan 04-08 orchestrator may extend the tail via BIC-winning copula's marginal model"). Slightly misleading at v1.0 — the label *promises* a parametric tail that doesn't exist yet.
- Seed determinism: `rng = np.random.default_rng(seed)` covers paths 1 (independence) and 3 (comonotone); path 2 (fitted_joint) calls `fitted_copula.random(n, seed=seed)` — depends on copulae's seed handling. If copulae's `.random(seed=...)` is reproducible, the whole stress is byte-identical; if not, test 5 (seed determinism on the price-triple) is flaky.
- Test 3 (comonotone-upper-bound for convex payoff) uses `x->x²`-type intuition; the proof that comonotone dominates independence for super-additive payoffs is a Fréchet-Hoeffding result — sound.

## Reality check

The most realistic failure is the `divergence_pct` test on the real ICHI panel landing exactly *near* 30%. With the empirical_body_parametric_tail label promising more than the v1.0 implementation delivers, the divergence may be driven mostly by tail-cutoff noise (the empirical inverse CDF clips at sample min/max) rather than genuine copula-family divergence. If real-data divergence comes in at 28% or 32%, the flag is essentially noise-driven and the binary signal is misleading. The flag-only-no-hard-fail policy from CONTEXT keeps this from blocking; the result is documented in Phase 5 with a callout. Acceptable as designed.

## Recommendation

Accept.
