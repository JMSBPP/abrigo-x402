---
phase: 06-iteration-2-swap-surface-validation-on-steer-ccop-usdt
plan: 01
subsystem: infra
tags: [quarto, pandoc, pdflatex, polars, protocol-spec, leak-gate, repro-02, hedge-05]

# Dependency graph
requires:
  - phase: 04-cross-leg-dependence-l5-falsification-carr-madan-strip-l6
    provides: "generic HEDGE-05 render_null_result_pdf scaffold + null_result.qmd/_evidence_branches.qmd templates + lint_artifacts.py column guard"
  - phase: 05-reporting-iteration-1-pdf-deliverable-l7
    provides: "proven pdf-engine:pdflatex + QUARTO_PYTHON + cd-into-dir render pattern; FOLLOWUP bug doc"
provides:
  - "First production-usable generic null-result PDF renderer (papermill-free, repo-root anchored, firing string in PDF body not just title)"
  - "Protocol-derived materialize namespace (data/raw/<protocol>/ from spec.protocol.name)"
  - "Generalized data/raw/<protocol>/ panel column-lint guard (Steer panels linted)"
  - "AF-12 PRE_REGISTRATION note re-scoping REPRO-01 to SC-5 intent + exact scoped-grep command"
  - "_artifacts/repro_02_baseline_sha.txt — the REPRO-02 empty-diff base sha for Plan 06-04"
affects: [06-02, 06-03, 06-04, steer-cost-leg, repro-02-attestation, null-result-deliverable]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Generic null-result renderer: -M top-level pandoc metadata (H1 shortcode) + HEDGE05_FIRING_CONDITION env var (executable evidence chunks) — dual channel because {{< meta >}} shortcodes do NOT expand inside {python} cell source"
    - "Render from template dir with bare relative --output + shutil.move to dest (avoids quarto absolute --output-dir safeMoveSync bug); QUARTO_PYTHON=sys.executable"
    - "Baseline-maintenance commits land BEFORE the REPRO-02 empty-diff window; the post-Plan-01 HEAD sha is pinned to a file as the diff base"

key-files:
  created:
    - ".planning/phases/06-iteration-2-swap-surface-validation-on-steer-ccop-usdt/_artifacts/repro_02_baseline_sha.txt"
  modified:
    - "analysis/src/abrigo_x402/hedge/null_result.py"
    - "reports/_templates/null_result.qmd"
    - "reports/_templates/_evidence_branches.qmd"
    - "analysis/tests/test_null_result_template.py"
    - "analysis/src/abrigo_x402/cli.py"
    - "scripts/lint_artifacts.py"
    - "notes/PRE_REGISTRATION.md"

key-decisions:
  - "Firing condition reaches the PDF body via an env var (HEDGE05_FIRING_CONDITION), not the meta shortcode, because quarto does not expand {{< meta >}} inside executable {python} cell source — the H1 uses the shortcode, both carry the same value"
  - "Pin pdf-engine:pdflatex in null_result.qmd (matching ichi.qmd) so the pdfTeX-only \\pdfinfo HEDGE05 marker survives TeX Live 2026's default LuaHBTeX"
  - "Scoped-grep M5 command targets ichi LITERALS (quoted/path) in code, excluding comments/docstrings + the CLI-overridable defaults (data/fits/ichi, reports/ichi.pdf, protocols/ichi.toml) — returns 0 hits post-scrub"
  - "REPRO-02 baseline sha pins the AF-12 note commit (9add304); the final artifact + docs commits touch no fetch/src or analysis/src, so the empty-diff holds from the pinned HEAD forward"

patterns-established:
  - "Dual-channel firing-condition injection (meta shortcode for markdown + env var for code chunks)"
  - "Generic protocol-namespacing derived from spec.protocol.name (materialize) mirrors the fetch parquet-writer.ts pattern"

requirements-completed: [REPRO-01, REPRO-02]

# Metrics
duration: 55min
completed: 2026-05-29
---

# Phase 6 Plan 01: Pre-Iteration-2 Baseline-Maintenance Edits Summary

**De-papermilled the generic HEDGE-05 null-result renderer (firing string now in the PDF body), protocol-derived the materialize namespace + generalized the panel column-lint guard, and pinned the REPRO-02 empty-diff baseline sha behind an explicit AF-12 REPRO-01 re-scope note.**

## Performance

- **Duration:** 55 min
- **Started:** 2026-05-29T21:19:58Z
- **Completed:** 2026-05-29T22:15:12Z
- **Tasks:** 3
- **Files modified:** 7 (+1 created)

