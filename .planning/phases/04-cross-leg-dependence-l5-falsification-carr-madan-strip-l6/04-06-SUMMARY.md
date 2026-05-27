---
phase: 04-cross-leg-dependence-l5-falsification-carr-madan-strip-l6
plan: 06
subsystem: hedge
tags: [wave-1, hedge, hedge-03, calibration, lhs, sensitivity, literature_range_stipulation, scipy.qmc]
dependency-graph:
  requires:
    - "04-00 scaffold (commit 2485320 — usdt_depeg.py stub + JUMP_PARAMS_DEFAULT + LHS_N_SAMPLES=64 + LHS_BOUND_RATIO=0.5 + LHS_SEED=20260527 constants pre-locked)"
    - "04-pre AF-03 amendment (commit 2dc3877 — PRE_REGISTRATION numerical-tolerances precedent)"
    - "CONTEXT.md commit e600d3a — literature_range_stipulation framing replaces 'methodological_port'"
    - "RESEARCH §Pitfall 1 — Hernandez Cruz 2024 + Wu & Liu 2026 NOT jump-diffusion parameter sources"
  provides:
    - "notes/usdt_depeg_calibration.md — load-bearing calibration doc with evidence_source: literature_range_stipulation + base triple (λ=0.05/yr, μ_J=-0.05, σ_J=0.02) + N=64 LHS bracket spec"
    - "load_calibration(path) -> {evidence_source, base_triple} (YAML frontmatter parser; fail-loud ValueError on evidence_source != 'literature_range_stipulation')"
    - "generate_lhs_samples(...) -> (64, 3) float64 via scipy.stats.qmc.LatinHypercube(d=3, seed=...) + qmc.scale with min/max-normalized bounds for negative-base μ_J"
    - "_resolve_calibration_path helper — repo-root-relative path resolution so the same `notes/usdt_depeg_calibration.md` literal works from analysis/ pytest cwd and repo-root CLI cwd alike"
  affects:
    - "Plan 04-04 (evaluate_condition_4_usdt_depeg already landed via concurrent agent; this plan provides its calibration substrate)"
    - "Plan 04-08 (orchestrator wires load_calibration + run_lhs_sensitivity into gate_report.json's condition_4.evidence dict)"
    - "Plan 04-09 (acceptance gate verifies non-citation discipline + reproducibility seed)"
tech-stack:
  added:
    - "pyyaml (already in dev deps via copulae transitive — load_calibration uses yaml.safe_load on the frontmatter)"
    - "scipy.stats.qmc.LatinHypercube (already in locked scipy 1.17.1)"
  patterns:
    - "Pattern G (REQUIRED_*_KEYS) NOT applied here — calibration doc carries YAML frontmatter for human-readability, not a JSON SC-1 header (different artifact class)"
    - "Bounds-min/max normalization for negative-base LHS parameters (handles μ_J = -0.05 -> bounds [-0.075, -0.025] correctly, not the inverted [-0.025, -0.075])"
    - "Repo-root-walk path resolution helper (`_resolve_calibration_path`) — graceful fallback when callers supply repo-root-relative paths from analysis/ cwd"
key-files:
  created:
    - notes/usdt_depeg_calibration.md
  modified:
    - analysis/src/abrigo_x402/hedge/usdt_depeg.py
    - analysis/tests/test_usdt_depeg_lhs.py
decisions:
  - "load_calibration is fail-loud on evidence_source != 'literature_range_stipulation' (no silent fallback to other evidence sources); raised as ValueError with the canonical label in the message"
  - "Bounds for LHS are computed as min(base*(1-r), base*(1+r)) / max(...) per dimension to handle negative bases (μ_J = -0.05) correctly — no sign-of-base branching"
  - "Repo-root-walk path resolution in load_calibration() — `notes/usdt_depeg_calibration.md` default works whether pytest runs from analysis/ or the orchestrator runs from repo root"
  - "run_lhs_sensitivity remains a NotImplementedError stub (deferred to Plan 04-08 orchestrator wiring per Wave-0 scaffold's canonical Wave-1 symbol surface promise) — the plan body's `! grep -q NotImplementedError` acceptance criterion conflicts with the scaffold contract and is documented as a deviation below"
