# abrigo-x402 — Candidate Applications: LP-Position Aggregators on Celo (Mento Local Stables × USD-Stables)

**Researched:** 2026-05-25
**Confidence:** HIGH on on-chain identities (Blockscout verified contracts + Forno RPC reads); HIGH on the two named aggregator protocols (ICHI confirmed on its own docs page for chain Celo; Steer confirmed on DefiLlama as deployed on Celo); MEDIUM on TVL figures (computed at ad-hoc FX rates, see Method); HIGH on Phase-0 ineligibility verdicts of anti-shortlist entries.

> READ FIRST. The substrate for the B2 scope (Celo apps with observable cashflows in Mento *local* stablecoins routed through LP aggregation) **does exist** but is structurally thin: every cCOP/cKES/cNGN/cGHS/cZAR/cXOF/BRLm pool sits at $11k–$130k TVL, the cCOP/USDT pool has ~100–150 swaps over 30 days, and the only two applications that observably aggregate LP positions across these pools are **ICHI** and **Steer**. The substrate-too-thin signal from PITFALLS.md applies — not as a blocker, but as a sample-size warning that propagates directly into the Hawkes/NHPP estimation downstream.

---

## 1. Method

Order of operations and filters applied:

1. **Anchor stables (celopedia `contracts.md`):** Pulled the canonical Mento token addresses for the 7 in-scope local stables (cCOP=COPm `0x8A56...41eA`, cKES=KESm `0x456a...B0d0`, cNGN=NGNm `0xE270...6F71`, cGHS=GHSm `0xfAeA...7313`, cZAR=ZARm `0x4c35...0BF6`, cXOF=XOFm `0x73F9...9A08`, BRLm=cREAL `0xe853...4787`) and the USD-stables on Celo (USDm=cUSD `0x765D...282a`, USDC `0xcebA...118C`, USDT canonical `0x4806...3D5e` — note Celo has *two* USDT tokens; the LP-active one is `0x4806...3D5e`, not `0x617f...546`).
2. **Token-holder enumeration:** `GET https://celo.blockscout.com/api/v2/tokens/{stable}/holders` for each of the 7 local stables. Parsed top-25 holders, classified by `is_contract`, `name`, and `creator_address_hash`.
3. **Pool token-pair confirmation:** For every `UniswapV3Pool` named holder, read `token0()` (`0x0dfe1681`), `token1()` (`0xd21220a7`), `fee()` (`0xddca3f43`) via `forno.celo.org` `eth_call`. This gives definitive pool composition (no marketing-copy trust).
4. **LP-position owner enumeration:** For each pool, `GET .../addresses/{pool}/logs?topic=0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde` (Uniswap V3 `Mint(address,address indexed owner,int24,int24,uint128,uint256,uint256)` event). Owner = topic[1]. Aggregated by count of Mint events per owner.
5. **Owner classification:** For every owner contract, fetched address profile and creator hash to determine whether it is (a) the Uniswap V3 NonfungiblePositionManager (`0x3d79EdAaBC0EaB6F08ED885C05Fc0B014290D95A` = retail LPs), (b) a known aggregator factory child (ICHIVault factory `0x9FAb...418F`; Steer factory `0x116Dba5DcE9CcDA828218b7eB46406810632014C`), or (c) something else.
6. **Aggregator deployment enumeration:** For ICHI factory `0x9FAb...418F` pulled the `ICHIVaultCreated` event log (50 decoded events present on the most recent page) — full list of vault contracts deployed by ICHI on Celo with their `tokenA/tokenB/fee`.
7. **Mento Broker / V3 FPMM check:** Pulled the `FPMMDeployed` event log on the V3 FPMMFactory `0xa849...613b` to verify whether Mento Broker pools contain any local stable. Result: every FPMM pool deployed pairs **USDm against major-currency stables only** (USDC, USDT, EURm, GBPm, CHFm, JPYm). No local Mento stables in Mento Broker. So local-stable LP venues are Uniswap V3 only.
8. **Public-app verification:** WebFetch against `app.ichi.org` (HIGH-confidence: Celo listed on the chain selector) and DefiLlama `defillama.com/protocol/steer-protocol` (HIGH-confidence: Celo TVL $855 listed). Direct fetch against `app.steer.finance` returned empty body (JS-only); the on-chain trace plus the DefiLlama listing is the primary-source verification.
9. **TVL computation:** For each in-scope pool, fetched `token-balances` from Blockscout, divided by token decimals, then approximated USD value at ad-hoc FX rates (1 USD = 4000 COP, 130 KES, 1500 NGN, 12 cGHS, 18 ZAR, 600 XOF, 5 BRL; EUR=$1.09). TVL = (USD side) + (local side in USD). These are coarse — used only to flag substrate thickness, not for hedge calibration.
10. **Subgraph freshness check:** All Blockscout reads taken against head block `67821539` (timestamp ≈ 2026-05-25 fetch). No subgraph was used in this discovery pass (per Pitfall 9 free-tier discipline); on-chain reads were the canonical path.

---

## 2. Pool Enumeration

All pools below are **Uniswap V3 mainnet** on Celo (`UniswapV3Factory = 0xAfE208a311B21f13EF87E33A90049fC17A7acDEc`). Fee tier `100` = 0.01 %, `500` = 0.05 %. **No Uniswap V4 pool on the local-stable pairs surfaced as a top holder** (the V4 PoolManager `0x288d...87BC` does hold small balances of cCOP/cNGN/cGHS/cZAR but those are not material LPs).

| Local stable | Pool address | Counter | Fee | TVL (approx) | Verified |
|---|---|---|---|---|---|
| **cCOP** (COPm) | `0x2AC5baA668A8A58FD0e302B9896717484fd217B0` | USDT (`0x4806...`) | 100 | ~$92,873 | yes |
| **cKES** | `0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F` | USDT | 100 | ~$129,978 | yes |
| cKES | `0x95faa9a91cD6c1C018e4B1a6fC4c89D4F1695e5D` | USDm | 100 | ~$37,711 | yes |
| cKES | `0xb1Ed164c736909bA7ddBC1FeB7CEd4EAAD854a87` | BRLm | 100 | (small) | yes |
| cKES | `0xA143ccF73C25eeC6f38bD1b741043ebeA228b8e9` | EURm | 100 | (small) | yes |
| **cNGN** (NGNm) | `0x1e2F87e1f8056Fcd39695aAeb63cb475E1DD2318` | USDT | 100 | ~$58,968 | yes |
| **cGHS** (GHSm) | `0x6BAB3AfA6d0c42d539bcbc33Ffb68C0406913413` | USDT | 100 | ~$21,239 | yes |
| cGHS | `0xa4bC5Aa6229e6f2BaA4B8851b19342A1D1217C08` | CELO | 100 | (small) | yes |
| **cZAR** (ZARm) | `0xb793ff8031FCe64b3f553DBf40a70370FDEAC1C7` | USDT | 100 | ~$50,171 (one-sided) | yes |
| **cXOF** (XOFm) | `0x625cB959213D18a9853973C2220Df7287F1e5B7d` | **EURm** (not USDT) | 100 | ~$24,519 | yes |
| cXOF | `0xAA97F0689660eA15b7d6f84F2E5250B63f2b381a` | USDm | 100 | ~$11,404 | yes |
| cXOF | `0xc767C0b2E2e56C455fd29f9eE9b6e6F035C71Ed4` | CELO | 500 | (small) | yes |
| **BRLm** (cREAL) | `0x1625fE58Cdb3726e5841Fb2bb367Dde9AAa009B3` | USDT | 100 | ~$21,989 | yes |
| BRLm | `0xb6c8f9490314394CFc6EDacb8717bFDC1EB8dab5` | EURm | 100 | (small) | yes |

