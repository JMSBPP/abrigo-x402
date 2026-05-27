---
phase: 4
slug: cross-leg-dependence-l5-falsification-carr-madan-strip-l6
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-27
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Distilled from `04-RESEARCH.md :: Validation Architecture` (commit f0ad6c1).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest>=9.0.3` (already in `analysis/pyproject.toml [dependency-groups].dev` from Phase 2 Plan 02-00) |
| **Config file** | `analysis/pyproject.toml [tool.pytest.ini_options]` (testpaths=["tests"], pythonpath=["src"], addopts="-ra --strict-markers") |
| **Quick run command** | `cd analysis && uv run pytest tests/test_<module>.py -x` |
| **Full suite command** | `cd analysis && uv run pytest tests/ -x` |
| **Acceptance grid command** | `make phase-4-acceptance` (Wave 0 adds the Makefile target wrapping the grid) |
| **Estimated runtime** | ~180–300 seconds (Carr–Madan FFT escalation tests + N=64 LHS sweep are the long poles under thread-pinned BLAS) |

---

## Sampling Rate

- **After every task commit:** Run `cd analysis && uv run pytest tests/test_<module>.py -x` (single-file run; < 30s typical).
- **After every plan wave:** Run `cd analysis && uv run pytest tests/ -x` (full Phase 2+3+4 suite; ~3–5 min wall-clock under thread-pinned BLAS).
- **Before `/gsd:verify-work`:** Full suite green + `make lint-artifacts` exit 0 + `make phase-4-acceptance` exit 0 + SC-2 grep gate green (`! grep -i "^[^#]*usdc" analysis/src/abrigo_x402/hedge/falsification.py`) + Carr–Madan anti-pattern grep (`! grep -E "scipy\.integrate\.quad|np\.trapz" analysis/src/abrigo_x402/hedge/carr_madan_strip.py`) + canonical-LL anti-pattern grep (`! grep -rE "loglik_in_sample_raw" analysis/src/abrigo_x402/hedge/`).
- **Max feedback latency:** 30s (per-task) / 300s (per-wave).

---

## Per-Task Verification Map

| Req ID | Behavior | Test Type | Automated Command | File Exists | Status |
|---|---|---|---|---|---|
| **DEPEND-01** | 5-family BIC + cross-correlogram + permutation null produce `joint_dist.json` with all `REQUIRED_JOINT_DIST_KEYS` | unit + integration | `cd analysis && uv run pytest tests/test_copula_bic.py tests/test_cross_correlogram.py tests/test_permutation_null.py tests/test_joint_dist_provenance.py -x` | ❌ W0 | ⬜ pending |
| **DEPEND-02** | `make lint-artifacts` asserts `joint_dist.json` schema before Phase 5 build | lint | `make lint-artifacts` exits non-zero on malformed `joint_dist.json` | ❌ W0 | ⬜ pending |
| **HEDGE-01** | Four-condition gate writes `gate_report.json` with each condition `{passed, evidence}`; SC-2 grep gate is also green | unit + grep | `cd analysis && uv run pytest tests/test_falsification.py -x && ! grep -i "^[^#]*usdc" analysis/src/abrigo_x402/hedge/falsification.py` | ❌ W0 | ⬜ pending |
| **HEDGE-02** | Carr–Madan strip emits at 2¹¹ on Gaussian fixture; escalates to 2¹² on fat-tail fixture OR aborts to `strip_degenerate.json` when 2¹² still fails; 0.1% positivity tolerance applied | unit | `cd analysis && uv run pytest tests/test_carr_madan_strip.py -x` (covers all three paths) | ❌ W0 | ⬜ pending |
| **HEDGE-03** | Latin hypercube N=64 sensitivity sweep around stipulated `(λ, μ_J, σ_J)` ±50% produces `gate_report :: usdt_depeg_basis_jump :: evidence :: sensitivity_summary` with N=64 cells; `evidence_source: "literature_range_stipulation"` recorded | unit | `cd analysis && uv run pytest tests/test_usdt_depeg_lhs.py -x` | ❌ W0 | ⬜ pending |
| **HEDGE-04** | Three-way stress test produces `stress_report.json` with `{independence, fitted_joint, comonotone}` prices + `divergence_flag: true` when (spread/mean) > 30% | unit + integration | `cd analysis && uv run pytest tests/test_stress_test.py -x` | ❌ W0 | ⬜ pending |
| **HEDGE-05** | All three firing-condition fixtures regenerate `reports/ichi.pdf` as null-result PDF; dual signature (visible `# HEDGE-05 NULL RESULT` heading + `HEDGE05-NULL-RESULT-V1` machine marker) verifiable via `pdftotext` AND `pdfinfo` | integration + grep | `cd analysis && uv run pytest tests/test_null_result_template.py -x` (parametrized over `null_cost`, `null_lr`, `null_convex`) | ❌ W0 | ⬜ pending |
| **SC-1 (Phase 4)** | All four new JSON artifacts (`joint_dist.json`, `gate_report.json`, `stress_report.json`, `strip.json`) carry the 6-key PANEL-02 metadata header | unit + lint | `make lint-artifacts` exit 0 on clean tree | ❌ W0 | ⬜ pending |
| **SC-2 (Phase 4)** | `grep -i "^[^#]*usdc" analysis/src/abrigo_x402/hedge/falsification.py` returns only comment/historical-reference hits | grep gate | inline in `test_falsification.py` + pre-commit hook | ❌ W0 | ⬜ pending |
| **SC-3 (Phase 4)** | Convergence-tested grid 2¹¹→2¹²; abort-to-`strip_degenerate.json` after 2¹² fail; 0.1% positivity tolerance | unit | included in `test_carr_madan_strip.py` | ❌ W0 | ⬜ pending |
| **SC-4 (Phase 4)** | `stress_report.json` includes all three scenarios + `divergence_flag` at >30% spread/mean | unit | included in `test_stress_test.py` | ❌ W0 | ⬜ pending |
| **SC-5 (Phase 4)** | HEDGE-05 template fires automatically; three fixture triplets verify | integration | included in `test_null_result_template.py` | ❌ W0 | ⬜ pending |
| **SC-6 (Phase 4)** | USDT-depeg calibration documented in `notes/usdt_depeg_calibration.md` with explicit `literature_range_stipulation` framing (NOT cited as Hernandez Cruz 2024 parameter source) | manual + lint | `test -f notes/usdt_depeg_calibration.md && grep -q 'literature_range_stipulation' notes/usdt_depeg_calibration.md && ! grep -qE 'port from Hernandez Cruz' notes/usdt_depeg_calibration.md` | ❌ W0 | ⬜ pending |
| **PR amendment** | `notes/PRE_REGISTRATION.md` AF-03 amendment locking the 0.1% Carr–Madan positivity tolerance committed as a SOLO commit predating all `analysis/src/abrigo_x402/hedge/*` commits | git ordering invariant | `git log --pretty=format:'%H %s' -- notes/PRE_REGISTRATION.md analysis/src/abrigo_x402/hedge/` shows the amendment commit before any hedge/* commit | ❌ W0 (first task) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Plan 04-00 (Wave 0 scaffold) MUST land these BEFORE any Wave-1 plan begins:

- [ ] **`notes/PRE_REGISTRATION.md` AF-03 amendment (FIRST TASK, SOLO COMMIT)** — locks the 0.1% Carr–Madan positivity tolerance per CONTEXT.md `<deferred>` requirement. Must predate all `analysis/src/abrigo_x402/hedge/*` commits. Acceptance: `git log -- notes/PRE_REGISTRATION.md analysis/src/abrigo_x402/hedge/` shows the amendment commit first.
- [ ] `analysis/src/abrigo_x402/dependence/{__init__,cross_correlogram,permutation_null,copula}.py` — module skeletons with canonical Wave-1 symbol names locked; `REQUIRED_JOINT_DIST_KEYS` tuple forward-declared.
- [ ] `analysis/src/abrigo_x402/hedge/{__init__,falsification,carr_madan_strip,stress_test,usdt_depeg,null_result,orchestrator}.py` — module skeletons; `REQUIRED_GATE_REPORT_KEYS`, `REQUIRED_STRESS_REPORT_KEYS`, `REQUIRED_STRIP_KEYS`, `STRIP_DEGENERATE_KEYS`, `HEDGE05_SIGNATURE = "HEDGE05-NULL-RESULT-V1"` constants forward-declared.
- [ ] `analysis/tests/test_{cross_correlogram,permutation_null,copula_bic,falsification,carr_madan_strip,stress_test,usdt_depeg_lhs,null_result_template,joint_dist_provenance,gate_report_provenance,stress_report_provenance,byte_identical_phase_4}.py` — skip-marked stubs at canonical Wave-1 symbol surface.
- [ ] `analysis/tests/conftest.py` extension — add `joint_dist_fixture`, `gate_report_fixture`, `null_result_fixture_triplet` (parametrized over `["null_cost", "null_lr", "null_convex"]`) fixtures.
- [ ] `analysis/tests/fixtures/hedge_05_{null_cost,null_lr,null_convex}/{fit_report.json, gate_report.json, cost_leg_bound.md}` — three synthetic triplets, each forcing exactly one HEDGE-05 firing condition. `null_lr` reuses Phase 3's `synthetic_nhpp_baseline_only.parquet` substrate; `null_convex` synthesizes an NHPP-only Hawkes adjacency; `null_cost` hand-authors `cost_leg_bound.md` with `verdict: FAIL`.
- [ ] `reports/_templates/null_result.qmd` — Quarto template scaffold with dual signature markers (visible `# HEDGE-05 NULL RESULT — <condition>` H1 + `\pdfinfo` injection of `HEDGE05-NULL-RESULT-V1` marker) + three conditional-content branches keyed off `firing_condition` parameter.
- [ ] `scripts/lint_artifacts.py` extension — add `JOINT_DIST_REQUIRED_KEYS`, `GATE_REPORT_REQUIRED_KEYS`, `STRESS_REPORT_REQUIRED_KEYS`, `STRIP_REQUIRED_KEYS`, `STRIP_DEGENERATE_REQUIRED_KEYS` tuples + `lint_<artifact>_json` helpers + glob walkers per pattern. Maintains sync with the in-source `REQUIRED_*_KEYS` tuples (Pattern G).
- [ ] `Makefile` — extend `lint-artifacts` target to walk five new JSON artifact patterns; add `render-null-result-pdf` + `render-strip-diagnostic` + `phase-4-acceptance` targets.
- [ ] `analysis/pyproject.toml` — add `copulae==0.8.0` to `[project] dependencies`; add `jupyter` to `[dependency-groups] dev`. **Defer** `pyvinecopulib==0.7.6` to a follow-up plan (lazy install — Pitfall 2 + RESEARCH Open Question 3).
- [ ] `README.md` or `analysis/README.md` system-dependency block — document `quarto` + `texlive-luatex` (or `quarto install tinytex`) install path.
- [ ] `.pre-commit-config.yaml` extensions — add SC-2 grep gate (`usdc` literals in `hedge/*.py` excluding comments), Carr–Madan anti-pattern gate (`scipy.integrate.quad`/`np.trapz` in `carr_madan_strip.py`), canonical-LL gate (`loglik_in_sample_raw` in `hedge/*`), hardcoded-jump-params gate.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual inspection of rendered `reports/ichi.pdf` (null-result variant) | HEDGE-05 / SC-5 | The grep test confirms the signature markers exist; a human-eye check confirms the firing condition narrative, evidence block, and primary-source citations render coherently in the rendered PDF. | After `make render-null-result-pdf FIRING=null_cost` (and the other two), open each generated PDF and confirm: visible H1 heading present, firing-condition evidence block populated with the correct fixture data, PRE_REGISTRATION.md citations resolve to a hyperlink in the bibliography. Document in `04-VERIFICATION-pre.md`. |
| Real ICHI panel run on the actual `data/fits/ichi/<run_id>/fit_report.json` from Phase 3 (expected outcome: HEDGE-05 fires per CONTEXT specifics) | HEDGE-01..05 end-to-end | Real data result may produce STRADDLE or null-fire on the four-criterion gate — this is the headline scientific output and merits human review before signing off on Phase 4. | Run `cd analysis && uv run python -m abrigo_x402.cli hedge --run-id <phase-3-run-id>` once on the real panel. Inspect `gate_report.json` and `stress_report.json` (or `strip_degenerate.json` if condition 4 failed convergence). Document whether HEDGE-05 fired and which condition in `04-VERIFICATION-pre.md`. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s per-task / 300s per-wave
- [ ] `nyquist_compliant: true` set in frontmatter
- [ ] PRE_REGISTRATION amendment commit predates all `hedge/*` commits (AF-03 ordering invariant)

**Approval:** pending
