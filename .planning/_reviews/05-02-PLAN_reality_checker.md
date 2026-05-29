# Reality-Checker RE-REVIEW — 05-02-PLAN.md (REPORT-02 spot-check + REPORT-04 manifest/verify-reproducibility)

**Reviewer:** Reality Checker (Reviewer 1)
**Date:** 2026-05-29 (re-review of revised plan)
**Artifact:** `.planning/phases/05-reporting-iteration-1-pdf-deliverable-l7/05-02-PLAN.md`

## VERDICT

PASS

The prior BLOCKER (fresh-clone panel unobtainable) is genuinely CLOSED — not by prose, but by a real, empirically-validated commit path: the panel parquet + CORRECTIONS.md + sensitivity_sweep.json are re-included via the 05-00 gitignore allowlists (which I rebuilt and confirmed work), the plan correctly REJECTS the impossible `materialize`-on-absence path (the JSONL cache is verifiably NOT tracked), and a CLEAN-CHECKOUT worktree run + a new `test_every_pinned_fits_path_tracked` (`git ls-files`) guard prove every pinned path resolves on a clone. Both prior MAJORs are CLOSED. No new BLOCKER.

---

## Prior findings — confirm-closed

### PRIOR BLOCKER-1 (fresh-clone: panel gitignored + uncommitted) — CLOSED
- LIVE-VERIFIED the starting reality is exactly as the prior review found: `git ls-files data/raw/` returns ONLY `data/raw/manifest.json`; the panel + JSONL cache are untracked; `git check-ignore` confirms `data/raw/*/` ignores the panel and `data/fits/.gitignore:*` ignores CORRECTIONS.md.
- The revision picks Option 2 (commit the 128KB panel) and CORRECTLY rejects Option 1 (materialize): line 48 / 64 / 158 / 176 state the JSONL source cache is NOT git-tracked so `cli.py materialize`-on-absence is impossible offline, and explicitly forbid wiring a materialize regeneration step. This matches the live `git ls-files` evidence.
- LIVE-VERIFIED the commit path WORKS: I reconstructed both 05-00 gitignore allowlist blocks in throwaway repos mirroring the live ignore rules — the panel parquet + CORRECTIONS.md + sensitivity_sweep.json all become NOT-ignored and `git add` (plain, no `-f`) stages them; the JSONL siblings + other run dirs stay ignored.
- Panel sha256 LIVE-VERIFIED: `sha256sum` of the panel == `a72a4ee…` == `fit_report.json dataHash`. (line 18/64 correct.)
- The fresh-clone contract is now PROVEN two ways, not asserted:
  1. Clean-checkout worktree run (action step 3, lines 167-173; acceptance line 184): `git worktree add /tmp/repro-check HEAD && (cd … && make verify-reproducibility)` MUST exit 0 — exercises the clone state, not the working tree.
  2. `test_every_pinned_fits_path_tracked` (Test 5, line 152): for every pinned `data/fits/...` + the panel `data/raw/...` path, `git ls-files <path>` must be non-empty — so a missing-on-clone pin can never ship.
This is the strongest possible closure: a clone genuinely has the headline input + artifacts.

### PRIOR MAJOR-1 (missing-file exit-code contract) — CLOSED
- The 3-state rule is now CONCRETE and restated as the contract (lines 86-92): ABSENT + `reports/ichi.pdf` → PENDING (decremented from PIN_COUNT, not a failure); ABSENT + any other path → MISSING → FAIL exit 1; PRESENT + mismatch → MISMATCH → FAIL exit 1; PRESENT + match → OK. `[ -f "$path" ]` BEFORE `sha256sum` (never empty-hash comparison) is mandated (line 92).
- LIVE-VERIFIED by reproducing the EXACT 05-00 loop body in a throwaway Makefile and exercising all states:
  - panel matches + PDF absent → `PASS (1/1 pins matched)` exit 0 ✓
  - 64-char tampered panel sha → `MISMATCH … verify-reproducibility: FAIL` exit 1 ✓
  - missing non-PDF committed artifact → `MISSING … OK_COUNT(0) != PIN_COUNT(1)` exit 1 ✓
  (Note: a tamper with a malformed 66-char hash is silently skipped by the `{64}` grep, but a realistic tamper that flips one char of a real 64-hex sha IS caught — the 05-02 tamper test mutates one char, so it stays 64 and is caught. Verified.)

