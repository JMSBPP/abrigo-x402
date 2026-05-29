# Reality-Checker RE-REVIEW — 05-01-PLAN.md (REPORT-03 qualitative sensitivity sweep)

**Reviewer:** Reality Checker (Reviewer 1)
**Date:** 2026-05-29 (re-review of revised plan)
**Artifact:** `.planning/phases/05-reporting-iteration-1-pdf-deliverable-l7/05-01-PLAN.md`

## VERDICT

PASS

Both prior MAJORs are CLOSED. The `recomputed: true` mislabel is replaced with the honest `evaluated_once / broadcast_to_grid / depends_on_cost_priors:false` triple, AND — crucially — Test 2 now ties each cell's four booleans to the gate's OWN evidence-dict values from `gate_report.json` and asserts no `recomputed` literal survives, so a constant-copy-with-fake-flag would fail the test. The no-cost-model grep guard is now a single byte-identical canonical regex shared with 05-00, with the legitimate pre-reg grid labels explicitly excluded from the forbidden set. Both MINORs addressed.

---

## Prior findings — confirm-closed

### PRIOR MAJOR-1 (`recomputed: true` labels work not done) — CLOSED
- The field is renamed to the honest triple `evaluated_once: true, broadcast_to_grid: true, depends_on_cost_priors: false` (truths line 20; behavior line 109; action step 3 line 121; success line 156). The plan repeatedly forbids attaching `recomputed: true` to a constant copy.
- The dishonest-label gap is closed by a REAL test, not just a rename: Test 2 (line 109) asserts `cell["conditions"]["hawkes_self_excitation"] == gate_report["hawkes_self_excitation"]["passed"]` (and the other three), i.e. the cell booleans must equal the gate source — a hardcoded inline copy that drifted from the gate would fail. It also asserts `all('recomputed' not in c ...)` (acceptance line 137).
- LIVE-VERIFIED the gate source values exist and are true: `gate_report.json` has `vol_of_vol_gt_zero/positive_skew_fat_tails/hawkes_self_excitation/usdt_depeg_basis_jump .passed=true`, `any_condition_passed=true`; `firing_condition.json` = `null_strip_unavailable`. The honest invariance result (`conditions_cost_prior_invariant=true`) is the real on-disk fact.

### PRIOR MAJOR-2 (no-cost-model grep under-specified / self-tripping) — CLOSED
- A SINGLE canonical forbidden regex is locked verbatim and declared byte-identical to 05-00 (line 85 / 111 / 138): `grep -rIE 'kappa|κ|dominance_delta|def +cost_leg|cost_of_convexity' analysis/src/` must return ZERO hits.
- `rate_per_event` / `USD_per_query` are EXPLICITLY removed from the forbidden set (lines 87, 111) — they are legitimate pre-reg grid labels written as `GRID_*` constants, not a cost model. So the guard no longer self-trips on the plan's own grid constants.
- LIVE-VERIFIED today: `grep -rIE 'kappa|κ|dominance_delta|def +cost_leg|cost_of_convexity' analysis/src/` returns ZERO hits (the guard passes against the current tree, as it must at RED-baseline).
- The plan instructs defining the regex ONCE as a module-level constant reused in both the test and the acceptance one-liner so they cannot diverge (line 111).

### PRIOR MINOR-1 (CWD-fragile relative path) — CLOSED
Test resolves the run dir via `Path(__file__).resolve().parents[2] / "data/fits/ichi/bdaf5c7ba5a2"` (line 114), CWD-independent.

### PRIOR MINOR-2 (`git add -f` misleading) — CLOSED
Plain `git add` (no `-f`), explicitly because the 05-00 allowlist re-includes `ichi/bdaf5c7ba5a2/*.json` (action line 127; acceptance line 139 also asserts the artifact is NOT ignored). LIVE-VERIFIED the nested allowlist re-includes `*.json` under that run dir.

### PRIOR MINOR-3 (`all_cells_convex_dominant` overstates) — CLOSED
Renamed to `all_cells_any_condition_passed` (mirrors the artifact field `any_condition_passed`), with an explicit note (line 89) that it is the convex-demand SHAPE signal, NOT the overall gate verdict, and must never be juxtaposed with `gate_passes` as a pass.

---

## Foundation re-confirmed (no regression)
- Pre-reg grid intact: LIVE `notes/PRE_REGISTRATION.md` line 28 `rate_per_event (1,5,10)`, line 29 `USD_per_query ($2.5e-6,$5e-6,$7.5e-6)`, line 162 locked-paragraph — matches the plan byte-for-byte; rate is `{1,5,10}` NOT `{2.5,5,7.5}` (explicitly guarded, line 79/117). ✓
- The 4 conditions + firing_condition exist on disk with the stated values. ✓
- No κ / no cost-leg / no dollar-Δ smuggled; honest invariance framing preserved. ✓
- Specialist (Analytics Reporter) named with a why. ✓

---

## NEW findings
None. The honest-broadcast labeling + the gate-sourced Test-2 assertion is the correct closure of the label-vs-reality gap.

---

## Cross-check summary
- `recomputed:true` honesty: CLOSED — renamed + test ties booleans to gate source + asserts no `recomputed` literal. (LIVE-verified source values)
- No-cost-model guard: CLOSED — single canonical regex, grid labels excluded, ZERO hits live. (closed)
- Grid matches the lock: YES, verified. (clean)
- Specialist: present. (clean)

**BLOCKER: 0 · MAJOR: 0 (2 prior CLOSED) · MINOR: 0 NEW**
