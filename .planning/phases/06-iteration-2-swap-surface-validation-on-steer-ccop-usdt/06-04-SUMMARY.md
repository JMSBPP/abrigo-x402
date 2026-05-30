---
phase: 06-iteration-2-swap-surface-validation-on-steer-ccop-usdt
plan: 04
subsystem: testing
tags: [repro-02, af-03, verify-reproducibility, hedge-05, null-cost, steer, acceptance-gate, content-check]

# Dependency graph
requires:
  - phase: 06-iteration-2-swap-surface-validation-on-steer-ccop-usdt (Plan 06-01)
    provides: "_artifacts/repro_02_baseline_sha.txt pinning 9add304 as the REPRO-02 empty-diff base + AF-12 REPRO-01 scoped-grep re-scope note"
  - phase: 06-iteration-2-swap-surface-validation-on-steer-ccop-usdt (Plan 06-02)
    provides: "pre-registered Steer cost-leg STRADDLE rule (verdict FAIL -> null_cost) committed before the verdict (AF-03) + notes/steer_cost_leg_bound.md"
  - phase: 06-iteration-2-swap-surface-validation-on-steer-ccop-usdt (Plan 06-03)
    provides: "Steer config-swap run (run_id 0dc5bee374b6) + reports/steer_null_result.pdf (145942B, null_cost) + data/fits/steer/0dc5bee374b6/firing_condition.json"
provides:
  - "REPRO-02 empty-diff attestation (_artifacts/repro_02_attestation.txt): base read from the pinned file (M3), git diff 9add304 HEAD -- fetch/src analysis/src EMPTY"
  - "AF-03 commit-ordering proof: pre-reg fc6eec0 + re-scope 9add304 predate verdict 0475bed + run 33f3e00/3c01427"
  - "verify-reproducibility extended with the steer null PDF content-check (size + null_cost + cost-leg + HEDGE05 via pdfinfo -custom + AF-03 5-string no-narrowing loop) — make verify-reproducibility PASS (13/13 sha pins + ichi + steer)"
  - "reports/MANIFEST.md steer_null_result.pdf row (content-checked, NOT byte-pinned — Phase-5 B1 lesson)"
  - "06-VERIFICATION-pre.md: REPRO-01..04 + HEDGE-05(a) + SC-1..5 acceptance grid; verification_pass=true (all 3 M2 gates hold); null AS-OBSERVED; SC-5 explicit SKIP-with-reason; B3 python3 coverage gate"
affects: [cycle-closure, phase-06-verification, iteration-2-pr]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "REPRO-02 empty-diff attestation reads the diff base from a pinned sha file (M3), never grepping a SUMMARY for a hex token"
    - "Generic null-result PDF carries the HEDGE05 marker as a CUSTOM metadata field (pdfinfo -custom), distinct from the ichi.qmd Keywords field — the steer content-check uses pdfinfo -custom"
    - "AF-03 forbidden-narrowing guard text DESCRIBES the 5 phrasings rather than quoting them contiguously, so a context-blind grep of the verification doc does not false-positive (Phase-5 B1/AF-03 enumeration-trap discipline)"

key-files:
  created:
    - ".planning/phases/06-…/_artifacts/repro_02_attestation.txt (REPRO-02 empty-diff + AF-03 ordering + REPRO-01 two-layer)"
    - ".planning/phases/06-…/06-VERIFICATION-pre.md (Phase 6 acceptance grid)"
  modified:
    - "Makefile (verify-reproducibility: additive steer PDF content-check)"
    - "reports/MANIFEST.md (steer_null_result.pdf content-checked row)"

key-decisions:
  - "verification_pass: true — all three M2 conditional gates hold this session (steer PDF 145942B>50KB + null_cost observed in firing_condition.json AND the in-session gate report + REPRO-02 empty-diff EMPTY)"
  - "Steer null_cost recorded AS-OBSERVED (the D-08 negative control), NOT narrowed; substitute-pending disposition recorded with the AF-03 future-substitute pre-registration guardrail"
  - "SC-5 = explicit SKIP-with-reason (V3-anchor-only; unified fallback pre-registered deferred; q9_pooling_test.json absent by design) — recorded VERBATIM, not PASS, not omitted"
  - "Steer HEDGE05 marker lives in the custom field HEDGE05Marker (pdfinfo -custom), unlike ichi's Keywords field — the steer Makefile check uses pdfinfo -custom accordingly"

patterns-established:
  - "Iteration-N acceptance gate = REPRO-02 empty-diff attestation (base from pinned file) + AF-03 ordering proof + null-PDF content-check in verify-reproducibility + a VERIFICATION-pre.md grid with a conditional verification_pass and an explicit python3 (NOT awk) coverage gate"

requirements-completed: [REPRO-01, REPRO-02, REPRO-03, REPRO-04, HEDGE-05]

