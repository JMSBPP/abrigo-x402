# Roadmap Follow-up TODOs

Non-blocking residuals from the 2-way roadmap review (pass-2, both PASS). To be addressed in the relevant phase PLAN.md, not as roadmap revisions.

## From Reality Checker pass-2

### RC-R1 — Phase-3-fires-into-Phase-4 needs Iteration-2 re-run clarification
**Where:** `ROADMAP.md` HEDGE-05 Firing Scope section, Phase 3 entry: "Phase 3 sets a flag in `fit_report.json :: dgp_indistinguishable = true` which Phase 4 reads."
**Issue:** This wiring is clear for Iteration 1 (sequential phase execution). For Iteration 2 (Steer re-running Phases 2–5 via swap-surface), it's underspecified how the Phase-3-equivalent of the re-run sets the flag — is it the same `fit_report.json` path with a different `run_id`, or a separate Steer-namespaced file?
**Resolve at:** Phase 3 PLAN.md (Iteration 1 wiring) + Phase 6 PLAN.md (Iteration 2 re-run wiring); document both paths explicitly.
**Severity:** Low — both Iteration paths should use the same `fit_report.json` schema with `run_id` partition; just needs to be specified.

### RC-R2 — Phase-6 cost-leg-failure code path needs integration test distinct from HEDGE-05 template fixture
**Where:** `ROADMAP.md` Phase 6 SC-2: "if the check fails, `reports/steer_null_result.pdf` ships instead and Phase 6 exits cleanly (no fetch/src or analysis/src edits attempted)."
**Issue:** Phase 4 SC-5 (HEDGE-05 fixtures) test the template *as the template* — synthetic inputs forcing each firing condition. Phase 6's cost-leg-fail path is the *real* fire of firing condition (a) and exercises the full Phase-6 wiring (TOML load, fetch refusal, PDF render, clean exit). These are different test surfaces.
**Resolve at:** Phase 6 PLAN.md — add an integration test `analysis/tests/test_phase6_cost_leg_fail_path.py` that runs the actual Phase 6 entrypoint against a `protocols/steer.toml` with `cost_leg_lower_bound_verified = false` and asserts `reports/steer_null_result.pdf` exists + `git diff fetch/src analysis/src` is empty.
**Severity:** Low-medium — without this, the Phase 6 cost-leg-fail path could ship broken and only be caught by a real fire of the condition.

## From Code Reviewer pass-2

### CR-NEW-1 — REQUIREMENTS.md L153 distribution clarity
**Status:** RESOLVED. Added the clarifying note ("REPRO-04 split across Phase 0 + Phase 6; counted once in the 32, not double-counted") to the Coverage block at 2026-05-25.

### CR-C2 carryover — `notes/README.md` documenting note-naming convention
**Where:** Code Reviewer pass-1 C2 recommended documenting `UPPER_SNAKE` (governance docs) vs `lower_snake` (working notes) convention in `notes/README.md` or PROJECT.md.
**Status:** Convention applied (kebab-case removed; `methodological_refinements.md` snake form locked) but the convention itself is not documented.
**Resolve at:** Phase 0 PLAN.md — author a 1-paragraph `notes/README.md` documenting the convention; or fold into PROJECT.md.
**Severity:** Cosmetic.

---
*Created: 2026-05-25 after pass-2 reviews returned PASS.*