## Accomplishments
- `render_null_result_pdf` is production-usable for the first time: no papermill (`-P` → `-M`), repo-root anchored, renders a 146KB null_cost PDF with the firing string in the H1 title, the callout, AND the `## Evidence: ...(null_cost)` body section. The un-skipped dual-signature test runs and passes.
- All THREE template interpolation points converted off the `params.` namespace: H1 reads `{{< meta firing_condition >}}`; the two `{python}` evidence chunks read `os.environ["HEDGE05_FIRING_CONDITION"]` (closing the B1 blank-body trap).
- `materialize` derives `data/raw/<protocol>/<pool>/` from `spec.protocol.name`; a Steer run writes `data/raw/steer/` with no further edit. The `lint_artifacts.py` column-guard (M1) generalized to any `data/raw/<protocol>/` panel; `ICHI_PANEL_REQUIRED_COLUMNS` → `LP_AGGREGATOR_PANEL_REQUIRED_COLUMNS`.
- AF-12 note in `PRE_REGISTRATION.md` re-scopes REPRO-01's literal all-hits grep to its SC-5 algorithmic-leak intent + a scoped grep (recorded BEFORE any leak-gate verdict, pure addition).
- `_artifacts/repro_02_baseline_sha.txt` pins `9add304…` as the single-line REPRO-02 empty-diff base for Plan 06-04.

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix the generic null-result renderer (-M + repo-root + all three template points)** — `0200bac` (fix)
2. **Task 2: Protocol-derive materialize namespace + generalize panel column-lint guard + scrub ichi couplings** — `7d15ff6` (fix)
3. **Task 3a: AF-12 PRE_REGISTRATION note re-scoping REPRO-01 to SC-5** — `9add304` (docs)
4. **Task 3b: Pin REPRO-02 baseline sha** — `1ecceac` (chore)

_Note: Task 3 is two commits by design — the note commits first so the pinned sha is the post-note HEAD; both are the last Plan-01 commits._

## Files Created/Modified
- `analysis/src/abrigo_x402/hedge/null_result.py` — REPO_ROOT=parents[4]; `-M` + `HEDGE05_FIRING_CONDITION` env var; render from template dir + `shutil.move` to dest; QUARTO_PYTHON pinned; generic default output path; scrubbed all ichi/steer literals.
- `reports/_templates/null_result.qmd` — H1 `{{< meta firing_condition >}}`; load-substrate chunk reads env (`echo:false`); `pdf-engine: pdflatex`; stale `params$firing_condition` comments removed.
- `reports/_templates/_evidence_branches.qmd` — evidence chunk reads `os.environ["HEDGE05_FIRING_CONDITION"]`; stale comment scrubbed.
- `analysis/tests/test_null_result_template.py` — dual-signature marker check queries `pdfinfo -custom` (this poppler build only surfaces the custom field there).
- `analysis/src/abrigo_x402/cli.py` — materialize namespace from `spec.protocol.name`; docstring `<protocol>`.
- `scripts/lint_artifacts.py` — `re` import; frozenset + function rename; M1 guard `re.search(r"data/raw/[^/]+/", str(p))`.
- `notes/PRE_REGISTRATION.md` — append-only AF-12 Phase-6 REPRO-01 re-scope section.
- `_artifacts/repro_02_baseline_sha.txt` — created; single 40-char sha `9add304fda4f7946e1720588a83acb52e413f424`.

## ichi-coupling scrub triage

| Hit | Location | Disposition |
|---|---|---|
| `data/raw/ichi/<pool>` namespace | cli.py:67 | **Scrubbed** → `data/raw/<protocol>/` from `spec.protocol.name` |
| materialize docstring path | cli.py:15 | **Scrubbed** → `<protocol>` |
| `ICHI_PANEL_REQUIRED_COLUMNS` frozenset | lint_artifacts.py | **Renamed** → `LP_AGGREGATOR_PANEL_REQUIRED_COLUMNS` |
| `lint_ichi_panel_columns` fn | lint_artifacts.py | **Renamed** → `lint_panel_columns` |
| `"data/raw/ichi" in str(p)` column guard | lint_artifacts.py:344 | **Generalized** → `re.search(r"data/raw/[^/]+/", str(p))` (M1) |
| default `reports/ichi.pdf` output_path | null_result.py | **Scrubbed** → `reports/null_result.pdf` (generic) |
| `data/fits/ichi/<run_id>` docstring | null_result.py | **Scrubbed** → `data/fits/<protocol>/` |
| `--protocol-toml default protocols/ichi.toml` | cli.py:201 | **Left** (CLI-overridable; protocols/ spec layer; reconciled by scoped grep) |
| `data/fits/ichi` / `reports/ichi.pdf` hedge defaults | cli.py hedge | **Left** (CLI-overridable defaults; reconciled by scoped grep) |
| ABI/vault docstrings (decoders.py, revenue_leg.py, dgp/orchestrator.py, __init__.py, fetch state-snap.ts) | various | **Left as iter-1 example** (comments/docstrings; reconciled by scoped grep) |
| `ichi_vault_abi.json` fixture reference | decoders.py | **Left** (module-load fixture; SC-5 lint does not flag fixture filenames; reconciled by scoped grep comment-exclusion) |
| `cmd !== 'ichi' && cmd !== 'steer'` CLI dispatch | fetch/src/cli.ts | **Left** (user-facing subcommand arg, NOT a `config.name ==` algorithmic branch) |

