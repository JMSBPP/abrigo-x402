---
phase: 04-cross-leg-dependence-l5-falsification-carr-madan-strip-l6
plan: 05
subsystem: hedge
tags: [wave-1, hedge-02, carr-madan, fft, strip-degenerate, iter-3-reason-field, af-03-consumer]
dependency-graph:
  requires:
    - "04-pre commit 2dc3877 (PRE_REGISTRATION §Carr-Madan Grid Numerical Tolerances — 0.001 tolerance + 2^11->2^12 + abort-to-strip_degenerate)"
    - "04-00 commit 2485320 (scaffold: REQUIRED_STRIP_KEYS + STRIP_DEGENERATE_KEYS + POSITIVITY_TOLERANCE forward-declared)"
  provides:
    - "compute_strip(payoff, char_func) — FFT-based Carr-Madan strip with single-step 2^11->2^12 escalation and abort-to-degenerate"
    - "STRIP_DEGENERATE_KEYS now includes `reason` field (iter-3 Issue 1) for null_strip_unavailable fourth-firing-condition routing"
    - "scripts/lint_artifacts.py STRIP_DEGENERATE_REQUIRED_KEYS synced with new `reason` field"
  affects:
    - "Plan 04-08 (orchestrator) — consumes strip dict / strip_degenerate dict; reads `reason` to call null_result.decide_firing_condition with the fourth firing condition"
    - "Plan 04-09 (acceptance gate) — greps for `Carr & Madan 2001` citation and verifies anti-pattern grep gate remains green"
tech-stack:
  added: []
  patterns:
    - "Pattern 5 (polymorphic payoff Callable[[np.ndarray], np.ndarray] for v2.0 streaming-tokenization) baked into compute_strip signature"
    - "Anti-pattern docstring discipline (Phase 3 Plan 03-00 + Phase 4 Plan 04-00 precedent) — never name prohibited tokens even in module docstring; paraphrase by description"
key-files:
  created: []
  modified:
    - analysis/src/abrigo_x402/hedge/carr_madan_strip.py
    - analysis/tests/test_carr_madan_strip.py
    - scripts/lint_artifacts.py
decisions:
  - "DEFAULT_U_MAX = 200.0 — Fourier-domain truncation bound chosen so Gaussian fixture (sigma=1) iFFT recovers a density with <1e-12 negative mass at 2^11 (orders of magnitude tighter than the 0.001 acceptance threshold) while keeping dk = 2π / (n_grid · du) coarse enough that the k-grid spans ~30 units symmetrically — sufficient resolution for the v1.0 linear-forward payoff and for typical Hawkes-driven char-funcs in Phase 4 fits."
  - "Pathological degenerate fixture is `phi(u) = exp(-|u|^0.3) - 0.5 * exp(-|u|^0.1)` (a *difference* of slow-decay envelopes — NOT Bochner-positive-definite). Empirically yields ~10.9% negative mass at both 2^11 and 2^12, exhausting the single escalation and exercising the abort-to-strip_degenerate path. The original plan-body fixture `slow_decay_char_func(alpha=0.3)` is a valid (positive-definite) stable-law characteristic function and so does NOT produce negative iFFT mass under our DEFAULT_U_MAX — auto-fix applied (Rule 1 — Bug: test fixture did not exercise the intended degenerate path)."
  - "lint_artifacts.py STRIP_DEGENERATE_REQUIRED_KEYS frozenset synced with new `reason` field — required because the scaffold-time test_required_keys_sync.py (NON-skip) caught the drift immediately. Without the sync update, any subsequent strip_degenerate.json on disk would fail `make lint-artifacts`."
metrics:
  duration: "5min"
  completed: "2026-05-27T18:10:53Z"
  files-modified: 3
  tests-passing: "7/7 (test_carr_madan_strip.py) + 5/5 (test_required_keys_sync.py)"
  commits: 2
---

# Phase 04 Plan 05: HEDGE-02 Carr-Madan FFT Strip Summary

