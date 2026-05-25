# Pre-Registration: abrigo-x402 Iteration 1 (ICHI on cKES/USDT) + Iteration 2 (Steer on cCOP/USDT)

**Committed:** 2026-05-25
**Status:** Locked — no downstream phase may revise without an AF-03 audit-trail entry

This document fixes all pre-fit numerical thresholds, test specifications, decision rules, and fallback paths BEFORE any vault-level estimation runs. Spec swap after seeing results is forbidden per FEATURES.md AF-03. Pre-commit hook enforces this contract (see `.pre-commit-config.yaml` review-trail enforcement).

Scope anchors (verbatim from `.planning/PROJECT.md` post-correction block + `STATE.md` locked decisions):

- Iteration 1 anchor pool: `0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F` (cKES/USDT, ICHI vault present, ~4,440 swaps/30d per CANDIDATES §7.3 audit).
- Iteration 2 anchor pool: `0x2AC5baA668A8A58FD0e302B9896717484fd217B0` (cCOP/USDT V3, Steer-only LP aggregator, ~580–625 swaps/30d on V3 per CANDIDATES §7.3).
- ICHI vault factory (Celo): `0x9FAb4bdD4E05f5C023CCC85D2071b49791D7418F`.
- Steer vault factory (Celo): `0x116Dba5DcE9CcDA828218b7eB46406810632014C`.
- USDT canonical Celo: `0x48065fbBE25f71C9282ddf5e1cD6D6A887483D5e` (per CANDIDATES §1 — the LP-active USDT, NOT `0x617f…546`).
- Mento V2 BrokerProxy: `0x777A8255cA72412f0d706dc03C9D1987306B4CaD`.
- Uniswap V4 PoolManager Celo: `0x288dc841A52FCA2707c6947B3A777c5E56cd87BC`.
- Tail-risk reframe (CLAUDE.md non-negotiable): USDT depeg + USDT/USDC basis risk is the condition-4 framing. The Hernandez Cruz et al. 2024 stablecoin-depeg calibration paper is retained ONLY as a historical methodological reference (its single permitted citation appears in §Sources below).
- x402-on-Celo settlement infrastructure: NON-EXISTENT in the x402-foundation monorepo as of 2026-05-25. Cost leg is MODELED (not paid) for Iterations 1+2. Any paid demo settles on Base; this is acknowledged as the forward-looking research finding to surface in the Iteration-1 PDF report.

## Kernel Forms

- **NHPP specification:** Non-homogeneous Poisson process fit via Kirchner 2015 INAR(p) bin-count estimator on `statsmodels.tsa.api.VAR` with non-negativity projection. Bin width selection: AIC-min over grid `{1m, 5m, 15m, 1h}` per FEATURES.md AF-04 (canonical label: "Hand-tuned bin width for INAR(p)" — no hand-tuned bin width allowed; AIC-min over the pre-registered grid is the locked selection rule). Source: Kirchner 2015 arxiv.org/abs/1509.02017.
- **Hawkes specification:** Bivariate (revenue leg × cost leg) Hawkes process via `tick.hawkes.HawkesExpKern` with exponential kernel and full off-diagonal excitation matrix `[[α_RR, α_RC], [α_CR, α_CC]]`. Diagonal-only shortcut is forbidden (DGP-02). Stationarity condition `||α/β||_∞ < 1` enforced. Source: Daw & Pender 2017 arxiv.org/pdf/1707.05143v3.
- **Power-law kernel (deferred):** Exponential kernel is the v1 headline; power-law kernel (Bacry et al.) is the v2 robustness sweep (DGP-V2-01). Not run in v1.

## Prior Parameters

- **rate_per_event:** Three-point grid `(1, 5, 10)` queries/event. Central value `5` = headline; `(1, 5, 10)` = REPORT-03 sensitivity sweep replayed in Phase 5. Rationale: `1` = single subgraph poll per swap (minimum plausible); `5` = typical multi-component vault dashboard polling; `10` = heavy multi-vault aggregation.
- **USD_per_query:** `$5e-6/query` headline. Sensitivity sweep ±50%: `($2.5e-6, $5e-6, $7.5e-6)` per REPORT-03 / FEATURES D-09. Defensible economic interpretation: opportunity-cost-of-free-tier-exhaustion at paid-tier marginal rate (~$0.05 per 100k Graph queries = $5e-7/query, conservatively rounded up to $5e-6 to account for premium subgraphs / paid-tier markup over volume-discount tiers).
- **LR-test α-level:** `α = 0.01` (defensive single-tier headline). Pre-committed for bootstrap-LR rig per DGP-03. Rationale: 50:50 χ²(0):χ²(1) mixture right-tail thickness + PITFALLS §4 boundary issues + AF-02 hand-tuned-p-value concern.
- **Branching-ratio η floor:** `η ≥ 0.2` (conventional "meaningful self-excitation" threshold in the Hawkes literature). Pre-registered as a co-requirement alongside LR rejection at α = 0.01 for any Hawkes-positive claim.