metrics:
  duration: "7 min (doc + RED tests landed via concurrent agent + GREEN implementation + verification + summary)"
  completed: "2026-05-27"
  files-created: 1
  files-modified: 2
  tests-collected: 5
  tests-passing: "5/5 test_usdt_depeg_lhs.py"
---

# Phase 04 Plan 06: HEDGE-03 USDT Depeg Calibration + N=64 LHS Sensitivity Summary

**One-liner:** Created the HEDGE-03 calibration substrate per the corrected CONTEXT.md commit-e600d3a discipline — `notes/usdt_depeg_calibration.md` carries the stipulated base triple `(λ=0.05/yr, μ_J=-0.05, σ_J=0.02)` with explicit non-citation of Hernandez Cruz 2024 / Wu & Liu 2026 (RESEARCH Pitfall 1), and `hedge/usdt_depeg.py` implements `load_calibration` (YAML frontmatter parser with fail-loud `evidence_source == 'literature_range_stipulation'` check) + `generate_lhs_samples` (scipy.stats.qmc.LatinHypercube N=64 ±50%, with min/max-normalized bounds so negative-base μ_J produces `[-0.075, -0.025]` correctly).

## Commits

| Commit  | Subject                                                                                                                                                            |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| ef64540 | docs(04-06): USDT depeg calibration — literature_range_stipulation base triple + N=64 LHS bracket (non-citation discipline per RESEARCH Pitfall 1)                 |
| 57b2997 | test(04-03 cross-bundle): RED — load_calibration + generate_lhs_samples behavior tests (5 tests landed by concurrent Plan 04-03 executor — see Deviation 1 below)  |
| d14e2ee | feat(04-06): GREEN — load_calibration (YAML frontmatter parser) + generate_lhs_samples (scipy.stats.qmc.LatinHypercube N=64 ±50%)                                  |

## What Landed

### Calibration Doc (1 file)

`notes/usdt_depeg_calibration.md` — 68-line markdown with YAML frontmatter carrying:
- `evidence_source: literature_range_stipulation` (load-bearing key — `load_calibration` raises ValueError on any other value)
- `base_triple: {lambda_J: 0.05, mu_J: -0.05, sigma_J: 0.02}` (Merton 1976 stablecoin-class defaults)
- `sensitivity: {n_samples: 64, bound_ratio: 0.5, seed: 20260527}` (reproducibility lock)
- `calibrated_date: 2026-05-27`

Body contains verbatim the non-citation discipline mandated by CONTEXT.md §"USDT-depeg jump-leg calibration (HEDGE-03)":

> "Base triple stipulated from literature-range Merton 1976 defaults for stablecoin-class jumps. NOT calibrated from cited primary data — Hernandez Cruz 2024 and Wu & Liu 2026 do not publish jump-diffusion parameters; cited only as methodological-context references for stablecoin tail-risk discussion. Sensitivity bracket (±50% N=64 Latin hypercube) is the uncertainty mechanism."

Non-citation grep gates ALL PASS:
- `! grep -q "port from Hernandez Cruz" notes/usdt_depeg_calibration.md` → exit 0
- `! grep -q "methodological_port" notes/usdt_depeg_calibration.md` → exit 0
- `! grep -q "calibrated from Hernandez Cruz" notes/usdt_depeg_calibration.md` → exit 0
- `! grep -q "calibrated from Wu & Liu" notes/usdt_depeg_calibration.md` → exit 0
- `grep -q "literature_range_stipulation" notes/usdt_depeg_calibration.md` → exit 0

### Source module (`analysis/src/abrigo_x402/hedge/usdt_depeg.py`)

Replaced 2 of 3 `NotImplementedError` stubs from the Wave-0 scaffold:

**`load_calibration(calibration_path) -> dict`** — Parses YAML frontmatter via `re.match(r"---\n(.*?)\n---", text, re.DOTALL)` + `yaml.safe_load`. Returns `{evidence_source, base_triple: {lambda_J, mu_J, sigma_J}}`. Raises `ValueError` if frontmatter is missing OR if `evidence_source != "literature_range_stipulation"` (fail-loud — no silent fallback to other evidence sources).

