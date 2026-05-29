---
phase: 00-candidate-eligibility-pre-registration
plan: 06
subsystem: infra
tags: [pre-commit, governance, anti-feature-lint, makefile, bash, schema-frozen, review-trail, GOV-03]

# Dependency graph
requires:
  - phase: 00-candidate-eligibility-pre-registration
    provides: "notes/PHASE_0_GATE.md with <SCHEMA_BASELINE_COMMIT> placeholder (Plan 00-02) + protocols/_schema.toml frozen baseline (Plan 00-04)"
provides:
  - ".pre-commit-config.yaml with three local-repo hooks (af-lint, review-trail, schema-frozen)"
  - "Makefile with schema-frozen-check + leak-check + verify-reproducibility targets"
  - "scripts/pre-commit/af_lint.sh covering all 12 anti-features (AF-01..AF-12)"
  - "scripts/pre-commit/review_trail.sh enforcing paired _reality_checker.md + _code_reviewer.md with ## VERDICT"
  - "scripts/pre-commit/schema_frozen.sh wrapping `make schema-frozen-check`"
  - "12 AF fixture directories: 7 active with violating payloads + 5 Phase-3+ deferred README placeholders"
  - "2 auxiliary fixtures: af_review_trail_missing/ + af_schema_frozen_diff/"
  - "tests/fixtures/README.md documenting taxonomy + AF-04 label-drift resolution"
affects: [00-07, 01-fetch-substrate, 02-panel-construction, all-future-phases-via-pre-commit-gate]

# Tech tracking
tech-stack:
  added: [pre-commit, GNU make, bash]
  patterns: ["pre-commit framework local-repo hooks", "anti-feature lint via grep/find/awk", "TOML enum-validity check via python3 tomllib", "review-trail enforcement via awk-parsed verdict line"]

key-files:
  created:
    - .pre-commit-config.yaml
    - Makefile
    - scripts/pre-commit/af_lint.sh
    - scripts/pre-commit/review_trail.sh
    - scripts/pre-commit/schema_frozen.sh
    - tests/fixtures/README.md
    - tests/fixtures/af_01_mock_data/{README.md,fake_panel.parquet}
    - tests/fixtures/af_02_phase_deferred/README.md
    - tests/fixtures/af_03_spec_swap/README.md
    - tests/fixtures/af_04_invalid_mixing_class/{README.md,protocols_fixture.toml}
    - tests/fixtures/af_05_phase_deferred/README.md
    - tests/fixtures/af_06_strip_without_gate/README.md
    - tests/fixtures/af_07_phase_deferred/README.md
    - tests/fixtures/af_08_dashboard_dir/{README.md,dashboard/.gitkeep}
    - tests/fixtures/af_09_phase_deferred/README.md
    - tests/fixtures/af_10_dune_plus/{README.md,.env.violating}
    - tests/fixtures/af_11_phase_deferred/README.md
    - tests/fixtures/af_12_silent_rescope/{README.md,protocols_baseline.toml}
    - tests/fixtures/af_review_trail_missing/PLAN.md
    - tests/fixtures/af_schema_frozen_diff/{README.md,_schema_modified.toml}
  modified: []

key-decisions:
  - "AF-04 label-drift resolution: FEATURES.md 'Hand-tuned bin width for INAR(p)' is the authoritative canonical label; the active af_lint.sh AF-04 check enforces the REQUIREMENTS.md GOV-03 mixing_class enum interpretation because INAR(p) fitting code does not yet exist (Phase-3+ deferred). Both interpretations documented in tests/fixtures/README.md."
  - "AF-10 fixture is detected by the hook by design (C2): the AF-10 grep excludes tests/unit and node_modules but NOT all of tests/, so .env.violating IS picked up. The fixture's mere existence triggers exit-nonzero. Plan 00-07 negative-case test temporarily removes the file to assert PASS, then restores."
  - "AF-12 hook handles initial-commit edge case explicitly (C3): uses `git cat-file -e HEAD:$f` — when file is new (no HEAD copy), logs baseline-establishment and exits 0; when file exists in HEAD, compares row counts and exits 1 if vault rows were added."
  - "AF-08 fixture lives under tests/fixtures/ and the AF-08 find excludes ./tests/* (M13), keeping the fixture dormant on clean state. Activation requires copying the dashboard subdir to the repo root."
  - "Makefile schema-frozen-check defers to no-op (exits 0) while notes/PHASE_0_GATE.md still has the <SCHEMA_BASELINE_COMMIT> placeholder; Plan 00-07 substitutes the actual hash (e9b214d) and the check becomes active."
  - "All 12 AFs have a corresponding fixture directory (af_01..af_12). 7 are active with violating payloads (AF-01, AF-03, AF-04, AF-06, AF-08, AF-10, AF-12); 5 are Phase-3+ deferred placeholders (AF-02, AF-05, AF-07, AF-09, AF-11) documenting why no active check exists yet."
  - ".env.violating fixture force-added via `git add -f` because the project .gitignore excludes `.env.*`. The fixture is required by the plan for AF-10 negative-case testing."

