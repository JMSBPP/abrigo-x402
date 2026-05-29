---
phase: 04-cross-leg-dependence-l5-falsification-carr-madan-strip-l6
plan: 00
subsystem: scaffold
tags: [wave-0, scaffold, dependence, hedge, falsification, carr-madan, hedge-05, lint, pre-commit]
dependency-graph:
  requires:
    - "04-pre commit 2dc3877 (AF-03 amendment to notes/PRE_REGISTRATION.md — Carr-Madan grid tolerances + 2^11->2^12 escalation policy)"
    - "Phase 3 dgp/ canonical re-export pattern + REQUIRED_FIT_REPORT_KEYS tuple shape + provenance.with_header / assert_has_header API"
    - "Phase 2 conftest.py fixture pattern (extension, not replacement)"
  provides:
    - "dependence/* + hedge/* canonical Wave-1 symbol surface (NotImplementedError stubs); Wave 1 plans 04-01..04-07 can import every symbol they own"
    - "Three HEDGE-05 firing-condition fixture triplets (null_cost / null_lr / null_convex)"
    - "Quarto null-result template with dual signature markers"
    - "Five-track lint extension (joint_dist + gate_report + stress_report + strip + strip_degenerate)"
    - "Four new pre-commit grep gates (SC-2 USDC, Carr-Madan anti-pattern, canonical-LL, hardcoded-jump-params)"
  affects:
    - "Wave 1 plans 04-01..04-07 (parallel-landable now)"
    - "Wave 2 plan 04-08 (depends on all of Wave 1)"
    - "Wave 3 plan 04-09 (acceptance gate)"
tech-stack:
  added:
    - "copulae==0.8.0 (5-family BIC menu — Gaussian, Student-t, Clayton, Frank, Gumbel)"
    - "jupyter (dev — for Wave-2 diagnostic notebooks per Plan 04-08)"
  patterns:
    - "Pattern G (REQUIRED_*_KEYS + lint frozenset mirror) replicated for 5 new artifact classes"
    - "Pattern I (thread-pinning header for SC-5 byte-identity) carried verbatim to test_byte_identical_phase_4.py"
    - "Pattern 5 (polymorphic payoff signature for v2.0 streaming tokenization) baked into compute_strip"
    - "Sequential firing-condition decision tree (cost -> lr -> convex -> strip-unavailable) in null_result.py"
key-files:
  created:
    - analysis/src/abrigo_x402/dependence/__init__.py
    - analysis/src/abrigo_x402/dependence/cross_correlogram.py
    - analysis/src/abrigo_x402/dependence/permutation_null.py
    - analysis/src/abrigo_x402/dependence/copula.py
    - analysis/src/abrigo_x402/hedge/__init__.py
    - analysis/src/abrigo_x402/hedge/falsification.py
    - analysis/src/abrigo_x402/hedge/carr_madan_strip.py
    - analysis/src/abrigo_x402/hedge/stress_test.py
    - analysis/src/abrigo_x402/hedge/usdt_depeg.py
    - analysis/src/abrigo_x402/hedge/null_result.py
    - analysis/src/abrigo_x402/hedge/orchestrator.py
    - analysis/tests/test_cross_correlogram.py
    - analysis/tests/test_permutation_null.py
    - analysis/tests/test_copula_bic.py
    - analysis/tests/test_falsification.py
    - analysis/tests/test_carr_madan_strip.py
    - analysis/tests/test_stress_test.py
    - analysis/tests/test_usdt_depeg_lhs.py
    - analysis/tests/test_null_result_template.py
    - analysis/tests/test_joint_dist_provenance.py
    - analysis/tests/test_gate_report_provenance.py
    - analysis/tests/test_stress_report_provenance.py
    - analysis/tests/test_byte_identical_phase_4.py
    - analysis/tests/test_required_keys_sync.py
    - analysis/tests/fixtures/hedge_05_null_cost/{fit_report.json,gate_report.json,cost_leg_bound.md}
    - analysis/tests/fixtures/hedge_05_null_lr/{fit_report.json,gate_report.json,cost_leg_bound.md}
    - analysis/tests/fixtures/hedge_05_null_convex/{fit_report.json,gate_report.json,cost_leg_bound.md}
    - reports/_templates/null_result.qmd
    - reports/_templates/_evidence_branches.qmd
    - analysis/INSTALL_TROUBLESHOOTING.md
    - analysis/README.md
  modified:
    - analysis/tests/conftest.py
    - scripts/lint_artifacts.py
    - Makefile
    - analysis/pyproject.toml
    - analysis/uv.lock
    - .pre-commit-config.yaml
