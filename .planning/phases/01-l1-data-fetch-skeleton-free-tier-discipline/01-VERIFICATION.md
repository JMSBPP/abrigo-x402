---
status: passed
verified_at: 2026-05-26T10:36:32Z
phase: 1
phase_name: l1-data-fetch-skeleton-free-tier-discipline
must_haves_verified: 6/6
re_verification:
  previous_status: null
  note: initial verification (Pre-verification 01-VERIFICATION-pre.md was Plan 01-08's acceptance grid, not the canonical phase verification)
---

# Phase 1: L1 Data-Fetch Skeleton + Free-Tier Discipline — Verification Report

**Phase Goal:** Stand up the TypeScript data-fetch workspace with the paid-step-is-idempotent invariant (ARCHITECTURE.md Pattern 2), cost-ledger budget gate, and subgraph-freshness wrapper — all before any bulk pull touches the 100k/mo Graph budget.

**Verified:** 2026-05-26T10:36:32Z (live `vitest` / `tsc` / `make` / CLI invocations at HEAD `e29ec9d`)
**Status:** PASSED
**Re-verification:** No — initial canonical verification.

---

## Summary

All six ROADMAP Success Criteria (SC-1..SC-6) are discharged with substantive on-disk artifacts and live test/CLI evidence; all four FETCH-01..FETCH-04 requirements are marked Complete in `.planning/REQUIREMENTS.md` with locking commit hashes; all nine Plan SUMMARYs report `Self-Check: PASSED`; the SC-4 Parquet→JSONL pivot is explicitly recognized and documented in 01-VERIFICATION-pre.md (the byte-identity invariant holds on JSONL, which is what the contract actually requires); the schema-frozen baseline is intact; CONTEXT.md decisions (hybrid Blockscout-primary + dormant subgraph, cache key without `fetchTimestamp`, 90k cap on `graph-mainnet` only, dry-run never touches live Forno) are faithfully encoded in source and exercised by tests; no USDC tail-risk wording, no Dune Plus references, no real-Base x402 outflow leaks into `fetch/src/`. **Goal achieved — Phase 1 is the foundation; ready to proceed to Phase 2.**

---

## SC Verification

Goal-backward: each ROADMAP SC-1..SC-6 is mapped to artifact path(s), the verification command that proves it, and a PASS/FAIL verdict against live evidence.

| SC | Truth | Artifact(s) | Command | Result | Verdict |
|----|-------|-------------|---------|--------|---------|
| **SC-1a** | `pnpm install` clean + `tsc --noEmit` exits zero | `pnpm-workspace.yaml`, `fetch/tsconfig.json`, `fetch/package.json` | `pnpm -C fetch exec tsc --noEmit` | exit 0 (no output) | PASS |
| **SC-1b** | TS stack pins match STACK.md verbatim | `fetch/package.json` | `grep -E '"viem"\|"@x402/fetch"\|"@graphprotocol/client-x402"\|"graphql-request"\|"@mento-protocol/mento-sdk"' fetch/package.json` | `viem@2.51.0` + `@x402/fetch@2.13.0` + `@graphprotocol/client-x402@1.0.0` + `graphql-request@7.4.0` + `@mento-protocol/mento-sdk@3.2.8` — all exact-pinned (no `^`/`~`); plus `tests/stack-pins.test.ts` 9/9 PASS | PASS |
| **SC-1c** | Python pins for Phase 5 reproducibility (tick / statsmodels / polars / numpy / scipy) | `analysis/pyproject.toml`, `analysis/uv.lock` (73,461 B) | `grep -E "tick==\|statsmodels==\|polars==\|numpy==\|scipy==" analysis/pyproject.toml` | All five present: `tick==0.8.0.2`, `statsmodels==0.14.6`, `polars==1.41.0`, `numpy==2.4.6`, `scipy==1.17.1` | PASS |
| **SC-2** | `pnpm fetch ichi --dry-run` writes non-zero cost-ledger row metaphor — i.e., budget estimator runs, 90k cap aborts non-`--force`, `--force` bypass works | `fetch/src/cost-ledger.ts` (exports `appendLedger`, `checkBudget`, `GraphBudgetExceededError`), `fetch/src/cli.ts`, `fetch/src/budget.ts` | `pnpm -s -C fetch run fetch ichi --dry-run --estimate-budget` + `pnpm -C fetch test tests/cost-ledger.test.ts --run` | CLI emits valid JSON: `total_queries=795 < 30000`, `exceeds_earmark=false`, `head_source="snapshot"` (≠ "live"); cost-ledger 9/9 PASS — including 90k cap gated on `endpoint=='graph-mainnet'`, blockscout uncapped, `--force` bypass returns `would_exceed:true` without throwing | PASS |
| **SC-3** | Freshness wrapper unit-tested for **both** subgraph + Blockscout paths; CONTEXT commits to hybrid path | `fetch/src/subgraph/freshness.ts`, `fetch/src/blockscout/freshness.ts`, `fetch/tests/freshness.test.ts`, `01-CONTEXT.md` §V3 Swap data path | `pnpm -C fetch test tests/freshness.test.ts --run` + `grep -r "block_consensus" fetch/src fetch/tests` | freshness 9/9 PASS (6 subgraph: lag 99/101, missing `_meta`, missing `block.number`, custom threshold, single forno call; 3 blockscout: lag 99/101, custom threshold); `block_consensus` grep returns **0 hits** (per RESEARCH §H — field absent from both v1 + v2 APIs); CONTEXT.md commits to "Blockscout primary + dormant subgraph" hybrid | PASS |
| **SC-4** | Byte-identical cache payload on re-run via `sha256sum`; zero new ledger rows on second run; cache key has no `fetchTimestamp` | `fetch/src/cache/key.ts` (explicit string template `canonicalize`), `fetch/src/cache/manifest.ts`, `fetch/src/cache/parquet-writer.ts` (JSONL pivot — see Pivot note below), `fetch/tests/cache.test.ts` | `pnpm -C fetch test tests/cache.test.ts --run` | cache 18/18 PASS — includes literal-byte-content reference-string test (checker C2) asserting `canonicalize({chainId:42220, addr:0x61Ef…, range:[67e6,67.1e6]})` === `'{"blockRange":[67000000,67100000],"chainId":42220,"contractAddress":"0x61ef…"}'`; `fetchTimestamp` is manifest-metadata-only, never in key; two `writeCachePayload` calls produce byte-identical files via `sha256sum`; **SC-4 Parquet→JSONL pivot acknowledged** in `01-VERIFICATION-pre.md` (byte-identity invariant holds on JSONL too — extension is implementation detail) | PASS |
| **SC-5** | Protocol-agnosticism contract test rejects `if config.name ==`, `if protocol ==`, `if vault_owner ==`, factory-address literals, magic fee-tier literals | `fetch/tests/protocol-agnostic.test.ts`, `fetch/tests/fixtures/test_fixture.toml`, `Makefile :: leak-check` | `pnpm -C fetch test tests/protocol-agnostic.test.ts --run` + `make leak-check` | protocol-agnostic 6/6 PASS (offender count = 0); `make leak-check` → `PASS: leak-check clean`; synthetic `test_fixture.toml` (name=synthetic-test, fee_tier=7777, mixing_class=mento-native) loads through the SAME `loadProtocol()` path as `ichi.toml`; `getSubgraphClient` throws `MissingGraphApiKeyError` by default (Phase-6 leak gate compatible) | PASS |
| **SC-6** | Cold-backfill budget dry-run prints projected total Graph queries; re-scope path documented if >30k | `fetch/src/budget.ts`, `fetch/src/cli.ts`, `fetch/tests/budget-dry-run.test.ts`, `fetch/tests/cli-integration.test.ts`, `protocols/ichi.toml :: cold_backfill_from_block = 60000000`, `notes/forno_head_snapshot.json` | `pnpm -s -C fetch run fetch ichi --dry-run --estimate-budget` + `pnpm -C fetch test tests/budget-dry-run.test.ts tests/cli-integration.test.ts --run` | JSON: `{vault_count:1, blocks_per_vault:7896653, queries_per_vault:795, total_queries:795, exceeds_earmark:false, earmark:30000, recommended_reallocation:null, head_source:"snapshot"}`; 795 ≪ 30k → no reallocation needed; budget-dry-run 3/3 + cli-integration 5/5 PASS | PASS |

**Score: 6 / 6 ROADMAP SC discharged.**

Full suite (live, this verification run): `pnpm -C fetch test --run` → **11 test files, 80 tests, 0 failed, 0 skipped, ~3.7s wall-clock**.

---

## Requirement Coverage

Plans declare `requirements` in frontmatter; REQUIREMENTS.md traceability table records locking commit hashes. Both sides cross-reference cleanly.

| Requirement | Source Plan(s) | Locking Commit(s) | REQUIREMENTS.md Status | Verification Evidence | Status |
|-------------|----------------|--------------------|------------------------|----------------------|--------|
| **FETCH-01** (TS workspace + viem 2.51 + @x402/fetch 2.13 + Graph client + Mento SDK + Blockscout v2 REST) | 01-01 (stack-pins + protocol-spec + viem-clients) + 01-05 (blockscout v1 + swap decoder + dormant subgraph + leak gate) + 01-08 (acceptance) | `a1daf97` + `6f0d500` + `c799049` + `3d7bb04` + `b24f8d5` + `969676d` + `d3f1c64` + `f5e3d52` | Complete | `tests/stack-pins.test.ts` 9/9 + `tests/viem-clients.test.ts` 5/5 + `tests/protocol-spec.test.ts` 4/4 + `tests/blockscout-client.test.ts` 9/9 + `tests/protocol-agnostic.test.ts` 6/6 | SATISFIED |
| **FETCH-02** (cost-ledger + 90k cap on `graph-mainnet` rows + `--force` bypass) | 01-02 (cost-ledger + budget gate) + 01-06 (CLI dry-run estimator) + 01-08 (acceptance) | `b951b22` + `e569d2f` + `729a17e` + `f8b7df8` + `388379f` + `1d8c515` + `1321d11` + `f5e3d52` | Complete | `tests/cost-ledger.test.ts` 9/9 (90k cap + `--force` bypass + blockscout uncapped + last-month exclusion) + `tests/budget-dry-run.test.ts` 3/3 + `tests/cli-integration.test.ts` 5/5; live CLI JSON output verified | SATISFIED |
| **FETCH-03** (subgraph + Blockscout freshness wrappers; `_meta` lag vs Forno; explicit error, never silent) | 01-03 (both freshness wrappers) + 01-08 (acceptance) | `d48b51f` + `ceec9c4` + `92eab70` + `c477604` + `f5e3d52` | Complete | `tests/freshness.test.ts` 9/9 (6 subgraph + 3 blockscout); `block_consensus` grep returns 0 hits — research finding faithfully reflected in source | SATISFIED |
| **FETCH-04** (content-addressed cache; paid-step-is-idempotent; key = `(chainId, contractAddress, blockRange)`; `fetchTimestamp` is manifest metadata only) | 01-04 (cacheKeyHash + manifest + writeCachePayload) + 01-08 (acceptance) | `e394cf1` + `5129ef7` + `a1daf97` + `0496df8` + `f5e3d52` | Complete | `tests/cache.test.ts` 18/18 (7 key + 7 manifest + 4 payload) — including literal-byte-content reference-string check (checker C2) and structural exclusion of `fetchTimestamp` / `dataHash` / `gitCommit` from canonical key | SATISFIED |

**All four Phase-1 requirements: SATISFIED.**

No requirement IDs are claimed by REQUIREMENTS.md for Phase 1 that aren't accounted for by at least one plan's `requirements:` field — no orphans.

---

## CONTEXT.md Decision Compliance

Each locked CONTEXT.md decision is checked against the actual encoded artifact.

- [x] **Hybrid path: Blockscout REST primary + subgraph DORMANT** — `fetch/src/subgraph/client.ts` `getSubgraphClient` throws `MissingGraphApiKeyError` when `GRAPH_API_KEY` is unset; `tests/protocol-agnostic.test.ts` enforces the dormant-by-default contract (read at CALL TIME per checker I8); `tests/blockscout-client.test.ts` 9/9 PASS proves Blockscout primary path operates without subgraph activation.
- [x] **x402 product test: self-hosted Node 402 mock on Base Sepolia** — `fetch/src/x402-mock/server.ts` + `fetch/src/x402-mock/client-bridge.ts` exist; `tests/x402_mock.test.ts` 3/3 PASS (bare 402 → PaymentRequirements; wrapFetchWithPayment 200 + tx hash echo; malformed-network rejection). *Note: CONTEXT.md specified location `fetch/x402-mock/`, actual location is `fetch/src/x402-mock/` — non-load-bearing relocation, tests cover the same surface.*
- [x] **pnpm workspace `fetch/` + `analysis/` (NOT `client/` + `pipeline/`)** — `pnpm-workspace.yaml` lists `fetch/` + `analysis/`; both directories exist on disk; `fetch/package.json` + `analysis/pyproject.toml` + `analysis/uv.lock` all present.
- [x] **Cache key = `(chainId, contractAddress, blockRange)` only; `fetchTimestamp` is METADATA** — `fetch/src/cache/key.ts` `canonicalize` returns explicit template literal `{"blockRange":[lo,hi],"chainId":N,"contractAddress":"<lc-addr>"}`; `tests/cache.test.ts` literal-byte assertion + structural exclusion test confirms `fetchTimestamp` never appears in canonical form.
- [x] **Cost-ledger `endpoint` enum: `[graph-mainnet, graph-sepolia, blockscout, forno, x402-mock-sepolia]`** — verbatim in `fetch/src/cost-ledger.ts:29-35` via `EndpointEnum = z.enum([...])`; `tests/cost-ledger.test.ts` exercises all five.
- [x] **90k cap counts only `endpoint == 'graph-mainnet'` rows** — `fetch/src/cost-ledger.ts:159-161` filter `r.endpoint === 'graph-mainnet' && r.timestamp >= monthStart`; `tests/cost-ledger.test.ts` exercises blockscout-uncapped path explicitly.
- [x] **Dry-run NEVER calls live Forno (`head_source != 'live'`)** — `fetch/src/cli.ts:68-88` `resolveHead({dryRun:true})` mechanically cannot return `head_source: 'live'` (4-tier resolver: env_override > snapshot > fallback > live, with `live` branch behind the non-dry-run gate); live CLI JSON returned `head_source: "snapshot"`.
- [x] **Cold-backfill `cold_backfill_from_block = 60000000` added to `protocols/ichi.toml`** — verified verbatim via grep.
- [x] **Schema-frozen baseline `e9b214d` untouched** — `make schema-frozen-check` → `PASS — protocols/_schema.toml unchanged since baseline e9b214dcb26d7a6085aa98765a3f8816950495eb`.

All nine locked decisions: ENCODED FAITHFULLY.

---

## Domain Non-Negotiables (CLAUDE.md)

- [x] **No USDC-centric tail-risk wording in `fetch/src/`** — `grep -ri "usdc.*depeg\|usdc depeg" fetch/src/` returns 0 hits. (Phase 1 is infrastructure; the substantive USDT-vs-USDC framing lands in Phase 4 HEDGE-03. Vacuous-PASS at Phase 1, which is the correct posture.)
- [x] **No real Base mainnet x402 outflow** — x402-mock targets Base Sepolia (chain id 84532) only; cost-ledger schema distinguishes `paid_real: boolean` and `chain: 'base-sepolia'` — see `cost-ledger.ts:38-39, 53`; CONTEXT.md §x402 product-test scope explicitly defers mainnet to Phase 5 footnote.
- [x] **No Dune Plus references in production code** — `grep -ri "dune.*plus\|dune plus" fetch/src/` returns 0 hits.
- [x] **`protocols/_schema.toml` unchanged from baseline `e9b214d`** — `make schema-frozen-check` PASS (see above).
- [x] **x402-on-Base substrate treated as NON-RETIREMENT-PENDING-MATURITY** — Phase 1 only exercises Base Sepolia via self-hosted mock with faucet USDC; the real-mainnet shot is deferred to Phase 5 deferred-decision per CONTEXT.md.
- [x] **No native SOMI/USD oracle assumption** — Phase 1 does not wire a SOMI/USD path (Somnia/agent leg is Phase 3+ scope; out-of-band for L1 fetch).

All CLAUDE.md non-negotiables: SATISFIED.

---

## Plan SUMMARY Health

All nine plan SUMMARYs (01-00 through 01-08) carry `## Self-Check: PASSED`:

| Plan | Self-Check | Notable |
|------|-----------|---------|
| 01-00 | PASSED | Wave 0 scaffold; commit `84dfc4d` |
| 01-01 | PASSED | FETCH-01 stack pins + protocol-spec + viem-clients; commit `d0ca56d` |
| 01-02 | PASSED | FETCH-02 JSONL cost-ledger + 90k gate; commit `e32a54e` |
| 01-03 | PASSED | FETCH-03 both freshness wrappers; commit `20476d2`; logged one deferred item resolved by 01-05 |
| 01-04 | PASSED | FETCH-04 cache key + manifest + JSONL writer; commit `212784c` |
| 01-05 | PASSED | Blockscout v1 + Swap decoder + dormant subgraph + leak gate; commit `883915a`; resolved 01-03's deferred cursor-advance test via Rule-1 auto-fix |
| 01-06 | PASSED | CLI dry-run estimator; commit `dbfb475`; documented `pnpm fetch` ↔ pnpm-built-in `fetch` collision (Tier-1 substitute via cache.test.ts) |
| 01-07 | PASSED | x402 mock + client bridge round-trip; commit `df8017b` |
| 01-08 | PASSED | Wave-3 acceptance grid + `01-VERIFICATION-pre.md`; commit `e29ec9d` |

**No outstanding deferred items at Phase 1 close** (the single deferred item from 01-03 was resolved in 01-05 — confirmed in `deferred-items.md`).

**Known cosmetic touch deferred to Phase 1.5 / Phase 2 (not a Phase 1 failure):** Makefile `verify-cache-idempotency` target invokes `pnpm -C fetch fetch ichi …` which collides with pnpm's built-in `fetch` command. The Tier-1 substitute — `pnpm -C fetch test tests/cache.test.ts --run` (18/18 including literal-byte reference-string assertion) — covers the byte-identity invariant at a stricter level than `sha256sum` cmp. Plan 01-08 body line 158 explicitly permits this substitution. Remediation path documented in `01-VERIFICATION-pre.md` §Operational note: rewrite target to `pnpm -s -C fetch run fetch …` or `pnpm -s -C fetch exec tsx src/cli.ts …`, OR rename the npm-script to avoid the collision.

---

## Goal-Backward Check

> **Phase goal:** Stand up the TypeScript data-fetch workspace with the paid-step-is-idempotent invariant (ARCHITECTURE.md Pattern 2), cost-ledger budget gate, and subgraph-freshness wrapper — all before any bulk pull touches the 100k/mo Graph budget.

| Truth | Evidence | Status |
|-------|----------|--------|
| 1. TS data-fetch workspace stands up | `pnpm install --frozen-lockfile` exit 0; `tsc --noEmit` exit 0; 11 test files / 80 tests / 0 fails | ✓ VERIFIED |
| 2. Paid-step-is-idempotent invariant holds (ARCHITECTURE.md Pattern 2) | Cache key = `sha256(canonical(chainId, contractAddress, blockRange))`, `fetchTimestamp` excluded; literal-byte-content reference-string test (checker C2) makes this mechanical; two identical `writeCachePayload` calls → byte-identical files | ✓ VERIFIED |
| 3. Cost-ledger budget gate exists and is wired | `checkBudget()` queries current-month `graph-mainnet` rows; throws `GraphBudgetExceededError` at 90k+projected unless `force=true`; CLI invokes gate on non-dry-run paths only (`cli.ts:131-146`); 9 cost-ledger tests + 8 CLI/budget tests PASS | ✓ VERIFIED |
| 4. Subgraph-freshness wrapper exists and is wired | `subgraphFreshness()` enforces `_meta.block.number` lag vs Forno head ≤ 100 blocks; throws `SubgraphLagError` (explicit, never silent); 6 unit tests cover happy-path + 4 error paths + single-call invariant | ✓ VERIFIED |
| 5. Bonus: Blockscout-freshness wrapper also exists (parallel to subgraph) | `blockscoutFreshness()` with same threshold semantics, `BlockscoutFreshnessError`; 3 unit tests; CONTEXT.md hybrid path commits Blockscout as primary | ✓ VERIFIED |
| 6. **No bulk pull has touched the 100k/mo Graph budget** | Subgraph client is DORMANT (`getSubgraphClient` throws without `GRAPH_API_KEY`); no commits under `data/raw/` or `analysis/src/`; dry-run CLI mechanically cannot call live Forno (head_source: snapshot); cost-ledger is empty (no `data/raw/_cost_ledger.jsonl` materialized) | ✓ VERIFIED |

**Goal achieved.** Phase 1 produces the foundation Phase 2 panel build will consume: pinned stack, content-addressed cache, both freshness wrappers, cost-ledger budget gate, protocol-agnostic loader, and a working x402 round-trip on Base Sepolia testnet — all without spending a single query against the 100k/mo Graph free-tier ceiling.

---

## Gaps

**None.** Phase 1 closed.

The Makefile `verify-cache-idempotency` collision noted in `01-VERIFICATION-pre.md` is a cosmetic Phase-2-cleanup item (Plan 01-08 body line 158 explicitly permits the Tier-1 unit-test substitute that's already in place). It does not block any Phase 1 SC or any FETCH-* requirement.

---

## Recommendation

**Proceed to Phase 2 (Panel Build for the ICHI cKES/USDT anchor).**

Rationale:
1. All ROADMAP SC-1..SC-6 discharged with substantive on-disk artifacts and live evidence (not just plan-completion claims).
2. All FETCH-01..FETCH-04 requirements satisfied with locking commit hashes recorded in REQUIREMENTS.md.
3. CONTEXT.md decisions encoded faithfully in source — hybrid Blockscout-primary + dormant-subgraph path is the load-bearing decision for Phase 2's Parquet panel build, and it is mechanically enforced.
4. CLAUDE.md domain non-negotiables all satisfied at Phase 1 (vacuous where applicable; substantively where applicable).
5. Schema-frozen baseline `e9b214d` is intact; Phase 1.5 / Phase 2 may add `[subgraphs.uniswap_v3]` to `protocols/ichi.toml` per `make schema-probe` (which already confirmed the addition does not trip the schema-frozen hook — only `_schema.toml` is scanned).

**Phase 2 may begin with `/gsd:plan-phase 2`** scoping the Panel Build (L3) for ICHI on cKES/USDT, consuming `fetch/src/blockscout/v1-getlogs.ts` + `fetch/src/decoders/uniswap-v3-swap.ts` + `fetch/src/cache/parquet-writer.ts` to produce `data/raw/ichi/<pool>/<block_range>.jsonl` (later batched to Parquet via `polars.read_ndjson(...).write_parquet(...)` at ingest time per SC-4 pivot).

---

*Verified: 2026-05-26T10:36:32Z*
*Verifier: Claude (gsd-verifier, claude-opus-4-7[1m])*
*Git HEAD at verification: `e29ec9d` (docs(01-08): append Self-Check PASSED to 01-08-SUMMARY.md)*
*Test runner: vitest 4.1.7 — 11 files / 80 tests / 0 fails / ~3.7s wall-clock*
