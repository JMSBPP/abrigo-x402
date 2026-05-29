# Reviewer 2 — DevOps Automator: Phase 5 render-fixes build/repro review

**Specialist picked:** DevOps Automator (CI/CD, Makefile, reproducibility-contract focus) — chosen because the diff is entirely build-pipeline + reproducibility-pin surface (`Makefile report-ichi`, `verify-reproducibility`, `reports/MANIFEST.md`).
**Artifact under review:** `/tmp/render_session.diff` = `git diff -- reports/ichi.qmd Makefile reports/MANIFEST.md`.
**Posture:** evidence-based; I ran the gates live. I did NOT edit any file.

## What I verified live (evidence)

- `sha256sum reports/ichi.pdf` = `654523fc...e39c5` — **matches** the MANIFEST pin. PDF = 517,238 B (> 50 KB gate).
- `sha256sum analysis/uv.lock` = `213132af...496e5` — **matches** the input pin; `git status --porcelain analysis/uv.lock analysis/.venv` is **empty** → the `uv run` interpreter probe did NOT mutate the lockfile or venv. Good.
- `make verify-reproducibility` with PDF present → **PASS (14/14)**, all `OK:`.
- Removed `reports/ichi.pdf`, re-ran → **PENDING: reports/ichi.pdf** + **PASS (13/13)**, exit 0; restored, sha intact. The 3-state PENDING-on-absent path works exactly as documented.
- `params.firing_condition` default in `reports/ichi.qmd:47` = `null_strip_unavailable` → dropping `--execute-param` is functionally equivalent; **no papermill on the `report-ichi` path** (only reference left is line 200 comment + the unrelated `render-null-result-pdf` target at line 180).
- Diff scope is exactly the 3 declared files; nothing else staged.

So the operator's headline claims are TRUE on this machine. The findings below are about whether the contract holds on a **fresh clone / second machine / future date** — which is the actual job of a reproducibility pin.

---

## BLOCKER

### B1 — The pinned PDF sha is bound to an undocumented, machine-specific TeX engine; a fresh clone on TinyTeX will MISMATCH, not reproduce
The PDF byte stream embeds the engine banner:
- `/Producer (pdfTeX-1.40.29)`
- `/PTEX.Fullbanner (This is pdfTeX, Version 3.141592653-2.6-1.40.29 (TeX Live 2026) ...)`

