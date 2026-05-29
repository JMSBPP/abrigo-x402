---
phase: 05-reporting-iteration-1-pdf-deliverable-l7
plan: 03
subsystem: reporting
tags: [quarto, latex, hawkes, carr-madan, report, pdf, null-result, af-03]

# Dependency graph
requires:
  - phase: 04.1.1
    provides: "canonical run_id bdaf5c7ba5a2 fit/gate/firing/sensitivity JSON artifacts + DISPOSITION_MEMO + DIAGNOSTIC"
  - phase: 05-00
    provides: "report-ichi Makefile skeleton (rm -f + size gate + quarto hard-prereq), null_result.qmd dual-signature template, _evidence_branches.qmd partial"
  - phase: 05-01
    provides: "sensitivity_sweep.json (9-cell pre-reg grid, cost-prior-invariant convex-dominance conditions)"
  - phase: 05-02
    provides: "abrigo_x402.report.spot_check (seeded_spot_check + verify_url_status), reports/MANIFEST.md, make verify-reproducibility"
provides:
  - "reports/ichi.qmd — the Iteration-1 PDF deliverable SOURCE (REPORT-01): research-paper-style near-miss writeup with typeset equations + honest 3/4 verdict"
  - "finalized make report-ichi (--execute-param + curl spot-check logging + sole producer of reports/ichi.pdf)"
  - "retargeted render-null-result-pdf (off reports/ichi.pdf -> _diagnostics/null_result_$FIRING.pdf)"
  - "AF-03 verdict-not-narrowed source-grep CI guard (runs without quarto) + 2 quarto-skip-guarded PDF-text tests"
affects: [phase-06, cycle-closure, iteration-2]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Research-paper-style Quarto .qmd (latex-econ-model + notation-clean discipline) specializing the HEDGE-05 null-result template"
    - "AF-03 verdict-integrity guard in TWO layers: NON-render source-grep (CI, runs without quarto) + quarto-skip-guarded PDF-text assertion (quarto machine / 05-04 checkpoint)"
    - "Sole-producer discipline: report-ichi owns reports/ichi.pdf; legacy render-null-result-pdf retargeted to a diagnostics path to kill the two-producers-one-artifact repro trap"

key-files:
  created:
    - "reports/ichi.qmd"
    - ".planning/phases/05-reporting-iteration-1-pdf-deliverable-l7/05-03-SUMMARY.md"
  modified:
    - "Makefile"
    - "analysis/tests/test_null_result_template.py"

key-decisions:
  - "PDF render is PENDING (quarto absent in this env) — the DESIGNED path, not a blocker. The .qmd source + report-ichi wiring are complete; the rendered PDF is a quarto-machine / 05-04-checkpoint deliverable."
  - "Forbidden narrowing strings rephrased out of the anti-fishing list (Rule-1): the AF-03 grep is context-blind, so the literal phrases ('pass with caveat' etc.) could not appear even inside the REJECTED-relabelings list; rephrased to 'four such forbidden relabelings (per disposition memo)' without printing the literals."
  - "USDC literal dropped (Rule-1): 'there is no USDC' violated the SC-2/CLAUDE.md no-USDC discipline + the source-grep guard; rephrased to 'the only stablecoin leg is USDT'."
  - "Notation: Lambda dual-role (LR statistic vs compensator Lambda_i(t)) disambiguated by subscript+argument; both standard in their literatures (flagged exception, kept)."

patterns-established:
  - "Two-layer AF-03 verdict guard (source-grep CI + PDF-text quarto-machine)"
  - "labeled p=0.0474 discipline: p-value labeled as a p-value, statistic D=0.148 named separately; grep asserts the LABELED form so a bare/statistic-labeled 0.0474 cannot pass"

requirements-completed: [REPORT-01]

# Metrics
duration: ~6min
completed: 2026-05-29
---

# Phase 5 Plan 03: ICHI Iteration-1 PDF Deliverable Source Summary

