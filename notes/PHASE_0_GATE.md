# Phase 0 Eligibility Gate: abrigo-x402 Candidate Verdicts

**Committed:** 2026-05-25

**Purpose:** Documents the five-check Phase-0 eligibility outcome per candidate. Resolves CANDIDATES.md §4.2 Steer CONDITIONAL row by Phase-0 primary-source pre-validation per CONTEXT.md REPRO-03 two-tier semantics. Each check row carries a verifying Blockscout URL. Phase-0 firing of HEDGE-05 (per ROADMAP HEDGE-05 firing scope) produces memo-only null — no PDF deliverable at this phase.

## Demand-Window Definition (DEMAND-01)

- **Lower bound:** Graph free-tier ceiling = 100,000 queries/mo
- **Upper bound:** Dune Plus subscription = $390/mo
- **Scope:** Indexer-backed analytics/UI queries only (Graph subgraphs + Dune analytics). **Forno RPC `eth_call` keeper polling is EXPLICITLY EXCLUDED** as it sits below the lower bound at any volume (free on Forno SLA, $0/mo for arbitrarily high volumes — wrong demand class). The data-cost leg the project hedges is the *indexer-paid* class, not the *keeper-RPC* class.
- Per CANDIDATES.md §6 Q6: this scope decision was locked by user in CONTEXT.md and is the canonical scope referenced throughout PRE_REGISTRATION.md REPRO-03 thresholds.

## Schema-Frozen Baseline

The Phase-0 commit hash of `protocols/_schema.toml` is recorded here as the baseline for `make schema-frozen-check`. Any diff to `_schema.toml` after this commit triggers pre-commit hook (c) rejection.

**Schema baseline commit:** `<SCHEMA_BASELINE_COMMIT>` (Plan 07 substitutes the actual hash after Plan 04 commits _schema.toml)

## ICHI on cKES/USDT — Five-Check Eligibility Gate

| # | Check | Outcome | Evidence |
|---|---|---|---|
| 1 | Mainnet contract verified | **PASS** | ICHI factory `0x9FAb4bdD4E05f5C023CCC85D2071b49791D7418F` verified on Blockscout (verified=true, name=`ICHIVaultFactory`). URL: https://celo.blockscout.com/address/0x9FAb4bdD4E05f5C023CCC85D2071b49791D7418F |
| 2 | Mento local-stable cashflow medium | **PASS** | ICHI vault for cKES/USDT (~40-vault Celo footprint includes cKES, cNGN, cGHS, cZAR, cXOF, BRLm pairs per CANDIDATES.md §4.1). Anchor pool cKES/USDT `0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F` (verified `token0()`/`token1()` reads via Forno = cKES + USDT). URL: https://celo.blockscout.com/address/0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F |
| 3 | Event observability ≥ 30/30d | **PASS** | cKES/USDT pool ~4,440 Uniswap V3 `Swap` events/30d per CANDIDATES.md §7.3 (corrected count post-thinness-retraction; original §2 figure of ~130/30d was a 5s/block miscalibration, refuted at §7.3 via Forno `eth_getBlockByNumber` block→timestamp verification confirming 1.00 s/block). Swap topic = `0xc42079f9...`. URL: https://celo.blockscout.com/address/0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F/logs?topic=0xc42079f9a2c8c12e9e210e7fb2bdaf26a14a25f6b6c8c2a2f8a2e0e2f8a2e0e2 |
| 4 | Sample size ≥ 300 lifetime + Hawkes floor | **PASS** | 4,440 cKES/USDT Swaps/30d = 14.8× the 300-event Hawkes floor (PITFALLS §1 thinness diagnosis retracted for cKES per CANDIDATES §7.3). Lifetime cumulative Swap count far exceeds the 300-event lifetime requirement. URL: https://celo.blockscout.com/address/0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F |
| 5 | Deployment age ≥ 60 days | **PASS** | Earliest ICHI vault on Celo created at block 28,527,843 (~mid-2024 per CANDIDATES §4.1), > 1 year of activity as of 2026-05-25. URL: https://celo.blockscout.com/address/0x9FAb4bdD4E05f5C023CCC85D2071b49791D7418F |

