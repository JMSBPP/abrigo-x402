# Phase 0: Candidate Eligibility & Pre-Registration - Context

**Gathered:** 2026-05-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Commit all pre-fit governance artifacts (pre-registration, Phase-0 eligibility gate, Q-9 cCOP-panel decision, anti-feature lint hook, schema-frozen demand-window definition) so no downstream phase can spec-swap after seeing results. No data-fetch in this phase; no estimation code; outputs are all human-authored governance markdown + TOML + a `.pre-commit-config.yaml`.

</domain>

<decisions>
## Implementation Decisions

### Q-4 ICHI granularity (Iter-1 panel scope)
- **Primary panel: single-vault microcosm only on the cKES/USDT ICHI anchor vault.** No per-protocol aggregate is built in Iter-1.
- **Microcosm vault: cKES/USDT anchor** (densest substrate ~4,440 swaps/30d, already locked as Iter-1 anchor in PROJECT.md).
- **Implication for Phase 7:** the Q-4 per-protocol-vs-per-vault retrospective becomes degenerate in v1 (only one panel ran). Phase 7 documents this and defers the retrospective to a future iteration that runs both. SYNTH-V2-01 fires with a "single-panel-iteration; retrospective deferred" verdict.
- **Pool inclusion rule, stated for future iterations not active in v1:** if/when an aggregate is added, include all ICHI vaults whose underlying Uniswap V3 pool pairs a Mento *local* stable against USDT and clears the Q-7 floor. cKES/USDT, cCOP/USDT, cGHS/USDT, cNGN/USDT, cZAR/USDT vaults are the candidate set; non-local pairs (cUSD/USDC etc.) stay excluded.

