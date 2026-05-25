# Stack Research

**Domain:** Empirical FX-cashflow modeling pipeline for MiniPay-hosted Celo apps; data-cost legs paid via x402.
**Researched:** 2026-05-25
**Overall confidence:** MEDIUM-HIGH
**Verification basis:** Live npm registry + PyPI JSON API pulls 2026-05-25; viem chain definition source on GitHub HEAD; mento-sdk README on GitHub HEAD; x402 monorepo README. Training-data versions IGNORED — every version below was retrieved live today.

---

## TL;DR — One-Liner Per Choice

| Layer | Library | Version (verified 2026-05-25) | Why this one |
|---|---|---|---|
| TS package manager | `pnpm` | 11.3.0 | Workspace support for `client/` + `contracts/`; same as `abrigo-analytics`. Node 22 LTS required. |
| TypeScript | `typescript` | 6.0.3 | Current; required by codegen v7 |
| TS Ethereum lib | `viem` | 2.51.0 | The 2026 standard; required peer of every x402 EVM package and Mento SDK 3.x. ethers is the explicit non-choice. |
| TS x402 transport | `@x402/fetch` | 2.13.0 | The scoped, actively-maintained x402 v2 fetch wrapper (org: `x402-foundation`). Auto-handles 402 → sign → retry. Released 3 days ago. |
| TS x402 EVM signer | `@x402/evm` | 2.13.0 | Provides the EVM signing primitives `@x402/fetch` calls into; uses viem under the hood. |
| TS x402 core types | `@x402/core` | 2.13.0 | Transitive via `@x402/fetch` and `@x402/evm`. Pin via pnpm to keep all three in lockstep. |
| TS Graph paid client | `@graphprotocol/client-x402` | 1.0.0 | **Official.** Built on top of `@x402/fetch` (`^2.8.0`), brings auto-pay for The Graph gateway without an API key. Settles on Base / Base Sepolia. |
| TS Graph SDK build | `@graphprotocol/client-cli` | 3.0.7 | Used **only** as the build tool that `@graphprotocol/client-x402`'s typed-SDK workflow drives. We do NOT use it for runtime queries — it has no x402 hook and is a year stale. |
| TS Graph minimal client | `graphql-request` | 7.4.0 | Used for direct subgraph calls that fall on the free 100k/mo tier (no payment); pairs with codegen. |
| TS Graph codegen | `@graphql-codegen/cli` + `@graphql-codegen/typescript-graphql-request` | cli 7.0.0, plugin 7.0.1, typescript-plugin 6.0.1 | Schema-first typing for Myriad, Mento, Celo Transfer subgraphs. Type-safety against subgraph drift. |
| TS chain RPC | `viem` (Celo + Base chain objects) + Blockscout REST | viem 2.51.0 | `forno.celo.org` is the free RPC (hardcoded in `viem/chains/celo`); Blockscout (`celo.blockscout.com/api`) is free, no key. |
| TS Mento integration | `@mento-protocol/mento-sdk` | 3.2.8 | Official; viem-native (peer `viem ^2.21.44`). Provides `Mento.create(ChainId.CELO)`, `tokens.getStableTokens()`, broker discovery. Replaces hard-coded address lists. |
| TS Mento typed ABIs | `@mento-protocol/mento-core-ts` | 2.6.5-rc3 | RC tag — only use for raw ABI imports; do not rely on stable semver. |
| TS validation | `zod` | 4.4.3 | Runtime subgraph-response validation; transitive peer of x402 packages anyway |
| TS env | `dotenv` | 16.x | Standard |
| TS test runner | `vitest` | 4.1.7 | Replaces jest+ts-jest for batch pipelines |
| TS lint/format | `@biomejs/biome` | 2.4.15 | Replaces eslint+prettier; faster |
| TS script runner | `tsx` | 4.22.3 | No build step for `scripts/*.ts` |
| Py runtime | Python 3.12 (uv-managed venv) | 3.12.x | `tick==0.8.0.2` ships cp311–cp314 wheels; 3.12 is the safe middle. |
| Py env manager | `uv` | 0.11.16 | 2026 standard; required by `feedback_python_venv.md`. |
| Py NHPP / Hawkes estimation | `tick` | 0.8.0.2 (released 2026-05-04) | Only Python library that's (a) actively maintained 2026, (b) supports multivariate parametric Hawkes (`HawkesExpKern`, `HawkesSumExpKern`, `HawkesEM`, `HawkesConditionalLaw`), (c) ships fast C++-backed MLE. `hawkeslib` (canerturkmen) is dead and univariate-only; `pyhawkes` is just primitives. |
| Py INAR(p) bin-count (Kirchner 2015) | `statsmodels.tsa.api.VAR` + custom non-negativity projection | statsmodels 0.14.6 | Kirchner's estimator reduces to constrained VAR; ~80 lines on `statsmodels`. Validate against `tick.hawkes.SimuHawkesExpKernels` synthetic data. |
| Py array stack | `numpy`, `pandas`, `polars` | numpy 2.4.6, pandas 3.0.3, polars 1.41.0 | polars for the panel build (millions of Transfer rows); pandas for small estimation frames. Pandas 3.0 is current. |
| Py LR test (Chen et al. 2017) | `scipy.stats.chi2` + hand-rolled LR on `tick` log-likelihoods | scipy 1.17.1 | Two log-lik + χ² tail; no third-party dep |
| Py Carr–Madan strip | `numpy` + `scipy.integrate` + `scipy.interpolate` (numerical strip) | scipy 1.17.1 | Strip is ~50 lines of numpy |
| Py FX-option sanity check | `QuantLib` Python | 1.42.1 | Garman-Kohlhagen baseline against our strip — cross-check tool only, not the implementation. |
| Py I/O | `pyarrow` | 24.0.0 | Parquet caching of the on-chain panel |
| Py notebooks | `marimo` + `jupyter` | marimo 0.23.8, jupyter 7.x | marimo for reactive dependency-graph notebooks; jupyter for share/export |
| Py plotting | `plotly` + `matplotlib` | plotly 5+, mpl 3.9+ | plotly interactive event-arrivals; mpl paper figures |
| Py lint/format | `ruff` | 0.15.14 | Replaces black+isort+flake8 |
| Py test | `pytest` | 9.0.3 | Validates Kirchner INAR(p) against tick's answer on synthetic data |