# Metrics
duration: ~25min
completed: 2026-05-29
---

# Phase 6 Plan 04: REPRO-02 Honest-Pass Gate + Steer Acceptance Grid Summary

**REPRO-02 empty-diff attested from the pinned post-Plan-01 baseline (9add304 -> HEAD EMPTY) with AF-03 ordering proven; verify-reproducibility now content-checks reports/steer_null_result.pdf (null_cost + HEDGE05 + AF-03 no-narrowing); 06-VERIFICATION-pre.md maps REPRO-01..04 + HEDGE-05 + SC-1..5 to runnable commands with verification_pass=true and the null recorded AS-OBSERVED.**

## Performance

- **Duration:** ~25 min (3 auto tasks)
- **Completed:** 2026-05-29
- **Tasks:** 3 (all auto)
- **Files created/modified:** 4 (2 created, 2 modified)

## Accomplishments

- **REPRO-02 honest pass attested.** `BASE=$(cat _artifacts/repro_02_baseline_sha.txt)` = `9add304…` (single 40-char line, M3 — read from the pinned file, NOT grepped from a SUMMARY); `git diff "$BASE" HEAD -- fetch/src analysis/src` is EMPTY across the iteration-1-complete -> iteration-2-complete window (demonstrated under the live config-swap run `0dc5bee374b6`). Full attestation written to `_artifacts/repro_02_attestation.txt`.
- **AF-03 commit-ordering proven.** `git log -- notes/PRE_REGISTRATION.md notes/steer_cost_leg_bound.md` + timestamps show the pre-registered STRADDLE rule `fc6eec0` (18:30:06) and the REPRO-01 re-scope note `9add304` (Plan 01) PREDATE the cost-leg verdict emission `0475bed` (18:30:13) and the Steer run/hedge commits `33f3e00` (19:17:16) / `3c01427` (19:19:48). The rule was fixed before the verdict and before any Steer data drove the pipeline.
- **REPRO-01 two-layer gate green.** `make leak-check` exit 0 ("PASS: leak-check clean") + `cd fetch && pnpm test protocol-agnostic` 6 passed exit 0; the scoped genuine-coupling grep returns 0 hits.
- **verify-reproducibility extended.** Added an additive steer PDF content-check after the ichi block: size > 51200 (observed 145942 B), `pdftotext` greps `null_cost` + a cost-leg/STRADDLE evidence string, `pdfinfo -custom` greps the `HEDGE05` marker, and the shared 5-string AF-03 forbidden-narrowing loop finds NOTHING. `make verify-reproducibility` PASS (13/13 sha pins + ichi + steer), exit 0. MANIFEST carries a content-checked (NOT byte-pinned) steer row.
- **06-VERIFICATION-pre.md authored.** REPRO-01, REPRO-02, REPRO-03, REPRO-04, HEDGE-05(a) + ROADMAP SC-1..5 mapped to {command, expected, observed, verdict}. `verification_pass: true` (all three M2 gates hold). SC-5 = the explicit SKIP-with-reason string verbatim. The requirement-coverage gate is an explicit `python3` exit-code test (NOT `awk '$1>=5'`). The null is recorded AS-OBSERVED with the substitute-pending disposition + AF-03 future-substitute guardrail; 0 forbidden-narrowing strings.

## Task Commits

Each task was committed atomically:

1. **Task 1: REPRO-02 empty-diff attestation + AF-03 ordering proof** — `d5d4268` (test)
2. **Task 2: steer PDF content-check in verify-reproducibility + MANIFEST row** — `9d6cfa0` (chore)
3. **Task 3: author 06-VERIFICATION-pre.md acceptance grid (null AS-OBSERVED)** — `cf41c0d` (test)

**Plan metadata:** (this commit — docs: complete plan)

## Files Created/Modified

- `_artifacts/repro_02_attestation.txt` — REPRO-02 empty-diff command/result + baseline sha + AF-03 ordering proof + REPRO-01 two-layer gate (created)
- `06-VERIFICATION-pre.md` — Phase 6 acceptance grid + REPRO-02 attestation section + verdict AS-OBSERVED + cycle-closure next-step (created)
- `Makefile` — `verify-reproducibility` extended with the additive steer null PDF content-check (modified)
- `reports/MANIFEST.md` — steer_null_result.pdf row, content-checked (modified)

## Decisions Made