**reports/ichi.qmd — a research-paper-style near-miss writeup with typeset Hawkes/branching-ratio/LR/time-rescaling-KS/Carr-Madan equations, the honest gate_passes=FALSE (3/4) verdict (labeled KS p=0.0474, D=0.148, firing null_strip_unavailable), the 3-run methodology-validation table, anti-fishing provenance, and the convexity-justified/calibration-caveated v2-path — plus a finalized make report-ichi and a two-layer AF-03 verdict-not-narrowed guard.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-05-29T17:51:42Z
- **Completed:** 2026-05-29T17:57:18Z
- **Tasks:** 2
- **Files modified:** 4 (1 created qmd, Makefile, test file, this summary)

## Accomplishments
- Authored `reports/ichi.qmd` (535 lines) as the REPORT-01 deliverable source: a concise research-paper writeup that READS (never recomputes) the canonical `bdaf5c7ba5a2/` artifacts via Pattern-1 read-only Python cells, with typeset equations and the locked methodology-validation + honest-near-miss narrative.
- Finalized `make report-ichi`: added `--execute-param firing_condition=null_strip_unavailable` (populates the included partial's branch selector) + per-row Blockscout curl spot-check logging (SC-2, network-optional, non-failing); kept the rm -f stale guard + >50KB size gate + markdown-fallback rejection.
- Retargeted the colliding legacy `render-null-result-pdf` off `reports/ichi.pdf` to `_diagnostics/null_result_$FIRING.pdf`, making `report-ichi` the SOLE producer of `reports/ichi.pdf`.
- Added a NON-render AF-03 source-grep guard (`test_ichi_qmd_source_not_narrowed`, runs in CI without quarto) + two quarto-skip-guarded PDF-text tests (`test_ichi_pdf_dual_signature`, `test_ichi_verdict_not_narrowed`).

## Skills Invoked (CONTEXT mandate — record for the 05-04 checkpoint)
- **latex-econ-model** — drove the §2 Model structure and typeset all five equation blocks: the bivariate Hawkes intensity (@eq-hawkes), branching ratio eta=rho(alpha/beta) (@eq-eta), boundary-correct LR with the 50:50 chi2(0):chi2(1) mixture null (@eq-lr), time-rescaling KS DeltaLambda~Exp(1) (@eq-rescale), and the Carr-Madan strip integral (@eq-carrmadan). Used `align`/`equation` environments, `\bm` for the adjacency matrix, `\left(...\right)` auto-sizing, and amsmath/amssymb/mathtools/bm in include-in-header.
- **notation-clean (fast path, --mode both, proactive)** — audited the math I introduced against the Econometrica reserved-symbol rules (beta, r, t, T, k, kappa, tau). Findings + dispositions (the **notation-clean diff** for 05-04):
  - **[Mid] Lambda dual-role** — `Lambda` is the LR statistic (@eq-lr) AND `Lambda_i(t)` is the compensator (@eq-rescale). KEPT as a flagged exception: both are the standard symbol in their respective literatures (LR test; time-rescaling theorem), and they are disambiguated by the subscript `i` + the argument `(t)`. No rename.
  - **[High] kappa (κ) reserved index** — CONFIRMED ABSENT. The locked equation set excludes any complexity index kappa (CLAUDE.md non-negotiable + AF-12). Grep `! grep -qE '\bkappa\b|κ'` clean.
  - **[Mid] r, T, k in Carr-Madan** — IN their reserved standard roles (risk-free rate, maturity, log-strike). Correct usage, no flag.
  - **[Low] theta reuse** — `theta` for the power-law exponent (v2 section) and `\hat\theta` for MLE params. Conventional; kept.
  - Net: 1 flagged exception kept (Lambda), 0 renames, 0 math changed. Notation pass: clean to Econometrica standard.
- **latex-doc** — checked the math for compile correctness (balanced environments, `\operatorname{Re}`, `\overset`, footnote `[^ksfull]`, cross-refs `@eq-*`). The actual LaTeX compile is PENDING (quarto absent); the source-grep test guards structure in the interim.
- **read-paper** — sourced the five locked citations from prior-phase provenance (Brown et al. 2002 time-rescaling, Carr-Madan 1998 strip, Daw & Pender 2017 Hawkes queues, Filimonov & Sornette 2014 calibration, Kirchner 2015 INAR, Self & Liang 1987 boundary-LR). Citations rendered in a References section.

## Task Commits

1. **Task 1: Author reports/ichi.qmd** — `27fd03c` (feat)
2. **Task 2: Finalize make report-ichi + retarget render-null-result-pdf + AF-03 source-grep guard + render tests** — `c7a5a0f` (feat)

**Plan metadata:** (this docs commit)

## Files Created/Modified
- `reports/ichi.qmd` (created) — the Iteration-1 deliverable source (REPORT-01): YAML dual-signature front matter (HEDGE05-NULL-RESULT-V1 + firing param), abstract, §1 Intro, §2 Model (5 typeset equations), §3 Data (832->778), §4 Methodology (3-run table + 3 root-cause bugs), §5 Results (read-only artifact cells: eta~0.600 lower bound, decay-AIC table, LR 561.29 p=0.0, held-out +114 nats, 4-criterion gate 3/4, KS knife-edge labeled p=0.0474/D=0.148, 4/4 convex-dominance) + `{{< include _templates/_evidence_branches.qmd >}}`, §6 anti-fishing (9 rejected post-hoc changes), §7 spot-check, §8 cost-prior sweep, §9 convexity-justified/calibration-caveated v2-path, §10 conclusion + reproducibility, References.
- `Makefile` (modified) — finalized report-ichi (execute-param + curl spot-check logging); retargeted render-null-result-pdf off reports/ichi.pdf.
- `analysis/tests/test_null_result_template.py` (modified) — +3 tests (1 CI source-grep + 2 quarto-skip-guarded), +`re` import.

## Decisions Made
- **PDF render PENDING by design.** quarto is absent in this env; per critical invariant 5 + 05-VALIDATION Manual-Only, the .qmd + target are authored/wired and the PDF render is deferred to a quarto-equipped machine / the 05-04 checkpoint. `verification_pass: pending-render` for REPORT-01-a/b. This is NOT a blocker.
- See key-decisions in frontmatter for the two Rule-1 rephrasings (forbidden-narrowing list + USDC literal) and the Lambda notation exception.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] AF-03 grep is context-blind — rephrased the rejected-relabelings list so the literal forbidden strings never appear**
- **Found during:** Task 1 (authoring §6 anti-fishing provenance)
- **Issue:** The plan's §6 spec lists the 9 rejected post-hoc changes including "relabeled as 'pass with caveat' / 'near-miss positive' / 'directionally positive' / 'exploratory positive'". Printing those literals — even as the things being REJECTED — trips the AF-03 forbidden-string grep (`! grep -qiE 'pass with caveat|near-miss positive|directionally positive|exploratory positive'`), which is context-blind.
- **Fix:** Rephrased item 8 to "Relabeling gate_passes=FALSE as any softened or positive-leaning verdict (the disposition memo enumerates four such forbidden relabelings) — not done; the verdict reads FALSE, full stop." The provenance is preserved (points to the memo) without printing the banned literals.
- **Files modified:** reports/ichi.qmd
- **Verification:** `! grep -qiE 'pass with caveat|near-miss positive|directionally positive|exploratory positive' reports/ichi.qmd` → clean; `test_ichi_qmd_source_not_narrowed` passes.
- **Committed in:** `27fd03c` (Task 1 commit)

