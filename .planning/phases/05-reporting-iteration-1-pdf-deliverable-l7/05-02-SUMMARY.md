---
phase: 05-reporting-iteration-1-pdf-deliverable-l7
plan: 02
subsystem: infra
tags: [reproducibility, sha256, makefile, blockscout, spot-check, manifest, devops, numpy-rng]

# Dependency graph
requires:
  - phase: 05-00
    provides: "verify-reproducibility Makefile body (canonical awk parse + 3-state rule + OK==PIN guard + MANIFEST ?= parameterization); root-.gitignore negation committing the panel parquet; nested allowlist committing the bdaf5c7ba5a2 run-dir artifacts; Wave-0 skip/xfail test scaffolds"
  - phase: 05-01
    provides: "data/fits/ichi/bdaf5c7ba5a2/sensitivity_sweep.json (committed, pinned in MANIFEST); abrigo_x402.report package __init__"
provides:
  - "REPORT-02: deterministic 5-row seeded Blockscout spot-check (abrigo_x402.report.spot_check) with recorded re-derivable seed + network-optional curl logging"
  - "REPORT-04: reports/MANIFEST.md (13 sha256 pins + provenance) + a finalized make verify-reproducibility gate proven on a clean checkout"
affects: [05-03, 05-04, cycle-closure]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Seeded-from-run_id determinism: numpy default_rng(int(sha256(run_id)[:8],16)) for cross-version-stable artifact draws"
    - "Network-optional build-time verification: bounded curl -I that logs status and never fails the build offline"
    - "Checksum-the-committed-artifacts reproducibility (Option C-hybrid) for non-byte-reproducible scipy fits"
    - "Clean-checkout worktree verification: git worktree add HEAD proves fresh-clone pin resolution, not working-tree-only green"

key-files:
  created:
    - "analysis/src/abrigo_x402/report/spot_check.py"
    - "reports/MANIFEST.md"
  modified:
    - "analysis/tests/test_spot_check.py"
    - "analysis/tests/test_manifest.py"

key-decisions:
  - "verify-reproducibility FAIL asserted as non-zero (not literally 1): GNU make wraps a failed recipe as exit 2; the load-bearing contract is exit 0 = pass / non-zero = fail, so the tests assert returncode != 0 on tamper/missing while keeping == 0 on full match."
  - "Makefile NOT modified: the 05-00 verify-reproducibility body already implements the 3-state rule + canonical parse verbatim; the SKIP-on-absent-MANIFEST early-exit is a harmless no-op now that MANIFEST exists. Inheriting verbatim avoids a divergent parse (the closed MAJOR-2)."
  - "MANIFEST prose avoids the literal npm-lockfile token so the 'wrong lockfile absent' assertion (and CONTEXT decision 6) holds at the string level, not just at the pin level."

patterns-established:
  - "Pattern: run_id-seeded deterministic draw — int(sha256(run_id)[:8],16) seed recorded in the manifest so a clone re-derives identical rows"
  - "Pattern: clean-checkout worktree gate — the fresh-clone reproducibility contract is exercised on git worktree add HEAD, not the working tree"

requirements-completed: [REPORT-02, REPORT-04]

# Metrics
duration: 5min
completed: 2026-05-29
---

# Phase 5 Plan 02: Deterministic Spot-Check + Reproducibility Manifest Summary

**Seeded 5-row Blockscout spot-check (run_id-derived RNG, network-optional curl) plus a 13-pin reports/MANIFEST.md and a verify-reproducibility gate proven green on a clean HEAD checkout (fresh-clone reproducibility genuinely met).**

## Performance

- **Duration:** 5 min
- **Started:** 2026-05-29T17:41:57Z
- **Completed:** 2026-05-29T17:47:05Z
- **Tasks:** 2 (both TDD: RED → GREEN)
- **Files modified:** 4 (2 created, 2 test files implemented)

## Accomplishments
- `seeded_spot_check(run_id, panel_path, k=5)` — a `numpy.random.default_rng(int(sha256("bdaf5c7ba5a2")[:8],16))` draw of 5 distinct rows from the committed 832-row panel parquet, each `{row_index, txHash, blockNumber, url}` with a `https://celo.blockscout.com/tx/0x...` URL; asserts `panel_rows==832` + well-formed `0x[0-9a-fA-F]{64}` txHash (silent-redraw guard). Seed `3812543816` is recorded in MANIFEST.md so a fresh clone re-draws the identical rows.
- `verify_url_status` — a bounded (`--connect-timeout 5 --max-time 10`) `curl -I` helper that logs HTTP status per row and NEVER raises offline (`000`/failure → "unverified (no network)"), satisfying SC-2's per-row-logging clause.
- `reports/MANIFEST.md` — Option C-hybrid manifest: panel sha256 (`a72a4ee…`), `analysis/uv.lock`, `pnpm-lock.yaml`, the 10 committed `bdaf5c7ba5a2/` run-dir artifact shas (incl. `CORRECTIONS.md` + `sensitivity_sweep.json`), and a PENDING-allowed `reports/ichi.pdf` placeholder; provenance subsection pins blockRange `[67378253,67896653]`, chainId `42220`, the seed, and the 832→778 PANEL-04 relationship.
- `make verify-reproducibility` exits 0 with `13/13 pins matched` (PDF PENDING) and — crucially — exits 0 on a **clean-checkout worktree of HEAD**, proving every pinned path resolves on a fresh clone (the closed fresh-clone BLOCKER).