**`generate_lhs_samples(...) -> np.ndarray`** — `scipy.stats.qmc.LatinHypercube(d=3, seed=seed).random(n=n_samples)` followed by `qmc.scale(unit, l_bounds=min(base*(1-r), base*(1+r)), u_bounds=max(...))`. The min/max normalization is the critical detail: μ_J = -0.05 yields raw bounds `(base*0.5, base*1.5) = (-0.025, -0.075)` which is INVERTED. Min/max produces the correct `[-0.075, -0.025]` interval. Returns `(64, 3)` float64.

**`_resolve_calibration_path(path) -> Path`** — Helper that resolves relative paths against the cwd first, then walks up from the module to find a parent containing the target. Lets `load_calibration("notes/usdt_depeg_calibration.md")` work from pytest's `analysis/` cwd AND from the orchestrator's repo-root cwd uniformly.

**`run_lhs_sensitivity(...)`** — Remains a `NotImplementedError` stub (deferred to Plan 04-08 orchestrator wiring per the Wave-0 scaffold's canonical Wave-1 symbol surface promise; see Deviation 2 below).

### Tests (`analysis/tests/test_usdt_depeg_lhs.py`)

5 tests, all PASS:
- `test_load_calibration_roundtrip` — doc on disk → dict with evidence_source + base_triple matching `DEFAULT_LAMBDA_J/MU_J/SIGMA_J` constants
- `test_lhs_shape` — `generate_lhs_samples()` returns `(64, 3)` float64
- `test_lhs_bounds_within_50pct` — every cell within `[base*(1-r), base*(1+r)]` per dimension (with min/max normalization for negative-base μ_J)
- `test_lhs_seed_determinism` — same seed twice → `np.array_equal(s1, s2)` True
- `test_lhs_different_seed_differs` — different seeds → samples differ

## Verification Output

```
$ cd analysis && uv run pytest tests/test_usdt_depeg_lhs.py -v | tail
tests/test_usdt_depeg_lhs.py::test_load_calibration_roundtrip PASSED     [ 20%]
tests/test_usdt_depeg_lhs.py::test_lhs_shape PASSED                      [ 40%]
tests/test_usdt_depeg_lhs.py::test_lhs_bounds_within_50pct PASSED        [ 60%]
tests/test_usdt_depeg_lhs.py::test_lhs_seed_determinism PASSED           [ 80%]
tests/test_usdt_depeg_lhs.py::test_lhs_different_seed_differs PASSED     [100%]
========================= 5 passed, 1 warning in 0.99s =========================

$ cd analysis && uv run python -c "
> from abrigo_x402.hedge.usdt_depeg import load_calibration, generate_lhs_samples
> cal = load_calibration('notes/usdt_depeg_calibration.md')
> print('load_calibration:', cal)
> samples = generate_lhs_samples()
> print(f'LHS shape: {samples.shape}, dtype: {samples.dtype}')
> print(f'lambda_J range: [{samples[:,0].min():.4f}, {samples[:,0].max():.4f}]')
> print(f'mu_J range:     [{samples[:,1].min():.4f}, {samples[:,1].max():.4f}]')
> print(f'sigma_J range:  [{samples[:,2].min():.4f}, {samples[:,2].max():.4f}]')
> "
load_calibration: {'evidence_source': 'literature_range_stipulation', 'base_triple': {'lambda_J': 0.05, 'mu_J': -0.05, 'sigma_J': 0.02}}
LHS shape: (64, 3), dtype: float64
lambda_J range: [0.0251, 0.0748]
mu_J range:     [-0.0750, -0.0251]
sigma_J range:  [0.0102, 0.0300]
```

Bounds confirmed for all three dimensions:
- λ_J ∈ [0.0250, 0.0750] (base 0.05 ±50%)
- μ_J ∈ [-0.0750, -0.0250] (base -0.05 ±50%, min/max-normalized — NOT inverted)
- σ_J ∈ [0.0100, 0.0300] (base 0.02 ±50%)

### Fail-loud `load_calibration` confirmation

```
$ uv run python -c "
> from abrigo_x402.hedge.usdt_depeg import load_calibration
> # ... write a temp doc with evidence_source: primary_calibration ...
> load_calibration('/tmp/bad.md')
> "
ValueError: /tmp/tmpo1mqj7i5.md: evidence_source must be 'literature_range_stipulation'
                                  per CONTEXT.md commit e600d3a (got 'primary_calibration')
```

ValueError raised as required by the success criterion "Fail-loud `ValueError` if `load_calibration()` is called expecting `evidence_source != 'literature_range_stipulation'`".

### Pre-commit grep gates

All 4 Phase-4 pre-commit gates PASS on the GREEN commit (`d14e2ee`):

```
SC-2 USDC gate                : PASS
Carr-Madan anti-pattern gate  : PASS
Canonical-LL gate             : PASS
Hardcoded jump-params gate    : PASS (defaults remain in usdt_depeg.py + the calibration doc only)
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Concurrent Plan 04-03 executor bundled test_usdt_depeg_lhs.py into its RED commit**

- **Found during:** Task 2 RED commit attempt (pre-commit hook tripped on canonical-ll-gate due to concurrent Plan 04-04 WIP in `falsification.py` working-tree; investigating, discovered that a parallel executor had already committed my exact `test_usdt_depeg_lhs.py` content as part of commit `57b2997` titled `test(04-03): RED — fit_5_families_bic + joint_dist provenance tests`).
- **Issue:** Three concurrent plan executors (04-03, 04-04, 04-06) were running in parallel against a shared working tree. The 04-03 executor's `git add` glob captured `test_usdt_depeg_lhs.py` along with its own test files, embedding this plan's RED tests into 04-03's commit message.
- **Fix:** Verified that the committed content of `test_usdt_depeg_lhs.py` at `57b2997` matches exactly what this plan would have committed (byte-identical to the file I wrote). No code change needed — the tests are present in HEAD with the correct content, just under a misleading commit subject. Proceeded directly to GREEN.
- **Files modified:** None (the bundled commit already contained correct content).
- **Commit:** `57b2997` (concurrent executor — content is correct, subject line cross-references Plan 04-03 but the file genuinely belongs to 04-06).
- **Pattern note:** This is the first observed cross-plan commit bundling in a parallel Wave-1 execution. Mitigation for future waves: agent-level `git add <explicit-files-only>` discipline (already specified in commit protocol) prevents capture of unrelated WT modifications. The discipline was followed correctly in THIS plan's GREEN commit (`d14e2ee` carries only `usdt_depeg.py`).

**2. [Rule 1 - Bug] Plan acceptance criterion `! grep -q "NotImplementedError"` conflicts with scaffold contract**

- **Found during:** Post-GREEN verification (running the plan-body grep gates against the GREEN commit).
- **Issue:** The plan body's acceptance criterion `! grep -q "NotImplementedError" analysis/src/abrigo_x402/hedge/usdt_depeg.py` would fail because `run_lhs_sensitivity` remains a `NotImplementedError` stub. The objective says "replace two NotImplementedError stubs" (load_calibration + generate_lhs_samples), and the Wave-0 scaffold's canonical Wave-1 symbol surface promise locks `run_lhs_sensitivity` as a deferred symbol for Plan 04-08 orchestrator wiring.
- **Fix:** Kept `run_lhs_sensitivity` as a `NotImplementedError` stub per the scaffold contract; the plan-body criterion is documented here as inconsistent with the stated objective and the scaffold's symbol-surface lock. Plan 04-08 will fill in `run_lhs_sensitivity` when it wires the orchestrator's condition-4 evidence collection.
- **Files modified:** None (intentional non-action — the criterion was too strict).
- **Commit:** N/A (deviation from plan acceptance criterion, not from execution behavior).
- **Forward fix:** Plan 04-09 acceptance grid should scope the no-NotImplementedError gate to `load_calibration` + `generate_lhs_samples` symbols specifically, OR wait until 04-08 lands `run_lhs_sensitivity` before applying the gate at module-level.

**3. [Rule 3 - Blocking] Test file imported notes/usdt_depeg_calibration.md by relative path; pytest cwd is analysis/, doc lives at repo root**

- **Found during:** First GREEN test run (4/5 PASS — only `test_load_calibration_roundtrip` failed with `FileNotFoundError: notes/usdt_depeg_calibration.md`).
- **Issue:** The default `calibration_path="notes/usdt_depeg_calibration.md"` is repo-root-relative; pytest runs with cwd = `analysis/`, so the relative open() fails. The plan body locks the default path string but doesn't specify the resolution strategy.
- **Fix:** Added `_resolve_calibration_path(path) -> Path` helper that walks up from the module's `__file__` to find a parent directory containing the target. Lets the same default literal work from any cwd. Tests pass 5/5 with no change to the test file's argument.
- **Files modified:** `analysis/src/abrigo_x402/hedge/usdt_depeg.py` (one helper function added; absorbed into the GREEN commit `d14e2ee`).
- **Pattern:** Same class as Phase 3's path-resolution helpers in `orchestrator.py` that locate `data/fits/<run_id>/` from any cwd.

No other deviations — the plan executed as written modulo the three Rule-1/3 fixes above.

## Authentication Gates

None — this plan involves no auth-bearing operations.

## Forward Reference

Plan 04-06 outputs feed two downstream plans:

- **Plan 04-04** (HEDGE-01 four-condition gate — already landed via concurrent executor, commits `557a811` + `dd866fe`): `evaluate_condition_4_usdt_depeg` calls `load_calibration` to retrieve the stipulated base triple + `generate_lhs_samples` to draw the N=64 sensitivity bracket, then computes the gate decision per LHS cell. The any-cell-flip semantics (`sensitivity_fragile = any(flips)`) are evaluated inside 04-04's condition-4 routine.
- **Plan 04-08** (Wave 2 orchestrator): wires the calibration loader + LHS sampler + condition-4 verdict into `gate_report.json :: condition_4.evidence = {source: "literature_range_stipulation", base_triple: {...}, sensitivity_fragile: <bool>, sensitivity_summary: {n_samples: 64, n_flips: <int>, flip_examples: [...]}}`. Will also implement `run_lhs_sensitivity` (the currently-stubbed third function) once the gate-decision callable signature is locked.

## Self-Check: PASSED

Created files verified on disk:

```
FOUND: notes/usdt_depeg_calibration.md (68 lines)
FOUND: commit ef64540 in git log (docs)
FOUND: commit d14e2ee in git log (GREEN)
FOUND: commit 57b2997 in git log (concurrent-RED — see Deviation 1)
```

Source module state verified:

```
FOUND: load_calibration symbol in analysis/src/abrigo_x402/hedge/usdt_depeg.py (no NotImplementedError)
FOUND: generate_lhs_samples symbol in analysis/src/abrigo_x402/hedge/usdt_depeg.py (no NotImplementedError)
FOUND: qmc.LatinHypercube reference in analysis/src/abrigo_x402/hedge/usdt_depeg.py
FOUND: literature_range_stipulation literal in analysis/src/abrigo_x402/hedge/usdt_depeg.py
FOUND: 5/5 tests PASS in analysis/tests/test_usdt_depeg_lhs.py
FOUND: grep -q "literature_range_stipulation" notes/usdt_depeg_calibration.md exit 0
FOUND: ! grep -q "port from Hernandez Cruz" notes/usdt_depeg_calibration.md exit 0
FOUND: ! grep -q "methodological_port" notes/usdt_depeg_calibration.md exit 0
FOUND: ! grep -q "calibrated from Hernandez Cruz" notes/usdt_depeg_calibration.md exit 0
FOUND: ! grep -q "calibrated from Wu & Liu" notes/usdt_depeg_calibration.md exit 0
FOUND: load_calibration raises ValueError on evidence_source != literature_range_stipulation
FOUND: μ_J LHS range [-0.0750, -0.0251] (correctly normalized for negative base)
```
