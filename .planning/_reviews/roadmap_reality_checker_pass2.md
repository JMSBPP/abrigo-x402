# Roadmap Reality Checker Review — Pass 2

**Artifact:** `.planning/ROADMAP.md` (revised, 202 lines, 8 phases, 2026-05-25)
**Reviewer:** Reality Checker (epistemic-skepticism default; comparing against pass-1 blockers/concerns)
**Date:** 2026-05-25

---

## VERDICT

**PASS (with two non-blocking residuals).**

The revision did real work, not paper-work. All four pass-1 blockers (B1–B4) are addressed by mechanisms that bind in code or in git, not by wording shifts: the Phase-0 firing path is explicitly memo-only (B1), REPRO-03's pass/straddle/fail numeric thresholds are pre-committed at 100k queries/mo and locked by git-log ordering (B2), the algorithmic leak-gate becomes a Phase-1 contract test with a CI lint that hard-rejects `if config.name ==`/magic-fee-tier patterns (B3), and Phase 7 is demoted to PROCEDURAL non-gating with explicit v1-complete-without-it semantics (B4). All six concerns (C1–C6) get concrete fixes. The convergent finding with Code Reviewer pass-1 — review-trail enforcement (my C5 + their B3) — is upgraded into a three-part pre-commit hook contract written into Phase 0 SC-4 with on-disk file-existence, freshness, and BLOCKER-absence checks. That is genuine enforcement.

Two residuals remain (R1 = Phase-3-fires-into-Phase-4 timing has a latent inconsistency for in-iteration runs; R2 = HEDGE-05 fixture for Phase-6 null-cost path tests the template, not the Phase-6 cost-leg-failure code path itself), both correctable in the relevant phase PLAN.md and neither blocking commit of the roadmap.

---

## RESOLUTIONS

### B1 — Phase 0 firing forward-reference: FIXED (real)

Pass-1 problem: Phase 0 listed as HEDGE-05 firing scope but the PDF template builds in Phase 4. Loophole: emit an ad-hoc Phase-0 PDF or a markdown stub.

Revision: §HEDGE-05 Firing Scope L189–191 now explicitly states "PDF null-result deliverable not available pre-Phase-4. Phase 0 fires **no** `reports/*.pdf`. Candidate switch or defer happens at memo level." The Phase-0 deliverable is `notes/PHASE_0_GATE.md` (memo). This is a clean separation — no agent reading the roadmap could plausibly emit an ad-hoc PDF here without contradicting the explicit text. **Not nominal.**

### B2 — REPRO-03 numeric threshold: FIXED (real)

Pass-1 problem: "fails" was undefined; CANDIDATES §4.2 leaves the cost-leg-vs-free-tier comparison soft, opening a spec-swap surface (AF-03).

Revision: Phase 0 SC-1 (L49) embeds verbatim "PASS = primary-source evidence shows ≥ 100k Graph queries/mo … STRADDLE = bounds include 100k/mo (fires null-result); FAIL = primary-source bound < 100k/mo (fires null-result). Threshold committed BEFORE Phase 6 first execution; rationale per PITFALLS §6." Three properties make this real, not nominal:
1. **Numeric** (100k/mo), not adjectival.
2. **Pre-committed** by git-log ordering already enforced by SC-1's "BEFORE any commit under `analysis/src/` or `data/raw/`" — the same mechanism that prevents AF-03 prevents tampering here.
3. **Straddle defaults to null-result**, matching PITFALLS §6's explicit "do not split-the-difference into the window" prescription.

The motivated-researcher loophole I worried about (read "~$25/mo" and rationalize "in window, ship it") is now mechanically closed: the threshold is a query-count, not a dollar-amount, and the straddle outcome is the same as the fail outcome.

### B3 — Algorithmic leak-gate scope: FIXED (real, with one residual sub-test gap)

Pass-1 problem: `grep -r "ichi"` is a string-level gate; the genuine failure mode is algorithmic (magic fee-tier `0.0001`, single-owner-per-pool, protocol-name conditional branches).

Revision: Phase 1 SC-5 (L68) introduces a Phase-1 contract test `analysis/tests/test_panel_agnostic.py` that:
- Constructs a panel from a synthetic `protocols/test_fixture.toml` covering "cKES-like + COP-like + a Steer-shaped multi-vault-per-pool layout" — directly addresses the multi-BeaconProxy concern from pass-1.
- Adds a CI lint rejecting `if config.name ==`, `if protocol ==`, `if vault_owner == "ichi"`, **or any hard-coded fee-tier magic number (`0.0001`, `100`, `500`) outside `protocols/*.toml`** — the magic-number leak I named explicitly.

