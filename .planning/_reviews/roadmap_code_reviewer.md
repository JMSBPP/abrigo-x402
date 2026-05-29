# Code Reviewer: ROADMAP.md

**Reviewer:** Code Reviewer (technical correctness, design coherence, implementability)
**Artifact:** `.planning/ROADMAP.md` @ commit-pending 2026-05-25
**Date:** 2026-05-25

---

## VERDICT

**NEEDS REVISION** — The phase DAG, requirement coverage, and L1→L7 mapping are sound. However four load-bearing technical gaps prevent the roadmap from being executed as written: (1) the build orchestrator (`make`) is referenced six times but absent from STACK.md; (2) the version `viem@2.51` in Phase 1 success criterion 1 is one minor-revision below STACK.md's `2.51.0` — the literal pin should match; (3) the 2-way review discipline has no enforcement mechanism on disk; (4) HEDGE-05's "fixture that forces all four gate conditions to false" is under-specified (no schema, no path). None are conceptual flaws — all are concrete fixes well under a day's editing.

---

## BLOCKERS

### B1. `make` build orchestrator referenced six times but never introduced in STACK.md

ROADMAP.md references the following `make` targets as success criteria:
- L71: `make lint-artifacts` (Phase 2)
- L115: `make report-ichi` (Phase 5)
- L118: `make verify-reproducibility` (Phase 5)
- L127, L131: `make leak-check` (Phase 6)
- L132: `make iteration-2-full` (Phase 6)

STACK.md §"Development Tools" lists `pnpm`, `uv`, `direnv`, `pre-commit`, `gh`, `Node 22`. No `make`. No `just`. No `taskfile`. STACK.md §"Stack Patterns by Variant" gives no build-orchestration story across the TS/Py boundary.

**Implication:** Phase 5 exit gate ("`make verify-reproducibility` exits zero") is unverifiable until someone retrofits a Makefile or equivalent. Either (a) add a "Build orchestration" line to STACK.md naming the tool, OR (b) replace the `make X` invocations with concrete commands (`bash scripts/verify-repro.sh`, `pnpm run leak-check`, etc.).

Recommendation: add to STACK.md "Development Tools": `make` (GNU Make 4.x) for cross-workspace orchestration (TS + Py + Quarto). It is the lowest-friction choice given direnv is already in stack.

### B2. Version pin inconsistency between ROADMAP.md L56 and STACK.md

ROADMAP.md L56 lists `viem@2.51`, `@x402/fetch@2.13`, `@graphprotocol/client-x402@1.0.0`, `graphql-request@7.4`, `@mento-protocol/mento-sdk@3.2.8`.

STACK.md authoritative table (lines 14–32) shows: `viem 2.51.0`, `@x402/fetch 2.13.0`, `@graphprotocol/client-x402 1.0.0`, `graphql-request 7.4.0`, `@mento-protocol/mento-sdk 3.2.8`. The short-form pins in the roadmap (`2.51`, `2.13`, `7.4`) drop the patch digit — under pnpm's default `^` they will resolve fine, but the success criterion as written ("`package.json` lists `viem@2.51`...") will fail a literal string-grep against a lockfile that records `viem@2.51.0`.

Recommendation: either (a) edit L56 to use full semver `2.51.0`, `2.13.0`, `7.4.0`, OR (b) reword the criterion to "the pinned major.minor versions match STACK.md".

### B3. 2-way review discipline (lines 12–14) has no enforcement mechanism

The "Execution discipline" block says: "this ROADMAP.md and every subsequent phase PLAN.md must pass a parallel review by Reality Checker + Code Reviewer before commit. Blocking findings ... force revision; non-blocking findings get TODO trails. Review trail preserved alongside the artifact."