**One-liner:** Implemented `compute_strip(payoff, char_func)` as a FFT-only Carr-Madan static-replication strip with single-step 2^11→2^12 grid escalation and abort-to-`strip_degenerate.json` (carrying iter-3 `reason: positivity_fail_after_2_12` field for the fourth HEDGE-05 firing condition), passing the locked 0.001 positivity tolerance from the AF-03 PRE_REGISTRATION amendment.

## Commits

| Commit  | Subject                                                                                                                     |
| ------- | --------------------------------------------------------------------------------------------------------------------------- |
| 989987c | test(04-05): RED — Carr-Madan compute_strip success + escalation + degenerate + polymorphic payoff + anti-pattern grep + iter-3 reason field + Carr-Madan citation grep |
| 9e2090f | feat(04-05): GREEN — FFT-based Carr-Madan strip + 2^11->2^12 escalation + abort-to-strip_degenerate (PRE_REG 0.001 tolerance) |

## What Landed

### compute_strip implementation

`analysis/src/abrigo_x402/hedge/carr_madan_strip.py` — full FFT-based Carr-Madan static-replication strip with the following surface:

- **Polymorphic payoff**: `payoff: Callable[[np.ndarray], np.ndarray]` (RESEARCH Pattern 5 — v2.0 streaming-tokenization ready; v1.0 caller passes `linear_payoff`, v2.0 will pass `stream_pv_payoff` unchanged).
- **Default grid**: `DEFAULT_N_GRID = 2**11` (2048 points).
- **Single-step escalation**: `ESCALATED_N_GRID = 2**12` (4096 points), at `max_escalations=1`.
- **Positivity tolerance**: `POSITIVITY_TOLERANCE = 0.001` (PRE_REGISTRATION amendment `2dc3877`); locked metric is `∑ q(k)⁻ / ∑ |q(k)|`.
- **Fourier-domain truncation**: `DEFAULT_U_MAX = 200.0`. Rationale recorded in decisions above.
- **Anti-pattern discipline**: numpy FFT primitives only (`np.fft.fft`, `np.fft.ifft`, `np.fft.fftshift`, `np.fft.ifftshift`); scipy quadrature routines and numpy trapezoidal integration NEVER appear in source (carr-madan-anti-pattern-gate pre-commit hook PASS).
- **Abort-to-degenerate**: on exhausted escalation, returns the strip_degenerate schema with `reason: "positivity_fail_after_2_12"` (iter-3 Issue 1 fourth-firing-condition routing); does NOT silently fall back to COS or PROJ (CONTEXT.md HEDGE-02 lock). The `recommended_method` field merely *flags* which alternative the Phase 5 report should document.
- **Decay-rate proxy**: `_estimate_char_func_decay_rate` log-log slope on `u ∈ {1, 10, 100}` for strip_degenerate.json provenance.
- **Recommendation router**: `_recommend_alternative_method(decay)` — slope > -0.5 → "none"; -1.5 < slope ≤ -0.5 → "PROJ"; slope ≤ -1.5 → "COS".

### Carr-Madan 2001 citation

Module docstring cites verbatim "Carr & Madan 2001, 'Towards a Theory of Volatility Trading'" alongside the canonical strip-replication formula:

  `Strip price = f(F) + ∫_0^F p(K) f''(K) dK + ∫_F^∞ c(K) f''(K) dK`

For the v1.0 linear-forward payoff `f(S)=S`, `f''=δ(K-F)` collapses both integrals — the FFT computes a single density quadrature labelled `strip_prices`. For v2.0 streaming-PV payoffs the integrals contribute non-trivially and the same FFT density kernel is reused.

### Test suite (7 functions)

`analysis/tests/test_carr_madan_strip.py` — `pytestmark = pytest.mark.skip` removed; 7 active tests:

| # | Test                                              | Path exercised                       |
| - | ------------------------------------------------- | ------------------------------------ |
| 1 | `test_strip_schema_success_gaussian_baseline`     | Success at 2^11; Gaussian fixture    |
| 2 | `test_strip_escalation_to_2_12`                   | Pass-through OR escalation OR abort  |
| 3 | `test_strip_degenerate_path`                      | Abort to strip_degenerate            |
| 4 | `test_polymorphic_payoff_call_option`             | Pattern 5 — call_option_payoff       |
| 5 | `test_anti_pattern_grep_no_scipy_quad_no_trapz`   | Source-level grep gate enforcement   |
| 6 | `test_strip_degenerate_reason_field`              | iter-3 reason="positivity_fail_after_2_12" |
| 7 | `test_carr_madan_citation_grep`                   | "Carr & Madan 2001" in module        |

All 7 pass. `test_required_keys_sync.py` (5/5 PASS) confirms the lint frozenset mirror is in sync with the source module after the `reason` field addition.

### Per-attempt grid sizes recorded

- **2^11 = 2048 points** — DEFAULT_N_GRID; first attempt.
- **2^12 = 4096 points** — ESCALATED_N_GRID; second (and final) attempt under `max_escalations=1`.

### Empirical fixture-to-path mapping

| Fixture                                                                          | 2^11 neg_frac | 2^12 neg_frac | Path                |
| -------------------------------------------------------------------------------- | ------------- | ------------- | ------------------- |
| `gaussian_char_func(sigma=1.0)` (linear payoff)                                  | ~0.000000     | (not reached) | Success at 2^11     |
| `slow_decay_char_func(alpha=1.5)` (linear payoff; PSD)                           | ~0.000000     | (not reached) | Success at 2^11     |
| `pathological_non_psd_char_func()` = exp(-\|u\|^0.3) − 0.5·exp(-\|u\|^0.1)       | ~0.109034     | ~0.109059     | Abort → degenerate  |
| Gaussian char_func (call_option payoff)                                          | ~0.000000     | (not reached) | Success at 2^11     |

The Gaussian fixture exercises the success path; the non-PSD mixture-difference fixture exercises the abort-to-degenerate path. The escalation-only path (fail at 2^11, pass at 2^12) is structurally accommodated by the implementation but is empirically rare — Test 2 (the escalation test) accepts any of {success at 2^11, success at 2^12, abort to degenerate} per the plan-body acceptance criteria.

## Verification Output

```
$ cd analysis && uv run pytest tests/test_carr_madan_strip.py -v | tail -11
tests/test_carr_madan_strip.py::test_strip_schema_success_gaussian_baseline PASSED
tests/test_carr_madan_strip.py::test_strip_escalation_to_2_12 PASSED
tests/test_carr_madan_strip.py::test_strip_degenerate_path PASSED
tests/test_carr_madan_strip.py::test_polymorphic_payoff_call_option PASSED
tests/test_carr_madan_strip.py::test_anti_pattern_grep_no_scipy_quad_no_trapz PASSED
tests/test_carr_madan_strip.py::test_strip_degenerate_reason_field PASSED
tests/test_carr_madan_strip.py::test_carr_madan_citation_grep PASSED
======================== 7 passed, 1 warning in 1.50s =========================

$ cd analysis && uv run pytest tests/test_required_keys_sync.py -v | tail -7
tests/test_required_keys_sync.py::test_joint_dist_keys_sync PASSED
tests/test_required_keys_sync.py::test_gate_report_keys_sync PASSED
tests/test_required_keys_sync.py::test_stress_report_keys_sync PASSED
tests/test_required_keys_sync.py::test_strip_keys_sync PASSED
tests/test_required_keys_sync.py::test_strip_degenerate_keys_sync PASSED
============================== 5 passed in 0.01s ===============================
```

### Acceptance grep gate sweep (all PASS)