## Exact scoped-grep command (M5 — byte-identical, recorded in PRE_REGISTRATION.md)

```
grep -rnE '"ichi"|/ichi/|raw/ichi|fits/ichi' analysis/src fetch/src \
  | grep -vE 'data/fits/ichi|reports/ichi\.pdf|protocols/ichi\.toml' \
  | grep -vE ':[0-9]+:[[:space:]]*(#|//|\*|/\*)'
```

Returns 0 lines on HEAD. System `grep` is ugrep 7.5.0 (GNU-compatible for these flags).

## Verification

- Full analysis suite (thread-pinned BLAS): **224 passed, 2 skipped, 0 failed** (41 min; the 2 skips are pre-existing — the Plan 04-09 byte-identity rerun stub + the copulae SPSD library bug).
- `tests/test_null_result_template.py`: **7 passed** (incl. the now-running `test_pdf_dual_signature_when_quarto_available`).
- B1 body-content proof on the null_cost PDF: `pdftotext | grep -A5 firing | grep null_cost` PASS; `pdftotext | grep "Evidence.*null_cost"` PASS; H1 `HEDGE-05 NULL RESULT` PASS; `pdfinfo -custom` shows `HEDGE05Marker: HEDGE05-NULL-RESULT-V1`; size 146KB > 5KB.
- `cd fetch && pnpm test protocol-agnostic`: **6 passed** (SC-5 algorithmic-leak gate green).
- `make leak-check`: exit 0 (no protocol-name branch / factory addr / fee-tier literal).
- Task-1 + Task-2 acceptance greps: all pass (papermill=0, -P=0, -M≥1, parents[4]≥1, params.firing in both qmds=0, params$firing=0, ichi/steer in renderer=0; spec.protocol.name≥1, hardcoded ichi namespace=0, "data/raw/ichi" guard=0, generalized guard≥1, ICHI_PANEL_REQUIRED_COLUMNS=0).
- `_artifacts/repro_02_baseline_sha.txt`: single line matching `^[0-9a-f]{40}$`.
- REPRO-02 invariant: `git diff 9add304 HEAD -- fetch/src analysis/src` empty.

## Decisions Made
See `key-decisions` frontmatter. Headline: the meta-shortcode does NOT expand inside `{python}` cell source, so the body firing condition is delivered via the `HEDGE05_FIRING_CONDITION` env var while the H1 keeps the shortcode — both carry the identical value.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Pinned pdf-engine:pdflatex in null_result.qmd**
- **Found during:** Task 1 (first render attempt)
- **Issue:** TeX Live 2026's default LuaHBTeX engine leaves the pdfTeX primitive `\pdfinfo` undefined → "Undefined control sequence" → render aborts. The template lacked the engine pin that the proven ichi.qmd carries.
- **Fix:** Added `pdf-engine: pdflatex` to the template's `format.pdf` block (matching reports/ichi.qmd). Templates are outside frozen dirs.
- **Files modified:** reports/_templates/null_result.qmd
- **Verification:** Render succeeds (146KB PDF); pdfTeX engine used.
- **Committed in:** `0200bac` (Task 1 commit)

