---
phase: 05-reporting-iteration-1-pdf-deliverable-l7
plan: 00
subsystem: infra
tags: [makefile, pytest, gitignore, quarto, reproducibility, manifest, sha256]

# Dependency graph
requires:
  - phase: 04.1.1-fix-hawkes-likelihood-mode-fit
    provides: "canonical run_id bdaf5c7ba5a2 (scipy_canonical_ll, η≈0.600, gate_passes=FALSE 3/4, firing_condition=null_strip_unavailable) — the verdict Phase 5 reports"
provides:
  - "3 RED/skip-marked Phase-5 pytest scaffolds (test_spot_check, test_sensitivity_sweep, test_manifest; 10 tests collect)"
  - "Makefile report-ichi target (rm -f stale PDF, idempotent tinytex install, >50KB size gate, markdown-fallback rejection)"
  - "Makefile verify-reproducibility target (parameterized MANIFEST, awk canonical parse, 3-state PENDING/FAIL/OK, OK_COUNT==PIN_COUNT guard)"
  - "Fresh-clone reproducibility wired on BOTH ends: nested data/fits/.gitignore allowlist (bdaf5c7ba5a2 artifacts incl. CORRECTIONS.md) + root .gitignore panel-parquet negation; both git-tracked via plain add"
affects: ["05-01 sensitivity sweep", "05-02 manifest authoring", "05-03 ichi.qmd render"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Option C-hybrid reproducibility: commit the canonical run-dir + 128KB panel as evidence; verify-reproducibility checksums committed files rather than re-fitting (scipy MLE not byte-reproducible across BLAS)"
    - "Directory-spanning gitignore allowlist negation under a nested ignore (re-include dir chain → re-ignore contents → negate kept artifacts)"
    - "RED/skip-marked Wave-0 test scaffolds (xfail strict=False) so the baseline suite stays green while downstream waves implement"

key-files:
  created:
    - analysis/tests/test_spot_check.py
    - analysis/tests/test_sensitivity_sweep.py
    - analysis/tests/test_manifest.py
  modified:
    - Makefile
    - .gitignore
    - data/fits/.gitignore
    - data/fits/ichi/bdaf5c7ba5a2/CORRECTIONS.md
    - data/raw/ichi/0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F/67378253_67896653.parquet

key-decisions:
  - "Option C-hybrid: panel parquet AND CORRECTIONS.md committed via allowlist negations (plain add, no -f); verify-reproducibility checksums rather than re-fits"
  - "report-ichi rm -f's reports/ichi.pdf before render to defeat the render-null-result-pdf output-collision / stale-PDF repro trap"
  - "verify-reproducibility uses awk (not read/sed) on the two-space sha256sum pin format, with an OK_COUNT==PIN_COUNT guard against the vacuous-PASS mode"

patterns-established:
  - "Wave-0 scaffold-then-implement: present-but-stub Makefile targets + RED/skip tests that downstream waves fill"
  - "Both-ends fresh-clone reproducibility: committed INPUT (panel) + committed OUTPUT (run-dir) + checksum-based verify"

requirements-completed: [REPORT-01, REPORT-02, REPORT-03, REPORT-04]

# Metrics
duration: scaffold-committed-prior; metadata-finalized this run
completed: 2026-05-29
---

# Phase 5 Plan 00: Phase-5 Scaffold Summary

**Wave-0 reporting scaffold — 3 RED/skip Phase-5 pytest files, `report-ichi` + `verify-reproducibility` Makefile targets, and both-ends fresh-clone reproducibility (nested-gitignore allowlist for the bdaf5c7ba5a2 run-dir + root-gitignore panel-parquet negation), all landed in commit `7373e73`.**

## Performance

- **Duration:** Scaffold committed in a prior run (`7373e73`); only metadata finalization completed this run.
- **Completed:** 2026-05-29
- **Tasks:** 1 (single-task scaffold plan)
- **Files modified:** 8 (3 created test files + Makefile + 2 .gitignore files + CORRECTIONS.md + panel parquet)

## Accomplishments

- 3 skip-marked Phase-5 test scaffolds collecting cleanly (10 tests: 3 spot-check + 3 sweep + 4 manifest), with the two non-xfail guards (`test_no_new_cost_model_introduced`, `test_correct_lockfile_names`) passing at scaffold time.
- `report-ichi` Makefile target present (rm -f stale PDF collision guard, idempotent `quarto install tinytex`, >50KB size gate, explicit markdown-fallback rejection).
- `verify-reproducibility` STUB replaced with the real recompute-and-match loop (parameterized `MANIFEST`, canonical awk parse of the two-space sha256sum pin format, 3-state PENDING/FAIL/OK rule, OK_COUNT==PIN_COUNT vacuous-PASS guard); exits 0 on the SKIP path until 05-02 authors MANIFEST.md.
- Fresh-clone reproducibility wired on BOTH ends: the nested `data/fits/.gitignore` allowlist re-includes the bdaf5c7ba5a2 run-dir artifacts (incl. the previously-untracked CORRECTIONS.md and the to-be-created sensitivity_sweep.json) while ae9e3ba17900 / 000c1cdce376 stay ignored; the root `.gitignore` scoped negation re-includes the 128KB panel parquet while the JSONL source siblings stay ignored. Both files committed via plain `git add` (post-allowlist, no `-f`).

## Task Commits

The scaffold was committed atomically in a prior execution run:

1. **Task 1: Phase-5 scaffold** — `7373e73` (feat) — Makefile targets + nested/root gitignore allowlists + 3 skip-marked test files + committed panel parquet + CORRECTIONS.md.

**Plan metadata:** this run — `docs(05-00): SUMMARY + STATE + ROADMAP progress`.

## Files Created/Modified

- `analysis/tests/test_spot_check.py` — REPORT-02 scaffold (seeded determinism, Blockscout URL format, network-optional curl logging); 3 xfail-strict=False stubs.
- `analysis/tests/test_sensitivity_sweep.py` — REPORT-03 scaffold (9-cell pre-reg grid `rate_per_event∈{1,5,10}` × `USD_per_query∈{2.5e-6,5e-6,7.5e-6}`, per-cell qualitative recompute, no-new-cost-model grep guard that passes NOW).
- `analysis/tests/test_manifest.py` — REPORT-04 scaffold (pins-present, verify exit-codes, missing-artifact-fails 3-state, lockfile-name guard that passes NOW).
- `Makefile` — added `report-ichi` to `.PHONY` + as a target; replaced `verify-reproducibility` STUB with the real loop.
- `.gitignore` — scoped panel-parquet re-include chain under `data/raw/ichi/...`.
- `data/fits/.gitignore` — directory-spanning allowlist re-including the bdaf5c7ba5a2 artifacts.
- `data/fits/ichi/bdaf5c7ba5a2/CORRECTIONS.md` — now git-tracked (was untracked+ignored).
- `data/raw/ichi/0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F/67378253_67896653.parquet` — 128KB panel now git-tracked.

## Verification

**The scaffold was orchestrator-verified at commit `7373e73`; this run did NOT re-run any tests** (the slow full-suite path is what killed an earlier executor — re-verification is unnecessary because the code commit is immutable and the verification below is confirmed from immutable git state).

Acceptance-criteria evidence (confirmed from `git show --stat 7373e73` + `git ls-files` / `git check-ignore` against the committed tree, no test execution):

- **REPORT-01 / REPORT-04 — Makefile targets present:** `git show --stat 7373e73` shows `Makefile | 49 +++-`. Live confirmation: `grep -c "report-ichi" Makefile` = 7 (in `.PHONY` + target + body refs ≥2), `grep -c "verify-reproducibility:" Makefile` = 4 (target present, STUB replaced). `report-ichi` carries the `rm -f reports/ichi.pdf` stale-PDF collision guard; `verify-reproducibility` carries the parameterized `MANIFEST` path + awk canonical parse + 3-state rule + OK_COUNT==PIN_COUNT guard.
- **REPORT-02 / REPORT-03 / REPORT-04 — 3 test scaffolds collect:** `git show --stat 7373e73` shows `test_manifest.py | 125`, `test_sensitivity_sweep.py | 100`, `test_spot_check.py | 82` created; all three are git-tracked. Orchestrator confirmed 10 tests collect + skip-marked, with the 2 non-xfail guards passing.
- **REPORT-04 — nested data/fits/.gitignore allowlist:** `git show --stat 7373e73` shows `data/fits/.gitignore | 14 +++`. Live: `git check-ignore -q data/fits/ichi/bdaf5c7ba5a2/CORRECTIONS.md` → exit 1 (NOT ignored); `git ls-files data/fits/ichi/bdaf5c7ba5a2/ | wc -l` = 9 (8 prior + CORRECTIONS.md). CORRECTIONS.md created in the commit (`+8` lines).
- **REPORT-04 — root .gitignore panel negation + committed panel:** `git show --stat 7373e73` shows `.gitignore | 10 ++` and `67378253_67896653.parquet | Bin 0 -> 128791 bytes`. Live: `git check-ignore -q .../67378253_67896653.parquet` → exit 1 (NOT ignored); `git ls-files data/raw/ | grep -c 67378253_67896653.parquet` = 1. JSONL siblings remain ignored (no scope creep).
- **No scope creep:** other run dirs (ae9e3ba17900, 000c1cdce376) and the JSONL source cache stay ignored (orchestrator-confirmed `git check-ignore` returns exit 0 for them).

## Decisions Made

- **Option C-hybrid reproducibility (CONTEXT decision):** commit the canonical run-dir artifacts + the 128KB panel as fresh-clone evidence; `verify-reproducibility` checksums the committed files rather than re-fitting, because scipy MLE is not byte-reproducible across BLAS implementations (RESEARCH Pitfall 2). The JSONL source cache is NOT git-tracked, so `cli.py materialize`-on-absence is impossible offline — committing the panel is the chosen path.
- **report-ichi stale-PDF collision guard:** the legacy `render-null-result-pdf` target also writes `reports/ichi.pdf`; `report-ichi` `rm -f`s it immediately before `quarto render` so a stale/wrong-source PDF can never satisfy the `test -f` / size gate.
- **awk over read/sed for pin parsing:** sha256sum pins use a two-space separator; `awk '{print $1,$2}'` splits on whitespace runs (no leading-space artifact), and the OK_COUNT==PIN_COUNT assertion guards against silently-skipped pins (vacuous PASS).

## Deviations from Plan

None — the scaffold executed exactly as written. This finalization run is metadata-only: the scaffold code landed in `7373e73`, and two prior executors were killed on the trailing finalization steps (one on the slow full-suite wait). This run completes only the SUMMARY + STATE + ROADMAP metadata; no code, Makefile, gitignore, or test file was touched, and no tests were run.

## AF-12 OUT-OF-SCOPE (verbatim from plan/context)

Per 05-CONTEXT.md (REPORT-03 sensitivity-sweep presentation), held verbatim as the AF-12 + CLAUDE.md non-negotiable boundary:

> **NO new cost-leg model, NO dominance-Δ implementation, NO κ index** (AF-12 + CLAUDE.md non-negotiable). If a cell's condition set is invariant to the cost priors (likely, since the conditions derive from the DGP density not the cost leg), report that invariance honestly as the finding.

And the phase-level out-of-scope (05-CONTEXT.md Phase Boundary):

> **Out of scope (own phases):** Iteration-2 / Steer (Phase 6); the power-law kernel sweep + more-data certification (v2 / DGP-V2-01); any re-fit or re-hedge of the DGP (Phase 04.1.1 is closed); deployed Solidity hedge contracts (Iteration 3+).

The Phase-04.1.1 verdict being reported is FIXED and MUST NOT be flipped, narrowed, or relabeled (AF-03; HALT disposition memo on record): run_id `bdaf5c7ba5a2`, gate_passes=FALSE (3/4), firing_condition=`null_strip_unavailable`, η≈0.600, held-out KS knife-edge miss (leg-0 p=0.0474). This scaffold introduced NO source code under `analysis/src/`, NO fit/hedge recompute, and did NOT author MANIFEST.md or ichi.qmd (downstream plans own those).

## Review Trail

Two-step review (Reality Checker + DevOps Automator specialist) for the Phase-5 plan set — including this 05-00 scaffold — landed in commit `226e164` ("docs(05): Phase 5 plans (5) + two-step review trail — PASS"). Both reviewers returned PASS prior to execution.

## Issues Encountered

Two prior executor runs were killed on trailing finalization steps (run #1 on the slow full-suite verification wait). The scaffold code commit `7373e73` was unaffected — clean and complete — leaving only metadata finalization, which this run performs without touching code or running tests.

## Next Phase Readiness

- Wave 1 (05-01 sensitivity sweep, 05-02 manifest) and Wave 2 (05-03 ichi.qmd render) can now land against present, collectible, fresh-clone-reproducible structure.
- All downstream file references exist: 3 test files, 2 Makefile targets, both gitignore allowlists, committed panel + run-dir.
- `make verify-reproducibility` exits 0 on the SKIP path until 05-02 authors `reports/MANIFEST.md`; `make report-ichi` fails with an explicit "quarto required" / "ichi.qmd absent" message until 05-03 authors the qmd (both expected at Wave 0).

## Self-Check: PASSED

Files verified present (git-tracked in `7373e73`):
- FOUND: analysis/tests/test_spot_check.py
- FOUND: analysis/tests/test_sensitivity_sweep.py
- FOUND: analysis/tests/test_manifest.py
- FOUND: data/fits/ichi/bdaf5c7ba5a2/CORRECTIONS.md (tracked; run-dir now 9 files)
- FOUND: data/raw/ichi/0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F/67378253_67896653.parquet (tracked)

Commit verified:
- FOUND: 7373e73 (`git log --oneline --all | grep -q 7373e73` → present)

Gitignore behavior verified (no test execution):
- CORRECTIONS.md NOT ignored (check-ignore exit 1); panel NOT ignored (check-ignore exit 1).

---
*Phase: 05-reporting-iteration-1-pdf-deliverable-l7*
*Completed: 2026-05-29*
