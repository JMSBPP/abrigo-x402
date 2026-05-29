# abrigo-x402

## What This Is

An empirical pipeline that identifies a MiniPay-hosted Celo app whose revenue lands in a non-USD Mento stablecoin while its data costs are denominated in USD/USDC, then estimates the joint stochastic process of both cashflow legs and outputs an FX hedge instrument design calibrated to that protocol. Iteration 1 targets **Myriad** (prediction market on `mini.myriad.markets`). The pipeline is built to be re-runnable on additional MiniPay candidates (Iteration 2 = Halo, receipt OCR).

## Core Value

The pipeline must produce a calibrated joint cashflow function `C(t)` and a falsifiable DGP estimate (NHPP vs Hawkes) for a real MiniPay protocol — using only free-tier data resources (Graph 100k/mo + Celo RPC + Blockscout). If `C(t)` is unrecoverable from free-tier data, the project's hedge-design thesis itself is unsupported, and that null result is the deliverable.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Identify Myriad's on-chain settlement contracts on Celo (addresses + verified ABI)
- [ ] Build observable revenue-leg panel: bet inflows + settlement payouts in local Mento stablecoin, timestamped per event
- [ ] Stipulate the data-cost leg with a calibrated prior anchored in the **demand window** `[Graph free tier, Dune Plus $390/mo]`
- [ ] Estimate joint arrival process per `SOMNIA_DRAFT.md` §ARRIVAL PROCESS — fit both NHPP (Kirchner 2015 INAR(p)) and multivariate Hawkes (Daw & Pender 2017); report likelihood-ratio test (Chen et al. 2017)
- [ ] Output `C(t)` cashflow function and a hedge-instrument sketch via Carr–Madan strip (Ma et al. 2014) under the conditions specified in `SOMNIA_DRAFT.md` §FUNCTIONAL FORM
- [ ] Make the pipeline reproducible: Iteration 2 (Halo) must reuse the same Python + TypeScript stack with only the contract-address and data-cost-class parameters changed
- [ ] Provide a falsification gate: if Myriad's data-cost class lands outside the demand window, document the null result and stop the iteration

### Out of Scope

- **Earn Mento Rewards (Mento Labs)** — wrong demand structure. Reward is a MENTO incentive, not local-revenue-against-USD-data-cost. No hedge to estimate.
- **Walapay** — half the cashflow (Alipay leg) lives off-chain; on-chain panel is structurally incomplete.
- **Apex Football / Blueboard sports stack** — live-sports feeds plausibly cost above the $390/mo upper bound; outside the demand window, so no x402 demand to model.
- **Non-MiniPay Celo apps** — broader ecosystem deferred unless empirical work back-tracks (project memory `project_abrigo_x402_minipay_scope.md`).
- **x402-on-Base substrate** — non-retirement-pending-maturity until 2026-11-12 (project memory `project_e10_x402_substrate_pending_maturity_2026_11.md`). abrigo-x402 uses Celo + x402-on-Celo, not Base.
- **Deployed Solidity hedge contracts in this iteration** — Iteration 3+ stretch; this iteration ships the DGP estimate + the design sketch, not the trading instrument.
- **Dune Plus subscription** — we are *proving the case against buying it*, not purchasing it. The $390/mo figure functions as a demand-window upper bound, not a paid resource.

## Context

- **Upstream cost model:** `../abrigo-analytics/notes/SOMNIA_DRAFT.md` formalizes the two-leg cost function `c_D(Y_D, κ)` (data leg) + `c_AI(Y_AI)` (agent leg), the no-native-SOMI/USD-oracle problem, and the Carr–Madan convex-hedge replication. `notes/DRAFT.md` in this repo records the user-story origin incident (E4 Superfluid R3+ DV audit 2026-05-19 — Dune Plus $390/mo decision parked) and the cCOP / Myriad-class second-test-case framing.
- **Substrate facts (verified via celopedia 2026-05-25):** Celo is an Ethereum L2 (chain 42220). ERC-8004 Agent Trust Protocol is deployed on Celo mainnet (Identity `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432`, Reputation `0x8004BAa17C55a88189AE136b182e5fdA19dE9b63`). x402 is the canonical payment layer for AI agents on Celo, settling in USDC. Mento stablecoins (cCOP, cNGN, cKES, cGHS, cZAR, cXOF, BRLm) are live on Celo. **Subgraph availability on Celo lags other chains** — verify each subgraph's `_meta.block.number` before relying on it.
- **MiniPay catalog (snapshot 2026-04-09):** Myriad is published in the discovery list with country blacklist `BR | MX | GB` — i.e., explicitly targets emerging markets, matching the abrigo FX-hedge thesis.
- **Sibling repos:** `../abrigo-analytics` (empirical validation + structural econometrics), `../abrigo-marketing` (positioning). PR/upstream conventions documented in `CLAUDE.md`.