patterns-established:
  - "pre-commit framework with `repo: local` hooks invoking bash scripts under scripts/pre-commit/ — pattern shared with sibling repo abrigo-analytics"
  - "Anti-feature lint as a single bash script covering all AF-NN cases; deferred AFs use `:` no-op placeholders with comment annotation"
  - "TOML enum validation via inline python3 tomllib invocation from bash"
  - "Schema-frozen baseline pattern: hash recorded in a markdown anchor file (notes/PHASE_0_GATE.md); Makefile greps the hash and runs `git diff <baseline>` to detect drift; pre-commit substitution happens in a later plan"
  - "Fixture taxonomy with active-vs-deferred split documented in tests/fixtures/README.md to prevent SC-4(a) audit ambiguity"

requirements-completed: [GOV-03]

# Metrics
duration: 5min
completed: 2026-05-25
---

# Phase 00 Plan 06: Pre-Commit Infrastructure & Anti-Feature Lint Gate Summary

**Three-layer pre-commit hook scaffolding (AF-01..AF-12 lint + 2-way review-trail + schema-frozen) with 12 AF fixtures (7 active + 5 Phase-3+ deferred) and AF-04 FEATURES.md/REQUIREMENTS.md label-drift resolution documented in tests/fixtures/README.md.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-05-25T20:29:31Z
- **Completed:** 2026-05-25T20:35:00Z (approx)
- **Tasks:** 3
- **Files modified:** 27 (3 hook scripts + Makefile + .pre-commit-config.yaml + tests/fixtures/README.md + 12 AF fixture dirs (≥1 README each, plus payloads for active fixtures) + 2 auxiliary fixture dirs)

## Accomplishments

- `.pre-commit-config.yaml` deploys three local-repo hooks via the `pre-commit` Python framework (Plan 00-07 runs `pre-commit install`)
- `Makefile` with phony targets `schema-frozen-check`, `leak-check`, `verify-reproducibility` — schema-frozen-check reads the baseline commit hash from `notes/PHASE_0_GATE.md` via grep, runs `git diff <baseline> -- protocols/_schema.toml`, exits non-zero on any diff. Defers to no-op while the `<SCHEMA_BASELINE_COMMIT>` placeholder is still in PHASE_0_GATE.md.
- `scripts/pre-commit/af_lint.sh` (154 lines) covers all 12 AFs explicitly. 7 active checks (AF-01, AF-03, AF-04, AF-06, AF-08, AF-10, AF-12) with concrete violation conditions; 5 Phase-3+ deferred passthroughs (AF-02, AF-05, AF-07, AF-09, AF-11) documented with `:` no-ops and comment-block annotations.
- `scripts/pre-commit/review_trail.sh` (76 lines) enforces the 2-way review-trail contract: staged commits touching `.planning/**/PLAN.md` or `.planning/ROADMAP.md` require paired `.planning/_reviews/<basename>_reality_checker.md` + `_code_reviewer.md` with `## VERDICT` as first H2 and no BLOCKER. `--allow-revision` flag overrides NEEDS REVISION but never BLOCKER.
- `scripts/pre-commit/schema_frozen.sh` (4 lines) is a thin wrapper invoking `make schema-frozen-check`.
- All 12 AF fixture directories exist (`ls tests/fixtures/ | grep -cE "^af_(0[1-9]|1[0-2])_"` returns 12). Active AFs carry violating payloads designed to be picked up by their respective hook check; deferred AFs carry README placeholders explaining the Phase-N where the active check will be added.
- `tests/fixtures/README.md` resolves the AF-04 FEATURES.md ("Hand-tuned bin width for INAR(p)") vs REQUIREMENTS.md GOV-03 (mixing_class enum) label drift: FEATURES.md is authoritative for label semantics; the *active* check enforces the GOV-03 mixing-class interpretation because INAR(p) fitting code doesn't exist yet; bin-width check Phase-3+ deferred.