## Test Statistics

- **Bootstrap LR:** Bootstrap likelihood-ratio test with 50:50 χ²(0):χ²(1) mixture null distribution. 1000 bootstrap reps simulating from fitted NHPP, refitting BOTH models per rep. Vanilla `statsmodels.likelihood_ratio_test` is forbidden (boundary error per PITFALLS §4). Sources: Filimonov & Sornette 2014 arxiv.org/pdf/1403.5227; arxiv.org/pdf/2410.05008 (LR over-rejection); Wheatley ETH thesis on robust Hawkes.
- **Time-rescaling KS:** Brown et al. 2002 time-rescaling theorem applied to Hawkes residuals. Conventional threshold `p > 0.05` for fail-to-reject under Hawkes calibration. Held-out split is the last 20% temporal block.
- **Profile-likelihood η-CI:** Profile likelihood for branching-ratio confidence intervals per PITFALLS §4 (Hessian-based MLE standard errors known to under-cover for Hawkes with small samples — Ogata 1978). EM-based estimator (`tick.hawkes` EM solver) is an acceptable alternative.
- **Cross-correlogram + permutation null:** DEPEND-01 spec: cross-correlogram between `dK_revenue(t)` and `dK_cost(t)` arrivals at lags from `-T` to `+T` with permutation null (1000 reps). Empirical copula fit follows; vine copula fallback only if BIC prefers.

## Acceptance Regions

A Hawkes-positive claim requires ALL FOUR of the PITFALLS §4 four-criterion gate to hold simultaneously:

1. Bootstrap LR rejects NHPP at α = 0.01 (50:50 χ²(0):χ²(1) mixture).
2. η ≥ 0.2 (conventional self-excitation floor).
3. Held-out KS test rejects NHPP rescaling under Hawkes-fitted parameters (last-20% temporal block).
4. Branching-ratio profile-likelihood CI excludes zero.

If ANY of the four fails: published as null-result per FEATURES TS-15 / HEDGE-05 firing condition (b) "NHPP-vs-Hawkes indistinguishable at conventional α". No retroactive relaxation of any criterion is permitted (AF-03 defense).

## Decision Rules

HEDGE-05 firing conditions (per FEATURES TS-15) — any ONE fires null-result emission:

(a) Phase-0 cost-leg gate fails (REPRO-03 threshold below window) — applies to Steer in Iteration 2 as the leading-firing-condition.
(b) NHPP-vs-Hawkes indistinguishable per the four-criterion gate above.
(c) Zero convex-dominance conditions hold per HEDGE-01 — i.e., NONE of:
   1. vol-of-vol > 0;
   2. positive skew / fat tails;
   3. Hawkes self-excitation (per Acceptance Regions above);
   4. USDT depeg + USDT/USDC basis jump (tail-risk condition — USDT, NOT USDC, per CLAUDE.md non-negotiables and SOMNIA_DRAFT.md §FUNCTIONAL FORM condition 4 reparameterization).

Each firing produces `reports/{protocol}_null_result.pdf` (or memo-only for Phase 0 firings per ROADMAP HEDGE-05 scope — i.e., a Phase-0 Steer FAIL produces `notes/steer_cost_leg_bound.md` and a `reports/steer_null_result.pdf` slim memo, not a full Phase 1–5 cycle).

## REPRO-03 Threshold

Two-tier semantics (NOT the binary ROADMAP draft):

- **PASS:** primary-source evidence shows ≥ 100k Graph queries/mo attributable to Steer's Celo deployment. Proceed with Iteration 2 estimation.
- **STRADDLE:** primary-source bound lands in `[30k, 100k]`/mo. Fires HEDGE-05 null with `marginal-demand` flag in `notes/steer_cost_leg_bound.md`. `reports/steer_null_result.pdf` ships documented as marginal-demand.
- **FAIL:** primary-source bound `< 30k`/mo. Fires HEDGE-05 null with `below-window` flag. `reports/steer_null_result.pdf` ships documented as below-window.

