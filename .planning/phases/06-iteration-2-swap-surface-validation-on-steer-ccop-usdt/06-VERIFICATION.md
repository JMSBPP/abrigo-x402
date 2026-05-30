---
phase: 06-iteration-2-swap-surface-validation-on-steer-ccop-usdt
verified: 2026-05-29T00:00:00Z
status: passed
score: 5/5 must-haves verified
re_verification: false
gaps: []
human_verification: []
---

# Phase 6: Iteration-2 Steer cCOP/USDT Swap-Surface Validation — Verification Report

**Phase Goal:** Re-run the same Phase 2–5 pipeline on Steer cCOP/USDT via config-swap only (zero edits to fetch/src or analysis/src), with the cost-leg lower-bound check first; emit an HONEST REPRO-02 swap-surface pass + an observed null_cost + reports/steer_null_result.pdf. Steer's expected cost-leg failure is the FEATURES.md D-08 negative-control validation (null-result emission observed at least once).

**Verified:** 2026-05-29
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | REPRO-02 empty-diff: zero edits to fetch/src or analysis/src from baseline to HEAD | VERIFIED | `git diff 9add304 HEAD -- fetch/src analysis/src` is EMPTY (exit 0); confirmed live. Baseline sha matches `_artifacts/repro_02_baseline_sha.txt` (single 40-char line `9add304fda4f7946e1720588a83acb52e413f424`). The baseline is the post-Plan-01 HEAD, after renderer fix + materialize namespace + AF-12 re-scope landed — so the empty-diff window is honest, not dressed-up. fetch/scripts also shows zero diff against baseline (deviation-1 hardcode did not touch fetch/src). |
| 2 | REPRO-03 + HEDGE-05: pre-reg commit precedes verdict commit (AF-03 ordering); verdict is FAIL -> null_cost | VERIFIED | `fc6eec0` (pre-reg STRADDLE rule, 18:30:06) precedes `0475bed` (verdict FAIL, 18:30:13) by 7 seconds. Both precede run commits `33f3e00/3c01427` (19:17–19:19). `notes/steer_cost_leg_bound.md` carries `verdict: FAIL`, `firing_condition: null_cost`, band 30k–100k vs free_tier_ceiling 100k. `data/fits/steer/0dc5bee374b6/firing_condition.json` field: `firing_condition: "null_cost"`, `decided_by: "abrigo_x402.hedge.null_result.decide_firing_condition"`. All commits confirmed to exist in repo. |
| 3 | REPRO-01 two-layer leak gate passes; AF-12 re-scope note in PRE_REGISTRATION.md with scoped-grep and SC-5 | VERIFIED | `make leak-check` exits 0 with "PASS: leak-check clean". The exact scoped-grep (`grep -rnE '"ichi"\|/ichi/\|raw/ichi\|fits/ichi' analysis/src fetch/src \| grep -vE '...'`) returns 0 hits on working tree. `notes/PRE_REGISTRATION.md` carries `## Phase 6 — REPRO-01 scoped-grep re-scope (AF-12 transparency note)` with the byte-identical scoped-grep command. AF-12 out-of-scope line present. SC-5 algorithmic-leak intent explicitly named. Layer-2 gate (`pnpm test protocol-agnostic`) attested in `_artifacts/repro_02_attestation.txt` (6 passed, exit 0). |
| 4 | REPRO-04 enforcement: panel_construction=v3-anchor-only honored; Q9 trigger evaluated in fit_report; q9_pooling_test.json absent by design with recorded SKIP-with-reason | VERIFIED | `protocols/steer.toml:35 panel_construction = "v3-anchor-only"`. `data/fits/steer/0dc5bee374b6/fit_report.json` `branching_ratio_ci` block: `eta_hat=0.7089`, `ci_width=0.949`, `q9_nullfire_triggered=true`, `q9_threshold=0.4`. `q9_pooling_test.json` absent by design. `notes/PRE_REGISTRATION.md` §Phase 6 SC-5 documents "SKIP — V3-anchor-only; unified fallback pre-registered deferred; q9_pooling_test.json absent; no REPRO-02 violation." Unified fallback deferred per pre-registration (not authored mid-iteration). |
| 5 | Deliverable: reports/steer_null_result.pdf exists, >50KB, null_cost in body, HEDGE05Marker custom field, no forbidden-narrowing strings; make verify-reproducibility PASS for both ichi + steer | VERIFIED | `reports/steer_null_result.pdf` = 145,942 bytes (>51,200). `pdftotext` shows `null_cost` 3 times in body. `pdfinfo -custom` returns `HEDGE05Marker: HEDGE05-NULL-RESULT-V1`. Forbidden-narrowing string grep returns 0 hits. `make verify-reproducibility` exits 0: "PASS (13/13 sha pins + ichi + steer PDF content-check)"; steer line: "OK (content: size+null_cost+HEDGE05+cost-leg, AF-03 no-narrowing): reports/steer_null_result.pdf". |