decisions:
  - "copulae==0.8.0 installed (wheel reports metadata 0.8.0 although __version__ attribute lags at 0.7.9 — internal version-string mismatch, 5-family API intact; not a blocker)"
  - "pyvinecopulib NOT installed per RESEARCH Open Question 3 — install in a v1.1 follow-up plan if Wave-1 empirical fit triggers ΔBIC≥5 vine fallback"
  - "decide_firing_condition implements FOUR firing conditions including null_strip_unavailable (iter-3 fourth branch), matching the Quarto template's params surface"
  - "_pit_with_clipping(eps=1e-10) helper present in dependence/copula.py per iter-3 fix (Archimedean LL boundary blow-up prevention)"
  - "Carr-Madan docstring deliberately avoids the prohibited token names (scipy.integrate.quad / np.trapz) — the pre-commit grep gate is at the line level and would trip on docstring mentions"
metrics:
  duration: "11 min (scaffold + sync + validation + commit)"
  completed: "2026-05-27"
  files-created: 31
  files-modified: 6
  tests-collected: 137
  tests-passing: "5/5 sync tests"
---

# Phase 04 Plan 00: Wave 0 Scaffold — Phase 4 dependence + hedge + HEDGE-05 fixtures Summary

**One-liner:** Created the full Phase 4 import graph (11 source modules + 13 test stubs + 9 fixture files + 1 Quarto template + 5 config edits) at canonical Wave-1 symbol surface, with `copulae==0.8.0` installed, all 4 pre-commit grep gates active, and the scaffold-time `test_required_keys_sync.py` invariant (5/5 PASS) catching REQUIRED_*_KEYS drift before Wave 1 lands.

## Commit

| Commit  | Subject                                                                                       |
| ------- | --------------------------------------------------------------------------------------------- |
| 2485320 | scaffold(04-00): Phase 4 dependence + hedge module skeletons + HEDGE-05 fixtures + lint extension + pre-commit gates |

## What Landed

### Source modules (11 files)

`analysis/src/abrigo_x402/dependence/`:
- `__init__.py` — canonical re-exports
- `cross_correlogram.py` — `cross_correlogram_event_index` stub
- `permutation_null.py` — `permutation_null_max_abs_rho` stub
- `copula.py` — `fit_5_families_bic` + `REQUIRED_JOINT_DIST_KEYS` + `VINE_FALLBACK_DELTA_BIC_THRESHOLD=5.0` + `_pit_with_clipping`

`analysis/src/abrigo_x402/hedge/`:
- `__init__.py` — canonical re-exports
- `falsification.py` — four `evaluate_condition_N_*` stubs + `evaluate_four_conditions` composite + `REQUIRED_GATE_REPORT_KEYS`
- `carr_madan_strip.py` — `compute_strip` stub + `REQUIRED_STRIP_KEYS` + `STRIP_DEGENERATE_KEYS` + `POSITIVITY_TOLERANCE=0.001`
- `stress_test.py` — `run_three_way_stress` stub + `REQUIRED_STRESS_REPORT_KEYS` + `DIVERGENCE_FLAG_THRESHOLD_PCT=30.0`
- `usdt_depeg.py` — `load_calibration`, `generate_lhs_samples`, `run_lhs_sensitivity` stubs + `DEFAULT_{LAMBDA_J,MU_J,SIGMA_J}` + `JUMP_PARAMS_DEFAULT` triple
- `null_result.py` — `decide_firing_condition` (4-condition sequential tree) + `render_null_result_pdf` stubs + `HEDGE05_SIGNATURE="HEDGE05-NULL-RESULT-V1"`
- `orchestrator.py` — `run_hedge` stub + `_build_char_func_from_winner` + `CHAR_FUNC_SOBOL_N=2**16`

### Test stubs (13 files)

12 skip-marked import-smoke tests at canonical Wave-1 symbol surface (one per Wave-1 plan owner).

1 NON-skip-marked test: `test_required_keys_sync.py` runs at Wave 0 and asserts every `REQUIRED_*_KEYS` tuple in dependence/hedge modules equals the corresponding `*_REQUIRED_KEYS` frozenset in `scripts/lint_artifacts.py`. 5/5 sync tests PASS.

`test_byte_identical_phase_4.py` carries Pattern I thread-pinning verbatim (four `os.environ.setdefault` calls on lines 10-13, before any numpy/statsmodels/scipy/copulae import).

