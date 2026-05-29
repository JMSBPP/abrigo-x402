# Reviewer 2 (DevOps Automator) — Plan 05-03 (ichi.qmd + finalize report-ichi + render tests) — RE-REVIEW

## VERDICT
PASS

Scoped re-review of the render/build wiring. My prior MAJOR (the `report-ichi` ↔ `render-null-result-pdf` output collision on `reports/ichi.pdf`) is CLOSED — this plan now owns the retarget of the legacy target to `reports/_diagnostics/null_result_$$FIRING.pdf`, making `report-ichi` the sole producer of `reports/ichi.pdf`. The three MINORs (include-path, dormant AF-03 guard, mid-recipe uv stall) are all resolved. I confirmed the include-path mechanics live against the actual file layout. No new BLOCKERs.

---

## Prior findings — confirm-closed

### MAJOR 1 — output collision render-null-result-pdf vs report-ichi → **CLOSED**
Confirmed live: `render-null-result-pdf` (Makefile L154) still writes `--output ichi.pdf` today. The revised plan's Task 2b (L177) + the `<interfaces>` OUTPUT COLLISION block (L100) retarget it to `mkdir -p reports/_diagnostics` + `--output _diagnostics/null_result_$$FIRING.pdf`. Acceptance L191 hard-gates both directions: `! grep -qE 'render _templates/null_result.qmd.*--output ichi.pdf' Makefile` AND `grep -q '_diagnostics/null_result' Makefile`. Plus the `rm -f reports/ichi.pdf` stale-guard from 05-00 is kept. Two-producers-one-artifact trap eliminated.

### MINOR 2 — wrong `{{< include ../_templates/... >}}` relative root → **CLOSED (verified live)**
I verified the file layout: `reports/_templates/null_result.qmd` includes the partial as `{{< include _evidence_branches.qmd >}}` (sibling, both in `_templates/`). The NEW `reports/ichi.qmd` lives one level up at `reports/`, so it must reference `_templates/_evidence_branches.qmd`. The revised plan uses exactly `{{< include _templates/_evidence_branches.qmd >}}` (truths L19, key_links L38, `<interfaces>` L98) and the acceptance L151 asserts BOTH the correct path present AND the wrong `../_templates/` form absent. The earlier `../_templates/` (resolving to a nonexistent repo-root `/_templates/`) is explicitly forbidden. Correct.

### MINOR 3 — AF-03 verdict-not-narrowed guard dormant in CI → **CLOSED**
A NON-render companion test `test_ichi_qmd_source_not_narrowed` (Task 2c L180) is added with NO quarto-skip guard — it runs in CI on this quarto-less env: greps `reports/ichi.qmd` source for required-present (`null_strip_unavailable`, labeled `p ?= ?0.0474`, correct include path) and required-absent (the 4 forbidden narrowing strings + the wrong include path). Acceptance L194 makes it a hard gate (`pytest …::test_ichi_qmd_source_not_narrowed -x` exits 0). The two PDF-text tests stay quarto-skip-guarded (correct). The most important correctness gate now fires in CI on source, with the PDF-text assertion owned by the quarto machine + 05-04 checkpoint.

### MINOR 4 — mid-recipe `uv run` curl stall → **CLOSED (acceptable)**
The curl-logging step (L173) retains the `|| echo "...unavailable (continuing)"` tail so it cannot fail the build. Documented as network-optional. Acceptable as-is.

---

## New findings from the edits
None at BLOCKER/MAJOR.

- **MINOR (new) — the `_evidence_branches.qmd` `null_strip_unavailable` branch is prose-only (no live JSON file reads in that branch).** I read the partial: the `null_strip_unavailable` block (lines ~55-74) prints narrative text referencing `strip_degenerate.json`/`gate_report.json` by name but does not `open()` them via relative paths in that branch. So the plan's proposed "NON-render path-existence smoke test" (Task 2c, L180 — "extract its load paths, assert they exist") will find few/no paths to check in the active branch and is close to a no-op. Harmless and still correct (it won't false-fail), but the executor should not over-invest in it; the real include-path guard is the `grep` for the correct vs wrong `{{< include >}}` form, which is sound.

- **MINOR (new) — `--execute-param firing_condition=null_strip_unavailable` uses `=` while the legacy target uses `:`.** The legacy `render-null-result-pdf` passes `--execute-param firing_condition:$$FIRING` (colon form, Makefile L154); the new `report-ichi` uses `firing_condition=null_strip_unavailable` (equals form, L189). Quarto accepts `--execute-param key:value`; the `key=value` form is the Quarto CLI's documented syntax for `-P/--execute-param` in recent versions but the colon form is what the proven path uses. Recommend matching the proven colon form (`firing_condition:null_strip_unavailable`) for parity, OR verify the `=` form on the quarto machine before relying on it. Non-blocking (the YAML `params:` default also sets it — belt-and-suspenders), but worth a one-line check at render time so the partial's branch selector isn't silently unpopulated.

---

## Clean checks (re-confirmed)
- quarto a HARD prerequisite; only TinyTeX self-installs (idempotent `quarto install tinytex`). ✓
- Render tests stay quarto-skip-guarded (verbatim `shutil.which` pattern, confirmed at test_null_result_template.py L59/L61); acceptance L192 `grep -c 'shutil.which("quarto")' … ≥ 2`. Green suite preserved. ✓
- Markdown fallback rejected + >50KB size gate carried from 05-00. ✓
- Dual-signature marker `HEDGE05-NULL-RESULT-V1` reused; ichi.qmd is a NEW doc (Pitfall 4). ✓
- Read-only artifact consumption (Pattern 1) — code cells load fit/gate/firing/sensitivity JSON, no re-fit. ✓
- KS label discipline: labeled `p=0.0474` (p-value), statistic `D=0.148`; AF-03 grep asserts the labeled form, not bare 0.0474 (`<interfaces>` L81, acceptance L150). ✓
- `depends_on: [05-00, 05-01, 05-02]` — render references the spot-check + sweep + MANIFEST, all produced upstream. ✓
