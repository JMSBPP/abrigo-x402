---
phase: 06-iteration-2-swap-surface-validation-on-steer-ccop-usdt
plan: 03
subsystem: validation
tags: [config-swap, repro-02, hedge-05, null-cost, steer, ccop-usdt, quarto, hawkes]

# Dependency graph
requires:
  - phase: 06-iteration-2-swap-surface-validation-on-steer-ccop-usdt (Plan 06-01)
    provides: "de-papermilled generic null-result renderer (-M + HEDGE05_FIRING_CONDITION env) + data/raw/<protocol>/ materialize namespace + REPRO-02 empty-diff baseline pin 9add304"
  - phase: 06-iteration-2-swap-surface-validation-on-steer-ccop-usdt (Plan 06-02)
    provides: "pre-registered Steer cost-leg STRADDLE rule (verdict FAIL -> null_cost) + notes/steer_cost_leg_bound.md + iteration-2-full Makefile recipe + Q9-fallback-deferred pre-reg"
provides:
  - "Steer cCOP/USDT config-swap run of the FROZEN Phase 2-5 pipeline (run_id 0dc5bee374b6) with ZERO fetch/src + analysis/src edits"
  - "reports/steer_null_result.pdf (145942B) — Iteration-2 null-result deliverable headlining null_cost, HEDGE05-NULL-RESULT-V1 signed, no forbidden narrowing"
  - "data/fits/steer/0dc5bee374b6/ artifact set (fit_report, gate_report, firing_condition=null_cost) — null_cost fired from INSIDE the completed run"
  - "REPRO-02 zero-edit invariant demonstrated under a live config-swap run (git diff 9add304 HEAD -- fetch/src analysis/src EMPTY)"
affects: [06-04, iteration-2-verification, cycle-closure]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Config-swap re-run: same frozen pipeline driven entirely by protocols/steer.toml + --protocol-toml namespace, no source edits"
    - "null_cost fires from a FIELD inside the completed run (Decision 3 SC-2-vs-SC-4 resolution), not a pre-fetch short-circuit"

key-files:
  created:
    - "reports/steer_null_result.pdf (145942B, committed — gitignore allowlisted)"
    - ".planning/phases/06-…/_artifacts/steer_run_id.txt (0dc5bee374b6)"
  modified: []

key-decisions:
  - "Steer cost-leg null_cost OBSERVED from inside the completed run (condition (a), sequential tree fires first) — verdict FAIL on the 30k-100k STRADDLE vs the 100k/mo Graph free-tier line"
  - "REPRO-02 zero-edit invariant HELD under a live config-swap run: git diff 9add304 HEAD -- fetch/src analysis/src EMPTY"
  - "Q9 unified-panel fallback DEFERRED per Plan 02 pre-registration; V3-anchor-only reported with the signal-scope caveat; SC-5 SKIP-with-reason (q9_pooling_test.json absent by design)"

patterns-established:
  - "Iteration-N swap-surface validation = config-swap run + null-result PDF + REPRO-02 empty-diff attestation, with the firing condition derived from the run output"

requirements-completed: [REPRO-02, REPRO-04, HEDGE-05]

# Metrics
duration: ~45min (across the 3-task plan incl. checkpoint)
completed: 2026-05-29
---

# Phase 6 Plan 03: Steer cCOP/USDT Config-Swap Null-Result Run Summary

**The frozen Phase 2-5 pipeline ran end-to-end on protocols/steer.toml (config-swap, ZERO fetch/src + analysis/src edits), null_cost fired from inside the completed run, and reports/steer_null_result.pdf (145942B) rendered the Iteration-2 null-result deliverable — REPRO-02 zero-edit invariant held under a live run.**

## Performance

- **Duration:** ~45 min (3-task plan, including the human-verify checkpoint round-trip)
- **Completed:** 2026-05-29
- **Tasks:** 3 (2 auto + 1 checkpoint:human-verify, APPROVED)
- **Files committed:** reports/steer_null_result.pdf + _artifacts/steer_run_id.txt (data/raw/steer + data/fits/steer are gitignored)

## Accomplishments