### PRIOR MAJOR-2 (MANIFEST parse format contradiction with 05-00) — CLOSED
- 05-02 no longer re-authors a divergent parse: line 84 states it INHERITS the 05-00 loop body verbatim (canonical `sha256sum` two-space format + `awk` parse + 3-state + OK==PIN), changing only the SKIP-on-absent-MANIFEST framing. The `sed`/`read` leading-space bug cannot reappear because the parse is single-sourced.
- LIVE-VERIFIED the awk parse leaves no leading space (see 05-00 review). Acceptance line 188 also asserts `grep -cE '^[a-f0-9]{64}  data/fits/ichi/bdaf5c7ba5a2/' reports/MANIFEST.md >= 10`, locking the two-space format in the authored manifest.

### PRIOR MINOR-1 (CWD-fragile panel path) — CLOSED
`Path(__file__).resolve().parents[2] / "data/raw/ichi/0x61Ef.../67378253_67896653.parquet"` (line 76/116).

### PRIOR MINOR-2 (txHash non-null per drawn row) — CLOSED
Line 76 + Test 2 (line 111) assert each drawn row matches `^https://celo.blockscout.com/tx/0x[0-9a-fA-F]{64}$` and the module asserts a well-formed `0x[0-9a-fA-F]{64}` txHash on each draw (line 120).

### PRIOR MINOR-3 (run_log.txt byte-stability) — ADDRESSED
The run-dir artifacts (incl. run_log.txt) are committed/tracked (verified via `git ls-files` for the 8 base files; CORRECTIONS.md added by 05-00); pinning them as immutable committed evidence is acceptable. The MANIFEST prose notes they are checksummed committed artifacts, not re-fit.

---

## Foundation re-confirmed (no regression)
- Correct lockfiles pinned (analysis/uv.lock + pnpm-lock.yaml), `package-lock.json` + root `uv.lock` explicitly absent (acceptance lines 186-187). LIVE-verified the two exist and the two do not. ✓
- 832-row panel with txHash; draw from 832 (retains txHash), state 832→778. LIVE blockRange `[67378253,67896653]`, chainId `42220` confirmed in fit_report.json. ✓
- No re-fit in verify (checksum committed artifacts only — Pitfall 2). ✓
- Deterministic numpy `default_rng` seed from run_id sha256. ✓
- Specialist (DevOps Automator) named with a why. ✓

---

## NEW findings
None blocking. The clean-checkout worktree assertion is the right mechanism and the `git ls-files` per-pin guard is a genuine closure of the fresh-clone gap.

---

## Cross-check summary
- Fresh-clone reproducibility: BLOCKER CLOSED — panel committed via empirically-working allowlist; materialize correctly rejected; clean-checkout worktree run + git-ls-files per-pin guard prove it. (LIVE-verified)
- Exit-code contract: CLOSED — 3-state rule with `[ -f ]` pre-check; PASS/FAIL/MISMATCH/PENDING all exercised live. (LIVE-verified)
- MANIFEST parse: CLOSED — single-sourced from 05-00, no leading-space, OK==PIN. (LIVE-verified)
- Correct lockfiles + tamper=FAIL + never-mutate-real-manifest: present. (clean)
- Specialist: present. (clean)

**BLOCKER: 0 (1 prior CLOSED) · MAJOR: 0 (2 prior CLOSED) · MINOR: 0 NEW**