## Task Commits

Each task was committed atomically with `(00-06)` scope:

1. **Task 1: Author Makefile with schema-frozen-check + leak-check stub** — `fc653e8` (feat)
2. **Task 2: Author three hook scripts (af_lint.sh + review_trail.sh + schema_frozen.sh) with C2/C3/M13 fixes** — `ec5c492` (feat)
3. **Task 3: Author .pre-commit-config.yaml + 12 AF fixtures (active + phase-deferred) + tests/fixtures/README.md taxonomy + auxiliary fixtures** — `13a7c99` (feat)

## Hook Exit-Code Observations (Phase 0 Clean State)

Verified per the plan's <output> requirement (a):

| Hook | Exit code | Notes |
|------|-----------|-------|
| `bash scripts/pre-commit/af_lint.sh` | **0** when AF-10 fixture is removed; **1** with AF-10 fixture present | The AF-10 .env.violating fixture is detected in-place by design (C2). Plan 00-07 negative-case test #2 removes-asserts-restores. |
| `bash scripts/pre-commit/review_trail.sh` | **0** | No PLAN.md/ROADMAP.md changes staged in clean Phase 0 state. |
| `bash scripts/pre-commit/schema_frozen.sh` | **0** | Defers to no-op because `<SCHEMA_BASELINE_COMMIT>` placeholder still in notes/PHASE_0_GATE.md; Plan 00-07 substitutes the actual hash. |

## AF Fixture Status Inventory (12 AFs)

Per the plan's <output> requirement (b):

| AF | Status | Trigger Mechanism |
|----|--------|-------------------|
| AF-01 | **ACTIVE** | `fake_panel.parquet` copied to `fetch/src/` |
| AF-02 | **PHASE-3+ DEFERRED** | Requires `analysis/src/` model-fitting code with reported p-values |
| AF-03 | **ACTIVE** | Synthetic git-log scenario: PRE_REGISTRATION.md timestamp > first analysis/src/ commit |
| AF-04 | **ACTIVE (REQUIREMENTS.md GOV-03 interpretation)** | `protocols_fixture.toml` with `mixing_class = "this-class-does-not-exist-in-schema-enum"` copied to `protocols/`. FEATURES.md bin-width interpretation Phase-3+ deferred. |
| AF-05 | **PHASE-3+ DEFERRED** | Requires `analysis/src/` with daily/hourly resample calls |
| AF-06 | **ACTIVE** | `analysis/src/.../carr_madan_strip.py` + `data/fits/.../strip.json` without `gate_report.json` |
| AF-07 | **PHASE-3+ DEFERRED** | Requires `fit_report.json` artifact with Hawkes vs NHPP comparison + held-out KS |
| AF-08 | **ACTIVE** | Copy `tests/fixtures/af_08_dashboard_dir/dashboard/` to repo root (M13: tests/ exclusion keeps fixture dormant in-place) |
| AF-09 | **PHASE-3+ DEFERRED** | Requires multiple `data/fits/` artifacts to compare |
| AF-10 | **ACTIVE (in-place)** | `.env.violating` with `DUNE_PLUS_API_KEY=...` is detected by hook by design (C2: AF-10 grep excludes only `tests/unit`, not all of `tests/`) |
| AF-11 | **PHASE-3+ DEFERRED** | Requires `fit_report.json` artifacts |
| AF-12 | **ACTIVE** | After `protocols/test_fixture.toml` is in HEAD, stage a diff adding a NEW `[protocol.vaults.X]` block (C3: initial-commit edge case logs baseline, subsequent additions exit 1) |

## AF-04 Label-Drift Resolution

Per the plan's <output> requirement (c):

- **FEATURES.md AF-04** = "Hand-tuned bin width for INAR(p)" (canonical label).
- **REQUIREMENTS.md GOV-03 AF-04** = retrospective category invention / mixing_class enum violation.

**Resolution:** FEATURES.md is treated as the authoritative source of truth for AF label semantics. However, the *active* `af_lint.sh` AF-04 hook check enforces the REQUIREMENTS.md GOV-03 interpretation (mixing_class enum validity) because the FEATURES.md AF-04 (bin-width tuning) check requires INAR(p) fitting code inside `analysis/src/`, which does not yet exist at Phase 0. The bin-width check is Phase-3+ deferred. Both readings are accepted in hook output messages. When Phase 3+ INAR(p) code exists, a future plan will add a second active AF-04 fixture (`af_04_invalid_bin_width/`) for the FEATURES.md interpretation.

