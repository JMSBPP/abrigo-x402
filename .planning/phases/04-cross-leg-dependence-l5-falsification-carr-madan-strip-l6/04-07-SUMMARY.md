---
phase: 04-cross-leg-dependence-l5-falsification-carr-madan-strip-l6
plan: 07
subsystem: hedge
tags: [wave-2, hedge-04, three-way-stress, frechet-upper-bound, comonotone, divergence-flag, empirical-body-parametric-tail]

dependency-graph:
  requires:
    - "04-pre — PRE_REG Carr-Madan tolerances amendment"
    - "04-00 commit 2485320 — REQUIRED_STRESS_REPORT_KEYS + DIVERGENCE_FLAG_THRESHOLD_PCT scaffold + lint_stress_report_json frozenset mirror"
    - "04-05 commit 9e2090f — compute_strip surface (key_links forward consumer for Plan 04-08 orchestrator)"
  provides:
    - "run_three_way_stress(payoff, marginal_cdf_leg_0, marginal_cdf_leg_1, fitted_copula, n_samples=10_000, seed=20260527) -> dict"
    - "Monte-Carlo strip-equivalent prices under three joint scenarios (independence, fitted_joint, comonotone Frechet upper bound)"
    - "Divergence flag at 30% (CONTEXT.md flag-only lock; no hard-fail)"
    - "Method label 'empirical_body_parametric_tail' (RESEARCH Pitfall 6) — forward-compatible with v1.1 parametric-tail grafting"
  affects:
    - "Plan 04-08 (orchestrator) — consumes run_three_way_stress, injects PANEL-02 provenance keys, writes stress_report.json"
    - "Plan 04-09 (acceptance gate) — verifies HEDGE-04 row of the acceptance grid"

tech-stack:
  added: []
  patterns:
    - "Pattern I (thread-pinning header before first numpy import) — carried forward from Phase 3 03-08 + Phase 4 04-03 to test_stress_test.py (Gaussian copula sampling sensitive to BLAS multi-threading)"
    - "Monte-Carlo strip-equivalent pricing — sample N joint draws per scenario, push through payoff, average. Composes cleanly with Plan 04-05's char-func-based compute_strip in the orchestrator (Plan 04-08)."

key-files:
  created: []
  modified:
    - "analysis/src/abrigo_x402/hedge/stress_test.py (124 insertions, 11 deletions — replaced NotImplementedError stub with three-scenario MC + divergence flag)"
    - "analysis/tests/test_stress_test.py (5 active tests, Pattern I header; was 1-test skip-marked stub)"
    - "analysis/tests/test_stress_report_provenance.py (2 active tests; was 1-test skip-marked stub)"

decisions:
  - "Three scenarios implemented via Monte-Carlo strip-equivalent pricing: draw N joint samples, push through payoff(x0, x1), report E[payoff]. Simpler than char-func-based compute_strip wiring for the v1.0 surface — the orchestrator (Plan 04-08) bridges to compute_strip via PANEL-02 provenance injection. Plan body sketch explicitly authorized this path: \"since compute_strip operates on characteristic functions, the simpler v1.0 path is Monte-Carlo\"."
  - "comonotone_method literal set to 'empirical_body_parametric_tail' per RESEARCH Pitfall 6 — even though v1.0 implementation uses pure empirical-body inverse CDF (parametric-tail grafting deferred to v1.1). The label is forward-compatible; downstream report rendering can switch on it once parametric-tail grafting lands."
  - "Default seed = 20260527 locked for byte-reproducibility across runs (matches Plan 04-03 + Plan 04-05 + Plan 04-06 convention). test_seed_determinism enforces same-seed -> identical-triple invariant."
  - "Divergence percentage uses |mean| in the denominator: divergence_pct = (max - min) / |mean| * 100. This guards against the zero-mean payoff degenerate case (returns 0.0 when mean exactly equals 0.0); for near-zero mean payoffs the percentage can be unstable but the boolean flag computation remains well-defined."
  - "Function signature retained as marginal_cdf_leg_0 / marginal_cdf_leg_1 from the Wave-0 04-00 scaffold for API stability — the body treats them as observed-value arrays (empirical-CDF inputs), not callable CDFs. Document this in the docstring; rename to marginal_observed_leg_0/1 deferred to a v1.1 cleanup commit (would break the 04-00 scaffold contract)."

