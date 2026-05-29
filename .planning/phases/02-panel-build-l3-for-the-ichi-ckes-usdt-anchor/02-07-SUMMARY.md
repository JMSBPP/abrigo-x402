---
phase: 02-panel-build-l3-for-the-ichi-ckes-usdt-anchor
plan: 07
subsystem: provenance
tags: [polars, parquet, panel-02, metadata, lint, makefile]

requires:
  - phase: 02-panel-build-l3-for-the-ichi-ckes-usdt-anchor
    provides: "Plan 02-00 scaffold of analysis/src/abrigo_x402/provenance.py with REQUIRED_KEYS tuple + git_commit_short + NotImplementedError-bodied with_header/assert_has_header; Phase 1 Makefile lint-artifacts placeholder target"
provides:
  - "with_header(df, path, **meta) — coerces values to str, validates all 6 PANEL-02 REQUIRED_KEYS present BEFORE write, embeds via polars 1.41 native df.write_parquet(path, metadata=dict[str,str])"
  - "assert_has_header(path) — reads via pl.read_parquet_metadata, raises AssertionError listing missing PANEL-02 keys"
  - "scripts/lint_artifacts.py — standalone linter usable from CI / Makefile / direct invocation; per-file missing-keys diagnostic"
  - "make lint-artifacts — SKIP-on-absent panels dir + ENFORCE-on-present invokes scripts/lint_artifacts.py against data/raw/ichi/panels/*.parquet"
affects:
  - "Plan 02-08 (panel e2e) — first plan to produce data/raw/ichi/panels/*.parquet; exercises Makefile ENFORCE branch end-to-end"
  - "Plan 02-09 (fit_report scaffold) — uses with_header for any persisted scaffolds"
  - "Phase 5 reproducibility manifest — every Parquet output carries the six metadata keys; manifest verifies header presence as part of REPRO-04"

tech-stack:
  added: []  # uses polars 1.41.0 + Python stdlib only; no new deps
  patterns:
    - "polars 1.41 native Parquet-footer metadata API (write_parquet metadata={} + read_parquet_metadata) — supersedes any JSON-sidecar approach"
    - "Validate-before-write: missing-key check raises ValueError BEFORE df.write_parquet so the filesystem never holds header-less artifacts"
    - "Makefile SKIP/ENFORCE dual-branch lint target gated by directory presence — enables pre-panel-build no-op + post-panel-build hard fail"
    - "Standalone linter script (no abrigo_x402 import) so it runs from repo-root via `uv run python scripts/lint_artifacts.py`"

key-files:
  created:
    - "scripts/lint_artifacts.py"
    - "analysis/tests/test_provenance.py"
  modified:
    - "analysis/src/abrigo_x402/provenance.py"
    - "Makefile"

key-decisions:
  - "Removed `import pyarrow.parquet` probe from test file: polars 1.41 ships the parquet writer/reader natively and the analysis/ uv env does not require an explicit pyarrow install. The probe added a spurious ImportError gate that did not reflect runtime needs."
  - "Linter is a standalone script (no `from abrigo_x402.provenance import REQUIRED_KEYS`) so it runs from repo-root without sys.path configuration; REQUIRED_KEYS is duplicated as a 6-key tuple inside the script. Single-source-of-truth deferred to a future refactor if the keys ever diverge."
  - "Validation raises BEFORE write (filesystem-clean invariant): callers passing an incomplete meta dict will never leave a header-less Parquet artifact on disk."
  - "I5 limitation acknowledged in commit message: `make lint-artifacts` exit-0 in this plan only proves the SKIP branch because data/raw/ichi/panels/ does not exist pre-Plan-02-08. The synthetic positive/negative fixtures under /tmp prove the ENFORCE branch in isolation; full Makefile-invokes-linter-on-real-panel is Plan 02-08 Task 2 territory."

patterns-established:
  - "polars 1.41 native Parquet metadata: df.write_parquet(path, metadata={'k':'v',...}) round-trips byte-stably through pl.read_parquet_metadata(path) -> dict[str,str]"
  - "All metadata values coerced to str via `{k: str(v) for k, v in meta.items()}` since polars metadata is dict[str,str]"
  - "Makefile lint-target dual-branch with `if [ -d <dir> ]; then ENFORCE; else SKIP; fi` — pattern reusable for Phase 3+ panel-derived artifact gates"

requirements-completed: [PANEL-02]

duration: 3min
completed: 2026-05-26
---

# Phase 02 Plan 07: PANEL-02 Provenance + Lint Gate Summary

**`with_header` + `assert_has_header` over polars 1.41 native Parquet-footer metadata, plus a Makefile-invocable `scripts/lint_artifacts.py` that enforces the six PANEL-02 required keys on every panel artifact.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-05-26T17:24:36Z
- **Completed:** 2026-05-26T17:27:30Z
- **Tasks:** 2
- **Files modified:** 4 (1 created Py script, 1 created Py test, 1 modified Py module, 1 modified Makefile)

## Accomplishments

- PANEL-02 metadata-header injection wired via polars 1.41 native API (no JSON sidecar)
- 6/6 provenance tests passing (round-trip, missing-key pre-write rejection, assert-has-header positive + negative, str coercion, git_commit_short hex contract)
- Standalone Python linter (`scripts/lint_artifacts.py`) with per-file missing-keys diagnostic
- Makefile `lint-artifacts` extended from Phase 1 echo-stub to dual-branch SKIP/ENFORCE gate
- Synthetic positive/negative linter validation confirms ENFORCE-branch behaviour against `/tmp/lint_test/{good,bad}.parquet`

## Task Commits

