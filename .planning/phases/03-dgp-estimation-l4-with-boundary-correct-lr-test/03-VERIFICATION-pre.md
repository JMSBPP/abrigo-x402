---
phase: 03-dgp-estimation-l4-with-boundary-correct-lr-test
phase_number: 3
verification_pass: true
verified_at: "2026-05-27T03:50:37Z"
git_commit: "2e5ad5f8af18c99a726422836043045902c760e1"
requirements_covered: [DGP-01, DGP-02, DGP-03, DGP-04, DGP-05, DGP-06]
roadmap_success_criteria: [SC-1, SC-2, SC-3, SC-4, SC-5]
test_runner: "pytest 9.0.3"
total_tests_phase3: 39
total_test_files_phase3: 9
plans_complete: 9/9 (this plan = the 9th)
---

# Phase 3 — Pre-Verification Summary

Sampling commands executed in `/home/jmsbpp/apps/d2p/abrigo/abrigo-x402/` after the Wave-3 (Plan 03-08) commit `2e5ad5f` (`test(03-08): implement SC-5 byte-identical determinism test`). All numbers are from live `pytest` / `make` / `grep` invocations against the working tree at HEAD, not inferred.

Thread pinning convention for every Phase 3 invocation below: `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1`. This is load-bearing for SC-5 byte-identity (statsmodels VAR.select_order AIC drifts under multi-thread BLAS); see the SC-5 row Notes/Caveats for the full mechanism.

## Test infrastructure (DGP-01..06)

| Property | Value |
|---|---|
| Runner | `pytest@9.0.3` via `uv run` |
| Full-suite command | `cd analysis && uv run pytest tests/test_nhpp_inar.py tests/test_hawkes_fit.py tests/test_lr_test.py tests/test_held_out.py tests/test_stationarity.py tests/test_time_rescaling.py tests/test_profile_likelihood.py tests/test_fit_artifact_provenance.py tests/test_byte_identical.py` |
| Test files (Phase 3) | 9 |
| Tests | 39 passing, 0 failing, 0 skipped |
| Full-suite duration | ~127 s wall-clock (thread-pinned single-thread BLAS) |

Per-file test counts (matches `03-NN-SUMMARY.md` claims):

| File | Owner Plan | Tests | Requirement |
|---|---|---|---|
| `tests/test_nhpp_inar.py` | 03-01 | 3 | DGP-01 |
| `tests/test_hawkes_fit.py` | 03-02 | 4 | DGP-02 |
| `tests/test_lr_test.py` | 03-03 | 6 | DGP-03 |
| `tests/test_held_out.py` | 03-04 | 5 | DGP-04 (held-out leg) |
| `tests/test_stationarity.py` | 03-04 | 4 | DGP-04 (stationarity leg) |
| `tests/test_time_rescaling.py` | 03-05 | 4 | DGP-05 |
| `tests/test_profile_likelihood.py` | 03-06 | 4 | DGP-06 |
| `tests/test_fit_artifact_provenance.py` | 03-07 | 6 | SC-1 orchestrator |
| `tests/test_byte_identical.py` | 03-08 | 3 | SC-5 byte-identity |
| **TOTAL** | | **39** | |

## Acceptance grid (DGP-01..06 + ROADMAP SC-1..SC-5)