**2. [Rule 1 - Bug] USDC literal dropped to honor the SC-2 / CLAUDE.md no-USDC discipline**
- **Found during:** Task 1 (authoring §1 Introduction)
- **Issue:** Wrote "the data-payment unit is one USDT; there is no USDC in this substrate." The literal "USDC" violates the CLAUDE.md non-negotiable (USDT framing, never USDC) and the source-grep guard's USDC-absent assertion — even in the negating phrase.
- **Fix:** Rephrased to "the data-payment unit is one USDT (the only stablecoin leg in this substrate)."
- **Files modified:** reports/ichi.qmd
- **Verification:** `! grep -qi 'usdc' reports/ichi.qmd` → clean.
- **Committed in:** `27fd03c` (Task 1 commit)

**3. [Rule 3 - Blocking] Missing `re` import in the test module**
- **Found during:** Task 2 (running the targeted test)
- **Issue:** `test_ichi_qmd_source_not_narrowed` uses `re.search` but `re` was not imported in test_null_result_template.py — NameError on first run.
- **Fix:** Added `import re` to the test module imports.
- **Files modified:** analysis/tests/test_null_result_template.py
- **Verification:** Targeted `pytest tests/test_null_result_template.py -q` → 4 passed, 3 skipped.
- **Committed in:** `c7a5a0f` (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (2 Rule-1 verdict/discipline rephrasings, 1 Rule-3 blocking import)
**Impact on plan:** All three necessary for correctness and the AF-03/SC-2 discipline gates. No scope creep; no verdict narrowing (the rephrasings strengthen the no-narrowing discipline by removing the banned literals entirely).

## Issues Encountered
- None beyond the deviations above. The KS-label discipline (labeled `p=0.0474`, statistic `D=0.148`) and the correct `_templates/` include path were authored right the first time and grep-confirmed.

## Verification

- Task 1 acceptance greps: ALL-OK (exists, null_strip_unavailable, labeled p=0.0474, correct include, wrong include absent, HEDGE05 marker, 3-run ids, no narrowing, no kappa, no USDC).
- Task 2 acceptance: `quarto render ichi.qmd` + `execute-param firing_condition=null_strip_unavailable` + `seeded_spot_check` present in Makefile; `render _templates/null_result.qmd ... --output ichi.pdf` ABSENT + `_diagnostics/null_result` present (collision retargeted); `grep -c 'shutil.which("quarto")'` = 3 (>= 2); all 3 new tests present.
- Targeted thread-pinned `pytest tests/test_null_result_template.py -q`: **4 passed, 3 skipped** (the 3 skips = the pre-existing render test + the 2 new quarto-skip-guarded render tests; the source-grep companion PASSES in CI without quarto). Full slow suite deliberately NOT run (critical invariant 6).
- Fit NOT recomputed; no κ; no new cost model. Read-only Pattern-1 artifact consumption.
- PDF render: **PENDING** (quarto absent) — the designed path; `verification_pass: pending-render` for REPORT-01-a/b (Manual-Only on a quarto machine).

## AF-12 OUT-OF-SCOPE (verbatim from plan/context)

Per 05-CONTEXT.md (REPORT-03 sensitivity-sweep presentation), held verbatim as the AF-12 + CLAUDE.md non-negotiable boundary:

> **NO new cost-leg model, NO dominance-Δ implementation, NO κ index** (AF-12 + CLAUDE.md non-negotiable). If a cell's condition set is invariant to the cost priors (likely, since the conditions derive from the DGP density not the cost leg), report that invariance honestly as the finding.

And the phase-level out-of-scope (05-CONTEXT.md Phase Boundary):

> **Out of scope (own phases):** Iteration-2 / Steer (Phase 6); the power-law kernel sweep + more-data certification (v2 / DGP-V2-01); any re-fit or re-hedge of the DGP (Phase 04.1.1 is closed); deployed Solidity hedge contracts (Iteration 3+).

## Next Phase Readiness
- REPORT-01 source is COMPLETE. The PDF is render-PENDING (quarto absent); on a quarto-equipped machine `make report-ichi` produces reports/ichi.pdf > 50KB and the 2 quarto-skip-guarded tests + `test_ichi_verdict_not_narrowed` activate.
- Plan 05-04 (the documented checkpoint) inherits: the notation-clean diff above, the .qmd-satisfies-.ipynb SC-1 deviation, and the render-PENDING state.
- Cycle closure (push origin -> PR upstream -> merge upstream) remains gated on the PDF rendering + `make verify-reproducibility` green + phase VERIFICATION passing (CLAUDE.md cycle-closure). Do NOT merge a verdict dressed as a pass (AF-03 carries into the merge).

## Self-Check: PASSED

- FOUND: reports/ichi.qmd
- FOUND: Makefile
- FOUND: analysis/tests/test_null_result_template.py
- FOUND: .planning/phases/05-reporting-iteration-1-pdf-deliverable-l7/05-03-SUMMARY.md
- FOUND commit: 27fd03c (feat 05-03: author reports/ichi.qmd)
- FOUND commit: c7a5a0f (feat 05-03: finalize report-ichi + retarget + AF-03 guard)

---
*Phase: 05-reporting-iteration-1-pdf-deliverable-l7*
*Completed: 2026-05-29*