There is no on-disk artifact contract for this. The roadmap should specify:
- The expected location of review trails (e.g., `.planning/_reviews/<artifact_name>_<reviewer>.md`)
- A pre-commit hook entry (or CI check) that blocks a commit modifying `.planning/<n>_*/PLAN.md` unless both `.planning/_reviews/<n>_*_reality_checker.md` and `.planning/_reviews/<n>_*_code_reviewer.md` exist and are newer than the PLAN.md
- The required header schema in each review file (VERDICT field, mandatory)

Without this, "must pass" is aspirational. Phase 0's Success Criterion 4 already mandates a pre-commit hook for the 12 anti-features — extend that same hook to enforce the review trail.

Recommendation: add a Phase 0 sub-criterion: "Pre-commit hook rejects commits to `.planning/**/PLAN.md` unless the two paired review files exist with `VERDICT: PASS` or `VERDICT: NEEDS REVISION` (latter requires explicit `--allow-revision` flag)."

### B4. HEDGE-05 fixture (Phase 4 SC-5, line 103) is under-specified

The success criterion: "tested via a fixture that forces all four gate conditions to false."

Missing:
- Fixture format (JSON? a synthetic `fit_report.json` + `gate_report.json` pair? a mock `panel.parquet`?)
- Path (e.g., `analysis/tests/fixtures/hedge_05_null/`)
- Which gate the fixture exercises (HEDGE-01's four conditions? or the three HEDGE-05 firing conditions (a/b/c) from line 176–180 of REQUIREMENTS.md L54?)

Note also the wording inconsistency: the criterion says "all four gate conditions to false," but the HEDGE-05 firing scope (ROADMAP.md lines 176–180) lists *three* firing conditions (a Phase-0 cost-leg fail, b DGP-03 LR indistinguishable, c HEDGE-01 zero conditions pass). The "four" likely refers to HEDGE-01's four convex-dominance conditions, in which case the criterion should read "a fixture that forces HEDGE-01 to find zero passing conditions" — but that only triggers firing condition (c), not (a) and (b). To exercise HEDGE-05 fully, three fixtures are needed, one per firing condition.

Recommendation: replace SC-5 with: "Three fixtures at `analysis/tests/fixtures/hedge_05_{null_cost,null_lr,null_convex}/` each force one of the three HEDGE-05 firing conditions; running `pytest analysis/tests/test_null_result_template.py` confirms `reports/ichi.pdf` becomes a null-result PDF in each case (verified by grep on the rendered PDF text for the null-result template's signature header)."

---

## CORRECTIONS

### C1. Requirement → phase mapping: walk-through

Result of walking REQUIREMENTS.md against ROADMAP.md "Requirements:" lines:

| REQ | In ROADMAP at | Match |
|---|---|---|
| GOV-01, 02, 03 | L36 (Phase 0) | OK |
| DEMAND-01 | L36 (Phase 0 "verify") + L65 (Phase 2 "enforce") | OK — explicit split annotated |
| FETCH-01..04 | L51 (Phase 1) | OK |
| PANEL-01..04 | L65 (Phase 2) | OK |
| DGP-01..06 | L79 (Phase 3) | OK |
| DEPEND-01, 02 | L94 (Phase 4) | OK |
| HEDGE-01..04 | L94 (Phase 4) | OK |
| HEDGE-05 | L94 (Phase 4, "template, where built") + L124 (Phase 6, "firing condition") | OK |
| REPORT-01..04 | L110 (Phase 5) | OK |
| REPRO-01, 02, 03, 04 | L124 (Phase 6); REPRO-04 *also* in Phase 0 per REQUIREMENTS.md L145 | **Inconsistency**: ROADMAP.md L36 lists "REPRO-04 (decision component)" for Phase 0 and L124 lists "REPRO-04 (enforcement component)" for Phase 6. REQUIREMENTS.md L145 names Phase 0 as REPRO-04's primary phase. Roadmap's framing is OK as long as the split is intentional. |

**Coverage: 32/32 ✓**. No duplicates beyond the explicitly-noted enforce-vs-decide splits. No orphans.

**Minor**: ROADMAP.md L5 says "32/32 v1 requirements mapped (0 orphaned)" — this matches REQUIREMENTS.md L150. Consistent.

### C2. Path-naming inconsistencies

Roadmap mixes `snake_case` and `kebab-case` for note files without a stated rule:

- `notes/PRE_REGISTRATION.md` (UPPER_SNAKE) — L41
- `notes/PHASE_0_GATE.md` (UPPER_SNAKE) — L42
- `notes/Q9_DECISION.md` (UPPER_SNAKE) — L43
- `notes/usdt_depeg_calibration.md` (lower_snake) — L104
- `notes/methodological-refinements.md` (kebab-case) — L27, L144
- `notes/cost_leg_empirical_bounds.md` (lower_snake) — L145
- `notes/tvl_thin_floor_decision.md` (lower_snake) — L146
- `notes/steer_cost_leg_bound.md` (lower_snake) — L130

Recommendation: pick one of `UPPER_SNAKE` (for explicit governance docs) + `lower_snake` (for working notes), drop `kebab-case` entirely. Change `methodological-refinements.md` → `methodological_refinements.md` (two occurrences: L27, L144). Document the convention in PROJECT.md or a new `notes/README.md`.

### C3. `analysis/src/abrigo_x402/...` vs `analysis/src/` collapse

ROADMAP.md uses both:
- L86: `grep -r "likelihood_ratio_test" analysis/src` (top-level)
- L100: `analysis/src/abrigo_x402/hedge/falsification.py` (full)
- L122: "zero edits to `fetch/src/` or `analysis/src/`" (top-level)
- L131: `grep -r "ichi" fetch/src analysis/src` (top-level)

These are fine in mixed contexts (grep root paths vs specific file paths), and the package layout `analysis/src/abrigo_x402/` matches ARCHITECTURE.md L136. No correction needed, but the leak-check on L131 should also include `protocols/_schema.toml` in the *excluded* set (since `_schema.toml` may legitimately mention both `ichi` and `steer` enum values).

Recommendation: edit L131 to clarify: "`grep -ri "ichi" fetch/src analysis/src` returns zero hits; matches inside `protocols/ichi.toml` and `protocols/_schema.toml` comments are explicitly excluded by being outside the searched roots."

### C4. Cross-references — resolve check

Spot-checked the references the roadmap names:
- "per CANDIDATES §4.1" (L42) — resolves to CANDIDATES.md L106 (ICHI heading) ✓
- "per CANDIDATES §6 Q6b" (L124, L180) — resolves to CANDIDATES.md L203 ✓
- "per FEATURES.md TS-09" (L45 in REQUIREMENTS, referenced indirectly via DEPEND-01) — resolves ✓
- "per FEATURES.md D-07" (REQUIREMENTS L59 → REPORT-02 → roadmap L116) ✓
- "per FEATURES.md TS-12 + D-08" (REQUIREMENTS L66 → REPRO-02) ✓
- "per FEATURES.md TS-14" (REQUIREMENTS L61 → REPORT-04) ✓
- "PITFALLS §4" (REQUIREMENTS L41, DGP-06) — not directly traced, but consistent with profile-likelihood ref ✓
- "per memory `feedback_pdf_deliverable.md`" (L108) — outside repo, can't verify from here ⚠

All in-repo cross-refs resolve.

### C5. Phase 5 → Phase 6 dependency: what artifact does Phase 6 actually consume from Phase 5?

ROADMAP.md L123 says "Depends on: Phase 5 (Iteration 1 PDF deliverable must have shipped — gate from PROJECT.md Constraints)". The dependency is a *process gate* (Iteration 1 done before Iteration 2 starts), not an *artifact consumption*. This is correct as written but the wording elsewhere (L169) implies artifact-flow. Make this explicit:

Recommendation: L123 should add: "Phase 6 does not consume any data artifact from Phase 5; the dependency is a discipline gate (REPRO-02 cannot validate the parameter-driven swap until Iteration 1 has actually shipped a complete output set)."

### C6. D-08 negative-control test absent from roadmap

FEATURES.md D-08 (and PITFALLS implications) define an "Iteration-2 dry-run on a known-bad candidate" as the validation substitute for AF-01 (mock-data). REQUIREMENTS.md folds this into REPRO-02 by reference. The roadmap mentions REPRO-02 in Phase 6 (L124) but doesn't surface D-08's *negative control* role — i.e., the Steer cost-leg lower-bound check IS the D-08 dry-run, since it's expected to potentially fail.

This is fine if intentional, but it should be stated. Otherwise a reader executing Phase 6 sees only "run Steer end-to-end" and not "the failure case is the validation."

Recommendation: add to Phase 6 Goal (L122): "Steer's expected-failure path on the cost-leg lower-bound check is itself the FEATURES.md D-08 negative-control validation — null-result emission must be observed at least once across the two iterations to confirm the falsification machinery works."

---

## DESIGN-LEVEL CONCERNS

### D1. Senior Project Manager + Analytics Reporter agents are archived

`/home/jmsbpp/.claude/agents/_archived/project-management/project-manager-senior.md` and `_archived/support/support-analytics-reporter.md` are in the **_archived** subtree. The roadmap names them as Primary Agent for Phase 0 (Senior PM) and Phases 3, 4, 6, 7 (Analytics Reporter). Either:
- the archived agents are still invocable but the operator needs to know they're out of the standard active set, OR
- a replacement should be named (e.g., gsd-planner for Phase 0; Model QA Specialist promoted to primary for Phase 3).

Recommendation: in the Execution discipline section (L11–14), add a note: "Agent names refer to definitions under `~/.claude/agents/` (active + archived subtrees). Where the cited agent is archived, the dispatcher must explicitly opt in to the archived path via `subagent_type` override."

### D2. Phase-0 Primary Agent fit

"Senior Project Manager" for governance artifacts (pre-registration, gate memo, Q9 decision) is *workable* — these are organizational artifacts, not code. But the technical content (kernel forms, prior parameters, test statistics for GOV-01) is statistical, not project-management. A more coherent split: **Senior PM authors the *outline / acceptance regions* + **Model QA Specialist** authors the *kernel forms / test statistics*. The "Consult" line (L38) doesn't currently name Model QA at Phase 0; it should.

Recommendation: edit L38 "Consult" to add **Model QA Specialist** (verifies the pre-registration's statistical content has the correct mathematical form before commit — this is exactly Phase-0-prevention of AF-03 spec-swap).

### D3. Phase 3 + Phase 4 share both Primary (Analytics Reporter) AND Consult (Model QA Specialist) agents

There is no separation-of-concerns between author and auditor across phases 3→4. Phase 4's success criteria critically depend on Phase 3's `fit_report.json` being correct. If the same Analytics Reporter authored both, the auditing surface collapses.

Recommendation: for Phase 4, swap roles — **Model QA Specialist** becomes Primary on the falsification gate + Carr–Madan strip (these are the math-validation-heavy components, matching their charter exactly), and **Analytics Reporter** becomes Consult for the empirical-copula fitting. This pattern is what the agent's documented charter ("audits ML and statistical models end-to-end") actually optimizes for.

### D4. `protocols/_schema.toml` leak risk for Iteration 2

ROADMAP.md L45 says the demand-window definition is "reflected in `protocols/_schema.toml` as a comment + the `data_cost_class` enum." If `data_cost_class` is enumerated (e.g., `["per-event-oracle", "per-scan-ocr", "per-pool-rebalance"]`), adding a Steer-specific value forces a `_schema.toml` edit, which would **violate REPRO-01** ("`protocols/*.toml` is the only file class that changes between iterations" — but `_schema.toml` arguably is in that class).

Two readings possible:
- (a) `protocols/*.toml` includes `_schema.toml` → schema edits are allowed, then REPRO-01 needs to clarify this.
- (b) `_schema.toml` is the *contract* (frozen) and per-protocol `*.toml` are *instances* → adding a new enum value for Steer is a schema edit and violates REPRO-01.

The roadmap does not pick. ARCHITECTURE.md L186–187 says the schema is mirrored in zod + pydantic and CI-checked — implying the schema itself is the contract (reading b). If so, `data_cost_class` should be defined as `string` (free-form) with the *enumeration* enforced at validation-time inside the per-protocol code, OR pre-populated with all expected values (ICHI's + Steer's + COPM + future) at Phase 0.

Recommendation: at Phase 0 success criterion 5 (L45), require that `protocols/_schema.toml` enumerates ALL anticipated `data_cost_class` values for both Iteration 1 and Iteration 2 (per CANDIDATES §6), so that Iteration 2 adds *only* `protocols/steer.toml`, never `_schema.toml`. Add a `make schema-frozen-check` that asserts `_schema.toml` has not been modified since the Phase 0 commit hash.

### D5. Reality Checker is named as both audit/review AND primary on REPRO-03 (Phase 6, L126)

L126: "**Reality Checker** primary on REPRO-03's cost-leg lower-bound check — this is the binding gate for Iteration 2 and Reality Checker's 'needs overwhelming proof' default is exactly the right epistemic posture."

But L127: "Audit/Review: Reality Checker + Code Reviewer (parallel review of the PLAN.md...)"

Reality Checker cannot simultaneously be Primary on a sub-task AND mandatory PLAN.md reviewer for the same phase — they'd be reviewing their own work. Either (a) Reality Checker is consult+primary on the cost-leg check and a *different* agent (e.g., second-pass Code Reviewer + Model QA) does the PLAN.md audit, or (b) Reality Checker steps off the PLAN.md audit role for Phase 6 only.

Recommendation: edit L127 to: "Audit/Review: Code Reviewer + Model QA Specialist (parallel review of the PLAN.md, since Reality Checker is consumed by REPRO-03 primary work this phase)."

### D6. Phase 7 has zero requirements assigned

L139: "Requirements: (none new; this phase is the v2-prep substrate — fires the SYNTH-V2-01 and SYNTH-V2-02 v2 requirements that are intentionally deferred)"

REQUIREMENTS.md L151 confirms "Phase 7 (0)" in distribution. This is internally consistent. But it raises the question: what is Phase 7's *exit* criterion if no v1 requirement gates it? The three success criteria (L144–146) define exit by file existence, which is OK — but they should be named in REQUIREMENTS.md (even as "v1 procedural requirements PROC-01..03 firing in Phase 7") so the 32/32 mapping table isn't subtly hiding a Phase-7-only set of obligations.

Recommendation: either accept Phase 7 as a *procedural* phase (and rename "Requirements: (none new)" → "Requirements: PROC-SYNTH-01..03 (procedural, defined in this phase's plan)") or upgrade those three success criteria into proper v1 requirements at the bottom of REQUIREMENTS.md.

---

## WHAT IT GETS RIGHT

1. **The L0→L7 ARCHITECTURE.md "Build Order" maps cleanly to phases 1→5.** No skipped layers, no out-of-order dependencies. Phase 4 correctly fuses L5 (dependence) + L6 (hedge), which matches the optional-L5 note in ARCHITECTURE.md L373.

2. **The "Iteration-2 swap surface" invariant is operationalized concretely.** REPRO-01's `grep -r "ichi"` enforcement at L131 is the right mechanism — it converts a design principle into a CI-checkable assertion. Phase 6 SC-4 `git diff fetch/src analysis/src` returning empty between iteration-complete commits is the cleanest possible test of swap-surface integrity.

3. **HEDGE-05 firing scope (L176–180) is enumerated explicitly.** Most pipelines hand-wave null-result paths; this one names three firing conditions and the phase each fires in. The placement at the bottom of ROADMAP.md (outside per-phase blocks) avoids duplication.

4. **The USDT-not-USDC reframe is honored throughout.** Phase 4 SC-2 (L100) explicitly requires `grep -i "usdc" ... falsification.py` to return only comparison/historical hits. This catches the most common form of the substitution bug.

5. **Phase 0's pre-commit hook for anti-features (L44) is the correct enforcement layer.** AF-03 (spec swap after seeing results) is genuinely impossible to prevent without commit-ordering proof — pinning it to git log is the right move.

6. **Phantom-transfer filter requires a real on-chain fixture (Phase 2 SC-4, L73).** This is the highest-value test in the roadmap; STACK.md §"Critical Pitfalls" item 5 calls it "the single biggest source of false self-excitation if missed." Roadmap correctly elevates it to phase-exit gate.

7. **Cost-ledger soft-cap discipline (Phase 1 SC-2, L57) at 90k with explicit `--force` opt-out.** Matches FETCH-02 + ARCHITECTURE.md L225 exactly. The 10k headroom is sized appropriately for the contingency budget in ARCHITECTURE.md §"Free-Tier Resource Budget".

8. **Reproducibility manifest with `uv.lock` SHA + `package-lock.json` SHA + per-artifact checksums (L118)** is the right level of paranoia for a research deliverable. TS-14 matches.

9. **The 8-phase granularity is justified** — collapsing 0+1 into one phase would lose the pre-registration commit-ordering proof; collapsing 5+6 would lose the swap-surface validation point. Each phase ships a distinct verifiable artifact.

---

## SUMMARY OF REQUIRED EDITS

| # | Location | Edit |
|---|---|---|
| B1 | STACK.md §Dev Tools | Add GNU Make 4.x as build orchestrator |
| B2 | ROADMAP.md L56 | Change pinned versions to full semver (`2.51.0`, `2.13.0`, `7.4.0`) OR reword criterion |
| B3 | ROADMAP.md Phase 0 SC | Add pre-commit hook for paired review trail enforcement; specify `.planning/_reviews/<n>_*_{reality,code}.md` layout |
| B4 | ROADMAP.md L103 | Replace single-fixture criterion with three fixtures per HEDGE-05 firing condition |
| C2 | ROADMAP.md (multiple) | Unify note-file naming: rename `methodological-refinements.md` → `methodological_refinements.md` |
| C3 | ROADMAP.md L131 | Clarify leak-check excludes `protocols/_schema.toml` |
| C5 | ROADMAP.md L123 | Annotate Phase 5→6 dependency as process gate, not artifact flow |
| C6 | ROADMAP.md L122 | State that Steer cost-leg-fail expectation is the D-08 negative control |
| D1 | ROADMAP.md L11–14 | Note that archived-agent names require explicit `subagent_type` opt-in |
| D2 | ROADMAP.md L38 | Add Model QA Specialist to Phase 0 Consult |
| D3 | ROADMAP.md L96 | Swap Primary/Consult between Analytics Reporter and Model QA on Phase 4 |
| D4 | ROADMAP.md L45 / REPRO-01 | Pre-populate `data_cost_class` enum to cover all anticipated iterations; add `make schema-frozen-check` |
| D5 | ROADMAP.md L127 | Remove Reality Checker from Phase 6 PLAN.md audit (they're primary on REPRO-03); substitute Model QA |
| D6 | REQUIREMENTS.md or ROADMAP.md L139 | Either add PROC-SYNTH-01..03 to v1, or explicitly flag Phase 7 as procedural-only |

None of these are conceptual — all are concrete textual fixes. After they're applied, the roadmap is ready to execute.

---

*Code Reviewer review complete. Paired review by Reality Checker required before commit per ROADMAP.md L13.*