| Criterion | Description | Command | Exit | Observed | Verdict |
|---|---|---|---|---|---|
| DGP-01 | Kirchner NHPP-INAR(p) estimator with ground-truth-recovery validation against tick-simulated paths | `cd analysis && uv run pytest tests/test_nhpp_inar.py -x` | 0 | "3 passed" | PASS |
| DGP-02 | tick Hawkes MLE with full 2x2 off-diagonal adjacency; LS-fallback documented under tick 0.8.0.2 + statsmodels 0.14.6 incompatibility | `cd analysis && uv run pytest tests/test_hawkes_fit.py -x` | 0 | "4 passed" | PASS |
| DGP-03 | Boundary-correct bootstrap LR test (50:50 chi2(0):chi2(1) mixture under nested-zero-on-boundary) | `cd analysis && uv run pytest tests/test_lr_test.py -x` | 0 | "6 passed" | PASS |
| DGP-04 | Held-out temporal evaluation + stationarity diagnostic (PRE_REGISTRATION ±25% rule) | `cd analysis && uv run pytest tests/test_held_out.py tests/test_stationarity.py -x` | 0 | "9 passed" (5+4) | PASS |
| DGP-05 | Time-rescaling KS test on rescaled residuals (per-leg + combined) | `cd analysis && uv run pytest tests/test_time_rescaling.py -x` | 0 | "4 passed" | PASS |
| DGP-06 | Profile-likelihood branching-ratio CI via brentq on chi2(1)-deficit (Filimonov–Sornette 2014) | `cd analysis && uv run pytest tests/test_profile_likelihood.py -x` | 0 | "4 passed" | PASS |
| SC-1 (test) | `data/fits/ichi/<run_id>/fit_report.json` carries 18-key SC-1 schema + PANEL-02 metadata header | `cd analysis && uv run pytest tests/test_fit_artifact_provenance.py -x` | 0 | "6 passed" | PASS |
| SC-1 (lint) | `make lint-artifacts` rejects any fit_report.json missing required SC-1 keys | `make lint-artifacts` | 0 | "lint_artifacts: 1 parquet PASS PANEL-02" (data/fits/ glob currently empty; PANEL-02 leg covered) | PASS |
| SC-2 | NHPP-INAR(p) recovers tick-simulated ground-truth parameters within tolerance | `cd analysis && uv run pytest tests/test_nhpp_inar.py::test_recovers_synthetic_ground_truth -x` | 0 | "1 passed" | PASS |
| SC-3 (test) | Bootstrap LR rig produces mixture null + boundary-correct p-value | `cd analysis && uv run pytest tests/test_lr_test.py -x` | 0 | "6 passed" | PASS |
| SC-3 (grep) | Vanilla LRT path is structurally absent from `lr_test.py` | `! grep -rE 'likelihood_ratio_test\|chi2\(1\)\.sf' analysis/src/abrigo_x402/dgp/lr_test.py` | 0 | (no hits) | PASS |
| SC-4 | Held-out split refuses in-sample fits + stationarity diagnostic gates piecewise-baseline branch | `cd analysis && uv run pytest tests/test_held_out.py::test_in_sample_only_raises tests/test_stationarity.py::test_piecewise_required_on_drifted_synthetic -x` | 0 | "2 passed" | PASS |
| SC-5 | Two consecutive `run_fit` invocations on the same panel produce byte-identical `fit_report.json` (modulo `fetchTimestamp`) AND byte-identical `residuals.parquet` | `cd analysis && OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run pytest tests/test_byte_identical.py -x` | 0 | "3 passed" | PASS |

### SC-5 row — Notes / Caveats (verbatim, Reality Checker fix)

```
SC-5 byte-identity requires OMP_NUM_THREADS=MKL_NUM_THREADS=OPENBLAS_NUM_THREADS=NUMEXPR_NUM_THREADS=1.
If missing, statsmodels VAR.select_order AIC values drift under variable thread parallelism and
nhpp_inar_params (p, loglik_in_sample) differ run-to-run on multi-core CI runners. The test
test_byte_identical.py sets these env vars via os.environ.setdefault BEFORE the first numpy
import (transitive via run_fit) and includes a sanity-guard assert inside test_deterministic_fit
that re-checks the pinning at runtime.
```

Mechanical enforcement on disk (Wave-3 implementation):
- `analysis/tests/test_byte_identical.py` lines 28–33: `os.environ.setdefault(...)` block before any non-stdlib import.
- `analysis/tests/test_byte_identical.py` lines 80–86: runtime `assert os.environ.get("OMP_NUM_THREADS") == "1"` (and three siblings) inside `test_deterministic_fit`.
- Grep enforcement (per-env-var): `grep -c "OMP_NUM_THREADS" analysis/tests/test_byte_identical.py` ≥ 2, same for MKL / OPENBLAS / NUMEXPR.
- Subprocess note: if a future revision migrates `run_fit` invocation to a subprocess CLI, the pinning env vars MUST be forwarded via `env=` to the child — `os.environ.setdefault` in the parent does NOT propagate. Documented in the test-file docstring.

## Full Suite Aggregate

```
cd analysis && OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run pytest \
    tests/test_nhpp_inar.py tests/test_hawkes_fit.py tests/test_lr_test.py \
    tests/test_held_out.py tests/test_stationarity.py tests/test_time_rescaling.py \
    tests/test_profile_likelihood.py tests/test_fit_artifact_provenance.py \
    tests/test_byte_identical.py
```

- Exit code: 0
- Result: **39 passed, 0 failed, 0 skipped** (1 warning — upstream tick → scipy.linalg.special_matrices DeprecationWarning, scipy-side, non-blocking)
- Wall-clock: 127.09 s (single-threaded BLAS; multi-thread is FASTER but breaks byte-identity per SC-5)

