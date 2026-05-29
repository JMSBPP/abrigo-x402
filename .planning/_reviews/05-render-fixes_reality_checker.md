# Reviewer 1 (Reality Checker) — Phase 5 render-mechanics diff

**Scope:** `/tmp/render_session.diff` = `git diff -- reports/ichi.qmd Makefile reports/MANIFEST.md` + untracked `reports/ichi.pdf` (517,238 B). 5 build-mechanics edits, pre-commit / pre-PR. Default posture: NEEDS WORK; require evidence.

**Verification I actually ran (not just claimed):**
- `git diff` of all three files; read `ichi.qmd`, `Makefile:48-74,180-206`, `MANIFEST.md` diff.
- `sha256sum reports/ichi.pdf` → `654523fc...e39c5` = matches the new MANIFEST pin. Size 517,238 B > 50 KB.
- `date -u -d @1780012800` → `2026-05-29 00:00:00 UTC` = consistent with qmd `date: 2026-05-29`.
- `make verify-reproducibility` → `PASS (14/14 pins matched)`, incl. `OK: reports/ichi.pdf`.
- **Re-render durability test:** `make report-ichi` a second time → exit 0, byte-identical (`cmp` → BYTE-IDENTICAL), sha unchanged. Determinism is real on THIS machine, not a one-shot.
- `pdftotext`: `null_strip_unavailable` ×7; `gate_passes = FALSE` present; `p=0.0474` present; forbidden strings (`pass with caveat`, `positive result`, `near-miss positive`) ×0.
- `pdfinfo`: `Keywords: HEDGE05-NULL-RESULT-V1`; raw binary grep confirms the `\pdfinfo /HEDGE05Marker (HEDGE05-NULL-RESULT-V1)` custom key IS also embedded.
- Traced `firing_condition` data flow through the qmd; ran the 3 named tests + the wider null-result suite.

---

## AF-03 (verdict-narrowing) — the load-bearing concern: CLEARED

The visible **Verdict banner** (`ichi.qmd:281-286`) and the §5 conclusion (`:512`) print `firing['firing_condition']` read from the **on-disk artifact** `data/fits/ichi/bdaf5c7ba5a2/firing_condition.json` (`ichi.qmd:69`), whose value is `"null_strip_unavailable"` (verified by reading the JSON). The dropped `--execute-param firing_condition=null_strip_unavailable` fed only the Python variable at `ichi.qmd:64` (`firing_condition = "{{< meta params.firing_condition >}}"`), which has **zero downstream consumers** — grep shows it is assigned once and never read in any f-string or branch. The YAML default (`params.firing_condition: null_strip_unavailable`, `:47`) is identical to the old `--execute-param` value anyway. Net effect on the reported verdict: **none.** The PDF reports the locked verdict, sourced from the artifact, not from the (now-defaulted) param. No narrowing, softening, or relabeling.

---

## BLOCKER
(none)

## MAJOR