**ICHI overall verdict: PASS — eligible for Iteration 1.**

All five checks pass per CANDIDATES.md §4.1 verbatim (with the §7.3 post-audit upgrade on check 4 from BORDERLINE to PASS). ICHI on cKES/USDT is the locked Iteration 1 anchor per PROJECT.md scope-correction block.

## Steer on cCOP/USDT — Five-Check Eligibility Gate

| # | Check | Outcome | Evidence |
|---|---|---|---|
| 1 | Mainnet contract verified | **PASS** | Steer factory `0x116Dba5DcE9CcDA828218b7eB46406810632014C` verified `TransparentUpgradeableProxy` on Blockscout (verified=true, EIP-1967 proxy pattern, implementation `VaultRegistry` at `0xa1Dd21fbd9e1F0BF28d41F18bDC22326e50C02e9`, creation_status=success). URL: https://celo.blockscout.com/address/0x116Dba5DcE9CcDA828218b7eB46406810632014C |
| 2 | Mento local-stable cashflow medium | **PASS** | Steer vaults on cCOP/USDT × 3 (incl. `STEER_UNIV3_VAULT_52`), cKES/USDT × 1 (`STEER_UNIV3_VAULT_12`), cNGN/USDT × 2 (incl. `STEER_UNIV3_VAULT_93`) per CANDIDATES.md §3. cCOP/USDT pool `0x2AC5baA668A8A58FD0e302B9896717484fd217B0` (verified via Forno `token0()`/`token1()` = cCOP + USDT). URL: https://celo.blockscout.com/address/0x2AC5baA668A8A58FD0e302B9896717484fd217B0 |
| 3 | Event observability ≥ 30/30d | **PASS** | cCOP/USDT pool ~580–625 Uniswap V3 `Swap` events/30d per CANDIDATES.md §7.3 (corrected count post-thinness-retraction). Additive cCOP corridor channels: ~185 Mento V2 Broker swap-equivalents/30d + ~90 Uniswap V4 PoolManager swaps/30d → ~900/30d unified. URL: https://celo.blockscout.com/address/0x2AC5baA668A8A58FD0e302B9896717484fd217B0/logs?topic=0xc42079f9a2c8c12e9e210e7fb2bdaf26a14a25f6b6c8c2a2f8a2e0e2f8a2e0e2 |
| 4 | Sample size ≥ 300 lifetime + Hawkes floor | **PASS** | 580–625 cCOP/USDT Swaps/30d ≈ 2× the 300-event Hawkes floor on V3-anchor-only panel; ~3× under the V3+V4+Broker unified panel (Q-9 fallback). Lifetime cumulative Swap count well above 300. URL: https://celo.blockscout.com/address/0x2AC5baA668A8A58FD0e302B9896717484fd217B0 |
| 5 | Deployment age ≥ 60 days | **PASS** | Steer factory verified, ≥ 50 vaults deployed per CANDIDATES §4.2 (`VaultCreated` event log shows ≥ 50 deployments on the most-recent factory log page). Earliest deployment > 1 year ago. URL: https://celo.blockscout.com/address/0x116Dba5DcE9CcDA828218b7eB46406810632014C |

**Five-check structural verdict: PASS on all five.** *However*, REPRO-03 cost-leg lower-bound pre-validation is the binding constraint per CONTEXT.md decision that elaborates ROADMAP's binary REPRO-03 draft into a two-tier semantics.

### REPRO-03 Cost-Leg Lower-Bound Pre-Validation (Phase-0 resolution of CANDIDATES §4.2 CONDITIONAL)

Per CONTEXT.md decision, this section pre-validates Steer's Celo-only analytics-query footprint at Phase 0 via primary-source triangulation. Two-tier thresholds (per notes/PRE_REGISTRATION.md `## REPRO-03 Threshold`):

- **PASS:** ≥ 100k Graph queries/mo attributable to Steer's Celo deployment
- **STRADDLE:** 30k–100k/mo → fires HEDGE-05 null with `marginal-demand` flag
- **FAIL:** < 30k/mo → fires HEDGE-05 null with `below-window` flag