---

## Recommended Stack — Detailed

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **TypeScript** | 6.0.3 | Type system | Required by `@graphql-codegen/cli@7` |
| **viem** | 2.51.0 | Ethereum interaction, signing, ABI typing, multi-chain client (Celo + Base) | 2026 default; peer of every other EVM lib here. First-class `chains.celo` (id 42220) and `chains.base` (id 8453). |
| **`@x402/fetch`** | 2.13.0 | Fetch wrapper that handles 402 → sign payment → retry | x402 v2 spec, scoped `@x402/foundation` org. The unscoped `x402-fetch@1.2.0` exists and is also current, but `@x402/fetch` is the path The Graph's `@graphprotocol/client-x402` depends on — pick the one that's already in our dep tree. |
| **`@x402/evm`** | 2.13.0 | EVM signer + transport behind `@x402/fetch` | Required when paying real x402 invoices. |
| **`@graphprotocol/client-x402`** | 1.0.0 | The Graph's own x402-aware client; auto-pays gateway in USDC on Base, no API key | This is the on-ramp the existing PROJECT.md `Tech stack` constraint asks for — note the constraint named `@graphprotocol/client-x402` and that package now exists (published 2026-04-14). |
| **`graphql-request`** | 7.4.0 | Minimal typed GraphQL client used for *free-tier* queries (no x402) | Tiny, no React/Apollo bloat. Plays cleanly with custom `fetch` injection if we want to wrap the free tier in a logger. |
| **`@graphql-codegen/cli`** | 7.0.0 | Codegen orchestrator | v7 supports the latest codegen plugins; v5 is obsolete |
| **`@graphql-codegen/typescript`** | 6.0.1 | Generates TS types from GraphQL schemas | Required base |
| **`@graphql-codegen/typescript-graphql-request`** | 7.0.1 | Generates a typed SDK targeting graphql-request | The SDK we wrap with the x402-aware fetcher |
| **`@mento-protocol/mento-sdk`** | 3.2.8 | Mento broker / pair / rate / swap access | Official; viem-native; `Mento.create(ChainId.CELO)` returns a typed client. Replaces 10+ hard-coded broker addresses. |
| **`@mento-protocol/mento-core-ts`** | 2.6.5-rc3 | Raw typed ABIs for Mento contracts | RC — use for ABI imports only; do not pin business logic |
| **Python** | 3.12 | Estimation runtime | Stable wheels across tick / numpy 2.x / statsmodels 0.14 |
| **uv** | 0.11.16 | Python venv + dep manager | 2026 standard; required by user memory `feedback_python_venv.md` |
| **tick** | 0.8.0.2 | Multivariate Hawkes simulation + MLE fitting | Only complete option (see "Hawkes/INAR decision" below) |
| **statsmodels** | 0.14.6 | VAR regression backbone for Kirchner INAR(p) implementation | `tsa.api.VAR` covers the multivariate bin-count estimator with non-negativity projection |
| **numpy** | 2.4.6 | Array math | Latest stable; numpy 2.x is the baseline for the rest of the scientific stack |
| **pandas** | 3.0.3 | Estimation frames | pandas 3.0 is current; works with numpy 2.x |
| **polars** | 1.41.0 | Panel construction on millions of Transfer rows | Orders faster than pandas for groupby on large event panels |
| **scipy** | 1.17.1 | LR test, numerical integration for strip | Standard |
| **QuantLib (Python)** | 1.42.1 | FX-option sanity check (Garman-Kohlhagen) | Cross-check only |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `dotenv` (TS) | 16.x | Load `.env` (`PRIVATE_KEY`, `CELO_RPC_URL`, `BASE_RPC_URL`) | Always |
| `zod` | 4.4.3 | Runtime subgraph-response validation | When subgraph is decentralized-network-hosted and may drift |
| `tsx` | 4.22.3 | Run TS scripts without a build step | `scripts/*.ts` iteration |
| `vitest` | 4.1.7 | Test runner | Unit tests on cost decomposition + ABI parsing |
| `pyarrow` | 24.0.0 | Parquet I/O | Cache panel between runs; avoid burning Graph queries |
| `marimo` | 0.23.8 | Reactive notebooks | Hawkes fit → LR test → strip params dependency chain |
| `jupyter` | 7.x | Classic notebooks | For sharing `.ipynb` artifacts |
| `pytest` | 9.0.3 | Test runner | INAR(p) validation against tick synthetic data |
| `ruff` | 0.15.14 | Lint + format | One tool replaces black/isort/flake8 |
| `@biomejs/biome` | 2.4.15 | Lint + format TS | Faster than eslint+prettier |
| `axios` (TS) | — | Only if we need `@x402/axios` instead of `@x402/fetch` for streaming uploads | Defer; fetch is enough |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `pnpm` 11.3 | TS workspace package manager | Workspaces: `client/` (Graph + x402), `pipeline/` (Python via uv), `contracts/` (deferred to Iteration 3) |
| `uv` 0.11 | Python env + lock | `uv venv --python 3.12 && uv pip install -e pipeline/` |
| `direnv` | Auto-load `.env` and venv on `cd` | Avoids wrong-python footgun |
| `pre-commit` | Git hook runner | Runs `ruff`, `biome`, `vitest --run` on staged files |
| `gh` | GitHub CLI | Required by `CLAUDE.md` (PRs to `upstream:master`) |
| Node 22 LTS | JS runtime | `pnpm@11` engine requirement |