### MAJOR-1 — Byte-pin durability is single-toolchain; cross-machine re-render will MISMATCH and FAIL the gate
**Where:** `Makefile:66` (PDF treated as PENDING only while absent; once present, strict sha), `Makefile:190` (`quarto install tinytex` installs *latest* TinyTeX), `MANIFEST.md:55-58` (claim: "stable under `make report-ichi && make verify-reproducibility`").
**Evidence:** The render toolchain is unpinned — `pdfTeX 3.141592653-2.6-1.40.27 (TeX Live 2026/dev/Arch Linux)`, `quarto 1.9.38`, `pandoc 3.8.3`. The 517,238-B/`654523fc…` byte image is a function of pdfTeX build, embedded font files, pandoc version, and the TinyTeX package set. On a fresh clone the PDF is absent → 3-state rule marks it PENDING → `verify-reproducibility` passes 13/13 (it silently drops the PDF pin). But the moment a *different* operator runs `make report-ichi` on a different TeX/pandoc/TinyTeX version, the PDF becomes present with a **different** sha → `MISMATCH` → `verify-reproducibility` FAIL (exit 1). So the determinism is real but *local*: SOURCE_DATE_EPOCH removes the wall-clock nondeterminism, it does NOT remove toolchain-version nondeterminism. The MANIFEST text "byte-deterministic via SOURCE_DATE_EPOCH" overstates portability — it is byte-deterministic *given a fixed toolchain*.
**Why it matters for a public PR:** an upstream reviewer who regenerates the PDF to audit it will trip a red `MISMATCH` gate through no fault of the content, and may misread it as a tampered/narrowed verdict.
**Fix (pick one):**
  (a) Document the pin as toolchain-scoped: in `MANIFEST.md` state the exact `quarto`, `pandoc`, `pdfTeX` versions the `654523fc…` sha was produced under, and add a note that re-pin is expected on a different toolchain (the content-level AF-03 checks — `pdftotext` greps + the dual-signature test — are the durable guarantees, not the byte sha); or
  (b) make the PDF pin advisory: have `verify-reproducibility` treat a *present-but-mismatching* `reports/ichi.pdf` as WARN (not FAIL) when toolchain versions differ, while keeping the content greps strict; or
  (c) pin the toolchain (commit a `quarto`/`tinytex` version lock) so the byte image is actually reproducible — heaviest, only if true byte-reproducibility is a hard requirement.
**Lowest-risk:** (a). The committed PDF + content-grep tests already deliver the real guarantee; the byte sha is a convenience pin, and the MANIFEST prose should say so instead of implying machine-independence.

