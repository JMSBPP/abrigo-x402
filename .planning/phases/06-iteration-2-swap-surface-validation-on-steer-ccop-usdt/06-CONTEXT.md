# Phase 6: Iteration-2 Swap-Surface Validation on Steer (cCOP/USDT) - Context

**Gathered:** 2026-05-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Re-run the *same* Phase 2–5 pipeline on Steer Protocol's cCOP/USDT swap surface using a **config-swap only** (`protocols/steer.toml`), with **zero edits to `fetch/src` or `analysis/src`** — validating the parameter-driven swap-surface invariant (REPRO-01/02). The cost-leg lower-bound check (REPRO-03) runs as the first step; the deliverable is `reports/steer.pdf` (positive) or `reports/steer_null_result.pdf` (null). Steer's expected cost-leg failure is the FEATURES.md D-08 negative-control validation — observing the null-result path fire at least once confirms the falsification machinery works in practice.

Clarifies HOW to implement this re-run/validation. New capabilities (substitute candidate execution, CI infra) are out of scope or future-milestone.
</domain>

<decisions>
## Implementation Decisions

### Cost-leg straddle adjudication (REPRO-03 — the binding first-step gate)
- Steer's data-demand estimate is a **STRADDLE**: `steer.toml` records `celo_attributable_queries_per_mo_lower_bound = 30000` against `demand_window_lower_bound_queries_per_mo = 100000` (Graph free-tier ceiling, canonical DEMAND-01). The 30k–100k band includes the 100k line but is not strictly above it.
- **Decision rule: a straddle (not strictly ABOVE the 100k lower bound) → cost-leg FAILS → fire HEDGE-05 condition (a) `null_cost`.** Steer is the honest D-08 negative control; the null firing is the intended validation, not a disappointment.
- **The straddle decision rule is PRE-REGISTERED now (before any Steer fetch) and applied to the existing pre-committed 30k–100k band as-is.** No re-estimation, no fresh enumeration to narrow the band. Phase 6 only OBSERVES the verdict — it never re-estimates demand to chase pass/fail (AF-03). The rule must be written to `notes/PRE_REGISTRATION.md` and `notes/steer_cost_leg_bound.md` BEFORE the check executes; commit ordering must show the rule predates the verdict.

### Resolution on cost-leg failure (REPRO-03)
- Iteration 2's resolution policy on the Steer null is **SUBSTITUTE a replacement candidate** (not defer-and-close).
- **The substitute candidate is NOT named or executed in this milestone** — it is a future-milestone decision. Phase 6 ships the Steer null-result deliverable and records the disposition as "substitute pending (future milestone)."
- **AF-03 guardrail (MANDATORY for the future milestone, recorded here so it is not lost):** any future substitute candidate MUST be pre-registered BEFORE its own data is seen. Choosing a substitute *after* observing Steer's null without pre-registration would be candidate-shopping — forbidden. Phase 6 does NOT pre-register a specific substitute (per user decision), so the future milestone owns that pre-registration.

### Pipeline execution on the (expected) null
- **The full Phase 2–5 pipeline RUNS on Steer cCOP/USDT regardless of the cost-leg fail** — it is not short-circuited. This mirrors how ICHI emitted `null_strip_unavailable` from *inside* its completed run.
- Rationale: the full re-run is what demonstrates the **REPRO-02 zero-edit swap-surface invariant** — `git diff fetch/src analysis/src` between the Iteration-1-complete baseline and Iteration-2-complete MUST be empty. `null_cost` is then fired from inside the gate report, as one possible OUTPUT of the run.
- This resolves the apparent ROADMAP SC-2 ("exits cleanly on cost-leg fail") vs SC-4 ("`make iteration-2-full` runs Phase 2–5 and produces steer.pdf OR steer_null_result.pdf") tension in favor of the full re-run: the cost-leg verdict is a field in the gate report, not a pre-fetch short-circuit. Free-tier fetch budget for the cCOP/USDT V3 anchor pull is accepted.