Rationale: 100k/mo = Graph free-tier ceiling (DEMAND-01 canonical demand-window lower bound). 30k floor reflects the paid-tier breakeven-ish band where Steer would *start* paying for queries but is structurally far from saturating the demand window.

Threshold committed BEFORE Phase 6 first execution. Phase-0 pre-validation (PHASE_0_GATE.md) attempts to resolve this for Steer at Phase 0 via primary-source enumeration (Blockscout + Steer docs + DefiLlama TVL extrapolation). If determinable at Phase 0 and FAIL: Iteration 2 fires HEDGE-05 memo-only null and no Phase 1–5 cycle runs for Iter-2. If PASS at Phase 0: Phase 6 first-step check is skipped as redundant.

## Q-9 Fallback Pre-Registration

- **Primary panel: V3-anchor-only** (cCOP/USDT Uniswap V3 pool `0x2AC5baA668A8A58FD0e302B9896717484fd217B0`, ~580–625 swaps/30d per CANDIDATES §7.3). No pooling assumption to defend at the headline level.
- **Pre-registered fallback: V3+V4+Broker unified.** Switch is triggered IF AND ONLY IF BOTH conditions hold simultaneously:
  1. V3-only sample size `< 300` events over the fitted window (Hawkes branching-ratio identifiability floor per PITFALLS §4) **OR** Hawkes branching-ratio profile-likelihood CI width `> 0.4` (conventional precision floor).
  2. Cross-class permutation test (1000 reps; null = three event classes V3 Swap / V4 PoolManager / Mento V2 Broker share common arrival-process structure) returns `p > 0.05` — i.e., fails to reject the pooling assumption.
- If both conditions hold: switch to unified panel (V3 ~625/30d + V4 PoolManager cCOP routing ~90/30d + Mento V2 Broker cCOP mint/burn ~185/30d ≈ ~900 events/30d total per CANDIDATES §7.3).
- This switch is PRE-COMMITTED, not Phase-6 ad-hoc decision — AF-03 defense.
- **Phase 2 code obligation:** The V3+V4+Broker pooling code AND the cross-class permutation test code MUST live in `analysis/src/` from Phase 2 onwards, dead-code-exercised by synthetic unit tests in Iteration 1. REPRO-02 invariant (`git diff fetch/src analysis/src` between Iter-1-complete and Iter-2-complete returns empty).

## Q-7 Floor

Pools below the floor are EXCLUDED from any aggregate (deferred substrate per Q-4 / SYNTH-V2-01).

- **Threshold: TVL `< $10k` OR events `< 30` per 30 days** (whichever is binding).
- Affected pools (per CANDIDATES §2):
  - `cXOF/USDm` `0xAA97F0689660eA15b7d6f84F2E5250B63f2b381a` (TVL ~$11k — at-or-just-above the $10k floor; flagged as marginal).
  - `BRLm/EURm` `0xb6c8f9490314394CFc6EDacb8717bFDC1EB8dab5` (small; below floor).
- Both flagged in §Deferred Substrate below as v2-reconsideration candidates.

## Deferred Substrate

The following are deferred from v1 scope and tracked here for AF-12 silent-re-scope defense. Activation in future iterations requires explicit decision artifact + git-visible flag toggles (no row additions to `protocols/*.toml`).

- **COPM (Minteo) vaults** — `0xC92E8Fc2947E32F2B574CCA9F2F12097A71d5606` token; ICHI vaults `0x9F2bB8B7dFF141e1e35d05D6B8215BA8634fFce8`, `0xB52CfF57Cf94717193C63fbcdd50d09EdEe3FBF5`. Reason: v2-deferred per CONTEXT.md (Minteo controlled-broadening flag retained but not active in v1). Reconsideration trigger: v2 substrate expansion to Minteo-fintech mixing class (`mixing_class = "minteo-fintech"`).
- **cXOF/USDm pool** (`0xAA97F0689660eA15b7d6f84F2E5250B63f2b381a`, ~$11k TVL) — at-or-marginally-above Q-7 floor. Reconsideration: Phase-7-or-v2 if TVL grows `≥ $20k`.
- **BRLm/EURm pool** (`0xb6c8f9490314394CFc6EDacb8717bFDC1EB8dab5`, < $10k TVL) — below floor. Reconsideration: Phase-7-or-v2 if events/30d `≥ 60`.
- **~38 non-anchor ICHI Celo vaults** — listed in `protocols/ichi.toml` with `active = false; reason = "v2-deferred"`. Activated by toggling boolean flags in future iterations; row additions forbidden by AF-12 silent-re-scope defense.
- **Real x402-on-Celo settlement infrastructure** — x402-foundation monorepo lists no Celo facilitator as of 2026-05-25. Cost leg is MODELED, not paid, in Iterations 1+2. Forward-looking research finding for the Iteration-1 PDF report.