Phase 6 SC-3 (L141) now has two layers: (a) cheap string grep on `fetch/src analysis/src`, (b) Phase-1 contract test continuing to pass. The roadmap labels (b) "load-bearing algorithmic-leak gate" and (a) "cheap pre-commit complement" — correct ordering.

Phase 0 SC-3 (L51) locks Q-9 with: "If unified mode is selected, the V3+V4+Broker pooling code must live in `analysis/src/` from Phase 2 onwards (dead-code-exercised by synthetic unit tests in Iteration 1), not deferred to Phase 6 — otherwise REPRO-02's `git diff fetch/src analysis/src` empty-set invariant is violated." This closes the Iteration-1/Iteration-2 dead-code/live-code asymmetry I flagged.

**Residual sub-test gap:** the magic-number lint catches `0.0001`, `100`, `500` but doesn't enumerate `3000`, `10000` (Uniswap V3 standard fee tiers). Minor — fixable in Phase 1 PLAN.md, not roadmap-blocking. The principle is encoded; the enumeration is incomplete.

### B4 — Phase 7 v1/v2 straddle: FIXED (real)

Pass-1 problem: Phase 7 fired v2-deferred reqs but was listed alongside v1 phases, creating a silent-skip loophole.

Revision: L146 header now reads "**PROCEDURAL phase, listed for continuity, NOT gating v1-completion.** v1 is complete when Phases 0–6 ship (REPORT-01..04 in Phase 5 and REPRO-01..04 in Phase 6 are the v1 closing reqs). Phase 7 fires the *v2-deferred* SYNTH-V2-01 and SYNTH-V2-02 requirements … It MAY be deferred to a follow-on milestone without violating the v1 contract."

This is option (a) from my pass-1 fix (demote Phase 7), executed cleanly. The v1 exit criteria are now unambiguous: Phases 0–6 complete. Phase 7 cannot be silently skipped because there is nothing to skip from a v1 contract perspective.

---

### C1 — Decorative agent assignments: FIXED

- Phase 2 Consult Analytics Reporter: L77 now produces concrete artifact `notes/fx_snap_decision.md` with the four-alternative trade-space enumerated. No longer a one-paragraph sign-off.
- Phase 5 Document Generator: dropped; L121 folds rendering into Technical Writer ("also owns the Quarto/nbconvert rendering pipeline — tool selection, not subtask").

### C2 — Python tooling pins: FIXED

L64 Phase 1 SC-1 appends "`analysis/uv.lock` exists with pinned versions of `tick==0.8.0.2`, `statsmodels==0.14.6`, `polars==1.41`, `numpy==2.4.x`, `scipy==1.17.1` — pinned at Phase 1 (not deferred to Phase 5) because `tick` validation in DGP-01 is non-reproducible without it." Tick is named explicitly with the rationale I gave.

### C3 — Subgraph vs Blockscout data source: FIXED

L66 Phase 1 SC-3 now requires the freshness wrapper to be unit-tested for **both** paths (subgraph + Blockscout RPC) and explicitly states "Phase 1 PLAN.md must explicitly commit to which data-source path is used for the V3 Swap event panel; the wrapper applies to whichever path is chosen." The choice is deferred to PLAN.md, but the *contract* (both wrappers tested) is locked here. Acceptable.

### C4 — Graph budget vs ICHI vault scope: FIXED

L69 Phase 1 SC-6 introduces `pnpm fetch ichi --dry-run --estimate-budget` with a hard rule: "if projection > 30k, the cold-backfill must be re-scoped or budget reallocated from the 20k reserve before any production fetch." The "Halo (now Steer)" mislabel is also corrected in-line: "25k earmark is now Iteration-2 cold-backfill on Steer." Clean.

### C5 — Review-trail enforcement: FIXED (CONVERGENT with Code Reviewer B3 — see CONVERGENT FINDINGS below)

### C6 — Stationarity diagnostic: FIXED

L97 Phase 3 SC-4 appends "**Stationarity diagnostic** (per PITFALLS §4): the held-out segment's mean event rate must be within ±25% of the train segment's, OR the NHPP/Hawkes fits must use a piecewise-constant or spline baseline; the diagnostic is logged in `fit_report.json :: baseline_stationarity_check` with `{train_rate, held_out_rate, ratio, decision: stationary|piecewise_required}`." The ±25% threshold matches my fix verbatim; the JSON schema embeds the decision in the fit artifact (auditable post-hoc).