## Production-Rep Size Sanity (Manual, Once-per-Phase)

Per CONTEXT.md "Manual-Only Verifications" + RESEARCH §Validation Architecture. The production-rep size sanity confirms the bootstrap LR rig at PRE_REGISTRATION-locked `n_reps=1000` (a) completes without runtime error AND (b) does not spuriously reject under a synthetic α=0 (pure-Poisson, no excitation) null DGP. This production-rep check runs once per phase.

Command:

```bash
cd analysis && OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  uv run python -c "
import polars as pl, numpy as np
from abrigo_x402.dgp.lr_test import parametric_bootstrap_lr
df = pl.read_parquet('tests/fixtures/synthetic_nhpp_baseline_only.parquet')
leg_0 = df.filter(pl.col('leg') == 0).select('event_time').to_numpy().ravel().astype(np.float64)
leg_1 = df.filter(pl.col('leg') == 1).select('event_time').to_numpy().ravel().astype(np.float64)
result = parametric_bootstrap_lr(
    leg_0, leg_1, panel_data_hash='03-08-size-sanity-prod',
    window_start=0.0, window_end=float(max(leg_0.max(), leg_1.max())),
    n_reps=1000, alpha=0.01,
)
print(result)
"
```

Observed (verbatim, single one-off run captured 2026-05-27):

| Field | Value |
|---|---|
| `observed_stat` | 0.006931 |
| `p_value` | 0.562000 |
| `n_failed` | 0 |
| `rejects_at_alpha` (α=0.01) | False |
| Wall-clock | 73.3 s |
| Panel size | leg_0 = 337 events, leg_1 = 316 events (synthetic α=0 NHPP, 30-day window) |

**Interpretation**: Under the synthetic null DGP (α=0 baseline-only NHPP), the bootstrap LR rig (i) completes all 1000 reps with zero failures, (ii) produces an observed LR statistic indistinguishable from zero (`2*(LL_hawkes - LL_nhpp) ≈ 0.007`), (iii) emits a p-value of 0.562 — well within the null acceptance region at α=0.01. A single observation is uninformative for a formal size-coverage check (would require ≥100 independent null replicates), but the *non-rejection* on data simulated from the null is the size-discipline expected outcome and the *successful completion of the 1000-rep run on production-scale event counts* is the load-bearing deliverable for this manual check.

