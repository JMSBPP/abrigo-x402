# Phase 1: L1 Data-Fetch Skeleton + Free-Tier Discipline - Context

**Gathered:** 2026-05-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Stand up the TypeScript data-fetch workspace (`fetch/`) — pinned stack, content-addressed Parquet cache, cost-ledger with per-endpoint accounting, subgraph-freshness wrapper, Blockscout-freshness wrapper, and a self-hosted Base Sepolia x402 mock endpoint — all before any Phase 2 bulk pull touches the 100k/mo Graph budget. The cost-leg "modeled, not paid" stance from PROJECT.md is partially relaxed for Phase 1: the x402 plumbing IS exercised end-to-end on Base Sepolia against a self-hosted 402 mock with faucet-funded test USDC (zero real-USD outflow) so the product (cost reduction of data consumption) has an actual round-trip validation, not just a stipulated `USD_per_query` prior.

</domain>

<decisions>
## Implementation Decisions

### V3 Swap data path (FETCH-01 + SC-3)
- **Hybrid panel construction**: Blockscout v2 REST is the **primary source-of-truth** for bulk Uniswap V3 Swap event panel on the cKES/USDT anchor pool; Uniswap V3 Celo subgraph is the **high-quality slice** used ONLY for in-range LP-fee accrual entities (saves re-implementing Q96 tick math from raw events) and ICHI vault state entities.
- **Blockscout for bulk swaps:** uses `celo.blockscout.com/api/v2/addresses/<pool>/logs?topic0=<Swap_hash>` with `fromBlock`/`toBlock` filters; keyset pagination via `next_page_params`; max 1,000 logs/page; ABI decode via viem `decodeEventLog`. At ~4,400 swaps/30d for cKES/USDT, the panel pulls in ~5 paginated requests (~2 seconds at the free 3 req/sec rate limit). No API key required for Iter-1 panel volume.
- **Subgraph for the LP-fee + vault-state slice:** typed SDK fetches `position`, `pool.feeGrowthGlobal0X128/1X128`, ICHI vault state per fetch — estimated ~200 paid queries per monthly refresh, negligible against 90k Graph cap. Steer's analogous slice would fire in Phase 6 if Phase 6 ran a Phase 1–5 cycle (it doesn't — Steer is STRADDLE memo-only null per Phase 0).
- **Both freshness wrappers ship** (REPRO-02-compatible pattern): `blockscoutFreshness({ block_consensus, lag_vs_forno })` (wired to production fetches) + `subgraphFreshness({ _meta.block.number, lag_vs_forno, 100_block_threshold })` (wired to LP-fee slice). Both unit-tested per SC-3.
- **Fallback if no Uniswap V3 Celo Decentralized Network deployment is found at acceptable quality:** the hybrid plan downgrades to **Blockscout-only**, and the LP-fee leg is computed from raw `Swap` events via Q96 tick math in `analysis/`. This downgrade is pre-registered, not Phase-2 ad-hoc.

### x402 product-test scope (NEW — partially relaxes PROJECT.md cost-leg-modeled-not-paid)
- **Self-hosted minimal Node 402-server at `fetch/x402-mock/`** — tiny HTTP server (~50 lines) that returns 402 with valid x402 v2 pricing headers and accepts a USDC tx hash on retry. Runs locally during tests + CI. Fully reproducible, no third-party dependency.
- **Wallet substrate: Base Sepolia testnet only** (chain id 84532, RPC `https://sepolia.base.org`). Test ETH via Coinbase CDP / Alchemy / QuickNode / Chainlink / Bware Labs faucets; test USDC at `0x036cbd53842c5426634e7929541ec2318f3dcf7e` via Circle Faucet (20 USDC per 2hr per address) or Coinbase CDP combined faucet.
- **Round-trip validation**: `@x402/fetch` v2.13 + `@x402/evm` v2.13 wired against the mock 402 endpoint; verifies wallet → sign EIP-712 → 402 retry → USDC transfer on Base Sepolia → tx-hash echo on `PAYMENT-RESPONSE` header.
- **Real Graph mainnet x402**: explicitly **out of scope for Phase 1**. The Graph operates NO Base Sepolia gateway (verified primary-source research 2026-05-25) — testnet x402 testing is limited to mock endpoints or non-Graph providers. Phase 5 PDF deliverable MAY include a one-shot real Graph mainnet paid query as a final product-validation footnote (deferred decision).
- **Cost-ledger entries for x402-mock**: `paid_real_usdc = false; chain = "base-sepolia"; usdc_amount = <quoted>; tx_hash = "0x..."; gateway_uri = "http://localhost:<port>/mock"`. Distinguishes from `paid_real_usdc = true` for any future real-mainnet shot.