---

## NEW ISSUES

### R1 (residual, non-blocking) — Phase 3 firing into Phase 4 has a latent ordering issue for in-iteration HEDGE-05

L191–192 §HEDGE-05 Firing Scope says: "Phase 3 — if NHPP-vs-Hawkes is indistinguishable at conventional α … PDF template now exists (built in Phase 4 but Phase 3 fires *into* Phase 4's gate, so Phase 4 actually emits the PDF in this case). In practice Phase 3 sets a flag in `fit_report.json :: dgp_indistinguishable = true` which Phase 4 reads."

This works for Iteration 1 (Phase 3 ships, Phase 4 reads). It does NOT obviously work for Phase-3-equivalent re-runs in Phase 6 (Iteration 2), because Phase 6's pipeline re-runs Phase 2–5 against `protocols/steer.toml`. If Phase 6's Phase-3-equivalent produces `dgp_indistinguishable = true` for Steer, the flag-passing is fine, but the firing-condition labeling in §HEDGE-05 Firing Scope only enumerates "Phase 3" and "Phase 4" by phase number, not by iteration. A reader could plausibly conclude Phase 3 firing condition only applies to Iteration 1.

**Recommendation:** Phase 6 PLAN.md should clarify that Phase-3-equivalent runs in Iteration 2 use the same `dgp_indistinguishable` flag mechanism and emit `reports/steer_null_result.pdf` via the same Phase-4-built template. Roadmap-level fix is unnecessary; PLAN.md-level note suffices.

### R2 (residual, non-blocking) — HEDGE-05 fixture for null_cost tests the template, not the Phase-6 cost-leg-failure code path

L113 Phase 4 SC-5 requires three fixtures at `analysis/tests/fixtures/hedge_05_{null_cost,null_lr,null_convex}/`. Each fixture is a "synthetic `fit_report.json` + `gate_report.json` + `cost_leg_bound.md` triplet." This validates the *template* fires correctly on each input.

But the `null_cost` fixture exercises template-rendering only — it does **not** test the actual Phase-6 code path that reads `notes/steer_cost_leg_bound.md` and decides to emit `reports/steer_null_result.pdf` vs proceed. The decision logic in Phase 6 SC-2 ("the check writes `notes/steer_cost_leg_bound.md` … if the check fails, `reports/steer_null_result.pdf` ships instead") needs its own integration test, distinct from the template fixture.

**Recommendation:** Phase 6 PLAN.md should add an integration test fixture: a synthetic `steer_cost_leg_bound.md` with a FAIL verdict, fed into `make iteration-2-full`, asserting the pipeline exits at the gate (no fetch attempted, `reports/steer_null_result.pdf` emitted). Roadmap-level fix unnecessary.

---

## CONVERGENT FINDINGS

### Review-trail enforcement (my pass-1 C5 + Code Reviewer pass-1 B3): FULL FIX, NOT NOMINAL

Both pass-1 reviews independently flagged that 2-way review discipline was aspirational with no on-disk contract. The revision installs a three-part mechanism in §"Execution discipline" L18–22 + Phase 0 SC-4 (b) L52:

1. **File-location contract:** `.planning/_reviews/<artifact_basename>_{reality_checker,code_reviewer}.md` — names the location, removes ambiguity.
2. **Mandatory header schema:** "`## VERDICT` section as its first H2, with the value PASS / NEEDS REVISION / NEEDS WORK / BLOCKED" — this very file (pass 2) has been written to match.
3. **Pre-commit hook:** "rejects commits modifying `.planning/**/PLAN.md` or `.planning/ROADMAP.md` unless both paired review files exist, are newer than the artifact, and neither carries an unresolved BLOCKER finding. Override flag `--allow-revision` requires an explicit human acknowledgement on a NEEDS REVISION verdict."
4. **Progress-table linkage:** L164 Progress table now has a "Review Status (RC / CR)" column showing `pending / pending` for all phases; L175 below the table makes the rule explicit: "A phase cannot be marked Complete until both paired review files exist under `.planning/_reviews/phase_N_{reality_checker,code_reviewer}.md` AND neither carries an unresolved BLOCKER finding."

The newer-than-artifact check (point 3) is the part that goes beyond nominal — it forces re-review after revisions, not just initial review. Without that timestamp check, an artifact could be re-edited post-review and shipped with stale reviews. The mechanism is real.