## Sources

- Kirchner 2015 INAR(p): arxiv.org/abs/1509.02017
- Daw & Pender 2017 bivariate Hawkes: arxiv.org/pdf/1707.05143v3
- Chen et al. 2017 NHPP-vs-Hawkes LR test: arxiv.org/pdf/1702.06055v2
- Brown et al. 2002 time-rescaling KS test (cited in PITFALLS §4)
- Filimonov & Sornette 2014 LR boundary correction: arxiv.org/pdf/1403.5227
- arxiv 2410.05008 LR over-rejection under naive plug-in
- Wheatley ETH thesis robust Hawkes: ethz.ch/.../wheatleythesis.pdf
- Hernandez Cruz et al. 2024 stablecoin depeg calibration (cited as historical USDC depeg comparison only; condition-4 framing is USDT not USDC per CLAUDE.md non-negotiables): arxiv.org/pdf/2407.11716v1
- Ma et al. 2014 Carr–Madan strip: arxiv.org/pdf/1406.5430v1
- `../abrigo-analytics/notes/SOMNIA_DRAFT.md` §FUNCTIONAL FORM — four convex-dominance conditions, condition 4 reparameterized to **USDT depeg + USDT/USDC basis** per CLAUDE.md non-negotiables (the historical "USDC" wording in the upstream draft is methodological; the empirical counter-stable on every Celo Mento-local pool surveyed is USDT `0x48065fbBE25f71C9282ddf5e1cD6D6A887483D5e`).
- `../abrigo-analytics/notes/SOMNIA_DRAFT.md` §ARRIVAL PROCESS — NHPP/Hawkes specification baseline.
- `.planning/research/CANDIDATES.md` §7 Hidden-Volume Audit (thinness retraction; cKES/USDT ~4,440/30d; cCOP/USDT ~580–625/30d on V3 anchor).
- `.planning/research/PITFALLS.md` §4 (LR-boundary correction + four-criterion gate); §1 (substrate-too-young — verified, retracted for cKES/USDT counting-artifact false positive; spirit retained as sample-thinness discipline).
- `.planning/research/FEATURES.md` TS-15 null-result template; D-03 pre-registration; AF-01..AF-12 anti-feature catalogue.

USDT framing discipline (CLAUDE.md domain non-negotiable): every mention of the convex-dominance condition 4 cites **USDT depeg + USDT/USDC basis** as the tail-risk headline. The Hernandez Cruz et al. 2024 historical citation in the bullet above is the single permitted reference to the alternative-stable historical case, used purely as methodology source — never as the condition-4 headline.

## Pre-Registration Discipline (AF-03 Audit Trail)

This subsection is non-negotiable scaffolding for the AF-03 spec-swap-after-seeing-results defense:

- **No post-hoc threshold revision.** Every numeric value committed above (α = 0.01, η ≥ 0.2, REPRO-03 `(30k, 100k)`, Q-7 `($10k, 30 events/30d)`, Q-9 trigger `(300 events OR CI width 0.4)`, rate_per_event grid `(1, 5, 10)`, USD_per_query grid `($2.5e-6, $5e-6, $7.5e-6)`) is locked. Revising any of them requires a new pre-registration entry with a git commit predating the next downstream phase. PHASE_0_GATE.md and the pre-commit review-trail hook gate this.
- **No post-hoc test substitution.** The bootstrap LR with 50:50 χ²(0):χ²(1) mixture is THE LR test; vanilla `statsmodels.likelihood_ratio_test` is forbidden as a substitute. The four-criterion gate is the headline acceptance procedure; weaker variants (η-only, LR-only, KS-only) are not acceptable substitutes for the Hawkes-positive claim.
- **No post-hoc panel substitution.** The Q-9 V3-only → V3+V4+Broker switch is permitted only via the two-condition trigger above; ad-hoc panel changes after seeing the V3-only fit fail are forbidden.
- **Null-result publishability.** Any HEDGE-05 firing per §Decision Rules is itself a valid deliverable; the project's epistemics explicitly admit `reports/{protocol}_null_result.pdf` as on-roadmap output. Treating null results as project failures is itself an AF-03 violation (the spec change would be "publish only positive results").

