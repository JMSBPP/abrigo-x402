---
phase: 06-iteration-2-swap-surface-validation-on-steer-ccop-usdt
plan: 04
artifact: VERIFICATION-pre
verification_pass: true
verdict: pass-null-as-observed
created: 2026-05-29
requirements_covered: [REPRO-01, REPRO-02, REPRO-03, REPRO-04, HEDGE-05, SC-1, SC-2, SC-3, SC-4, SC-5]
firing_condition: null_cost
repro_02_empty_diff: true
iteration_1_complete_marker: "87991ac"
repro_02_baseline_sha: "9add304fda4f7946e1720588a83acb52e413f424"
repro_02_baseline_sha_file: ".planning/phases/06-iteration-2-swap-surface-validation-on-steer-ccop-usdt/_artifacts/repro_02_baseline_sha.txt"
steer_run_id: "0dc5bee374b6"
steer_pdf_path: "reports/steer_null_result.pdf"
steer_pdf_bytes: 145942
quarto_skipped: false
q9_unified_fallback: deferred
sc5_disposition: "SKIP — V3-anchor-only (panel_construction=v3-anchor-only); unified fallback pre-registered deferred; q9_pooling_test.json absent; no REPRO-02 violation"
---

# Phase 6 — Iteration-2 Steer cCOP/USDT Acceptance Gate Verification

Mirrors the Phase 4 `04-VERIFICATION-pre.md` template (frontmatter `verification_pass`
+ an N-row acceptance grid mapping requirement IDs / SCs → runnable command → exit
code → verdict). Every Phase 6 requirement (REPRO-01..04 + HEDGE-05(a)) and every
ROADMAP §Phase 6 success criterion (SC-1..5) is mapped to {command, expected,
observed, verdict}.

**Headline scientific outcome (AS-OBSERVED, the D-08 negative control fired):** the
frozen Phase 2–5 pipeline ran end-to-end on `protocols/steer.toml` (config-swap, ZERO
`fetch/src` + `analysis/src` edits, run_id `0dc5bee374b6`). The Steer cost-leg demand
estimate STRADDLES the 100k/mo Graph free-tier line (pre-committed 30k–100k band, NOT
strictly ABOVE 100k) → the pre-registered conservative-fail rule fires HEDGE-05
condition (a) `null_cost` from INSIDE the completed run. `reports/steer_null_result.pdf`
(145942 B > 50 KB) headlines `null_cost`. This is the intended FEATURES.md D-08
negative-control validation — observing the null-result path fire at least once across
the two iterations confirms the falsification machinery works in practice. **The verdict
is recorded AS-OBSERVED — it was NOT narrowed/relabeled to any form of positive.**

**`verification_pass: true` — all three M2 conditional gates hold this session:**
(1) `reports/steer_null_result.pdf` exists and `wc -c` = 145942 > 51200;
(2) `null_cost` is observed in `data/fits/steer/0dc5bee374b6/firing_condition.json`
AND in the in-session `make verify-reproducibility` steer content-check report;
(3) the REPRO-02 empty-diff holds (`git diff 9add304 HEAD -- fetch/src analysis/src`
EMPTY, base read from the pinned `_artifacts/repro_02_baseline_sha.txt`).
Had any gate been unmet (Steer fetch deferred / PDF absent or ≤ 50 KB / empty-diff
violated), `verification_pass` would be `false` with `verdict: pending-fetch`.

> Path note (latent-path-bug correction): the 06-04 plan text and the canonical
> REPRO-02 attestation command reference `_artifacts/repro_02_baseline_sha.txt` as a
> repo-root path. There is NO repo-root `_artifacts/` directory; the pinned sha file
> lives at the PHASE-DIR path recorded in `repro_02_baseline_sha_file` above. Every
> command in this grid uses the phase-dir path so it is reproducible.

## Acceptance Grid

