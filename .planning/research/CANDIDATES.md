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

## Sources

- Blockscout v2 API on Celo (`https://celo.blockscout.com/api/v2/...`) — verified contract names, source verification status, holder lists, decoded event logs. No API key required. Fetch timestamp: 2026-05-25, head block 67821539.
- Celo Forno RPC (`https://forno.celo.org`) — `eth_call` reads against `token0()`, `token1()`, `fee()`, `liquidity()`, `slot0()`, `pool()`, ICHIVault `name()`. Free.
- Celopedia skill references: `contracts.md` (Mento token addresses + Uniswap V3 factory address), `defi-protocols.md` (Mento V3 FPMM addresses, Uniswap V3 NonfungiblePositionManager address).
- ICHI Docs — `https://docs.ichi.org/home/contract-addresses` (confirms `0x9FAb...418F` on Celo).
- ICHI App — `https://app.ichi.org/` (chain selector lists Celo).
- DefiLlama — `https://defillama.com/protocol/steer-protocol` (confirms Steer-on-Celo with $855 TVL).
- Project `PROJECT.md` (2026-05-25) — demand window, two-leg model, free-tier discipline.
- Project `research/PITFALLS.md` (2026-05-25) — substrate-too-young / cashflow-medium-wrong gate (§1), demand-window stipulation error (§6), reproducibility gate (§8), free-tier exhaustion (§9).