### Workspace layout (FETCH-01 + SC-1)
- **pnpm workspace** rooted at repo root with `pnpm-workspace.yaml` listing `fetch/` (and a placeholder for `analysis/` which Phase 2 will populate with `pyproject.toml` + `uv.lock`). `contracts/` deferred to Iteration 3+.
- **Root `package.json`** carries the workspace declaration + dev-tools (biome, vitest, tsx, @types/node). The existing root `package.json` (which has the two Graph deps installed by hand-prototyping) gets re-scoped: Graph deps move into `fetch/package.json`; root keeps only workspace meta + shared dev-tools.
- **Directory names: `fetch/` + `analysis/`** (matches ROADMAP.md SC paths verbatim, supersedes STACK.md's `client/` + `pipeline/` naming).
- **Pinned versions per FETCH-01 / STACK.md** in `fetch/package.json`: `viem@2.51.0`, `@x402/fetch@2.13.0`, `@x402/evm@2.13.0`, `@x402/core@2.13.0`, `@graphprotocol/client-x402@1.0.0`, `@graphprotocol/client-cli@3.0.7` (build-only), `graphql-request@7.4.0`, `@mento-protocol/mento-sdk@3.2.8`, `zod@4.4.3`, `dotenv@16.x`, `viem/chains` provides `celo` + `baseSepolia`.
- **`analysis/uv.lock` pinned at Phase 1 (NOT deferred to Phase 5)** per ROADMAP Phase 1 SC-1: `tick==0.8.0.2`, `statsmodels==0.14.6`, `polars==1.41.0`, `numpy==2.4.6`, `scipy==1.17.1`. Phase 2's `pyproject.toml` is created here too (empty src layout, dependencies pinned), even though no Python code lands until Phase 2.

### Cache key idempotency (FETCH-04)
- **Cache key: `(chainId, contractAddress, blockRange)`** — `fetchTimestamp` is **NOT** part of the key. Re-running the same fetch is a cache hit with zero new cost-ledger rows. Byte-identical Parquet output verified via `sha256sum` per SC-4.
- **`fetchTimestamp` logged as metadata** in `data/raw/<protocol>/manifest.json` alongside `cache_key_hash`, `dataHash` (sha256 of the Parquet content), `gitCommit`, `endpoint`, `query_count`, `usdc_cost`, `paid_real`.
- **Honors FETCH-04's paid-step-is-idempotent invariant**: re-running with identical `(chainId, contractAddress, blockRange)` must produce byte-identical Parquet and zero new ledger rows.

### Cost-ledger schema (FETCH-02)
- **Per-endpoint columns** for downstream demand-window analytics: `{timestamp, endpoint, query_id, cost_usdc, paid_real, tx_hash?, chain?, response_bytes, response_sha256, fetch_id}`.
- **`endpoint` enum**: `["graph-mainnet", "graph-sepolia", "blockscout", "forno", "x402-mock-sepolia"]`. The 90k/mo soft cap counts only `endpoint == "graph-mainnet"` rows (Graph paid + Graph free-tier collapsed into one bucket since both burn the 100k/mo allowance). Blockscout / Forno / x402-mock-sepolia rows are logged but uncapped.
- **`--force` override** bypasses the 90k abort. Required for any fetch that would push cumulative monthly Graph spend above 90k.
- **Storage**: `data/raw/manifest.json` (per-fetch manifest summarizing the run) + `data/raw/_cost_ledger.parquet` (append-only ledger). Both content-addressed.

### Uniswap V3 Celo subgraph deployment hunt
- **Phase 1 researcher agent** (spawned by `/gsd:plan-phase 1`) MUST hunt the Decentralized Network for a maintained Uniswap V3 Celo subgraph:
  - Verify it covers chain id 42220 and includes cKES/USDT + cCOP/USDT pools
  - Verify indexer count ≥ 1 (preferably ≥ 3) and typical `_meta.block.number` lag < 100 blocks vs Forno head
  - Commit the deployment ID (Qm... hash or `subgraphs/id/...` URL) to `protocols/ichi.toml [subgraphs.uniswap_v3] deployment_id = "..."; verified_at_phase_1_commit = "..."`
- **If no acceptable deployment is found**: hybrid plan downgrades to **Blockscout-only**; LP-fee leg computed from raw events via Q96 tick math in `analysis/` from Phase 2 onwards. The downgrade is pre-registered in this CONTEXT, not Phase-2 ad-hoc.

### Subgraph-query side: Mento broker rates + ICHI vault state
- **Mento broker rates**: queried via `@mento-protocol/mento-sdk` at event-block (Phase 2 panel snap); no Graph paid budget needed.
- **ICHI vault state**: typed entities pulled from the same Uniswap V3 Celo subgraph slice OR ICHI's own subgraph if one exists (researcher to verify both). Tracked in `protocols/ichi.toml [subgraphs]` block.

### Claude's Discretion
- **HTTP retry policy** (network errors vs 402 vs 500): exponential backoff, max 3 retries on transient failures; 402 retried per @x402/fetch defaults.
- **viem chain config** for `celo` (id 42220, RPC `https://forno.celo.org`) and `baseSepolia` (id 84532, RPC `https://sepolia.base.org`).
- **vitest setup**: standard ESM, `vitest run` for CI, no watch mode in CI; coverage via `@vitest/coverage-v8` if requested.
- **biome config**: STACK.md defaults; rules tuned only if false positives surface in fetch/.
- **`.env` policy**: `.env.example` committed (no secrets); `.env` in `.gitignore`; `PRIVATE_KEY` for Base Sepolia faucet wallet documented as test-only in `.env.example`.
- **Forno keeper-polling explicitly out of cost-ledger** (per DEMAND-01 demand-window definition); free at any volume; not counted.
- **Cold-backfill budget allocation** (FETCH-02 SC-6): proposed at /gsd:plan-phase 1 time based on Phase 1 researcher's subgraph audit. Default budget envelope: 30k cold-backfill (Iter-1 first pull) + 15k incremental (monthly refresh) + remaining 45k reserve. Re-allocated if researcher finds the subgraph slice costs more than predicted.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase-0 governance carried forward
- `.planning/phases/00-candidate-eligibility-pre-registration/00-CONTEXT.md` — all locked Phase-0 decisions (Q-4, Q-7, Q-9, REPRO-03 two-tier, COPM v2-deferred, pre-reg priors)
- `notes/PRE_REGISTRATION.md` — kernel forms, priors, acceptance regions, decision rules
- `notes/PHASE_0_GATE.md` — ICHI PASS verbatim; Steer STRADDLE verdict (Iter-2 fires HEDGE-05 memo-only null at Phase 0; Phases 1–5 cycle is ICHI-only)
- `notes/Q9_DECISION.md` — V3-anchor-only primary + V3+V4+Broker unified fallback (Iter-2 only; not relevant for Iter-1 cKES panel)
- `protocols/_schema.toml` — frozen baseline at commit `e9b214d`; schema for `[subgraphs.*]` block must be defined here (or extension confirmed before Phase 1 wires subgraph queries — verify `subgraphs` enum/field is present; if not, plan a Phase-0-style schema increment via the schema-frozen check)
- `protocols/ichi.toml` — Phase 1 researcher adds `[subgraphs.uniswap_v3]` block after deployment hunt

### Project-level
- `.planning/PROJECT.md` — free-tier-only constraint; cost-leg-modeled stance (relaxed to "modeled + Sepolia mock plumbing" per Phase 1 decision); domain non-negotiables
- `.planning/REQUIREMENTS.md` — FETCH-01..FETCH-04 acceptance criteria
- `.planning/ROADMAP.md` — Phase 1 §Phase Details: 6 verbatim success criteria SC-1..SC-6

### Research substrate
- `.planning/research/STACK.md` — pinned versions, dependency rationale, x402 substrate caveats (no Celo facilitator), pnpm workspace layout
- `.planning/research/ARCHITECTURE.md` — L1 pattern (paid-step-is-idempotent), L2 cache hygiene
- `.planning/research/PITFALLS.md` — §2 subgraph silent lag (freshness wrapper), §9 free-tier exhaustion (cost-ledger gate)
- `.planning/research/CANDIDATES.md` — ICHI/Steer addresses, Phase-0 Blockscout enumeration proof-of-concept

### x402 + Base Sepolia external references
- The Graph `@graphprotocol/client-x402` 1.0.0 (published 2026-04-14) — `npmjs.com/package/@graphprotocol/client-x402` — settles on Base mainnet ONLY; NO Sepolia gateway exists for The Graph
- `@x402/fetch` 2.13.0 + `@x402/evm` 2.13.0 — `npmjs.com/package/@x402/fetch` — Base Sepolia (chain id 84532) supported via standard viem chain config
- Base Sepolia USDC contract: `0x036cbd53842c5426634e7929541ec2318f3dcf7e` (verified via `sepolia.basescan.org`)
- Faucets (verified active 2026-05): Coinbase CDP (portal.cdp.coinbase.com), Alchemy (alchemy.com/faucets/base-sepolia), QuickNode (faucet.quicknode.com/base/sepolia), Chainlink (faucets.chain.link/base-sepolia), Circle test USDC (faucet.circle.com)
- Blockscout v2 REST docs: `docs.blockscout.com/devs/apis/rest` — keyset pagination via `next_page_params`; default 3 req/sec free, 10 req/sec with free email-signup API key
- Coinbase x402 quickstart: `docs.cdp.coinbase.com/x402/quickstart-for-buyers` (alternative mock endpoint if the self-hosted mock is judged insufficient)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Phase-0 governance artifacts**: PRE_REGISTRATION.md priors (`rate_per_event`, `USD_per_query`, LR α, η floor) are the source of truth for cost-ledger interpretation
- **`protocols/_schema.toml`** (frozen baseline at `e9b214d`): defines `[protocol.vaults.<id>]` shape that ichi.toml uses; the `[subgraphs.<provider>]` block schema may need a Phase-0-style schema increment if not already specified there
- **`protocols/ichi.toml`**: existing vault enumeration is the panel-source-of-truth; Phase 1 adds `[subgraphs.*]` blocks after the researcher hunt
- **Pre-commit hooks (active)**: af_lint.sh + review_trail.sh + schema_frozen.sh — Phase 1 commits must respect them
- **Existing root `package.json`**: has `@graphprotocol/client-cli@^3.0.7` + `@graphprotocol/client-x402@^1.0.0` installed (hand-prototyping). Phase 1 re-scopes these into `fetch/package.json` after pnpm-workspace bootstrap

### Established Patterns
- **Git fork/upstream pattern from CLAUDE.md**: `origin = JMSBPP/abrigo-x402` (push target), `upstream = wvs-finance/abrigo-x402` (PR target); all Phase 1 commits go to `origin`
- **Atomic commits with phase-plan scope**: e.g. `feat(01-NN): ...` or `test(01-NN): ...`; reviewed by 2-way review-trail hook if touching PLAN.md/ROADMAP.md
- **Two-way plan review pattern**: Reality Checker + Code Reviewer in parallel before PLAN.md commits land; review files at `.planning/_reviews/01-NN-PLAN_{reality_checker,code_reviewer}.md`
- **AF-10 fixture permanent-active workflow**: per-commit temp-park OR `--no-verify` for restore (documented in Phase 0 SUMMARY 00-07)

### Integration Points
- **`fetch/` package** is the L1 layer per ARCHITECTURE.md; produces Parquet files under `data/raw/<protocol>/<pool>/<block_range>.parquet` consumed by Phase 2's `analysis/` ingest
- **`data/raw/manifest.json`** + **`data/raw/_cost_ledger.parquet`** are the artifacts every downstream phase reads to verify provenance (PANEL-02 metadata header requirement)
- **`fetch/x402-mock/server.ts`** is exercised by `fetch/tests/x402_mock.test.ts` during the CI test run; not deployed anywhere outside tests
- **`Makefile`** (committed in Phase 0) adds Phase 1 targets: `fetch-ichi`, `lint-artifacts`, `verify-cache-idempotency` (FETCH-04 sha256 check)
- **`.env.example`** added at repo root listing required env vars: `PRIVATE_KEY` (Base Sepolia test wallet), `CELO_RPC_URL` (defaults to forno.celo.org), `BASE_SEPOLIA_RPC_URL` (defaults to sepolia.base.org), `BLOCKSCOUT_API_KEY` (optional, free email signup)

</code_context>

<specifics>
## Specific Ideas

- "The product being tested IS cost reduction of data consumption." Phase 1 must exercise x402 plumbing end-to-end, not just stub it — even if only against a self-hosted mock on Base Sepolia. The `USD_per_query` prior (Phase 0 PRE_REGISTRATION.md, $5e-6) remains the headline estimate, but Phase 1 lands a real round-trip that validates the wallet/sign/retry/settle flow against a representative payload.
- "Practical now, paid later" — Blockscout for the bulk panel (free, fast, sufficient at Iter-1 volume), subgraph for the high-quality LP-fee + vault-state slice. The hybrid choice is *not* a hedge — Blockscout is the source-of-truth for the panel; the subgraph saves reimplementing Q96 tick math that doesn't add empirical value.
- "Faucet-funded, not real-USDC" — Base Sepolia is the substrate for x402 plumbing validation; mainnet Base x402 is reserved for the Phase 5 PDF deliverable's product-validation footnote (deferred decision).
- Phase 1 researcher hunting the Uniswap V3 Celo subgraph deployment ID is a Phase 1 substrate audit — if no acceptable deployment exists, the hybrid plan downgrades to Blockscout-only without re-planning; the downgrade is pre-registered here, not Phase-2 ad-hoc.

</specifics>

<deferred>
## Deferred Ideas

- **Real Graph mainnet x402 paid query** ($0.001–0.005 USDC one-shot from a real Base mainnet wallet) — deferred to Phase 5 PDF deliverable as a product-validation footnote. Decision: include or skip lives in `notes/PRE_REGISTRATION.md`'s deferred-substrate section.
- **Steer subgraph slice** — Steer Iter-2 is structurally pre-disqualified at Phase 0 (STRADDLE → memo-only null), so the analogous Steer LP-fee subgraph slice never runs in v1. Preserved as future-iteration substrate (v2 if Steer's Celo TVL grows).
- **Q96 tick-math implementation in analysis/** — fires only as the fallback path if the Uniswap V3 Celo subgraph deployment hunt fails. Not implemented unless the binding constraint triggers.
- **Mainnet x402 test on Base** — covered above as Phase 5 footnote candidate.
- **Blockscout Pro/paid tier** — not needed for Iter-1 panel; free tier handles 4,400-event monthly pull in seconds. Defer Pro evaluation to a future iteration that pushes Blockscout volume well beyond 10 req/sec.
- **TS contracts/ workspace** — Iteration 3+ when deployed Solidity hedge contracts enter scope.
- **`contracts/` directory entry in pnpm-workspace.yaml** — Iteration 3+.

</deferred>

---

*Phase: 01-l1-data-fetch-skeleton-free-tier-discipline*
*Context gathered: 2026-05-25*