---

## Installation

### TypeScript side (`client/`)

```bash
# Workspace bootstrap
pnpm init
pnpm add -D typescript@^6 tsx@^4.22 vitest@^4.1 @biomejs/biome@^2.4 @types/node

# Core EVM + x402
pnpm add viem@^2.51 \
         @x402/fetch@^2.13 \
         @x402/evm@^2.13 \
         @x402/core@^2.13

# Graph clients
pnpm add @graphprotocol/client-x402@^1.0      # paid gateway, x402-aware
pnpm add graphql graphql-request@^7.4         # free-tier direct queries

# Codegen (dev)
pnpm add -D @graphql-codegen/cli@^7 \
            @graphql-codegen/typescript@^6 \
            @graphql-codegen/typescript-operations@^6 \
            @graphql-codegen/typescript-graphql-request@^7

# Mento + validation
pnpm add @mento-protocol/mento-sdk@^3.2.8 \
         @mento-protocol/mento-core-ts \
         zod@^4 dotenv
```

### Python side (`pipeline/`)

```bash
uv venv --python 3.12
source .venv/bin/activate

# Core estimation
uv pip install \
  "tick==0.8.0.2" \
  "numpy>=2.4,<3" \
  "pandas>=3.0,<4" \
  "polars>=1.41,<2" \
  "scipy>=1.17,<2" \
  "statsmodels>=0.14.6,<1"

# Sanity + notebooks + plotting + I/O
uv pip install "QuantLib>=1.42" marimo jupyter plotly matplotlib pyarrow

# Dev
uv pip install pytest ruff
```

---

## Hawkes / INAR Library Decision — Concrete

The arrival-process question this project ships against: *Does the joint arrival process of Myriad's bet inflows and oracle settlements reject NHPP in favor of multivariate Hawkes?* That requires fitting BOTH families on the same data, comparing log-likelihoods, and running the Chen et al. 2017 LR test.