### HEDGE-05 fixture triplets (9 files)

Three directories under `analysis/tests/fixtures/hedge_05_*/`, each with `fit_report.json + gate_report.json + cost_leg_bound.md`. Each triplet forces exactly one HEDGE-05 firing condition via the sequential decision tree (cost -> lr -> convex):

| Triplet      | cost-leg verdict | lr p_value | gate.any_condition_passed | Firing condition  |
| ------------ | ---------------- | ---------- | ------------------------- | ----------------- |
| null_cost    | FAIL             | 0.001      | true                      | `null_cost`       |
| null_lr      | PASS             | 0.5        | true                      | `null_lr`         |
| null_convex  | PASS             | 0.001      | false                     | `null_convex`     |

### Quarto template (2 files)

`reports/_templates/null_result.qmd` with dual signature markers:
- Visible H1: `# HEDGE-05 NULL RESULT — \`r params$firing_condition\``
- LaTeX header: `\pdfinfo{ /HEDGE05Marker (HEDGE05-NULL-RESULT-V1) }`

`reports/_templates/_evidence_branches.qmd` is a Wave-2 placeholder for the four firing-condition branches.

### Lint extension

`scripts/lint_artifacts.py` extended with 5 new frozensets (JOINT_DIST / GATE_REPORT / STRESS_REPORT / STRIP / STRIP_DEGENERATE), 5 per-artifact linters, and a `lint_phase_4_artifacts` walker wired into `main()`. Dormant pre-Wave-2 (no artifacts on disk yet); `make lint-artifacts` exits 0.

### Config edits

- `Makefile`: 3 new targets — `render-null-result-pdf` / `render-strip-diagnostic` / `phase-4-acceptance`
- `analysis/pyproject.toml`: `+copulae==0.8.0`, `+jupyter` (dev)
- `analysis/uv.lock`: regenerated by `uv sync`
- `.pre-commit-config.yaml`: 4 new local grep gates

## Verification Output

```
$ cd analysis && uv run pytest --collect-only -q | tail -3
========================= 137 tests collected in 1.05s =========================

$ cd analysis && uv run pytest tests/test_required_keys_sync.py -v | tail -10
tests/test_required_keys_sync.py::test_joint_dist_keys_sync PASSED       [ 20%]
tests/test_required_keys_sync.py::test_gate_report_keys_sync PASSED      [ 40%]
tests/test_required_keys_sync.py::test_stress_report_keys_sync PASSED    [ 60%]
tests/test_required_keys_sync.py::test_strip_keys_sync PASSED            [ 80%]
tests/test_required_keys_sync.py::test_strip_degenerate_keys_sync PASSED [100%]
============================== 5 passed in 0.01s ===============================

$ cd analysis && uv run python -c "from abrigo_x402.dependence import *; from abrigo_x402.hedge import *; assert HEDGE05_SIGNATURE == 'HEDGE05-NULL-RESULT-V1'; assert POSITIVITY_TOLERANCE == 0.001; assert DIVERGENCE_FLAG_THRESHOLD_PCT == 30.0; print('OK')"
OK

$ make lint-artifacts | tail -2
lint-artifacts: scanning data/raw/ichi/ for PANEL-02 + data/fits/ for SC-1...
lint_artifacts: 1 parquet PASS PANEL-02

$ cd analysis && uv run python -c "import copulae; print('copulae', copulae.__version__)"
copulae 0.7.9
$ cd analysis && uv pip list | grep -i copula
copulae                       0.8.0
```

