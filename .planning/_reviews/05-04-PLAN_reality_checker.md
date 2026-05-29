# Reality-Checker RE-REVIEW — 05-04-PLAN.md (numbers-match consult + VERIFICATION grid + cycle-closure PR)

**Reviewer:** Reality Checker (Reviewer 1)
**Date:** 2026-05-29 (re-review of revised plan)
**Artifact:** `.planning/phases/05-reporting-iteration-1-pdf-deliverable-l7/05-04-PLAN.md`

## VERDICT

PASS

Both prior MAJORs are CLOSED. The premature-approval pattern is eliminated: `verification_pass` is now TRI-STATE (`pass` ONLY after a rendered >50KB PDF exists AND the AF-03 PDF-text grep ran GREEN, never on skipped tests), and the cycle-closure PR is HARD-gated on a rendered+grepped PDF + a RESOLVED (non-PENDING) MANIFEST pin + clean-checkout `verify-reproducibility` green — with an explicit HALT instruction when quarto is absent (as it is here). The KS source-of-truth self-contradiction is resolved to a single canonical `p=0.0474` (the only `0.04735` occurrences are negative-context "NOT 0.04735"). All three MINORs addressed.

---

## Prior findings — confirm-closed

### PRIOR MAJOR-1 (premature `verification_pass:true` / PDF-less PR) — CLOSED
- `verification_pass` is now TRI-STATE `pass | pending-render` (interfaces line 79; truths line 18; acceptance line 119): `pass` ONLY when `reports/ichi.pdf` exists AND `pdftotext … | grep` confirms {null_strip_unavailable, labeled p=0.0474, gate FALSE} present + the 4 forbidden strings absent (AF-03 PDF grep GREEN, not skipped). Otherwise `pending-render`, and the Task-2 checkpoint REFUSES to open the PR.
- The PR open is HARD-gated (Task 2 line 133): do NOT proceed unless (i) PDF exists >50KB; (ii) MANIFEST PDF pin RESOLVED (real sha256, not PENDING) + `make verify-reproducibility` exit 0 with the PDF line STRICT incl. the clean-checkout worktree run; (iii) AF-03 PDF-text grep GREEN (not skipped); (iv) Task-1 `verification_pass: pass`.
- Explicit HALT when quarto absent (line 133 + <what-built> step 1 line 150): "render reports/ichi.pdf on a quarto machine … then resume — do NOT open a PDF-less PR." LIVE-confirmed quarto is absent in this env, so the executor WILL halt rather than certify an unrendered PDF — the exact fix demanded.
- A PENDING PDF pin is explicitly declared NOT a closeable state (line 99/133). The phase cannot be certified "pass" on a PDF nobody rendered.

### PRIOR MAJOR-2 (KS source-of-truth self-inconsistency: 0.04735 vs 0.0474) — CLOSED
- LIVE-VERIFIED: `grep -n "0.04735" 05-04-PLAN.md` returns only NEGATIVE-context lines ("NOT `0.04735`"). The source-of-truth block (line 72) now states `KS held-out leg-0 p-value = 0.0474 (full 0.047350…)`, single canonical rounding aligned with the AF-03 grep `p ?= ?0.0474` (line 77) and the PR body (line 135).
- The label discipline is enforced: line 72 states explicitly "the 0.0474 is the P-VALUE, never the statistic; STATISTIC D = 0.148"; the numbers-match consult (1a, line 97) rejects any bare or wrongly-labeled `0.0474` and any `0.04735` divergence.
- LIVE-VERIFIED the underlying values (see 05-03 review): leg-0 p=0.047350… → `p=0.0474`; ks_statistic=0.14799… → `D=0.148`; leg-1 p=0.05643… → `p=0.0564`. All correct.

### PRIOR MINOR-1 (verify-reproducibility weak while pins PENDING) — CLOSED
The gate now requires the PDF pin RESOLVED (non-PENDING) on the build machine before close, AND the clean-checkout worktree run (line 99/118/133). On a fresh clone the panel is committed (05-02), so the gate is no longer "as strong as a skipped pin."

### PRIOR MINOR-2 (blanket "commit all" sweeps unrelated 04.1.1 work) — CLOSED
Task 2 (line 135 + <what-built> step 3) enumerates the EXACT Phase-5 pathspec (reports/ichi.qmd, ichi.pdf, MANIFEST.md, analysis/src/abrigo_x402/report/, the 4 test files, Makefile, .gitignore, data/fits/.gitignore, sensitivity_sweep.json, CORRECTIONS.md, the panel parquet, the 05-* planning dir), explicitly EXCLUDES the 04.1.1 working-tree changes, and mandates a `git status --short` review first. LIVE git status confirms unrelated 04.1.1 files are present in the tree, so this enumeration is necessary and correct.

### PRIOR MINOR-3 (branch name only suggested → verify query misses) — CLOSED
The branch name is PINNED non-optional `phase-05-iteration-1-pdf` (interfaces line 64), used identically in the push, PR `--head`, and the checkpoint verify query (line 138). No name drift.

---

## Foundation re-confirmed (no regression)
- Git workflow correct: LIVE `git remote -v` confirms origin=JMSBPP/abrigo-x402, upstream=wvs-finance/abrigo-x402; PR command `gh pr create --repo wvs-finance/abrigo-x402 --base master --head JMSBPP:phase-05-iteration-1-pdf` matches CLAUDE.md; push to origin only; never push upstream. ✓
- PRE-FLIGHT added: assert origin URL + `gh auth status` before push (line 63/151). ✓
- Merge user-gated: Task 2 is `checkpoint:human-verify gate="blocking"`; executor opens PR and PAUSES; "MERGE is YOUR action" + resume-signal. ✓
- PR body honest (gate_passes=FALSE, null_strip_unavailable, labeled p=0.0474, convexity-justified-but-calibration-caveated, false-null correction, v2 path NAMED-not-executed); 4 narrowing strings forbidden + grep-checked. ✓
- Commit/PR trailers correct (Co-Authored-By + Generated-with). ✓
- Specialist (DevOps Automator + Analytics Reporter) named with why. ✓

---

## NEW findings

### NEW MINOR-1 — same AF-03 grep regex caveat as 05-03 (`p ?= ?0\.0474` won't match `p-value = 0.0474`)
**Evidence:** The acceptance grep on 05-VERIFICATION-pre.md (line 122) and the PDF-text gate (line 133) use `p ?= ?0.0474`, which (LIVE-tested) matches `p=0.0474` / `p = 0.0474` but NOT `**p-value = 0.0474**`. Since the VERIFICATION doc + PR body are authored to use the `p=0.0474` form, this passes; flagged only for cross-plan consistency with the 05-03 NEW MINOR-1.
**Fix (optional):** Align with 05-03 — broaden to `p ?(-value)? ?= ?0\.0474`. Not blocking.

---

## Cross-check summary
- Premature approval: CLOSED — tri-state verification_pass + hard gate on rendered+grepped PDF + resolved pin + clean-checkout + HALT-when-quarto-absent. (LIVE-confirmed quarto absent → executor halts.)
- KS source-of-truth: CLOSED — single canonical `p=0.0474`, no competing 0.04735, statistic D=0.148 labeled. (LIVE-verified)
- Cycle-closure PR repo/base/head correct; merge user-gated; honest body. (clean, LIVE-verified remotes)
- Exact pathspec excludes 04.1.1; pinned branch name. (closed)
- Specialist: present. (clean)

**BLOCKER: 0 · MAJOR: 0 (2 prior CLOSED) · MINOR: 1 NEW (cosmetic grep regex, shared with 05-03)**