| Library | Last release | Multivariate Hawkes? | INAR(p) bin-count path? | MLE? | Verdict |
|---|---|---|---|---|---|
| **`tick`** (X-DataInitiative) | **2026-05-04** (v0.8.0.2) | Yes — `HawkesExpKern`, `HawkesSumExpKern`, non-parametric `HawkesConditionalLaw` + `HawkesEM` | Indirectly via simulation + custom bin-count VAR | Yes (`.fit`) | **CHOSEN.** |
| `hawkeslib` (canerturkmen) | 2019, README redirects to tick | Univariate only | No | Yes | **Reject** — dead, univariate. |
| `pyhawkes` / `py-hawkes` (ragoragino) | ~2020 | Yes (sim / compensator / log-lik only) | No | Helpers only | **Reject** — not an estimator, just primitives. |
| R `hawkes` (`rpy2` bridge) | Maintained | Yes | No | Yes | **Reject as primary** — adds R + rpy2 dependency; slower than tick per tick paper benchmarks. Acceptable as a peer-review cross-check. |

**INAR(p) implementation (Kirchner 2015):** tick does not expose Kirchner's bin-count INAR(p) estimator directly. We implement it on top of `statsmodels.tsa.api.VAR`: multivariate bin counts → constrained least-squares → non-negativity projection on AR coefficients. ~80 lines, matches the algorithm in the paper, matches the path `abrigo-analytics` used at E10.

**Validation test (pytest):** simulate from `tick.hawkes.SimuHawkesExpKernels`, bin to a daily grid, recover parameters via our INAR(p), confirm agreement with tick's `HawkesExpKern.fit` on the same realization within a tolerance.

**Confidence:** HIGH on library choice (tick is the only live option). MEDIUM on INAR(p) implementation effort estimate.

---

## Graph Client Decision — Concrete

PROJECT.md's `Constraints` block named `@graphprotocol/client-x402` and `@graphprotocol/client-cli` as the data-fetch stack. Live npm inspection 2026-05-25 confirms:

| Package | Status | Decision |
|---|---|---|
| `@graphprotocol/client-x402` | v1.0.0, published 2026-04-14, depends on `@x402/fetch ^2.8.0` and `@x402/evm ^2.8.0`. README: "automatic payment handling using the x402 protocol, no API key required!" Settles on Base / Base Sepolia. | **USE for paid gateway queries.** This is the canonical x402 path. |
| `@graphprotocol/client-cli` | v3.0.7, published 2024-08-22 (≈21 months stale). | **USE only as the codegen build tool** that `@graphprotocol/client-x402`'s typed-SDK workflow drives. Do NOT use for runtime queries. |
| `graphql-request` | v7.4.0, published 2025-12-12. | **USE for free-tier (100k/mo) direct queries** where no x402 payment fires. Cleaner injection than the client-cli wrapper. |

The hybrid lets us: (a) run the entire Iteration 1 inside the free tier using `graphql-request`, (b) when we need to *demonstrate* x402-paid flow, route the same query through `@graphprotocol/client-x402`, and (c) keep codegen unified across both via the cli's build pipeline.

---

## Critical Pitfalls in the Stack — Read Before Coding

### 1. `@graphprotocol/client-x402` settles in USDC on **Base**, not Celo

Confirmed via the package README on GitHub HEAD (graphprotocol/graph-client, packages/x402): production payments go to Base; testnet payments go to Base Sepolia. The project's stated substrate is x402-on-Celo, but the *paid Graph endpoint* lives on Base.

**Implications:**
- The TS client needs a viem `WalletClient` configured for **Base** (chain 8453) holding USDC, to *pay* for Graph queries.
- The *data* fetched is Celo (chain 42220). This is two chains, one client — viem handles cleanly.
- The Iteration 1 narrative "x402-on-Celo + Mento" in `CLAUDE.md` is aspirational for the *settlement substrate* of the protocols being modeled. The *measurement-instrument* substrate (paid Graph) is Base.

**Action:** roadmap should flag this. Iteration 1 baseline = stay strictly inside the 100k/mo free tier, never pay. Demo x402-paid flow only as a verification spike, not the primary path.

