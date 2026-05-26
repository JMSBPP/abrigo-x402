---
phase: 3
slug: dgp-estimation-l4-with-boundary-correct-lr-test
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-26
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Distilled from `03-RESEARCH.md :: Validation Architecture` (commit a50797c).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest>=9.0.3` (already installed in Phase 2 Plan 02-00 via `analysis/pyproject.toml [dependency-groups].dev`) |
| **Config file** | `analysis/pyproject.toml` `[tool.pytest.ini_options]` (testpaths=["tests"], pythonpath=["src"]) — already established |
| **Quick run command** | `cd analysis && uv run pytest tests/test_<module>.py -x` |
| **Full suite command** | `cd analysis && uv run pytest -x` |
| **Estimated runtime** | ~120–300 seconds (bootstrap LR is the long pole at n_reps=200 in tests; production = 1000) |

---

## Sampling Rate

- **After every task commit:** Run `cd analysis && uv run pytest tests/test_<module>.py -x` (single-file run; < 30s typical).
- **After every plan wave:** Run `cd analysis && uv run pytest -x` (full Phase 3 suite; ~2–5 min).
- **Before `/gsd:verify-work`:** Full suite green + `make lint-artifacts` PASS + SC-3 grep gate green (`! grep -rE "likelihood_ratio_test|chi2\(1\)\.sf" analysis/src/abrigo_x402/dgp/lr_test.py`).
- **Max feedback latency:** 30s (per-task) / 300s (per-wave).

---

## Per-Task Verification Map

| Req ID | Behavior | Test Type | Automated Command | File Exists | Status |
|---|---|---|---|---|---|
| **DGP-01** | Kirchner INAR(p) recovers ground-truth NHPP baseline within ±10% over 1000 paths | unit (synthetic) | `cd analysis && uv run pytest tests/test_nhpp_inar.py::test_recovers_synthetic_ground_truth -x` | ❌ W0 | ⬜ pending |
| **DGP-01** | INAR(p) AIC-min selects bin width from `{60, 300, 900, 3600}`s | unit | `cd analysis && uv run pytest tests/test_nhpp_inar.py::test_aic_bin_selection -x` | ❌ W0 | ⬜ pending |
| **DGP-01** | Non-negativity projection clamps negative VAR coefficients to 0 | unit | `cd analysis && uv run pytest tests/test_nhpp_inar.py::test_nonneg_projection -x` | ❌ W0 | ⬜ pending |
| **DGP-02** | `tick.HawkesExpKern` fit produces 2×2 adjacency with off-diagonal NOT forced to 0 | unit | `cd analysis && uv run pytest tests/test_hawkes_fit.py::test_full_offdiag -x` | ❌ W0 | ⬜ pending |
| **DGP-02** | Branching ratio = spectral radius of α/β (not max element) | unit | `cd analysis && uv run pytest tests/test_hawkes_fit.py::test_branching_ratio_spectral -x` | ❌ W0 | ⬜ pending |
| **DGP-02** | Same-block timestamps handled without logIndex tie-breaking | unit | `cd analysis && uv run pytest tests/test_hawkes_fit.py::test_simultaneous_events -x` | ❌ W0 | ⬜ pending |
| **DGP-03** | Bootstrap LR null distribution shows χ²(0):χ²(1) mixture shape (point mass at 0 + continuous tail) | unit (synthetic NHPP) | `cd analysis && uv run pytest tests/test_lr_test.py::test_null_distribution_mixture_shape -x` | ❌ W0 | ⬜ pending |
| **DGP-03** | Bootstrap LR rejects at α=0.01 on synthetic Hawkes with η=0.5 (power) | unit (synthetic) | `cd analysis && uv run pytest tests/test_lr_test.py::test_power_on_synthetic_hawkes -x` | ❌ W0 | ⬜ pending |
| **DGP-03** | Bootstrap LR ~1% rejection on synthetic NHPP (size calibration) | unit (synthetic, n_reps=200) | `cd analysis && uv run pytest tests/test_lr_test.py::test_size_calibration -x` | ❌ W0 | ⬜ pending |
| **DGP-03** | Source has zero hits for `likelihood_ratio_test` or naive `chi2(1).sf` | lint (grep) | `! grep -rE "likelihood_ratio_test\|chi2\(1\)\.sf" analysis/src/abrigo_x402/dgp/lr_test.py` | ❌ W0 | ⬜ pending |
| **DGP-04** | Held-out split is wall-clock not event-count (last 20% of time window) | unit | `cd analysis && uv run pytest tests/test_held_out.py::test_wallclock_split -x` | ❌ W0 | ⬜ pending |
| **DGP-04** | In-sample-only fit attempt raises `InsufficientEvaluationError` | unit | `cd analysis && uv run pytest tests/test_held_out.py::test_in_sample_only_raises -x` | ❌ W0 | ⬜ pending |
| **DGP-04** | Stationarity diagnostic flags non-stationary panel with rate drift (piecewise_required) | unit (synthetic) | `cd analysis && uv run pytest tests/test_stationarity.py::test_piecewise_required_on_drifted_synthetic -x` | ❌ W0 | ⬜ pending |
| **DGP-05** | Time-rescaling KS passes on correctly-specified Hawkes synthetic | unit (synthetic) | `cd analysis && uv run pytest tests/test_time_rescaling.py::test_passes_on_true_model -x` | ❌ W0 | ⬜ pending |
| **DGP-05** | Time-rescaling KS fails on misspecified model (NHPP rescaling of true Hawkes) | unit (synthetic) | `cd analysis && uv run pytest tests/test_time_rescaling.py::test_fails_on_misspecified -x` | ❌ W0 | ⬜ pending |
| **DGP-05** | Compensator Λ(t) for exponential kernel is correct closed-form | unit (analytic) | `cd analysis && uv run pytest tests/test_time_rescaling.py::test_compensator_closed_form -x` | ❌ W0 | ⬜ pending |
| **DGP-06** | Profile-likelihood η-CI on synthetic Hawkes covers known η | unit (synthetic) | `cd analysis && uv run pytest tests/test_profile_likelihood.py::test_ci_covers_truth -x` | ❌ W0 | ⬜ pending |
| **DGP-06** | η-CI is bounded in [0, 1) (never extends past boundary) | unit | `cd analysis && uv run pytest tests/test_profile_likelihood.py::test_ci_bounded -x` | ❌ W0 | ⬜ pending |
| **DGP-06** | CI width > 0.4 triggers Q-9 null-fire flag in `fit_report.json` | unit | `cd analysis && uv run pytest tests/test_profile_likelihood.py::test_q9_nullfire_trigger -x` | ❌ W0 | ⬜ pending |
| **SC-1** | `fit_report.json` carries metadata header (chainId, contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit) | integration | `cd analysis && uv run pytest tests/test_fit_artifact_provenance.py::test_metadata_keys -x` | ❌ W0 | ⬜ pending |
| **SC-1** | `make lint-artifacts` recognizes `fit_report.json` + rejects missing keys | lint | `make lint-artifacts` | ❌ W0 | ⬜ pending |
| **SC-3** | `reports/_diagnostics/lr_null_dist.png` renders headless and exists with nonzero size | smoke | `cd analysis && uv run pytest tests/test_lr_test.py::test_diagnostic_plot_renders -x` | ❌ W0 | ⬜ pending |
| **SC-5** | Byte-identical `fit_report.json` + `residuals.parquet` across two runs (same panel + git commit, modulo wall-clock) | integration | `cd analysis && uv run pytest tests/test_byte_identical.py::test_deterministic_fit -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `analysis/tests/test_nhpp_inar.py` — stubs for DGP-01 (synthetic-ground-truth recovery harness)
- [ ] `analysis/tests/test_hawkes_fit.py` — stubs for DGP-02 (tick fit, branching ratio, simultaneous events)
- [ ] `analysis/tests/test_lr_test.py` — stubs for DGP-03 (bootstrap null shape, size, power, grep gate, diagnostic plot)
- [ ] `analysis/tests/test_held_out.py` — stubs for DGP-04 (wall-clock split, InsufficientEvaluationError)
- [ ] `analysis/tests/test_stationarity.py` — stubs for PITFALLS §4 (±25% ratio + piecewise_required decision)
- [ ] `analysis/tests/test_time_rescaling.py` — stubs for DGP-05 (compensator closed-form, KS pass/fail)
- [ ] `analysis/tests/test_profile_likelihood.py` — stubs for DGP-06 (η-CI bounded, covers truth, Q-9 null-fire)
- [ ] `analysis/tests/test_fit_artifact_provenance.py` — stubs for SC-1 (metadata header)
- [ ] `analysis/tests/test_byte_identical.py` — stubs for SC-5 (deterministic rerun byte-identity)
- [ ] `analysis/tests/conftest.py` — extend Phase 2 conftest with synthetic Hawkes/NHPP fixture generators + canonical 30-day `panel_fixture`
- [ ] `analysis/tests/fixtures/synthetic_hawkes_eta_05.parquet` — `SimuHawkesExpKernels` 30-day panel, η=0.5, locked seed
- [ ] `analysis/tests/fixtures/synthetic_nhpp_baseline_only.parquet` — `SimuHawkesExpKernels` 30-day panel, α=0 (pure NHPP), locked seed
- [ ] `scripts/lint_artifacts.py` extension — recognize `fit_report.json` and require SC-1 metadata header

*Framework install: not needed — `pytest>=9.0.3` already in `analysis/pyproject.toml` from Phase 2 Plan 02-00.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual inspection of `reports/_diagnostics/lr_null_dist.png` mixture shape | DGP-03 / SC-3 | Test only checks file exists + nonzero size; visual mixture-shape sanity (point mass at 0 + continuous tail) is a human-eye check before signing off Phase 3 verification | After full suite green, open `reports/_diagnostics/lr_null_dist.png` and confirm a tall spike at 0 plus a right-skewed continuous tail. Document in `03-VERIFICATION-pre.md`. |
| Bootstrap LR rejection-rate sanity at production `--bootstrap-reps 1000` | DGP-03 size | Tests use n_reps=200 for runtime; a one-shot 1000-rep size check on synthetic NHPP is run manually once before phase sign-off | Run `cd analysis && uv run python -m abrigo_x402.dgp.lr_test --panel tests/fixtures/synthetic_nhpp_baseline_only.parquet --bootstrap-reps 1000` and confirm reported p-value distribution centered at ~0.5 (or empirical size ≈ α). |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s per-task / 300s per-wave
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
