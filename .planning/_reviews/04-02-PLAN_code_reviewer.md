## VERDICT

PASS

## Scope

Code-reviewer pass on Plan 04-02 (Wave 2: `permutation_null_max_abs_rho` 1000-rep within-window shuffle on rescaled_dt, p_value continuity correction, 4 unit tests).

## Findings

- Frontmatter: `wave: 2`, `depends_on: [pre, "00", "01"]` — correctly bumped to Wave 2 because of the `key_links` import edge from `cross_correlogram.py` (Plan 04-01, wave 1). The plan body explicitly calls out the sequencing: "Per standard wave semantics `wave = max(deps_wave) + 1`, this plan is wave 2 (04-01 is wave 1)." Honors the wave graph acyclicity invariant
- `files_modified` only touches `permutation_null.py` + its test — disjoint from 04-01
- Test statistic + null + p-value formula all pinned verbatim from PRE_REGISTRATION §Test Statistics: `n_reps=1000` default, `max|ρ(h)|` over the lag grid, within-window shuffle of `leg_1`, `p_value = (1 + sum(perm_max >= observed_max)) / (n_reps + 1)` continuity correction — the +1 correction is documented in the SUMMARY output as an explicit decision
- Default seed `20260527` locked for byte-identity discipline; test 4 (reproducibility) enforces `r1["p_value"] == r2["p_value"]` exactly
- Test 3 (power — cross-excitation) reuses the same Phase 3 fixture as Plan 04-01 with the same inter-arrival-times proxy; same graceful `pytest.skip` on missing fixture
- Acceptance: `grep -q "from abrigo_x402.dependence.cross_correlogram import" permutation_null.py` enforces the composition with 04-01 (no copy-paste of the cross-correlogram math into this module)
- Substrate discipline carried forward: `grep -q "rescaled_dt"` acceptance criterion mirrors Plan 04-01; PITFALLS §4 is the cited justification
- Wave-2 timing means the iter-1 W1 "wave assignments" concern (mentioned in the harness prompt as "on-disk verified already correct") is honored — `04-02` is wave 2, NOT wave 1, despite the original W1 warning's concern

## Recommendation

Accept.