`SOURCE_DATE_EPOCH` only neutralizes the *timestamps* (`/CreationDate`, `/ModDate`, trailer `/ID`). It does **not** neutralize `/Producer` or `/PTEX.Fullbanner`, which carry the exact pdfTeX build string. The canonical render used **system TeX Live 2026/dev (pdfTeX 1.40.29)** — confirmed by `pdflatex --version` (1.40.27 in the interactive shell, 1.40.29 in the embedded banner: itself evidence the version is drifting under the operator's feet on the *same* box).

But `report-ichi:190` runs `quarto install tinytex` and `reports/ichi.qmd:30` sets `pdf-engine: pdflatex`. A fresh-clone operator with no system TeX will render under **quarto-managed TinyTeX**, whose pdfTeX banner string differs from `1.40.29 (TeX Live 2026)`. Result: different `/PTEX.Fullbanner` bytes → different sha256 → `verify-reproducibility` reports **MISMATCH → FAIL (exit 1)**, not PENDING. The PENDING escape only fires when the PDF is *absent*; once an operator renders, they are locked into a strict equality the toolchain cannot meet.

This is the core DevOps defect: a byte-pin on a PDF is a pin on the *entire TeX toolchain*, and that toolchain is (a) not version-recorded anywhere, (b) explicitly two different installers (system pdflatex vs. `quarto install tinytex`), and (c) observably drifting (1.40.27 → 1.40.29) on one machine within one session.

**Concrete fix (pick one):**
- **Preferred (keep byte-pin honest):** Pin the toolchain. Record the exact pdfTeX/TeX Live version and the pandoc + quarto versions next to the sha in `MANIFEST.md`, and make `report-ichi` assert them (fail-fast if `pdflatex --version` / `quarto --version` don't match). Without this, the sha is a pin on undocumented state. Also force TinyTeX vs system-tex consistently — do not `quarto install tinytex` AND silently fall through to `/usr/bin/pdflatex`; the producer string differs.
- **Or (decouple repro from byte-identity):** Demote `reports/ichi.pdf` from a strict sha pin to a *content* check — verify the PDF exists, exceeds the size gate, and contains the `HEDGE05-NULL-RESULT-V1` marker + the verbatim "3/4 / null_strip_unavailable" verdict — and drop the sha line (or keep it as a same-machine-only convenience clearly labelled "not portable"). The MANIFEST already (correctly, per its own "Option C-hybrid" section) refuses to byte-pin the scipy fit "NOT byte-reproducible across BLAS builds"; the identical logic applies to pdfTeX builds and is currently violated for the PDF.

Either fix is fine; shipping the strict sha pin *as a public reproducibility contract* without one of them is the blocker.

---

## MAJOR

### M1 — `report-ichi` has a TeX-engine ambiguity that will bite CI/other machines (Makefile:190 + ichi.qmd:30)
Line 190 `quarto install tinytex 2>/dev/null || true` installs TinyTeX, but the render then uses whatever `pdflatex` quarto resolves on `PATH`. On this box that resolved to system `/usr/bin/pdflatex` (1.40.29), NOT TinyTeX. So the recipe is non-deterministic about *which* TeX it uses depending on whether system TeX is installed — the worst kind of "works on my machine." Fix: be explicit — either remove the TinyTeX install and document system TeX Live as the prerequisite (with a version assert), or force the render to use the TinyTeX path (`quarto` honors `QUARTO_...`/PATH ordering) and never fall through to system TeX. Tie this to B1's version assert.

### M2 — No CI wiring; the entire repro contract is operator-manual with no fail-fast enforcement
`grep` shows no `.github/workflows` invoking `make report-ichi` or `make verify-reproducibility` (the diff adds none, and none pre-exist for this path). The "14/14 PASS" is a hand-run claim. For a public PR whose deliverable IS the PDF + repro gate, `verify-reproducibility` should run in CI on every push so a drifted pin fails the build rather than being discovered by a reader. Quarto + TeX are heavy CI deps, but at minimum `verify-reproducibility` (pure sha256, no quarto needed when the committed PDF is present) is cheap and should be a required check. Fix: add a CI job that runs `make verify-reproducibility`; optionally a separate, allowed-to-be-slow job that runs `make report-ichi` and asserts the re-rendered sha matches (this job is exactly what will surface B1 on the CI runner's TeX version — which is the point).

### M3 — `SOURCE_DATE_EPOCH=1780012800` hardcoded and silently decoupled from the qmd `date`
The epoch is a magic literal in the recipe (Makefile:201-202) whose comment says it "matches the qmd frontmatter date: 2026-05-29." Nothing *enforces* that coupling — if someone bumps `ichi.qmd:date` for Iteration 2 and forgets the epoch (or vice versa), `/CreationDate` and the human-visible cover date diverge silently and the sha shifts with no guardrail. Fix: derive the epoch from the qmd `date` field in the recipe (`date -d "$(grep ^date ichi.qmd ...)" +%s` — but note GNU vs BSD `date` differ, so guard it), or assert equality between the two in `report-ichi` before rendering.

---

## MINOR

### m1 — `tlmgr`/TinyTeX auto-update is a latent non-determinism source (Makefile:190)
The operator observed `updating tlmgr` / `updating existing packages` during render. A self-updating TeX package set means the byte output (and even `/PTEX.Fullbanner`) can change across time on the *same* machine without any repo change — directly undermining B1's pin. `quarto install tinytex` does not pin a TinyTeX snapshot. Fix: disable auto-update during the gated render (e.g. ensure no `tlmgr update` runs in the recipe path) and record the TinyTeX/tlmgr snapshot date alongside the engine version in MANIFEST.

### m2 — Network/hidden-state in the spot-check step is correctly soft-failed but undocumented as such in MANIFEST
`report-ichi:193` curls Blockscout (`verify_url_status`) and is guarded with `|| echo ... (continuing)`, so the render does not hard-depend on network — good. But the MANIFEST "Provenance" section presents the spot-check as deterministic without noting the URL-status logging is network-optional and does not affect the pinned bytes. Minor doc gap: state that the curl logging is non-load-bearing for the sha.

### m3 — `cd reports && ... quarto render` subshell + backslash continuation is correct but brittle to copy-paste (Makefile:201-203)
The `VENV_PY=$$(...) ; cd reports && ... quarto render` is a single recipe logical line joined by `\`. It works (verified: exit 0), and the `cd analysis`/`cd reports` are in separate subshell segments so they don't compound. No bug, but it's a long fragile line; a stray edit dropping the trailing `\` silently splits it into two recipe lines with broken `cd` semantics. Low risk, flagging for awareness. The portable `wc -c` (vs `stat -c%s`) at line 205 is correctly macOS-safe — good.

### m4 — `render-null-result-pdf` (Makefile:179-180) still writes `reports/ichi.pdf`? Verify the path
The comment at Makefile:185 warns that "the legacy render-null-result-pdf target ALSO writes reports/ichi.pdf." In the current source it writes `_diagnostics/null_result_$$FIRING.pdf`, NOT `reports/ichi.pdf`, so the `rm -f reports/ichi.pdf` guard at line 194 is defensive but the comment is now stale/misleading. Fix the comment to match (it still uses `--execute-param`, which is fine — that target is off the deliverable path and out of scope here).

---

## VERDICT

**NEEDS WORK.** The recipe is functionally correct and I reproduced every claim on this machine — 14/14 strict, 13/13 PENDING-on-absent, uv.lock untouched, papermill off the path, byte-stable across re-render *on this engine*. But a reproducibility pin's whole job is to hold off this machine, and it does not: the PDF embeds `/Producer` + `/PTEX.Fullbanner` carrying the exact pdfTeX build (`1.40.29 / TeX Live 2026`), which `SOURCE_DATE_EPOCH` cannot neutralize, which is recorded nowhere, and which the recipe sources ambiguously (system pdflatex vs. `quarto install tinytex`) with observed tlmgr auto-update drift — so a fresh clone rendering under TinyTeX will produce a different sha and `verify-reproducibility` will MISMATCH-FAIL rather than reproduce (B1). This is the same byte-instability the MANIFEST already concedes for the scipy fit and (correctly) refuses to byte-pin; the PDF deserves the same treatment. Resolve B1 (pin or document the toolchain version, or demote the PDF to a content+marker+size check) and the M-items (engine disambiguation, a cheap `verify-reproducibility` CI gate, epoch/date coupling) before this lands as a public reproducibility claim.