### Null-result deliverable (REPORT-01 re-fires for Iteration 2)
- **Renderer: fix + use the generic HEDGE-05 `render_null_result_pdf`** (`analysis/src/abrigo_x402/hedge/null_result.py`) — its originally-intended purpose. This folds the tracked follow-up bug (relative template path + papermill `-P` dependency; see `_artifacts` ref below) INTO Phase 6 and gives the null-result template its first production use.
- **CRITICAL SEQUENCING (REPRO-02 preservation):** fixing `render_null_result_pdf` is an edit to `analysis/src`, which would otherwise violate the REPRO-02 "empty `git diff` on `fetch/src` + `analysis/src`" invariant. Therefore the generic-renderer fix MUST land as a **standalone pre-Iteration-2 baseline maintenance commit**, and the Iteration-1-complete→Iteration-2-complete empty-diff window is measured AFTER that fix. The fix is GENERIC (no `ichi`/`steer` identifiers — must pass `grep -r "ichi" fetch/src analysis/src` = 0). The protocol-agnosticism lint (SC-5) must still pass.
- **Depth: cost-leg headline + DGP/gate results as supporting material.** The PDF headlines the disqualifying cost-leg evidence (straddle 30k–100k → `null_cost`) as the gating verdict, but INCLUDES the full DGP/Hawkes/gate output the re-run produced (since the pipeline actually ran) plus an explicit REPRO-02 zero-edit attestation. Honest and complete, not a stub.

### Research-surfaced collision resolutions (REPRO-02 honesty — locked 2026-05-29)
Three collisions surfaced by 06-RESEARCH.md threaten an honest REPRO-02 "empty-diff" pass. All resolved on the honest-not-convenient path:

1. **REPRO-01 grep (54 `ichi` hits, mostly comments/docstrings).** The literal `grep -ri ichi fetch/src analysis/src` = 0 is an over-strict proxy; the load-bearing gate is the SC-5 no-protocol-branch lint. **Resolution: scrub the genuine coupling (collision 2) + reconcile REPRO-01 to its INTENT** — SC-5 algorithmic-leak lint + a scoped grep that excludes comments/docstrings — **documented via an explicit AF-12 pre-registration note** (NOT silent). The narrowing is transparent and recorded in `notes/PRE_REGISTRATION.md`.
2. **`cli.py:67` hardcodes `data/raw/ichi/<pool>`.** The one genuine functional protocol-coupling. **Resolution: generalize the path to derive `data/raw/<protocol>/` from `--protocol-toml`, landed as a STANDALONE pre-Iteration-2 baseline commit** (same pattern as the renderer fix), so the iter1→iter2 REPRO-02 empty-diff window starts AFTER it. Generic, leak-clean.
3. **Q9 unified-panel + cross-class permutation modules never built** (Phase-0 SC-3 mandated them as dead-code in `analysis/src/.../panel/`; no `panel/` package exists). **Resolution: pre-register (before the fit) that the unified-panel fallback is DEFERRED with an honest signal-scope caveat** — V3-only ~600/30d is 2× the 300-event floor so trigger-1 (sample<300 OR CI>0.4) likely won't fire; the SC-3 dead-code modules were never built. AF-03 clean (pre-registered, admits the gap). If a fallback trigger DID fire, the honest outcome is a documented "fallback-unavailable" note, NOT new code mid-iteration.

**Baseline-commit sequence (all generic, leak-clean, pre-Iteration-2):** renderer `-P`→`-M` + path fix (Decision 4) + materialize path generalization (collision 2) + any coupling scrub (collision 1) land FIRST as maintenance commits; the REPRO-02 empty-diff is measured from that re-baselined HEAD forward.