| Row | Requirement / SC | Command | Expected | Observed | Verdict | Notes/Caveats |
|-----|------------------|---------|----------|----------|---------|---------------|
| 1 | REPRO-01 (two-layer leak gate) | `make leak-check` (layer 1, scoped-ichi) + `cd fetch && pnpm test protocol-agnostic` (layer 2, authoritative SC-5 lint) | exit 0 + exit 0 | `make leak-check` → "PASS: leak-check clean" exit 0 (grep emits stderr `binary file matches` noise on `__pycache__/*.pyc`; the leak logic inspects only textual output). `pnpm test protocol-agnostic` → Test Files 1 passed (1); Tests 6 passed (6), exit 0. Scoped genuine-coupling grep (text-only, AF-12 re-scope per `notes/PRE_REGISTRATION.md`) → 0 hits. | PASS | The scoped grep is the SC-5-intent re-scope (excludes comments/docstrings + CLI-overridable defaults `data/fits/ichi`, `reports/ichi.pdf` + `protocols/ichi.toml`); the authoritative gate is the protocol-agnosticism contract test. |
| 2 | REPRO-02 (zero-edit swap-surface invariant) | `BASE=$(cat .planning/phases/06-…/_artifacts/repro_02_baseline_sha.txt); git diff "$BASE" HEAD -- fetch/src analysis/src` | EMPTY (no output; `--quiet` exit 0) | EMPTY. BASE=`9add304fda4f7946e1720588a83acb52e413f424` (single 40-char line, `^[0-9a-f]{40}$`). HEAD=`71e2f83` at attestation. Demonstrated under a LIVE config-swap run (run_id `0dc5bee374b6`). | PASS | Honest pass — base READ from the pinned file (M3), not grepped from a SUMMARY. Cited in `_artifacts/repro_02_attestation.txt`. See REPRO-02 attestation section below. |
| 3 | REPRO-03 (cost-leg first-step + AF-03 ordering) | `git log --oneline -- notes/PRE_REGISTRATION.md notes/steer_cost_leg_bound.md` + read `notes/steer_cost_leg_bound.md` verdict | straddle-rule pre-reg + REPRO-01 re-scope PREDATE the verdict + run commits; `verdict: FAIL` | Pre-reg STRADDLE rule `fc6eec0` (2026-05-29 18:30:06) + REPRO-01 re-scope `9add304` (Plan 01) PREDATE the cost-leg verdict emission `0475bed` (18:30:13) and the Steer run/hedge commits `33f3e00` (19:17:16) / `3c01427` (19:19:48). `notes/steer_cost_leg_bound.md`: `verdict: FAIL`, `firing_condition: null_cost`, band 30000–100000 vs free_tier_ceiling 100000. | PASS (FAIL verdict AS-OBSERVED) | Cost-leg check is STEP 1 of `make iteration-2-full` (before any fetch). The 30k–100k band STRADDLES (not strictly ABOVE) 100k → conservative-fail → `null_cost`. No demand re-estimated/narrowed — Phase 6 OBSERVES the verdict. |
| 4 | REPRO-04 (panel-construction lock honored) | `grep -n panel_construction protocols/steer.toml` + check `data/fits/steer/0dc5bee374b6/q9_pooling_test.json` + read Q9 trigger eval | `panel_construction="v3-anchor-only"`; Q9 trigger EVALUATED; unified fallback DEFERRED per pre-reg | `protocols/steer.toml:35 panel_construction="v3-anchor-only"`. Q9 trigger EVALUATED + logged in `fit_report.json`: `branching_ratio_ci.eta_hat=0.7089`, `ci_width=0.949 > q9_threshold=0.4` → `q9_nullfire_triggered=true`; per-leg `[271, 260]` both < 300 floor. Per Plan-02 pre-registration the unified cross-class fallback is DEFERRED (not authored); V3-anchor-only reported with the signal-scope caveat. `q9_pooling_test.json` ABSENT by design (no unified mode). | PASS | The honest outcome on a fired trigger in V3-anchor-only mode is a documented "fallback-DEFERRED" note (NOT new code mid-iteration); AF-03 clean (pre-registered, admits the gap). See SC-5 row. |
| 5 | HEDGE-05(a) (null-result emission on cost-leg fail) | `python3 -c "import json;print(json.load(open('data/fits/steer/0dc5bee374b6/firing_condition.json'))['firing_condition'])"` + `make verify-reproducibility` steer content-check | `null_cost`; steer PDF content-check PASS | `firing_condition.json` → `firing_condition: "null_cost"`, `decided_by: abrigo_x402.hedge.null_result.decide_firing_condition`. `make verify-reproducibility` → "OK (content: size+null_cost+HEDGE05+cost-leg, AF-03 no-narrowing): reports/steer_null_result.pdf" + "PASS (13/13 sha pins + ichi + steer PDF content-check)" exit 0. PDF 145942 B > 50 KB; `null_cost` x3 in body; `HEDGE05Marker: HEDGE05-NULL-RESULT-V1` (via `pdfinfo -custom`); 0 forbidden-narrowing strings. | PASS (null AS-OBSERVED) | `null_cost` fired from a FIELD inside the completed run (sequential firing tree: condition (a) cost-leg evaluated first), NOT a pre-fetch short-circuit. The full DGP/Hawkes/gate output ran regardless (the run is what demonstrates the zero-edit invariant). |
| 6 | SC-1 (`protocols/steer.toml` populated) | `grep -nE "panel_construction|repro_03_verdict|0x2AC5baA668A8A58FD0e302B9896717484fd217B0" protocols/steer.toml` | populated: anchor pool + verdict block + panel-construction lock | `protocols/steer.toml` carries the cCOP/USDT V3 anchor pool `0x2AC5…217B0`, `[protocol.repro_03_verdict]` STRADDLE block, `panel_construction="v3-anchor-only"`, demand-window fields (30k–100k band). Authored Phase 0 (Plan 00-05) + verdict applied Plan 06-02. | PASS | `cost_leg_lower_bound_verified=false` STRADDLE comment present (the band is not strictly above 100k). |
| 7 | SC-2 (cost-leg first step; clean null exit) | `grep -n "STEP 1" Makefile` (cost-leg is iteration-2-full STEP 1, before fetch) + `notes/steer_cost_leg_bound.md` written | cost-leg check is the FIRST executed step; null PDF ships | `Makefile :: iteration-2-full` STEP 1 = `scripts/cost_leg_check.py` (REPRO-03 first-step, AF-03 ordering) BEFORE the Steer fetch (STEP 2). `notes/steer_cost_leg_bound.md` written with primary-source band + `verdict: FAIL`. On the FAIL, `reports/steer_null_result.pdf` ships (the Decision-3 SC-2-vs-SC-4 resolution: the cost-leg verdict is a FIELD in the gate report, the pipeline is NOT short-circuited — the full re-run demonstrates REPRO-02). | PASS | Per 06-CONTEXT Decision 3, the apparent SC-2-vs-SC-4 tension is resolved in favor of the full re-run; `null_cost` fires from inside the completed run. |
| 8 | SC-3 (two-layer leak gate) | `make leak-check` + `cd fetch && pnpm test protocol-agnostic` | exit 0 + exit 0 | Identical to Row 1: leak-check exit 0 "PASS: leak-check clean"; protocol-agnostic 6 passed exit 0. | PASS | Layer (a) string grep is the cheap pre-commit complement; layer (b) SC-5 protocol-agnosticism lint is the load-bearing algorithmic-leak gate. |
| 9 | SC-4 (`make iteration-2-full` empty-diff) | `make verify-reproducibility` (in-session steer content-check) + REPRO-02 empty-diff (Row 2) | steer null PDF produced; `git diff` between iteration-1-complete and iteration-2-complete EMPTY | `make iteration-2-full` produced `reports/steer_null_result.pdf` (run_id `0dc5bee374b6`); `make verify-reproducibility` exit 0 content-checks it; `git diff 9add304 HEAD -- fetch/src analysis/src` EMPTY. | PASS | Two deviations in the iteration-2-full recipe were worked AROUND in Plan 06-03 without touching frozen source (see Known carried-forward deviations below); the empty-diff invariant held. |
| 10 | SC-5 (Q9 pooling test if unified) | `test -f data/fits/steer/0dc5bee374b6/q9_pooling_test.json` (only required if unified) | N/A — V3-anchor-only mode selected | `q9_pooling_test.json` ABSENT (no unified mode). `panel_construction="v3-anchor-only"`. | **SKIP — V3-anchor-only (panel_construction=v3-anchor-only); unified fallback pre-registered deferred; q9_pooling_test.json absent; no REPRO-02 violation** | Recorded VERBATIM as the SKIP-with-reason string (per M-requirement) — NOT PASS, NOT omitted. SC-5's `q9_pooling_test.json` artifact is only mandated in unified mode; V3-anchor-only is the Phase-0-locked Q-9 primary decision. |

