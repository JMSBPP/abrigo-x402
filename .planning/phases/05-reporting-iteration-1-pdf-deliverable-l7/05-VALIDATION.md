---
phase: 05
slug: reporting-iteration-1-pdf-deliverable-l7
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-29
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Reporting phase: the deliverable is `reports/ichi.pdf` + the build/repro Makefile targets. The verdict reported is FIXED (gate_passes=FALSE 3/4, firing_condition=null_strip_unavailable, run_id bdaf5c7ba5a2) — the report READS artifacts, never recomputes the fit, never narrows the verdict.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (analysis/ suite; 207-green baseline, thread-pinned BLAS Pattern I) |
| **Config file** | `analysis/pyproject.toml` |
| **Quick run command** | `cd analysis && OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run pytest tests/test_null_result_template.py -x` |
| **Full suite command** | `cd analysis && OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run pytest -x` |
| **Estimated runtime** | quick ~10-30s; full ~4-7min (the 207-suite incl. thread-pinned fits) |
| **Quarto note** | `quarto` binary is an OPERATOR PREREQUISITE absent in this env; all render-touching tests stay `quarto_skipped`-guarded so the 207-green suite is preserved. `make report-ichi` hard-requires quarto + self-installs TinyTeX. |

---

## Sampling Rate

- **After every task commit:** quick run of the new test file (thread-pinned)
- **After every plan wave:** full suite (confirm 207-green + the 3 quarto-skips hold)
- **Before `/gsd:verify-work`:** full suite green + `make report-ichi` green (PDF >50KB) + `make verify-reproducibility` exits 0
- **Max feedback latency:** 30s (quick); ~7min (full)

---

## Per-Task Verification Map

| Task ID | Req | Wave | Behavior | Test Type | Automated Command | File | Status |
|---------|-----|------|----------|-----------|-------------------|------|--------|
| 05-00-* | infra | 0 | New test files + Makefile targets + .gitignore exception scaffolded | scaffold | `cd analysis && uv run pytest tests/test_spot_check.py tests/test_sensitivity_sweep.py tests/test_manifest.py --collect-only` | Wave 0 | ⬜ |
| REPORT-02-a | REPORT-02 | 1 | Seeded 5-row draw deterministic from run_id bdaf5c7ba5a2 | unit | `pytest tests/test_spot_check.py::test_seeded_draw_deterministic -x` | ❌ Wave 0 | ⬜ |
| REPORT-02-b | REPORT-02 | 1 | Blockscout URLs well-formed (`https://celo.blockscout.com/tx/0x...`) | unit | `pytest tests/test_spot_check.py::test_blockscout_urls_wellformed -x` | ❌ Wave 0 | ⬜ |
| REPORT-02-c | REPORT-02 | 1 | Build-time curl logs HTTP status per row; network-optional (no fail on offline) | integration | `pytest tests/test_spot_check.py::test_curl_logging_network_optional -x` | ❌ Wave 0 | ⬜ |
| REPORT-03-a | REPORT-03 | 1 | `sensitivity_sweep.json` schema valid + 9 cells, grid = rate{1,5,10}×usd{2.5e-6,5e-6,7.5e-6} | unit | `pytest tests/test_sensitivity_sweep.py::test_schema_and_grid -x` | ❌ Wave 0 | ⬜ |
| REPORT-03-b | REPORT-03 | 1 | Each cell RE-EVALUATES the 4 qualitative convex-dominance conditions + firing_condition (not interpolated); no cost-model/Δ/κ introduced | unit | `pytest tests/test_sensitivity_sweep.py::test_per_cell_conditions_recomputed -x` + `! grep -rE 'rate_per_event\|USD_per_query\|kappa' analysis/src/` (no new cost-model code) | ❌ Wave 0 | ⬜ |
| REPORT-04-a | REPORT-04 | 1 | MANIFEST pins exist (panel sha256 a72a4ee…, analysis/uv.lock SHA, pnpm-lock.yaml SHA, subgraph block-pins, bdaf5c7ba5a2 artifact sha256s, PDF) | unit | `pytest tests/test_manifest.py::test_pins_present -x` | ❌ Wave 0 | ⬜ |
| REPORT-04-b | REPORT-04 | 1 | `make verify-reproducibility` exits 0 on match, 1 on tamper | smoke | `pytest tests/test_manifest.py::test_verify_repro_exit_codes -x` (fills Makefile STUB ~L47) | ❌ Wave 0 | ⬜ |
| REPORT-01-a | REPORT-01 | 2 | `make report-ichi` exits 0; `reports/ichi.pdf` >50KB; markdown-only rejected | smoke (build) | `make report-ichi && test $(stat -c%s reports/ichi.pdf) -gt 51200` | ❌ Wave 0 target | manual/quarto |
| REPORT-01-b | REPORT-01 | 2 | PDF dual-signature greppable via pdftotext (ichi.qmd) | integration (quarto-skip-guarded) | `pytest tests/test_null_result_template.py::test_ichi_pdf_dual_signature -x` | ✅ extend, skip-guarded | ⬜ |
| AF-03-guard | AF-03/AF-12 | 2 | PDF text contains gate_passes FALSE + `0.0474` + `null_strip_unavailable`; forbidden strings ("pass with caveat", "positive result") ABSENT | integration (quarto-skip-guarded) | `pdftotext reports/ichi.pdf - \| grep` required + assert-absent forbidden | ❌ Wave 0 | ⬜ |
| regression | all | each wave | full 207-suite stays green incl. 3 quarto-skips | regression | `cd analysis && uv run pytest -x` | ✅ exists | ⬜ |