**Confidence:** HIGH (verified on the package's own README via raw GitHub HEAD).

### 2. `@graphprotocol/client-cli` is 21 months stale

Last release 2024-08-22. Has no x402 hook. We use it only as the schema-build / typed-SDK code generator that `@graphprotocol/client-x402` plugs into — never for runtime.

### 3. `tick` build can be slow from source — pin to wheels

tick 0.8.0.2 ships cp311–cp314 wheels for linux+macOS. We pin Python 3.12 explicitly to land on a wheel. If a teammate hits a from-source build, they need CMake 3.24+ and a C++17 compiler. Document this in the repo README.

### 4. CELO token duality

CELO is both the gas asset and an ERC-20 at `0x471EcE3750Da237f93B8E339c536989b8978a438`. Transfers appear in *both* the ERC-20 Transfer log stream **and** as native value in transaction-level data. Naive aggregation double-counts. The Python panel-build must deduplicate at `(tx_hash, log_index)` keyed against the canonical ERC-20 log; native transfers without a Transfer event kept only if hitting a tracked Mento contract.

### 5. Fee-abstraction adapters create phantom transfers

Per the downstream-consumer brief:
- USDC adapter: `0x2F25deB3848C207fc8E0c34035B3Ba7fC157602B`
- USDT adapter: `0x0e2a3e05bc9a16f5292a6170456a710cb89c6f72`

These contracts let users pay Celo gas in USDC/USDT instead of CELO. **Transactions paying gas through these adapters emit an extra ERC-20 transfer that is NOT a user-meaningful cashflow** — it is a gas-payment artifact. The panel-build must filter these out by matching `(to == adapter, sender == tx.origin, value < gas-fee-cap)`. Failure inflates per-user transfer counts and corrupts the Hawkes self-excitation estimate downstream. **This is the single biggest source of false self-excitation if missed.**

### 6. Subgraph staleness on Celo

`PROJECT.md` notes Celo subgraphs lag other chains. Every query must include `_meta { block { number timestamp } }`, and the panel-build must reject snapshots where `block.number` lags `forno.celo.org` head by more than a threshold (suggest: 2000 blocks ≈ 100 minutes at 3-second block time). Implement as a `validateMeta()` helper in the TS client.

### 7. Myriad multi-chain deployment — Celo volume not guaranteed

Verified via search 2026-05-25: Myriad is deployed on Abstract, Linea, and Celo, with markets migrated to BNB Chain for season 3 (smart contracts v3.2–v3.4). **The Active requirement in PROJECT.md "Identify Myriad's on-chain settlement contracts on Celo (addresses + verified ABI)" may resolve to "Celo deployment exists but has near-zero volume."** Phase-0 verification required: pull `Market created` and `Position settled` events from the Celo deployment over a recent 30-day window. If volume is negligible, the falsification gate fires (per PROJECT.md) and Iteration 2 (Halo) becomes the primary candidate.

### 8. `@mento-protocol/mento-core-ts` is an RC

Latest tag `2.6.5-rc3` (2025-09-11). RC tags can churn. **Use only for raw ABI imports** (via `import { brokerAbi } from '@mento-protocol/mento-core-ts'`). Do not depend on RC business-logic helpers — use `@mento-protocol/mento-sdk@3.2.8` (stable) for all logic.

### 9. Pandas 3.0 + numpy 2.x ABI compatibility

Pandas 3.0 dropped numpy 1.x compatibility entirely. statsmodels 0.14.6 is the first release that fully supports both. **Do NOT** mix any package compiled against numpy 1.x — that would mean ABI-breaking import errors at runtime. uv's resolver will catch this if we let it run unconstrained, so do not pin numpy lower.

### 10. x402 facilitator chain support is asymmetric

The Coinbase-hosted x402 facilitator settles USDC on Base. There is currently no Celo facilitator listed in the x402-foundation monorepo. **This means our "x402-on-Celo" framing is forward-looking** — the verifier infra doesn't exist on Celo yet. Treat this as a research finding to surface in the roadmap, not a blocker for Iteration 1 (which is empirical, not on-chain payment).

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `viem` 2.51 | `ethers` v6 | Only if integrating an existing ethers-only codebase. Every adjacent dep here is viem-first; mixing forces duplicate signer plumbing. |
| `@x402/fetch` 2.13 | `x402-fetch` 1.2.0 (unscoped) | Both are current. We pick the scoped one because `@graphprotocol/client-x402` already pins it. |
| `@x402/fetch` | `@x402/axios` 2.13 | If you need streaming uploads or richer interceptor chain; we don't, fetch covers it. |
| `@graphprotocol/client-x402` + cli (build only) | Pure `graphql-request` everywhere | If we decide to never demo a paid query; then the cli + client-x402 packages add no value. Hybrid is safer. |
| `graphql-request` | `urql` / Apollo Client | Only with reactive UI caching needs — we don't have those |
| `tick` | `pyhawkes` (ragoragino) | If you need a kernel `tick` doesn't ship (e.g., custom heavy-tailed power-law). For Daw–Pender / Kirchner exponential kernels, tick is direct. |
| `tick` | R `hawkes` via `rpy2` | If a peer reviewer demands R reproduction; otherwise no. |
| Custom Carr-Madan in numpy | `QuantLib::VanillaOption` chain | Only as a Garman-Kohlhagen sanity check. The strip itself is ~50 lines of numpy. |
| `polars` for panel | `pandas` | If event count stays < 100k rows, pandas is fine. Above that, polars wins meaningfully. |
| `marimo` | classic `jupyter` | When the audience needs `.ipynb` artifacts; marimo exports both ways but jupyter-first audiences read .ipynb natively |
| `uv` | `poetry` / `pip-tools` | If team policy mandates `poetry`; uv supports the same lock semantics and is faster |
| Forno (`forno.celo.org`) RPC | dRPC / Ankr Celo free tier | If forno rate-limits us (it does — undocumented). Backup, not primary. |
| `@mento-protocol/mento-sdk` 3.2.8 | Hand-rolled viem contract reads via Mento ABIs | If we discover an SDK bug. Lower priority since 3.2.8 is fresh (2026-04-29). |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `ethers` v5 | EoL, no Celo L2 nuances, viem 2.x is the 2026 default | `viem@^2.51` |
| `ethers` v6 (mixing) | Mixing viem + ethers in the same codebase forces duplicate signer wiring; every other dep is viem-first | `viem@^2.51` everywhere |
| `@graphprotocol/client-cli` 3.0.7 for *runtime* queries | 21 months stale, no x402 hook, heavy multi-source machinery | `@graphprotocol/client-x402` for paid, `graphql-request` for free-tier |
| `Dune SDK` / `@duneanalytics/client-sdk` | Project thesis is to *prove the case against* Dune Plus. Using its SDK contradicts the falsification design. | Free-tier Graph + Blockscout REST + `forno.celo.org` |
| `hawkeslib` (canerturkmen) | Author's README redirects to tick; univariate only; will not handle bivariate (bet × settlement) Hawkes | `tick` |
| `pyhawkes` / `py-hawkes` | Helpers, not estimators; we would write the MLE wrapper ourselves | `tick` |
| `Apollo Client` | Designed for reactive UI caches; massive overkill for a batch pipeline | `graphql-request` |
| `web3.py` (Python) | We do NOT do chain reads from Python — TS owns the data layer, Python owns the estimation layer | `viem` (TS) for chain reads; pass parquet snapshots to Python |
| `pip install` against system Python | Per `feedback_python_venv.md` — always venv | `uv venv` |
| `npm` / `yarn classic` | No workspace, slow | `pnpm@11` |
| Paid Graph plan / Dune Plus / paid oracle subscriptions | Free-tier-only is a hard constraint of the project's thesis | Free Graph (100k/mo), Blockscout, forno; x402 micro-payments only if/when we exhaust free tier |
| `web3.storage` / Filecoin for snapshots | Adds infra to a batch-research project | Local `data/*.parquet`; not in scope |
| `@mento-protocol/mento-sdk` < 3.x | 1.x line is ethers-based; not viem-native | `@mento-protocol/mento-sdk@^3.2.8` |
| `@graphql-codegen/cli` v5 | Superseded by v7 | `@graphql-codegen/cli@^7` |

---

## Stack Patterns by Variant

**Baseline (Iteration 1 primary path): stay strictly inside 100k/mo free tier**
- TS client uses `graphql-request@7.4` against The Graph Decentralized Network gateway without payment
- All "x402 cost" numbers come from the Agora `Cost(Q) = Σ Cost(q)` decomposition (per `SOMNIA_DRAFT.md`) applied to the *query plan*, not from settled payments
- `@graphprotocol/client-x402` and `@x402/fetch` are installed but never trigger
- Cache every response to `data/raw/<subgraph>/<query-hash>.json` to avoid re-fetching across re-runs
- This is the empirical case the project is built to demonstrate

**If we cross the free tier (Iteration 2+ or for a paid-flow demo)**
- TS client switches to `@graphprotocol/client-x402` for the over-budget queries
- viem `WalletClient` configured for **Base** (chain 8453), funded with a few USDC on Base for x402 settlement
- Pre-flight a `_meta` query (cheap) before any expensive paginated pull
- Persist payment receipts to `data/receipts/*.json` for audit

**If subgraph staleness blocks the panel build**
- Fall back to direct RPC + log-range pulls via viem `getLogs` over `forno.celo.org` + Blockscout `?module=logs&action=getLogs`
- Stitch into the same polars panel — same schema, different source
- Document the fallback in `notes/data-sources.md`

**If Myriad's Celo deployment has insufficient volume**
- Per `PROJECT.md` falsification gate, document the null result
- Iteration 2 (Halo) becomes Iteration 1's substitute test case
- Stack does not change; only contract addresses + subgraph IDs swap

---

## Version Compatibility — Known Constraints

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `viem@2.51.x` | `@x402/evm@2.13`, `@x402/fetch@2.13`, `@mento-protocol/mento-sdk@3.2.8` | All declare viem as peer/dep at `^2.x`; lockstep keeps them aligned |
| `@graphprotocol/client-x402@1.0.0` | `@x402/fetch@^2.8`, `@x402/evm@^2.8`, `graphql ^15.2 \|\| ^16` | Verified in package.json on npm |
| `@graphql-codegen/cli@7` | `@graphql-codegen/typescript-graphql-request@7.0.1` | Matching pair |
| `@graphql-codegen/typescript@6.0.1` | TypeScript 5.5+ | Works with TS 6 |
| `tick@0.8.0.2` | Python 3.11 / 3.12 / 3.13 / 3.14 (cp311–cp314 wheels) | DO NOT use Python 3.10 or earlier |
| `pandas@3.0` | `numpy@2.x`, `statsmodels@0.14.6+` | pandas 3.0 dropped numpy 1.x; statsmodels 0.14.6 is first fully numpy-2-compatible release |
| `polars@1.41` | `pyarrow@>=15` | Latest pyarrow is 24.0 — fine |
| `pnpm@11` | Node 20 LTS / Node 22 LTS | Node 18 EoL |
| `tsx@4.22` | TS 5.5+, ESM | Works with TS 6 |
| Celo chain ids | viem `chains.celo` = 42220, `chains.celoAlfajores` = 44787 | First-class in viem 2.x |
| Base chain ids | viem `chains.base` = 8453, `chains.baseSepolia` = 84532 | First-class in viem 2.x |
| `@mento-protocol/mento-sdk@3.2.8` | viem `^2.21.44` | Matches our viem 2.51 |

---

## Free-Tier Verification Audit

| Dependency | Cost | Verified path | Risk |
|---|---|---|---|
| The Graph queries (Decentralized Network) | 100k/mo free | thegraph.com docs + Celo docs confirm free tier on Decentralized Network | Exhaustion possible mid-month; mitigation: cache to parquet, `_meta` pre-flight |
| Celo RPC (`forno.celo.org`) | Free, no key | Hardcoded in viem's `chains.celo`; listed at docs.celo.org / chainlist.org | Undocumented rate limits; backup: dRPC / Ankr free tiers |
| Blockscout REST (`https://celo.blockscout.com/api`) | Free, no key needed | Public endpoint | Soft rate limits; cache aggressively |
| Base RPC (only if we demo x402-paid flow) | Free public RPC available | viem `chains.base` defaults; Alchemy/Ankr free tiers available | Only triggered if we exit free tier |
| All NPM packages above | Free (MIT / Apache-2.0) | Per package npm pages | None |
| All Python packages above | Free (BSD / MIT / Apache-2.0) | Per package PyPI pages | None |
| `tick` C++ build (if no wheel) | Free, requires CMake + clang/gcc | Wheel exists for cp312 — no build needed | None on linux/macOS |
| `@graphprotocol/client-x402` paid queries | Only fires if we actually call it; per-query USDC on Base | Free at install — payment only on use | Only triggered if we cross 100k/mo free tier |
| Coinbase x402 facilitator | Free to query (hosted); fees only when settling actual payment | docs.cdp.coinbase.com/x402 | Only triggered if we cross free tier |
| Marimo / Jupyter / plotly / matplotlib | Free | Open source | None |

**Result:** every dependency has a verified free path. No hidden paid tier. The single trigger for any spend is exceeding 100k Graph queries/month, which Iteration 1 is explicitly designed to avoid by cache discipline.

---

## Sources

### High confidence — verified live 2026-05-25

- npm registry JSON API (verified versions):
  - `viem@2.51.0` (released 2026-05-25)
  - `@x402/fetch@2.13.0` (released 2026-05-22)
  - `@x402/evm@2.13.0` (released 2026-05-22)
  - `@x402/core@2.13.0` (released 2026-05-22)
  - `x402@1.2.0`, `x402-fetch@1.2.0`, `x402-axios@1.2.0` (unscoped family, released 2026-04-16)
  - `@graphprotocol/client-x402@1.0.0` (released 2026-04-14; deps `@x402/fetch ^2.8.0`, `@x402/evm ^2.8.0`, peer `graphql ^15.2 || ^16`)
  - `@graphprotocol/client-cli@3.0.7` (stale, released 2024-08-22)
  - `@graphql-codegen/cli@7.0.0`, `typescript@6.0.1`, `typescript-graphql-request@7.0.1`
  - `@mento-protocol/mento-sdk@3.2.8` (released 2026-04-29, deps `viem`)
  - `@mento-protocol/mento-core-ts@2.6.5-rc3` (released 2025-09-11)
  - `graphql-request@7.4.0` (released 2025-12-12)
  - `zod@4.4.3`, `vitest@4.1.7`, `tsx@4.22.3`, `typescript@6.0.3`, `pnpm@11.3.0`, `@biomejs/biome@2.4.15`
- PyPI JSON API (verified versions):
  - `tick==0.8.0.2` (released 2026-05-04, cp311–cp314 wheels)
  - `statsmodels==0.14.6`, `numpy==2.4.6`, `pandas==3.0.3`, `polars==1.41.0`, `scipy==1.17.1`, `QuantLib==1.42.1`
  - `uv==0.11.16`, `marimo==0.23.8`, `ruff==0.15.14`, `pytest==9.0.3`, `pyarrow==24.0.0`
- viem chain definition source (raw GitHub HEAD): <https://raw.githubusercontent.com/wevm/viem/main/src/chains/definitions/celo.ts> — confirms `id: 42220`, `rpcUrls.default.http: ['https://forno.celo.org']`, multicall3 deployed
- Mento SDK README (raw GitHub HEAD): <https://raw.githubusercontent.com/mento-protocol/mento-sdk/main/README.md> — confirms `Mento.create(ChainId.CELO)` API, viem-native, service namespaces (`tokens`, `pools`, `quotes`, `swap`, `trading`, etc.)
- `@graphprotocol/client-x402` README (raw GitHub HEAD, packages/x402): confirms Base / Base Sepolia settlement, "no API key required", CLI + programmatic SDK + typed-SDK build workflow
- x402 monorepo README (raw GitHub HEAD): confirms `@x402/evm @x402/svm @x402/stellar` chain implementations; Celo not explicitly named on the README index

### Medium confidence — single source or paper-derived

- Kirchner 2015 INAR(p) estimator: <https://arxiv.org/abs/1509.02017> — implementation effort estimated at ~80 lines on statsmodels.VAR
- Daw & Pender 2017 Hawkes moments: <https://arxiv.org/pdf/1707.05143v3>
- Chen et al. 2017 LR test (Hawkes vs Poisson): <https://arxiv.org/pdf/1702.06055v2>
- Carr–Madan strip / Ma et al. 2014: <https://arxiv.org/pdf/1406.5430v1>
- Myriad multi-chain deployment (Abstract / Linea / Celo, then BNB migration): secondary sources (mexc, indexbox 2025) — phase-0 task to verify Celo volume

### Low confidence — verify before committing to architecture

- Exact Mento broker contracts holding cCOP / cKES / cNGN / cGHS volume — confirm in Phase-0 via `mento.pools.getAllPools()` once SDK is installed
- Whether Myriad has currently active Celo markets post v3.4 + CLOB + BNB migration — confirm in Phase-0 by direct contract reads / event queries
- Whether x402 facilitator infrastructure on Celo (rather than Base) ships before Iteration 2 — track x402-foundation roadmap

---

## Confidence Assessment — Per Choice

| Layer | Confidence | Reason |
|---|---|---|
| `viem@2.51` | HIGH | Live npm today; peer of everything; Celo chain hardcoded with forno RPC |
| `@x402/fetch@2.13`, `@x402/evm@2.13`, `@x402/core@2.13` | HIGH | Live npm 3 days ago; scoped `x402-foundation` org; transitively required by `@graphprotocol/client-x402` |
| `@graphprotocol/client-x402@1.0.0` | HIGH | Live npm 2026-04-14; package README confirms behavior; matches PROJECT.md `Constraints` exactly |
| `@graphprotocol/client-cli@3.0.7` (build-only role) | HIGH | Live npm; confirmed stale (21 months); confined to codegen role |
| `graphql-request@7.4` + codegen v7 stack | HIGH | All live; standard 2026 toolchain |
| `@mento-protocol/mento-sdk@3.2.8` | HIGH | Live npm 2026-04-29; README confirms viem-native, `Mento.create(ChainId.CELO)` API |
| `@mento-protocol/mento-core-ts@2.6.5-rc3` | MEDIUM | RC tag; use for ABIs only |
| `tick@0.8.0.2` | HIGH | PyPI 2026-05-04; multi-Python wheels |
| Kirchner INAR(p) on `statsmodels.VAR` | MEDIUM | Implementation effort ~half-day; paper explicit but no off-the-shelf package |
| Carr-Madan in numpy + QuantLib sanity | HIGH | Strip is shallow code; QuantLib well-documented |
| `@graphprotocol/client-x402` settles on Base (not Celo) | HIGH | Verified on package README via raw GitHub HEAD |
| Myriad has live Celo settlement contracts with non-trivial volume | LOW-MEDIUM | Confirmed multi-chain deploy; BNB migration may have moved most volume; Phase-0 verification required |
| Free-tier sufficiency for full Iteration 1 panel | MEDIUM | 100k/mo is generous; cache discipline required; will hold unless we discover a high-frequency Hawkes regime requiring sub-hour binning across a year |
| x402 facilitator on Celo (vs Base) | LOW | Not present in x402-foundation monorepo today; treat as forward-looking |

---

*Stack research for: empirical FX-cashflow modeling pipeline (abrigo-x402, Iteration 1 = Myriad on Celo)*
*Researched: 2026-05-25*
*Every npm/PyPI version above was retrieved live from `registry.npmjs.org` / `pypi.org` on 2026-05-25 — no training-data versions accepted.*