## Requirement-coverage gate (B3 — explicit-fail test, NOT a silent awk no-op)

The ≥ 5-distinct-requirement-ID coverage check uses an explicit `python3`
exit-code test (`awk '$1>=5'` is a silent no-op that exits 0 even when false):

```bash
grep -cE "REPRO-0[1-4]|HEDGE-05" \
  .planning/phases/06-iteration-2-swap-surface-validation-on-steer-ccop-usdt/06-VERIFICATION-pre.md \
  | python3 -c "import sys; sys.exit(0 if int(sys.stdin.read().strip())>=5 else 1)" && echo OK
```

Expected: exit 0 (OK) — this file maps all of REPRO-01, REPRO-02, REPRO-03,
REPRO-04, HEDGE-05 (≥ 5 distinct ID mentions). The `python3` form FAILS LOUDLY
(exit 1) if the count drops below 5; `awk '$1>=5'` would have exited 0 regardless.

## Regex Acceptance Footers

- `grep -cE "REPRO-0[1-4]|HEDGE-05" 06-VERIFICATION-pre.md` → expected ≥ 5 hits
  (≥ 5 distinct requirement IDs mapped).
- `grep -cE "null_cost" 06-VERIFICATION-pre.md` → expected ≥ 1 hit (the
  AS-OBSERVED D-08 negative-control firing condition surfaced).

