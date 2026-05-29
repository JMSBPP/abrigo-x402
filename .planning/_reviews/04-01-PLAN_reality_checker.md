## VERDICT

PASS

## Scope

`cross_correlogram_event_index` Bowsher-2007 event-index lag-domain implementation on rescaled_dt substrate + 4 RED/GREEN tests.

## Findings

- Substrate discipline locked: rescaled_dt (Phase 3 DGP-05 output), not raw timestamps — honors PITFALLS §4 verbatim. The grep acceptance check `grep -q "rescaled_dt"` enforces docstring documentation.
- The full-sample-norm denominator convention (Bowsher-2007: same denominator across all lags) is documented in code comments and locked in the SUMMARY output — comparable across lags, intentional divergence from naive per-lag-renorm.
- Independence baseline tolerance `< 0.15` at N=1000 with max-over-101-lags is loose but defensible — under H0 the maximum of 101 sample correlations concentrates above the per-lag √(1/N)≈0.032 distribution; 0.15 is comfortable.
- Test 3 (cross-excitation positive control) uses inter-arrival times as a proxy for rescaled_dt because the fixture stores raw event times. Note documented in the test comment — acceptable, but the *real* integration on residuals.parquet only fires at Plan 04-08.
- Vectorization left as scalar loop over lags (101 iterations) — RESEARCH §"Don't Hand-Roll" suggested full-vectorize. Acceptable: 101 lags × full numpy correlation is microsecond-scale; the bottleneck is the 1000-rep permutation loop in Plan 04-02 which calls this in-loop.

## Reality check

The most realistic failure is in test 3: the synthetic Hawkes fixture's inter-arrival-time proxy may not show max|ρ| > 0.05 at the locked seed depending on Phase 3's `synthetic_hawkes_eta_05.parquet` (η=0.5 branching ratio). If the actual fixture has weaker cross-excitation than expected, test 3 fails or skips; if stronger and clustered at lag 0, the `max-lag within ±5` check still holds. The plan's `pytest.skip` guard on missing fixture is correct, but a flaky-power assertion (0.05 threshold against a fixed-seed Hawkes sim) is one of the more brittle assertions in the wave. Low blocker risk because test 3 is one of four.

## Recommendation

Accept.