```
ANTIPATTERN_GATE       : ! grep -E "scipy\.integrate\.(quad|fixed_quad|romberg)|np\.trapz" -> exit non-zero  : PASS
FFT_PRIMITIVE          : grep -q "np.fft.fft\|np.fft.ifft"                                                   : PASS
POSITIVITY_TOLERANCE   : grep -q "POSITIVITY_TOLERANCE.*=.*0\.001"                                           : PASS
DEFAULT_N_GRID         : grep -q "DEFAULT_N_GRID.*=.*2\*\*11"                                                : PASS
ESCALATED_N_GRID       : grep -q "ESCALATED_N_GRID.*=.*2\*\*12"                                              : PASS
POLYMORPHIC_PAYOFF     : grep -q "payoff: Callable"                                                          : PASS
NO_STUB                : ! grep -q "NotImplementedError"                                                     : PASS
CARR_MADAN_CITATION    : grep -q "Carr & Madan 2001"                                                         : PASS
REASON_FIELD           : grep -q '"reason"'                                                                  : PASS
REASON_VALUE           : grep -q "positivity_fail_after_2_12"                                                : PASS
CANONICAL_LL_GATE      : ! grep -rE "loglik_in_sample_raw|tick\.score\(" analysis/src/abrigo_x402/hedge/     : PASS
```

### Pre-commit hook output (GREEN commit `9e2090f`)

```
AF-01..AF-12 anti-feature lint gate (GOV-03)                                                  : Passed
SC-2 grep gate (no usdc literals outside comments in hedge/falsification.py)                  : Passed
Carr-Madan integration anti-pattern gate (no scipy.integrate.quad / np.trapz)                 : Passed
Canonical-LL contract gate (no loglik_in_sample_raw in hedge/*)                               : Passed
Hardcoded jump-diffusion params gate (params only live in usdt_depeg.py + notes/...)          : Passed
```

## AF-03 Ordering Invariant Discharged

- Plan 04-pre amendment commit `2dc3877` (2026-05-27T17:44:37Z) predates this GREEN commit `9e2090f` (2026-05-27T18:11Z) by ~27 minutes on the same branch.
- The 0.001 tolerance constant, 2^11→2^12 single-escalation policy, and abort-to-strip_degenerate.json fallback are all cited verbatim in the implementation module docstring (PRE_REGISTRATION §Carr-Madan Grid Numerical Tolerances bullet 4 honored).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan-body degenerate fixture did not exercise the abort path**

- **Found during:** Task 2 GREEN verification (test_strip_degenerate_path FAILED: "missing degenerate key: max_negative_value" — result had success-schema keys instead).
- **Issue:** Plan body Test 3 instructs to use `slow_decay_char_func(alpha=0.3)` for the degenerate path. Empirically, `phi(u) = exp(-|u|^0.3)` IS a Bochner-positive-definite function (stable-law characteristic function with α=0.3), so its iFFT remains non-negative and the positivity tolerance check passes trivially — the abort path is never reached. The test therefore fell into the success branch and asserted on degenerate-only keys.
- **Fix:** Added a second, genuinely-pathological fixture `pathological_non_psd_char_func()` returning `phi(u) = exp(-|u|^0.3) - 0.5 * exp(-|u|^0.1)` — a *difference* of slow-decay envelopes, NOT positive-definite. Empirically yields ~10.9% negative mass at both 2^11 and 2^12, exhausting the single escalation. Tests 3 and 6 (degenerate-path + reason-field) updated to use this fixture; Test 2 (escalation) retains the original `slow_decay_char_func(alpha=1.5)` and accepts any of the three permitted paths.
- **Files modified:** `analysis/tests/test_carr_madan_strip.py` (fixture addition + Tests 3 and 6 retargeted).
- **Commit:** Squashed into GREEN commit `9e2090f`.
- **Rationale:** Honors the plan's stated *intent* (exercise the abort-to-strip_degenerate path) while correcting the mathematical mis-specification of the original fixture. The 04-05 plan body acknowledges in `<acceptance_criteria>` that the test design is to construct a char_func with ≥0.1% negative mass at both grid sizes — `slow_decay_char_func(alpha=0.3)` does not satisfy this in practice; the mixture-difference fixture does.

**2. [Rule 3 - Blocking] lint_artifacts.py STRIP_DEGENERATE_REQUIRED_KEYS drift**