## Constraints

- **Tech stack**: TypeScript + `@graphprotocol/client-x402` + `@graphprotocol/client-cli` for the data-fetch client; Python (uv-managed venv) + pandas/numpy + statsmodels for DGP estimation. — Why: matches sibling abrigo-analytics tooling and the `functional-python` skill the user defaults to.
- **Free-tier only**: 100k Graph queries/mo on the Decentralized Network, free Celo RPC (`forno.celo.org`), Blockscout API (no key). No Dune Plus. No paid oracle subscriptions. — Why: evidence-before-spend per memory `feedback_phased_buy_discipline.md`; the project's existence is to *prove* the case against paid subscriptions.
- **Git workflow**: `origin = JMSBPP/abrigo-x402`, `upstream = wvs-finance/abrigo-x402`. All pushes go to `origin`; PRs target `upstream:master`. — Why: matches `abrigo-analytics` pattern, documented in `CLAUDE.md`.
- **Timeline**: aligned with Proof of Ship MVP cycle (~May 2026 per memory `project_deadlines_2026.md`); Iteration 1 must produce a falsifiable result before any Iteration 2 work begins.
- **Substrate**: x402-on-Celo + Mento, *not* x402-on-Base (which is substrate-pending-maturity per project memory).
- **Output discipline**: research artifacts as Markdown + notebooks. Any user-facing CV/document deliverable must render to PDF per memory `feedback_pdf_deliverable.md`.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| **Iteration 1 candidate = Myriad** (prediction market on Celo) | Cleanest two-leg fit: bet inflows in Mento stablecoin + oracle-driven discrete settlement payouts; data-cost leg (oracle subscription) sits in the `[free tier, $390/mo]` demand window; both legs have natural arrival-process structure testable against NHPP vs Hawkes. | — Pending |
| **Iteration 2 candidate = Halo** (Human Labs, receipt OCR) | Different data-cost class (per-scan OCR rather than per-event oracle) to test DGP-shape generality across cost classes. Same on-chain observability story. | — Pending |
| **Excluded from Iteration 1: Mento Rewards** | No USD data-cost leg. Reward is a MENTO governance-token incentive, not data-cost-against-local-revenue. Cannot serve as a null model because it has the wrong demand structure entirely. | ✓ Locked 2026-05-25 |
| **Excluded from Iteration 1: Walapay** | Multi-corridor remit, but the Alipay leg is fully off-chain → on-chain panel is structurally incomplete. Stretch goal only. | ✓ Locked 2026-05-25 |
| **Scope filter: MiniPay-hosted apps only (by preference)** | Concentrated in unserved/emerging-market countries (NG, KE, GH, ZA, CO, …), natively transact in Mento local stablecoins, enumerable from Proof of Ship cohorts + MiniPay discovery directory. | ✓ Locked 2026-05-25 (memory `project_abrigo_x402_minipay_scope.md`) |
| **Free-tier resources only for Iteration 1** | Evidence-before-spend discipline. The project's thesis is that x402 dominates Dune Plus for protocols in the demand window — buying Dune Plus to prove it would invert the argument. | ✓ Locked 2026-05-25 |
| **Demand window** = `[Graph free tier ≈ 100k queries/mo, Dune Plus = $390/mo]` | Below the free tier → no demand (free dominates). Above $390/mo → no demand for x402 (Dune Plus flat dominates). Inside = target customer segment. | ✓ Locked 2026-05-25 |
| **Deliverable shape for Iteration 1** = research artifact + reproducible pipeline | Premature to ship deployed hedge contracts before the DGP is identified. Solidity ships in Iteration 3+ contingent on positive Iteration 1 result. | ✓ Locked 2026-05-25 |

## Scope Correction 2026-05-25 (post-research)

The initial scope (Iteration 1 = Myriad, MiniPay-by-preference) was invalidated during the project-research phase. The corrections below supersede the corresponding entries above; the originals are preserved for audit trail.

### What failed and why

