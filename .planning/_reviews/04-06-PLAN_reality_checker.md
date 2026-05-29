## VERDICT

PASS

## Scope

`notes/usdt_depeg_calibration.md` (literature_range_stipulation framing + non-citation discipline) + `load_calibration` YAML frontmatter parser + `generate_lhs_samples` via `scipy.stats.qmc.LatinHypercube` N=64 ±50% + 5 tests.

## Findings

- Non-citation discipline triple-enforced: doc body explicitly says "does NOT cite Hernandez Cruz 2024…" + acceptance gate row 14 greps `! grep -E "port from Hernandez Cruz|methodological_port"` + Makefile `phase-4-acceptance` target greps the same.
- `evidence_source` mismatch fails loud: `load_calibration` raises `ValueError` if frontmatter `evidence_source ≠ 'literature_range_stipulation'`. Documented in SUMMARY.
- LHS bounds-check correctly handles negative-base (`mu_J=-0.05`) via `np.minimum/maximum` of `base*(1±ratio)` — the test asserts `lo1 = min(...)`, `hi1 = max(...)`, accounting for sign flip.
- Seed determinism + different-seed-differs are both tested. `scipy.stats.qmc.LatinHypercube(d=3, seed=...)` is byte-deterministic.
- The 64-sample size against ±50% on 3 dimensions gives ≈ 64^(1/3) ≈ 4 cells per dimension — coarse but explicitly the locked size per CONTEXT.

## Reality check

Per CONTEXT.md `<decisions>`, condition 4 records `sensitivity_fragile: <bool>` if any LHS cell flips the gate decision under the σ_J upper-bound or other bracket extreme. But as flagged in the 04-04 review, the `gate_decision_func` default in `evaluate_condition_4_usdt_depeg` is permissive (always True) — so by construction, no cell can flip, `n_flips=0`, `sensitivity_fragile=false` is locked. This plan correctly produces the LHS samples (64 valid triples in the box), but the downstream consumer in 04-04 doesn't actually use them for flip detection. The "sensitivity bracket is the honesty mechanism" claim in CONTEXT becomes vacuous in v1.0 unless 04-04 or 04-08 inject a real per-cell decision rule. Per CONTEXT `<deferred>`, `sensitivity_fragile: true` is informational-only and doesn't gate Phase 5 — so the vacuity is intentional, not a bug. Worth re-stating: the LHS infrastructure is correct; the sensitivity *claim* in CONTEXT is aspirational without a real per-cell gate.

## Recommendation

Accept.
