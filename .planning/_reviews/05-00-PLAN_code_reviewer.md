# Reviewer 2 (DevOps Automator) — Plan 05-00 (Wave-0 scaffold) — RE-REVIEW

## VERDICT
PASS

Scoped re-review of the revised Wave-0 scaffold against my 4 prior BLOCKER/MAJOR findings, all of which were re-derived empirically in a /tmp git sandbox (not taken on faith). Every prior finding is CLOSED. The nested `data/fits/.gitignore` allowlist and the root `data/raw` panel negation both produce exactly the intended check-ignore behavior — target artifacts un-ignored, siblings/other-run-dirs still ignored, plain `git add` works (no `-f`), and even `git add -A` stages only the panel parquet. No new BLOCKERs introduced by the edits.

---

## Prior findings — confirm-closed (empirically re-derived)

### BLOCKER 1 — `.gitignore` exception targeted the WRONG file → **CLOSED**
The revised plan now edits the NESTED `data/fits/.gitignore` (Task 1e), not root, and `files_modified` lists both `data/fits/.gitignore` and `.gitignore`. I replicated the live nested ignore (`*` / `!.gitignore` / `!manifest.json`) + the run dirs in a sandbox and appended the VERBATIM proposed block:
```
!ichi/
ichi/*
!ichi/bdaf5c7ba5a2/
ichi/bdaf5c7ba5a2/*
!ichi/bdaf5c7ba5a2/*.json
!ichi/bdaf5c7ba5a2/*.parquet
!ichi/bdaf5c7ba5a2/*.md
!ichi/bdaf5c7ba5a2/*.txt
```
Empirical `git check-ignore` result AFTER the block:
- `bdaf5c7ba5a2/CORRECTIONS.md`, `sensitivity_sweep.json`, and all 8 existing artifacts → **NOT-IGNORED** ✓
- `ichi/ae9e3ba17900/fit_report.json` and `000c1cdce376/fit_report.json` → **IGNORED** by `data/fits/.gitignore:8:ichi/*` ✓ (no scope creep)
- plain `git add data/fits/ichi/bdaf5c7ba5a2/CORRECTIONS.md sensitivity_sweep.json` → staged as `A` (no `-f`) ✓

The directory-spanning idiom (`!dir/` then `dir/*` then `!dir/sub/` … then negate the extensions) is the canonical git pattern for re-including a leaf under a `*`-ignored parent, and it works here exactly as written. The "git cannot re-include a file under an excluded parent dir" hazard I raised is sidestepped because each intermediate directory is itself re-included (`!ichi/`, `!ichi/bdaf5c7ba5a2/`) before its contents are re-ignored — git can descend.

### BLOCKER 2 — CORRECTIONS.md + sensitivity_sweep.json untracked/ignored → fresh-clone verify FAILs → **CLOSED**
Revised plan removes the false "9 artifacts already tracked / do NOT force-add" claim. The `<interfaces>` GITIGNORE REALITY block now states the TRUE state ("8 tracked, CORRECTIONS.md untracked"). Task 1g does a PLAIN `git add` of CORRECTIONS.md (post-allowlist) and the panel; 05-01 plain-adds sensitivity_sweep.json. Acceptance L243 asserts `git ls-files … | wc -l ≥ 9`. The fresh-clone failure mode is closed at the source (the files become tracked) and re-verified downstream in 05-02 via a clean-checkout `git worktree` run.

### MAJOR 3 — output collision render-null-result-pdf vs report-ichi → **CLOSED (Wave-0 portion)**
I confirmed live: `render-null-result-pdf` (Makefile L154) still writes `--output ichi.pdf`. The revised 05-00 adds the `rm -f reports/ichi.pdf` stale-PDF guard immediately before `quarto render` in `report-ichi` (Task 1d, acceptance L239 `grep -q 'rm -f reports/ichi.pdf'`), and explicitly defers the deeper retarget to 05-03 (which now owns it — verified in 05-03 Task 2b). The Wave-0 guard against a stale/wrong-source PDF satisfying the `test -f`/size gate is present.

### MAJOR 4 — stale-PDF race defeats `test -f` → **CLOSED**
`rm -f reports/ichi.pdf` is now the line immediately before `quarto render` (Task 1d verbatim body L213). A failed render can no longer leave a prior valid PDF that passes the gate.

### MINOR 5 — brittle `sed "s/  / /"` parse → **CLOSED**
The canonical parse is now `grep -E "^[a-f0-9]{64}  " | awk '{print $1, $2}'` (locked in `<interfaces>` CANONICAL MANIFEST block + the Makefile body L198). awk splits on whitespace runs → no leading-space artifact. The OK_COUNT==PIN_COUNT guard (L199) closes the vacuous-PASS mode.

### MINOR 6 — stale "207-green" baseline → **CLOSED**
Task 1 step 0 (L154) now captures the baseline live via `pytest --collect-only -q | tail -1` and records it in the SUMMARY; the hardcoded 207 is gone (truths L24 says "captured at Wave-0 start, not hardcoded").

### MINOR 7 — brittle `quarto list tools | grep tinytex` → **CLOSED**
Replaced by an unconditional idempotent `quarto install tinytex 2>/dev/null || true` (Task 1d L211, note at L219). Matches Quarto docs.

---

## New findings from the edits
None at BLOCKER/MAJOR. Two MINOR observations:

- **MINOR (new) — root panel negation relies on the parent `data/raw/ichi/` re-include surviving the pre-existing `data/raw/*` (non-slash) rule.** The live root ignore has BOTH `data/raw/*` (L42) and `data/raw/*/` (L43); the panel is currently caught by L43. I replicated both lines in the sandbox and appended the proposed `!data/raw/ichi/` … chain: the panel was NOT-IGNORED and all JSONL siblings + synthetic parquets + an unrelated protocol dir stayed IGNORED, and `git add -A` staged ONLY the panel. So the block is correct as written. Flagged only so the executor appends it AFTER the existing data/raw block (the plan says "after line 46" — correct) and does not reorder it above L42/43.

- **MINOR (new) — `git check-ignore -q …; test $? -ne 0` acceptance idiom (L241-242).** Under `set -e` this is safe because `test` is the last command, but if the executor runs the suite under `set -e` without the trailing `test`, a non-zero `check-ignore` (the desired "not ignored" result) would abort. The plan writes it correctly with the explicit `test $? -ne 0` wrapper. Non-blocking.

---

## Clean checks (re-confirmed live)
- Lockfiles: `analysis/uv.lock` (257 KB) + `pnpm-lock.yaml` (241 KB) exist; `package-lock.json` + root `uv.lock` do NOT. `test_correct_lockfile_names` will pass now.
- `verify-reproducibility` is a STUB at Makefile L47-48 (to be replaced); `.PHONY` L6-8 already lists it; `report-ichi` to be added — all as the plan states.
- quarto-skip pattern present verbatim at test_null_result_template.py L59/L61.
- 8 run-dir files tracked; CORRECTIONS.md on disk (1158 B) untracked — matches the plan's REALITY block exactly.
- 05-02 `depends_on: [05-00, 05-01]` — the DAG-ordering MINOR I raised on 05-04 is now fixed at the source.
