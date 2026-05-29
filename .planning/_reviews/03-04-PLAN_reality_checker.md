## VERDICT

PASS

## Scope

Reality check on DGP-04 (wall-clock 80/20 temporal split + held-out log-likelihood for NHPP and Hawkes + InsufficientEvaluationError + ±25% baseline stationarity diagnostic).

## Findings

- Split is wall-clock (`t_split = window_start + 0.80 * (window_end - window_start)`), NOT event-count. `test_wallclock_NOT_event_count_split` deliberately front-loads 900/1000 events into the first half — an event-count split would put ~800 events in the train segment regardless of front-loading, while a wall-clock split puts 900 there. The assertion `held_out_leg_0.size < 0.20 * total_events` catches a regression to `np.array_split` or `iloc[:int(n*0.8)]`.
- `InsufficientEvaluationError` raised in two places: `wall_clock_split(held_out_fraction=0.0)` and `compute_held_out_loglik_*(test_window_start=None, ...)`. Both paths covered by `test_in_sample_only_raises`.
- Hawkes held-out log-likelihood passes `full_history_leg_*` (train + held-out) into `_hawkes_intensity_at` for the kernel sum, while integrating only over `[W_start=test_window_start, W_end]`. This correctly preserves self-excitation continuity across the split — a common bug is dropping pre-split history and underestimating intensity on the early held-out events.
- Stationarity diagnostic returns `{train_rate, held_out_rate, ratio, decision, threshold, per_leg_decision}`; the ±25% threshold (`STATIONARITY_RATIO_THRESHOLD = 0.25`) is grep-gated.
- Zero-train-rate safety branch returns `ratio=inf, decision='piecewise_required'` instead of NaN-propagating.

## Reality check

The most realistic failure is the closed-form integral in `_hawkes_integrated_intensity` being O(n_events × n_history) — for each prior event `t_jk`, a Python-level loop over `hist` runs without vectorization. On the synthetic Hawkes(η=0.5) 30-day fixture (~700 events/leg) this is fine, but the `break` clause (`if tjk >= W_end: break`) assumes `hist` is sorted; the function calls `np.sort(full_history_leg_*)` at the call site in `compute_held_out_loglik_hawkes`, so the assumption holds. The subtler bug is that for ties (`tjk == W_end`), the integral lower bound `lo = max(W_start, float(tjk))` becomes `W_end` and the term evaluates to `exp(0) - exp(0) = 0` — silently dropping the tied event's contribution. With block-level tie counts already surfaced in 03-07's `tie_counts` diagnostic this is auditable, but not asserted by any test in this plan.

## Recommendation

Accept. DGP-04 invariants are met; the tie-edge integral behavior is a known-and-documented edge case worth a follow-up note but not a blocker.