1. **Myriad disqualified** — its own contract registry (`docs.myriad.markets/builders/contract-addresses`) lists Celo mainnet `PredictionMarket` / `PredictionMarketQuerier` / `USDT` as "Coming soon." The MiniPay variant is points-based ("no financial commitment required"). No Mento-stablecoin cashflow leg exists. Primary-source verified via Pitfalls research.
2. **Halo disqualified** — production JS-bundle inspection: 79× "reward" + 60× "points", zero references to any Mento stablecoin, OP-stack predeploys (`0x4200…0007–0016`) indicating settlement on Base or another OP-stack chain rather than Celo Mento. Same structural failure mode as Myriad: rewards-game wrapping, not real local-stablecoin cashflow.
3. **MiniPay-scope retired** — celopedia SKILL.md rule #10 confirms MiniPay's enforced wallet scope is **USDT / USDC / USDM only**. The Mento *local* stablecoins (cCOP, cKES, cNGN, cGHS, cZAR, cXOF, BRLm) that the FX-hedge thesis depends on are NOT in MiniPay's wallet scope. The MiniPay-by-preference filter was structurally anti-correlated with the cashflow shape required.

### Path B chosen, B2 specifically

Scope broadened to **Celo apps with observable cashflows in Mento *local* stablecoins**, MiniPay filter dropped. See memory `project_abrigo_x402_minipay_scope` (now SUPERSEDED with the reasoning preserved).

### Candidate discovery (research/CANDIDATES.md)

LP-position aggregator discovery on Uniswap V3 Celo pools cleared **two applications** out of an 8-entry anti-shortlist (Bridgers routers, generic SwapPools, Mento DAO treasury Safes, SubsidyProgram, Sushi fee-collector, Ubeswap LP-token wrapper, bare EOAs):

- **ICHI** (`app.ichi.org`) — factory `0x9FAb4bdD4E05f5C023CCC85D2071b49791D7418F`. ≥ 40 verified vaults on Celo, present in every Mento local-stable pool surveyed. Phase-0 PASS.
- **Steer Protocol** (`app.steer.finance`) — factory `0x116Dba5DcE9CcDA828218b7eB46406810632014C`. Only LP-aggregator on cCOP/USDT. Conditional Phase-0 PASS — Celo TVL ~$855 (DefiLlama) may put data spend *below* the demand-window lower bound.

### Substrate findings (alter the FX-hedge framing)

- **Local-stable LP venues are exclusively Uniswap V3 on Celo** — Mento V3 FPMM holds zero local stables (verified via `FPMMDeployed` event log enumeration). Mento Broker is not a candidate venue.
- **Counter-stable is overwhelmingly USDT, not USDC.** The original `SOMNIA_DRAFT.md` tail-risk parameterization built around USDC depeg (Hernandez Cruz 2024, Wu & Liu 2026) does not apply. Tail-risk class shifts to **USDT depeg + USDT/USDC basis risk.**
- **Pool TVLs $11k–$130k**, cKES/USDT densest. cCOP/USDT sample is ~100–150 swaps/30d, below the 300-event Hawkes floor from PITFALLS §1.