This resolution is documented verbatim in `tests/fixtures/README.md` under the `## AF-04 Label-Drift Resolution (C1 from Phase 0 checker review)` section and is also annotated in the `af_lint.sh` header comment block.

## Files Created/Modified

Per the plan's <output> requirement (d), commit hashes:

- `fc653e8` — Makefile (Task 1)
- `ec5c492` — scripts/pre-commit/{af_lint.sh, review_trail.sh, schema_frozen.sh} (Task 2)
- `13a7c99` — .pre-commit-config.yaml + tests/fixtures/ (Task 3, 22 files in single commit)

## Decisions Made

(See `key-decisions` frontmatter for full list with rationale.)

Key choices:
1. AF-04 label-drift resolved by treating FEATURES.md as canonical for *labels* and REQUIREMENTS.md GOV-03 as authoritative for the *currently-enforceable check*. Both interpretations remain valid; both surface in hook output and fixture documentation.
2. AF-10 fixture intentionally violates in-place — the C2 fix to AF-10 grep makes this the correct behavior. Plan 00-07 negative-case validation works around this by temporarily removing the file.
3. AF-12 initial-commit handling uses `git cat-file -e HEAD:$f` to distinguish baseline-establishment from row addition, preventing fail-open on the first commit of a protocol TOML.
4. `Makefile schema-frozen-check` deliberately defers to a no-op while the PHASE_0_GATE.md placeholder is unsubstituted; Plan 00-07 substitutes `e9b214dcb26d7a6085aa98765a3f8816950495eb` and the check becomes active.
5. `.env.violating` force-added via `git add -f` because `.gitignore` excludes `.env.*` — required by the plan's AF-10 fixture spec.

## Deviations from Plan

None — plan executed exactly as written. All 27 files specified in `files_modified` frontmatter were created (plus one additional README at `tests/fixtures/af_schema_frozen_diff/README.md` for fixture documentation parity, not in `files_modified` but consistent with the taxonomy pattern). The plan's hook scripts, Makefile, and pre-commit config were used verbatim from the inline plan content.

## Issues Encountered

None during execution. One environmental note: PyYAML was not available in the system Python environment (PEP 668 externally-managed); validation of `.pre-commit-config.yaml` YAML structure was performed via a temporary `python3 -m venv` install. This does NOT affect downstream hook execution because `pre-commit install` (Plan 00-07) brings its own YAML parser.

## User Setup Required

None — Plan 00-07 handles the `pre-commit install` step. Hooks are NOT installed in this plan by design.

## Next Phase Readiness

- **Plan 00-07** consumes this plan's output: runs `pre-commit install`, substitutes `e9b214dcb26d7a6085aa98765a3f8816950495eb` into `notes/PHASE_0_GATE.md` `<SCHEMA_BASELINE_COMMIT>` placeholder, and validates each hook via negative-case tests against the 7 active fixtures.
- **Plan 00-05** (sibling Wave-2 plan, parallel to this) authors `protocols/ichi.toml` — once 00-05 lands, the AF-04 hook check (mixing_class enum) operates against a real protocol file in addition to the synthetic fixture.
- Schema-frozen baseline pattern is in place; future schema changes will be rejected at commit time after Plan 00-07 substitutes the hash.

## Self-Check

Verified after writing this SUMMARY:

- File `Makefile` — FOUND (commit `fc653e8`)
- File `.pre-commit-config.yaml` — FOUND (commit `13a7c99`)
- Files `scripts/pre-commit/{af_lint,review_trail,schema_frozen}.sh` — all FOUND and executable (commit `ec5c492`)
- Files `tests/fixtures/README.md` — FOUND with `FEATURES.md is treated as the authoritative` and `Hand-tuned bin width for INAR` strings present
- 12 AF fixture directories — FOUND (`ls tests/fixtures/ | grep -cE "^af_(0[1-9]|1[0-2])_"` = 12)
- Auxiliary fixtures `af_review_trail_missing/PLAN.md` + `af_schema_frozen_diff/_schema_modified.toml` — both FOUND
- No hooks installed (`test ! -f .git/hooks/pre-commit`) — OK
- Commits `fc653e8`, `ec5c492`, `13a7c99` all FOUND in `git log --oneline`

## Self-Check: PASSED

---
*Phase: 00-candidate-eligibility-pre-registration*
*Completed: 2026-05-25*
