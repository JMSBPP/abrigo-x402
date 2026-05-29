# Reality-Checker RE-REVIEW — 05-03-PLAN.md (REPORT-01 ichi.qmd deliverable + report-ichi finalize)

**Reviewer:** Reality Checker (Reviewer 1)
**Date:** 2026-05-29 (re-review of revised plan)
**Artifact:** `.planning/phases/05-reporting-iteration-1-pdf-deliverable-l7/05-03-PLAN.md`

## VERDICT

PASS

Both prior MAJORs are CLOSED. The render misfire is fixed: `--execute-param firing_condition=null_strip_unavailable` is added, the include path is corrected to `_templates/_evidence_branches.qmd` with a grep-assert that the wrong `../_templates/` form is absent, the colliding `render-null-result-pdf` is retargeted off `reports/ichi.pdf`, and a NON-render source-grep + path-existence companion test runs in CI. The KS-label gap is closed: the AF-03 grep asserts the LABELED `p ?= ?0.0474` (not bare), D=0.148 is verified-real as the statistic, single canonical rounding. One NEW MINOR on the grep regex (cosmetic; the abstract form guarantees a match).

---

## Prior findings — confirm-closed

### PRIOR MAJOR-1 (`_evidence_branches.qmd` include misfires) — CLOSED (and the risk is even smaller than feared)
- `--execute-param` added: action 2a (line 171) + the render line (line 175) + acceptance (line 189) require `quarto render ichi.qmd … --execute-param firing_condition=null_strip_unavailable`, for parity with the proven `render-null-result-pdf` path, belt-and-suspenders with the YAML param.
- Include path corrected: the plan mandates `{{< include _templates/_evidence_branches.qmd >}}` (NOT `../_templates/...`) and grep-asserts the wrong form ABSENT (acceptance line 151: `! grep -q '\.\./_templates/_evidence_branches'`). LIVE-VERIFIED the partial lives at `reports/_templates/_evidence_branches.qmd`, so the `_templates/...` relative form from `reports/ichi.qmd` is correct.
- Non-render CI guard added: `test_ichi_qmd_source_not_narrowed` (line 180) runs WITHOUT quarto and asserts the correct include path + a path-existence smoke for the partial's JSON loads — so a wrong path is caught in CI, not only on the operator machine.
- BONUS reality check: I READ `_evidence_branches.qmd` live. Its `null_strip_unavailable` branch is PURE `print()` statements — it reads NO JSON via relative paths (no `open()`, no `json.load`, no `read_parquet`). Its only dynamic input is `{{< meta params.firing_condition >}}`, which both the YAML param and `--execute-param` populate. So the original "relative JSON reads break from the include site" concern is moot — there are no such reads. The plan's path-existence smoke test will trivially pass (no paths to check), which is harmless.

### PRIOR MAJOR-2 (`0.0474` p-value vs statistic conflation) — CLOSED
- KS LABEL DISCIPLINE block (line 81) + §5 (line 135) + FORBIDDEN (line 142): the PDF must print the LABELED `p=0.0474` / `p = 0.0474` and NEVER a bare `0.0474` or a statistic-labeled `0.0474`; the statistic is `D=0.148`.
- The AF-03 grep asserts the labeled form: `grep -qE 'p ?= ?0\.0474'` (verify line 145, acceptance line 150, test line 180) — a wrong `D=0.0474` / `KS=0.0474` cannot satisfy it.
- LIVE-VERIFIED the numbers: `fit_report.json ks_rescaled_time.per_leg[0]`: `p_value=0.047350333810196134` (→ `p=0.0474`), `ks_statistic=0.14799982742727918` (→ `D=0.148`), `n_events=83`; leg-1 `p_value=0.05643942824856608` (→ `p=0.0564`). The plan's stated values (line 75) are byte-correct. (The artifact field is `ks_statistic`, not `statistic` — the plan's "statistic D=0.148" is the right value.)

### PRIOR MINOR-1 (SC-1 .qmd/.ipynb deviation note) — ADDRESSED
Success criteria (line 212) restates the documented `.qmd`-satisfies-`.ipynb` SC-1 deviation; carries into 05-04.

### PRIOR MINOR-2 (skill invocation unverifiable) — ADDRESSED
Output (line 216) requires the SUMMARY record which skills were invoked + the notation-clean diff for the 05-04 checkpoint.

### PRIOR MINOR-3 (`\bkappa\b|κ` brittle for LaTeX glyph) — ADDRESSED
Acceptance line 155 keeps the guard but documents it targets the INDEX, not a stray glyph, and notes the locked equation set excludes κ. Acceptable.

---

## Foundation re-confirmed (no regression)
- Every embedded number LIVE-VERIFIED real (eta=0.5999724…; LR observed_stat=561.2948… p=0.0; gate_passes=FALSE; firing_condition=null_strip_unavailable; KS leg-0/1 as above). ✓
- AF-03 no-narrowing strings grep-asserted absent (4 forbidden phrases, line 154); gate_passes stays FALSE; 9-rejected-changes provenance + 3-run comparison required. ✓
- USDT not USDC (line 133); no κ index. ✓
- Collision fix: LIVE-confirmed `render-null-result-pdf` line 154 still writes `--output ichi.pdf`; 05-03 retargets it to `_diagnostics/null_result_$$FIRING.pdf` (acceptance line 191). ✓
- quarto-skip guards preserved on the two render tests (`grep -c 'shutil.which("quarto")' >= 2`, line 192); the source-grep test is unguarded (runs everywhere). ✓
- Specialist (Technical Writer + DevOps consult) named with skills + why. ✓

---

## NEW findings

### NEW MINOR-1 — the AF-03 grep `p ?= ?0\.0474` does NOT match the `**p-value = 0.0474**` bold form the plan also mandates; it matches only `p=0.0474` / `p = 0.0474`
**Evidence:** LIVE-tested the regex: `echo '**p-value = 0.0474**' | grep -qE 'p ?= ?0\.0474'` → NO MATCH (the char after `p` is `-`, not space/`=`); `echo 'p=0.0474'` and `'p = 0.0474'` → MATCH. The plan mandates `p=0.0474` in the Abstract (line 130) AND `**p-value = 0.0474**` in §5 Results (line 135). The grep passes only because the Abstract `p=0.0474` form is required to appear — so a correct document passes. But if an author writes ONLY the `p-value = 0.0474` form throughout, the guard would FALSE-FAIL a correct document.
**Why it matters:** Low — the plan's own structure (Abstract `p=0.0474`) guarantees a match; the failure mode is a false-negative on an over-zealous author, not a missed narrowing. Verdict integrity is not at risk.
**Fix (optional):** Broaden the AF-03 grep to `p ?(-value)? ?= ?0\.0474` (or add an alternation) so both the abstract and the §5 bold form satisfy it. Not blocking.

---

## Cross-check summary
- Render realism: CLOSED — `--execute-param` + correct `_templates/` include path + wrong-path grep-assert + retargeted collision + non-render CI companion. The partial reads no relative JSON (pure prints), so the residual risk is minimal. (LIVE-verified)
- KS label: CLOSED — labeled `p=0.0474`, D=0.148 verified-real, single rounding, grep asserts labeled form. (LIVE-verified)
- Verdict integrity: every number real; no-narrowing strings asserted absent. (clean)
- Specialist: present. (clean)

**BLOCKER: 0 · MAJOR: 0 (2 prior CLOSED) · MINOR: 1 NEW (cosmetic grep regex)**
