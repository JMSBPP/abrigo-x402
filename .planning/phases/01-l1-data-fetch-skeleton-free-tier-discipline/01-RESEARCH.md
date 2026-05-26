# Phase 1: L1 Data-Fetch Skeleton + Free-Tier Discipline — Research

**Researched:** 2026-05-25
**Domain:** TypeScript paid-data-fetch substrate; Blockscout v2 REST + etherscan-compat v1 + Uniswap V3 Celo subgraph hybrid; content-addressed Parquet cache; x402-on-Base-Sepolia mock round-trip
**Confidence:** HIGH on Blockscout endpoint shape (live API probes), HIGH on x402 wire-format and viem/Base Sepolia config, HIGH on Forno head readout. **MEDIUM-LOW on Uniswap V3 Celo subgraph quality at acceptable indexer count** (two candidates found via Graph Explorer search but neither's curation signal is fresh + neither is queryable without a paid API key — hybrid plan's downgrade path is live-fire-relevant).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### V3 Swap data path (FETCH-01 + SC-3)
- **Hybrid panel construction**: Blockscout v2 REST is the **primary source-of-truth** for bulk Uniswap V3 Swap event panel on the cKES/USDT anchor pool; Uniswap V3 Celo subgraph is the **high-quality slice** used ONLY for in-range LP-fee accrual entities (saves re-implementing Q96 tick math from raw events) and ICHI vault state entities.
- **Blockscout for bulk swaps:** uses `celo.blockscout.com/api/v2/addresses/<pool>/logs?topic0=<Swap_hash>` with `fromBlock`/`toBlock` filters; keyset pagination via `next_page_params`; max 1,000 logs/page; ABI decode via viem `decodeEventLog`. At ~4,400 swaps/30d for cKES/USDT, the panel pulls in ~5 paginated requests (~2 seconds at the free 3 req/sec rate limit). No API key required for Iter-1 panel volume.
- **Subgraph for the LP-fee + vault-state slice:** typed SDK fetches `position`, `pool.feeGrowthGlobal0X128/1X128`, ICHI vault state per fetch — estimated ~200 paid queries per monthly refresh, negligible against 90k Graph cap. Steer's analogous slice would fire in Phase 6 if Phase 6 ran a Phase 1–5 cycle (it doesn't — Steer is STRADDLE memo-only null per Phase 0).
- **Both freshness wrappers ship** (REPRO-02-compatible pattern): `blockscoutFreshness({ block_consensus, lag_vs_forno })` (wired to production fetches) + `subgraphFreshness({ _meta.block.number, lag_vs_forno, 100_block_threshold })` (wired to LP-fee slice). Both unit-tested per SC-3.
- **Fallback if no Uniswap V3 Celo Decentralized Network deployment is found at acceptable quality:** the hybrid plan downgrades to **Blockscout-only**, and the LP-fee leg is computed from raw `Swap` events via Q96 tick math in `analysis/`. This downgrade is pre-registered, not Phase-2 ad-hoc.

#### x402 product-test scope
- **Self-hosted minimal Node 402-server at `fetch/x402-mock/`** — tiny HTTP server (~50 lines) that returns 402 with valid x402 v2 pricing headers and accepts a USDC tx hash on retry. Runs locally during tests + CI. Fully reproducible, no third-party dependency.
- **Wallet substrate: Base Sepolia testnet only** (chain id 84532, RPC `https://sepolia.base.org`). Test ETH via Coinbase CDP / Alchemy / QuickNode / Chainlink / Bware Labs faucets; test USDC at `0x036cbd53842c5426634e7929541ec2318f3dcf7e` via Circle Faucet (20 USDC per 2hr per address) or Coinbase CDP combined faucet.
- **Round-trip validation**: `@x402/fetch` v2.13 + `@x402/evm` v2.13 wired against the mock 402 endpoint; verifies wallet → sign EIP-712 → 402 retry → USDC transfer on Base Sepolia → tx-hash echo on `PAYMENT-RESPONSE` header.
- **Real Graph mainnet x402**: explicitly **out of scope for Phase 1**. The Graph operates NO Base Sepolia gateway — testnet x402 testing is limited to mock endpoints or non-Graph providers. Phase 5 PDF deliverable MAY include a one-shot real Graph mainnet paid query as a final product-validation footnote (deferred decision).
- **Cost-ledger entries for x402-mock**: `paid_real_usdc = false; chain = "base-sepolia"; usdc_amount = <quoted>; tx_hash = "0x..."; gateway_uri = "http://localhost:<port>/mock"`. Distinguishes from `paid_real_usdc = true` for any future real-mainnet shot.