### MAJOR-2 — Three in-text citations render as literal broken `[@key]` in the shipped PDF
**Where:** `ichi.qmd:149` `[@self1987]`, `:160` `[@brown2002]`, `:176` `[@carr1998]`; no `bibliography:` / `csl:` in frontmatter.
**Evidence:** `pdftotext reports/ichi.pdf | grep '\[@'` returns `[@self1987]`, `[@brown2002]`, `[@carr1998]` verbatim in the body text. With no bibliography file and no CSL, citeproc has nothing to resolve these keys to, so they print raw.
**Important nuance (lowers severity, does NOT erase it):** this is **pre-existing** — `git show HEAD:reports/ichi.qmd` shows the same three `[@key]` and the same absent `bibliography:` *with* the `::: {#refs}` div present. The `#refs` div was already inert (citeproc populates it only from a bibliography, which never existed). So removing `#refs` (edit #2) did **not** regress citations and did **not** drop any reference — the hand-written 6-item bullet list is the real reference section and all 6 entries are present in the PDF (Brown, Carr & Madan, Daw & Pender, Filimonov & Sornette, Kirchner, Self & Liang — confirmed by `pdftotext`). The bug is that this diff is the moment the broken-citation PDF becomes a public artifact.
**Fix:** replace the three `[@key]` in-text refs with plain prose author-year cites (e.g. `[@self1987]` → `(Self & Liang 1987)`) to match the hand-written bibliography style. ~3 edits, no toolchain change, render stays deterministic. (Strictly out of scope of "render mechanics," but it is a visible defect in the deliverable this PR publishes.)

## MINOR

### MINOR-1 — "test suite passes" is overstated now that quarto is on PATH
**Where:** `analysis/tests/test_null_result_template.py::test_pdf_dual_signature_when_quarto_available` (calls `render_null_result_pdf` on `reports/_templates/null_result.qmd`).
**Evidence:** `uv run pytest -k dual_signature or verdict_not_narrowed or qmd_source_not_narrowed` → the 3 named tests PASS, but the broader suite has `1 failed`: the quarto-available template test errors with `ERROR: No valid input files passed to render`. Root cause is a cwd/relative-path bug in `render_null_result_pdf` (the test runs from `analysis/`, the template path `reports/_templates/null_result.qmd` resolves relative to repo root → quarto sees no input). This code is **untouched by the diff** (`git diff -- analysis/.../null_result.py reports/_templates/` is empty) and was previously *skipped* because quarto was absent. So it is not a regression from the 5 edits — but installing quarto un-skipped a latent failure, so a blanket "tests green" claim is inaccurate.
**Fix:** out of scope for this PR; either fix the path resolution in `render_null_result_pdf` (resolve template/output against repo root) or mark the test xfail with a tracking note. At minimum, do not claim a fully green suite in the PR body — scope the claim to the 3 ichi-deliverable tests, which do pass.

### MINOR-2 — `pdf-engine: pdflatex` and `quarto install tinytex` are coupled assumptions worth a one-line note
**Where:** `ichi.qmd:30` (`pdf-engine: pdflatex`), `Makefile:190` (`quarto install tinytex`).
**Evidence:** The `\pdfinfo` primitive is pdfTeX-only, so `pdflatex` is correctly required (lualatex would silently drop the custom key — the Keywords field would still carry the marker, but the belt-and-suspenders custom key would be lost). This is fine and verified working. The minor risk: an operator whose `pdflatex`/TinyTeX lacks a package the header needs would fail; the Makefile has no explicit pdflatex-present guard (only a `quarto` guard at `:189`).
**Fix:** optional — a one-line comment in the Makefile noting "pdf-engine pinned to pdflatex in qmd frontmatter; \pdfinfo is pdfTeX-only" would aid a fresh operator. Non-blocking.

---

## Claims I verified as ACCURATE (give credit where due)
- PDF size 517,238 B > 50 KB gate. ✔
- sha256 pin matches render and survives re-render byte-identically. ✔
- `make verify-reproducibility` → PASS 14/14. ✔
- AF-03 PDF text: `null_strip_unavailable` ×7, `gate_passes = FALSE`, `p=0.0474` present; forbidden strings ×0. ✔
- `pdfinfo | grep HEDGE05` → `Keywords: HEDGE05-NULL-RESULT-V1`, AND the `\pdfinfo` custom key is genuinely embedded too. ✔ The keywords marker is a **strengthening**, not a weakening: it adds a second independent machine-readable channel that survives poppler's custom-key collapse (the dual-signature test at `test_null_result_template.py:88` was already written to accept exactly this, `... in info or "HEDGE05" in info`).
- The 3 named tests (`test_ichi_pdf_dual_signature`, `test_ichi_verdict_not_narrowed`, `test_ichi_qmd_source_not_narrowed`) pass. ✔
- SOURCE_DATE_EPOCH 1780012800 == 2026-05-29T00:00:00Z, consistent with `date: 2026-05-29` and the PDF's CreationDate (`Thu May 28 20:00:00 2026 EDT` = same instant). ✔
- Dropping `--execute-param` did not change the reported firing_condition (verified by data-flow trace: verdict reads the JSON artifact, not the param). ✔
- Removing `#refs` lost no references (all 6 in PDF; div was already inert pre-diff). ✔

---

## VERDICT

**NEEDS WORK** — but narrowly, and not on the load-bearing axis. The AF-03 verdict-integrity concern is fully cleared: every edit is provenance-neutral, the verdict banner reads the on-disk artifact (`null_strip_unavailable`), the dropped `--execute-param` fed a dead variable, and the PDF carries the locked 3/4 / `p=0.0474` / `gate_passes = FALSE` text with zero forbidden strings. The keywords marker strengthens (not weakens) the dual signature, removing `#refs` lost nothing, and on-machine determinism is genuinely real (byte-identical re-render). Two items hold the PASS: MAJOR-1 — the byte-pin is durable only under a fixed toolchain, and the MANIFEST prose overstates this as machine-independent "byte-deterministic," which will produce a confusing MISMATCH FAIL when an upstream auditor regenerates the PDF on a different TeX/pandoc; fix by scoping the pin's prose to its toolchain (or making the PDF pin advisory). MAJOR-2 — three `[@key]` citations render literally in the published PDF; pre-existing and not caused by this diff, but this PR is what ships it, so convert them to prose author-year cites. MINOR-1 (un-skipped latent template-render test failure — keep PR claims scoped to the 3 ichi tests) and MINOR-2 are non-blocking. Resolve MAJOR-1's prose and MAJOR-2's three cites and this is a clean PASS.