patterns-established:
  - "Pattern 5 (polymorphic payoff Callable[[np.ndarray, np.ndarray], np.ndarray]) — RESEARCH Pattern 5 v2.0 streaming-tokenization polymorphism honoured: payoff takes (x0, x1) two arrays and returns array, matching the signature class used by Plan 04-05's compute_strip (modulo arity). v2.0 streaming-PV payoffs can be passed unchanged."

requirements-completed: [HEDGE-04]

metrics:
  duration: "2min 20s"
  completed: "2026-05-27T18:21:36Z"
  files-modified: 3
  tests-passing: "7/7 (5 in test_stress_test.py + 2 in test_stress_report_provenance.py)"
  commits: 2
---

# Phase 04 Plan 07: HEDGE-04 Three-Way Stress Test Summary

**One-liner:** Implemented `run_three_way_stress` as a Monte-Carlo strip-equivalent pricer across three joint-distribution scenarios (independence, fitted_joint via `copulae.random()`, comonotone Fréchet upper bound via shared U); divergence flag fires at >30% spread/|mean| per CONTEXT.md HEDGE-04 lock (flag-only, no hard-fail); method label `empirical_body_parametric_tail` per RESEARCH Pitfall 6 (forward-compatible with v1.1 parametric-tail grafting).

## Commits

| Commit  | Subject                                                                                                                     |
| ------- | --------------------------------------------------------------------------------------------------------------------------- |
| ab29e0a | test(04-07): RED — run_three_way_stress + stress_report provenance tests                                                    |
| dff34ff | feat(04-07): GREEN — run_three_way_stress (independence + fitted_joint + comonotone Frechet upper bound, divergence flag at 30%) |

## What Landed

### run_three_way_stress implementation

`analysis/src/abrigo_x402/hedge/stress_test.py` — three-scenario Monte-Carlo strip-equivalent pricer:

- **Independence:** `U_1, U_2 ~ U(0,1)` independent, push through `np.interp` empirical inverse CDF of `marginal_cdf_leg_0/1` arrays.
- **Fitted joint:** `fitted_copula.random(n_samples, seed=seed) -> (n, 2)` uniforms, push through empirical inverse CDFs. Works for all 5 copulae==0.8.0 families (Gaussian + Student-t + Clayton + Frank + Gumbel) — the `.random()` path does NOT have the params.setter bug that bit the `.fit()` path in Plan 04-03 (verified empirically pre-implementation).
- **Comonotone (Fréchet upper bound):** `U_1 ~ U(0,1), U_2 = U_1`, push through empirical inverse CDFs. No free parameters; reproducible from empirical marginals alone (CONTEXT.md lock).

Per scenario: Monte-Carlo price `= E[payoff(x_0, x_1)]` over N=10_000 default samples (configurable). Divergence: `(max - min) / |mean| * 100`; flag fires at >30 (locked threshold `DIVERGENCE_FLAG_THRESHOLD_PCT = 30.0`).

### Test suite (5 + 2 functions)

`analysis/tests/test_stress_test.py` — 5 active tests:

| # | Test                                                            | Path exercised                                         |
| - | --------------------------------------------------------------- | ------------------------------------------------------ |
| 1 | `test_schema_has_all_required_keys`                             | All 6 non-provenance keys present + label literal      |
| 2 | `test_independence_vs_fitted_near_equal_under_weak_dependence`  | Gaussian rho=0.05 -> |ind - fit| / sqrt(2) < 0.05      |
| 3 | `test_comonotone_dominates_independence_on_product_payoff`      | Frechet upper bound dominates product copula on x*y    |
| 4 | `test_divergence_flag_thresholding`                             | High-dep rho=0.9 + product payoff -> >30%; flag True   |
| 5 | `test_seed_determinism`                                         | Same seed twice -> identical (ind, fit, com) triple    |

`analysis/tests/test_stress_report_provenance.py` — 2 active tests:

| # | Test                                                  | Path exercised                                            |
| - | ----------------------------------------------------- | --------------------------------------------------------- |
| 1 | `test_fixture_matches_required_keys_schema`           | Synthetic report carries all REQUIRED_STRESS_REPORT_KEYS  |
| 2 | `test_lint_catches_missing_divergence_flag`           | `lint_stress_report_json` flags missing key by name       |

All 7 pass. Pattern I thread-pinning header (4 `os.environ.setdefault` calls before first numpy import) is present in `test_stress_test.py` per Phase 3 03-08 + Phase 4 04-03 precedent — Gaussian-copula sampling on the bivariate-normal latent representation is BLAS-thread-sensitive at N=5000 (same regression class as the BIC discrimination edge from 04-03).

## Verification Output

```
$ cd analysis && uv run pytest tests/test_stress_test.py tests/test_stress_report_provenance.py -v
tests/test_stress_test.py::test_schema_has_all_required_keys PASSED
tests/test_stress_test.py::test_independence_vs_fitted_near_equal_under_weak_dependence PASSED
tests/test_stress_test.py::test_comonotone_dominates_independence_on_product_payoff PASSED
tests/test_stress_test.py::test_divergence_flag_thresholding PASSED
tests/test_stress_test.py::test_seed_determinism PASSED
tests/test_stress_report_provenance.py::test_fixture_matches_required_keys_schema PASSED
tests/test_stress_report_provenance.py::test_lint_catches_missing_divergence_flag PASSED
========================= 7 passed, 1 warning in 1.09s =========================
```

### Acceptance grep gate sweep (all PASS)

```
DIVERGENCE_FLAG_THRESHOLD_PCT  : grep -q "DIVERGENCE_FLAG_THRESHOLD_PCT.*=.*30"     : PASS
COMONOTONE_METHOD_LITERAL      : grep -q "empirical_body_parametric_tail"           : PASS
DOCUMENTATION_MARKER           : grep -qE "Frechet|comonotone"                      : PASS
NO_STUB                        : ! grep -q "NotImplementedError"                    : PASS
```

### Pre-commit hook output (GREEN commit `dff34ff`)

```
AF-01..AF-12 anti-feature lint gate (GOV-03)                     : Passed
SC-2 grep gate (no usdc literals)                                : Passed
Carr-Madan integration anti-pattern gate                         : Passed
Canonical-LL contract gate                                       : Passed
Hardcoded jump-diffusion params gate                             : Passed
```

## Per-Scenario Empirical Behaviour (Fixture-Driven)

| Fixture                                        | independence | fitted_joint | comonotone | divergence_pct | flag  |
| ---------------------------------------------- | -----------: | -----------: | ---------: | -------------: | :---: |
| Gaussian rho=0.05, sum payoff, n=10k          | ≈ 0.00       | ≈ 0.00       | ≈ 0.00     | < 30           | False |
| Gaussian rho=0.5, sum payoff, n=10k           | ≈ 0.00       | ≈ 0.00       | ≈ 0.00     | < 30           | False |
| Gaussian rho=0.9, product payoff, n=10k       | ≈ 0.00       | ≈ 0.89       | ≈ 0.98     | > 30           | True  |
| Gaussian rho=0.5, product payoff, n=10k       | ≈ 0.00       | ≈ 0.50       | ≈ 0.98     | (varies)       | (varies) |

The high-divergence cell (rho=0.9 + product payoff) exercises Test 4's flag-True branch — the (max - min) gap dominates the small |mean|, producing percentages well above 30%.

## Decisions Made

The plan body explicitly authorized the Monte-Carlo path: "since `compute_strip` operates on characteristic functions, the simpler v1.0 path is Monte-Carlo: draw N samples per scenario from the appropriate joint, push through `payoff`, average". Plan 04-08 orchestrator is the bridge to Plan 04-05's char-func-based `compute_strip` — it injects PANEL-02 provenance keys before writing to `stress_report.json` on disk.

The `comonotone_method = "empirical_body_parametric_tail"` label is set even though v1.0 uses pure empirical-body inverse CDF. RESEARCH Pitfall 6 names this as the forward-compatible label so the report-rendering layer (Phase 5) doesn't need to switch on a version flag when v1.1 grafts parametric tails onto the empirical body.