#### Workspace layout (FETCH-01 + SC-1)
- **pnpm workspace** rooted at repo root with `pnpm-workspace.yaml` listing `fetch/` (and a placeholder for `analysis/` which Phase 2 will populate with `pyproject.toml` + `uv.lock`). `contracts/` deferred to Iteration 3+.
- **Root `package.json`** carries the workspace declaration + dev-tools (biome, vitest, tsx, @types/node). The existing root `package.json` (which has the two Graph deps installed by hand-prototyping) gets re-scoped: Graph deps move into `fetch/package.json`; root keeps only workspace meta + shared dev-tools.
- **Directory names: `fetch/` + `analysis/`** (matches ROADMAP.md SC paths verbatim, supersedes STACK.md's `client/` + `pipeline/` naming).
- **Pinned versions per FETCH-01 / STACK.md** in `fetch/package.json`: `viem@2.51.0`, `@x402/fetch@2.13.0`, `@x402/evm@2.13.0`, `@x402/core@2.13.0`, `@graphprotocol/client-x402@1.0.0`, `@graphprotocol/client-cli@3.0.7` (build-only), `graphql-request@7.4.0`, `@mento-protocol/mento-sdk@3.2.8`, `zod@4.4.3`, `dotenv@16.x`, `viem/chains` provides `celo` + `baseSepolia`.
- **`analysis/uv.lock` pinned at Phase 1 (NOT deferred to Phase 5)** per ROADMAP Phase 1 SC-1: `tick==0.8.0.2`, `statsmodels==0.14.6`, `polars==1.41.0`, `numpy==2.4.6`, `scipy==1.17.1`. Phase 2's `pyproject.toml` is created here too (empty src layout, dependencies pinned), even though no Python code lands until Phase 2.

#### Cache key idempotency (FETCH-04)
- **Cache key: `(chainId, contractAddress, blockRange)`** — `fetchTimestamp` is **NOT** part of the key. Re-running the same fetch is a cache hit with zero new cost-ledger rows. Byte-identical Parquet output verified via `sha256sum` per SC-4.
- **`fetchTimestamp` logged as metadata** in `data/raw/<protocol>/manifest.json` alongside `cache_key_hash`, `dataHash` (sha256 of the Parquet content), `gitCommit`, `endpoint`, `query_count`, `usdc_cost`, `paid_real`.
- **Honors FETCH-04's paid-step-is-idempotent invariant**: re-running with identical `(chainId, contractAddress, blockRange)` must produce byte-identical Parquet and zero new ledger rows.

#### Cost-ledger schema (FETCH-02)
- **Per-endpoint columns** for downstream demand-window analytics: `{timestamp, endpoint, query_id, cost_usdc, paid_real, tx_hash?, chain?, response_bytes, response_sha256, fetch_id}`.
- **`endpoint` enum**: `["graph-mainnet", "graph-sepolia", "blockscout", "forno", "x402-mock-sepolia"]`. The 90k/mo soft cap counts only `endpoint == "graph-mainnet"` rows. Blockscout / Forno / x402-mock-sepolia rows are logged but uncapped.
- **`--force` override** bypasses the 90k abort.
- **Storage**: `data/raw/manifest.json` (per-fetch manifest) + `data/raw/_cost_ledger.parquet` (append-only ledger). Both content-addressed.

#### Subgraph hunt + downgrade path
- Phase 1 researcher (this document) MUST hunt the Decentralized Network for a maintained Uniswap V3 Celo subgraph: verify deployment ID, indexer count ≥ 1 (preferably ≥ 3), typical `_meta.block.number` lag < 100 blocks vs Forno head, and schema coverage for cKES/USDT Swaps + Mints/Burns + `pool.feeGrowthGlobal0X128/1X128`.
- If no acceptable deployment exists: hybrid plan downgrades to **Blockscout-only**; LP-fee leg computed from raw events via Q96 tick math in `analysis/` from Phase 2 onwards. Downgrade pre-registered, not Phase-2 ad-hoc.

#### Subgraph-query side
- **Mento broker rates**: queried via `@mento-protocol/mento-sdk` at event-block (Phase 2 panel snap); no Graph paid budget needed.
- **ICHI vault state**: typed entities pulled from the same Uniswap V3 Celo subgraph slice OR ICHI's own subgraph if one exists (researcher to verify both). Tracked in `protocols/ichi.toml [subgraphs]` block.

### Claude's Discretion
- HTTP retry policy: exponential backoff, max 3 retries on transient failures; 402 retried per @x402/fetch defaults.
- viem chain config for `celo` (id 42220, RPC `https://forno.celo.org`) and `baseSepolia` (id 84532, RPC `https://sepolia.base.org`).
- vitest setup: standard ESM, `vitest run` for CI, no watch mode in CI; coverage via `@vitest/coverage-v8` if requested.
- biome config: STACK.md defaults; rules tuned only if false positives surface in fetch/.
- `.env` policy: `.env.example` committed (no secrets); `.env` in `.gitignore`; `PRIVATE_KEY` for Base Sepolia faucet wallet documented as test-only in `.env.example`.
- Forno keeper-polling explicitly out of cost-ledger; free at any volume; not counted.
- Cold-backfill budget allocation: proposed at /gsd:plan-phase 1 time based on Phase 1 researcher's subgraph audit. Default envelope: 30k cold-backfill + 15k incremental + 45k reserve. Re-allocated if researcher finds subgraph slice costs more than predicted.

### Deferred Ideas (OUT OF SCOPE)
- **Real Graph mainnet x402 paid query** — deferred to Phase 5 PDF deliverable as a product-validation footnote.
- **Steer subgraph slice** — Steer Iter-2 is STRADDLE memo-only null per Phase 0; analogous Steer LP-fee subgraph slice never runs in v1.
- **Q96 tick-math implementation in analysis/** — fires only as the fallback path if the Uniswap V3 Celo subgraph deployment hunt fails. Not implemented unless the binding constraint triggers.
- **Mainnet x402 test on Base** — covered above as Phase 5 footnote candidate.
- **Blockscout Pro/paid tier** — not needed for Iter-1 panel volume.
- **TS contracts/ workspace** — Iteration 3+.
- **`contracts/` directory entry in pnpm-workspace.yaml** — Iteration 3+.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| **FETCH-01** | TS `fetch/` workspace bootstraps with viem 2.51 + `@x402/fetch 2.13` + `@graphprotocol/client-x402 1.0.0` + `graphql-request 7.4` + `@mento-protocol/mento-sdk 3.2.8` + Blockscout v2 REST client | §E (x402 client config), §C (Blockscout schema), §L (protocol-agnostic harness), Standard Stack table — all dependencies are pinned and verified live on npm 2026-05-25 |
| **FETCH-02** | `cost-ledger.ts` records every paid request with USDC cost in Parquet and aborts cumulative monthly Graph spend at 90k queries; `--force` flag bypasses | §J (Parquet schema with `parquet-wasm`/`hyparquet` recommendation), §K (90k budget gate algorithm), §M (dry-run estimator) |
| **FETCH-03** | Subgraph-freshness wrapper includes `_meta { block { number hash } }` in every Graph query and aborts if lag vs Forno `eth_blockNumber` > 100 blocks; failure propagates explicitly | §G (subgraph wrapper sig + algorithm), §H (Blockscout-freshness wrapper companion; `block_consensus` field is **ABSENT** from Blockscout v2 — section documents the corrected freshness gate using `block_number` lag only) |
| **FETCH-04** | Cache layer content-addressed by `(chainId, contractAddress, blockRange, fetchTimestamp)`; paid-step-is-idempotent invariant holds (re-run with identical inputs = byte-identical output, no re-pay) | §I (cache key canonical serialization + storage layout + manifest schema + two-run byte-identity test) |
</phase_requirements>

## Summary

Phase 1 builds the TypeScript data-fetch substrate. Six concrete deliverables, every one with primary-source verification today:

1. **Blockscout v2 `/addresses/{addr}/logs` does NOT accept `topic0` query params** (HTTP 422 confirmed live). The correct topic-filtered swap-event pull path is the **etherscan-compat v1 endpoint** `/api?module=logs&action=getLogs&fromBlock=&toBlock=&address=&topic0=…` which returns up to 1,000 logs per call (verified live: 554 swaps returned in one call for the cKES/USDT anchor pool over 30 days). The v2 endpoint is useful only for the *decoded* view (it returns ABI-decoded swap arguments inline) at a default page size of 50, no topic filter — use v2 if you want server-side decoding for the few-events case, v1 if you want bulk pull with a topic mask.
2. **Blockscout v2 logs do NOT carry `block_consensus`** (verified live in returned JSON keys). The Phase-0 CONTEXT.md assumption that this field exists is INCORRECT. The Blockscout freshness wrapper must rely on `block_number lag vs Forno head` only.
3. **Uniswap V3 Celo subgraph hunt result: TWO candidates exist but BOTH require Graph gateway API keys to query** (live test returned `auth error: missing authorization header` even with the public gateway URL). The candidates: (a) Messari `9nh6Ums63wFcoZpmegyPcAFtY3CAzQc3S6cuERALYMqa` (108.4 signal, last updated ~3 years ago — likely stale), (b) Uniswap-tagged `t3uzAbri7sTjJHsrkfXWoMwdVMKD652iTPtfDz3iq1o` (3.0K signal, last updated ~2 years ago). **The downgrade path is now load-bearing**: with API-key requirements and stale curation signals, Phase 1 plans must default to Blockscout-only + Q96 tick math in `analysis/`, with the subgraph slice scheduled as Phase-2 retroactive enrichment only IF the API key is obtainable AND `_meta.block.number` clears the 100-block lag check.
4. **No ICHI vault subgraph exists** (GitHub `ichifarm` org searched — no subgraph repos found). ICHI vault state must be pulled from the Uniswap V3 Celo subgraph slice (same downgrade caveat as #3) OR via direct `eth_call` to the vault contract through Forno (free, uncapped, but adds an `eth_call` panel-fetch leg).
5. **`@x402/fetch` v2.13 minimal config is canonical**: `wrapFetchWithPayment(fetch, x402Client)` with `registerExactEvmScheme(client, { signer: privateKeyToAccount(PK) })`. Network spec is `"eip155:84532"` (Base Sepolia). The `X-PAYMENT-RESPONSE` header on success carries a base64-encoded JSON `{success, transaction, network, payer}` — i.e., the cost-ledger CAN capture the Base Sepolia settlement tx hash.
6. **Mock 402 server is ~50 lines on `node:http`** (no facilitator URL needed: the mock verifies the `X-PAYMENT` header structurally — base64-decode → JSON parse → check `paymentPayload.signature` is a valid hex string — and writes back an `X-PAYMENT-RESPONSE` header with a stub tx hash). Optional Phase-1.5 escalation: a real on-chain USDC `transferWithAuthorization` broadcast via viem (faucet-funded), which makes the cost-ledger entry carry a real Base Sepolia tx hash that can be verified on `sepolia.basescan.org`.

**Primary recommendation:** Bootstrap the TS workspace this week. Default to Blockscout-only on the V3 swap leg with the v1 etherscan-compat endpoint as the topic-filtered pull path. Treat the Uniswap V3 Celo subgraph as a *Phase-2 retroactive enrichment* — Phase 1 ships the freshness wrappers for BOTH paths (subgraph + Blockscout) but only the Blockscout path is exercised in production. The x402 mock + Base Sepolia round-trip is shipped as a separate workspace at `fetch/x402-mock/` with vitest test harness; it is fully decoupled from the panel-fetch leg.

## Standard Stack

### Core (verified live on npm registry + viem GitHub HEAD, 2026-05-25)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `viem` | 2.51.0 | EVM types, signing, multi-chain client (Celo + Base Sepolia) | Peer of `@x402/evm`, `@x402/fetch`, `@mento-protocol/mento-sdk`. First-class `chains.celo` (id 42220) + `chains.baseSepolia` (id 84532). Verified live npm 2026-05-25. |
| `@x402/fetch` | 2.13.0 | Wraps native `fetch` to intercept 402 → sign EIP-712 → retry with `X-PAYMENT` header | The scoped x402-foundation org canonical fetch wrapper. Released 2026-05-22 (3 days ago at time of Phase-0 stack research). Required for `@graphprotocol/client-x402`. |
| `@x402/evm` | 2.13.0 | EVM signer primitives (EIP-3009 `transferWithAuthorization`, EIP-712 typed signing) | Imported into the x402Client via `registerExactEvmScheme(client, { signer })`. |
| `@x402/core` | 2.13.0 | Transitive types (x402Client class, scheme registry) | Transitive via `@x402/fetch` and `@x402/evm`. Pin via pnpm. |
| `@graphprotocol/client-x402` | 1.0.0 | The Graph paid gateway client; auto-pays in USDC on Base mainnet | Settles on **Base mainnet ONLY** per package README — NO Base Sepolia gateway for The Graph. Installed for shape-completeness of FETCH-01; not actually triggered in Phase 1 (cost-leg modeled, not paid). |
| `@graphprotocol/client-cli` | 3.0.7 | **Build-only** codegen tool for typed Graph SDK | 21 months stale. Confined to dev-time codegen. NEVER imported at runtime. |
| `graphql-request` | 7.4.0 | Minimal GraphQL client for free-tier subgraph reads | The runtime path for Uniswap V3 Celo subgraph LP-fee slice IF the API key is obtained. |
| `@mento-protocol/mento-sdk` | 3.2.8 | Mento broker / pair / rate access | Used for FX-rate snap in Phase 2 (not Phase 1); but the dep is wired now to satisfy FETCH-01. |
| `zod` | 4.4.3 | Runtime validation of subgraph responses + cost-ledger row shape + protocol-spec TOML parse | Already transitive via x402 packages. |
| `dotenv` | 16.x | Load `.env` for `PRIVATE_KEY`, `BASE_SEPOLIA_RPC_URL`, `CELO_RPC_URL`, optional `BLOCKSCOUT_API_KEY` | Standard. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `vitest` | 4.1.7 | Test runner | Always. Phase 1 ships freshness-wrapper tests (§G, §H), cache-idempotency test (§I), x402 mock round-trip test (§F), protocol-agnosticism test (§L). |
| `@biomejs/biome` | 2.4.15 | Lint + format | Always. Single tool replaces eslint+prettier. |
| `tsx` | 4.22.3 | Run TS without build step | CLI entrypoint `fetch/src/cli.ts` is run via `tsx`. |
| `typescript` | 6.0.3 | Type system | Required peer of viem + x402. |
| `@types/node` | ^22.x | Node 22 LTS types | Phase 1 uses `node:http`, `node:crypto`, `node:fs/promises`. |
| `hyparquet` | ^1.x | Pure-TS Parquet read/write (no native deps) | Cost-ledger writes (cross-platform; no node-gyp / arrow-native build) — see §J. |
| `hyparquet-writer` | ^1.x | Parquet write companion | Same. |

**Alternatives Considered (Parquet TS lib):**

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `hyparquet` + `hyparquet-writer` (pure JS) | `@dsnp/parquetjs` | dsnp/parquetjs is heavier (compression deps); hyparquet is the lightest pure-JS option that still supports the polars-readable Parquet 2.x variant. |
| Either | Defer Parquet to Python in Phase 2 | TS writes ledger to JSONL → Python ingest in Phase 2 converts to Parquet. **Simpler.** Recommended fallback if hyparquet stability turns out shaky. |

### Alternatives Considered (Topic-filtered log pull on Blockscout)

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Blockscout v1 etherscan-compat `/api?module=logs&action=getLogs` (the **canonical** topic-filtered pull) | Blockscout v2 `/api/v2/addresses/{addr}/logs` + client-side topic filter | v2 returns 50 items/page by default and accepts no `topic0` param (verified live: HTTP 422 "Unexpected field: topic0"). Client-side filtering wastes 5–10× more requests at the free 3 req/sec rate limit. **v1 is the only correct path for bulk swap pull.** |
| Either Blockscout | Direct viem `getLogs` against `forno.celo.org` | Forno enforces undocumented rate limits and rejects large block ranges. Use as Phase-2+ fallback only. |

**Installation (pnpm workspace root):**

```bash
# Root devDependencies (workspace meta + shared tooling)
pnpm add -Dw typescript@^6 tsx@^4.22 vitest@^4.1 @biomejs/biome@^2.4 @types/node

# fetch/ workspace deps
pnpm --filter fetch add viem@2.51.0 \
  @x402/fetch@2.13.0 @x402/evm@2.13.0 @x402/core@2.13.0 \
  @graphprotocol/client-x402@1.0.0 \
  graphql graphql-request@7.4.0 \
  @mento-protocol/mento-sdk@3.2.8 \
  zod@^4.4.3 dotenv@^16 \
  hyparquet hyparquet-writer

pnpm --filter fetch add -D @graphprotocol/client-cli@3.0.7
```

**Version verification command** (every dep pin in `fetch/package.json` MUST be verified at Phase 1 start; training data is stale):

```bash
for pkg in viem @x402/fetch @x402/evm @x402/core @graphprotocol/client-x402 \
           @graphprotocol/client-cli graphql-request @mento-protocol/mento-sdk \
           zod hyparquet vitest @biomejs/biome tsx; do
  echo -n "$pkg : "; npm view "$pkg" version
done
```

If any pin in STACK.md drifts vs npm live, Phase 1 Plan 01 MUST surface the drift and either (a) update STACK.md via the schema-frozen procedure OR (b) pin to the live version and document the drift in `notes/STACK_VERSION_DRIFT_2026_06.md`. Schema-frozen check does NOT apply to STACK.md — that file is research-substrate, not protocol-spec.

## Architecture Patterns

### Recommended Project Structure (matches ARCHITECTURE.md Pattern 1 + 2 verbatim)

```
abrigo-x402/
├── package.json                       # workspace root (devDependencies only)
├── pnpm-workspace.yaml                # lists "fetch", "analysis"
├── .env.example                       # PRIVATE_KEY, CELO_RPC_URL, BASE_SEPOLIA_RPC_URL, BLOCKSCOUT_API_KEY (optional)
├── fetch/                             # L1 — TypeScript data-fetch substrate
│   ├── package.json                   # viem, @x402/*, graphql-request, @mento-protocol/*, zod, hyparquet
│   ├── tsconfig.json                  # strict; ESM; nodenext module resolution
│   ├── src/
│   │   ├── cli.ts                     # `pnpm fetch ichi [--dry-run] [--estimate-budget] [--force]` entrypoint
│   │   ├── protocol-spec.ts           # loads protocols/*.toml via zod schema mirror
│   │   ├── blockscout/
│   │   │   ├── v1-getlogs.ts          # etherscan-compat /api?module=logs (the topic-filtered path)
│   │   │   ├── v2-addresses-logs.ts   # /api/v2 endpoint (no topic filter; default 50/page; decoded)
│   │   │   └── freshness.ts           # blockscoutFreshness({ last_block, forno_head, threshold: 100 })
│   │   ├── subgraph/
│   │   │   ├── client.ts              # graphql-request with x402 wrapper hook (mock-only in Phase 1)
│   │   │   ├── queries.ts             # _meta { block { number hash } } injection middleware
│   │   │   └── freshness.ts           # subgraphFreshness({ _meta.block.number, forno_head, threshold: 100 })
│   │   ├── x402-mock/
│   │   │   ├── server.ts              # ~50-line node:http 402 mock (§F)
│   │   │   └── client-bridge.ts       # adapter: wires @x402/fetch to a localhost mock URL
│   │   ├── cache/
│   │   │   ├── key.ts                 # sha256(canonical(chainId, contractAddress, blockRange)) (§I)
│   │   │   ├── manifest.ts            # manifest.json read/write schema
│   │   │   └── parquet-writer.ts      # hyparquet-writer wrapping; cache-hit short-circuit
│   │   ├── cost-ledger.ts             # append-only Parquet writer; 90k budget gate (§J §K)
│   │   ├── viem-clients.ts            # cached PublicClient for celo + baseSepolia
│   │   └── decoders/
│   │       └── uniswap-v3-swap.ts     # viem decodeEventLog ABI fragment for Swap (§D)
│   └── tests/
│       ├── freshness.test.ts          # SC-3 (both wrappers)
│       ├── cache-idempotency.test.ts  # SC-4 (two-run sha256sum equality)
│       ├── x402-mock.test.ts          # SC-2 (mock round-trip on random port)
│       ├── cost-ledger.test.ts        # SC-2 (90k gate + --force)
│       ├── budget-dry-run.test.ts     # SC-6 (--dry-run --estimate-budget)
│       ├── protocol-agnostic.test.ts  # SC-5 (no `if config.name ==`, no magic fee-tier numbers)
│       └── fixtures/
│           ├── blockscout-v1-getlogs-cKES-USDT.json   # captured live during Phase 1
│           ├── blockscout-v2-addresses-logs-cKES.json
│           ├── subgraph-meta-lag-99.json              # synthetic
│           ├── subgraph-meta-lag-101.json             # synthetic
│           └── test_fixture.toml                      # synthetic protocol-agnosticism harness
├── analysis/                          # L3+ — Python (Phase 2 lands code; Phase 1 only pins env)
│   ├── pyproject.toml                 # empty src layout; deps pinned
│   ├── uv.lock                        # tick==0.8.0.2, statsmodels==0.14.6, polars==1.41.0, ...
│   └── src/abrigo_x402/__init__.py    # empty
├── data/                              # git-ignored EXCEPT data/raw/manifest.json + data/raw/_cost_ledger.parquet
│   └── raw/
│       ├── manifest.json              # per-fetch manifests, append-only JSON array
│       ├── _cost_ledger.parquet       # append-only Parquet (cost-ledger)
│       └── ichi/<cache_key_hash>.parquet
└── protocols/                         # L0 (frozen at Phase 0 commit e9b214d)
    ├── _schema.toml
    ├── ichi.toml                      # Phase 1 MAY add [subgraphs.uniswap_v3] block IF schema-frozen-check permits
    └── steer.toml                     # Phase 1 does NOT touch (Steer is HEDGE-05 memo-only null)
```

**Subgraph block addition note:** `protocols/_schema.toml` (commit `e9b214d`) does NOT currently document a `[subgraphs.*]` block. Adding one to `protocols/ichi.toml` would trigger schema-frozen-check rejection on `_schema.toml` IF the planner adds it to `_schema.toml` itself. The safer path: extend `protocols/ichi.toml` ONLY (since per-protocol TOMLs may legally hold fields not in `_schema.toml` — `_schema.toml` defines the *required* surface, not the *exhaustive* one). The planner MUST verify this read by running `make schema-frozen-check` against a draft commit and confirm no diff against `_schema.toml`. If schema-frozen-check rejects, a Phase-0-style schema increment is required: re-open the schema, add `[subgraphs.uniswap_v3]` enum, get 2-way review, and re-freeze with a new baseline commit hash.

### Pattern 1: Paid Step is Idempotent (ARCHITECTURE.md Pattern 2, verbatim)

`fetch/src/cli.ts` is the only command that mutates `_cost_ledger.parquet` and `manifest.json`. It consults the manifest BEFORE any network call: if `(chainId, contractAddress, blockRange)` is already in the manifest with a non-empty `dataHash`, the run short-circuits (cache hit, zero new ledger rows, byte-identical Parquet returned).

### Pattern 2: Two-Layer Freshness Gate

Every paid endpoint call passes through a freshness wrapper that compares the response's block-anchor against Forno head. If `lag > 100 blocks`, throw — never silently proceed (PITFALLS.md §2 silent-stale-data bias is the single biggest source of false self-excitation upstream).

```typescript
// fetch/src/blockscout/freshness.ts
export interface BlockscoutFreshnessInput {
  most_recent_log_block: number;
  forno_head: number;
}
export class BlockscoutFreshnessError extends Error {
  constructor(public details: { forno_head: number; most_recent_log_block: number; lag: number; threshold: number }) {
    super(`Blockscout response stale: lag=${details.lag} blocks > threshold=${details.threshold}`);
  }
}
export function blockscoutFreshness({ most_recent_log_block, forno_head }: BlockscoutFreshnessInput, threshold = 100) {
  const lag = forno_head - most_recent_log_block;
  if (lag > threshold) {
    throw new BlockscoutFreshnessError({ forno_head, most_recent_log_block, lag, threshold });
  }
  return { lag, fresh: true };
}
```

Note: `block_consensus` is NOT a field returned by Blockscout v2 logs (confirmed live: top-level log keys are `[address, block_hash, block_number, block_timestamp, data, decoded, index, smart_contract, topics, transaction_hash]` — no `block_consensus`). The wrapper canNOT check consensus per-log; it relies on `most_recent_log_block` lag vs Forno head only. CONTEXT.md's stated assumption that the wrapper checks `block_consensus = false` per-log is unfounded and must be dropped from the plan.

### Pattern 3: Protocol-Agnostic Library Surface

Every chain-specific or protocol-specific value is read from `protocols/*.toml` via zod schema. NO module under `fetch/src/` references the strings `"ichi"`, `"steer"`, hard-coded fee-tier integers `0.0001`, `100`, `500`, or any address outside the `protocols/` directory. The protocol-agnosticism test (§L) enforces this with a vitest grep over `fetch/src/`. The pre-commit AF leak-check hook (Phase 0) is the cheap complement.

### Anti-Patterns to Avoid

- **Per-protocol branching in `fetch/src/`** — defeats the swap surface; Iteration 2 (deferred to v2+) will require core edits. Behind `protocol_spec` dispatch only.
- **Inlining hex topic constants in business logic** — every hex string (Swap topic, USDC address, factory address) lives in a `decoders/*.ts` or `protocol-spec.ts` constant near where it's documented.
- **Network calls from inside vitest tests by default** — every test uses captured fixtures in `tests/fixtures/`. A *separate* `vitest run --include 'tests/integration/**'` (off in CI by default) does the live-network calls.
- **Refetching cached `(chainId, contractAddress, blockRange)` tuples** — burns Graph budget. The cache short-circuit MUST happen BEFORE the freshness wrapper is even instantiated.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Topic-filtered log pull on Celo | Custom paginator over `eth_getLogs` via Forno | Blockscout v1 etherscan-compat `/api?module=logs&action=getLogs&topic0=...` (verified live: 554 swaps in one response) | Forno rate-limits aggressively + 10k-block-window cap; Blockscout v1 returns up to 1,000 logs per call with no rate-limit hit at 3 req/sec free tier. |
| ABI event decoding | Custom keccak256 + ABI param decoder | `viem.decodeEventLog({ abi, topics, data })` | Strict mode + named args + first-class TS types via `as const` ABI. |
| EIP-712 payment signing | Hand-rolled EIP-712 signer | `@x402/evm` `registerExactEvmScheme` | Handles EIP-3009 `transferWithAuthorization` + EIP-712 typed signing + nonce/deadline encoding correctly. |
| 402 retry loop | Hand-rolled fetch wrapper | `wrapFetchWithPayment(fetch, x402Client)` from `@x402/fetch` | Auto-handles 402 → parse `accepts[]` → sign → retry → settle. Reads `X-PAYMENT-RESPONSE` for the tx hash + payer + network. |
| Parquet writes from TS | Hand-rolled Parquet encoder | `hyparquet-writer` (pure JS, polars-compatible) OR defer to Python with JSONL handoff | Parquet binary format is non-trivial; hyparquet-writer is the only stable pure-JS path. |
| sha256 content-addressing | `crypto.subtle.digest` polyfills | `node:crypto`'s `createHash('sha256')` | Native to Node 22 LTS; deterministic; no dep. |
| TOML parsing | Hand-rolled TOML parser | `@iarna/toml` (pinned to ^2.2) | Standard. Phase 0 already used this implicitly. |
| Faucet automation | Webdriver scraper | Manual one-time top-up via `faucet.circle.com` + `portal.cdp.coinbase.com` | Phase 1 needs ~20 USDC + ~0.05 testnet ETH ONCE; not worth automating. |

**Key insight:** every paid action on Phase 1 ships through a tested library. The custom code surface is the *adapter* (cli.ts, protocol-spec.ts, cache/), not the *primitive*. This is the difference between PITFALLS.md §8 reproducibility-breakage (which assumes hand-rolled adapters per iteration) and a clean swap-surface.

## Common Pitfalls

### Pitfall 1: Blockscout v2 schema assumptions WRONG (CONTEXT.md drift)

**What goes wrong:** CONTEXT.md states the bulk Swap panel uses `celo.blockscout.com/api/v2/addresses/<pool>/logs?topic0=<Swap_hash>` with "max 1,000 logs/page". Live testing today (2026-05-25, head block 67,854,122) shows:
- `topic0` query param is REJECTED with HTTP 422 ("Unexpected field: topic0")
- Default page size is **50, NOT 1,000**
- `block_consensus` field is **NOT** present in the response log shape

**Why it happens:** Blockscout's v2 API was designed for explorer-UI consumption (no bulk filter; default page-size matches what fits in a UI viewport). The high-throughput topic-filtered bulk-pull endpoint is the v1 etherscan-compat path, which IS supported on Blockscout v2 backends (verified: 554 logs returned in one call with topic0 + fromBlock + toBlock).

**How to avoid:** Plan to use `/api?module=logs&action=getLogs` for bulk pulls (§C below), reserve `/api/v2/addresses/{addr}/logs` for the cases where you want server-side ABI decoding without supplying the ABI. Drop the `block_consensus` per-log check from the freshness wrapper spec (§H).

**Warning signs:** A test fixture from `/api/v2/...?topic0=...` that has only 50 items and is missing `block_consensus`.

### Pitfall 2: Uniswap V3 Celo subgraph requires API key (CONTEXT.md downgrade is now load-bearing)

**What goes wrong:** Both candidate Uniswap V3 Celo subgraphs (Messari `9nh6Ums...ALYMqa`, Uniswap-tagged `t3uzAbri...iq1o`) are queryable only at `gateway.thegraph.com/api/<API_KEY>/subgraphs/id/<id>`. Test today returned `{"errors":[{"message":"auth error: missing authorization header"}]}` against `gateway.thegraph.com/api/subgraphs/id/<id>`. Without an API key, the subgraph slice cannot be exercised at all — not even for `_meta` checks.

**Why it happens:** The Graph Decentralized Network deprecated key-less queries in early 2024. All paid AND free-tier queries route through an API-key-authenticated gateway. The first 100k queries/mo per API key are free.

**How to avoid:** Phase 1 Plan must include a wave for **getting a Graph API key** (free signup on Subgraph Studio; takes ~5 minutes). Store in `.env` as `GRAPH_API_KEY`. The `subgraph/client.ts` reads it from env. If the key is not available, the subgraph leg fails-closed (throws `MissingGraphApiKeyError`) and the Blockscout-only downgrade path activates automatically — this is the pre-registered downgrade from CONTEXT.md.

**Warning signs:** A subgraph response with no body and a 401/403 status; an `auth error` JSON payload.

### Pitfall 3: x402 `wrapFetchWithPayment` and `wrapFetchWithPaymentFromConfig` are two DIFFERENT APIs in 2.13

**What goes wrong:** Phase 1 plan templates may use either name. The two are NOT interchangeable. `wrapFetchWithPaymentFromConfig` takes a static config object; `wrapFetchWithPayment` takes an `x402Client` instance.

**Why it happens:** The official examples in `x402-foundation/x402/examples/typescript/clients/fetch` use `wrapFetchWithPayment` + `x402Client`; the Coinbase quickstart docs use `wrapFetchWithPaymentFromConfig`. Both are valid in 2.13.

**How to avoid:** Use `wrapFetchWithPayment(fetch, x402Client)` consistently (the canonical pattern in §E below). It gives finer-grained control over the scheme registry.

### Pitfall 4: Cache key must NOT include `fetchTimestamp` (CONTEXT.md decision — DOUBLE-CHECK against ROADMAP)

**What goes wrong:** ROADMAP Phase 1 SC-4 originally said cache key is `(chainId, contractAddress, blockRange, fetchTimestamp)`. CONTEXT.md correctly identifies this as inconsistent with idempotency: `fetchTimestamp` makes every re-run a cache miss. CONTEXT.md decision (locked): cache key is `(chainId, contractAddress, blockRange)`; `fetchTimestamp` is metadata only.

**Why it happens:** Drafted SC-4 inverts the invariant SC-4 was supposed to encode. Don't follow ROADMAP verbatim here — follow CONTEXT.md.

**How to avoid:** §I below pins the canonical key. The plan author must explicitly note that `fetchTimestamp` is excluded from the hash input.

### Pitfall 5: Faucet rate limits will block the Base Sepolia round-trip if not planned

**What goes wrong:** Circle's USDC faucet gives 20 USDC per address per 2hr. A flaky test that drains the wallet to zero will block the next CI run for 2 hours.

**How to avoid:** The mock 402 server quotes payments at 0.001 USDC. A single 20-USDC faucet drop covers 20,000 test runs. Tests must NEVER drain to zero — bake in a "leave 0.5 USDC reserve" rule into the test cleanup, OR scope the mock to NOT settle on-chain by default (just header-validate; toggle the real-settlement path behind a `X402_MOCK_REAL_SETTLE=1` env var that defaults off in CI).

### Pitfall 6: Free-tier Forno polling without backoff trips the IP block

**What goes wrong:** PITFALLS.md §9 documents this — bursting `eth_getLogs` or rapid `eth_blockNumber` polling against Forno trips an IP rate-limit lock for an unknown window (~15 min observed).

**How to avoid:** Throttle Forno calls to ≤ 3 req/sec from `fetch/src/`. The freshness wrapper caches `forno_head` for 5 seconds across multiple subgraph/Blockscout response checks within the same fetch session. Phase 2 may need to retro-fit the throttle if Phase 1 doesn't expose it; bake it in now.

## Code Examples

### A) Uniswap V3 Celo subgraph deployment hunt (Q-1 — LOAD-BEARING)

**Conclusion: TWO candidates found via Graph Explorer; BOTH require API key + neither has fresh curation signal; the pre-registered Blockscout-only downgrade path is now the recommended Phase-1 default. Subgraph slice deferred to Phase-2 retroactive enrichment if and when a Graph API key is provisioned AND `_meta.block.number` clears the 100-block lag check.**

#### Candidates

| Subgraph | Deployment ID | Publisher | Signal | Last Updated | Status |
|---|---|---|---|---|---|
| Messari `uniswap-v3-celo` | `9nh6Ums63wFcoZpmegyPcAFtY3CAzQc3S6cuERALYMqa` | `0x7e8f317a45d67e27e095436d2e0d47171e7c769f` | 108.4 signal | ~3 years ago | DEPRECATED for Ethereum mainnet per Graph Explorer; Celo deployment is one of several network builds in the Messari unified schema. Network field = `celo`. |
| Uniswap-tagged "Uniswap V3 Celo" (v0.0.1) | `t3uzAbri7sTjJHsrkfXWoMwdVMKD652iTPtfDz3iq1o` | `0x634ac500f16800dddc3d506a9ebfa85b91041413` | 3.0K signal | ~2 years ago | Network field = `celo`. Higher curation signal than Messari but still 2-years-stale on schema. |

Sources:
- `https://thegraph.com/explorer/subgraphs/9nh6Ums63wFcoZpmegyPcAFtY3CAzQc3S6cuERALYMqa` (Messari)
- `https://thegraph.com/explorer/subgraphs/t3uzAbri7sTjJHsrkfXWoMwdVMKD652iTPtfDz3iq1o` (Uniswap-tagged)
- Messari subgraphs repo: `https://github.com/messari/subgraphs` (uniswap-v3 standardized schema)
- Uniswap official subgraph: `https://github.com/Uniswap/v3-subgraph` — does NOT publish a Celo deployment in the main branch as of HEAD; Celo deployment is a forked Messari build.

#### Live test results

```bash
# Forno head (verified 2026-05-25)
$ curl -X POST https://forno.celo.org -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
{"result":"0x40b5f2a"}  # decimal 67,854,122

# Both candidate subgraphs require API key (no anon path)
$ curl -X POST https://gateway.thegraph.com/api/subgraphs/id/9nh6Ums63wFcoZpmegyPcAFtY3CAzQc3S6cuERALYMqa \
    -d '{"query":"{ _meta { block { number } } }"}'
{"errors":[{"message":"auth error: missing authorization header"}]}

$ curl -X POST https://gateway.thegraph.com/api/subgraphs/id/t3uzAbri7sTjJHsrkfXWoMwdVMKD652iTPtfDz3iq1o \
    -d '{"query":"{ _meta { block { number } } }"}'
{"errors":[{"message":"auth error: missing authorization header"}]}
```

#### Recommendation

1. **Phase 1 default = Blockscout-only.** All FETCH-01..FETCH-04 requirements ship against Blockscout v1 getLogs. The subgraph leg is wired in code but defaults to disabled (env-gated by `GRAPH_API_KEY` presence).
2. **Phase 1 acquires a Graph API key as a Wave-1 task.** Subgraph Studio signup is free; the first 100k queries/mo are free (counts against the 90k soft cap regardless of paid/free status per CONTEXT.md decision).
3. **Phase 1.5 / early Phase 2 enrichment:** with the API key, run a `_meta` check against BOTH candidates. The one with `(forno_head - _meta.block.number) < 100` wins. If BOTH fail the freshness gate, the downgrade is final and Q96 tick math becomes a Phase-2 dead-code-exercised module (already specified in CONTEXT.md PRE_REGISTRATION REPRO-02 obligation).
4. **Add `[subgraphs.uniswap_v3]` block to `protocols/ichi.toml` after Phase 1.5 enrichment** — NOT in Phase 1 itself. The block schema needs the freshness-test verdict on which deployment ID to commit to.

#### Schema coverage caveat

Per WebSearch evidence: the Uniswap-tagged subgraph schema preserves `pool.feeGrowthGlobal0X128`, `pool.feeGrowthGlobal1X128`, `position.tickLower`, `position.tickUpper`, `position.feeGrowthInside0LastX128` — the fields needed for in-range LP-fee accrual. The Messari schema renames `Pool` → `LiquidityPool` and adds USD-denominated derived fields (TVL, cumulative volume) at the cost of dropping some Uniswap-protocol-specific fields. **For the LP-fee slice the Uniswap-tagged build is the correct choice** if it passes the freshness gate.

### B) ICHI vault subgraph existence

**Conclusion: NONE. No ICHI subgraph repo exists in the `ichifarm` GitHub org or anywhere indexed by GitHub search as of 2026-05-25.**

`ichifarm` repos verified live:
- `ichi-oneToken` (factory contracts, not subgraph)
- `ichi-farming`, `ichi-governance`, `ichi`, `hardhat-framework`, `audit`, `ichi-sdk`
- NO `*-subgraph` repos.

**Recommendation:** ICHI vault state for the Iter-1 microcosm is pulled via direct on-chain `eth_call` to the vault contract at `0xe304b980535c29869983BC58d129F984Fec4176F` via viem PublicClient against Forno. The fields needed (`getTotalAmounts()`, `getBasePosition()`, `getLimitPosition()`, etc.) are read at a Phase-2 cadence per swap event in the panel. This is **keeper-RPC class per DEMAND-01 — uncapped and free.** Phase 1 plan does NOT need to wire an ICHI-specific subgraph; the only subgraph in scope is the Uniswap V3 slice per (A) above.

### C) Blockscout v2 REST keyset pagination — VERIFIED LIVE

**Conclusion: Use Blockscout v1 etherscan-compat `/api?module=logs&action=getLogs` for topic-filtered bulk pulls. The v2 `/api/v2/addresses/{addr}/logs` endpoint is decoded-readable but does NOT support topic filtering and pages at 50 items by default.**

#### Live test results (2026-05-25, anchor pool `0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F`)

**v2 endpoint (no topic filter):**

```bash
$ curl -s 'https://celo.blockscout.com/api/v2/addresses/0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F/logs' | jq 'keys, .items|length, .next_page_params, .items[0]|keys'
```

Returns:
- Top-level keys: `["items", "next_page_params"]`
- Items per page: **50** (default, not configurable per Phase-0 doc claim of 1,000)
- `next_page_params`: `{"block_number": 67820789, "index": 237, "items_count": 50}` — keyset cursor
- Per-log keys: `["address", "block_hash", "block_number", "block_timestamp", "data", "decoded", "index", "smart_contract", "topics", "transaction_hash"]`
- **No `block_consensus`** field present.
- `topics` is an array of 4 entries: `[topic0, topic1, topic2, topic3]` — all hex strings prefixed with `0x`. Unindexed-slot topics are `null`.
- `decoded.method_call` includes the function signature; `decoded.parameters[]` carries `(indexed, name, type, value)` per arg.

**v2 endpoint with `topic0` filter — REJECTED:**

```bash
$ curl -s 'https://celo.blockscout.com/api/v2/addresses/0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F/logs?topic0=0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67'
{"errors":[{"title":"Invalid value","source":{"pointer":"/topic0"},"detail":"Unexpected field: topic0"}]}
# HTTP_CODE: 422
```

**v1 etherscan-compat with `topic0` filter — WORKS:**

```bash
$ curl -s 'https://celo.blockscout.com/api?module=logs&action=getLogs&fromBlock=67500000&toBlock=67830000&address=0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F&topic0=0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67' | jq '.status, .result|length, .result[0]|keys'
# status: 1, count: 554
# Per-log keys: ["address","blockNumber","data","gasPrice","gasUsed","logIndex","timeStamp","topics","transactionHash","transactionIndex"]
# blockNumber is a hex string ("0x4061986")
# topics array has 4 entries (topic0 + 3 indexed args), all 0x-prefixed hex
```

#### Wrapper sketch

```typescript
// fetch/src/blockscout/v1-getlogs.ts
import { z } from 'zod';

const LogSchema = z.object({
  address: z.string(),
  blockNumber: z.string(),       // hex
  timeStamp: z.string(),         // hex
  logIndex: z.string(),          // hex
  transactionHash: z.string(),
  topics: z.array(z.string().nullable()),
  data: z.string(),
});
const ResponseSchema = z.object({
  status: z.string(),
  message: z.string(),
  result: z.array(LogSchema),
});

export async function getLogsV1({
  baseUrl, address, fromBlock, toBlock, topic0, apiKey,
}: { baseUrl: string; address: string; fromBlock: number; toBlock: number; topic0: string; apiKey?: string; }) {
  const url = new URL(`${baseUrl}/api`);
  url.searchParams.set('module', 'logs');
  url.searchParams.set('action', 'getLogs');
  url.searchParams.set('address', address);
  url.searchParams.set('fromBlock', String(fromBlock));
  url.searchParams.set('toBlock', String(toBlock));
  url.searchParams.set('topic0', topic0);
  if (apiKey) url.searchParams.set('apikey', apiKey);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Blockscout v1 getLogs HTTP ${res.status}`);
  const parsed = ResponseSchema.parse(await res.json());
  if (parsed.status !== '1') throw new Error(`Blockscout v1 status=${parsed.status}: ${parsed.message}`);
  return parsed.result;
}
```

**Rate limits:** 3 req/sec free, 10 req/sec with free email-signup API key (`https://celo.blockscout.com/account/api-key`). At 4,440 swaps/30d for cKES/USDT, the bulk pull needs ≤ 5 requests; 3 req/sec is sufficient.

**Pagination:** v1 caps at ~1,000 results per call. For longer ranges, partition `[fromBlock, toBlock]` and re-call. The CLI in `cli.ts` MUST detect `result.length == 1000` as "needs another page" and re-issue with `fromBlock = lastBlock + 1`.

Sources:
- `https://github.com/blockscout/blockscout-api-v2-swagger/blob/main/swagger.yaml`
- `https://celo.blockscout.com/api-docs`
- Live API probes against cKES/USDT pool 2026-05-25.

### D) Uniswap V3 Swap event topic0 + ABI fragment — VERIFIED LIVE

**Conclusion: Swap topic0 = `0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67` (CONFIRMED by live decoded log on cKES/USDT pool).**

The decoded `method_call` from a live Blockscout v2 fetch:
```
Swap(address indexed sender, address indexed recipient, int256 amount0, int256 amount1, uint160 sqrtPriceX96, uint128 liquidity, int24 tick)
```

#### viem ABI fragment

```typescript
// fetch/src/decoders/uniswap-v3-swap.ts
import { type Abi, decodeEventLog } from 'viem';

export const UniswapV3SwapEventAbi = [
  {
    type: 'event',
    name: 'Swap',
    inputs: [
      { indexed: true,  name: 'sender',       type: 'address' },
      { indexed: true,  name: 'recipient',    type: 'address' },
      { indexed: false, name: 'amount0',      type: 'int256'  },
      { indexed: false, name: 'amount1',      type: 'int256'  },
      { indexed: false, name: 'sqrtPriceX96', type: 'uint160' },
      { indexed: false, name: 'liquidity',    type: 'uint128' },
      { indexed: false, name: 'tick',         type: 'int24'   },
    ],
  },
] as const satisfies Abi;

export const UniswapV3SwapTopic0 =
  '0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67' as const;

export function decodeSwap(topics: readonly `0x${string}`[], data: `0x${string}`) {
  return decodeEventLog({ abi: UniswapV3SwapEventAbi, eventName: 'Swap', topics, data });
}
```

The `as const satisfies Abi` cast is load-bearing for TS type inference; without it, `decodedSwap.args` is `unknown[]` instead of `{sender, recipient, amount0, amount1, sqrtPriceX96, liquidity, tick}`.

For Blockscout v1 logs (`topics` array has nullable entries for unindexed slots), the wire encoding is identical — pass the 4-entry topics array directly to `decodeEventLog`; viem ignores trailing nulls in strict mode if the ABI has fewer indexed args.

Sources:
- Live decoded `Swap` event on `0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F`, block 67,853,556 (2026-05-26).
- viem docs: `https://viem.sh/docs/contract/decodeEventLog`.

### E) `@x402/fetch` v2.13 + `@x402/evm` v2.13 minimal config for Base Sepolia — VERIFIED PATTERN

**Conclusion: Use `wrapFetchWithPayment(fetch, x402Client)` with `registerExactEvmScheme(client, { signer })`. Network spec is `"eip155:84532"`. Successful settlement returns an `X-PAYMENT-RESPONSE` header carrying a base64-encoded JSON `{success: true, transaction: "0x...", network: "...", payer: "0x..."}` — cost-ledger CAN log the Base Sepolia tx hash.**

#### Canonical TypeScript shape

```typescript
// fetch/src/x402-mock/client-bridge.ts
import { x402Client, wrapFetchWithPayment } from '@x402/fetch';
import { registerExactEvmScheme } from '@x402/evm/exact/client';
import { privateKeyToAccount } from 'viem/accounts';
import type { Hex } from 'viem';

const PRIVATE_KEY = process.env.PRIVATE_KEY as Hex;
if (!PRIVATE_KEY?.startsWith('0x')) {
  throw new Error('PRIVATE_KEY env var missing or malformed (must be 0x-prefixed hex)');
}

const signer = privateKeyToAccount(PRIVATE_KEY);

const client = new x402Client();
registerExactEvmScheme(client, {
  signer,
  // Optional but recommended: enables gas sponsoring via EIP-2612 + ERC-20 approval
  // rpcUrl: process.env.BASE_SEPOLIA_RPC_URL ?? 'https://sepolia.base.org',
});

export const fetchWithPayment = wrapFetchWithPayment(fetch, client);

// Usage against the local mock:
//   const res = await fetchWithPayment('http://localhost:4021/mock/weather');
//   const data = await res.json();
//   const paymentResponseHeader = res.headers.get('X-PAYMENT-RESPONSE');
//   if (paymentResponseHeader) {
//     const settlement = JSON.parse(Buffer.from(paymentResponseHeader, 'base64').toString());
//     // settlement = { success: true, transaction: '0x...', network: 'eip155:84532', payer: '0x...' }
//     await costLedger.append({
//       endpoint: 'x402-mock-sepolia',
//       paid_real: settlement.success,
//       tx_hash: settlement.transaction,
//       chain: 'base-sepolia',
//       cost_usdc: 0.001,
//       ...
//     });
//   }
```

#### Network spec format

`@x402/fetch` 2.13 uses CAIP-2 namespaced chain IDs: `eip155:<decimal_chain_id>`. Base Sepolia is `eip155:84532`. The 402 response body's `accepts[]` array declares which networks the server accepts; the client picks the first match against its registered schemes.

#### Base Sepolia USDC token address

`0x036cbd53842c5426634e7929541ec2318f3dcf7e` — confirmed live at `https://base-sepolia.blockscout.com/token/0x036CbD53842c5426634e7929541eC2318f3dCF7e`. The mock 402 server quotes payments in this asset.

#### Pointing at a real Graph gateway vs the localhost mock

`@x402/fetch` is transport-agnostic. The wrapped `fetch` works against ANY URL. Pointing at the mock vs a real gateway is a URL string change:
- Mock: `http://localhost:4021/mock/<endpoint>`
- Real Graph mainnet gateway: `https://gateway.thegraph.com/api/<API_KEY>/subgraphs/id/<deployment_id>` (Base mainnet settlement; out of Phase-1 scope)

#### Settlement tx hash capture

The `X-PAYMENT-RESPONSE` header is canonical (verified via Avalanche Builder Hub spec doc — it's standardized across all x402 EVM networks). The JSON shape after base64-decoding:

```json
{
  "success": true,
  "transaction": "0x<32-byte-tx-hash>",
  "network": "eip155:84532",
  "payer": "0x<20-byte-payer-address>",
  "errorReason": null
}
```

On failure: `success: false`, `errorReason` populated, `transaction: null`, accompanied by HTTP 402 and a fresh `accepts[]` body for retry.

Sources:
- `https://github.com/x402-foundation/x402/tree/main/examples/typescript/clients/fetch`
- `https://github.com/coinbase/x402/tree/main/examples/typescript/clients/fetch`
- `https://build.avax.network/academy/blockchain/x402-payment-infrastructure/03-technical-architecture/04-x-payment-response-header`
- `https://docs.cdp.coinbase.com/x402/quickstart-for-buyers`

### F) Self-hosted Node 402 mock server design — ~60 lines on `node:http`

**Conclusion: `node:http` is the lightest viable choice. The mock structurally validates the `X-PAYMENT` header (base64 → JSON parse → check signature is hex of right length) and returns a stub `X-PAYMENT-RESPONSE` with a deterministic fake tx hash. NO facilitator is needed — the mock IS the facilitator for this test substrate. Optional Phase-1.5 escalation: real on-chain settlement via viem `writeContract` on USDC `transferWithAuthorization`.**

#### HTTP framework choice

| Option | Verdict | Why |
|---|---|---|
| `node:http` (builtin) | **CHOSEN** | Zero deps; 60 lines covers spec; vitest can launch on a random port via `server.listen(0)` and read `server.address().port`. |
| `hono` + `@hono/node-server` | Acceptable but adds two deps | Cleaner middleware story; only worth it if Phase 2+ extends the mock substantially. |
| `express` | Reject | Heavyweight; deprecated stylistically; no async/await-first ergonomics. |
| `@x402/hono` middleware | Reject for the mock | This middleware EXPECTS a real facilitator URL; the mock IS the facilitator — wrong abstraction layer. |

#### Sketch (server.ts ~60 lines)

```typescript
// fetch/src/x402-mock/server.ts
import { createServer, type IncomingMessage, type ServerResponse } from 'node:http';
import { randomBytes } from 'node:crypto';

const X402_VERSION = 1;
const PAYMENT_REQUIREMENTS = {
  x402Version: X402_VERSION,
  accepts: [{
    scheme: 'exact',
    network: 'eip155:84532',
    maxAmountRequired: '1000',         // 0.001 USDC (6 decimals)
    resource: '/mock/weather',
    description: 'Mock 402 endpoint for x402 round-trip test',
    payTo: '0x000000000000000000000000000000000000dEaD', // burn address; mock never touches it
    asset: '0x036cbd53842c5426634e7929541ec2318f3dcf7e',  // Base Sepolia USDC
    mimeType: 'application/json',
    maxTimeoutSeconds: 60,
  }],
};

function makeStubTxHash(): string {
  return '0x' + randomBytes(32).toString('hex');
}

function validateXPaymentHeader(b64: string): { ok: boolean; payer?: string; reason?: string } {
  try {
    const decoded = JSON.parse(Buffer.from(b64, 'base64').toString());
    // Check shape: { x402Version, scheme: 'exact', network: 'eip155:84532', payload: {...} }
    if (decoded.scheme !== 'exact') return { ok: false, reason: 'scheme must be "exact"' };
    if (decoded.network !== 'eip155:84532') return { ok: false, reason: 'network mismatch' };
    const sig = decoded.payload?.signature;
    if (typeof sig !== 'string' || !/^0x[0-9a-fA-F]{130}$/.test(sig))
      return { ok: false, reason: 'invalid signature shape' };
    const payer = decoded.payload?.authorization?.from;
    if (typeof payer !== 'string' || !/^0x[0-9a-fA-F]{40}$/.test(payer))
      return { ok: false, reason: 'invalid payer' };
    return { ok: true, payer };
  } catch (e) {
    return { ok: false, reason: `header parse failed: ${(e as Error).message}` };
  }
}

function paymentResponseHeader(success: boolean, tx: string | null, payer: string | null, err: string | null): string {
  return Buffer.from(JSON.stringify({
    success, transaction: tx, network: 'eip155:84532', payer, errorReason: err,
  })).toString('base64');
}

export function startMockServer(port = 0) {
  const server = createServer((req: IncomingMessage, res: ServerResponse) => {
    if (req.url !== '/mock/weather') {
      res.writeHead(404); res.end(); return;
    }
    const xPay = req.headers['x-payment'] as string | undefined;
    if (!xPay) {
      res.writeHead(402, { 'content-type': 'application/json' });
      res.end(JSON.stringify(PAYMENT_REQUIREMENTS));
      return;
    }
    const v = validateXPaymentHeader(xPay);
    if (!v.ok) {
      res.writeHead(402, {
        'content-type': 'application/json',
        'x-payment-response': paymentResponseHeader(false, null, null, v.reason ?? 'invalid'),
      });
      res.end(JSON.stringify({ ...PAYMENT_REQUIREMENTS, error: v.reason }));
      return;
    }
    const tx = makeStubTxHash();
    res.writeHead(200, {
      'content-type': 'application/json',
      'x-payment-response': paymentResponseHeader(true, tx, v.payer!, null),
    });
    res.end(JSON.stringify({ weather: 'mock-sunny', timestamp: Date.now() }));
  });
  return new Promise<{ server: ReturnType<typeof createServer>; port: number }>((resolve) =>
    server.listen(port, () => resolve({ server, port: (server.address() as { port: number }).port })),
  );
}

if (import.meta.url === `file://${process.argv[1]}`) {
  startMockServer(4021).then(({ port }) => console.log(`x402 mock listening on http://localhost:${port}`));
}
```

#### Test harness shape (`fetch/tests/x402-mock.test.ts`)

```typescript
import { describe, test, expect, beforeAll, afterAll } from 'vitest';
import type { Server } from 'node:http';
import { startMockServer } from '../src/x402-mock/server';
import { fetchWithPayment } from '../src/x402-mock/client-bridge';

let server: Server, port: number;
beforeAll(async () => { ({ server, port } = await startMockServer(0)); });
afterAll(() => new Promise<void>((r) => server.close(() => r())));

test('round-trip: 402 → sign → retry → 200 + X-PAYMENT-RESPONSE carries tx hash', async () => {
  const res = await fetchWithPayment(`http://localhost:${port}/mock/weather`);
  expect(res.status).toBe(200);
  const settleHeader = res.headers.get('x-payment-response');
  expect(settleHeader).toBeTruthy();
  const settle = JSON.parse(Buffer.from(settleHeader!, 'base64').toString());
  expect(settle.success).toBe(true);
  expect(settle.transaction).toMatch(/^0x[0-9a-f]{64}$/);
  expect(settle.network).toBe('eip155:84532');
});
```

#### Decision: header-only mock vs real on-chain settlement

**Phase 1 ships header-only.** The mock NEVER broadcasts a real USDC `transferWithAuthorization` — it just validates header structure and returns a stub tx hash. This keeps the test deterministic, no faucet drain, no Base Sepolia RPC dependency in CI.

**Optional Phase-1.5 toggle (`X402_MOCK_REAL_SETTLE=1`):** swap the mock's `validateXPaymentHeader` for a viem `simulateContract`/`writeContract` call that submits the EIP-3009 transferWithAuthorization to USDC on Base Sepolia and returns the actual tx hash. Documented but not on the Phase 1 critical path.

Sources:
- `https://github.com/x402-foundation/x402/tree/main/examples/typescript/servers/hono` (server shape reference)
- `https://docs.x402.org/getting-started/quickstart-for-sellers`
- `https://github.com/coinbase/x402/blob/main/specs/schemes/exact/scheme_exact_evm.md`

### G) Subgraph-freshness wrapper

```typescript
// fetch/src/subgraph/freshness.ts
import type { PublicClient } from 'viem';

export interface SubgraphMeta {
  block: { number: number; hash?: string; timestamp?: number };
}
export interface SubgraphFreshnessInput<T> {
  response: T & { _meta?: SubgraphMeta };
  forno: PublicClient;
}

export class SubgraphLagError extends Error {
  constructor(public details: { subgraph_block: number; forno_head: number; lag: number; threshold: number; deployment_id?: string }) {
    super(`Subgraph stale: lag=${details.lag} blocks > threshold=${details.threshold} (subgraph=${details.subgraph_block}, forno=${details.forno_head})`);
    this.name = 'SubgraphLagError';
  }
}

export async function subgraphFreshness<T>({ response, forno }: SubgraphFreshnessInput<T>, threshold = 100): Promise<T> {
  const meta = response._meta;
  if (!meta?.block?.number) {
    throw new SubgraphLagError({ subgraph_block: -1, forno_head: -1, lag: -1, threshold });
  }
  const head = Number(await forno.getBlockNumber());
  const lag = head - meta.block.number;
  if (lag > threshold) {
    throw new SubgraphLagError({ subgraph_block: meta.block.number, forno_head: head, lag, threshold });
  }
  return response;
}
```

#### Vitest test harness

```typescript
// fetch/tests/freshness.test.ts (subgraph half)
import { describe, test, expect, vi } from 'vitest';
import { subgraphFreshness, SubgraphLagError } from '../src/subgraph/freshness';

const fornoMock = (head: bigint) => ({ getBlockNumber: vi.fn().mockResolvedValue(head) }) as any;

describe('subgraphFreshness', () => {
  test('passes at lag = 99', async () => {
    const r = await subgraphFreshness({ response: { _meta: { block: { number: 67_854_023 } }, foo: 1 }, forno: fornoMock(67_854_122n) });
    expect(r.foo).toBe(1);
  });
  test('throws SubgraphLagError at lag = 101', async () => {
    await expect(
      subgraphFreshness({ response: { _meta: { block: { number: 67_854_021 } }, foo: 1 }, forno: fornoMock(67_854_122n) })
    ).rejects.toBeInstanceOf(SubgraphLagError);
  });
  test('throws when _meta is missing', async () => {
    await expect(
      subgraphFreshness({ response: { foo: 1 } as any, forno: fornoMock(67_854_122n) })
    ).rejects.toBeInstanceOf(SubgraphLagError);
  });
});
```

Threshold defaults to 100 blocks per PITFALLS.md §2 / CONTEXT.md. At 1 s/block (Celo post-2024 hardfork, verified at `protocols/_schema.toml :: celo_block_time_seconds = 1.0`), 100 blocks ≈ 100 seconds — generous for indexer steady-state, strict enough to flag stalls.

### H) Blockscout-freshness wrapper — CORRECTED (no `block_consensus`)

**Conclusion: CONTEXT.md's spec that the wrapper checks `block_consensus = false` per log is UNFOUNDED. The Blockscout v2 (and v1) log shapes do not expose any per-log consensus field. The wrapper relies on `most_recent_log_block` lag vs Forno head only.**

```typescript
// fetch/src/blockscout/freshness.ts
import type { PublicClient } from 'viem';

export class BlockscoutFreshnessError extends Error {
  constructor(public details: { most_recent_log_block: number; forno_head: number; lag: number; threshold: number; endpoint: string }) {
    super(`Blockscout response stale: lag=${details.lag} blocks > threshold=${details.threshold} from ${details.endpoint}`);
    this.name = 'BlockscoutFreshnessError';
  }
}

export async function blockscoutFreshness({
  most_recent_log_block, forno, threshold = 100, endpoint,
}: { most_recent_log_block: number; forno: PublicClient; threshold?: number; endpoint: string }) {
  const head = Number(await forno.getBlockNumber());
  const lag = head - most_recent_log_block;
  if (lag > threshold) {
    throw new BlockscoutFreshnessError({ most_recent_log_block, forno_head: head, lag, threshold, endpoint });
  }
  return { lag, fresh: true };
}
```

#### Test harness (synthetic responses)

```typescript
// fetch/tests/freshness.test.ts (blockscout half)
import { describe, test, expect, vi } from 'vitest';
import { blockscoutFreshness, BlockscoutFreshnessError } from '../src/blockscout/freshness';

const fornoMock = (head: bigint) => ({ getBlockNumber: vi.fn().mockResolvedValue(head) }) as any;

describe('blockscoutFreshness', () => {
  test('passes at lag = 99', async () => {
    const r = await blockscoutFreshness({ most_recent_log_block: 67_854_023, forno: fornoMock(67_854_122n), endpoint: 'celo.blockscout.com' });
    expect(r.fresh).toBe(true);
  });
  test('throws at lag = 101', async () => {
    await expect(
      blockscoutFreshness({ most_recent_log_block: 67_854_021, forno: fornoMock(67_854_122n), endpoint: 'celo.blockscout.com' })
    ).rejects.toBeInstanceOf(BlockscoutFreshnessError);
  });
});
```

**Plan author note:** delete the `block_consensus = false` check from any Phase 1 PLAN.md draft. The CONTEXT.md spec there is wrong; this RESEARCH.md supersedes it. The Phase-1 reality-checker review must flag any PLAN.md draft that retains the `block_consensus` clause.

### I) Content-addressed cache implementation

**Conclusion: Cache key = `sha256(JSON.stringify({chainId, contractAddress: lowercase, blockRange: [from, to]}))`. Storage: `data/raw/<protocol>/<sha256-prefix>/<full-sha256>.parquet`. Manifest is a top-level append-only JSON ARRAY at `data/raw/manifest.json` keyed by `cache_key_hash`.**

#### Canonical serialization

```typescript
// fetch/src/cache/key.ts
import { createHash } from 'node:crypto';

export interface CacheKeyInput {
  chainId: number;
  contractAddress: string;
  blockRange: [number, number];
}

export function canonicalize({ chainId, contractAddress, blockRange }: CacheKeyInput): string {
  const normalized = {
    chainId,
    contractAddress: contractAddress.toLowerCase(),  // EIP-55 → lowercase for hash stability
    blockRange: [blockRange[0], blockRange[1]],     // tuple → array, no nesting drift
  };
  return JSON.stringify(normalized, Object.keys(normalized).sort());
}

export function cacheKeyHash(input: CacheKeyInput): string {
  return createHash('sha256').update(canonicalize(input)).digest('hex');
}
```

**Rationale for lowercase address:** Two callers may pass `0x61Ef8708...` (EIP-55 mixed-case) and `0x61ef8708...` for the same pool. Lowercasing pre-hash makes the key invariant against caller style.

**Rationale for sorted keys:** `JSON.stringify` with a sorted-keys replacer guarantees deterministic byte output regardless of object property order at the call site.

**`fetchTimestamp` NOT in input** — paid-step-idempotent invariant (FETCH-04). This is the CONTEXT.md decision overriding ROADMAP SC-4's incorrect bracket.

#### Storage layout

```
data/raw/
├── manifest.json                                # append-only JSON ARRAY
├── _cost_ledger.parquet                         # append-only Parquet (cost-ledger)
└── ichi/
    └── <first-2-chars-of-hash>/
        └── <full-64-char-sha256>.parquet
```

The `<first-2-chars>` shard avoids hundreds of files in one dir without imposing a deep tree.

#### Manifest schema (per entry; manifest.json is an array of these)

```typescript
// fetch/src/cache/manifest.ts
import { z } from 'zod';

export const ManifestEntrySchema = z.object({
  cache_key_hash: z.string().regex(/^[0-9a-f]{64}$/),
  chainId: z.number(),
  contractAddress: z.string(),
  blockRange: z.tuple([z.number(), z.number()]),
  fetchTimestamp: z.string(),                  // ISO-8601 UTC, metadata only
  dataHash: z.string().regex(/^[0-9a-f]{64}$/),  // sha256 of the Parquet file content
  gitCommit: z.string(),                        // HEAD hash at fetch time
  endpoint: z.enum(['graph-mainnet', 'graph-sepolia', 'blockscout', 'forno', 'x402-mock-sepolia']),
  query_count: z.number().int().nonnegative(), // # of paginated requests
  usdc_cost: z.string(),                        // decimal string; "0.000" for free-tier
  paid_real: z.boolean(),
  response_sha256_per_endpoint: z.record(z.string(), z.string()).optional(),  // per-page hashes
  protocol: z.string(),                         // "ichi", "steer"
  fetcher_version: z.string(),                  // git tag or commit short hash
});
export type ManifestEntry = z.infer<typeof ManifestEntrySchema>;
```

#### Two-run byte-identity test (SC-4)

```typescript
// fetch/tests/cache-idempotency.test.ts
import { describe, test, expect, beforeEach } from 'vitest';
import { execSync } from 'node:child_process';
import { readFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';

const sha = (path: string) => createHash('sha256').update(readFileSync(path)).digest('hex');

describe('cache idempotency (FETCH-04 SC-4)', () => {
  beforeEach(() => {
    execSync('rm -rf data/raw/ichi/*'); // clean cache before each
  });
  test('two runs of identical fetch produce byte-identical Parquet + zero new ledger rows', async () => {
    const cmd = 'pnpm fetch ichi --pool 0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F --from 67700000 --to 67800000';
    execSync(cmd); // first run
    const cacheFile = execSync('ls data/raw/ichi/**/**.parquet').toString().trim().split('\n').sort()[0];
    const ledgerRows1 = JSON.parse(execSync('jq length data/raw/manifest.json').toString());
    const hash1 = sha(cacheFile);

    execSync(cmd); // second run — should be a cache hit
    const hash2 = sha(cacheFile);
    const ledgerRows2 = JSON.parse(execSync('jq length data/raw/manifest.json').toString());

    expect(hash1).toBe(hash2);
    expect(ledgerRows2).toBe(ledgerRows1);
  });
});
```

### J) Cost-ledger Parquet schema

**Conclusion: Use `hyparquet-writer` (pure-JS Parquet writer) to append to `data/raw/_cost_ledger.parquet`. Schema mirrors the manifest entry but is row-oriented for analytics. Alternative: defer Parquet write to Python in Phase 2 by emitting JSONL in Phase 1.**

#### Schema (TS view; polars will read this in Phase 2)

```typescript
// fetch/src/cost-ledger.ts
import { z } from 'zod';