### Code Reviewer's other pass-1 blockers: addressed in revision

- **CR-B1 (make orchestrator):** Roadmap still uses `make` targets but the existence of `make report-ichi`, `make verify-reproducibility`, `make leak-check`, `make iteration-2-full`, `make schema-frozen-check`, `make lint-artifacts` is now load-bearing in multiple SCs. STACK.md was the CR recommendation surface — I cannot verify STACK.md was updated without reading it, but the roadmap presupposes Make exists. **Cross-check needed: confirm STACK.md was updated. If not, this CR-B1 is still open.**
- **CR-B2 (viem version pin):** L64 now reads `viem@2.51.0`, `@x402/fetch@2.13.0`, `@graphprotocol/client-x402@1.0.0`, `graphql-request@7.4.0`, `@mento-protocol/mento-sdk@3.2.8` — full semver everywhere. Fixed.
- **CR-B4 (HEDGE-05 fixture under-specification):** L113 now specifies three fixtures with full paths, schemas, and grep-on-PDF-text verification. Fixed (modulo R2 above).
- **CR-D1 (archived agents):** L14 Agent-name resolution paragraph names archived-subtree opt-in semantics. Each archived-agent reference in phase blocks carries an inline "*(archived — explicit opt-in)*" annotation. Fixed.
- **CR-D2 (Phase 0 Model QA consult):** L46 Phase 0 Consult now includes Model QA Specialist as primary author of statistical content. Fixed.
- **CR-D3 (Phase 4 Primary/Consult swap):** L105–106 swaps roles — Model QA Specialist is now Phase 4 Primary; Analytics Reporter is Consult. Fixed.
- **CR-D4 (`_schema.toml` leak risk):** L52 SC-4 (c) adds `make schema-frozen-check` rejecting any diff to `_schema.toml` after the Phase-0 commit hash; L53 SC-5 requires the `data_cost_class` enum to be pre-populated at Phase 0 covering Iteration 1 + Iteration 2 + COPM. Fixed.
- **CR-D5 (Reality Checker double-role on Phase 6):** L137 Audit/Review reads "Code Reviewer + Model QA Specialist (parallel review of the PLAN.md; Reality Checker is *not* on the PLAN.md audit for Phase 6 since they're consumed by the REPRO-03 primary work above — separation of concerns)." Fixed.
- **CR-D6 (Phase 7 zero-requirement orphan):** Resolved jointly with my B4 fix — Phase 7 is now PROCEDURAL/non-gating, the absence of v1 requirements is the design, not a bug.

### Single residual cross-check

**STACK.md `make` addition** is the only Code Reviewer pass-1 item I cannot confirm from the roadmap alone. If STACK.md still lists only `pnpm`, `uv`, `direnv`, `pre-commit`, `gh`, `Node 22` (no `make`), then six `make`-prefixed success criteria in this roadmap have no tool to invoke and CR-B1 is still open. Recommend the orchestrator confirms STACK.md was updated in this same revision pass.

---

## FINAL RECOMMENDATION

**COMMIT.**

The revision converted four blockers and six concerns into mechanically enforced contracts: git-log ordering for pre-registration, pre-commit hook for review trail, CI lint for protocol-agnosticism, Phase-0 schema-freeze hash, numeric query-count thresholds for REPRO-03, and explicit memo-vs-PDF separation for Phase-0 HEDGE-05 firing. The two residuals (R1 in-iteration HEDGE-05 labeling, R2 Phase-6 cost-leg integration test distinct from template fixture) are PLAN.md-level concerns, not roadmap-level. Both reviewers' convergent finding on review-trail enforcement received the strongest fix (three-part hook + Progress-table linkage), which is the right priority weighting.

One final commit-time check: confirm STACK.md now lists `make` (GNU Make 4.x) per Code Reviewer pass-1 B1. If yes, commit. If no, address that single line and then commit — it would not warrant another full review pass.

**Files reviewed:**
- `/home/jmsbpp/apps/d2p/abrigo/abrigo-x402/.planning/ROADMAP.md` (revised, 202 lines)
- `/home/jmsbpp/apps/d2p/abrigo/abrigo-x402/.planning/_reviews/roadmap_reality_checker.md` (my pass 1)
- `/home/jmsbpp/apps/d2p/abrigo/abrigo-x402/.planning/_reviews/roadmap_code_reviewer.md` (Code Reviewer pass 1)

---

*Reality Checker pass 2 complete. VERDICT: PASS with two non-blocking residuals + one external cross-check (STACK.md `make`).*
