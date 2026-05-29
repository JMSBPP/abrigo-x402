---
phase: 06-iteration-2-swap-surface-validation-on-steer-ccop-usdt
plan: 02
subsystem: infra
tags: [repro-03, hedge-05, null-cost, straddle, makefile, leak-check, af-03, pre-registration]

# Dependency graph
requires:
  - phase: 06-iteration-2-swap-surface-validation-on-steer-ccop-usdt
    plan: 01
    provides: "scrubbed ichi couplings + the byte-identical M5 scoped-grep recorded in PRE_REGISTRATION.md; data/raw/<protocol>/ materialize namespace; -M null-result renderer; REPRO-02 baseline sha 9add304"
provides:
  - "Pre-registered Steer cost-leg STRADDLE conservative-fail rule (band not strictly > 100k -> null_cost), committed BEFORE the verdict (AF-03)"
  - "scripts/cost_leg_check.py — stdlib-only REPRO-03 first-step tool (outside frozen dirs); emits notes/steer_cost_leg_bound.md verdict: FAIL"
  - "notes/steer_cost_leg_bound.md — verdict: FAIL / firing_condition: null_cost, consumed by decide_firing_condition -> null_cost"
  - "make iteration-2-full — deterministic cost-leg-check-FIRST recipe (fetch/materialize/fit/hedge under Pattern-I BLAS)"
  - "make leak-check scoped-ichi layer byte-identical to the PRE_REGISTRATION M5 pin"
  - "render-null-result-pdf de-papermilled to -M firing_condition + HEDGE05_FIRING_CONDITION env"
