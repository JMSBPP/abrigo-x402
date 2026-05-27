## VERDICT

PASS

## Scope

Reality check on DGP-03 (boundary-correct parametric bootstrap LR test, the load-bearing test statistic for the four-criterion gate and the plan most prone to silent wrong-null failure).

## Findings

- **Bootstrap simulates from the FITTED NULL, not the alternative.** `_simulate_nhpp_under_null` passes `adjacency=np.zeros((2, 2))` to `SimuHawkesExpKernels` with `baseline=nhpp_baseline_per_sec` derived from the fitted INAR(p) intercept. This is the single most common Phase-3 silent-failure mode and the plan gets it right — the test_null_distribution_mixture_shape assertion (≥ some point mass at 0 AND ≥ some continuous tail) would catch a Hawkes-as-null misconfiguration.
- SC-3 grep gate (`! grep -rE 'likelihood_ratio_test|chi2\(1\)\.sf' lr_test.py`) is operationalized as a `subprocess` call inside `test_grep_gate_forbidden_calls_absent` — the test runs in CI, not just at scaffold time.
- Deterministic seed via `sha256(panel_dataHash + b"phase-3-bootstrap").digest()[:4]` as uint32 (big-endian). CONTEXT.md says `[:8]` of the hex string; plan uses `digest()[:4]` of bytes. Both yield uint32 (4 bytes = 8 hex chars). This is the gsd-plan-checker INFO note — semantically equivalent and the implementation choice is defensible.
- `PRODUCTION_N_REPS: int = 1000` constant is grep-gated visible (no CLI override at production-fit time per AF-04). Tests use n_reps=50/200 with documented runtime trade-off.
- Headless `matplotlib.use("Agg")` is set BEFORE `pyplot` import — passes the grep `matplotlib.use."Agg"` acceptance criterion AND avoids the import-order trap that bites people when running pytest under uv.
- Pitfall 9 (`force_simulation=True`) absent — grep acceptance criterion `returns 0`.

## Reality check

The most realistic failure mode is bootstrap reps silently failing en masse: `_simulate_nhpp_under_null` filters `sim_0.size < 10 or sim_1.size < 10` to `n_failed`, and the surrounding `try/except` catches any tick/statsmodels error. On a degenerate panel where many bootstrap draws produce sparse legs, `n_failed` could approach `n_reps` and `valid.size` could be near 0 — yet `p_value = mean(valid >= LR_observed)` would still return a number in [0, 1], and `rejects_at_alpha` would be `False` (vacuous PASS of the gate). The plan records `n_failed` in the result dict but the four-criterion gate evaluator in 03-07 does not check it — a high-failure run looks identical to a clean run with low LR observed.

## Recommendation

Accept. The DGP-03 core invariants (simulate-from-null, grep gate, deterministic seed) are correct. The n_failed-not-checked-by-gate issue is a 03-07 concern, not a 03-03 fix.