- See key-decisions frontmatter. `verification_pass: true` because the three M2 gates are all satisfied THIS session (PDF >50KB + null_cost observed + empty-diff EMPTY); had any been unmet it would be `false` with `verdict: pending-fetch`. The null `null_cost` is the AS-OBSERVED D-08 negative control — not narrowed, not relabeled.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Steer HEDGE05 marker requires `pdfinfo -custom`, not plain `pdfinfo`**
- **Found during:** Task 2 (verify-reproducibility extension)
- **Issue:** The plan said to mirror the ichi PDF check, whose Makefile block greps `HEDGE05` from plain `pdfinfo` (the ichi.qmd template writes the marker into the standard `Keywords` field). The generic null-result renderer that produced `reports/steer_null_result.pdf` writes the marker ONLY as a custom metadata field `HEDGE05Marker`, which plain `pdfinfo` does not list — so a plain-`pdfinfo` grep would false-FAIL the steer check.
- **Fix:** The steer check uses `pdfinfo -custom` to read the `HEDGE05Marker` custom field. Verified `pdfinfo -custom reports/steer_null_result.pdf | grep HEDGE05` returns `HEDGE05Marker: HEDGE05-NULL-RESULT-V1`.
- **Files modified:** Makefile
- **Verification:** `make verify-reproducibility` exit 0 with "OK (content: size+null_cost+HEDGE05+cost-leg, AF-03 no-narrowing): reports/steer_null_result.pdf"
- **Committed in:** `9d6cfa0` (Task 2 commit)

**2. [Rule 1 - Bug] Forbidden-narrowing enumeration tripped a context-blind grep of the verification doc**
- **Found during:** Task 3 (06-VERIFICATION-pre.md authoring)
- **Issue:** The AF-03 forbidden-narrowing guard sentence originally quoted all five forbidden strings contiguously, so a context-blind grep of the VERIFICATION file false-positived (1 hit each) on the enumeration itself — the same Phase-5 B1/AF-03 enumeration trap.
- **Fix:** Rephrased the guard to DESCRIBE the five phrasings ("the pass-with-caveat phrasing", "the near-miss-prefixed positive", etc.) rather than quoting them contiguously, preserving the meaning while keeping the doc grep-clean (0 hits for all five). The load-bearing content-check still targets the PDF, not this doc.
- **Files modified:** 06-VERIFICATION-pre.md
- **Verification:** `grep -ci` for each of the five strings = 0; coverage gate still count=28>=5; null_cost 16 hits.
- **Committed in:** `cf41c0d` (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (both Rule-1 bugs in the verification tooling/text). NONE touched the frozen `fetch/src` + `analysis/src` REPRO-02 scope — the empty-diff invariant held across all three commits.
**Impact on plan:** No scope creep. Both fixes were necessary for the content-check to pass correctly and for the verification doc to survive a naive grep.

## Known carried-forward deviations (from Plan 06-03, recorded as known-items in the grid)

Documented in 06-VERIFICATION-pre.md as known-items (all APPROVED at the 06-03 checkpoint, all OUTSIDE the frozen scope): (1) `fetch/scripts/build_panel_real.ts` hardcodes `data/raw/ichi/<pool>` (worked around via stage+relocate); (2) `make iteration-2-full` recipe `--reports-pdf ../reports/…` latent path bug (invoked with the repo-correct path); (3) PDF at generic-template depth (DGP-support + REPRO-02 attestation recorded on-disk + in commits, user-approved).

## Issues Encountered

None beyond the two documented Rule-1 deviations. The Steer `null_cost` is the expected, honest Iteration-2 outcome (HEDGE-05 condition (a)); recorded AS-OBSERVED.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Phase 6 acceptance gate is GREEN:** `verification_pass: true`; REPRO-01..04 + HEDGE-05 all mapped to passing commands; `make verify-reproducibility` PASS (ichi + steer).
- **Cycle-closure next step (USER-gated, per CLAUDE.md ritual):** the Iteration-2 terminal deliverable (`reports/steer_null_result.pdf`) has landed + verified. Next: **push origin -> open PR into upstream (`wvs-finance/abrigo-x402:master`) -> merge upstream after verification passes.** The PR body must honestly summarize the `null_cost` D-08 negative control AS-OBSERVED (NOT narrowed). No push to upstream from inside this plan (AF-12 OUT-OF-SCOPE; user-gated).

## Self-Check: PASSED

- `_artifacts/repro_02_attestation.txt` — FOUND
- `06-VERIFICATION-pre.md` — FOUND (verification_pass: true; coverage count=28; 0 forbidden-narrowing strings; SC-5 verbatim SKIP string present)
- `Makefile` steer_null_result hits — 2 (FOUND)
- `reports/MANIFEST.md` steer_null_result hits — 1 (FOUND)
- Commit `d5d4268` — FOUND in git log
- Commit `9d6cfa0` — FOUND in git log
- Commit `cf41c0d` — FOUND in git log
- REPRO-02: `git diff 9add304 HEAD -- fetch/src analysis/src` — EMPTY (PASS)
- `make verify-reproducibility` — PASS (13/13 sha pins + ichi + steer), exit 0

---
*Phase: 06-iteration-2-swap-surface-validation-on-steer-ccop-usdt*
*Completed: 2026-05-29*