(Verifiable from the contents of THIS file.)

## Verdict AS-OBSERVED (the D-08 negative control — NOT narrowed)

**Steer cCOP/USDT cost-leg verdict: FAIL → `null_cost`.** The Steer data-demand
estimate is a STRADDLE: the pre-committed band `[30000, 100000]` queries/mo includes
the 100k/mo Graph free-tier line but is NOT strictly above it. Per the pre-registered
conservative-fail straddle rule (committed `fc6eec0` BEFORE the verdict `0475bed`), a
straddle → cost-leg FAILS → fires HEDGE-05 condition (a) `null_cost`. Steer is the
honest D-08 negative control; the null firing is the INTENDED validation, not a
disappointment. The full Phase 2–5 pipeline RAN regardless (`gate_report.json
any_condition_passed=true`: hawkes_self_excitation η=0.7089 + usdt_depeg_basis_jump
pass; vol_of_vol + positive_skew_fat_tails did not) — these are convex-dominance
SUPPORT material, NOT the firing condition (the cost-leg `null_cost` fired first in the
sequential tree).

**Resolution disposition: substitute pending (future milestone).** Iteration 2's
resolution policy on the Steer null is to SUBSTITUTE a replacement candidate — but the
substitute is NOT named or executed in this milestone (per 06-CONTEXT Decision on
REPRO-03 resolution + the AF-12 OUT-OF-SCOPE list). **AF-03 future-substitute
guardrail (recorded so it is not lost):** any future substitute candidate MUST be
pre-registered BEFORE its own data is seen; choosing a substitute AFTER observing
Steer's null without pre-registration would be candidate-shopping — forbidden. Phase 6
ships the Steer null-result deliverable and records the disposition only.

**Forbidden-narrowing guard (shared 5-string set, M7).** The AF-03 forbidden-narrowing
set has five members: the "pass-with-caveat" phrasing, the "near-miss"-prefixed
positive, the "directionally"-prefixed positive, the "exploratory"-prefixed positive,
and the bare "positive"-result phrasing. NONE of these five appear describing this
verdict in `reports/steer_null_result.pdf` (0 hits, enforced by the
`make verify-reproducibility` steer content-check loop). The verdict here is `null_cost`,
recorded verbatim AS-OBSERVED — it is not relabeled as any of those five. (This guard
sentence deliberately describes the forbidden phrasings rather than quoting them
contiguously, so a context-blind grep of THIS file does not false-positive on the
enumeration — the same Phase-5 B1/AF-03 enumeration-trap discipline.)

## REPRO-02 Empty-Diff Attestation

**Command (base read from the pinned file, M3 — NOT grepped from a SUMMARY):**

```bash
BASE=$(cat .planning/phases/06-iteration-2-swap-surface-validation-on-steer-ccop-usdt/_artifacts/repro_02_baseline_sha.txt)
git diff "$BASE" HEAD -- fetch/src analysis/src
```

**Result:** EMPTY (no output). `git diff --quiet "$BASE" HEAD -- fetch/src analysis/src`
→ exit 0.