Note (input-type discipline): the manual command above casts `to_numpy().ravel().astype(np.float64)` to match the `synthetic_*_legs` conftest fixture pattern. Raw `to_numpy()` on the polars Series returns a 2-D array shape `(N, 1)` whose downstream `set_data()` call into `tick.hawkes.model.build.hawkes_model.ModelHawkesExpKernLogLik` raises a `TypeError: incompatible function arguments` (tick's pybind11 signature requires a flat `array[float64]`). All Phase 3 internal callers (`conftest.synthetic_*_legs` + orchestrator `_extract_legs_from_panel`) already cast correctly; this caveat is documentary for manual CLI invocations.

## Diagnostic Artifact (DGP-03 mixture-null visual)

- Path: `reports/_diagnostics/lr_null_dist.png`
- Size: 40,236 bytes (>1 KB threshold)
- Generated by: Plan 03-03 (DGP-03 bootstrap LR rig) on 2026-05-26 23:18
- Manual sign-off note: Histogram inspected; point mass at 0 + right-skewed continuous tail visible — verdict: **VISUAL PASS** (mixture null shape consistent with 50:50 χ²(0):χ²(1) under nested-zero-on-boundary; matches Self & Liang 1987 + Cavaliere 2022 expectation).

## Phase 3 Goal-Backward Checks

- [x] All DGP-01..06 requirements covered with test evidence (`REQUIREMENTS.md` traceability rows match SC-1..SC-5 grid above)
- [x] All ROADMAP SC-1..5 covered:
  - **SC-1** `fit_report.json` 18-key schema → `test_fit_artifact_provenance.py` 6/6 + `make lint-artifacts` exit 0
  - **SC-2** NHPP ground-truth recovery → `test_nhpp_inar.py::test_recovers_synthetic_ground_truth` PASS
  - **SC-3** boundary-correct LR test → `test_lr_test.py` 6/6 + grep gate green
  - **SC-4** held-out + stationarity discipline → `test_held_out.py::test_in_sample_only_raises` + `test_stationarity.py::test_piecewise_required_on_drifted_synthetic` PASS
  - **SC-5** byte-identical fit pair → `test_byte_identical.py` 3/3 with thread-pinning hardening
- [x] PRE_REGISTRATION four-criterion gate evaluable on real panel: `orchestrator.run_fit` `gate_passes` + `gate_criteria` fields populated unconditionally (Pattern G — complete-artifact-on-failure); gate may FAIL on the real ICHI panel and that is the expected outcome per CONTEXT.md `<specifics>`, but the gate machinery WORKS
- [x] SC-3 grep gate: 0 hits for `likelihood_ratio_test` or `chi2(1).sf` in `analysis/src/abrigo_x402/dgp/lr_test.py`
- [x] PANEL-02 invariant preserved: every fit artifact carries the 6-key metadata header (`make lint-artifacts` PASS)
- [x] SC-5 thread-pinning preserved: `grep -c "OMP_NUM_THREADS" analysis/tests/test_byte_identical.py` = 3 (≥ 2 required), same ≥2 for MKL/OPENBLAS/NUMEXPR
- [x] Regex acceptance check (Phase-1 I11 pattern): `grep -cE "DGP-0[1-6]|SC-[1-5]" 03-VERIFICATION-pre.md` ≥ 11

## Deferred Items

- **Real ICHI panel actual fit run** (DGP-07 end-to-end on `data/raw/ichi/0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F/<from>_<to>.parquet`): NOT exercised in Plan 03-08. The orchestrator + provenance + SC-1 schema are unit-tested against synthetic Hawkes data + a captured-real-shape mini panel; the production fit on the full ICHI panel is the first step of Phase 4 (and will populate `data/fits/ichi/<run_id>/`). Justification: Plan 03-08's scope is acceptance consolidation, not first-real-data execution; the four-criterion gate is expected to FAIL on the real panel per CONTEXT.md `<specifics>` (insufficient ICHI cKES/USDT swap volume — that null outcome is itself documented as a HEDGE-05 firing condition in Phase 4).
- **Piecewise-baseline branch** (stationarity diagnostic → piecewise-NHPP fit): scaffolded in `stationarity.py` + tested for `piecewise_required` flag emission; the actual piecewise-fit code path is deferred to Phase 4 IF the real ICHI panel triggers `decision: piecewise_required` (rolled forward per CONTEXT.md `<deferred>`).
- **tick API drift on raw polars `to_numpy()`** (informational, not blocking): tick 0.8.0.2's pybind11 `set_data()` signature rejects 2-D `(N, 1)` arrays from polars `Series.to_numpy()`. All internal callers correctly cast via `.ravel().astype(np.float64)` (conftest + orchestrator). Captured in the Production-Rep Size Sanity caveat above so future manual CLI users avoid the trap; not a Phase 3 acceptance failure.
- **LS-fallback objective-scale mismatch** (carried from 03-02 + 03-06 + 03-07): when tick 0.8.0.2's HawkesExpKern MLE solver throws on degenerate inputs at extreme `decays`, the LS-fallback path returns the LS objective (~0) rather than the Hawkes log-likelihood. Plan 03-07's orchestrator absorbs this via the canonical-LL contract (Pattern F): `lr_test.py :: _hawkes_loglik_vectorized` is the single source of truth, imported into the orchestrator and recorded in `fit_report.json :: input_diagnostics.hawkes_loglik_source`. Raw upstream LL preserved under `loglik_in_sample_raw` for audit. **This is documented behavior, not a deviation** — but flagged here so Phase 4 consumers know to read `loglik` not `loglik_in_sample` from `hawkes_mv_params`.

## Outstanding gaps

**None — Phase 3 closed at 9/9 plans complete.** All five ROADMAP Success Criteria (SC-1..5) and all six DGP requirements (DGP-01..06) verified PASS via live `pytest` / `make` / `grep` invocations against the working tree at commit `2e5ad5f`. The SC-5 byte-identical contract is operationalized as an automated test with BLAS/OMP/MKL/OpenBLAS/NumExpr thread pinning that protects against the silent-non-determinism failure mode documented in `lr_test.py` LS-fallback context + statsmodels VAR.select_order CI-runner drift.

## Next step

Run `/gsd:verify-work 03-dgp-estimation-l4-with-boundary-correct-lr-test` to produce the canonical `03-VERIFICATION.md` and close out Phase 3. Then `/gsd:plan-phase 4` to scope Phase 4 (Cross-Leg Dependence + Falsification + Carr–Madan Strip on the produced `data/fits/ichi/<run_id>/{residuals.parquet,fit_report.json}` substrate).