## Verification Hooks

The following commands operationalize this pre-registration's enforceability and are runnable by reviewers and downstream phases:

- `git log --oneline -- notes/PRE_REGISTRATION.md` must return at least one commit predating any commit under `analysis/src/` or `data/raw/` (SC-1 ordering invariant). At Phase 0 commit time `analysis/src/`, `data/raw/`, `fetch/src/` do not exist (verifiable via `test ! -d`).
- `.pre-commit-config.yaml` review-trail enforcement (Plan 00-04) rejects edits to this file unless paired `_reality_checker.md` + `_code_reviewer.md` artifacts exist with `## VERDICT` headers and no unresolved BLOCKER.
- `protocols/_schema.toml` is frozen after the Phase-0 commit hash recorded in `notes/PHASE_0_GATE.md` (Plan 00-05); `make schema-frozen-check` rejects diffs to it in any downstream phase.
- The Q-7 floor and Q-9 fallback trigger thresholds committed here are consumed by `protocols/ichi.toml` (Plan 00-06) and the Q-9 decision artifact `notes/Q9_DECISION.md` (Plan 00-03) — both must reference these threshold values, not redefine them.

## Cross-Plan Consumer Map

Other Phase-0 plans and downstream phases consume specific elements of this pre-registration. Listed here so that any drift between this file and a consumer is immediately auditable:

- **Plan 00-02 (`notes/PHASE_0_GATE.md`):** consumes the REPRO-03 two-tier threshold above for the Steer-row PASS/STRADDLE/FAIL classification and the ICHI cKES/USDT anchor verbatim (CANDIDATES §4.1 PASS).
- **Plan 00-03 (`notes/Q9_DECISION.md`):** consumes the §Q-9 Fallback Pre-Registration section verbatim, including the trigger conditions and the pre-committed unified panel composition (V3 + V4 PoolManager + Mento V2 Broker). The pooling-assumption argument structure (cross-class permutation test) is the consumer's full statistical specification; this file's role is only to lock the pre-fit thresholds.
- **Plan 00-04 (`.pre-commit-config.yaml`):** consumes the AF-01..AF-12 anti-feature catalogue references (this document cites AF-02, AF-03, AF-04, AF-12) and the review-trail enforcement contract for `.planning/**/PLAN.md` artifacts.
- **Plan 00-05 (`protocols/_schema.toml`):** consumes the demand-window definition implied by the cost-leg framing above (indexer-backed analytics/UI queries only; Forno RPC keeper polling explicitly excluded — locked in this document via the `USD_per_query` Graph-paid-tier-anchored prior).
- **Plan 00-06 (`protocols/ichi.toml`):** consumes the Q-7 floor (`TVL < $10k OR events < 30/30d`), the §Deferred Substrate enumeration (vault flags `active = false; reason = "v2-deferred"`), and the COPM controlled-broadening flag.
- **Plan 00-07 (`protocols/steer.toml`):** consumes the REPRO-03 threshold and the cost-leg framing for the `cost_leg_lower_bound_verified` flag default.
- **Phase 3 (DGP Estimation):** consumes §Kernel Forms (Hawkes specification, Kirchner INAR(p) baseline), §Test Statistics (bootstrap LR, time-rescaling KS, profile-likelihood η-CI), and §Acceptance Regions (four-criterion gate).
- **Phase 4 (Carr–Madan + falsification):** consumes §Decision Rules condition-4 framing (USDT depeg + USDT/USDC basis) for the jump-leg overlay calibration.
- **Phase 5/6 (Reporting + Iteration 2):** consumes the entire document as the canonical pre-registration audit reference; the PDF deliverable cites this file's commit hash to anchor the AF-03 timeline.

---

*Pre-registration committed 2026-05-25 by GSD plan 00-01 executor against `.planning/phases/00-candidate-eligibility-pre-registration/00-01-PLAN.md`. Pre-fit numerical thresholds, test statistics, decision rules, fallback paths, and deferred substrate enumeration are now locked. No downstream phase may revise without an AF-03 audit-trail entry.*
