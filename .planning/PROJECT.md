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

---
*Last updated: 2026-05-25 after initialization*