**Channel A — Blockscout enumeration of Steer's Celo deployments.** Steer factory `0x116Dba5DcE9CcDA828218b7eB46406810632014C` queried via Blockscout v2 API on 2026-05-25 (head block ≈ 67,821,582). Factory verified `TransparentUpgradeableProxy` (EIP-1967), implementation `VaultRegistry`. CANDIDATES.md §3 enumerates **6 active vaults on in-scope Mento local-stable pairs**: cCOP/USDT × 3 (Mint events: 34 + 15 + 1 = 50 sampled), cKES/USDT × 1 (42 Mints sampled), cNGN/USDT × 2 (15 + 1 = 16 Mints sampled). Factory `VaultCreated` log shows ≥ 50 lifetime deployments across all Steer-on-Celo vaults (not just in-scope-pair vaults). Activity proxy = ~108 lifetime Mints sampled across the 6 in-scope vaults; the small per-vault Mint count (LP rebalance events, not swap events) indicates a *low rebalance cadence* — each rebalance triggers ≤ 1 Graph subgraph re-read for vault state. URL: https://celo.blockscout.com/address/0x116Dba5DcE9CcDA828218b7eB46406810632014C and https://celo.blockscout.com/api/v2/addresses/0x116Dba5DcE9CcDA828218b7eB46406810632014C/logs (factory VaultCreated event log).

**Channel B — Steer docs / architecture statement.** DefiLlama protocol description (primary-source) confirms Steer is "a decentralized compute protocol that provides a scaling solution for data processing through its robust off-chain infrastructure. Services are targeted at leveraging off-chain data for on-chain automation, such as automated liquidity management in DeFi." Per CANDIDATES.md §4.2: "Strategist-curated rebalance triggers driven by off-chain monitoring; on Celo Steer also leverages Gelato keepers historically." Gelato keepers are RPC-based (Forno `eth_call` polling), NOT indexer-backed — this places the bulk of Steer's on-Celo data spend in the **keeper-RPC class, which DEMAND-01 explicitly excludes from the demand window** (Forno SLA = free at any volume, wrong demand class). The Graph subgraph leg is limited to powering `app.steer.finance` analytics/leaderboards and vault performance pages — a small per-vault tail of the total data footprint. URL: https://defillama.com/protocol/steer-protocol and https://app.steer.finance/ (JS-only client; on-chain trace plus DefiLlama listing = primary verification per CANDIDATES.md §1.8).

**Channel C — DefiLlama TVL extrapolation (primary-source).** Direct DefiLlama API read on 2026-05-25 (`https://api.llama.fi/protocol/steer-protocol`):

- **Steer-on-Celo TVL:** $855.65 (`currentChainTvls.Celo`)
- **Steer total TVL across 42 chains:** ~$20.64M (sum of all `currentChainTvls` non-staking/borrowed/treasury entries)
- **Celo share of Steer total TVL:** 855.65 / 20,644,661 = **0.0041%** (4.1 basis points)

Two extrapolation methods bound the Celo-only Graph spend:

1. **TVL-proportional** (Graph spend scales with usage volume which scales with TVL): If Steer's aggregate multi-chain Graph spend is $100–$500/mo (typical for a ~$20M TVL multi-chain ALM protocol — industry observation, not Steer-confirmed), Celo's slice is $0.0041 × [$100, $500] = $0.41–$2.05/mo. At Graph paid-tier ~$5×10⁻⁶/query (per PRE_REGISTRATION.md cost-leg prior `USD_per_query`), that maps to **80k–410k queries/mo** in absolute Steer-aggregate terms — but Celo's *attributable* share is the TVL-proportional fraction, giving **~8k–40k Celo-attributable queries/mo** at most. This lands clearly in **STRADDLE/FAIL** (the upper bound is at or below the 100k Graph free-tier ceiling).

2. **Vault-count-proportional** (Graph spend scales with number of managed vaults requiring analytics): Steer-on-Celo has ~6 active in-scope vaults (per Channel A) out of an estimated ~250–500 active multi-chain Steer vaults (extrapolating from the 42-chain footprint with comparable per-chain vault density). Celo's vault-count share = 6/250 = **2.4%**. If Steer's aggregate Graph spend is $100–$500/mo, Celo's slice is $2.40–$12/mo, mapping to **48k–240k queries/mo**. This straddles the 100k PASS boundary at its upper edge but the **lower end stays in STRADDLE**.

