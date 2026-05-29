---
phase: 06
slug: iteration-2-swap-surface-validation-on-steer-ccop-usdt
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-29
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Iteration-2 re-run: the pipeline is FROZEN (no edits to `fetch/src`/`analysis/src` except the standalone pre-Iteration-2 baseline fixes). The EXPECTED outcome is a null (`null_cost` from the cost-leg straddle). The deliverable READS the run artifacts; the cost-leg verdict is pre-registered, never tuned.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework (Python)** | `pytest` 9.x (analysis/), thread-pinned BLAS (Pattern I — OMP/MKL/OpenBLAS/NumExpr=1 before numpy import) |
| **Framework (TS)** | `vitest` (fetch/) — hosts the authoritative SC-5 protocol-agnosticism leak gate |
| **Config file** | `analysis/pyproject.toml` (pytest), `fetch/vitest.config.ts` |
| **Quick run command** | `cd analysis && OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 uv run pytest tests/test_null_result_template.py -x` |
| **Full suite command** | `cd analysis && OMP_NUM_THREADS=1 … uv run pytest` + `cd fetch && pnpm test` + `make verify-reproducibility` + `make leak-check` |
| **Estimated runtime** | quick ~10–30s; full ~5–8min |
| **Quarto note** | quarto 1.9.38 installed (~/.local, outside repo); render tests stay skip-guarded so the no-quarto green baseline is preserved. The generic renderer (`render_null_result_pdf`) fix un-skips `test_pdf_dual_signature_when_quarto_available`. |

---

## Sampling Rate

- **After every task commit:** quick run of the affected test (renderer-fix RED→GREEN; `pytest scripts/test_cost_leg_check.py` for the straddle tool)
- **After every plan wave:** `make leak-check` + `cd fetch && pnpm test protocol-agnostic` + targeted analysis suite
- **Before `/gsd:verify-work`:** full analysis suite (thread-pinned) green + `cd fetch && pnpm test` + `make verify-reproducibility` (extended for the steer PDF) + the REPRO-02 empty-diff attestation
- **Max feedback latency:** 30s (quick); ~8min (full)

---

## Per-Task Verification Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? | Status |
|--------|----------|-----------|-------------------|-------------|--------|
| REPRO-01 | genuine protocol-coupling scrubbed + SC-5 lint passes; scoped `ichi` grep (excl. comments/docstrings) clean; AF-12 re-scope note present | leak-gate | `make leak-check` (extend with scoped ichi layer) + `cd fetch && pnpm test protocol-agnostic` + `grep -q "REPRO-01" notes/PRE_REGISTRATION.md` | ⚠️ leak-check exists, lacks ichi layer; SC-5 test exists | ⬜ |
| REPRO-02 | empty `git diff` on frozen dirs across the iter boundary (measured from the re-baselined HEAD after the baseline fixes) | smoke/attestation | `git diff <iter1-baseline-sha> HEAD -- fetch/src analysis/src` → empty | ❌ Wave 0 — author the attestation check | ⬜ |
| REPRO-03 | straddle rule → `notes/steer_cost_leg_bound.md` verdict:FAIL (`null_cost`), written BEFORE any Steer fetch; rule pre-registered before the verdict | unit + commit-ordering | `pytest scripts/test_cost_leg_check.py` + `git log` shows rule predates verdict + `grep -q "null_cost" notes/steer_cost_leg_bound.md` | ❌ Wave 0 — author `scripts/cost_leg_check.py` + test | ⬜ |
| REPRO-04 | `panel_construction == "v3-anchor-only"` honored; Q9 trigger EVALUATED + logged; fallback DEFERRED note present | unit | assert `load_protocol("protocols/steer.toml")` panel field; `grep -q "fallback.*deferred" notes/PRE_REGISTRATION.md`; trigger-eval in fit_report | ✅ steer.toml set; ⚠️ Q9 fallback modules absent (deferred per CONTEXT) | ⬜ |
| HEDGE-05(a) | `decide_firing_condition` returns `null_cost` on FAIL doc; null PDF renders with dual signature | unit + render | `pytest tests/test_null_result_template.py::test_pdf_dual_signature_when_quarto_available` + `make render-null-result-pdf FIRING=null_cost` | ✅ decision test exists (fixture `hedge_05_null_cost`); ⚠️ render test exposes the papermill bug until fixed | ⬜ |
| regression | full analysis + fetch suites stay green (incl. skip-guards) | regression | `cd analysis && uv run pytest` + `cd fetch && pnpm test` | ✅ exists | ⬜ |