*Status: ⬜ pending · ✅ green · ❌ red*

---

## Wave 0 Requirements

- [ ] `analysis/tests/test_spot_check.py` — REPORT-02 (seeded determinism + URL format + network-optional curl logging)
- [ ] `analysis/tests/test_sensitivity_sweep.py` — REPORT-03 (schema + 9-cell pre-reg grid + per-cell qualitative-condition recompute + no-new-cost-model grep)
- [ ] `analysis/tests/test_manifest.py` — REPORT-04 (pins present incl. CORRECT lockfile names `analysis/uv.lock` + `pnpm-lock.yaml` — NOT `package-lock.json`/root uv.lock; sha256 match; tamper→exit-1)
- [ ] Extend `analysis/tests/test_null_result_template.py` — ichi.qmd dual-signature + verdict-not-narrowed test (keep `quarto_skipped` guard)
- [ ] `Makefile` targets: `report-ichi` (NEW, quarto render + TinyTeX self-install + curl spot-check logging), `verify-reproducibility` (FILL STUB ~lines 47-49); add to `.PHONY`
- [ ] `.gitignore` exception for `data/fits/ichi/bdaf5c7ba5a2/` (Option C-hybrid: commit the <50KB run-dir artifacts as repro evidence; pin panel by sha256 + document `cli.py materialize` regeneration rather than committing the large parquet)

*No framework install needed — pytest + the quarto-skip pattern already present. quarto binary is an operator prerequisite (this env lacks it → render tests MUST stay skip-guarded to preserve the 207-green suite).*

---

## Manual-Only Verifications

| Behavior | Req | Why Manual | Instructions |
|----------|-----|------------|--------------|
| PDF renders + is non-empty + math typesets | REPORT-01 | Requires quarto + TinyTeX (absent in CI/this env) | On a quarto-equipped machine: `make report-ichi` → open `reports/ichi.pdf`, confirm equations render + size >50KB |
| Blockscout URLs return live HTTP 200 | REPORT-02 | Requires network (free-tier/offline discipline) | `make report-ichi` logs HTTP status per row; on a networked machine confirm 5×200, else "unverified (no network)" |
| Fresh-clone reproducibility | REPORT-04 | Requires a clean clone | fresh clone → `make verify-reproducibility` → exit 0 (Option C-hybrid: committed bdaf5c7ba5a2 artifacts checksummed; panel regenerated via documented `cli.py materialize` + sha256 match) |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependency
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (3 new test files + 2 Makefile targets + .gitignore exception)
- [ ] No watch-mode flags
- [ ] Render tests skip-guarded (207-green preserved); build target hard-requires quarto
- [ ] Verdict-not-narrowed guard test present (AF-03)
- [ ] `nyquist_compliant: true` set after Wave 0 lands

**Approval:** pending