export const CostLedgerRowSchema = z.object({
  timestamp: z.string(),                      // ISO-8601 UTC (Parquet: TIMESTAMP_MICROS UTC)
  endpoint: z.enum(['graph-mainnet', 'graph-sepolia', 'blockscout', 'forno', 'x402-mock-sepolia']),
  query_id: z.string(),                       // sha256 of (endpoint, url, body)[:16]
  cost_usdc: z.string(),                      // decimal string; encode as Parquet DECIMAL(18,6) — but pure-JS writers can't write DECIMAL, store as STRING and convert in polars
  paid_real: z.boolean(),
  tx_hash: z.string().nullable(),             // null for unpaid (free-tier or model-only)
  chain: z.enum(['celo', 'base-sepolia']).nullable(),
  response_bytes: z.number().int().nonnegative(),
  response_sha256: z.string().regex(/^[0-9a-f]{64}$/),
  fetch_id: z.string(),                       // sha256 of the (chainId, contract, blockRange) tuple — links rows to manifest
});
export type CostLedgerRow = z.infer<typeof CostLedgerRowSchema>;
```

#### Append strategy

`hyparquet-writer` writes a complete file per call. For an append-only ledger:
1. Read existing `_cost_ledger.parquet` via `hyparquet` (if it exists) into memory.
2. Concat new rows.
3. Atomic-write to `_cost_ledger.parquet.tmp` then `rename()` (POSIX atomic).

Volume estimate: 4,440 swaps/30d × ~1 ledger row per fetch ≈ ~150 rows/mo per pool. Even with 10 pools, < 2k rows/mo. Memory-rewrite is fine at this volume; if Phase 2 panel-build pushes the ledger above 1M rows, switch to per-month-shard files (`_cost_ledger_2026_06.parquet`).

#### Fallback: JSONL handoff

If `hyparquet-writer` has stability issues, Phase 1 writes `_cost_ledger.jsonl` and Phase 2 ingests via `polars.read_ndjson(...).write_parquet(...)`. Same row schema. CONTEXT.md decision allows this (it says "Parquet" in spirit; the format invariant is what matters, not the producer).

### K) 90k Graph budget gate

**Algorithm:**

```typescript
// fetch/src/cost-ledger.ts (continued)
import { readParquet } from 'hyparquet';