**2. [Rule 1 - Bug] Body firing condition delivered via env var (meta shortcode does not expand in code chunks)**
- **Found during:** Task 1 (B1 body-content check failed — body blank, code echoed)
- **Issue:** The plan's chosen mechanism (convert the three points to `{{< meta firing_condition >}}` and pass `-M`) resolves the shortcode in the markdown H1 but NOT inside `{python}` cell source, where the literal `{{< meta firing_condition >}}` string survives and no evidence branch matches → blank body (the exact B1 trap the plan warned about).
- **Fix:** Renderer also exports `HEDGE05_FIRING_CONDITION` env var; the two `{python}` chunks read `os.environ.get(...)`; the H1 keeps the `{{< meta >}}` shortcode. Both channels carry the same value. Added `echo: false` to the load-substrate chunk so its source no longer prints into the body. The plan's acceptance (no `params.`/`params$` prefix in the templates) is still satisfied — env-var reads carry no `params.` prefix.
- **Files modified:** null_result.py, null_result.qmd, _evidence_branches.qmd
- **Verification:** B1 checks pass — firing string in H1 + callout + Evidence body.
- **Committed in:** `0200bac` (Task 1 commit)

**3. [Rule 3 - Blocking] Render from the template dir + move (quarto absolute --output-dir bug)**
- **Found during:** Task 1 (renderer raised on absolute --output-dir)
- **Issue:** `quarto render ... --output-dir /abs/path` triggers a `safeMoveSync` path-join bug (`rename '<repo>/x.pdf' -> '/x.pdf'`, PermissionDenied). The proven `make report-ichi` avoids it by `cd reports && quarto render ... --output <name>` (no --output-dir).
- **Fix:** Run quarto with `cwd = template dir` and a bare relative `--output`, then `shutil.move` the rendered PDF to the requested destination. Also pin `QUARTO_PYTHON=sys.executable` so the jupyter/nbformat stack resolves.
- **Files modified:** null_result.py
- **Verification:** Renders to arbitrary absolute/relative output paths (the test uses a pytest tmp_path).
- **Committed in:** `0200bac` (Task 1 commit)

**4. [Rule 1 - Bug] Dual-signature marker check uses pdfinfo -custom**
- **Found during:** Task 1 (dual-signature test failed on the marker assertion)
- **Issue:** This poppler build surfaces the injected `/HEDGE05Marker` only under `pdfinfo -custom`; plain `pdfinfo` reports `Custom Metadata: yes` without the value. The marker IS genuinely in the PDF.
- **Fix:** The test queries `pdfinfo -custom` (then falls back to plain) so the real marker is read on every build. This strengthens, not weakens, the dual-signature contract.
- **Files modified:** analysis/tests/test_null_result_template.py
- **Verification:** test_pdf_dual_signature_when_quarto_available passes.
- **Committed in:** `0200bac` (Task 1 commit)

---

**Total deviations:** 4 auto-fixed (2 Rule-3 blocking, 2 Rule-1 bug)
**Impact on plan:** All four were necessary to make the renderer actually produce a body-correct, marker-bearing PDF on this toolchain (TeX Live 2026 + this poppler + this quarto). No scope creep — all edits are within the plan's three target files + the two templates the plan explicitly authorizes editing. The plan's stated `-M`/`{{< meta >}}` mechanism is retained for the H1; the env var is the necessary complement for the code-chunk body (the plan's B1 warning anticipated this risk).

## Issues Encountered

- **Pre-existing (out of scope, logged):** The two synthetic Phase-4 parquets under `data/raw/ichi/.../synthetic_p4_09*` fail `lint_artifacts.py` on the PANEL-02 metadata-header keys (chainId etc.) — a pre-existing gap unrelated to this plan (they DO carry `block_timestamp`, so the generalized column-guard passes on them). Not invoked by `make leak-check` / the test suite / the real-panel lint. Logged to `deferred-items.md` (D1); not fixed.
- The full analysis suite is genuinely slow (41 min, dominated by the post-02c profile_likelihood stationarity-barrier fits). Task-2's blast-radius subset (panel_e2e + ingest + required_keys_sync = 26 passed) confirmed green first; the full suite then corroborated 224 passed.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan 06-02 may now wire `make iteration-2-full` + the `make leak-check` scoped-grep extension (the exact M5 command is recorded byte-identical in PRE_REGISTRATION.md).
- Plan 06-03 (Steer fetch + pipeline run) inherits a frozen analysis/src + fetch/src tree; a Steer materialize will namespace to `data/raw/steer/` with no code edit.
- Plan 06-04's REPRO-02 attestation reads `_artifacts/repro_02_baseline_sha.txt` directly (`9add304…`) as the empty-diff base.

## Self-Check: PASSED

All 9 claimed files exist on disk; all 4 task commits (`0200bac`, `7d15ff6`, `9add304`, `1ecceac`) are present in git history.

---
*Phase: 06-iteration-2-swap-surface-validation-on-steer-ccop-usdt*
*Completed: 2026-05-29*