- **Config-swap run of the frozen pipeline on Steer cCOP/USDT** (run_id `0dc5bee374b6`): fetch -> materialize (`data/raw/steer/0x2AC5baA668A8A58FD0e302B9896717484fd217B0/65600000_68190000.parquet`, 533 rows) -> fit (`data/fits/steer/0dc5bee374b6/`) -> hedge, all driven by `protocols/steer.toml` + `--protocol-toml protocols/steer.toml`, with ZERO edits to `fetch/src` or `analysis/src`.
- **null_cost fired from INSIDE the completed run.** `decide_firing_condition` evaluated condition (a) first against the Plan-02 `notes/steer_cost_leg_bound.md` verdict (FAIL on the 30k-100k STRADDLE vs the 100k/mo Graph free-tier line) and returned `null_cost`. The full DGP/Hawkes/gate output ran regardless of the cost-leg fail — the run is what demonstrates the zero-edit invariant.
- **reports/steer_null_result.pdf** rendered via the Plan-01 fixed generic renderer: 145942B (> 50KB), `null_cost` appears x3 in the PDF body (cost-leg headline), `HEDGE05Marker: HEDGE05-NULL-RESULT-V1` custom-field dual signature present, and zero forbidden-narrowing strings (AF-03 SHARED 5-string set: 0 hits).
- **REPRO-02 zero-edit invariant demonstrated under a live run:** `git diff 9add304 HEAD -- fetch/src analysis/src` is EMPTY across both Task commits.
- **Live cCOP/USDT provenance** spot-checked at the human-verify checkpoint: 3 panel-row Blockscout tx URLs returned HTTP 200 (operator confirmed; checkpoint APPROVED).

## Task Commits

1. **Task 1: Config-swap run of frozen pipeline on Steer cCOP/USDT (fetch+materialize+fit)** — `33f3e00` (feat)
   - data/raw/steer/ panel (533 rows, gitignored) + data/fits/steer/0dc5bee374b6/ (gitignored) + _artifacts/steer_run_id.txt
2. **Task 2: hedge stage + reports/steer_null_result.pdf (null_cost from inside the run)** — `3c01427` (feat)
   - hedge stage emits firing_condition=null_cost; reports/steer_null_result.pdf 145942B committed
3. **Task 3: human-verify checkpoint (null PDF + live cCOP/USDT provenance)** — APPROVED by user (no code commit; verification gate)

**Plan metadata:** (this commit — docs: complete plan)

## Run facts (on-disk)

- **run_id:** `0dc5bee374b6` (gitCommit `33f3e00`, blockRange [65600000, 68190000], dataHash `5997a25e…`)
- **firing_condition.json:** `firing_condition: "null_cost"`, `decided_by: abrigo_x402.hedge.null_result.decide_firing_condition`
- **gate_report.json:** `any_condition_passed: true` (hawkes_self_excitation passed: branching_ratio=0.709 ≥ 0.2 floor; usdt_depeg_basis_jump passed; vol_of_vol + positive_skew_fat_tails did not pass) — convex-dominance support material, NOT the firing condition (cost-leg null_cost fired first in the tree).
- **fit_report.json:** `fit_method_used=scipy_canonical_ll`; `gate_passes=false`; `total_events_per_leg=[271, 260]`; canonical LL sources point at `abrigo_x402.dgp.lr_test._{hawkes_loglik_vectorized,nhpp_pointprocess_loglik}` (Pattern F).

## Q9 trigger evaluation (logged)

- `branching_ratio_ci`: `method=constrained_mle_profile`, `eta_hat=0.709`, `lower=0.001`, `upper=0.95`, `ci_width=0.949`, `q9_threshold=0.4`, **`q9_nullfire_triggered=true`** (0.949 > 0.4 — CI-width trigger fired on the grid-clamped interval).
- Per-leg event counts `271 / 260` are below the 300-event sample-size floor.
- Per the Plan-02 pre-registration, the unified cross-class Q9 fallback is **DEFERRED** (not authored). The V3-anchor-only fit is reported with the pre-registered signal-scope caveat. **SC-5 SKIP-with-reason**: `panel_construction=v3-anchor-only`; `q9_pooling_test.json` absent by design; no REPRO-02 violation (no fallback module written).

## Decisions Made

- See key-decisions frontmatter. The cost-leg null_cost is OBSERVED (from the run output field), not pre-committed to a positive; the verdict was NOT narrowed/relabeled (AF-03 discipline — 0 forbidden-narrowing strings in the PDF).

## Deviations from Plan

Three deviations were flagged at the Task-3 checkpoint return and APPROVED by the user. None touched the frozen `fetch/src` + `analysis/src` REPRO-02 scope (the empty-diff invariant held).

### Auto-fixed / worked-around Issues