*Status: ⬜ pending · ✅ green · ❌ red*

---

## Wave 0 Requirements

- [ ] **Generic-renderer fix** in `analysis/src/abrigo_x402/hedge/null_result.py` — `-P firing_condition:X` → `-M firing_condition:X` (pandoc metadata; template already reads `{{< meta params.firing_condition >}}`) + repo-root path anchoring. **Standalone pre-Iteration-2 baseline commit** (CONTEXT Decision 4). Un-skips + greens `test_pdf_dual_signature_when_quarto_available`.
- [ ] **Materialize-namespace generalization** in `cli.py` — derive `data/raw/<protocol>/` from `--protocol-toml` (replaces the `data/raw/ichi/<pool>` hardcode at L67). **Standalone baseline commit** (collision 2).
- [ ] **Coupling scrub** of genuine `ichi` couplings in `fetch/src`/`analysis/src`; leave protocol-neutral comments per the scoped-grep re-scope. **Baseline commit.**
- [ ] `scripts/cost_leg_check.py` — reads `steer.toml` cost-leg band + the pre-registered straddle rule, applies conservative-FAIL, writes `notes/steer_cost_leg_bound.md` (verdict:FAIL, `null_cost`). Covers REPRO-03.
- [ ] `scripts/test_cost_leg_check.py` (or `analysis/tests/`) — asserts the FAIL verdict + frontmatter shape.
- [ ] `make iteration-2-full` target (NEW) + extend `make leak-check` with the scoped `ichi` layer + extend `make render-null-result-pdf` to drop `--execute-param`.
- [ ] REPRO-02 empty-diff attestation mechanism pinning the iter-1-baseline sha (post-baseline-fixes HEAD; iteration-1-complete marker ≈ PR#1 merge `87991ac`).
- [ ] `reports/MANIFEST.md` extension / steer content-check in `verify-reproducibility` for `reports/steer_null_result.pdf` (mirror ichi: size>50KB + `null_cost` string + HEDGE05 marker + AF-03 forbidden-narrowing guard).
- [ ] AF-12/AF-03 pre-registration notes in `notes/PRE_REGISTRATION.md`: (a) the straddle decision rule (BEFORE the check), (b) the REPRO-01 scoped-grep re-scope, (c) the Q9 fallback-deferred + signal-scope caveat.

*quarto is an operator prerequisite (installed here); render tests stay skip-guarded so the no-quarto baseline is preserved.*

---

## Manual-Only Verifications

| Behavior | Req | Why Manual | Instructions |
|----------|-----|------------|--------------|
| Steer null PDF renders + math typesets | HEDGE-05/REPORT-01 | Requires quarto + TinyTeX | `make render-null-result-pdf FIRING=null_cost` → open `reports/steer_null_result.pdf`, confirm cost-leg headline + DGP-support + REPRO-02 attestation + size>50KB |
| cCOP/USDT Blockscout provenance live | REPRO-02 | Requires network (free-tier discipline) | spot-check logs HTTP status per row; confirm on a networked machine |
| Fresh-clone REPRO-02 empty-diff | REPRO-02 | Requires clean clone + the pinned baseline sha | fresh clone → `git diff <baseline-sha> HEAD -- fetch/src analysis/src` → empty |

---

## Validation Sign-Off

- [ ] All requirements have an automated verify or a Wave 0 dependency
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers the baseline-fix commits (renderer, materialize, scrub) BEFORE the REPRO-02 diff window
- [ ] AF-03/AF-12 pre-registration notes precede the verdicts they govern (commit-ordering proof)
- [ ] The null verdict is recorded AS-OBSERVED — never narrowed to a pass
- [ ] `nyquist_compliant: true` set after Wave 0 lands

**Approval:** pending
