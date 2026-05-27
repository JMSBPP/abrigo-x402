## VERDICT

PASS

## Scope

`permutation_null_max_abs_rho` 1000-rep within-window shuffle on rescaled_dt; max|ρ(h)| statistic; `(1+k)/(n+1)` continuity-corrected p-value; 4 tests (schema, size, power, reproducibility).

## Findings

- Wave-2 sequencing explicitly documented in the `<objective>`: imports `cross_correlogram_event_index` from 04-01; orchestrator must land 04-01 first. Iter-1 gsd-plan-checker W1 verified.
- p-value formula `(1 + sum(perm_max >= observed_max)) / (n_reps + 1)` correctly uses continuity correction; locked in SUMMARY output for forward audit.
- `default_rng(seed)` reproducibility test is the byte-identity discipline gate (no BLAS thread-pin needed here because the permutation generator is numpy-native, not BLAS-routed).
- Power test uses `synthetic_hawkes_eta_05.parquet` inter-arrival proxy (same caveat as 04-01); n_reps=500 for the test (production default 1000). Acceptable.
- Default n_reps=1000 grep-locked against PRE_REGISTRATION §Test Statistics (`grep -qE "n_reps.*[:=].*1000"`).

## Reality check

The 1000-rep permutation loop calls `cross_correlogram_event_index` in-loop with a 101-lag scalar inner loop (04-01). At N=10,000 events × 1000 reps × 101 lags ≈ 10^9 elementary ops — on the real ICHI panel this is a 30s–2min wall-clock cost on a single core. Not a correctness risk but a latency risk against VALIDATION's 300s per-wave target. If the real ICHI panel has fewer events (~5,000) it's fine; if more (~30,000) the permutation test alone could blow the wave budget. The plan doesn't ship a vectorized rewrite. Low blocker since Phase 3 STRADDLE expectation makes the real panel smallish, but flag for monitoring.

## Recommendation

Accept.