Substrate-thickness notes:
- **All flagged but not blocking.** The largest pool (cKES/USDT @ $130k) clears the $10k floor by an order of magnitude; the smallest pools (cXOF/USDm $11k, BRLm/EURm < $10k) are at-or-below the floor.
- **cCOP/USDT pool processed ~100–150 swap events over ~30 days** (Blockscout topic-filter pagination). This is at the lower bound of the 300-event NHPP/Hawkes floor from PITFALLS.md §1 — the LP-fee revenue leg sample-size risk surfaces immediately.
- **cZAR/USDT is one-sided**: 49.6k USDT vs only 543 USD-equiv of cZAR — pool price is at one band edge; LP fee rate is structurally compressed.
- **Mento V3 FPMM has zero local-stable pools.** Every `FPMMDeployed` event pairs USDm against USDC, USDT, EURm, GBPm, CHFm, or JPYm. The Mento Broker swap layer is not a candidate venue for cCOP/cKES/cNGN/cGHS/cZAR/cXOF/BRLm liquidity.

---

## 3. Top LP-Position Holders per Pool

Counts below are `Mint` events per owner across the most recent ~50 Mint events available on Blockscout's `logs` endpoint (`topic=0x7a53...0bde`). The "26-vs-24" two-vault pattern repeating across every pool is the ICHI signature: one "deposit token0" vault + one "deposit token1" vault per pool.

**cCOP/USDT pool `0x2AC5...17B0`** (3 owners total):
| Owner | Classification | Mints (sample) |
|---|---|---|
| `0x71d69f8eaA11b293EC9de8C56550d57Dcd372202` | **Steer** BeaconProxy (impl `0xC1Ec...081c`) | 34 |
| `0x94E4728eCfd3E1B73D67d687eED8B8C4C6814439` | **Steer** BeaconProxy (impl `0xC1Ec...081c`) | 15 |
| `0x95F02276b5656b79bE2F5Ca89618B70214165C1d` | **Steer** `STEER_UNIV3_VAULT_52` (factory `0x116Dba...014C`) | 1 |

**cKES/USDT `0x61Ef...829F`** (2 owners):
| `0xce2e58630C76f76C355109fff1E2976a2C409bd2` | **Steer** `STEER_UNIV3_VAULT_12` | 42 |
| `0xe304b980535c29869983BC58d129F984Fec4176F` | **ICHI** ICHIVault | 8 |

**cKES/USDm `0x95fa...95e5D`** (3 owners):
| `0xe5d19ae5271dcee3138d163dd7f7c662cfba7bbb` | **ICHI** ICHIVault | 30 |
| `0x388434da760b975ae20ab3c72d705a09ec9986d1` | **ICHI** ICHIVault | 18 |
| `0x3d79edaabc0eab6f08ed885c05fc0b014290d95a` | Uniswap V3 NPM (retail) | 2 |

**cNGN/USDT `0x1e2F...2318`** (5 owners):
| `0xAe3C63c6398cB63E2D6416C6D4a77aDdE8c717d1` | **ICHI** ICHIVault | 20 |
| `0x62cCf2a34db6Bd68C74c85f996f4566c12e64732` | **Steer** BeaconProxy | 15 |
| `0x8cBFFbC031A8e3627456774b6337baC75640ceAc` | **ICHI** ICHIVault | 12 |
| `0x3d79edaabc0eab6f08ed885c05fc0b014290d95a` | Uniswap V3 NPM (retail) | 2 |
| `0xF7eAef3a41Dc6b1ce129994e05D085658C63D1bC` | **Steer** `STEER_UNIV3_VAULT_93` | 1 |

**cGHS/USDT `0x6BAB...3413`** (2 owners): both **ICHI** ICHIVault (`0x93e2...224B`, `0x3fdA...A6bF`).

**cZAR/USDT `0xb793...C1C7`** (2 owners): both **ICHI** ICHIVault (`0xdf15...99fA`, `0xb563...0BeE`).

