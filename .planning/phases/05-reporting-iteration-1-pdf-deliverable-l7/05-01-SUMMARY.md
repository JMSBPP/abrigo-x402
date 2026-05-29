---
phase: 05-reporting-iteration-1-pdf-deliverable-l7
plan: 01
subsystem: reporting
tags: [report-03, sensitivity-sweep, convex-dominance, qualitative-conditions, honest-broadcast, hawkes]

# Dependency graph
requires:
  - phase: 05-00
    provides: nested data/fits/.gitignore allowlist re-including ichi/bdaf5c7ba5a2/*.json; skip-marked test_sensitivity_sweep.py scaffold
  - phase: 04.1.1
    provides: canonical run_id bdaf5c7ba5a2 gate_report.json (4 convex-dominance conditions) + firing_condition.json (null_strip_unavailable)
provides:
  - "data/fits/ichi/bdaf5c7ba5a2/sensitivity_sweep.json — the 9-cell qualitative convex-dominance sweep the PDF presents (REPORT-03)"
  - "abrigo_x402.report package + compute_sensitivity_sweep(run_dir) entry point for the .qmd cell + the test"
affects: [05-02, 05-03, 05-04, reports/ichi.qmd, MANIFEST.md]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Honest-broadcast labeling: evaluate the parameter-free gate ONCE, broadcast to the grid with evaluated_once/broadcast_to_grid/depends_on_cost_priors:false — never a fabricated per-cell recomputed flag (AF-03 label-vs-reality discipline)"
    - "Gate-sourced test assertion: each cell boolean tied to gate_report.json evidence .passed so a constant-copy-with-fake-flag would fail"
    - "Docstring forbidden-token avoidance: prose rephrased so the no-cost-model grep gate (κ/dominance_delta/cost_leg/cost_of_convexity) sees zero hits (same regression class as 04-00/03-00 docstring fixes)"

key-files:
  created:
    - analysis/src/abrigo_x402/report/__init__.py
    - analysis/src/abrigo_x402/report/sensitivity_sweep.py
    - data/fits/ichi/bdaf5c7ba5a2/sensitivity_sweep.json
  modified:
    - analysis/tests/test_sensitivity_sweep.py

key-decisions:
  - "Sourced the 4 booleans from gate_report.json's persisted evidence dict (a real Phase-04.1.1 evaluation) rather than re-invoking evaluate_four_conditions, which would require re-fitting read-only-unavailable residuals/fit inputs — honest, and respects the no-recompute invariant"
  - "Reported cost-prior invariance honestly as the convexity-driven finding (conditions_cost_prior_invariant=true), not manufactured cost-dependent variation"

patterns-established:
  - "Pattern: evaluate-once + honest broadcast for parameter-free gate metrics over a parameter grid"

requirements-completed: [REPORT-03]

# Metrics
duration: ~12min
completed: 2026-05-29
---

# Phase 5 Plan 01: REPORT-03 Qualitative-Conditions Sensitivity Sweep Summary

**A 9-cell cost-prior sweep over the 4 qualitative convex-dominance conditions, evaluated once from the gate's own evidence and broadcast honestly across the pre-reg-locked {1,5,10}×{2.5e-6,5e-6,7.5e-6} grid — reporting cost-prior invariance as the convexity-driven finding, with no cost-leg model introduced.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-05-29T17:25:00Z (approx)
- **Completed:** 2026-05-29T17:37:00Z
- **Tasks:** 1 (TDD)
- **Files modified:** 4 (3 created + 1 rewritten)

## Accomplishments
- Produced `data/fits/ichi/bdaf5c7ba5a2/sensitivity_sweep.json`: exactly 9 cells over the PRE-REG-LOCKED grid `rate_per_event ∈ {1,5,10}` × `USD_per_query ∈ {2.5e-6,5e-6,7.5e-6}`, each carrying the 4 convex-dominance booleans (nested under `conditions`) + `firing_condition: null_strip_unavailable` + honest labels `evaluated_once/broadcast_to_grid/depends_on_cost_priors:false`.
- The four booleans are SOURCED from `gate_report.json`'s own evidence `.passed` values (a real Phase-04.1.1 gate evaluation), not inline literals — the test ties each cell boolean to the gate source so a constant copy with a fabricated `recomputed` flag would fail.
- Reported cost-prior invariance honestly: `conditions_cost_prior_invariant=true`, `all_cells_any_condition_passed=true`, with the modeled-not-paid / convexity-driven caveat. No new cost-leg model, no dollar-Δ, no provider-complexity index anywhere in `analysis/src/` (canonical forbidden-regex clean).
- Created the `abrigo_x402.report` package with `compute_sensitivity_sweep(run_dir)` as the entry point the `.qmd` cell + tests call. Artifact git-tracked via plain `git add` (05-00 nested allowlist, not `-f`).

## Task Commits

1. **Task 1 (RED): sensitivity_sweep tests** - `826b13f` (test) — rewrote the Wave-0 xfail scaffold into 4 real tests per the plan behavior block; module-import RED.
2. **Task 1 (GREEN): sensitivity_sweep module + artifact** - `12bfd33` (feat) — `abrigo_x402.report.sensitivity_sweep` + `sensitivity_sweep.json`; 4 tests GREEN.

_TDD: RED → GREEN (no REFACTOR needed; module clean)._

## Files Created/Modified
- `analysis/src/abrigo_x402/report/__init__.py` - re-exports `compute_sensitivity_sweep` + the GRID constants.
- `analysis/src/abrigo_x402/report/sensitivity_sweep.py` - `compute_sensitivity_sweep(run_dir)`: reads `gate_report.json` + `firing_condition.json` read-only, sources the 4 booleans from the gate evidence, broadcasts to the 9-cell pre-reg grid with honest labels, writes `sensitivity_sweep.json`.
- `analysis/tests/test_sensitivity_sweep.py` - 4 tests: schema+grid, per-cell-evaluated-and-broadcast (gate-sourced), invariance-reported-honestly, no-new-cost-model (canonical forbidden-regex).
- `data/fits/ichi/bdaf5c7ba5a2/sensitivity_sweep.json` - the 9-cell artifact the PDF presents.

## Decisions Made
- Read the gate's persisted evidence dict from `gate_report.json` rather than re-invoking `evaluate_four_conditions` (which requires `residuals_df`/`fit_report`/`calibration`/`lhs_samples` — re-fit inputs not available read-only, and re-invoking would violate the no-recompute invariant). The booleans are still the gate's, not inline literals; the test ties them to the gate source.
- Reported invariance as the honest finding (conditions are DGP-density-derived, cost-prior-free) instead of manufacturing cost-dependent variation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Docstring tripped the no-cost-model grep gate**
- **Found during:** Task 1 (GREEN test run)
- **Issue:** `test_no_new_cost_model_introduced` failed because the module docstring contained the literal Greek `κ` (and `dominance-Δ`) while explaining what is forbidden — the canonical forbidden-regex `κ|dominance_delta|...` matched the prose, not a cost model.
- **Fix:** Rephrased the docstring to "no provider-complexity-index term of any kind" (no literal `κ`, no `dominance` token) — same regression class as the 04-00 and 03-00 docstring-vs-grep-gate fixes.
- **Files modified:** `analysis/src/abrigo_x402/report/sensitivity_sweep.py`
- **Verification:** `grep -rIE 'kappa|κ|dominance_delta|def +cost_leg|cost_of_convexity' analysis/src/` returns rc=1 (clean); all 4 tests GREEN.
- **Committed in:** `12bfd33` (part of the GREEN task commit)

---

**Total deviations:** 1 auto-fixed (1× Rule 3).
**Impact on plan:** The fix was a prose rephrase required to satisfy the plan's own forbidden-regex acceptance gate; zero scope creep, zero behavior change.

## Issues Encountered
None beyond the docstring grep-gate (above). Verification was kept to the targeted `pytest tests/test_sensitivity_sweep.py -x` (fast, JSON-only, thread-pinned) — the full slow Hawkes-fit suite was deliberately NOT run, per the verification-discipline invariant. The fit was NOT recomputed; artifacts were consumed read-only.

## AF-12 OUT-OF-SCOPE (honored verbatim)

- NO new cost-leg model, NO dollar-Δ metric, NO provider-complexity index anywhere in analysis/src/ (forbidden-regex clean, byte-identical to 05-00).
- NO re-fit / NO re-hedge — gate_report.json / firing_condition.json consumed read-only.
- NO modification of falsification.py or any dgp/ or hedge/ source.
- NO new firing conditions (the existing 4 stand; the artifact reports null_strip_unavailable verbatim).
- NO verdict flip (gate_passes=FALSE 3/4 stands; the sweep reports the convex-demand SHAPE signal `any_condition_passed`, NOT an overall pass).
- NO fabricated per-cell `recomputed: true` literal — honest evaluated_once/broadcast_to_grid/depends_on_cost_priors:false triple.
- NO `git add -f` — plain add via the 05-00 allowlist.
- NO PDF authoring (Plans 05-02..05-04).
- NO PANEL-02 schema bump (provenance header copied verbatim from gate_report.json).
- NO staging of unrelated untracked files (04.1.1 churn, notes/DRAFT.md left alone).

## Forward pointer

Plan 05-02 (next in Phase 5) consumes `data/fits/ichi/bdaf5c7ba5a2/sensitivity_sweep.json` — the 3×3 qualitative convex-dominance grid the `reports/ichi.qmd` REPORT-03 section presents (heatmap/annotated table), and the MANIFEST.md pins its checksum among the run-dir artifacts.

## Self-Check: PASSED

- Files exist: `report/__init__.py`, `report/sensitivity_sweep.py`, `test_sensitivity_sweep.py`, `sensitivity_sweep.json` — all FOUND.
- Commits exist: `826b13f` (RED), `12bfd33` (GREEN) — both FOUND.
- `git ls-files data/fits/ichi/bdaf5c7ba5a2/sensitivity_sweep.json` == 1; `git check-ignore` rc=1 (NOT ignored).
- All 4 targeted tests GREEN; forbidden-regex rc=1; acceptance one-liners print OK.
