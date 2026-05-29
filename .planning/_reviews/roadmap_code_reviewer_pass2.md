# Code Reviewer: ROADMAP.md — Pass 2

**Reviewer:** Code Reviewer (technical correctness, design coherence, implementability)
**Artifacts (revised):** `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/research/STACK.md`
**Prior review:** `.planning/_reviews/roadmap_code_reviewer.md` (4 blockers + 6 corrections + 6 design concerns)
**Date:** 2026-05-25

---

## VERDICT

**PASS** — All four prior blockers are resolved with verifiable on-disk text. Five of six corrections are addressed; C2 (path-naming inconsistency) is partially addressed (the `methodological-refinements.md` → `methodological_refinements.md` rename is applied at ROADMAP L35 and REQUIREMENTS L88, but no `notes/README.md` documents the convention — non-blocking nit). All six design concerns are addressed in-text. One **new minor inconsistency** introduced by the Phase 7 demotion is flagged below (NEW-1: REQUIREMENTS L153 phase-distribution arithmetic vs Phase 4 SC count), but it is a cosmetic accounting glitch, not a load-bearing defect. 32/32 v1 coverage is preserved.

The roadmap is ready to execute.

---

## RESOLUTIONS

### B1. `make` build orchestrator — RESOLVED

STACK.md L100 now contains:
> `make` (GNU Make 4.x) | Cross-workspace build orchestrator (TS + Python + Quarto) | Phase orchestration targets (`make lint-artifacts`, `make report-ichi`, `make verify-reproducibility`, `make leak-check`, `make iteration-2-full`, `make schema-frozen-check`) per ROADMAP.md success criteria

All six `make` targets referenced in ROADMAP are enumerated. Tool, version family, and purpose are explicit. Verified.

### B2. Version-pin patch digits — RESOLVED

ROADMAP L64 (Phase 1 SC-1) now reads:
> `package.json` lists `viem@2.51.0`, `@x402/fetch@2.13.0`, `@graphprotocol/client-x402@1.0.0`, `graphql-request@7.4.0`, `@mento-protocol/mento-sdk@3.2.8` at the full semver pins matching STACK.md exactly

Full semver. Matches STACK.md L14–32 byte-for-byte for the named packages. The criterion adds a Python lockfile complement (`analysis/uv.lock` with `tick==0.8.0.2`, `statsmodels==0.14.6`, `polars==1.41`, `numpy==2.4.x`, `scipy==1.17.1`) with the right justification (DGP-01 validation requires `tick` pinned at Phase 1, not deferred). Resolved.

### B3. Review-trail enforcement — RESOLVED

ROADMAP L18–22 now specifies the on-disk contract explicitly:
- Path layout: `.planning/_reviews/<artifact_basename>_reality_checker.md` + `..._code_reviewer.md`
- Required header: `## VERDICT` as first H2, values `PASS / NEEDS REVISION / NEEDS WORK / BLOCKED`
- Pre-commit hook enforcement (introduced in Phase 0 SC-4(b)) rejects commits to `.planning/**/PLAN.md` or `.planning/ROADMAP.md` unless paired files exist, are newer than the artifact, and carry no unresolved BLOCKER
- Override flag `--allow-revision` for NEEDS REVISION verdicts
- Progress table cannot mark a phase Complete until both review files exist

Phase 0 SC-4 (L52) now packs three independent layers into one pre-commit config: (a) 12 anti-features, (b) review-trail contract, (c) `make schema-frozen-check`. Layer (b) is exactly what B3 demanded. This file (`_pass2.md`) itself complies — `## VERDICT` is the first H2. Resolved.

### B4. HEDGE-05 fixture — RESOLVED