1. **Task 1 RED — failing tests for provenance** — `3a4dfb1` (test)
2. **Task 1 GREEN — implement with_header + assert_has_header** — `463d7fa` (feat)
3. **Task 2 — lint_artifacts.py + Makefile target** — `f83ca9b` (feat)

_Note: Task 1 followed TDD with RED + GREEN commits. No refactor commit needed — implementation passed cleanly on first GREEN._

## Files Created/Modified

- `analysis/src/abrigo_x402/provenance.py` — implemented `with_header` + `assert_has_header`; `REQUIRED_KEYS` + `git_commit_short` unchanged from Plan 02-00 skeleton
- `analysis/tests/test_provenance.py` — created; 6 tests covering round-trip, missing-key, assert pass/fail, str coercion, git_commit hex
- `scripts/lint_artifacts.py` — created; standalone executable Python linter (chmod +x)
- `Makefile` — `lint-artifacts` target replaced from Phase 1 echo-stub with SKIP-on-absent + ENFORCE-via-uv-run-script dual branch

## Decisions Made

- **Drop pyarrow probe import in test file:** Plan body included `import pyarrow.parquet as _pq` as a sanity probe. polars 1.41 ships parquet I/O natively and the analysis/ uv env doesn't carry an explicit pyarrow pin; the probe blocked test collection with ImportError. Removed under Rule 3 (blocking issue caused directly by this task). The polars-native API does the work; no external arrow dependency is needed for PANEL-02.
- **Linter standalone (no abrigo_x402 import):** Keeps the script invocable from repo-root via `uv run python scripts/lint_artifacts.py ...` without sys.path tinkering. `REQUIRED_KEYS` is duplicated as a 6-element tuple inside the script. If the keys ever change, both definitions update together (low-risk because of the test in `test_provenance.py`).
- **Validate-before-write invariant:** `with_header` raises `ValueError` BEFORE `df.write_parquet` so the filesystem never holds an artifact with an incomplete header. Callers can't end up with a partially-written half-compliant file.
- **Makefile SKIP/ENFORCE dual branch:** `lint-artifacts` exits 0 with a "skipping" message pre-Plan-02-08 (no `data/raw/ichi/panels/`) and enforces the lint post-02-08. This lets the target be wired into CI / pre-commit immediately without breaking on the current empty state.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Dropped unnecessary `import pyarrow.parquet` probe from test file**
- **Found during:** Task 1 RED phase (initial pytest run)
- **Issue:** Plan body's test code included `import pyarrow.parquet as _pq  # noqa: F401  (probe pyarrow available)` as a sanity check. The analysis/ uv environment doesn't have pyarrow installed (transitively or directly) — polars 1.41 ships parquet support natively. Test collection failed with `ModuleNotFoundError: No module named 'pyarrow'` before any test could run.
- **Fix:** Removed the import. polars 1.41 native `write_parquet(metadata=...)` and `read_parquet_metadata(...)` do not require user-visible pyarrow; the runtime probe in the Task 1 acceptance grid confirms this.
- **Files modified:** `analysis/tests/test_provenance.py`
- **Verification:** All 6 tests pass; the runtime probe `df.write_parquet('/tmp/probe.parquet', metadata={'k':'v'}); md=pl.read_parquet_metadata('/tmp/probe.parquet'); assert md['k']=='v'` prints `runtime probe ok`.
- **Committed in:** `3a4dfb1` (Task 1 RED commit — fix folded into the same commit since it was a single-line edit before tests could even fail meaningfully).

---

**Total deviations:** 1 auto-fixed (1 blocking).
**Impact on plan:** Unblocking only. Removed a spurious dependency probe that didn't reflect runtime needs. No scope creep; all 6 PANEL-02 keys, validation semantics, and round-trip behaviour matched the plan body verbatim.

## Issues Encountered

- None beyond the pyarrow probe deviation above.

## User Setup Required

None — no external service configuration required for this plan. PANEL-02 is pure Python + polars + Makefile wiring; runs offline.

## Next Phase Readiness

- **Plan 02-08 (panel e2e) unblocked:** Imports `with_header` from `abrigo_x402.provenance` to write the first `data/raw/ichi/panels/*.parquet` with the full 6-key header. The Makefile `lint-artifacts` ENFORCE branch activates as soon as that directory exists and will hard-fail any artifact missing keys.
- **Plan 02-09 (fit_report scaffold) unblocked:** Same `with_header` helper applies to any persisted scaffold output.
- **Phase 5 REPRO-04 manifest:** Every Phase 2 panel + downstream artifact carries the metadata header in its Parquet footer; the reproducibility-manifest job can verify presence via `pl.read_parquet_metadata` against each tracked artifact.

## Self-Check: PASSED

- `analysis/src/abrigo_x402/provenance.py` exists with `write_parquet.*metadata=` + `REQUIRED_KEYS` grep hits (FOUND).
- `analysis/tests/test_provenance.py` exists; 6/6 pass via `cd analysis && uv run pytest tests/test_provenance.py -x -q` (FOUND).
- `scripts/lint_artifacts.py` exists + executable; `REQUIRED_KEYS` grep hits (FOUND).
- `Makefile` `lint-artifacts` target invokes `scripts/lint_artifacts.py` via `uv run` (FOUND).
- `make lint-artifacts` exits 0 pre-panel-build SKIP branch (CONFIRMED).
- Synthetic positive (good.parquet, all 6 keys) → exit 0; synthetic negative (bad.parquet, no metadata) → exit 1 (CONFIRMED).
- Commits exist: `3a4dfb1` (RED), `463d7fa` (GREEN), `f83ca9b` (Task 2) (FOUND in `git log --oneline`).

---
*Phase: 02-panel-build-l3-for-the-ichi-ckes-usdt-anchor*
*Completed: 2026-05-26*