- **Found during:** Task 2 GREEN verification (test_strip_degenerate_keys_sync FAILED: source module added `"reason"` to STRIP_DEGENERATE_KEYS but lint frozenset still listed 11 keys).
- **Issue:** Adding the `reason` field to STRIP_DEGENERATE_KEYS in `carr_madan_strip.py` (mandated by iter-3 Issue 1 for the null_strip_unavailable fourth-firing-condition routing) created drift between the source tuple and the lint frozenset mirror in `scripts/lint_artifacts.py`. The scaffold-time `test_required_keys_sync.py` invariant correctly caught this immediately.
- **Fix:** Added `"reason"` to `STRIP_DEGENERATE_REQUIRED_KEYS` in `scripts/lint_artifacts.py` with an inline comment citing iter-3 Issue 1.
- **Files modified:** `scripts/lint_artifacts.py`.
- **Commit:** Bundled with GREEN commit `9e2090f`.
- **Rationale:** Rule-3 blocking — without the sync update, `make lint-artifacts` would fail on any future strip_degenerate.json on disk (and the scaffold-time invariant test would block the commit). This is the documented pattern (Phase 4 Plan 04-00 §"Pattern G — REQUIRED_*_KEYS + lint frozenset mirror") for keeping the source tuple and lint frozenset in lock-step.

No other deviations — the implementation followed the plan body sketch.

## Forward Reference

Plan 04-08 (Wave 2 orchestrator) is the immediate consumer:

- Calls `compute_strip(payoff, char_func)` after the four-condition falsification gate (Plan 04-04) PASSES.
- Injects PANEL-02 provenance keys (`chainId`, `contractAddress`, `blockRange`, `fetchTimestamp`, `dataHash`, `gitCommit`, `run_id`) into the returned dict before writing to `data/fits/ichi/<run_id>/strip.json` or `strip_degenerate.json`.
- On strip_degenerate, reads the `reason` field and passes it to `null_result.decide_firing_condition` — value `"positivity_fail_after_2_12"` (from compute_strip itself) OR `"build_failed_upstream"` (injected by orchestrator if `_build_char_func_from_winner` raised) both route to firing condition (d) `null_strip_unavailable`.

Plan 04-09 (Wave 3 acceptance gate) verifies:

- `grep -q "Carr & Madan 2001" analysis/src/abrigo_x402/hedge/carr_madan_strip.py` exits 0.
- `! grep -E "scipy\.integrate\.(quad|fixed_quad|romberg)|np\.trapz" analysis/src/abrigo_x402/hedge/carr_madan_strip.py` exits 0.
- All Phase 4 hedge/dependence commits postdate the AF-03 amendment commit `2dc3877`.

## Self-Check: PASSED

```
FOUND: analysis/src/abrigo_x402/hedge/carr_madan_strip.py (193 lines, fully implemented, no NotImplementedError)
FOUND: analysis/tests/test_carr_madan_strip.py (7 active tests, no pytest.mark.skip)
FOUND: scripts/lint_artifacts.py (STRIP_DEGENERATE_REQUIRED_KEYS includes "reason")
FOUND: commit 989987c in git log (RED)
FOUND: commit 9e2090f in git log (GREEN)
FOUND: "Carr & Madan 2001" literal in module docstring (1 hit)
FOUND: "positivity_fail_after_2_12" literal in source (2 hits — constant + return-dict assignment)
FOUND: "reason" literal in source (3 hits — STRIP_DEGENERATE_KEYS, REASON_POSITIVITY_FAIL doc, return dict)
VERIFIED: 7/7 test_carr_madan_strip.py tests pass
VERIFIED: 5/5 test_required_keys_sync.py tests pass
VERIFIED: all 4 pre-commit grep gates pass on GREEN commit
VERIFIED: AF-03 ordering invariant — 2dc3877 (2026-05-27T17:44:37Z) predates 9e2090f (2026-05-27T18:11Z)
```