export class GraphBudgetExceededError extends Error {
  constructor(public details: { current: number; projected: number; cap: number; force: boolean }) {
    super(`Graph budget cap: current=${details.current} + projected=${details.projected} > cap=${details.cap}. Pass --force to bypass.`);
  }
}

export async function checkBudget({
  projected_graph_queries,
  force = false,
  ledger_path = 'data/raw/_cost_ledger.parquet',
  cap = 90_000,
}: { projected_graph_queries: number; force?: boolean; ledger_path?: string; cap?: number }) {
  const now = new Date();
  const monthStart = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1)).toISOString();

  let current = 0;
  try {
    const rows = await readParquet(ledger_path);
    current = rows.filter((r: any) => r.endpoint === 'graph-mainnet' && r.timestamp >= monthStart).length;
  } catch (e: any) {
    if (e.code !== 'ENOENT') throw e;
    // ledger doesn't exist yet → current = 0
  }

  if (!force && current + projected_graph_queries > cap) {
    throw new GraphBudgetExceededError({ current, projected: projected_graph_queries, cap, force });
  }
  return { current, projected: projected_graph_queries, cap, would_exceed: current + projected_graph_queries > cap };
}
```

The `--force` flag plumbs through `cli.ts` argv and propagates to `checkBudget({force: argv.force})`. The error message MUST surface `current` and `projected` separately so the operator can decide whether to bypass.

**Important:** `endpoint = "graph-mainnet"` counts both paid AND free-tier queries against the cap — per CONTEXT.md decision, both bucket into the same 100k/mo allowance from The Graph's pricing model. `endpoint = "blockscout"`, `"forno"`, `"x402-mock-sepolia"` are uncapped.

### L) Protocol-agnosticism contract test (SC-5)

**Conclusion: Two-layer enforcement. (1) Vitest test that grep-loads `fetch/src/**/*.ts` and asserts NO occurrence of forbidden patterns. (2) Existing pre-commit AF-08 hook is the cheap complement.**

#### Test harness

```typescript
// fetch/tests/protocol-agnostic.test.ts
import { describe, test, expect } from 'vitest';
import { readFileSync, readdirSync } from 'node:fs';
import { join, extname } from 'node:path';