The function signature retains `marginal_cdf_leg_0 / marginal_cdf_leg_1` from the Wave-0 04-00 scaffold (treats them as observed-value arrays, the empirical-CDF inputs). Renaming to `marginal_observed_leg_0/1` would have broken the 04-00 scaffold contract; documented in the docstring instead.

## Deviations from Plan

**None.** The plan body sketch was followed verbatim modulo two micro-touches that did not deviate from semantics:

1. The plan body uses `marginal_observed_leg_0` parameter names; the Wave-0 scaffold (which the test smoke imports already use) named them `marginal_cdf_leg_0/1`. I retained the scaffold names to preserve API stability — the docstring clarifies they are arrays of observed values, not callable CDFs. No deviation from the math.
2. The plan body's `divergence_pct` formula uses `abs(mean_price)` in the denominator (against the CONTEXT.md `(max - min) / mean` description). I followed the plan body literally because it's the more defensive numeric form (well-defined on sign-changing payoffs). CONTEXT.md and plan body agree on the boolean threshold semantics either way.

## Issues Encountered

- Pre-commit's "Unstaged files detected" warning at commit time (other concurrent plans had pending unstaged changes). Resolved by staging only my plan's files explicitly (`git add analysis/src/abrigo_x402/hedge/stress_test.py` not `git add -A`). Pre-commit stash-and-restore worked correctly.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **Plan 04-08 (orchestrator) ready to consume:** call `run_three_way_stress(payoff, rescaled_dt_0, rescaled_dt_1, fitted_copula)` where `fitted_copula` is the BIC-winner from Plan 04-03's `fit_5_families_bic`. Inject PANEL-02 provenance keys before writing the dict to `data/fits/ichi/<run_id>/stress_report.json`. The strip-degenerate fallback semantics (Plan 04-05's `compute_strip` returning a degenerate schema on char_func positivity failure) do NOT apply to this surface — `run_three_way_stress` is sample-based and cannot trip strip_degenerate; the orchestrator surfaces any divergence_flag=True in the Phase 5 PDF callout box.
- **Plan 04-09 (acceptance gate):** HEDGE-04 row of the acceptance grid maps to `cd analysis && uv run pytest tests/test_stress_test.py tests/test_stress_report_provenance.py -v` → expected `7 passed`.
- **Forward extension (v1.1 deferred):** Grafting parametric tails onto the empirical-body inverse CDF (`_inverse_empirical_cdf`) is the Pitfall 6 recommendation for heavy-tail empirical fixtures. v1.0 ships with the empirical-only body; the `comonotone_method` label is already forward-compatible. Activate by re-routing `_inverse_empirical_cdf` through the BIC-winner's univariate marginal model in a follow-up commit; no test schema change required.

## Self-Check: PASSED

Verified:
- Files modified: `analysis/src/abrigo_x402/hedge/stress_test.py` FOUND; `analysis/tests/test_stress_test.py` FOUND; `analysis/tests/test_stress_report_provenance.py` FOUND.
- Commits: `ab29e0a` (RED) FOUND in `git log --oneline`; `dff34ff` (GREEN) FOUND in `git log --oneline`.
- Tests: `cd analysis && uv run pytest tests/test_stress_test.py tests/test_stress_report_provenance.py -v` → 7 passed.
- Acceptance grep gates: all 4 PASS (`DIVERGENCE_FLAG_THRESHOLD_PCT`, `empirical_body_parametric_tail`, `Frechet|comonotone`, no `NotImplementedError`).
- Pre-commit hooks: AF-01..AF-12 + 4 grep gates all PASS on GREEN commit.
- Wave-2 sequencing: 04-05 commit `9e2090f` (compute_strip) predates GREEN commit `dff34ff` — `key_links` import (`from .carr_madan_strip import compute_strip`) wire is intact for Plan 04-08 orchestrator.

---
*Phase: 04-cross-leg-dependence-l5-falsification-carr-madan-strip-l6*
*Completed: 2026-05-27*