**1. [Rule 3 - Blocking] `fetch/scripts/build_panel_real.ts` hardcodes `data/raw/ichi/<pool>`**
- **Found during:** Task 1 (config-swap fetch leg)
- **Issue:** The `fetch/scripts/` driver `build_panel_real.ts` hardcodes the `data/raw/ichi/<pool>` output namespace. This driver lives in `fetch/scripts/`, OUTSIDE the frozen `fetch/src` + `analysis/src` REPRO-02 scope.
- **Fix:** Worked around via stage-then-relocate (run, then move the panel into the `data/raw/steer/<pool>/` namespace). ZERO source edits to `fetch/src` or `analysis/src`.
- **Verification:** Panel landed at `data/raw/steer/0x2AC5…/65600000_68190000.parquet` (steer namespace, not ichi); `git diff 9add304 HEAD -- fetch/src analysis/src` EMPTY.
- **Committed in:** `33f3e00` (Task 1 commit)

**2. [Rule 3 - Blocking] `make iteration-2-full` recipe passes `--reports-pdf ../reports/…`**
- **Found during:** Task 2 (hedge + render leg)
- **Issue:** The `make iteration-2-full` recipe passes `--reports-pdf ../reports/…`, which would land the PDF ABOVE the repo root (latent recipe path bug).
- **Fix:** Invoked the hedge stage with a repo-correct `--reports-pdf reports/steer_null_result.pdf` so the PDF lands inside the repo. The recipe path bug is NOTED for a future maintenance pass (not fixed here — out of this plan's frozen-source scope and not blocking the deliverable).
- **Verification:** `reports/steer_null_result.pdf` exists at the repo path, 145942B, committed.
- **Committed in:** `3c01427` (Task 2 commit)

**3. [Rule 1 - Depth] PDF at generic-template depth — DGP-support tables + REPRO-02 attestation line not inlined**
- **Found during:** Task 2 / Task 3 (PDF render + checkpoint)
- **Issue:** The Plan-01 fixed generic renderer emits the null-result PDF at generic-template depth; the DGP-support tables and the REPRO-02 zero-edit attestation line are not inlined into the PDF body.
- **Fix:** The DGP/gate support and the REPRO-02 attestation are recorded on-disk (`data/fits/steer/0dc5bee374b6/gate_report.json`, `fit_report.json`) and in the Task commit bodies instead of inlined into the PDF. The user APPROVED the deliverable at this depth at the Task-3 checkpoint.
- **Verification:** PDF carries the `null_cost` headline (x3) + HEDGE05 signature; the support facts are auditable on-disk and in the commit history; checkpoint APPROVED.
- **Committed in:** `3c01427` (PDF) + recorded in this SUMMARY

---

**Total deviations:** 3 (2 Rule-3 blocking work-arounds, 1 Rule-1 depth note). All OUTSIDE the frozen `fetch/src` + `analysis/src` REPRO-02 scope — the empty-diff invariant held. User APPROVED the deliverable at the Task-3 checkpoint.
**Impact on plan:** No scope creep into frozen sources. Two latent bugs (fetch/scripts hardcoded namespace, Makefile recipe PDF path) noted for a maintenance pass.

## Issues Encountered

None beyond the three documented deviations. The cost-leg null_cost is the expected, honest Iteration-2 outcome (HEDGE-05 condition (a)); it was recorded AS-OBSERVED, not narrowed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Plan 06-04 (REPRO-02 attestation)** is unblocked: it reads `_artifacts/repro_02_baseline_sha.txt` (pins `9add304…`) and attests the empty-diff invariant; this plan demonstrated it held under a live run.
- The Iteration-2 null-result deliverable (`reports/steer_null_result.pdf`) is on disk + committed for the phase acceptance gate.

## Self-Check: PASSED

- **reports/steer_null_result.pdf** — FOUND (145942B > 50KB; `null_cost` x3 in body; `HEDGE05Marker: HEDGE05-NULL-RESULT-V1`; 0 forbidden-narrowing strings)
- **.planning/phases/06-…/_artifacts/steer_run_id.txt** — FOUND (`0dc5bee374b6`)
- **data/fits/steer/0dc5bee374b6/firing_condition.json** — FOUND (`firing_condition: null_cost`)
- **data/fits/steer/0dc5bee374b6/{fit_report,gate_report}.json** — FOUND
- **Commit `33f3e00`** — FOUND in git log
- **Commit `3c01427`** — FOUND in git log
- **REPRO-02:** `git diff 9add304 HEAD -- fetch/src analysis/src` — EMPTY (PASS)

---
*Phase: 06-iteration-2-swap-surface-validation-on-steer-ccop-usdt*
*Completed: 2026-05-29*