### Revised Key Decisions (supersede the originals above)

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| **Iteration 1 = ICHI on cKES/USDT anchor pool** | Broadest substrate, multi-pool diversification, densest sample (cKES/USDT $130k TVL), ICHI's deployment registry well-documented, Phase-0 PASS verified primary-source on Blockscout + own docs. | ✓ Locked 2026-05-25 |
| **Iteration 2 = Steer Protocol on cCOP/USDT** | Different LP-management class (strategist-curated rebalance vs ICHI's single-asset auto-rebalance) — tests DGP generality across structurally distinct LP services. Recovers the cCOP corridor focus from prior ThetaSwap work. Cost-leg empirical lower bound verification required before execution. | ✓ Locked 2026-05-25 |
| **Tail-risk reframe: USDT depeg + USDT/USDC basis risk** | Empirical counter-stable in all Celo Mento-local pools is USDT, not USDC. The Mar-2023 USDC anchor citations remain useful as methodological references but the actual cashflow leg's stability anchor is USDT. | ✓ Locked 2026-05-25 |
| **Allow Minteo COPM into scope (controlled broadening)** | ICHI's two COPM (`0xc92e8Fc...`) vaults are the closest analogue to a Colombian-corridor LP-aggregator. Including them recovers data density on the COP corridor at the cost of mixing Mento-native + Minteo-fintech regimes; the mixing must be flagged in any joint analysis. | ✓ Locked 2026-05-25 (overrides ThetaSwap Rev-5.3 Mento-native-only convention for this iteration) |
| **Cost-leg = indexer-backed analytics/UI queries only** | Forno RPC `eth_call` keeper polling is free at any volume → falls below the demand-window lower bound. The demand window is defined for *per-query* indexed reads (Graph subgraphs, Dune analytics) only. Aligns with original `c_D · N_queries` cost-function model. | ✓ Locked 2026-05-25 |
| **Excluded: Myriad** | Mainnet contracts "Coming soon" per own docs; MiniPay variant is points-based, no stablecoin cashflows. | ✓ Locked 2026-05-25 (supersedes the original Iteration 1 = Myriad row above) |
| **Excluded: Halo** | Production JS bundle is points/reward-dominant, no Mento references, OP-stack predeploys indicate non-Celo settlement. | ✓ Locked 2026-05-25 (supersedes the original Iteration 2 = Halo row above) |

### Thinness retraction 2026-05-25 (post-skepticism audit)

The CANDIDATES.md §2 finding that cKES/USDT processed ~130 swaps/30d and cCOP/USDT ~100–150 swaps/30d is **retracted as a counting-artifact false positive**. Root cause: §1 Method implicitly used 5 s/block for Celo; actual post-2024 Celo block time is **1 s/block** (verified via Forno `eth_getBlockByNumber` over a 232,989-block window). Window calculations were 5× too short; pagination cutoffs compounded for cKES.

**Corrected 30-day Uniswap V3 Swap counts** (per CANDIDATES.md §7 Hidden-Volume Audit):
- **cKES/USDT: ~4,440 swaps/30d** (14.8× above 300-event Hawkes floor)
- **cCOP/USDT: ~580–625 swaps/30d** (~2× above floor)

Audit covered six gap channels with symmetric burden of proof (Ubeswap V2 + V3, Carbon DeFi, Sushi V2/V3, Velodrome, Mento V1 Exchange, Uniswap V4, Mento V2 Broker, total Transfer panel, DEX/bridge aggregators, MiniPay processors, Mento Labs Safes). Findings:
- All alternative DEX venues ruled out as material (dormant, dead pools, or zero local-stable holdings).
- Mento V2 Broker contributes ~185 mint/burn pairs/30d to **cCOP only** (28 of 100 cCOP Transfer counterparties are BrokerProxy).
- Uniswap V4 PoolManager contributes ~90 swaps/30d to **cCOP only** (holds 7.4M cCOP).
- Total Transfer panel is NOT a separate signal — ≥99% of cKES Transfer events have UniV3Pool/ICHIVault/SwapRouter on one side.

**Material consequences:**
- **ICHI on cKES/USDT** sample-size: BORDERLINE → PASS comfortably.
- **Steer on cCOP/USDT** sample-size: CONDITIONAL → PASS. Cost-leg lower-bound (CANDIDATES §6 Q6b) is now the only remaining binding constraint on Iteration 2.
- **Recommended dependent variable for the revenue-arrival process**: Uniswap V3 Swap events on the anchor pool (fee × tier = revenue per event, clean economic interpretation). ICHI deposit/withdraw is *demand-for-service*, not revenue. Transfer panel is DEX-amplified noise, not separate signal.
- **PITFALLS §1 sample-thinness application to abrigo-x402 is hereby retracted** as a counting-artifact false positive. The discipline (PITFALLS §1 as a category, anti-fishing replication) remains valid in general; it just doesn't bind here. This is exactly the failure mode `feedback_thinness_skepticism` warns against — caught by the skepticism audit, not by silently accepting the first count.

### New open question (post-audit)

| ID | Question |
|---|---|
| Q-9 (post-audit) | **cCOP panel construction for Iteration 2**: V3-anchor-only (~625 swaps/30d) OR unified across V3 + V4 + Mento V2 Broker (~900 events/30d)? Unifying adds density and captures more of the cCOP flow universe but requires a justified pooling assumption (the three event classes must share a common arrival-process structure for joint Hawkes estimation to be valid). Resolved in Phase 0 / Phase 6. |

### Out of Scope additions (post-research)

- **MiniPay-by-preference candidate filter** — superseded (see memory `project_abrigo_x402_minipay_scope`).
- **Mento V3 FPMM as a candidate venue** — verified to hold zero local Mento stables.
- **Bridge-aggregator routers, generic SwapPools, Mento DAO/Labs treasury Safes, SubsidyProgram contracts, DEX fee-collectors, Ubeswap LP-token wrappers** — verified non-LP-aggregator (transient inventory or upstream-of-LP-layer); see `research/CANDIDATES.md` §5 anti-shortlist.
- **Bare-EOA top-holders of local stables** — out of scope per "application not EOA" rule, even when they may run sophisticated off-chain LP strategies. They are *clients* (potential hedge buyers), not *operators* (candidate apps).

---
*Last updated: 2026-05-25 after research + candidate discovery*