### Q-7 TVL-too-thin floor
- **Rule: drop with documented reasoning.** Pools below a Phase-0-committed TVL/event-count floor are excluded from any aggregate. Threshold lives in `notes/PRE_REGISTRATION.md`.
- **Threshold (Claude's Discretion to propose at planning time, e.g. TVL < $5k OR events < 30/30d) — committed in PRE_REGISTRATION.md before any Phase 2 work.**
- **Affected pools (per CANDIDATES.md):** cXOF/USDm, BRLm/EURm — pre-flagged in PRE_REGISTRATION.md `Deferred substrate` section as v2-reconsideration candidates.

### Q-9 cCOP panel construction (Iter-2)
- **Primary panel: V3-anchor-only** (~625 swaps/30d on cCOP/USDT V3). No pooling assumption to defend at the headline level.
- **Pre-registered fallback: V3+V4+Broker unified.** If the actual Phase 6 V3-only sample falls below a numeric trigger threshold AND the cross-class permutation test passes, switch to the unified panel. The switch is *pre-registered as a fallback in PRE_REGISTRATION.md, not a Phase 6 ad-hoc decision* (no AF-03 spec-swap).
- **Phase 2 code obligation:** the V3+V4+Broker pooling code AND the cross-class permutation test code MUST live in `analysis/src/` from Phase 2 onwards, dead-code-exercised by synthetic unit tests in Iter-1. This is the REPRO-02 invariant (`git diff fetch/src analysis/src` between Iter-1-complete and Iter-2-complete returns empty).
- **Numeric fallback-trigger threshold:** Claude's Discretion to propose at planning time (e.g., V3-only sample < 300 events over the fitted window, OR Hawkes branching-ratio profile-likelihood CI width > some bound). Committed in PRE_REGISTRATION.md before Phase 6.

### REPRO-03 Steer cost-leg lower-bound threshold
- **Two-tier outcome semantics (not the binary ROADMAP draft):**
  - **PASS:** primary-source evidence shows ≥ 100k Graph queries/mo attributable to Steer's Celo deployment.
  - **STRADDLE:** primary-source bound lands in 30k–100k/mo → fires HEDGE-05 null with `marginal-demand` flag in `notes/steer_cost_leg_bound.md`. Phase 6 still emits `reports/steer_null_result.pdf`, documented as marginal-demand rather than below-window.
  - **FAIL:** primary-source bound < 30k/mo → fires HEDGE-05 null with `below-window` flag. Same null-result PDF emission.
- **Rationale:** 100k/mo = Graph free-tier ceiling (the canonical demand-window lower bound per DEMAND-01). 30k floor reflects a paid-tier breakeven-ish band where Steer would *start* paying for queries but is structurally far from saturating the demand window. Captures the empirical uncertainty in Steer's Celo footprint.
- **PHASE_0_GATE.md Steer row resolution:** **pre-validate the bound in Phase 0** via primary-source enumeration of Steer's Celo-only analytics-query footprint (Blockscout + Steer docs + DefiLlama TVL extrapolation as triangulation). If the Phase-0 primary-source bound is determinable AND below the 30k FAIL threshold, the row is marked **FAIL** in `PHASE_0_GATE.md` and Iteration 2 fires HEDGE-05 memo-only null per ROADMAP HEDGE-05 firing scope for Phase 0. No Phase 1–5 cycle gets run for Iter-2 in that case. If the bound is determinable and PASSes, mark **PASS** (skip the Phase 6 first-step check; it becomes redundant). If indeterminate, remain CONDITIONAL/STRADDLE and resolve as Phase 6 first step.

### Minteo COPM operationalization
- **Status: v2-deferred substrate.** COPM does NOT enter the Iter-1 panel (single-vault cKES) or the Iter-2 panel (V3-only cCOP, COPM is its own token `0xc92e8Fc...`, not cCOP).
- **`protocols/_schema.toml` `mixing_class` enum** pre-populated at Phase 0 with **all values needed across v1+v2**: `["mento-native", "minteo-fintech"]` plus any other anticipated value (e.g. `"mento-bridged"` for future BRLm). The enum is **frozen by `make schema-frozen-check`** after the Phase-0 commit hash; subsequent iterations add rows to `protocols/*.toml` but never edit `_schema.toml`.
- **`protocols/ichi.toml` vault enumeration:** lists the full ICHI Celo footprint (~40 vaults) with per-vault status flags — `[vaults.<anchor>] active = true; mixing_class = "mento-native"` for the cKES anchor; `[vaults.<copm_vault>] active = false; mixing_class = "minteo-fintech"; reason = "v2-deferred"` for the two COPM vaults; similar `active = false; reason = "v2-deferred"` flags for the other ~38 non-anchor vaults. Iteration moves are toggles, not row additions. Defends AF-12 silent re-scope.
- **`notes/PRE_REGISTRATION.md` `Deferred substrate` section** documents all v2-deferred items (COPM vaults, cXOF/USDm pool, BRLm/EURm pool, non-anchor ICHI vaults, etc.) with the reason for deferral and the Phase-7-or-v2 reconsideration trigger. Co-located with the pre-fit governance discipline; auditable as part of the locked pre-reg.

### Pre-registration prior values (PRE_REGISTRATION.md numerics)

- **`rate_per_event` cost-leg prior:** three-point empirical-floor + arbitrary-ceiling grid **(1, 5, 10) queries/event** — central value 5 is the headline; (1, 5, 10) is the sensitivity sweep replayed in Phase 5 per REPORT-03 / FEATURES D-09. Rationale: 1 = single subgraph poll per swap (minimum plausible); 5 = typical multi-component vault dashboard polling; 10 = heavy multi-vault aggregation. Wider span than the conventional ±50% sweep, so the headline is more robust to the prior's misspecification.
- **`USD_per_query` cost-leg prior:** paid-tier marginal cost **≈ $5e-6/query** (~$0.05 per 100k Graph queries on the Network = $5e-7/query, conservatively rounded *up* to $5e-6 to account for premium subgraphs / paid-tier markup over volume-discount tiers). Sensitivity sweep ±50% per REPORT-03: ($2.5e-6, $5e-6, $7.5e-6). Defensible economic interpretation: opportunity-cost-of-free-tier-exhaustion (what Iteration 1's subgraph spend *would* cost if it weren't on the free tier).
- **LR-test α-level for NHPP-vs-Hawkes:** **α = 0.01 (defensive)**, single-tier headline. Pre-committed for the bootstrap-LR rig per DGP-03. Given the 50:50 χ²(0):χ²(1) mixture's known right-tail thickness + PITFALLS §4 boundary issues + AF-02 hand-tuned-p-value concern, the defensive default applies. Hawkes-positive claim requires LR-rejection at this α *and* the η ≥ 0.2 floor *and* held-out KS-rejection of NHPP rescaling *and* branching-ratio profile-likelihood CI excluding zero (PITFALLS §4 four-criterion gate).
- **Branching-ratio η floor for self-excitation claim:** **η ≥ 0.2** (conventional threshold for `meaningful` self-excitation in the Hawkes literature). Pre-registered as a co-requirement for any Hawkes-positive claim alongside LR rejection at α = 0.01.

### Phase-0 governance artifacts (mandated by ROADMAP SC-1 through SC-5)
- **`notes/PRE_REGISTRATION.md`** — kernel forms (`HawkesExpKern` exponential, with off-diagonal excitation matrix; NHPP via Kirchner INAR(p)); prior parameters (above grids); test statistics (bootstrap LR, time-rescaling KS, profile-likelihood η-CI); acceptance regions (above thresholds); decision rules (HEDGE-05 firing conditions per FEATURES TS-15); Deferred substrate section; REPRO-03 two-tier threshold semantics; Q-9 V3-only primary + unified fallback (with numeric trigger threshold).
- **`notes/PHASE_0_GATE.md`** — five-check eligibility outcome for ICHI (PASS verbatim per CANDIDATES §4.1) and Steer (PASS/STRADDLE/FAIL per Phase-0-resolved REPRO-03 threshold check) with Blockscout verification URL per row.
- **`notes/Q9_DECISION.md`** — V3-only primary + pre-registered unified fallback with the trigger threshold and the pooling-assumption argument structure (cross-class permutation test specification).
- **`.pre-commit-config.yaml`** with three layered hooks:
  - (a) AF-01..AF-12 anti-feature lint gate — synthetic violating fixture exits non-zero
  - (b) 2-way review-trail enforcement — rejects `.planning/**/PLAN.md` or `.planning/ROADMAP.md` commits unless paired `_reality_checker.md` + `_code_reviewer.md` files exist with `## VERDICT` headers and no unresolved BLOCKER; `--allow-revision` override flag honors NEEDS REVISION but not BLOCKER
  - (c) `make schema-frozen-check` — rejects any diff to `protocols/_schema.toml` after the Phase-0 commit hash recorded in `notes/PHASE_0_GATE.md`
- **`protocols/_schema.toml`** — schema for protocol-spec TOMLs with:
  - `data_cost_class` enum pre-populated with `["indexer-analytics-queries", "per-event-oracle-stretch", "per-scan-ocr-stretch"]` and any other anticipated value
  - `mixing_class` enum pre-populated with `["mento-native", "minteo-fintech"]` and any other anticipated value
  - Comment block documenting the demand-window definition (indexer-backed analytics/UI queries only; Forno RPC keeper polling explicitly excluded)
- **`protocols/ichi.toml`** — Iter-1 swap surface with full ICHI Celo vault enumeration (per-vault active/deferred status flags)
- **`protocols/steer.toml`** — Iter-2 stub with `cost_leg_lower_bound_verified = false` flag (cleared in Phase 6 first step OR pre-validated to FAIL in Phase 0)

### Claude's Discretion
- Q-7 numeric floor specifics (e.g. exact TVL threshold $5k vs $10k; events/30d threshold 30 vs 50). Recommended values proposed at /gsd:plan-phase 0 time and committed in PRE_REGISTRATION.md.
- Q-9 fallback numeric trigger threshold (e.g. V3-only sample < 300 events OR branching-ratio CI width threshold). Recommended values proposed at /gsd:plan-phase 0 time.
- KS test threshold for time-rescaling residuals (conventional p ≤ 0.05 to reject NHPP under Hawkes calibration; or D-statistic threshold). Standard literature default applies unless argument for deviation surfaces.
- Pre-commit hook deployment tool: `.pre-commit-config.yaml` per ROADMAP SC-4 wording (the `pre-commit` Python framework). Alternative (`.husky/`) only if a node-only-runtime argument surfaces.
- Stationarity diagnostic threshold (Phase 3 SC-4 says ±25% — keep as-is unless evidence-based argument to revise).
- Held-out split block boundary spec (Phase 3 SC-4 says last 20% time-split — keep as-is).
- Carr–Madan grid escalation specifics (ROADMAP locks 2^11 → 2^12 → abort — keep as-is).
- USDT depeg jump-leg calibration source (deferred to Phase 4 per ROADMAP; not a Phase 0 decision).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project-level governance
- `.planning/PROJECT.md` — Constraints (TS+Python stack, free-tier-only, x402-on-Celo+Mento substrate); Scope Correction 2026-05-25 block is authoritative (supersedes Myriad/Halo/MiniPay scope); Key Decisions table including Minteo COPM controlled-broadening
- `.planning/REQUIREMENTS.md` — 32 v1 reqs; Phase 0 primary-fires: GOV-01 (pre-reg), GOV-02 (five-check eligibility), GOV-03 (anti-feature lint), DEMAND-01 (verify component), REPRO-04 (Q-9 decision component)
- `.planning/ROADMAP.md` — Phase 0 success criteria SC-1 through SC-5 verbatim; review-trail enforcement contract; HEDGE-05 firing scope by phase

### Research substrate (post-correction synthesis)
- `.planning/research/SUMMARY.md` — Implications for Roadmap §Phase 0; confidence assessment; gaps to address
- `.planning/research/CANDIDATES.md` — §4.1 ICHI five-check PASS verbatim; §4.2 Steer CONDITIONAL row; §5 anti-shortlist disqualifications; §6 Q4/Q6/Q7 open questions; §7 Hidden-Volume Audit + Q-9 cCOP unified-vs-V3-only question
- `.planning/research/PITFALLS.md` — §1 substrate-too-young (Myriad-blocker resolved via switch; spirit reapplies as sample-thinness on chosen anchor — RETRACTED for cKES/USDT per CANDIDATES §7 post-audit); §3 in-sample optimism; §4 LR-boundary error (boundary-correct LR test + profile-likelihood CIs + four-criterion gate); §6 cost-leg stipulation; §7 Carr-Madan strip pitfalls
- `.planning/research/FEATURES.md` — TS-04 demand-window gate; TS-15 null-result template; D-03 pre-registration; D-09 cost-leg sensitivity; AF-01..AF-12 anti-features (AF-03 spec-swap, AF-04 retrospective category invention, AF-06 strip-without-gate, AF-12 silent re-scope especially load-bearing for Phase 0)
- `.planning/research/ARCHITECTURE.md` — L0 protocol-spec TOML layer; Pattern 2 paid-step-is-idempotent; Pattern 5 thin notebook orchestrator; build-order dependency chain
- `.planning/research/STACK.md` — pinned versions for the pinned-from-Phase-1 contract (FETCH-01 / Phase 1 SC-1)

### Upstream cost-model substrate
- `../abrigo-analytics/notes/SOMNIA_DRAFT.md` — §FUNCTIONAL FORM (four convex-dominance conditions; condition 4 reparameterized USDT depeg + USDT/USDC basis); §ARRIVAL PROCESS (NHPP vs Hawkes specification, Kirchner 2015 INAR(p), Daw & Pender 2017 bivariate Hawkes, Chen et al. 2017 LR test, Ma et al. 2014 Carr–Madan strip)
- `notes/DRAFT.md` — user-story origin (E4 Superfluid R3+ DV audit 2026-05-19); cCOP / Myriad-class second-test-case framing (now superseded; preserved as audit trail)

### State / continuity
- `.planning/STATE.md` — Decisions Pending Phase 0 (Q-9, Q-4, Q-7, USDT depeg jump-leg calibration source); Substrate Findings (thinness retraction 2026-05-25; cKES/USDT ~4,440 swaps/30d; cCOP/USDT ~580–625 on V3); Resume hint pointing at this CONTEXT.md

### Specific upstream citations for PRE_REGISTRATION.md statistical content
- Kirchner 2015 INAR(p): arxiv.org/abs/1509.02017
- Daw & Pender 2017 bivariate Hawkes: arxiv.org/pdf/1707.05143v3
- Chen et al. 2017 NHPP-vs-Hawkes LR test: arxiv.org/pdf/1702.06055v2
- Ma et al. 2014 Carr–Madan strip: arxiv.org/pdf/1406.5430v1
- Filimonov & Sornette 2014 LR boundary correction: arxiv.org/pdf/1403.5227
- arxiv 2410.05008 LR over-rejection
- Wheatley ETH thesis robust Hawkes
- Brown et al. 2002 time-rescaling KS test (PITFALLS §4 reference)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **None at code level — greenfield repo.** Only artifacts present: `package.json` with `@graphprotocol/client-cli ^3.0.7` + `@graphprotocol/client-x402 ^1.0.0` installed (no other src); `notes/DRAFT.md`; `README.md`; `CLAUDE.md`; `.planning/` planning tree.
- **No existing scaffolding for:** `fetch/` workspace, `analysis/` workspace, `protocols/` TOMLs, `notes/PRE_REGISTRATION.md`, `notes/PHASE_0_GATE.md`, `notes/Q9_DECISION.md`, `.pre-commit-config.yaml`, `Makefile`, `data/` directories.

### Established Patterns
- **Git fork/upstream pattern from CLAUDE.md**: `origin = JMSBPP/abrigo-x402` (push target), `upstream = wvs-finance/abrigo-x402` (PR target). All Phase 0 commits go to origin; PR opened against upstream:master once Phase 0 artifacts pass 2-way review.
- **Two-way plan review pattern from ROADMAP.md**: Reality Checker + Code Reviewer in parallel; review files at `.planning/_reviews/<artifact_basename>_{reality_checker,code_reviewer}.md` with `## VERDICT` first H2.
- **Sibling repo `abrigo-analytics`** uses the same uv-managed Python + TS+pnpm pattern this repo will adopt — STACK.md is calibrated against that pattern.

### Integration Points
- **`.pre-commit-config.yaml`** is the integration point for the AF-01..AF-12 lint gate + review-trail enforcement hook + schema-frozen check. Hook scripts likely live under `.pre-commit/` or a `scripts/` directory.
- **`Makefile`** integration point for `make schema-frozen-check` (called by the pre-commit hook) and the later `make leak-check` / `make verify-reproducibility` / `make iteration-2-full` targets specified across Phases 1–6.
- **`protocols/_schema.toml` + `protocols/ichi.toml` + `protocols/steer.toml`** are the protocol-spec swap surface (ARCHITECTURE.md L0). `_schema.toml` is the schema layer (frozen after Phase 0); `*.toml` files for each protocol are added/edited iteration by iteration without ever touching `_schema.toml`.
- **`notes/` directory** for human-authored governance markdown (PRE_REGISTRATION.md, PHASE_0_GATE.md, Q9_DECISION.md, steer_cost_leg_bound.md once Phase 6 fires, etc.).
- **Existing `notes/DRAFT.md`** (user-story origin) — read-only audit-trail; Phase 0 governance artifacts can link to it but don't modify it.

</code_context>

<specifics>
## Specific Ideas

- The two-tier REPRO-03 threshold (PASS / STRADDLE / FAIL with `marginal-demand` vs `below-window` flag) is a specific elaboration of ROADMAP's binary threshold draft. Both flags fire HEDGE-05 null but carry different epistemic signal in the report.
- "Pre-validate Steer bound in Phase 0" means a real primary-source enumeration during Phase 0 — Blockscout enumeration of Steer's analytics-query-emitting deployments, Steer docs scrape, DefiLlama TVL extrapolation — not a stub for Phase 6 to do. If determinable now, save 4 phases of nothing.
- "Q-9 fallback as pre-registration, not Phase 6 ad-hoc decision" is explicit anti-AF-03 discipline — the V3→unified switch is *not* allowed to happen *after* seeing the V3-only fit fail; it must be committed in PRE_REGISTRATION.md before any data lands.
- "ichi.toml lists all ICHI Celo vaults with active/deferred status flags" is a specific defense against AF-12 silent re-scope — adding a vault to the active panel in a future iteration requires flipping a boolean, which is git-diff-visible, rather than adding a row to the TOML (which could be lost in a larger config change).
- "_schema.toml enums pre-populated with all v1+v2 values now" anticipates Iter-2 + v2 substrate types without requiring a schema diff at that time (caught by `make schema-frozen-check`).

</specifics>

<deferred>
## Deferred Ideas

- **COPM Minteo vaults** — v2-deferred substrate; flagged in PRE_REGISTRATION.md `Deferred substrate` section with reason and reconsideration trigger.
- **cXOF/USDm and BRLm/EURm pools** — v2-deferred per Q-7 floor; tracked in PRE_REGISTRATION.md `Deferred substrate`.
- **~38 non-anchor ICHI Celo vaults** — listed in ichi.toml with `active = false; reason = "v2-deferred"`. Activated by toggling flags in a future iteration.
- **Q-4 per-protocol-vs-per-vault retrospective (SYNTH-V2-01)** — degenerate in v1 because only one panel ran; Phase 7 marks the retrospective as deferred to a future iteration that runs both granularities.
- **USDT depeg jump-leg calibration source** — Phase 4 lock per ROADMAP. Not a Phase 0 decision.
- **KS test threshold specifics, Carr-Madan grid mechanics, held-out split boundary, stationarity diagnostic threshold** — all locked in ROADMAP success criteria for later phases; Phase 0 PRE_REGISTRATION.md references them but doesn't author the numerics.
- **Pre-commit hook deployment tool choice** — default to `.pre-commit-config.yaml` per ROADMAP SC-4; consider `.husky/` only if a node-only-runtime argument surfaces during planning.
- **Real x402-on-Celo settlement infrastructure** — does not exist in x402-foundation monorepo as of 2026-05-25; cost leg is modeled (not paid) in Iter-1+Iter-2; forward-looking research finding to report, not a Phase 0 deliverable.

</deferred>

---

*Phase: 00-candidate-eligibility-pre-registration*
*Context gathered: 2026-05-25*