## Task Commits

1. **Task 1 RED: spot_check seeded-draw tests** — `28622a3` (test)
2. **Task 1 GREEN: spot_check module** — `b68352e` (feat)
3. **Task 2 RED: manifest pins + verify-repro exit-code tests** — `fd3e5ed` (test)
4. **Task 2 GREEN: MANIFEST.md + verify-reproducibility match** — `5819656` (feat)

**Plan metadata:** (this docs commit)

## Files Created/Modified
- `analysis/src/abrigo_x402/report/spot_check.py` — seeded draw + network-optional curl helper
- `reports/MANIFEST.md` — 13-pin reproducibility manifest + provenance
- `analysis/tests/test_spot_check.py` — 4 tests (determinism, URL form, recorded seed, network-optional curl)
- `analysis/tests/test_manifest.py` — 5 tests (pins present, exit codes, missing-artifact 3-state, lockfile names, every-pin-tracked)

## Decisions Made
- **make exit code:** GNU make wraps a failed recipe as exit 2, so the FAIL-path tests assert `returncode != 0` (with a `MISMATCH`/`MISSING` stdout check) rather than the literal `1` the plan/scaffold prose used; the match path still asserts exit 0. The reproducibility contract ("the gate fails the build on tamper/missing") is fully preserved.
- **Makefile unchanged:** the 05-00 body already encodes the canonical awk parse + 3-state rule + OK==PIN guard + `MANIFEST ?=` parameterization; finalizing required no edit (the absent-MANIFEST early-exit is now a no-op). This keeps the parse single-sourced from 05-00 (no divergence).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] verify-reproducibility FAIL exit code is 2, not 1 (GNU make recipe wrapping)**
- **Found during:** Task 2 (manifest verify-repro exit-code tests)
- **Issue:** The plan/scaffold asserted `returncode == 1` for the tamper + missing-artifact FAIL paths. GNU make always wraps a non-zero recipe as its own exit code 2, so the inner `bash ... exit 1` surfaces to the test as `make` exit 2. A literal `== 1` assertion can never pass through a `make` target.
- **Fix:** Changed the two FAIL-path assertions to `returncode != 0` plus a `MISMATCH`/`MISSING` stdout check; the full-match path retains `== 0`. The reproducibility contract (exit 0 = pass / non-zero = fail) is preserved exactly; only the over-specific literal was relaxed.
- **Files modified:** analysis/tests/test_manifest.py
- **Verification:** All 5 manifest tests GREEN; the tamper test confirms `MISMATCH` + non-zero, the missing test confirms `MISSING` + non-zero and `PENDING` + exit 0; the real `reports/MANIFEST.md` is byte-unchanged after the run.
- **Committed in:** fd3e5ed (Task 2 RED commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The deviation tightens (not loosens) the contract test and is forced by GNU make semantics. No scope creep; no change to the Makefile, the manifest pins, the spot-check, or the verdict.

## Issues Encountered
- MANIFEST prose initially contained the literal npm-lockfile token, tripping the `assert "<npm-lockfile>" not in text` string check; reworded the prose to describe the lockfiles without the literal token. Resolved within Task 2 GREEN.

## User Setup Required
None - no external service configuration required. (The build-time Blockscout curl is network-optional and logs "unverified (no network)" offline.)

## Next Phase Readiness
- REPORT-02 + REPORT-04 satisfied; `reports/MANIFEST.md` + `make verify-reproducibility` are the reproducibility spine for cycle closure.
- Plan 05-03 (PDF render): consumes `seeded_spot_check` for the spot-check table prose and renders `reports/ichi.pdf`; the manifest already PENDING-pins the PDF path.
- Plan 05-04: replaces the all-zero `reports/ichi.pdf` placeholder sha with the real render sha (the ONLY allow-listed PENDING path).
- No re-fit, no new cost model, no κ; verdict untouched.

## Self-Check: PASSED

All created files exist (`spot_check.py`, `reports/MANIFEST.md`, both test files, this SUMMARY); all 4 task commits (`28622a3`, `b68352e`, `fd3e5ed`, `5819656`) present in git history. Targeted suite `pytest tests/test_spot_check.py tests/test_manifest.py` 9 passed (full slow Hawkes suite deliberately NOT run); `make verify-reproducibility` exits 0 (13/13, PDF PENDING); clean-checkout worktree run exits 0 (fresh-clone proven); real `reports/MANIFEST.md` byte-unchanged after the tamper test. No fit recompute, no cost model, no κ.

---
*Phase: 05-reporting-iteration-1-pdf-deliverable-l7*
*Completed: 2026-05-29*