**Score:** 5/5 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `reports/steer_null_result.pdf` | Steer null-result PDF >50KB with null_cost in body | VERIFIED | 145,942 bytes; null_cost x3 in body; HEDGE05Marker custom field present; 0 forbidden-narrowing strings |
| `data/fits/steer/0dc5bee374b6/firing_condition.json` | firing_condition=null_cost, decided_by field | VERIFIED | `firing_condition: "null_cost"`, `decided_by: "abrigo_x402.hedge.null_result.decide_firing_condition"` |
| `notes/steer_cost_leg_bound.md` | verdict: FAIL, firing_condition: null_cost, band + free_tier_ceiling | VERIFIED | Carries `verdict: FAIL`, `firing_condition: null_cost`, `band_lower: 30000`, `band_upper: 100000`, `free_tier_ceiling: 100000`, straddle rule citation |
| `.planning/phases/06-…/_artifacts/repro_02_baseline_sha.txt` | Single 40-char sha `9add304…` | VERIFIED | Contains exactly `9add304fda4f7946e1720588a83acb52e413f424` (single line) |
| `.planning/phases/06-…/_artifacts/repro_02_attestation.txt` | Full attestation: empty-diff, AF-03 ordering, two-layer REPRO-01 gate | VERIFIED | All four sections present: baseline sha, empty-diff command + result EMPTY, AF-03 commit timestamps with ordering proof, REPRO-01 two-layer gate |
| `notes/PRE_REGISTRATION.md` | AF-12 re-scope section with SC-5 + exact scoped-grep + AF-12 out-of-scope line | VERIFIED | Section `## Phase 6 — REPRO-01 scoped-grep re-scope` present; SC-5 named as authoritative gate; exact scoped-grep command reproduced; AF-12 out-of-scope line present |
| `protocols/steer.toml` | panel_construction=v3-anchor-only; anchor pool address; repro_03_verdict block | VERIFIED | Line 35: `panel_construction = "v3-anchor-only"`; cCOP/USDT V3 anchor pool `0x2AC5…217B0`; `[protocol.repro_03_verdict]` STRADDLE block present |
| `data/fits/steer/0dc5bee374b6/fit_report.json` | Q9 trigger evaluated: eta_hat, ci_width, q9_nullfire_triggered | VERIFIED | `branching_ratio_ci.eta_hat=0.7089`, `ci_width=0.949`, `q9_nullfire_triggered=true`, `q9_threshold=0.4` |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `_artifacts/repro_02_baseline_sha.txt` | `git diff "$BASE" HEAD -- fetch/src analysis/src` | Shell `cat` + `git diff` | WIRED | Empty diff confirmed live; baseline read from file, not grepped from summary |
| `fc6eec0` (pre-reg STRADDLE rule) | `0475bed` (verdict FAIL) | Git commit timestamp ordering | WIRED | Pre-reg 18:30:06 precedes verdict 18:30:13 (AF-03 satisfied) |
| `notes/steer_cost_leg_bound.md` verdict FAIL | `firing_condition.json` null_cost | `cost_leg_check.py` sequential firing tree STEP 1 | WIRED | STEP 1 is the cost-leg check (Makefile); verdict FAIL fires `null_cost` from inside the completed run |
| `notes/PRE_REGISTRATION.md` scoped-grep | `make leak-check` recipe | Byte-identical grep command (M5) | WIRED | Scoped-grep in PRE_REGISTRATION.md matches Makefile recipe; `make leak-check` exit 0 confirmed |
| `reports/steer_null_result.pdf` | `make verify-reproducibility` | MANIFEST sha-pin + content-check | WIRED | PASS 13/13 sha pins + steer PDF content-check |

---

## Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| REPRO-01 | 06-01, 06-02, 06-04 | Protocol-spec layer is the only file class that changes between iterations; zero algorithmic protocol-coupling in fetch/src + analysis/src | SATISFIED | Two-layer gate: `make leak-check` exit 0 (scoped-grep 0 hits) + `pnpm test protocol-agnostic` 6 passed. AF-12 re-scope recorded in PRE_REGISTRATION.md before verdict. REQUIREMENTS.md: `[x] Complete (Plan 06-04)` |
| REPRO-02 | 06-01, 06-03, 06-04 | Same Phase 2–5 pipeline runs end-to-end on Steer with no edits to fetch/src or analysis/src | SATISFIED | `git diff 9add304 HEAD -- fetch/src analysis/src` EMPTY. Live config-swap run (run_id `0dc5bee374b6`) completed. REQUIREMENTS.md: `[x] Complete (Plan 06-03)` |
| REPRO-03 (first-step) | 06-02, 06-04 | Cost-leg lower-bound check runs as the first step of Iteration 2; null-result on failure | SATISFIED | `cost_leg_check.py` is STEP 1 of `make iteration-2-full`. Pre-reg commit `fc6eec0` precedes verdict `0475bed`. `notes/steer_cost_leg_bound.md` verdict FAIL. REQUIREMENTS.md: `[x] Complete (Plan 06-02)` |
| REPRO-04 (enforcement component) | 06-02, 06-03, 06-04 | cCOP panel construction decision documented before estimation; V3-anchor-only lock honored; Q9 evaluated | SATISFIED | `protocols/steer.toml panel_construction="v3-anchor-only"`. Q9 trigger evaluated + logged (`q9_nullfire_triggered=true`). Unified fallback deferred per pre-registration. `q9_pooling_test.json` absent by design with recorded SKIP-with-reason. REQUIREMENTS.md: `[x] Complete (Plan 00-03 + Plan 00-01)` with Phase 6 enforcement confirmed |
| HEDGE-05 (firing condition) | 06-03, 06-04 | Null-result emission template fires when cost-leg gate fails; PDF documents null with disqualifying evidence | SATISFIED | `firing_condition.json`: `"null_cost"`. PDF 145,942 bytes with `null_cost` x3 in body, `HEDGE05Marker: HEDGE05-NULL-RESULT-V1`. `make verify-reproducibility` content-check PASS. REQUIREMENTS.md: `[x] Complete (Plan 04-08)` with Phase 6 firing confirmed |

All 5 requirement IDs accounted for and marked Complete (or Complete with Phase-6 enforcement confirmed).

---

## Three Documented Deviations Assessment

| Deviation | Scope Location | Undermines Phase Goal? | Assessment |
|-----------|---------------|----------------------|------------|
| `fetch/scripts/build_panel_real.ts` hardcodes `data/raw/ichi/<pool>` | `fetch/scripts/` — OUTSIDE frozen `fetch/src` | No | The REPRO-02 diff window covers only `fetch/src` and `analysis/src`. `git diff 9add304 HEAD -- fetch/scripts/` = 0 lines changed. Zero impact on the empty-diff claim. Noted for future maintenance pass. |
| `make iteration-2-full` recipe passes wrong `--reports-pdf` path (latent bug) | Makefile recipe — outside frozen source | No | Worked around by invoking with correct `--reports-pdf reports/steer_null_result.pdf` in Plan 06-03. Makefile is not in the frozen scope. PDF landed at the correct path. Does not affect REPRO-02. |
| PDF at generic-template depth (DGP-support tables + REPRO-02 attestation not inlined into PDF body) | PDF content depth — user-approved | No | Underlying data is on-disk in `data/fits/steer/0dc5bee374b6/{gate_report,fit_report}.json` and in the phase `_artifacts/`. User approved this depth at Task-3 checkpoint. The `null_cost` verdict, size, HEDGE05Marker, and no-narrowing constraints all pass. |

None of the three deviations undermines the phase goal. All three are outside `fetch/src + analysis/src` or are user-accepted.

---

## Anti-Patterns Found

No blockers or warnings identified. Specific checks:

- `verification_pass: true` in `06-VERIFICATION-pre.md` is conditional on three gates, not pre-baked: the frontmatter documents that a false gate would yield `verification_pass: false` with `verdict: pending-fetch`.
- No verdict narrowing: `null_cost` is recorded AS-OBSERVED throughout. The forbidden-narrowing string check (5 strings) returns 0 hits in the PDF.
- SC-5 SKIP is recorded as "SKIP — V3-anchor-only (panel_construction=v3-anchor-only)…" not as "PASS" and not omitted.
- AF-03 future-substitute guardrail recorded in `06-VERIFICATION-pre.md` (any substitute candidate must be pre-registered before its data is seen).

---

## Human Verification Required

None. All material claims were verified programmatically:

- PDF content (null_cost occurrences, forbidden-narrowing strings, HEDGE05Marker) verified via `pdftotext` + `pdfinfo`.
- Empty-diff verified via `git diff --quiet` exit code.
- AF-03 commit ordering verified via `git show -s --format='%ci'`.
- `make verify-reproducibility` ran to completion with exit 0.
- Scoped-grep ran live and returned 0 hits.

---

## Gaps Summary

No gaps. All five requirement truths are verified at all three levels (exists, substantive, wired).

---

_Verified: 2026-05-29_
_Verifier: Claude (gsd-verifier) — Phase 6 initial verification, no previous VERIFICATION.md_
