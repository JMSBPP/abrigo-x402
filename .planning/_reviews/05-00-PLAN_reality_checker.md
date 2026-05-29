# Reality-Checker RE-REVIEW — 05-00-PLAN.md (Wave-0 scaffold)

**Reviewer:** Reality Checker (Reviewer 1)
**Date:** 2026-05-29 (re-review of revised plan)
**Artifact:** `.planning/phases/05-reporting-iteration-1-pdf-deliverable-l7/05-00-PLAN.md`

## VERDICT

PASS

Both prior MAJORs are CLOSED with live-repo-verified evidence (not prose-only). The MANIFEST parse contradiction is resolved to ONE canonical `sha256sum` two-space format + an `awk` parse that I empirically confirmed leaves no leading space and works inside the Makefile recipe escaping. The inert/false-guard `.gitignore` negation block is replaced with a real, empirically-validated nested `data/fits/.gitignore` allowlist + a scoped root panel negation — I rebuilt both in throwaway repos and confirmed they re-include exactly the intended files and nothing else. All three MINORs are addressed. One NEW MINOR (cosmetic) noted below; not blocking.

---

## Prior findings — confirm-closed

### PRIOR MAJOR-1 (MANIFEST parse self-contradiction / vacuous-PASS) — CLOSED
- The plan now LOCKS one canonical format (lines 130-134): standard `sha256sum` `<64-hex><TWO spaces><path>`, parsed with `grep -E "^[a-f0-9]{64}  " | awk '{print $1, $2}'`, and explicitly states 05-02 MUST restate it identically (05-02 line 84 does — verified verbatim).
- LIVE-VERIFIED: I ran the exact grep+awk on a two-space `sha256sum`-format line; `read -r expected path` yields `path=[data/raw/...]` with NO leading space (the prior `sed`/`read` leading-space bug is gone).
- The vacuous-PASS hole is closed by the `OK_COUNT == PIN_COUNT` guard (line 199), which I exercised: a missing non-PDF pin trips `OK(0) != PIN(1)` → exit 1.
- The Makefile-escaped form `awk "{print \$$1, \$$2}"` works — I reproduced the full recipe and it parsed correctly.

### PRIOR MAJOR-2 (inert `.gitignore` negation / false defensive comment) — CLOSED
- The bare inert `!data/fits/ichi/bdaf5c7ba5a2/` block is GONE. Replaced by:
  - a NESTED `data/fits/.gitignore` directory-spanning allowlist (lines 100-115), and
  - a scoped ROOT `.gitignore` panel negation chain (lines 117-128).
- LIVE-VERIFIED in throwaway repos (matching the live `data/fits/.gitignore` `*` rule and the live root `data/raw/*` + `data/raw/*/` rules):
  - Nested block: `bdaf5c7ba5a2/{CORRECTIONS.md,sensitivity_sweep.json,*.json,*.parquet,*.txt}` all `check-ignore -q` rc=1 (NOT ignored); `ae9e3ba17900/fit_report.json` rc=0 (STILL ignored); `git add data/fits/` stages exactly the allowlisted files. No scope creep.
  - Root block: panel parquet `check-ignore -q` rc=1 (NOT ignored) and `git add` stages it; `pool_events.jsonl` / `vault_state.jsonl` rc=0 (STILL ignored). No JSONL leakage.
- The acceptance assertions use `git check-ignore -q ...; test $? -ne 0` — I confirmed `-q` returns rc=1 for a negated/re-included file (correct "not ignored" disposition), so the assertion form is valid (NOT the `-v` rc=0 trap).

### PRIOR MINOR-1 (TinyTeX detection brittle) — CLOSED
`report-ichi` now runs `quarto install tinytex` unconditionally (line 211, idempotent), replacing the brittle `quarto list tools | grep tinytex` (line 219 documents the fix).

### PRIOR MINOR-2 (xfail-strict masking) — ADDRESSED
Wave-0 stubs are `xfail(strict=False)`; the two real guards (`test_no_new_cost_model_introduced`, `test_correct_lockfile_names`) are NOT xfail and run NOW. 05-01/05-02 remove the xfails on implementation. Acceptable for scaffold.

### PRIOR MINOR-3 (loose ≥9 count) — ADDRESSED
Acceptance now asserts `≥10 tests collected (3 + 3 + 4)` and names the two non-xfail guards that must pass NOW (lines 237-238).

---

## Foundation re-confirmed (no regression)
- Lockfile guard correct: LIVE `analysis/uv.lock` (257455 B) + `pnpm-lock.yaml` (241013 B) exist; `package-lock.json` + root `uv.lock` absent. ✓
- Makefile STUB still present at lines 47-48 (plan is pre-execution); `render-null-result-pdf` still has the `--output ichi.pdf` collision (line 154) — correctly flagged for the `rm -f` Wave-0 guard + 05-03 retarget. ✓
- quarto absent — render hard-required, TinyTeX self-heals, render tests skip-guarded. ✓
- Specialist (DevOps Automator) named in frontmatter + on the task with a why. ✓
- No verdict numbers embedded (scaffold). ✓

---

## NEW findings

### NEW MINOR-1 — `report-ichi` size gate uses `stat -c%s` (GNU-only); fine on this Linux env, brittle on a macOS quarto operator machine
**Evidence:** Line 216 `SIZE=$$(stat -c%s reports/ichi.pdf)`. The render is explicitly deferred to "the operator's quarto machine" (05-04). `stat -c%s` is GNU coreutils; BSD/macOS `stat` uses `-f%z`. If the operator renders on macOS, the size gate errors.
**Why it matters:** Low — the deliverable is rendered once by the operator; if they are on Linux it is fine. But the plan explicitly contemplates a separate quarto machine.
**Fix (optional):** Use `wc -c < reports/ichi.pdf` (portable) instead of `stat -c%s`. Not blocking.

---

## Cross-check summary
- MANIFEST parse: ONE canonical format, awk parse, no leading space, OK==PIN guard — LIVE-VERIFIED. (closed)
- gitignore wiring: both allowlist blocks empirically re-include intended files only — LIVE-VERIFIED in throwaway repos. (closed)
- Fantasy claims: none; the plan correctly debunks the CONTEXT gitignore fantasy and the BLOCKER. (clean)
- Specialist: present. (clean)

**BLOCKER: 0 · MAJOR: 0 (2 prior CLOSED) · MINOR: 1 NEW (cosmetic)**