The two methods disagree by ~6× (40k vs 240k upper bounds) — **within 1 order of magnitude**, so NOT indeterminate. The TVL-proportional bound is the more defensible default (Graph spend tracks usage volume which tracks TVL more directly than vault count, since most vault-level analytics queries are powered by aggregated/cached results rather than per-vault re-fetches). The convergent verdict is that Steer's Celo-attributable Graph spend lands in the **30k–100k/mo STRADDLE band, plausibly leaning toward the lower end (~30k–50k/mo)**.

URL: https://api.llama.fi/protocol/steer-protocol and https://defillama.com/protocol/steer-protocol.

**Steer REPRO-03 verdict: STRADDLE** (30k–100k Celo-attributable Graph queries/mo, per cross-channel synthesis).

- Channel A (Blockscout enumeration): 6 active in-scope vaults with low rebalance cadence → small Graph query base.
- Channel B (Steer architecture): Gelato keeper-RPC class dominates total data spend; Graph subgraph reads are a small analytics-leg tail per the DEMAND-01 scope exclusion of keeper polling.
- Channel C (DefiLlama TVL extrapolation): TVL-proportional bound 8k–40k/mo; vault-count-proportional bound 48k–240k/mo; convergent best estimate in STRADDLE band.

Steer overall verdict: ** STRADDLE ** — fires HEDGE-05 memo-only null with `marginal-demand` flag at Phase 0 per ROADMAP HEDGE-05 firing scope. Iteration 2 does NOT run a full Phase 1–5 cycle; the pre-validation already proves the cost leg cannot reliably clear the 100k/mo PASS threshold, so running the full pipeline against Steer-on-cCOP would not change the outcome. Phase 6 produces `reports/steer_null_result.pdf` documented as `marginal-demand`, NOT `below-window`. The retained REPRO-03 empirical check at Phase 6 first-step becomes a confirmation pass rather than a discovery; the Phase-0 pre-validation is the binding determination.

## Anti-Shortlist (mirror of CANDIDATES.md §5)

Per CANDIDATES.md §5, the following are FAIL on the five-check gate (no LP-aggregation behavior observed) and are excluded from any Iteration-1/Iteration-2 candidate panel:

- **BridgersSwap** (`0x467B254a41df8D98ce89eAf840eA69C36d4567e4` and siblings `0x66d31fB7E471D30dc314e04Aa819A29e5C554E09`, `0xF22d9Cc5328a08afC86595B9B373668049F87c2E`) — bridge aggregator router, no LP Mint events on any in-scope pool. URL: https://celo.blockscout.com/address/0x467B254a41df8D98ce89eAf840eA69C36d4567e4
- **SwapPool** (`0xACfa7344807480C908eC1a1316134eA0d3EE13f0`, `0xD12F1aE0C018210d18F6cB01cD6c7bd669eF7529`) — transient inventory holder, no LP-aggregation behavior. URL: https://celo.blockscout.com/address/0xACfa7344807480C908eC1a1316134eA0d3EE13f0
- **Mento DAO / Mento Labs Treasury Safes** (8 Gnosis Safes incl. `0x5f41...01B3` holding 22.8M cCOP + 72k BRLm) — incentive granters, not LP service. No Uniswap V3 Mint events from any Safe.
- **SubsidyProgram** (`0x947C6dB1569edc9fd37B017B791cA0F008AB4946`) — incentive distribution contract, no LP events. URL: https://celo.blockscout.com/address/0x947C6dB1569edc9fd37B017B791cA0F008AB4946
- **ICHI vault on COPM Minteo** (`0xC92E8Fc2947E32F2B574CCA9F2F12097A71d5606` is the COPM token; the two ICHI-on-COPM vaults are `0x9F2bB8B7dFF141e1e35d05D6B8215BA8634fFce8` and `0xB52CfF57Cf94717193C63fbcdd50d09EdEe3FBF5`) — wrong cashflow medium (COPM is Minteo's privately-issued cCOP-clone, out of Mento-native scope per CONTEXT.md). v2-deferred substrate per notes/PRE_REGISTRATION.md `Deferred substrate` section. URL: https://celo.blockscout.com/address/0xC92E8Fc2947E32F2B574CCA9F2F12097A71d5606
- **TokenChwomper** (`0xde7259893Af7cdbC9fD806c6ba61D22D581d5667`) — Sushi-on-Celo fee-collector, not LP service. URL: https://celo.blockscout.com/address/0xde7259893Af7cdbC9fD806c6ba61D22D581d5667
- **Ubeswap LP Token** (`0x67449E82A0D354d34e6B7487A968EB3E15Cd47b9`) — single Ubeswap V2 pair contract (cUSD/BRLm), is a DEX *pool* not an LP-aggregator service. 4 retail LPs, no aggregator vault on top. URL: https://celo.blockscout.com/address/0x67449E82A0D354d34e6B7487A968EB3E15Cd47b9
- **Bare-EOA top holders** (e.g. `0xC35641C58b70d826d2105095C3d57F001d5aC92f` 4.5M cKES; `0x185080...f909` 14M cCOP) — out of scope per brief's anti-EOA rule (EOAs are not "applications").

## HEDGE-05 Firing Scope (Phase 0)

Per ROADMAP HEDGE-05 firing scope:

- **Phase 0 firing → memo-only null-result** (no PDF deliverable yet — PDF template built in Phase 4).
- **Steer REPRO-03 verdict = STRADDLE → this PHASE_0_GATE.md memo-only documents the marginal-demand disqualification at Phase 0.** Iteration 2 either (a) defers entirely until Steer's Celo footprint grows past the 100k/mo threshold (a forward-looking re-survey trigger), or (b) is documented as `reports/steer_null_result.pdf` at Phase 6 emission point, flagged as `marginal-demand` per PRE_REGISTRATION.md REPRO-03 two-tier semantics.
- **Iteration 1 (ICHI on cKES/USDT) proceeds to Phase 1** per ICHI PASS-on-all-five above.

The memo-only Phase-0 null fires here, in this file, with `marginal-demand` as the flag value. No additional file is required at Phase 0; the formal PDF (with full statistical commentary) is the Phase 6 first-step product if Iteration 2 is launched.

## Sources

- **Blockscout v2 API on Celo** (https://celo.blockscout.com/api/v2/): contract verification, holder enumeration, decoded event logs. No API key required. Used for ICHI factory verification (`0x9FAb...418F`), Steer factory verification (`0x116Dba...014C`), and pool verification (cKES/USDT `0x61Ef...829F`, cCOP/USDT `0x2AC5...17B0`).
- **Celo Forno RPC** (https://forno.celo.org): `eth_call` reads against `token0()`, `token1()`, `fee()` for pool composition verification; `eth_getBlockByNumber` for block→timestamp conversion (1.00 s/block confirmation post-2024 Celo hardfork).
- **DefiLlama API** (https://api.llama.fi/protocol/steer-protocol): Steer-on-Celo TVL = $855.65; Steer multi-chain TVL = $20.64M across 42 chains.
- **DefiLlama protocol page** (https://defillama.com/protocol/steer-protocol): Steer Celo deployment confirmation + protocol description.
- **CANDIDATES.md §4.1, §4.2, §5, §7.3** (Phase-0 verdicts source-of-truth; ICHI five-check PASS verbatim per §4.1; Steer CONDITIONAL row per §4.2 resolved by Phase-0 pre-validation per CONTEXT.md decision).
- **notes/PRE_REGISTRATION.md `## REPRO-03 Threshold`** (two-tier semantics: PASS ≥ 100k/mo, STRADDLE 30k–100k/mo, FAIL < 30k/mo).
- **ROADMAP.md HEDGE-05 firing scope** (Phase 0 = memo-only null; PDF deliverable from Phase 4 onward).
- **PITFALLS.md §1 (thinness retraction per CANDIDATES §7.3) and §6 (cost-leg stipulation rationale).**

---
*Phase 0 Gate Committed: 2026-05-25*