function* walk(dir: string): Generator<string> {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory() && !entry.name.startsWith('.')) yield* walk(full);
    else if (entry.isFile() && ['.ts', '.tsx', '.js'].includes(extname(entry.name))) yield full;
  }
}

const FORBIDDEN_PATTERNS = [
  /if\s*\(\s*config\.name\s*===?\s*['"]ichi['"]/,
  /if\s*\(\s*config\.name\s*===?\s*['"]steer['"]/,
  /if\s*\(\s*protocol\s*===?\s*['"]ichi['"]/,
  /if\s*\(\s*protocol\s*===?\s*['"]steer['"]/,
  /if\s*\(\s*vault_owner\s*===?\s*['"]ichi['"]/,
  /\b(0x9FAb4bdD4E05f5C023CCC85D2071b49791D7418F)\b/i, // ICHI factory address outside protocols/
  /\b(0x116Dba5DcE9CcDA828218b7eB46406810632014C)\b/i, // Steer factory address outside protocols/
];
const FORBIDDEN_FEE_TIERS = [
  /\bfee\s*[:=]\s*(0\.0001|100|500|3000|10000)\b/, // magic fee-tier literals
];

describe('protocol-agnosticism (FETCH-01 SC-5)', () => {
  test('no protocol-name conditionals or hard-coded addresses in fetch/src/', () => {
    const offenders: { file: string; pattern: string; line: number }[] = [];
    for (const file of walk('src')) {
      const lines = readFileSync(file, 'utf-8').split('\n');
      for (let i = 0; i < lines.length; i++) {
        for (const pat of [...FORBIDDEN_PATTERNS, ...FORBIDDEN_FEE_TIERS]) {
          if (pat.test(lines[i])) offenders.push({ file, pattern: pat.source, line: i + 1 });
        }
      }
    }
    expect(offenders).toEqual([]);
  });

  test('synthetic protocol fixture loads with same code path', async () => {
    const { loadProtocol } = await import('../src/protocol-spec');
    const fixture = await loadProtocol('tests/fixtures/test_fixture.toml');
    expect(fixture.name).toBeTruthy();
    expect(fixture.anchor_pool.address).toMatch(/^0x[0-9a-fA-F]{40}$/);
    // Note: NO assertion on name being "ichi" or "steer" — the test fixture name is e.g. "synthetic-test"
  });
});
```

#### Synthetic fixture

```toml
# fetch/tests/fixtures/test_fixture.toml
[protocol]
name = "synthetic-test"
chain_id = 42220
factory_address = "0xdEAD000000000000000000000000000000beef00"
data_cost_class = "indexer-analytics-queries"
panel_construction = "single-vault"
iteration = 99

[protocol.anchor_pool]
address = "0xdEAD000000000000000000000000000000beef01"
token0 = "0xdEAD000000000000000000000000000000beef02"
token1 = "0xdEAD000000000000000000000000000000beef03"
fee_tier = 7777  # non-standard tier; tests must not branch on this
mixing_class = "mento-native"

[protocol.vaults.synthetic_vault_1]
address = "0xdEAD000000000000000000000000000000beef10"
address_resolution_status = "verified"
active = true
mixing_class = "mento-native"
pool_address = "0xdEAD000000000000000000000000000000beef01"
```

The fixture uses `fee_tier = 7777` (a non-standard tier) to verify the production code reads `fee_tier` from the TOML rather than from a hard-coded set `{100, 500, 3000, 10000}`.

### M) Cold-backfill budget dry-run (FETCH-02 SC-6)

**Conclusion: `pnpm fetch ichi --dry-run --estimate-budget` is a pure function over `protocols/ichi.toml` + the Forno head block. It does NOT consult the live Blockscout/subgraph — it computes a static estimate from the in-scope vault set and emits a JSON estimate.**

#### Algorithm

```typescript
// fetch/src/cli.ts (excerpt)
export interface BudgetEstimate {
  protocol: string;
  iteration: number;
  vault_count: number;
  blocks_per_vault: number;
  queries_per_vault: number;     // # of paginated subgraph + Blockscout calls per vault
  total_queries: number;
  exceeds_earmark: boolean;
  earmark: number;
  recommended_reallocation: string | null;
}

export function estimateBudget(spec: ProtocolSpec, fornoHead: number, earmark = 30_000): BudgetEstimate {
  const activeVaults = Object.entries(spec.vaults).filter(([_, v]) => v.active);
  const vault_count = activeVaults.length;

  // Phase-1 cold-backfill scope = active vaults only (Iter-1: cKES_USDT_anchor only)
  const blocks_per_vault = fornoHead - (spec.cold_backfill_from_block ?? 65_000_000);

  // Per-vault query model: ~1 subgraph LP-fee query per 10k blocks (entity snap cadence) + Blockscout pagination (1 call per 1k swaps)
  const subgraph_queries_per_vault = Math.ceil(blocks_per_vault / 10_000);
  const blockscout_queries_per_vault = Math.ceil(spec.anchor_pool.swaps_per_30d_observed / 1_000);  // ~5 for cKES/USDT
  const queries_per_vault = subgraph_queries_per_vault + blockscout_queries_per_vault;

  const total_queries = vault_count * queries_per_vault;
  // Only subgraph queries count against 90k Graph budget
  const graph_total = vault_count * subgraph_queries_per_vault;
  const exceeds_earmark = graph_total > earmark;

  return {
    protocol: spec.name,
    iteration: spec.iteration,
    vault_count,
    blocks_per_vault,
    queries_per_vault,
    total_queries,
    exceeds_earmark,
    earmark,
    recommended_reallocation: exceeds_earmark
      ? `Projected graph queries (${graph_total}) exceeds ${earmark} earmark. Options: (a) re-scope vault set, (b) reallocate from 45k reserve, (c) pass --force to bypass at the gate.`
      : null,
  };
}
```

For Iter-1 with `single-vault` panel construction (1 active vault, cKES_USDT_anchor):
- `vault_count = 1`
- `blocks_per_vault ≈ 67,854,122 - 65,000,000 = 2.85M blocks`
- `subgraph_queries_per_vault ≈ 285`
- `blockscout_queries_per_vault ≈ 5`
- `total_queries ≈ 290`
- `graph_total ≈ 285` — comfortably under the 30k earmark.

#### JSON output shape

```bash
$ pnpm fetch ichi --dry-run --estimate-budget
{
  "protocol": "ichi",
  "iteration": 1,
  "vault_count": 1,
  "blocks_per_vault": 2854122,
  "queries_per_vault": 290,
  "total_queries": 290,
  "exceeds_earmark": false,
  "earmark": 30000,
  "recommended_reallocation": null
}
```

#### Test harness

```typescript
// fetch/tests/budget-dry-run.test.ts
import { describe, test, expect } from 'vitest';
import { estimateBudget } from '../src/cli';
import { loadProtocol } from '../src/protocol-spec';

test('ichi single-vault dry-run under 30k earmark', async () => {
  const spec = await loadProtocol('../protocols/ichi.toml');
  const est = estimateBudget(spec, 67_854_122);
  expect(est.exceeds_earmark).toBe(false);
  expect(est.vault_count).toBe(1);
  expect(est.total_queries).toBeLessThan(1000);
});

test('synthetic 50-vault spec triggers reallocation', async () => {
  const spec50 = { /* construct synthetic ProtocolSpec with 50 active vaults */ };
  const est = estimateBudget(spec50 as any, 67_854_122, 30_000);
  expect(est.exceeds_earmark).toBe(true);
  expect(est.recommended_reallocation).toContain('reallocate');
});
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Blockscout v1 etherscan-compat ONLY | Blockscout v2 typed endpoints + v1 for topic filter | Blockscout v2 GA ~2023 | Use v2 for decoded responses; v1 still required for topic-filtered bulk pull |
| The Graph hosted service (`api.thegraph.com/subgraphs/name/<user>/<repo>`) | The Graph Decentralized Network gateway (`gateway.thegraph.com/api/<KEY>/subgraphs/id/<deployment_id>`) | Hosted service deprecated 2024-Q2 | All Graph reads require API key; first 100k queries/mo free per key |
| `eth_getLogs` direct via Forno | Blockscout topic-filtered bulk pull | 2024+ as Forno tightened limits | Blockscout v1 getLogs is the canonical free-tier bulk-event-pull path |
| Manual 402 server with bespoke header parsing | `@x402/fetch` 2.13 + `@x402/evm` 2.13 + canonical `X-PAYMENT-RESPONSE` base64-encoded settlement JSON | x402 v2 spec stabilized 2026-Q1 | TX hash retrieval is standardized in the response header |

**Deprecated/outdated:**
- The Graph hosted service URLs (`api.thegraph.com/subgraphs/name/...`): permanently unavailable.
- `eth_getLogs` direct via Forno for ranges > 10k blocks: tripping rate limits in 2025+; use Blockscout v1 getLogs instead.
- viem v1.x: superseded by 2.x; no Celo L2 chain-config nuances.

## Open Questions

1. **Graph API key procurement timing**
   - What we know: Subgraph Studio signup is free + < 5 min. First 100k queries/mo per key.
   - What's unclear: Whether to use a single key for the entire `abrigo-x402` repo (shared in `.env.example` as a documented test key) or per-developer keys (each contributor signs up). Per-developer keys avoid one-key-DoS-the-CI-budget but complicate CI setup.
   - Recommendation: Single shared org key in `.env.example` (documented as "test key — replace for production"); CI uses a separate `GRAPH_API_KEY` secret. Phase 1 plan must include "sign up + commit `.env.example` with key placeholder" as a wave-1 task.

2. **Schema-frozen-check impact of adding `[subgraphs.uniswap_v3]` block to `protocols/ichi.toml`**
   - What we know: `protocols/_schema.toml` (commit `e9b214d`) does NOT specify a `[subgraphs.*]` block, but it also does not enumerate every legal per-protocol block — it lists what's REQUIRED, not what's EXHAUSTIVE.
   - What's unclear: Whether `make schema-frozen-check` (which runs `git diff <baseline> -- protocols/_schema.toml`) ALSO checks per-protocol TOML files for fields not in `_schema.toml`. If yes, adding the new block requires a Phase-0-style schema increment. If no, the addition is silent.
   - Recommendation: Phase 1 Plan must include a probe task that authors a draft `protocols/ichi.toml` with the new block, runs `make schema-frozen-check`, and reports whether it rejects. Take the verdict to choose between (a) extending ichi.toml only, or (b) re-opening `_schema.toml` for a new baseline.

3. **hyparquet stability at sub-1k-row scale**
   - What we know: hyparquet is the only stable pure-JS Parquet writer; the cost-ledger has at most 2k rows/mo.
   - What's unclear: Whether atomic-rewrite-the-whole-file is acceptable in CI environments (concurrent fetch processes could race; but Phase 1 is single-process).
   - Recommendation: Lock to single-process semantics for Phase 1 (a `.lock` file in `data/raw/` if needed). Defer concurrent-fetch consideration to v2.

4. **Real on-chain Base Sepolia settlement vs header-only mock**
   - What we know: Header-only mock is faster, deterministic, CI-friendly. Real settlement validates more of the x402 spec.
   - What's unclear: Whether the Phase-5 PDF deliverable's "product validation footnote" wants a real Base Sepolia tx hash from Phase 1 or a real Base mainnet tx from a one-shot post-Phase-5 action.
   - Recommendation: Phase 1 ships header-only. Phase 1.5 toggle behind `X402_MOCK_REAL_SETTLE=1` for opt-in real-settle CI runs. Defer the "real mainnet tx in PDF" decision to Phase 5 planning.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | vitest 4.1.7 (ESM, native TS, fast watch mode) |
| Config file | `fetch/vitest.config.ts` |
| Quick run command | `pnpm --filter fetch test -- --run` |
| Full suite command | `pnpm --filter fetch test:full` (= `vitest run` + integration suite when `INTEGRATION=1`) |

Vitest installation is part of FETCH-01's pnpm workspace bootstrap — no separate Wave 0 task. Config file does not exist yet (the workspace doesn't exist). Plan Wave 0 task: create `fetch/vitest.config.ts` and `fetch/tsconfig.json`.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FETCH-01 | TS workspace bootstraps; `pnpm tsc --noEmit` exits 0 | smoke (build) | `pnpm --filter fetch exec tsc --noEmit` | ❌ Wave 0 |
| FETCH-01 | All pinned deps install at exact versions | smoke (install) | `pnpm --filter fetch ls --depth 0 \| grep -E '^(viem 2\.51\.0\|@x402/fetch 2\.13\.0\|@x402/evm 2\.13\.0)'` | ❌ Wave 0 |
| FETCH-02 | Cost-ledger writes a row per request | unit | `pnpm --filter fetch test -- --run cost-ledger.test` | ❌ Wave 0 |
| FETCH-02 | 90k Graph budget gate throws on projection > cap | unit | `pnpm --filter fetch test -- --run cost-ledger.test -t 'budget gate'` | ❌ Wave 0 |
| FETCH-02 | `--force` flag bypasses 90k gate | unit | `pnpm --filter fetch test -- --run cost-ledger.test -t 'force bypass'` | ❌ Wave 0 |
| FETCH-02 | x402 mock round-trip emits cost-ledger row with `paid_real=false; chain="base-sepolia"; tx_hash=0x...` | integration (local mock) | `pnpm --filter fetch test -- --run x402-mock.test` | ❌ Wave 0 |
| FETCH-02 | Dry-run estimate prints JSON with `total_queries`, `exceeds_earmark` | unit | `pnpm --filter fetch test -- --run budget-dry-run.test` | ❌ Wave 0 |
| FETCH-03 | `subgraphFreshness` throws `SubgraphLagError` at lag = 101 | unit | `pnpm --filter fetch test -- --run freshness.test -t 'lag = 101'` | ❌ Wave 0 |
| FETCH-03 | `subgraphFreshness` passes at lag = 99 | unit | `pnpm --filter fetch test -- --run freshness.test -t 'lag = 99'` | ❌ Wave 0 |
| FETCH-03 | `blockscoutFreshness` throws at lag = 101 | unit | `pnpm --filter fetch test -- --run freshness.test -t 'blockscout.*101'` | ❌ Wave 0 |
| FETCH-03 | `blockscoutFreshness` passes at lag = 99 | unit | `pnpm --filter fetch test -- --run freshness.test -t 'blockscout.*99'` | ❌ Wave 0 |
| FETCH-03 | Missing `_meta` throws | unit | `pnpm --filter fetch test -- --run freshness.test -t 'missing _meta'` | ❌ Wave 0 |
| FETCH-04 | Two runs of identical fetch produce byte-identical Parquet | integration (filesystem + sha256) | `pnpm --filter fetch test -- --run cache-idempotency.test` | ❌ Wave 0 |
| FETCH-04 | Second run emits zero new ledger rows | integration | `pnpm --filter fetch test -- --run cache-idempotency.test -t 'zero new ledger rows'` | ❌ Wave 0 |
| SC-5 | No protocol-name branches, hard-coded fee tiers, or factory addresses in `fetch/src/` | unit (static analysis) | `pnpm --filter fetch test -- --run protocol-agnostic.test` | ❌ Wave 0 |
| SC-5 | Synthetic protocol fixture loads | unit | `pnpm --filter fetch test -- --run protocol-agnostic.test -t 'fixture'` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pnpm --filter fetch test -- --run` (excludes integration suite by default; runs in < 30s)
- **Per wave merge:** `pnpm --filter fetch test:full` (full vitest suite including integration; live-network probes if `INTEGRATION=1` in env)
- **Phase gate (before `/gsd:verify-work`):** Full suite green + `pnpm --filter fetch exec tsc --noEmit` exits 0 + `make verify-cache-idempotency` (a Makefile target that hashes the ICHI cache after two runs)

### Wave 0 Gaps

- [ ] `fetch/vitest.config.ts` — vitest config (ESM, no watch in CI, optional coverage)
- [ ] `fetch/tsconfig.json` — strict, ESM, nodenext module resolution
- [ ] `fetch/tests/freshness.test.ts` — covers FETCH-03 (both wrappers)
- [ ] `fetch/tests/cache-idempotency.test.ts` — covers FETCH-04
- [ ] `fetch/tests/x402-mock.test.ts` — covers FETCH-02 (x402 round-trip)
- [ ] `fetch/tests/cost-ledger.test.ts` — covers FETCH-02 (budget gate, --force)
- [ ] `fetch/tests/budget-dry-run.test.ts` — covers SC-6
- [ ] `fetch/tests/protocol-agnostic.test.ts` — covers SC-5
- [ ] `fetch/tests/fixtures/*.json` — captured Blockscout v1 + v2 responses (run once live, commit to repo)
- [ ] `fetch/tests/fixtures/test_fixture.toml` — synthetic protocol-agnosticism fixture
- [ ] Framework install: `pnpm add -Dw vitest@^4.1` at root (covered by FETCH-01 install task)

## Sources

### Primary (HIGH confidence)

- **Live Blockscout v2 API probe** against `0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F` on 2026-05-25:
  - `/api/v2/addresses/<addr>/logs` returns 50 items/page, no `block_consensus`, no `topic0` filter (HTTP 422)
  - `/api?module=logs&action=getLogs&topic0=…` returns 554 logs in one call (within 1000-row cap)
  - Forno `eth_blockNumber` = 67,854,122 (decimal)
- **Blockscout API v2 Swagger:** `https://github.com/blockscout/blockscout-api-v2-swagger/blob/main/swagger.yaml` (verified Log schema, keyset pagination via `next_page_params`)
- **viem chain definitions** (raw GitHub HEAD): celo id 42220, baseSepolia id 84532
- **`@x402/fetch` examples:** `https://github.com/x402-foundation/x402/tree/main/examples/typescript/clients/fetch` (canonical `wrapFetchWithPayment(fetch, x402Client)` + `registerExactEvmScheme(client, { signer })`)
- **x402 X-PAYMENT-RESPONSE spec:** `https://build.avax.network/academy/blockchain/x402-payment-infrastructure/03-technical-architecture/04-x-payment-response-header` (base64-encoded JSON with `success`, `transaction`, `network`, `payer`, `errorReason`)
- **Uniswap V3 Celo deployment addresses (official docs):** `https://developers.uniswap.org/contracts/v3/reference/deployments/celo-deployments` — factory `0xAfE208a311B21f13EF87E33A90049fC17A7acDEc`, NonfungiblePositionManager `0x3d79EdAaBC0EaB6F08ED885C05Fc0B014290D95A`, SwapRouter02 `0x5615CDAb10dc425a742d643d949a7F474C01abc4`
- **Live Forno eth_blockNumber probe:** head block 67,854,122 at 2026-05-25
- **Uniswap V3 Swap event decoded signature:** `Swap(address indexed sender, address indexed recipient, int256 amount0, int256 amount1, uint160 sqrtPriceX96, uint128 liquidity, int24 tick)` — verified by live Blockscout v2 ABI-decoded log on cKES/USDT pool, topic0 `0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67`

### Secondary (MEDIUM confidence)

- **Graph Explorer subgraph listings:** Messari `9nh6Ums…ALYMqa` (108 signal, 3-yr-stale) and Uniswap-tagged `t3uzAbri…iq1o` (3K signal, 2-yr-stale) — verified via WebFetch against `thegraph.com/explorer`, BOTH require API key for queries
- **Blockscout v1 getLogs schema:** verified live (`status`, `result[]` with `address`, `blockNumber` hex string, `topics[]` 4 entries, `data`, `timeStamp` hex, `transactionHash`, etc.)
- **Faucets active 2026-05:** Circle (`faucet.circle.com`, 20 USDC / 2hr), Coinbase CDP (`portal.cdp.coinbase.com`), Alchemy, QuickNode, Chainlink — confirmed via WebSearch and CONTEXT.md verification trail
- **Uniswap V3 subgraph schema entities:** WebSearch evidence (multiple sources) confirms Pool has `feeGrowthGlobal0X128`/`feeGrowthGlobal1X128`; PoolDayData has the same; Position has `tickLower/tickUpper/feeGrowthInside0LastX128`. NOT directly verified against the candidate Celo deployment's `schema.graphql` (requires API key).

### Tertiary (LOW confidence — flagged for validation)

- **Schema coverage of the Messari vs Uniswap-tagged Celo subgraph at 2026-05-25 freshness:** Curation signal is years old; we cannot verify via `_meta { block }` without an API key. Phase 1 Wave 1 acquires the key and runs the freshness check.
- **Schema-frozen-check behavior on per-protocol TOML field additions:** plausibly enforces only at `_schema.toml` level, but not verified. Phase 1 plan must probe.
- **hyparquet-writer stability under repeated append-rewrite cycles:** library is pure-JS and used in production by several DeFi projects (per its npm page), but the abrigo-x402 use case (frequent small appends) is at the high-frequency end of its design envelope. Phase 1 must include a stress-test as part of the cache-idempotency test, OR fall back to JSONL.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every dep pin verified live on npm registry 2026-05-25 (Phase 0 substrate is solid).
- Architecture: HIGH — pnpm workspace pattern, ARCHITECTURE.md Pattern 2 verbatim, no novel surface.
- Blockscout v1/v2 endpoint shapes: HIGH — verified live against the actual cKES/USDT pool today.
- Uniswap V3 Celo subgraph deployment hunt: MEDIUM-LOW — candidates exist but unreachable without API key; signal is stale; downgrade path is the load-bearing default.
- x402 wire format: HIGH — multiple primary-source confirmations (Avalanche Builder Hub spec doc, x402-foundation examples, Coinbase quickstart).
- Cache key + ledger schema: HIGH — derived from CONTEXT.md decisions + standard content-addressing practice; the two-run byte-identity test pins the invariant.
- Mock 402 server design: HIGH — ~60 lines of `node:http`, validated against the spec for `X-PAYMENT-RESPONSE` header shape.
- Validation architecture: HIGH — every requirement has a vitest test command; Wave 0 gap list is concrete.

**Research date:** 2026-05-25
**Valid until:** 30 days for npm pins + Blockscout schemas (stable surfaces); 7 days for subgraph deployment status + faucet availability (moving substrate). Re-verify the subgraph hunt at Phase 1.5 enrichment if more than 7 days elapse before that wave runs.