(Copulae note: `pip` metadata reports 0.8.0 — the installed wheel — but the package's internal `__version__` attribute lags at 0.7.9. The 5-family API is intact. Not a blocker; documented in INSTALL_TROUBLESHOOTING.md.)

### Pre-commit grep gates

All 4 new gates clean on the scaffold:

```
SC-2 USDC gate                : PASS (no USDC literals in falsification.py)
Carr-Madan anti-pattern gate  : PASS (no quadrature names in carr_madan_strip.py)
Canonical-LL gate             : PASS (no loglik_in_sample_raw in hedge/)
Hardcoded jump-params gate    : PASS (params only in usdt_depeg.py)
```

## AF-03 Ordering Confirmation

```
2dc3877  2026-05-27 13:48  docs(pre-reg): AF-03 amendment — Carr-Madan grid 0.1% positivity tolerance + 2^11->2^12 escalation + abort-to-strip_degenerate.json fallback (Phase 4 prerequisite)
d9bdb72  2026-05-27 13:48  docs(04-pre): complete AF-03 Carr-Madan tolerance amendment plan
2485320  2026-05-27 13:59  scaffold(04-00): Phase 4 dependence + hedge module skeletons + HEDGE-05 fixtures + lint extension + pre-commit gates
```

AF-03 amendment precedes this scaffold by 11 minutes. Invariant preserved: this commit is strictly later than the PRE_REGISTRATION amendment on the same branch.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Carr-Madan docstring tripped its own anti-pattern grep gate**

- **Found during:** STEP 13 (post-write grep gate verification)
- **Issue:** The Carr-Madan module's docstring literally listed the prohibited tokens (`scipy.integrate.quad`, `np.trapz`) to explain what NOT to use; the pre-commit grep gate is line-level and matched the docstring.
- **Fix:** Rewrote the docstring + function docstring to reference the anti-patterns by description ("scipy quadrature routines, numpy trapezoidal integration") without naming the exact regex tokens.
- **Files modified:** `analysis/src/abrigo_x402/hedge/carr_madan_strip.py` (docstrings only — no symbol-surface change)
- **Commit:** Squashed into scaffold commit `2485320`
- **Pattern:** Same class as Phase 3 Plan 03-00 Rule-1 fix (SC-3 grep gate tripping on lr_test.py docstring naming the prohibited functions verbatim).

No other deviations — the plan executed as written.

## Forward Reference

Plans 04-01..04-07 may now land in parallel:

- **04-01** — DEPEND-01 cross-correlogram (owns `dependence/cross_correlogram.py` + `test_cross_correlogram.py`)
- **04-02** — DEPEND-01 permutation null (owns `dependence/permutation_null.py` + `test_permutation_null.py`)
- **04-03** — DEPEND-01 5-family BIC + joint_dist provenance (owns `dependence/copula.py` + `test_copula_bic.py` + `test_joint_dist_provenance.py`)
- **04-04** — HEDGE-01 four-condition gate + gate_report provenance (owns `hedge/falsification.py` + `test_falsification.py` + `test_gate_report_provenance.py`)
- **04-05** — HEDGE-02 Carr-Madan strip (owns `hedge/carr_madan_strip.py` + `test_carr_madan_strip.py`)
- **04-06** — HEDGE-03 USDT depeg LHS (owns `hedge/usdt_depeg.py` + `test_usdt_depeg_lhs.py`)
- **04-07** — HEDGE-04 three-way stress + stress_report provenance (owns `hedge/stress_test.py` + `test_stress_test.py` + `test_stress_report_provenance.py`)

Plan 04-08 (Wave 2) depends on all of Wave 1 — wires the hedge orchestrator, HEDGE-05 firing decision, and Quarto rendering.
Plan 04-09 (Wave 3) is the Phase 4 acceptance gate.

## Self-Check: PASSED

Created files verified on disk:

```
FOUND: analysis/src/abrigo_x402/dependence/__init__.py
FOUND: analysis/src/abrigo_x402/dependence/cross_correlogram.py
FOUND: analysis/src/abrigo_x402/dependence/permutation_null.py
FOUND: analysis/src/abrigo_x402/dependence/copula.py
FOUND: analysis/src/abrigo_x402/hedge/__init__.py
FOUND: analysis/src/abrigo_x402/hedge/falsification.py
FOUND: analysis/src/abrigo_x402/hedge/carr_madan_strip.py
FOUND: analysis/src/abrigo_x402/hedge/stress_test.py
FOUND: analysis/src/abrigo_x402/hedge/usdt_depeg.py
FOUND: analysis/src/abrigo_x402/hedge/null_result.py
FOUND: analysis/src/abrigo_x402/hedge/orchestrator.py
FOUND: analysis/tests/test_required_keys_sync.py (NON-skip; 5/5 PASS)
FOUND: analysis/tests/fixtures/hedge_05_null_cost/{fit_report.json,gate_report.json,cost_leg_bound.md}
FOUND: analysis/tests/fixtures/hedge_05_null_lr/{fit_report.json,gate_report.json,cost_leg_bound.md}
FOUND: analysis/tests/fixtures/hedge_05_null_convex/{fit_report.json,gate_report.json,cost_leg_bound.md}
FOUND: reports/_templates/null_result.qmd (dual signature markers verified)
FOUND: analysis/INSTALL_TROUBLESHOOTING.md (3 fallback paths)
FOUND: commit 2485320 in git log
FOUND: AF-03 amendment commit 2dc3877 predates 2485320 by 11 minutes
```