- **Baseline (post-Plan-01) sha:** `9add304fda4f7946e1720588a83acb52e413f424` — the
  re-baselined HEAD AFTER the three generic, leak-clean baseline-maintenance commits
  (renderer `-P`→`-M` fix, materialize `data/raw/<protocol>/` namespace, AF-12
  REPRO-01 scoped-grep re-scope) landed. NOT the PR#1 merge marker; per the DevOps
  review, `87991ac..HEAD` is empty today and goes non-empty only after Plan 01's source
  edits, so the base MUST be the post-Plan-01 sha for the empty-diff to mean "no frozen
  edits in the iteration-2 window."
- **Iteration-1-complete marker (CLAUDE.md cycle-closure anchor):** `87991ac` (Merge
  pull request #1 from JMSBPP/phase-05-iteration-1-pdf).
- **HEAD at attestation:** `71e2f83`.

Full attestation (empty-diff command/result + AF-03 ordering proof + REPRO-01 two-layer
gate) recorded in
`.planning/phases/06-iteration-2-swap-surface-validation-on-steer-ccop-usdt/_artifacts/repro_02_attestation.txt`.

## Known carried-forward deviations (from Plan 06-03, recorded as known-items)

All three were flagged at the Plan 06-03 Task-3 checkpoint and APPROVED by the user;
NONE touched the frozen `fetch/src` + `analysis/src` REPRO-02 scope (the empty-diff
invariant held):

1. **`fetch/scripts/build_panel_real.ts` hardcodes `data/raw/ichi/<pool>`** [Rule-3,
   worked around via stage-then-relocate; `fetch/scripts/` is OUTSIDE the frozen
   `fetch/src` scope; zero source edits]. Noted for a future maintenance pass.
2. **`make iteration-2-full` recipe passes `--reports-pdf ../reports/…`** (would land
   the PDF above the repo root — latent recipe path bug) [Rule-3; invoked with the
   repo-correct `--reports-pdf reports/steer_null_result.pdf`; recipe path bug noted
   for a maintenance pass, not fixed here — out of this plan's frozen-source scope].
3. **PDF at generic-template depth** — DGP-support tables + the REPRO-02 attestation
   line are not inlined into the PDF body [Rule-1; recorded on-disk in
   `data/fits/steer/0dc5bee374b6/{gate_report,fit_report}.json` + the Task commit
   bodies + this VERIFICATION grid; user APPROVED the deliverable at this depth at the
   Task-3 checkpoint].

## Forward Audit Trail (Phase 6 plan commits)

| Plan | Commit(s) | Notes |
|------|-----------|-------|
| 06-01 | `0200bac` `7d15ff6` `9add304` `1ecceac` | baseline maintenance (renderer -P→-M, materialize namespace, AF-12 REPRO-01 re-scope); `9add304` is the pinned REPRO-02 base. |
| 06-02 | `fc6eec0` `0475bed` `a8f0ef0` | pre-reg STRADDLE rule (before verdict) + `cost_leg_check.py` verdict FAIL + deterministic iteration-2-full + scoped leak-check. |
| 06-03 | `33f3e00` `3c01427` | config-swap run (fetch+materialize+fit) + hedge + `reports/steer_null_result.pdf` (null_cost from inside the run); Task-3 human-verify APPROVED. |
| 06-04 | `d5d4268` `9d6cfa0` (this verification) | REPRO-02 attestation + AF-03 ordering proof; steer PDF content-check in verify-reproducibility + MANIFEST; this acceptance grid. |

## Cycle-closure next step (USER-gated)

Per CLAUDE.md cycle-closure ritual, the Iteration-2 cycle closes when its terminal
deliverable (`reports/steer_null_result.pdf`) lands + verifies — which it has
(verification_pass=true). The next step is USER-gated and is NOT performed inside this
plan: **push origin → PR into upstream (`wvs-finance/abrigo-x402:master`) → merge
upstream after verification passes.** The PR body must summarize the Iteration-2
deliverable honestly (the `null_cost` D-08 negative control, recorded AS-OBSERVED, NOT
narrowed). No push to upstream from inside this plan (AF-12 OUT-OF-SCOPE).

---

*Phase 6 verification authored 2026-05-29 by GSD execute-phase executor against
`06-04-PLAN.md` (Model QA Specialist charter). The null `null_cost` is the AS-OBSERVED
D-08 negative control — `verification_pass: true` because the steer PDF (145942 B) + the
observed `null_cost` + the REPRO-02 empty-diff all hold this session.*
