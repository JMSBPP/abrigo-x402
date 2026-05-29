## VERDICT

PASS

## Scope

Code-reviewer pass on Plan 04-01 (Wave 1: `cross_correlogram_event_index` Bowsher-2007 event-index lag-domain ρ(h) on rescaled-time residuals, 4 unit tests).

## Findings

- Frontmatter: `wave: 1`, `depends_on: [pre, "00"]`, `files_modified` only touches `dependence/cross_correlogram.py` + its test file — disjoint from sibling Wave-1 plans 04-03/04/05/06
- Substrate discipline locked in `must_haves.truths`: "Substrate is residuals.parquet :: rescaled_dt per leg (PITFALLS §4 — NOT raw timestamps)" + `grep -q "rescaled_dt"` acceptance criterion — addresses Pitfall 4 (non-stationary baseline) head-on; the Bowsher-2007 event-index convention is explicitly tied to the Phase 3 DGP-05 output
- Test 3 (cross-excitation positive control) reads Phase 3 fixture `synthetic_hawkes_eta_05.parquet` via `polars` → `to_numpy().ravel().astype(np.float64)` — honors Phase 3 Pitfall 8 (polars 2-D shape) and gracefully skips on missing fixture (test resilience)
- The honest acknowledgement in Test 3 — "this fixture stores raw event times; for true rescaled_dt we would need to run Phase 3 time_rescaling on it. For the unit-test sanity check, we use inter-arrival times per leg as a proxy. Plan 04-08 integration test exercises the real residuals.parquet path." — is a fair compromise on a Wave-1 unit test that defers the substrate-fidelity check to Plan 04-08's orchestrator
- Implementation choice for the rho-per-lag denominator is `a_norm * b_norm` (full-sample norm — Bowsher 2007 convention) — documented in the function docstring + recorded in the SUMMARY output requirements ("Key implementation choice: full-sample norm denominator (Bowsher-2007 convention) vs per-shift norm")
- `ValueError` raised on `n_min <= 2*max_lag+1` is the correct fail-loud posture for an underdetermined cross-correlogram; no silent fallback
- TDD discipline: separate RED then GREEN commits with conventional prefixes `test(04-01): RED` / `feat(04-01): GREEN`; pre-commit hooks AF-01..AF-12 + AF-03 ordering invariant rechecked in acceptance
- Lag-grid is 2*max_lag+1=101 (default 50) and the zero-lag entry is centered at index 50 — test 1 enforces this explicitly

## Recommendation

Accept.