### Claude's Discretion
- Where the cost-leg first-step check physically lives such that it runs first WITHOUT editing `fetch/src`/`analysis/src` (likely a `scripts/` tool or a `make iteration-2-full` Makefile step that reads `steer.toml`'s pre-committed band + applies the pre-registered straddle rule + writes `notes/steer_cost_leg_bound.md`). Researcher to confirm existing cost-leg machinery vs. new scripts/-level glue.
- Exact `make iteration-2-full` target wiring and the leak-check (`make leak-check`) enforcement mechanism (pre-commit hook vs. CI — note: no CI currently exists in the repo).
- Null-result PDF reproducibility treatment (mirror the ichi content-check / SOURCE_DATE_EPOCH determinism approach where applicable).
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Panel construction (LOCKED — REPRO-04)
- `notes/Q9_DECISION.md` — cCOP panel decision: V3-anchor-only primary (pool `0x2AC5baA668A8A58FD0e302B9896717484fd217B0`, ~580–625 swaps/30d) + pre-registered V3+V4+Broker unified fallback with a two-condition switch trigger (sample<300 OR profile-likelihood CI width>0.4) AND (cross-class permutation p>0.05). AF-03 locked — spec swap after seeing data is forbidden.
- `notes/PRE_REGISTRATION.md` §Q-9 Fallback Pre-Registration — must agree numerically with Q9_DECISION; the straddle decision rule (this phase) is appended here BEFORE the check runs.

### Protocol-spec layer (the only file class that changes)
- `protocols/steer.toml` — Iteration-2 swap surface; Phase-0 scaffolding: factory `0x116Dba5DcE9CcDA828218b7eB46406810632014C`, anchor pool, 3 verified cCOP/USDT vaults, V4 PoolManager `0x288dc841…` + Mento V2 Broker `0x777A8255…` fallback addresses, `cost_leg_lower_bound_verified=false` STRADDLE comment, `panel_construction="v3-anchor-only"`, demand-window fields.
- `protocols/ichi.toml` — Iteration-1 reference surface (the comparison baseline).
- `protocols/_schema.toml` — frozen schema; the schema-frozen pre-commit check rejects diffs to it post-Phase-0 (substrate expansion is a toggle, not a row addition).

### Requirements + roadmap
- `.planning/REQUIREMENTS.md` — DEMAND-01 (demand window `[100k Graph queries/mo free-tier, $390/mo Dune Plus]`, indexer-analytics only, Forno excluded); HEDGE-05 (firing conditions, (a) cost-leg = leading for Steer); REPRO-01..04 (leak gate, parametric re-run, cost-leg first-step, panel-construction lock).
- `.planning/ROADMAP.md` §Phase 6 — success criteria (SC-1 steer.toml populated; SC-2 cost-leg first step; SC-3 two-layer leak gate; SC-4 `make iteration-2-full` empty-diff; SC-5 Q9 pooling test if unified).

### Falsification + negative-control framing
- `notes/CANDIDATES.md` §6 Q6b (cost-leg as leading firing condition) + §7.3 (corrected cCOP volume counts, hidden-volume audit) — primary-source volume/cost basis. *(planner: confirm exact path under notes/.)*
- FEATURES.md D-08 (negative-control: null must be observed ≥once) + TS-12 (parametric re-runnability) — *(planner: confirm exact path.)*

### Null-result renderer (fix in-scope this phase)
- `analysis/src/abrigo_x402/hedge/null_result.py` — generic `render_null_result_pdf` (HEDGE-05 template) to FIX + use.
- `.planning/phases/05-reporting-iteration-1-pdf-deliverable-l7/_artifacts/FOLLOWUP_generic_null_result_renderer_bug.md` — the documented bug (relative path + papermill `-P`) and acceptance criteria for the fix.
- `reports/ichi.qmd` + `Makefile` (`report-ichi`, `verify-reproducibility`) — Iteration-1 render machinery: SOURCE_DATE_EPOCH determinism + PDF content-check + AF-03 greps; reuse the content-check/determinism patterns for the steer null PDF.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `render_null_result_pdf` (`hedge/null_result.py`): the generic HEDGE-05 null-result PDF renderer — to be repaired (path + papermill) and used for steer; carries the visible H1 + `HEDGE05-NULL-RESULT-V1` dual-signature.
- HEDGE-05 firing-decision tree (`decide_firing_condition`, Phase 4 / Plan 04-08): already routes the four firing conditions incl. `null_cost`.
- The full Phase 2–5 orchestration (`analysis/src/abrigo_x402/{panel.py, dgp/, dependence/, hedge/}`, `cli.py`; `fetch/src/*` incl. `protocol-spec.ts`) — driven by the protocol TOML; FROZEN (no edits except the standalone generic-renderer baseline fix).
- ichi render/verify machinery (`Makefile report-ichi` + `verify-reproducibility` content-check, SOURCE_DATE_EPOCH determinism) — pattern to reuse for the steer null PDF reproducibility.

### Established Patterns
- **Protocol config-swap:** `protocols/*.toml` → `protocol_spec.load_protocol` (Python) / `protocol-spec.ts` (fetch). Swapping the TOML is the entire iteration delta.
- **Leak gate (two layers):** `grep -ri "ichi" fetch/src analysis/src` = 0 + the SC-5 protocol-agnosticism lint (rejects `if config.name ==`, magic fee-tiers, single-owner-per-pool); `make leak-check` is the intended CI/pre-commit complement.
- Pattern I (thread-pinned BLAS before numpy), Pattern H (content-addressed run_id), Pattern F (canonical-LL single source) — carry into the Steer re-run unchanged.

### Integration Points
- New `make iteration-2-full` target invokes the same Phase 2–5 pipeline against `protocols/steer.toml`; the cost-leg first-step check + `notes/steer_cost_leg_bound.md` write precede it (timestamped commit ordering).
- The cost-leg check must live OUTSIDE `fetch/src`/`analysis/src` (scripts/ or Makefile glue) to preserve the empty-diff invariant; researcher to confirm whether generic cost-leg machinery already exists.
- `reports/steer_null_result.pdf` is a new `reports/` artifact (allowed — `reports/` is outside the frozen source dirs).
</code_context>

<specifics>
## Specific Ideas

- The cost-leg straddle (30k–100k vs the 100k free-tier line) is the concrete instance of the wider "tokenized data-flow" cost leg: when free-tier data access is exhausted, access crosses toward the `$390/mo Dune Plus` paid threshold. Steer's demand straddling that line — neither clearly free nor clearly paid — is exactly why the conservative-fail rule + honest `null_cost` is the right call.
- "Null results are valid completions, not failures" (HEDGE-05) — the steer null PDF is a real deliverable, headlining the disqualifying evidence with the full re-run output as support.
- The free→$390 subscription crossover is itself a discontinuous step (its own convexity on the cost side) — noted as a v2/synthesis theme, not built here.
</specifics>

<deferred>
## Deferred Ideas

- **Substitute candidate execution** (e.g. cNGN/USDT) — Iteration 2's resolution on the Steer null is "substitute," but the named candidate + its run is a FUTURE MILESTONE, pre-registered before its data is seen (AF-03).
- **CI wiring for `make leak-check` + `verify-reproducibility`** — no CI exists in the repo today (flagged by the Phase-5 DevOps review); making these required CI checks is a project-wide infra follow-up, not Phase 6.
- **Cost-side convexity modeling** (the free→paid subscription step as a convex exposure) — Phase 7 / v2 synthesis theme.
- **Unified-panel path execution** — only materializes if BOTH Q9 switch-trigger conditions hold during the Steer fit; pre-registered, not pre-built.

</deferred>

---

*Phase: 06-iteration-2-swap-surface-validation-on-steer-ccop-usdt*
*Context gathered: 2026-05-29*