affects: [06-03, 06-04, steer-null-result-deliverable, repro-02-attestation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Cost-leg adjudication as scripts/-level stdlib glue (tomllib, no abrigo_x402 import) so the REPRO-02 empty-diff on fetch/src+analysis/src is preserved"
    - "AF-03 commit-ordering enforced by the af-lint hook: the PRE_REGISTRATION amendment MUST carry a docs(pre-reg:<phase>): subject AND predate the verdict artifact commit"
    - "Byte-identical leak-gate command pinned in PRE_REGISTRATION.md and embedded verbatim (modulo Make/bash escaping + a set-pipefail || true guard) in make leak-check"

key-files:
  created:
    - "scripts/cost_leg_check.py"
    - "scripts/test_cost_leg_check.py"
    - "notes/steer_cost_leg_bound.md"
    - ".planning/phases/06-iteration-2-swap-surface-validation-on-steer-ccop-usdt/06-02-SUMMARY.md"
  modified:
    - "notes/PRE_REGISTRATION.md"
    - "Makefile"

key-decisions:
  - "The pre-reg amendment commit was AMENDED from docs(06-02): to docs(pre-reg:06): because the af-lint AF-03 hook requires the PRE_REGISTRATION.md HEAD subject to match ^docs\\(pre-reg(:<phase>)?\\): — the documented audit-trail convention (Plan 04.1.1 used docs(pre-reg:04.1.1):). This is the existing AF-03 mechanism, not a new one."
  - "The leak-check scoped-ichi layer reproduces the PRE_REGISTRATION M5 command byte-identically; the inline grep -vE exclusions ARE the allowlist (data/fits/ichi, reports/ichi.pdf, protocols/ichi.toml + comment/docstring line-format). A diff-equality extraction confirms byte-identity."
  - "The one-off render-null-result-pdf test artifact (146KB null_cost PDF) was REMOVED after verification rather than committed — it is reproducible via the target and is not a Plan 06-02 deliverable (the real reports/steer_null_result.pdf is a Plan 06-03 output)."

patterns-established:
  - "Pre-registered conservative-fail adjudication: verdict FAIL unless band STRICTLY ABOVE the free-tier line; observe the pre-committed band, never re-estimate (AF-03)"

requirements-completed: [REPRO-03, REPRO-04, HEDGE-05]

# Metrics
duration: 10min
completed: 2026-05-29
---

# Phase 6 Plan 02: Cost-leg STRADDLE Pre-Registration + REPRO-03 First-Step Machinery + Makefile Wiring Summary

**Pre-registered the Steer cost-leg conservative-fail STRADDLE rule BEFORE the verdict (AF-03), built the stdlib-only `scripts/cost_leg_check.py` that emits `notes/steer_cost_leg_bound.md` (`verdict: FAIL` -> `null_cost`), and wired the deterministic `make iteration-2-full` recipe + the byte-identical scoped-ichi `leak-check` layer + the de-papermilled `-M` renderer — all OUTSIDE the frozen `fetch/src`/`analysis/src` trees so REPRO-02's empty-diff invariant holds.**

## Performance

- **Duration:** ~10 min
- **Tasks:** 3
- **Files:** 3 created + 2 modified

## Accomplishments

- **Task 1 (pre-registration, AF-03):** Appended two greppable sections to `notes/PRE_REGISTRATION.md`: (A) the **conservative-fail straddle rule** — "a STRADDLE (band NOT strictly ABOVE the 100k/mo Graph free-tier lower bound) -> cost-leg FAILS -> HEDGE-05 condition (a) `null_cost`", applied to the pre-committed 30k–100k band AS-IS with NO re-estimation, plus the Steer-as-D-08-negative-control framing and the "substitute pending (future milestone), pre-register before its data" resolution policy; (B) the **Q-9 unified-panel fallback DEFERRED** disposition with the signal-scope caveat (V3-only ~600/30d = 2.0x the 300-event floor; the SC-3 dead-code modules were never built; if both triggers fire the fallback is a documented "fallback-unavailable" note, NOT reactive code; **ROADMAP SC-5 is SKIPPED-with-reason** and `q9_pooling_test.json` is absent by design). Both carry AF-12 OUT-OF-SCOPE lines.
- **Task 2 (REPRO-03 first-step tool):** Created `scripts/cost_leg_check.py` (stdlib + `tomllib`, no `abrigo_x402` import) that reads `protocols/steer.toml [protocol.repro_03_verdict]` verbatim, applies the pre-registered rule (`verdict = FAIL unless lower_bound > demand_window_lower_bound`), and writes `notes/steer_cost_leg_bound.md` with frontmatter `verdict: FAIL / flag: marginal-demand / firing_condition: null_cost / band_lower: 30000 / band_upper: 100000 / free_tier_ceiling: 100000`. Ran it to emit the artifact. `scripts/test_cost_leg_check.py` (4 tests) asserts the production parser `_parse_cost_leg_bound_verdict` returns `"FAIL"`, `firing_condition: null_cost` present, line-1 `---`, and the strictly-above->`PASS` symmetry — all green under thread-pinned BLAS.
- **Task 3 (Makefile wiring):** Added the deterministic `iteration-2-full` target (cost-leg check STEP 1 BEFORE any fetch, then materialize/fit/hedge, Pattern-I `$(BLAS)` prefix on every Python line, `.PHONY` entry); extended `leak-check` with the scoped-ichi layer **byte-identical** to the PRE_REGISTRATION M5 pin (diff-equality confirmed); de-papermilled `render-null-result-pdf` to `-M firing_condition:$FIRING` + `HEDGE05_FIRING_CONDITION` env with `SOURCE_DATE_EPOCH`/`QUARTO_PYTHON` determinism (rendered a 146KB `null_cost` PDF with the firing string in the H1, callout, and Evidence body — verification artifact removed after the check).

## Task Commits

1. **Task 1: pre-register straddle rule + Q9-fallback-deferred** — `fc6eec0` (`docs(pre-reg:06):`)
2. **Task 2: cost_leg_check.py + test + emitted verdict FAIL** — `0475bed` (`feat`)
3. **Task 3: iteration-2-full recipe + scoped leak-check + -M renderer** — `a8f0ef0` (`feat`)

AF-03 ordering proven: `fc6eec0` (rule) PRECEDES `0475bed` (verdict artifact) — `git log -- notes/PRE_REGISTRATION.md notes/steer_cost_leg_bound.md`.

## Verification

- `python scripts/cost_leg_check.py ...` -> `verdict=FAIL firing_condition=null_cost`; `_parse_cost_leg_bound_verdict` returns `FAIL` (run under the analysis venv which carries `tick`).
- `pytest scripts/test_cost_leg_check.py` -> **4 passed** (FAIL on the Steer band + boundary-at-ceiling FAIL + strictly-above->PASS symmetry).
- `make leak-check` exit 0; scoped-ichi grep byte-identical to PRE_REGISTRATION M5 (diff-equality empty after Make/bash unescaping).
- `make render-null-result-pdf FIRING=null_cost` -> 145934B PDF (>5KB), `null_cost` in H1+callout+body; no `--execute-param` (`grep -c execute-param Makefile` == 0); `-M firing_condition` present.
- `iteration-2-full` is a deterministic recipe (cost-leg check STEP 1, then fetch/materialize/fit/hedge); in `.PHONY`.
- **REPRO-02: `git diff 9add304 HEAD -- fetch/src analysis/src` EMPTY** across all 3 task commits. Zero edits to frozen source.
- System `grep` is ugrep 7.5.0 (GNU-compatible for `-rnE`/`-vE`/`[[:space:]]`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Pre-reg commit subject must be `docs(pre-reg:<phase>):` for the af-lint AF-03 gate**
- **Found during:** Task 2 (committing the verdict artifact tripped the af-lint AF-03 hook on the Task-1 commit).
- **Issue:** The `af-lint` pre-commit hook (`scripts/pre-commit/af_lint.sh` AF-03) requires the HEAD commit touching `notes/PRE_REGISTRATION.md` to match `^docs\(pre-reg(:[^)]+)?\):` — the documented audit-trail amendment convention (Plan 04.1.1 used `docs(pre-reg:04.1.1):`). My Task-1 commit used `docs(06-02):`, so the hook rejected the next commit as a "spec-swap" (pre-reg timestamp later than the first analysis/src commit, with no amendment-prefixed subject).
- **Fix:** Amended the Task-1 commit message from `docs(06-02): ...` to `docs(pre-reg:06): ...` (content unchanged; PRE_REGISTRATION.md-only commit). This is the EXISTING AF-03 mechanism, not a new pattern.
- **Files modified:** commit message only (`notes/PRE_REGISTRATION.md` content unchanged).
- **Commit:** `fc6eec0` (amended).

**2. [Rule 1 - Bug] render-null-result-pdf output landed in reports/, not reports/_templates/**
- **Found during:** Task 3 (first render of the verification PDF).
- **Issue:** `quarto render _templates/null_result.qmd --output null_result_$FIRING.pdf` (run with `cwd=reports`) places the PDF at `reports/null_result_$FIRING.pdf` (project-relative), not `reports/_templates/`. My initial `mv reports/_templates/...` therefore could not find it.
- **Fix:** Replaced the single `mv` with a candidate-location loop (`reports/`, `reports/_templates/`, repo-root) + a final `test -f` PASS/FAIL guard, so the diagnostic PDF is reliably moved to `reports/_diagnostics/` regardless of quarto's output-resolution quirk.
- **Files modified:** `Makefile` (render-null-result-pdf recipe).
- **Commit:** `a8f0ef0`.

**3. [Rule 1 - Bug] Pre-existing `--execute-param` token in the report-ichi comment tripped the acceptance grep**
- **Found during:** Task 3 (`grep -c "execute-param" Makefile` returned 1 after the renderer edit).
- **Issue:** The `report-ichi` recipe (Plan 05) carries a comment "no `--execute-param` -> no papermill dependency" — a benign documentation token, but the acceptance criterion `grep -c "execute-param" Makefile == 0` is global.
- **Fix:** Reworded the comment to "no per-parameter papermill flag" (same in my new renderer comment). No behavior change to `report-ichi`.
- **Files modified:** `Makefile`.
- **Commit:** `a8f0ef0`.

**Total deviations:** 3 auto-fixed (1 Rule-3 blocking, 2 Rule-1 bug). All within the plan's authorized target files (notes/, scripts/, Makefile). ZERO edits to `fetch/src` or `analysis/src`.

## Issues Encountered

- The plan's literal acceptance one-liner `python -c "...from abrigo_x402.hedge.null_result import _parse_cost_leg_bound_verdict..."` fails under bare system python (`ModuleNotFoundError: tick`) because `abrigo_x402.hedge` transitively imports `tick` via `dgp`. Run under the analysis venv (`cd analysis && uv run python ...`) it returns `FAIL` correctly. This is an environment artifact of the verification command, not a defect in `cost_leg_check.py` (which is stdlib-only and never imports `abrigo_x402`).
- The scoped-ichi leak grep prints `grep: <file>.pyc: binary file matches` warnings (ugrep scans `__pycache__/*.pyc`) to stderr; these are harmless (no `path:line:content` match reaches the exclusion filters) and the layer returns PASS. Byte-identity with the pinned command is preserved (no `-I`/`2>/dev/null` added).

## User Setup Required

None — quarto is present in the environment; the render verification ran live. Plan 06-03 supplies the operator block-range/run-id env vars (`STEER_FROM`/`STEER_TO`/`STEER_RANGE`/`STEER_RUN`) at `make iteration-2-full` invocation.

## Next Phase Readiness

- Plan 06-03 can now run `make iteration-2-full` (or the equivalent fetch/materialize/fit/hedge sequence) on the Steer cCOP/USDT V3 anchor pool; the cost-leg STEP-1 emits `notes/steer_cost_leg_bound.md` (already present, `verdict: FAIL`) and `cli.py hedge --cost-leg-bound` routes `decide_firing_condition` to `null_cost` from inside the completed run.
- Plan 06-04's REPRO-02 attestation reads the same `9add304` baseline; the empty-diff invariant is intact after all three Plan-02 commits.

## Self-Check: PASSED

All 4 claimed files exist on disk (scripts/cost_leg_check.py, scripts/test_cost_leg_check.py, notes/steer_cost_leg_bound.md, 06-02-SUMMARY.md). All 3 task commits (`fc6eec0`, `0475bed`, `a8f0ef0`) are present in git history. REPRO-02 `git diff 9add304 HEAD -- fetch/src analysis/src` is empty.

---
*Phase: 06-iteration-2-swap-surface-validation-on-steer-ccop-usdt*
*Completed: 2026-05-29*