**cXOF/EURm `0x625c...5B7d`** (2 owners): both **ICHI** ICHIVault (`0x72c7...37dF`, `0xe942...7077`). The first is also tagged as token `ICHI_Vault_LP` (ERC-20, ICHI's LP receipt token) — direct shortlist evidence.

**cXOF/CELO `0xc767...1Ed4`** (2 owners): both **ICHI** ICHIVault (`0xd3d0...0eb3`, `0xa991...ee26`).

**BRLm/USDT `0x1625...09B3`** (2 owners): both **ICHI** ICHIVault (`0xe7fc...60d4`, `0x9ee7...45c5`).

**BRLm/cKES `0xb1Ed...4a87`** (2 owners): both **ICHI** ICHIVault.

Two patterns to lock in:

- **ICHI** is the dominant LP-aggregator across cKES/cNGN/cGHS/cZAR/cXOF/BRLm. Every one of those pools has at least one verified `ICHIVault` (creator = `ICHIVaultFactory 0x9FAb...418F`) holding active LP positions.
- **Steer** is the dominant LP-aggregator on cCOP and a co-occupant on cKES and cNGN. All Steer vaults are `BeaconProxy` (impl `0xC1Ecd10398A6D7036CceE1f50551ff169715081c`) or named `STEER_UNIV3_VAULT_N` with creator = `0x116Dba5DcE9CcDA828218b7eB46406810632014C`.

No other LP-aggregator class (Beefy, Gamma, Arrakis, Velodrome ALM, Curve LP) shows up as a top-10 LP-position holder on any in-scope pool.

---

## 4. Candidate Applications Shortlist

### 4.1 ICHI (`app.ichi.org`)

| Field | Value |
|---|---|
| Application | ICHI — automated single-asset-deposit concentrated-liquidity vaults |
| Public URL | https://app.ichi.org/ (Celo listed in chain selector — primary verified) |
| Docs (Celo) | https://docs.ichi.org/home/contract-addresses — lists `0x9FAb4bdD4E05f5C023CCC85D2071b49791D7418F` for Celo |
| Vault factory (Celo) | `0x9FAb4bdD4E05f5C023CCC85D2071b49791D7418F` (Blockscout-verified, name `ICHIVaultFactory`) |
| Pools touched | cKES/USDT, cKES/USDm, cNGN/USDT, cGHS/USDT, cZAR/USDT, cXOF/EURm, cXOF/USDm, cXOF/CELO, BRLm/USDT, BRLm/EURm — *all* Mento local-stable pools surveyed have ICHI vault liquidity |
| Sample vault contracts (verified) | cXOF/cEUR: `0x72c7e587482C94ED2A0DD50A52BC2013Be3337dF` (LP-token symbol `ICHI_Vault_LP`); cKES/USDm: `0xE5D19ae5271DcEE3138D163dd7F7C662cfBA7BbB`; cNGN/USDT: `0xAe3C63c6398cB63E2D6416C6D4a77aDdE8c717d1`; cZAR/USDT: `0xdf156f474D5eDB15Ee67995207d961976E7099fA`; BRLm/USDT: `0xe7fcd93380d9a83564b75b63901711c93a1e60d4`; full list ≥ 40 vaults available from `ICHIVaultCreated` event log on the factory |
| Evidence of LP-aggregation | Verified contract source on Blockscout (`is_verified=true`, name `ICHIVault`); ERC-20 LP receipt token; bulk Uniswap V3 `Mint` event signatures (≥ 30 Mints per vault on active pools); `ICHIVaultCreated` events on the factory log enumerate the deployment set primary-source |
| Plausible data-cost class | Each vault must monitor (a) current pool `slot0` (tick + sqrtPriceX96) for in-range detection, (b) external price oracle (ICHI historically uses Chainlink+Pyth+Uniswap-TWAP composite; on Celo most likely Chainlink + on-chain pool TWAP), (c) rebalance triggers. Continuous polling of pool state for ≥ 40 vaults across Celo = ~40 × 1 query/min × 1440 = ~58k pool-state queries/day = ~1.7M/mo. Pure Graph subgraph reads ≪ that; most state would be on-chain `eth_call` via Forno RPC. Direct subgraph reads for analytics/UI plausibly land **inside the demand window**: rough estimate ~50k–200k Graph queries/mo ≈ $0–$80/mo on Graph paid tier, comfortably under $390/mo Dune Plus and meaningfully above the 100k free-tier ceiling at the upper end |
| Country lane | ICHI is chain-agnostic; on Celo the lane spans every Mento local-stable corridor (KES, NGN, GHS, ZAR, XOF, BRL, COP). No single country focus |
| **Phase-0 verdict** | **PASS — eligible.** (1) Mainnet contract: PASS — `0x9FAb...418F` verified on Celo. (2) Cashflow medium: PASS — vaults hold cKES/cNGN/cGHS/cZAR/cXOF/BRLm and pair them with USDT/USDC/USDm. (3) Event observability: PASS — Uniswap V3 Mint/Burn events on the wrapped pools + ICHI's own deposit/withdraw events on the vault. (4) Sample size: BORDERLINE — most active vaults have 20–40 lifetime Mints; this is the LP rebalance count not the swap count, and the underlying pool swap counts (cKES/USDT ≈ 130 over 30d) are below the 300-event floor for Hawkes per PITFALLS.md §1. (5) Deployment age: PASS — earliest vault created at block 28527843 (~mid-2024), so ≥ 1 year of activity. |

### 4.2 Steer Protocol (`app.steer.finance`)

| Field | Value |
|---|---|
| Application | Steer Protocol — concentrated-liquidity management with strategist-curated rebalancing |
| Public URL | https://app.steer.finance/ (DefiLlama confirms Celo deployment with $855 TVL — primary-source via DefiLlama API) |
| Vault factory (Celo) | `0x116Dba5DcE9CcDA828218b7eB46406810632014C` (Blockscout-verified `TransparentUpgradeableProxy`; `VaultCreated` events confirm ≥ 50 deployments visible on most-recent log page) |
| Pools touched | cCOP/USDT (3 active vaults), cKES/USDT (1 active vault), cNGN/USDT (2 active vaults). Steer is the *exclusive* LP-aggregator on cCOP. |
| Sample vault contracts | cCOP/USDT: `0x71d69f8eaA11b293EC9de8C56550d57Dcd372202` (BeaconProxy), `0x94E4728eCfd3E1B73D67d687eED8B8C4C6814439` (BeaconProxy), `0x95F02276b5656b79bE2F5Ca89618B70214165C1d` (`STEER_UNIV3_VAULT_52`); cKES/USDT: `0xce2e58630C76f76C355109fff1E2976a2C409bd2` (`STEER_UNIV3_VAULT_12`); cNGN/USDT: `0xF7eAef3a41Dc6b1ce129994e05D085658C63D1bC` (`STEER_UNIV3_VAULT_93`), `0x62cCf2a34db6Bd68C74c85f996f4566c12e64732` (BeaconProxy) |
| Implementation (impl behind beacons) | `0xC1Ecd10398A6D7036CceE1f50551ff169715081c` |
| Evidence of LP-aggregation | Beacon-proxy upgrade pattern; `VaultCreated(address deployer, address vault, string beaconName)` events on the factory; ≥ 34 `Mint`s on a single Steer vault on the cCOP pool (the highest-activity LP owner anywhere in the cCOP substrate) |
| Plausible data-cost class | Strategist-curated rebalance triggers driven by off-chain monitoring; on Celo Steer also leverages Gelato keepers historically (verify per-vault). Data-cost surface: continuous pool-state polling (slot0 + tick liquidity) per managed vault + strategy backtests. Total Celo footprint is ~5–10 active vaults so a *much* smaller per-strategist data cost than ICHI's 40+. Plausibly $0–$40/mo Graph spend; **may sit below the demand window's lower bound** for Celo alone (the protocol-level data spend across 42 chains is large, but the per-Celo-deployment slice is small). Falsification-gate risk: this candidate plausibly *fails* the "above-free-tier" lower bound when sliced to Celo only. |
| Country lane | Multi-chain; on Celo concentrated on Colombia (cCOP), Kenya (cKES), Nigeria (cNGN) corridors |
| **Phase-0 verdict** | **CONDITIONAL PASS — eligibility hinges on cost-leg lower bound.** (1) Mainnet contract: PASS — Steer factory verified. (2) Cashflow medium: PASS — vaults hold cCOP/cKES/cNGN paired with USDT. (3) Event observability: PASS. (4) Sample size: BORDERLINE on cCOP (only ~50 Mint events; pool swaps ~150/mo, below the 300-event Hawkes floor). (5) Deployment age: PASS. **Cost-leg bound (Pitfall 6):** Steer-on-Celo with 5–10 vaults and modest TVL ($855 per DefiLlama) is more likely to land *below* the Graph free tier than above $390/mo — the *protocol-level* spend across 42 chains is irrelevant to this project, and Celo-only spend may not clear the demand window's lower bound. This must be verified before estimation starts. |

### 4.3 (No other applications clear the gate)

Beefy, Velodrome ALM, Gamma, Arrakis: **not present** as top LP-position holders on any in-scope pool. Searched the top-25 token holders for every local stable; no vault contracts named after these protocols surfaced. They may have *swap volume* on Celo but they do **not** appear to operate LP-aggregator vaults on the Mento local-stable pools as of 2026-05-25.

---

## 5. Anti-Shortlist (mandatory, mirror of Myriad/Halo learnings)

### 5.1 BridgersSwap (`0x467B254a41df8D98ce89eAf840eA69C36d4567e4`, `0x66d31fB7E471D30dc314e04Aa819A29e5C554E09`, `0xF22d9Cc5328a08afC86595B9B373668049F87c2E`)

- **First glance**: Three contracts named `BridgersSwap` collectively hold ~167k cNGN (~3rd–6th largest non-Uniswap holder of cNGN).
- **Primary-source check**: Contract source is verified on Blockscout; name says "BridgersSwap" which is a **bridge aggregator router** (Bridgers DEX aggregator — see `bridgers.xyz`), not an LP-position aggregator. Each contract holds transient inventory for swap routing, not concentrated-liquidity positions.
- **Verifiable evidence of mismatch**: No Mint events from any of the three Bridgers contracts against any Uniswap V3 pool on the in-scope set. They appear in `holders` because they hold transient cNGN inventory between bridge-in and bridge-out hops, not because they provide liquidity.
- **Phase-0 verdict**: **FAIL on check (3)** — no LP-event observability. Bridgers' cashflow leg is bridge fees, not LP fees. Out of B2 scope.

### 5.2 SwapPool (`0xACfa7344807480C908eC1a1316134eA0d3EE13f0`, `0xD12F1aE0C018210d18F6cB01cD6c7bd669eF7529`)

- **First glance**: Verified contracts named `SwapPool` holding ~42k+17k BRLm (~4th–8th BRLm holder).
- **Primary-source check**: Creator is `0xd08913a93C2C28B2BF6717264378C57083a5eF5c` — an unknown EOA. Contract is verified but the name `SwapPool` is generic. No Uniswap V3 Mint events from these addresses on the BRLm pools. Likely an internal swap-pool of an off-chain remittance app holding inventory, not an LP aggregator.
- **Phase-0 verdict**: **FAIL on check (3)** — no LP-aggregation behavior observed. Same class of fail as Bridgers: transient inventory holder, not LP service.

### 5.3 Mento DAO / Mento Labs Treasury Safes (Gnosis Safes `0x5f41...01B3`, `0xBDf7...0E48`, `0x36139e35...0B92`, `0x6C6Dc3D4...3D49`, `0x4C3e0D2d...e2d4a`, `0x9fb57E91...10A9`, `0x655133d8...0150`, `0x1D918355...1dE8`)

- **First glance**: Several Gnosis Safes appear repeatedly across the top holders of cCOP, cKES, cGHS, cZAR, cXOF, BRLm (eight Safes total, some holding millions of local-stable tokens — `0x5f41...01B3` holds 22.8 M cCOP and 72k BRLm).
- **Primary-source check**: Common creator = Gnosis Safe Proxy Factory `0xC22834581EbC8527d974F8a1c97E1bEA4EF910BC` (i.e. the *generic* GnosisSafeProxyFactory, not a project tag). These are most consistent with **Mento DAO / Mento Labs operations Safes holding reserve or liquidity-incentive funds**, not LP-position aggregators. No Uniswap V3 Mint events from these Safes on any in-scope pool.
- **Verifiable evidence of mismatch**: A Safe holding 22M cCOP without minting LP positions is balance-sheet inventory, not LP service. It is the *source* of liquidity-incentive grants, not an LP service taker.
- **Phase-0 verdict**: **FAIL on check (3)** — no LP-event observability. They are *upstream* of the LP layer (incentive granters), not LP-fee earners. If treated as candidates, the project would be modeling Mento Labs' own treasury, not a third-party app.

### 5.4 SubsidyProgram (`0x947C6dB1569edc9fd37B017B791cA0F008AB4946` — 3rd largest cCOP holder, 18.3M cCOP)

- **First glance**: Holds 18.3M cCOP, second-largest non-Uniswap holder.
- **Primary-source check**: Named `SubsidyProgram` on Blockscout — i.e., a Mento subsidy distribution contract, not an LP aggregator. No Uniswap V3 Mint events observed.
- **Phase-0 verdict**: **FAIL** — incentive-distribution contract, same disqualification class as the Mento DAO Safes.

### 5.5 ICHI vault on COPM (Minteo cCOP-clone, `0xC92E8Fc2947E32F2B574CCA9F2F12097A71d5606`)

- **First glance**: ICHI factory log shows two vaults paired with `0xC92E8Fc...` = **COPM (Minteo)**, not the Mento-native cCOP at `0x8A56...41eA`. Specifically `0x9F2bB8B7dFF141e1e35d05D6B8215BA8634fFce8` and `0xB52CfF57Cf94717193C63fbcdd50d09EdEe3FBF5`.
- **Primary-source check**: COPM is explicitly noted as OUT of Mento-native scope in the research-task brief (it is Minteo's privately-issued cCOP-like stable, not Mento Reserve-backed). These vaults are *real LP-aggregator deployments* but they sit on the *wrong stablecoin*.
- **Phase-0 verdict**: **FAIL on cashflow-medium scope (check 2)** — same class of disqualification as the Myriad-on-points-USDT case in PITFALLS.md §1: the application exists, the contracts are verified, but the stable they sit on is not in the Mento local-stable scope. If user broadens to "Mento-or-Minteo" in §6, these become eligible.

### 5.6 TokenChwomper (`0xde7259893Af7cdbC9fD806c6ba61D22D581d5667` — 11th cZAR holder)

- **First glance**: Verified contract named `TokenChwomper` holding small cZAR balance.
- **Primary-source check**: `TokenChwomper` is the canonical SushiSwap-protocol fee-collection contract name. Creator is an EOA. This is Sushi-Swap-on-Celo fee dust, not an LP aggregator. No Mint events from this contract.
- **Phase-0 verdict**: **FAIL** — fee-collector, not LP service.

### 5.7 Ubeswap LP Token (`0x67449E82A0D354d34e6B7487A968EB3E15Cd47b9` — 10th BRLm holder)

- **First glance**: Holds ~37k BRLm and is named "Ubeswap LP Token". Ubeswap is Celo-native DEX (V2 + V3).
- **Primary-source check**: This is a single **Ubeswap V2 pair contract** (creator = Ubeswap V2 Factory `0x62d5b84bE28a183aBB507E125B384122D2C25fAE`), holders_count=4. It is a *pool*, not an LP-aggregator service. The 4 holders are direct retail LPs (no aggregator vault on top). Ubeswap V2 itself has no concentrated-liquidity-management vault deployed on the in-scope pools, and Ubeswap V3 (separate factory `0x67FEa58D5a5a4162cED847E13c2c81c73bf8aeC4`) was not surfaced as a top holder of any local Mento stable.
- **Phase-0 verdict**: **FAIL** as an *application* shortlist — Ubeswap is a DEX, not a third-party LP service. It would be a candidate venue, not a candidate operator. The single Ubeswap V2 BRLm pair has 4 LPs and is substrate-too-thin even by the project's lowest floor.

### 5.8 Bare-EOA top holders (`0xC35641C58b70d826d2105095C3d57F001d5aC92f` 4.5M cKES; `0x185080...f909` 14M cCOP; `0xCCA057Da...8a06` 5.4M cCOP; `0x4263DF45...317A` 2.1M cCOP; etc.)

- **First glance**: Large EOA balances in local stables — could be market makers running scripted LP strategies.
- **Primary-source check**: EOAs are by definition not "applications" per the brief's anti-EOA rule. Even if they run sophisticated off-chain LP strategies via the Uniswap V3 NonfungiblePositionManager, they have no public site, no public repo, and no verifiable application identity. They are *clients* (potential hedge buyers), not *applications* (candidate operators).
- **Phase-0 verdict**: **OUT OF SCOPE per brief** — these are EOAs, not applications. Recorded here only because the brief explicitly required surfacing anti-shortlist evidence.

---

## 6. Open Questions for User Decision

1. **ICHI vs Steer — primary candidate.** ICHI is the *broader* substrate (≥ 40 Celo vaults across every Mento local stable surveyed), Steer is the *only* LP-aggregator on cCOP/USDT and the most consistent with the project's prior cCOP focus. Which becomes Iteration 1's anchor? Recommendation: **ICHI first** — bigger sample for NHPP/Hawkes, multi-corridor diversification, well-documented public deployment registry. Steer becomes Iteration 2 (replacing Halo), which also re-tests reproducibility across two structurally different LP-management classes (single-asset-deposit auto-rebalance vs. strategist-curated rebalance).
2. **Substrate thickness vs. forced reframe.** The cCOP/USDT pool's ~100–150 monthly swaps is below the PITFALLS.md §1 Hawkes floor (300). Three options: (a) accept that Iteration 1 will ship as "indistinguishable NHPP/Hawkes" null result on cCOP — which is itself a publishable finding; (b) shift the anchor pool to **cKES/USDT** ($130k TVL, the densest in the substrate) where the sample is likely cleanest; (c) extend the panel to multi-pool aggregate (ICHI's full Celo footprint) at the cost of a more complex bivariate model. User decision needed.
3. **Counter-stable selection.** Most local-stable pools pair against USDT (`0x4806...3D5e`), not USDC. The original FX-hedge thesis assumed USDC depeg as a tail risk. With USDT as the dominant counter-stable, the tail risk class shifts to USDT depeg + USDT/USDC basis risk. Does the project rescope to USDT or keep modeling USDC depeg and accept that the actual cashflow leg is USDT-denominated?
4. **Per-protocol vs. per-vault granularity.** ICHI's data-cost class is plausibly aggregated at the protocol level (one Graph subscription, one keeper service). Modeling a single Celo *vault* as the "protocol" overstates the per-unit data cost. Decide: (a) model ICHI-on-Celo as one entity with one data-cost leg + revenue summed across all its Celo vaults; (b) pick one representative vault (e.g. cKES/USDm `0xE5D1...7BbB`) and treat as a microcosm.
5. **Minteo COPM inclusion.** ICHI's two COPM (Minteo `0xc92e8Fc...`) vaults exist. The research-task explicitly excluded COPM from Mento-native scope, but these vaults are the closest analogue to a "Colombia corridor LP aggregator" available on Celo. If the user permits a controlled broadening to "Mento + Minteo for the COP corridor," these become a fourth eligible vault class. Otherwise they stay anti-shortlisted.
6. **Cost-leg empirical bounds.** Per PITFALLS.md §6, before stipulating the data-cost prior, attempt: (a) count of `eth_call`s a vault keeper would need against Forno (slot0 + tick liquidity per pool per rebalance window) — a 1-minute polling cadence × ~5 pools × 30 days = ~216k calls/mo, free per Forno SLA, $0 cost, *below* the demand window's lower bound; (b) the analytics/UI subgraph reads ICHI/Steer themselves run for their front-end leaderboards — this is the leg that plausibly sits in the demand window and is the right surface to estimate. User: agree that the data-cost leg should be defined narrowly as "indexer-backed analytics/UI queries", not "keeper polling"?
7. **TVL-too-thin floor.** Two pools (cXOF/USDm $11k, BRLm/EURm < $10k) sit at or below the substrate floor. Drop them from the panel, or include them with explicit substrate-too-thin flags propagated into the Hawkes branching-ratio CI?

---

## 7. Hidden-Volume Audit 2026-05-25 (post-thinness-skepticism)

This section stress-tests the "~130 swaps/30d on cKES/USDT and ~100–150/30d on cCOP/USDT" finding from §2 against alternative venues, batching/aggregation channels, and broader event classes per the thinness-skepticism discipline. **Headline result: the original thinness finding is FALSE — the cKES/USDT and cCOP/USDT Uniswap V3 Swap counts were undercounted by ~6×–34× due to a block-time miscalibration in the §1 method; the corrected 30-day Swap counts clear the 300-event Hawkes floor without needing to broaden the event class.** Two channels (Mento V2 Broker on cCOP; Uniswap V4 hooks routing cCOP) add additional uncounted but small volume; all other gap channels rule out.

### 7.1 Method (delta from §1)

Queries executed against `celo.blockscout.com/api/v2` and `forno.celo.org` (no API key, head block ≈ 67,826,000, 2026-05-25T16:30 UTC). Block-time used: **~1 second/block** (post-2024 Celo L2 hardfork; the §1 Method implicitly used a 5-second baseline which produced the original thinness number — primary error). Specific endpoints used:

- `/addresses/{factory}/logs` with `PairCreated` (Ubeswap V2 topic `0x0d3648bd...`) / `PoolCreated` (Ubeswap V3 + Sushi V3 topic `0x783cca1c...`) — paginate full history, decode topics 1+2 for stable hits.
- `/tokens/{stable}/transfers` paginated for top-of-history Transfer events per stable, decompose by `from.name` × `to.name` to separate DEX-routed from wallet-to-wallet flow.
- `/addresses/{aggregator}/token-transfers` for ZeroEx, 1inch v6 router candidates, BridgersSwap contracts.
- `/addresses/{pool}/logs?topic={Swap}` paginated for full 30-day cKES/USDT and cCOP/USDT Swap counts.
- `eth_getBlockByNumber` via Forno for block→timestamp conversion (block 67,591,867 = 2026-05-22T23:30:25 UTC, block 67,824,856 = 2026-05-25T16:13:34 UTC → **1.00 second/block confirmed**).
- Mento docs (`docs.mento.org/mento-v3/build/deployments/addresses.md`) for V2 Broker (`0x777A8255cA72412f0d706dc03C9D1987306B4CaD`) + BiPoolManager (`0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901`).
- DefiLlama for Carbon DeFi on Celo TVL ($1.74M), Sushi on Celo TVL ($600k), Velodrome (404 — not deployed on Celo).
- Uniswap docs (`developers.uniswap.org/contracts/v4/deployments`) for canonical V4 PoolManager on Celo (`0x288dc841A52FCA2707c6947B3A777c5E56cd87BC`).

No subgraph use. All counts are from Blockscout pagination of decoded logs.

### 7.2 Per-channel findings

#### Channel 1 — Alternative Celo DEX venues

**Ubeswap V2** (`0x62d5b84bE28a183aBB507E125B384122D2C25fAE`) — full history paginated (~10 pages, all `PairCreated` events). Local-stable hits: **0 cCOP, 0 cKES, 0 cNGN, 0 cGHS, 0 cZAR, 0 cXOF, 7 BRLm**. Of the 7 BRLm pairs only 3 have any liquidity. Most active is `0x67449E82A0D354d34e6B7487A968EB3E15Cd47b9` (cUSD/BRLm, token0=`0x765de8...282a` USDm, token1=`0xe8537a...4787` BRLm): **25 V2 Swap events in ~566k blocks ≈ 6.5 days → ~115 swaps/30d**. The other live pair `0xe8f4c4...0c3c` is CELO/BRLm (out-of-counter-scope, CELO not USD-stable). **Verdict: rules out for cCOP/cKES/cNGN/cGHS/cZAR/cXOF; raises BRLm count by ~115/30d on USDm counter, which is small but additive to BRLm Phase-0 analysis.**

**Ubeswap V3** (`0x67FEa58D5a5a4162cED847E13c2c81c73bf8aeC4`) — full history paginated (~130 PoolCreated events total). Local-stable hits: **2 BRLm pools, 0 cCOP, 0 cKES, 0 cNGN, 0 cGHS, 0 cZAR, 0 cXOF**. Both BRLm pools are effectively dead — USDT/BRLm `0x48854b22ef0c6417b17fa0ae74abadc69725705c` has 13 V3 Swaps over ~34M blocks (~395 days), ~1/30d. **Verdict: rules out.**

**Carbon DeFi on Celo** (`0x6619871118D144c1c28eC3b23036FC1f0829ed3a`, verified `OptimizedTransparentUpgradeableProxy`) — DefiLlama reports $1.74M TVL on Celo, the largest of Carbon's 5 chains. Direct token-balance read on the Controller shows: USDC $724k, USDT $237k, USDGLO $29k, **cUSD/USDm $24k, cEUR $297, cREAL ≈ $0, no cCOP/cKES/cNGN/cGHS/cZAR/cXOF at all**. The entire $1.74M is USDC+USDT+stCELO+CELO; local Mento stables are absent. **Verdict: rules out.**

**SushiSwap V2** (`0xc35DADB65012eC5796536bD9864eD8773aBc74C4`) — paginated history. Local-stable PairCreated hits: **1 cKES pair (`0x145cc935...` cKES/UnknownToken `0x62b8b110...`), 3 BRLm pairs**. All effectively dead — cKES pair latest activity at block 54M (year-old), BRLm pairs at ~56M block. No swaps in the last 30 days on any. **Verdict: rules out.**

**SushiSwap V3** (`0x93395129bd3fcf49d95730D3C2737c17990fF328`) — only **6 PoolCreated events ever** on Celo, **none containing a local Mento stable**. **Verdict: rules out.**

**Velodrome on Celo** — DefiLlama lookup `defillama.com/protocol/velodrome-finance` returned 404 + docs site refused connection; per Velodrome's product positioning (Optimism + Base focus) it has **no Celo deployment**. **Verdict: rules out by primary-source absence.**

**Uniswap V4 on Celo** (canonical PoolManager `0x288dc841A52FCA2707c6947B3A777c5E56cd87BC`, verified). Direct `balanceOf(PoolManager)` reads via Forno:
| Stable | PoolManager balance | USD-eq |
|---|---|---|
| cCOP | 7,428,279.84 | ~$1,857 |
| cNGN | 73,063.18 | ~$49 |
| cXOF | 27,012.18 | ~$45 |
| cKES | 6,271.48 | ~$48 |
| cZAR | 802.70 | ~$45 |
| cGHS | 528.88 | ~$44 |
| BRLm | 263.78 | ~$53 |

V4 PoolManager is highly active (50 Swap events in 2,391 blocks ≈ ~40 min → **~10,800 V4 swaps/30d total**), but the cCOP balance dominates the local-stable footprint. Decomposing the cCOP Transfer panel: **35 of 100 cCOP transfers in a 67.5-hour window had PoolManager on one side** (see §7.2 channel 3 below) — implying ~12.4/day cCOP-V4 transfers ≈ **~180/30d cCOP V4 flow, ~90 cCOP/X V4 swaps/30d**. V4 hooks/pools on cCOP exist but the through-volume is an order of magnitude below the cCOP/USDT V3 anchor. The four unverified contracts that mediate this flow (`0x5DC3065ed4b...`, `0xf9e41C21F27A...`, `0xbECBd94b00...`, `0x288dc8...87BC` itself) are likely PositionManager / UniversalRouter components, not LP-aggregator vaults. **Verdict: raises cCOP count by ~90 swaps/30d (additive, observable as separate event class — V4 Swap topic `0x40e9ce...`); rules out as LP-aggregator venue.**

#### Channel 2 — Mento Broker V1 + V2

**Mento V2 Broker** (`0x777A8255cA72412f0d706dc03C9D1987306B4CaD` BrokerProxy, verified). **BiPoolManager** (`0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901` BiPoolManagerProxy, verified). Activity: BiPoolManager emits 50 events in ~7,653 blocks (~2.1 hrs → **~17,200/30d**), Broker emits 50 events in ~3,282 blocks (~55 min → **~39,000/30d**).

The §1 §1.7 enumeration covered the **V3 FPMM** (`0xa849...613b`) and confirmed it pairs only USDm against major-currency stables. **V2 BiPoolManager exchanges** were not checked. Decoded Broker V2 Swap events in current sample show tokens `0x471ece37` (CELO), `0x765de8...282a` (USDm), `0x48065fbb...3D5e` (USDT), `0xceba9300...118C` (USDC), `0xD8763CBa...6CA73` (EURm) — **no cCOP/cKES/cNGN/cGHS/cZAR/cXOF/BRLm in the Broker Swap stream**.

However: **the cCOP token Transfer panel (next channel) shows 28 of 100 transfers involving BrokerProxy on cCOP over a 67.5-hour window** → ~12 transfers/day × 30 = **~370 cCOP-Broker-related transfers/30d, implying ~185 Broker-mediated cCOP mint/burn pairs/30d**. This appears to be a Reserve-mint path that doesn't surface in BiPoolManager `PoolBalancesUpdated` events but does emit ERC-20 Transfer events with BrokerProxy as a counterparty. The exact mechanism (V2 Reserve.mint of cCOP via a non-FPMM exchange contract, or Mento Router routing through an off-FPMM cCOP pair) was not pinned down with one more drill-down query.

For cKES, sample of 200 Transfer events had **0 BrokerProxy involvement** — Mento V2 Broker is not active on cKES.

**Verdict: raises cCOP count by ~185 Broker-mediated swap-equivalents/30d (uncounted in §2's cCOP/USDT V3 figure); rules out for cKES/cNGN/cGHS/cZAR/cXOF/BRLm. The cCOP Broker mechanism is inconclusive — would require one more on-chain trace to identify the exact exchange contract.**

**Mento V1** — V1's `Exchange.sol` contracts (one per currency pair) were superseded by V2 BiPoolManager + V3 FPMM. Mento docs `docs.mento.org/mento-v3/build/deployments/addresses.md` lists only V2 and V3 contracts. No deprecated V1 Exchange addresses surface in the top-25 holders of any local stable. **Verdict: rules out V1.**

#### Channel 3 — Total Transfer-event volume per local stable

`/tokens/{stable}/transfers` first-page sample with block-time conversion (1 s/block confirmed):

| Stable | Page-1 sample (n=50) span (blocks) | Span (hours) | Extrapolated transfers/30d |
|---|---|---|---|
| cKES | 4,044 | 1.12 | **~32,400** |
| cCOP | 7,010 | 1.95 | **~18,500** |
| cNGN | 1,300,963 | 361 (~15 days) | **~100** |
| cGHS | 3,596 | 1.00 | **~36,000** |
| cZAR | 52,661 | 14.6 | **~2,460** |
| cXOF | 4,147 | 1.15 | **~31,300** |
| BRLm | 4,909 | 1.36 | **~26,400** |

**Decomposition for cKES (200-transfer sample over 12,895 blocks ≈ 3.6 hrs):**
| From → To | Count | Category |
|---|---|---|
| UniswapV3Pool → UniswapV3Pool | 87 | DEX router multi-hop (already in §2 Swap counts) |
| unverified-contract → UniswapV3Pool | 18 | aggregator router into pool |
| UniswapV3Pool → unverified-contract | 18 | aggregator router out of pool |
| ICHIVault → GnosisSafeProxy | 16 | ICHI deposit/withdraw to user Safe |
| UniswapV3Pool → ICHIVault | 14 | ICHI rebalance leg (already in pool Mint/Burn) |
| ICHIVault → UniswapV3Pool | 11 | ICHI rebalance leg |
| SwapRouter02 → UniswapV3Pool | 11 | Uniswap V3 direct route |
| UniswapV3Pool → SwapRouter02 | 11 | Uniswap V3 direct route |
| EOA → UniswapV3Pool | 7 | retail LP add or direct swap |
| UniswapV3Pool → EOA | 7 | retail LP remove or swap-out |

**~99% of cKES Transfer activity has a Uniswap V3 Pool, ICHI Vault, or SwapRouter on at least one side.** Net wallet-to-wallet retail/merchant transfers in the sample: ≤ 2/200. **The cKES Transfer panel is NOT a separate revenue arrival process; it is a 6×–10× amplified projection of the same Swap stream (each swap emits 2 Transfers, multi-hop routes amplify further).**

**Decomposition for cCOP (100-transfer sample over 48,621 blocks ≈ 13.5 hrs):**
| From → To | Count | Category |
|---|---|---|
| BrokerProxy → EOA | 17 | **Mento V2 Broker mint of cCOP to user — uncounted** |
| PoolManager → unverified-contract | 16 | **Uniswap V4 routing through cCOP — uncounted** |
| unverified-contract → PoolManager | 13 | V4 routing |
| EOA → BrokerProxy | 11 | **V2 Broker burn of cCOP — uncounted** |
| UniswapV3Pool → EOA | 11 | V3 direct swap (already counted) |
| SubsidyProgram → EOA | 5 | Mento subsidy distribution (incentive, not LP fee) |
| unverified-contract → BrokerProxy | 5 | Broker via router |
| PoolManager → UniswapV3Pool | 3 | V4↔V3 routing |
| UniswapV3Pool → unverified-contract | 3 | V3 aggregator |
| PoolManager → EOA | 3 | V4 direct |
| EOA → unverified-contract | 3 | wallet→aggregator |
| MentoRouter → BrokerProxy | 1 | Mento Router (V2 path) |

**Net uncounted cCOP volume in §2:** ~34 Broker transfers (~185 swap-equivalents/30d) + ~35 V4 transfers (~190 swap-equivalents/30d) = **~375 additional cCOP swap-equivalents/30d on top of the V3 anchor pool count**.

For cNGN: per-30d Transfer total is **only ~100** (substrate genuinely thin — the Transfer panel CONFIRMS, does not contradict, the thinness for cNGN specifically; cNGN/USDT V3 pool ~$59k TVL is the entire venue).

**Verdict: For cKES — the Transfer panel does NOT raise the count; it is DEX-amplification of the same Swap stream. For cCOP — the Transfer panel raises the count by ~375 swap-equivalents/30d via Broker + V4 channels, additive to the V3 anchor. For cNGN — Transfer panel CONFIRMS thinness (~100 transfers/30d total).**

#### Channel 3.bis — Recount of the anchor pool Swap events (corrects §2)

Paginated full Swap-event log for cKES/USDT and cCOP/USDT pools via `/addresses/{pool}/logs?topic=0xc42079f9...` (Uniswap V3 Swap topic), with primary-source block→timestamp conversion via `eth_getBlockByNumber`:

| Pool | Swaps paginated | Block range | Time span | **Swaps/30d** |
|---|---|---|---|---|
| cKES/USDT `0x61Ef...829F` | 400 | 67,591,867 → 67,824,856 | 2026-05-22T23:30 → 2026-05-25T16:13 (2.7 days) | **~4,440** |
| cCOP/USDT `0x2AC5...17B0` | 600 (paged 12 pages) | 65,146,204 → 67,824,856 | ~31.0 days | **~580–625** |

**The §2 figures (130/30d and 100–150/30d) appear to have used a 5-second/block assumption** which inflates "30 days" by 5×, dividing the true count by 5×–34×. Confirmed via Forno `eth_getBlockByNumber` against block 67,591,867 (2026-05-22T23:30:25 UTC) and block 67,824,856 (2026-05-25T16:13:34 UTC) → **1.00 s/block on Celo** (consistent with the post-2024 hardfork). The cKES/USDT and cCOP/USDT pool Swap streams are **both ≥ 580/30d, well above the 300-event Hawkes floor**.

**Verdict: PRIMARY THINNESS FINDING IS REFUTED.** The original ~130 swaps/30d on cKES/USDT figure was a counting error; corrected count is ~4,440 swaps/30d. The cCOP/USDT count is ~580–625 swaps/30d, not ~100–150.

#### Channel 4 — DEX / bridge aggregator routed volume

**0x Protocol (ZeroEx Celo, `0xDef1C0ded9bec7F1a1670819833240f027b25EfF`, verified)**: last 50 token transfers are at block 27.7M–28.3M (~year-old), zero local-Mento-stable hits. ZeroEx on Celo is dormant. **Rules out.**

**1inch v6 router** (canonical `0x111111125421cA6dc452d289314280a0f8842A65`): Blockscout reports `verified=False, name=None` on Celo — not a real deployment. **Rules out.**

**SwapRouter02** (`0x5615cdab10dc425a742d643d949a7f474c01abc4`, verified Uniswap V3 router) appears in cKES sample as 11+11 transfers — these are direct V3 swaps already counted as Pool Swap events. **Double-counting flagged — no additive volume.**

**BridgersSwap** (anti-shortlisted in §5.1 as 3 contracts; current top-25 cNGN holders show **7 BridgersSwap contracts** with combined balance ~306k cNGN, larger than originally noted). Bridgers is a bridge aggregator; balances are transient inventory between bridge legs. No Uniswap V3 Mint events from any Bridgers contract on the in-scope set; their flow does not pass through Uniswap V3 cNGN/USDT (otherwise it would appear as router-mediated Swap events already counted). The **direct-aggregator-to-Mento-Broker path is implausible because Mento Broker has no cNGN exchange** (channel 2 verdict). Bridgers' cNGN inventory is most likely tied to **off-chain remittance settlement** that does not touch any observable LP venue. **Verdict: rules out as additive Swap volume; flags cNGN as a substrate where bridge-aggregator inventory dwarfs LP-pool TVL ($306k Bridgers cNGN inventory vs $59k LP-pool TVL — Bridgers inventory is 5× the LP pool's local-stable side). This is a downstream demand signal worth noting but not an LP-fee revenue source.**

**Squid / LI.FI / Socket / Symbiosis**: any local-stable volume they route on Celo would flow through Uniswap V3 (the only material venue per §2 and channels 1–2 above). Routed-through volume is already in §2 Swap counts. **No additive flow possible without a separate venue, which doesn't exist.**

**Verdict: rules out all aggregator channels as sources of additive uncounted swap volume.**

#### Channel 5 — MiniPay payment-processor settlement flows (Bitgifty etc.)

Bitgifty (`www.bitgifty.com`) publishes no Celo contract addresses on its public site (per fetch — page describes only "decentralized application across multiple EVM chains" without addresses). Top-25 holder enumeration of every local stable (channels 1+3 work) surfaced **zero contracts tagged "Bitgifty", "MiniPay", "payment", "merchant", or "remit"**. The named contracts surfacing in cKES/cCOP/cNGN/cGHS holders are exhaustively: UniswapV3Pool, ICHIVault, GnosisSafeProxy, SubsidyProgram, BridgersSwap, BrokerProxy, SwapPool (already anti-shortlisted §5.2), PoolManager (V4), STEER_UNIV3_VAULT_N, FeeCollector, BeaconProxy, OptimizedTransparentUpgradeableProxy, ERC1967Proxy. **No identifiable payment-processor settlement contract surfaces.**

The single ambiguous case is the `0xD1088D3376C2384D469d1c0d55D503695e1BE3E6` cNGN holder (35.1M cNGN, ~$23k, unverified contract, recent activity in USDC/USDT/wUSD₮/wCELO). Its activity profile — multi-stable inventory with USDT-heavy throughput — is most consistent with a bridge/aggregator inventory contract, not a payment processor settling fiat off-chain. Without a verified source or public attribution this cannot be conclusively classified.

**Verdict: inconclusive but bounded.** Bitgifty / MiniPay payment processors are NOT visibly present on-chain as named contracts holding meaningful local-stable inventory. If they do route through Celo, they either (a) operate via EOAs (out-of-scope by brief) or (b) settle through Mento Broker (channel 2 ruled out for cKES/cNGN/cGHS/cZAR/cXOF/BRLm; partial cCOP exposure already counted) or (c) settle directly through Uniswap V3 pools (already counted). The 30-day Transfer-panel decomposition (channel 3) shows **≥ 99% of cKES Transfer events are DEX-routed**, leaving < 1% headroom for any unobserved merchant/payment channel on cKES. The same bound holds for cCOP (≥ 95% of Transfer activity decomposed to V3 + V4 + Broker + Subsidy).

#### Channel 6 — Mento Labs treasury swap flows

Anti-shortlisted in §5.3 — the eight Gnosis Safes hold large local-stable inventories but emit no Uniswap V3 Mint events. Re-check during this audit: in the cKES 200-transfer sample, GnosisSafeProxy receives ICHI vault payouts (16 instances) but does NOT initiate swaps against any local-stable Uniswap V3 pool. No Safe-initiated swap stream surfaces. **Verdict: rules out — confirms §5.3.**

### 7.3 Updated thinness verdict

**The original CANDIDATES.md §2 thinness finding ("cKES/USDT ~130 swaps/30d; cCOP/USDT ~100–150 swaps/30d") is REFUTED by primary-source recount.** Corrected 30-day Uniswap V3 Swap counts on the anchor pools, with timestamp verification via Forno `eth_getBlockByNumber`:

- **cKES/USDT: ~4,440 swaps/30d** (14.8× above the 300-event Hawkes floor)
- **cCOP/USDT: ~580–625 swaps/30d** (~2× above the floor)

The root cause of the §2 undercount was a Celo block-time miscalibration (5 s/block used implicitly; true is 1 s/block post-2024). The thinness finding is no longer load-bearing.

**Recommended revenue-arrival event class for the project:** **Uniswap V3 Swap events on the anchor pool** (`Swap` topic `0xc42079f9...`) remains the correct dependent variable — it directly drives the LP-aggregator's fee accrual and is the only event class where the project has a clean economic interpretation (swap fee × fee tier = revenue per event). ICHI vault deposit/withdraw events are the **wrong** dependent variable for the revenue arrival process — they are demand for the aggregator's service, not revenue events per se (fee revenue accrues on the underlying Uniswap V3 swaps, not on user deposits). ERC-20 Transfer events on the local stable are not a separate signal — they are DEX-amplified projections of the Swap stream (channel 3 decomposition).

Two **additive** event-class contributions for the cCOP corridor (not for cKES):
- Mento V2 Broker cCOP mint/burn: ~185 swap-equivalents/30d (uncounted in §2; routes through `BrokerProxy = 0x777A...4CaD`)
- Uniswap V4 PoolManager cCOP routing: ~90 V4 swaps/30d (uncounted in §2; routes through `PoolManager = 0x288d...87BC`)

These extend the cCOP arrival process from ~625/30d to ~**900/30d** if all three event classes are counted, but the cleanest single dependent variable remains the V3 anchor pool Swap stream.

### 7.4 Implication for the locked Iteration-1 candidate (ICHI on cKES/USDT)

**Phase-0 verdict: UNCHANGED — ICHI on cKES/USDT remains PASS-eligible.** The audit strengthens, not weakens, the candidate:

- Sample-size (check 4) was BORDERLINE in §4.1 because of the (now-refuted) 130 swaps/30d figure. **Re-status: PASS comfortably** — 4,440 cKES/USDT swaps/30d is 14.8× the 300-event Hawkes floor.
- Panel construction: **use cKES/USDT Uniswap V3 Swap events as the dependent variable**, not Transfer events (which would inflate the panel ~7× via DEX amplification but introduce variance from multi-hop routing). PITFALLS.md §1 "sample-thinness propagates into Hawkes/NHPP CI" is now disposable — the cKES/USDT sample is dense enough for Hawkes branching-ratio estimation with usable CIs.
- The original Steer-on-cCOP Iteration-2 candidate (now §4.2) was CONDITIONAL PASS partly because of the ~150 swaps/30d figure. **Re-status for Iteration 2: PASS** — corrected cCOP/USDT count is ~580–625 swaps/30d, above the 300-event floor without needing to count Broker or V4 contributions. The cost-leg lower-bound concern (Steer-on-Celo's Graph spend possibly below the demand window) is the remaining binding constraint, untouched by this audit.

PITFALLS.md §1 (substrate-too-young / cashflow-medium-wrong) — the "thinness" diagnosis was a counting-artifact false positive (per `feedback_thinness_skepticism.md`), not a substrate-too-young real positive. The pitfall record itself remains valid as a discipline; the specific application of it to abrigo-x402 was wrong and is hereby retracted for cKES and cCOP.

### 7.5 Open questions for user decision (additive to §6)

8. **§2 figures retraction.** The original §2 cKES/USDT "~130 swaps/30d" and cCOP/USDT "~100–150 swaps/30d" numbers were derived under a 5 s/block assumption (implicit, not stated). They are **off by 6×–34×**. Should §2 be edited in place, or kept as-is with §7 as the corrective addendum? Recommendation: keep §2 as the record of the original pass (do-not-rewrite-history), but add a footnote pointing to §7.3 for the corrected counts.
9. **cCOP additive channels (Broker + V4).** ~375 swap-equivalents/30d of cCOP flow routes through Mento V2 Broker or Uniswap V4 PoolManager, additive to the V3 anchor's 625/30d. Decide: (a) include all three event classes as a unified arrival process (cleaner total ~1000/30d but multi-venue model adds spec complexity); (b) keep V3 anchor as the single dependent variable (simpler, ignores ~38% of the cashflow signal); (c) treat V3 as primary, Broker+V4 as covariates in a marked Hawkes model.
10. **cNGN substrate thinness — now load-bearing.** Channel 3 found cNGN has only ~100 Transfer events/30d total (the panel includes DEX, mint/burn, retail wallet — all of it). The cNGN/USDT V3 pool has $59k TVL but 7 BridgersSwap inventory contracts hold 5× that in cNGN (~$200k bridge inventory). This is the inverse pattern from cKES/cCOP. If the project ever extends to cNGN as an anchor pool, the thinness is real and binding. Decide: anti-shortlist cNGN explicitly as Iteration-3+ blocked-by-thinness, or treat as "would need bridge-flow analysis" caveat?
11. **Mento V2 Broker cCOP exchange identification.** The audit identified Broker-mediated cCOP mint/burn (~185/30d) via Transfer-panel decomposition but did NOT pin down the specific BiPoolManager exchange contract or the V2 routing path. One more on-chain query (decode a single BrokerProxy → EOA cCOP Transfer to its parent transaction's logs) would identify it. Worth the budget? Recommendation: defer to Iteration-2 spec build — only needed if cCOP becomes anchor.

---

## Sources

- Blockscout v2 API on Celo (`https://celo.blockscout.com/api/v2/...`) — verified contract names, source verification status, holder lists, decoded event logs. No API key required. Fetch timestamp: 2026-05-25, head block 67821539.
- Celo Forno RPC (`https://forno.celo.org`) — `eth_call` reads against `token0()`, `token1()`, `fee()`, `liquidity()`, `slot0()`, `pool()`, ICHIVault `name()`; `eth_getBlockByNumber` for block→timestamp conversion (§7 audit).
- Celopedia skill references: `contracts.md` (Mento token addresses + Uniswap V3 factory address), `defi-protocols.md` (Mento V3 FPMM addresses, Uniswap V3 NonfungiblePositionManager address).
- ICHI Docs — `https://docs.ichi.org/home/contract-addresses` (confirms `0x9FAb...418F` on Celo).
- ICHI App — `https://app.ichi.org/` (chain selector lists Celo).
- DefiLlama — `https://defillama.com/protocol/steer-protocol` (confirms Steer-on-Celo with $855 TVL); `defillama.com/protocol/carbon-defi` (Celo $1.74M TVL); `defillama.com/protocol/sushiswap` (Celo $600k TVL); `defillama.com/protocol/velodrome-finance` returned 404 (no Celo deployment).
- Mento Docs — `docs.mento.org/mento-v3/build/deployments/addresses.md` (Broker V2 + BiPoolManager Celo addresses).
- Carbon DeFi Docs — `docs.carbondefi.xyz/contracts-and-functions/contracts/deployments/mainnet-contracts.md` (Celo Controller `0x6619871118D144c1c28eC3b23036FC1f0829ed3a`).
- Uniswap Developer Docs — `developers.uniswap.org/contracts/v4/deployments` (Celo V4 PoolManager `0x288dc841A52FCA2707c6947B3A777c5E56cd87BC`).
- Project `PROJECT.md` (2026-05-25) — demand window, two-leg model, free-tier discipline.
- Project `research/PITFALLS.md` (2026-05-25) — substrate-too-young / cashflow-medium-wrong gate (§1), demand-window stipulation error (§6), reproducibility gate (§8), free-tier exhaustion (§9). §1 application to abrigo-x402 retracted per §7.3.
- Memory `feedback_thinness_skepticism.md` — the symmetric-burden discipline that drove this audit.