ROADMAP L113 (Phase 4 SC-5) is fully rewritten:
> **Three fixture sets** at `analysis/tests/fixtures/hedge_05_{null_cost,null_lr,null_convex}/` each force one firing condition (synthetic `fit_report.json` + `gate_report.json` + `cost_leg_bound.md` triplet per fixture); `pytest analysis/tests/test_null_result_template.py` confirms `reports/ichi.pdf` is regenerated as a null-result PDF in each case (verified by grep on the rendered PDF text for the null-result template's signature header).

One fixture per HEDGE-05 firing condition (a/b/c). Paths are concrete. Fixture schema is specified (the triplet). Pytest target is named. Verification mechanism (grep on rendered PDF text) is specified. Resolved.

### C1. Requirement→phase mapping — RESOLVED

Walked again. 32 v1 requirements map to phases as follows: Phase 0 (GOV-01..03 + DEMAND-01-verify + REPRO-04-decision = 5), Phase 1 (FETCH-01..04 = 4), Phase 2 (PANEL-01..04 + DEMAND-01-enforce = 4 unique), Phase 3 (DGP-01..06 = 6), Phase 4 (DEPEND-01..02 + HEDGE-01..05 = 7), Phase 5 (REPORT-01..04 = 4), Phase 6 (REPRO-01..03 + REPRO-04-enforce + HEDGE-05-fire = 3 unique), Phase 7 (0). Total 5+4+4+6+7+4+3+0 = 33 surface count, 32 unique (DEMAND-01 split across 0+2; REPRO-04 split across 0+6; HEDGE-05 re-fires in 6; all annotated). REQUIREMENTS.md L153 reports the same distribution. Coverage 32/32 preserved.

### C2. Path-naming inconsistency — PARTIALLY RESOLVED

`methodological-refinements.md` → `methodological_refinements.md` rename applied at ROADMAP L35 and REQUIREMENTS L88 (kebab-case gone). All other note files are `UPPER_SNAKE` (governance) or `lower_snake` (working notes), consistent with the recommendation. The `notes/README.md` documenting the convention was not created — non-blocking nit, can be deferred.

### C3. `_schema.toml` exclusion from leak-check — RESOLVED

ROADMAP L141 (Phase 6 SC-3a) explicitly states:
> matches inside `protocols/*.toml` and `protocols/_schema.toml` comments are explicitly excluded by being outside the searched roots

Resolved. The two layers (string-grep cheap; protocol-agnosticism contract test at Phase 1 SC-5 = load-bearing) are correctly named and ordered.

### C4. Cross-references — RE-VERIFIED

Spot-checked the new references introduced by the revision:
- "per memory `feedback_specialized_agent_per_subtask`" (L12, L14) — outside-repo memory, can't verify from here but consistent with prior pattern
- "PITFALLS §6" (L49) — referenced for REPRO-03 threshold rationale
- "PITFALLS §4" (L97 stationarity diagnostic) — referenced for held-out drift check

All in-repo refs (CANDIDATES §4.1, §6 Q6b, ARCHITECTURE Build Order, FEATURES TS-09/D-07/TS-12/D-08/TS-14, PROJECT.md Constraints) continue to resolve as in pass 1.

### C5. Phase 5→6 dependency framing — RESOLVED

ROADMAP L133 now reads:
> Depends on: Phase 5 (Iteration 1 PDF deliverable must have shipped — *process gate*, not artifact consumption; Phase 6 consumes no data artifact from Phase 5, but REPRO-02 cannot validate the parameter-driven swap until Iteration 1 has actually shipped a complete output set)

Exactly the requested annotation. Resolved.

### C6. D-08 negative-control framing — RESOLVED

ROADMAP L132 (Phase 6 Goal) explicitly states:
> **Steer's expected-failure path on the cost-leg lower-bound check is itself the FEATURES.md D-08 negative-control validation** — null-result emission must be observed at least once across the two iterations to confirm the falsification machinery works in practice.

Resolved.

### D1. Archived-agent disambiguation — RESOLVED

ROADMAP L14 ("Agent-name resolution") flags Senior PM and Analytics Reporter as archived with explicit `subagent_type` opt-in. Each phase that lists an archived agent annotates it inline (e.g., L45 `**Senior Project Manager** *(archived — explicit subagent_type opt-in required)*`, L77 same for Analytics Reporter, L122 / L135 / L151 likewise). Resolved.

### D2. Phase 0 Consult adds Model QA — RESOLVED

ROADMAP L46 ("Consult") now leads with:
> **Model QA Specialist** (authors the statistical content inside PRE_REGISTRATION.md — kernel forms, prior parameters, test statistics, REPRO-03 numeric thresholds — this is exactly Phase-0-prevention of AF-03 spec-swap)

The author/auditor split is now correct for governance-vs-statistics content. Resolved.

### D3. Phase 4 Primary/Consult swap — RESOLVED

ROADMAP L105 (Phase 4 Primary):
> **Model QA Specialist** (falsification gate math + Carr–Madan grid convergence + USDT-depeg jump-leg calibration + three-way independence/fitted-joint/comonotone stress test ... separation-of-concerns from Phase 3's Analytics Reporter primary)

ROADMAP L106 (Consult): Analytics Reporter, demoted to consult for empirical-copula fitting.

Author/auditor separation between Phase 3 (Analytics Reporter primary) and Phase 4 (Model QA primary) is achieved. Resolved.

### D4. `_schema.toml` pre-populated enum + frozen-check — RESOLVED

ROADMAP L53 (Phase 0 SC-5):
> The enum MUST be pre-populated at Phase 0 with all values anticipated across Iteration 1 + Iteration 2 + COPM mixing-class ... so that Iteration 2 adds *only* `protocols/steer.toml`, never edits `_schema.toml` — enforced by the schema-frozen check in SC-4

ROADMAP L52 (Phase 0 SC-4(c)) defines `make schema-frozen-check` rejecting any diff to `_schema.toml` after the Phase 0 commit hash recorded in `notes/PHASE_0_GATE.md`. The `make` target appears in STACK.md L100. Resolved end-to-end.

### D5. Reality Checker double-booking on Phase 6 — RESOLVED

ROADMAP L137 (Phase 6 Audit/Review):
> **Code Reviewer + Model QA Specialist** (parallel review of the PLAN.md; Reality Checker is *not* on the PLAN.md audit for Phase 6 since they're consumed by the REPRO-03 primary work above — separation of concerns

Resolved with the explicit rationale.

### D6. Phase 7 demotion — RESOLVED

This is the most material change. Verifying it correctly preserves 32/32 v1 coverage:

- ROADMAP L146 marks Phase 7 explicitly: `**Status**: **PROCEDURAL phase, listed for continuity, NOT gating v1-completion.** v1 is complete when Phases 0–6 ship (REPORT-01..04 in Phase 5 and REPRO-01..04 in Phase 6 are the v1 closing reqs).`
- ROADMAP L150: "Requirements: (no v1 requirements; fires v2 SYNTH-V2-01 + SYNTH-V2-02 only)"
- REQUIREMENTS.md L90: "Note on Phase 7: ... Phase 7 may be deferred to a follow-on milestone without violating the v1 contract; running it in this milestone is optional substrate for the next iteration cycle."
- REQUIREMENTS.md L153 phase distribution: "Phase 7 (0; consumes prior results, fires deferred v2 SYNTH reqs)"
- Progress table (L173): Phase 7 row labeled "(procedural, non-gating)"
- HEDGE-05 Firing Scope section (L189–196) still includes Phase 6 as a firing site (the binding one for Iteration 2), independent of Phase 7

The demotion is *internally* consistent: nothing in Phases 0–6 depends on a Phase-7 artifact. All 32 v1 requirements land in Phases 0–6. The two v2 SYNTH requirements that Phase 7 would fire are correctly excluded from the v1 count.

---

## NEW ISSUES (introduced by the pass-1→pass-2 edits)

### NEW-1 (minor accounting glitch — not blocking)

REQUIREMENTS.md L153 phase distribution sum reports "Phase 0 (5) + Phase 1 (4) + Phase 2 (4) + Phase 3 (6) + Phase 4 (7) + Phase 5 (4) + Phase 6 (3) + Phase 7 (0)" = **33**, but coverage states 32 unique. The "extra" comes from HEDGE-05 being counted in Phase 4 (template build) while REPRO-04 is split-counted (Phase 0 decision + Phase 6 enforcement) but DEMAND-01 split (Phase 0 verify + Phase 2 enforce) is counted only once.

This is **not a coverage bug** — it's an arithmetic-presentation glitch in the distribution line. The Traceability table (L113–147) lists each REQ exactly once with a single Primary Phase, summing to 32. Recommend a one-line edit at L153 to either:
- "Phase distribution (primary-phase only): Phase 0 (5) + Phase 1 (4) + Phase 2 (4) + Phase 3 (6) + Phase 4 (7) + Phase 5 (4) + Phase 6 (2) + Phase 7 (0) = 32" (counting REPRO-04 primary in Phase 0, not Phase 6), OR
- accept the secondary-scope double-counting and note explicitly "33 surface entries, 32 unique requirements (REPRO-04 split-counted as Phase 0 + Phase 6)."

Either edit is one line; nothing downstream breaks. Non-blocking.

### NEW-2 (consistency check — no action required, just noted)

ROADMAP L64 (Phase 1 SC-1) extends scope by also requiring Python lockfile pins. This is **good** (resolves the latent risk that DGP-01 validation needs `tick` pinned before Phase 3) but it expands Phase 1's surface beyond FETCH-01..04. The REQUIREMENTS table maps FETCH-01 → Phase 1, and FETCH-01's text (L22) only names the TS pins. The Python pins are implicit. This is fine because Phase 1 SC-1 is an *exit criterion* (broader than any single requirement), but a future reader walking REQUIREMENTS → ROADMAP may not see the Python-pin obligation traced from a REQ.

Recommend (optional, can defer): a one-line note in REQUIREMENTS.md FETCH-01 mentioning that the Python lockfile pin is also obligated at Phase 1 SC-1. Non-blocking.

### NEW-3 (referenced agent doc — verify before dispatch)

ROADMAP L91 names "**Model QA Specialist**" as the Phase 3 consult/audit. This agent now appears in 5 phases (0, 3, 4, 6, 7). I have not verified the agent definition exists under `~/.claude/agents/`. Pass-1 noted Senior PM and Analytics Reporter are archived; Model QA Specialist may or may not be active. The dispatcher should verify before invoking. Non-blocking for the document itself.

---

## FINAL RECOMMENDATION

**Merge / commit the revised ROADMAP.md, REQUIREMENTS.md, STACK.md trio.** All four prior blockers are cleared, the design concerns are addressed in-text with explicit rationale, and the Phase 7 demotion is internally consistent (32/32 preserved, Phases 0–6 self-contained, v2 deferral pathway documented). The single new finding (NEW-1) is a one-line arithmetic clarification and does not gate the artifact.

Suggested follow-up edits, all non-blocking:
1. Add a one-line clarification at REQUIREMENTS.md L153 reconciling the 33-vs-32 phase-distribution count.
2. Add a `notes/README.md` documenting the `UPPER_SNAKE` (governance) vs `lower_snake` (working notes) convention.
3. Optional: trace the Python-lockfile pin at Phase 1 SC-1 back to REQUIREMENTS.md FETCH-01 as a secondary obligation.

After the paired Reality Checker pass-2 review reaches the same verdict, the ROADMAP is ready to commit per the L18–22 review-trail contract.

---

*Code Reviewer pass-2 review complete. Paired Reality Checker pass-2 review required before commit per ROADMAP.md L18–22.*
