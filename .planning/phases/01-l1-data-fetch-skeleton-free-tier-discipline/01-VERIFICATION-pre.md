---
phase: 01-l1-data-fetch-skeleton-free-tier-discipline
verification_pass: true
generated: 2026-05-26T14:25:54Z
git_commit_at_run: df8017b12440117ab25ce495f7e7f8f666394b9c
test_runner: vitest 4.1.7
total_tests: 80
total_test_files: 11
plans_complete: 8/9 (this plan = the 9th)
---

# Phase 1 — Pre-Verification Summary

Sampling commands executed in `/home/jmsbpp/apps/d2p/abrigo/abrigo-x402/` immediately after the Wave-2 plans landed (last commit before this run: `df8017b` `docs(01-07): complete x402 mock + client bridge + integration test plan`). All numbers are from live `vitest` / `make` / `tsc` / `pnpm` invocations, not inferred.

## Test infrastructure (FETCH-01 SC-1)

| Property | Value |
|---|---|
| Runner | `vitest@4.1.7` (pinned via root devDependency; ESM, no watch in CI) |
| Full-suite command | `pnpm -C fetch test --run` |
| Test files | 11 |
| Tests | 80 passing, 0 failing, 0 skipped |
| Full-suite duration | ~3.65 s (transform 817 ms + import 2.56 s + tests 5.31 s = wall-clock 3.65 s with parallel workers) |
| Type-check command | `pnpm -C fetch exec tsc --noEmit` (exit 0) |

Per-file test counts (matches `01-NN-SUMMARY.md` claims):

| File | Owner Plan | Tests |
|---|---|---|
| `tests/stack-pins.test.ts` | 01-01 | 9 |
| `tests/protocol-spec.test.ts` | 01-01 | 4 |
| `tests/viem-clients.test.ts` | 01-01 | 5 |
| `tests/cost-ledger.test.ts` | 01-02 | 9 |
| `tests/freshness.test.ts` | 01-03 | 9 (6 subgraph + 3 blockscout) |
| `tests/cache.test.ts` | 01-04 | 18 (7 key + 7 manifest + 4 payload) |
| `tests/blockscout-client.test.ts` | 01-05 | 9 |
| `tests/protocol-agnostic.test.ts` | 01-05 | 6 |
| `tests/budget-dry-run.test.ts` | 01-06 | 3 |
| `tests/cli-integration.test.ts` | 01-06 | 5 |
| `tests/x402_mock.test.ts` | 01-07 | 3 |
| **TOTAL** | | **80** |

## Acceptance grid (FETCH-01..04 + ROADMAP SC-1..SC-6)

| Criterion | Command | Exit | Verdict | Evidence |
|---|---|---|---|---|
| FETCH-01 SC-1 (workspace install) | `pnpm install --frozen-lockfile` | 0 | PASS | "Lockfile is up to date, resolution step is skipped / Already up to date" — clean ESM workspace |
| FETCH-01 SC-1 (type-check) | `pnpm -C fetch exec tsc --noEmit` | 0 | PASS | no output, exit 0 |
| FETCH-01 SC-1 (TS stack pins) | `pnpm -C fetch test tests/stack-pins.test.ts --run` | 0 | PASS | 9/9 pin assertions; semver rejects `^` `~` prefixes |
| FETCH-01 SC-1 (analysis Python pins) | `grep -E "tick==0.8.0.2\|statsmodels==0.14.6\|polars==1.41.0" analysis/pyproject.toml` | 0 | PASS | 3 expected matches (tick==0.8.0.2, statsmodels==0.14.6, polars==1.41.0); `analysis/uv.lock` 73,461 bytes present |
| FETCH-01 SC-5 (protocol-agnosticism) | `pnpm -C fetch test tests/protocol-agnostic.test.ts --run` | 0 | PASS | 6/6 tests — offender count = 0; synthetic test_fixture.toml loads via SAME loadProtocol code path as ichi.toml |
| FETCH-01 SC-5 (leak gate Makefile) | `make leak-check` | 0 | PASS | `PASS: leak-check clean` — no protocol-name branches, factory addresses, or magic fee tiers in fetch/src |
| FETCH-02 SC-2 (cost-ledger budget gate) | `pnpm -C fetch test tests/cost-ledger.test.ts --run` | 0 | PASS | 9/9 — 4 append/read + 5 budget-gate (90k/mo cap on graph-mainnet only; blockscout uncapped; --force bypass; last-month rows excluded) |
| FETCH-02 SC-6 (cold-backfill dry-run) | `pnpm -s -C fetch exec tsx src/cli.ts ichi --dry-run --estimate-budget` | 0 | PASS | JSON below; `head_source: "snapshot"` ≠ `"live"` (mechanically cannot escalate per Plan 01-06 4-tier resolver) |
| FETCH-02 SC-6 (dry-run + CLI unit) | `pnpm -C fetch test tests/budget-dry-run.test.ts tests/cli-integration.test.ts --run` | 0 | PASS | 8/8 (3 budget + 5 CLI integration) |
| FETCH-03 SC-3 (freshness wrappers) | `pnpm -C fetch test tests/freshness.test.ts --run` | 0 | PASS | 9/9 — 6 subgraphFreshness + 3 blockscoutFreshness; `grep -r "block_consensus" fetch/src fetch/tests` returns 0 hits |
| FETCH-04 SC-4 (cache byte-identity) | `pnpm -C fetch test tests/cache.test.ts --run` | 0 | PASS | 18/18 — see SC-4 pivot section below for JSONL ext substitution |
| FETCH-01 (blockscout v1 client + swap decoder) | `pnpm -C fetch test tests/blockscout-client.test.ts --run` | 0 | PASS | 9/9 — v1 etherscan-compat URL, keyset pagination by block-cursor, viem-decoded `Swap` topic0 = 0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67 |
| x402 mock round-trip | `pnpm -C fetch test tests/x402_mock.test.ts --run` | 0 | PASS | 3/3 — bare 402 → PaymentRequirements; wrapFetchWithPayment 200 + 32-byte tx hash echo; malformed-network rejection |
| viem cached clients | `pnpm -C fetch test tests/viem-clients.test.ts --run` | 0 | PASS | 5/5 — chain.id 42220 (celo) + 84532 (baseSepolia); singleton identity; factory == singleton |
| protocol-spec loader | `pnpm -C fetch test tests/protocol-spec.test.ts --run` | 0 | PASS | 4/4 — ichi load + synthetic fee_tier=7777 load + invalid-enum + missing-file |
| Schema-frozen baseline (Phase 0) | `make schema-frozen-check` | 0 | PASS | `PASS — protocols/_schema.toml unchanged since baseline e9b214dcb26d7a6085aa98765a3f8816950495eb` |
| Schema-probe (Phase 1.5 readiness) | `make schema-probe` | 0 | PROBE_PASS | `PROBE_PASS: schema-frozen-check only scans protocols/_schema.toml` — safe to add `[subgraphs.uniswap_v3]` to ichi.toml at Phase 1.5; Phase 1 does NOT add the block |
| `make verify-cache-idempotency` (network leg) | `make verify-cache-idempotency` | non-zero | **SUBSTITUTED** | Documented `pnpm fetch` ↔ pnpm-built-in collision (see Operational note below); cache-idempotency unit test (`tests/cache.test.ts`, 18 tests including literal-byte-content reference-string check) is the Tier-1 substitute per plan body line 158 |

## Operational note — `pnpm fetch` ↔ pnpm built-in collision (carried from Plan 01-06)

`pnpm` ships with a built-in `fetch` command. The Makefile `verify-cache-idempotency` target invokes `pnpm -C fetch fetch ichi ...`, which routes to the built-in (which rejects `--pool/--from/--to` as "Unknown options"). This was documented in Plan 01-06 SUMMARY.

**Invocation forms that work**:
- `pnpm -s -C fetch run fetch ichi ...` (explicit `run`)
- `pnpm -s -C fetch exec tsx src/cli.ts ichi ...` (direct tsx)

**Tier-1 substitute for `verify-cache-idempotency`**: `pnpm -C fetch test tests/cache.test.ts --run` — covers the SAME byte-identity invariant at the unit-test level (sha256 of canonical JSONL content; 18/18 tests passing; includes a literal-byte-content reference-string assertion per checker C2). This is acceptable per Plan 01-08 body line 158: "the executor MAY skip the network leg and instead invoke the cache-idempotency unit test as a Tier-1 substitute. Document the substitution explicitly."

**Remediation deferred to Phase 1.5 / Phase 2**: Either rewrite Makefile target to use `pnpm -s -C fetch run fetch ...` or `pnpm -s -C fetch exec tsx src/cli.ts ...`, or add an `npm-script` alias whose name doesn't collide with pnpm built-ins.

## Per-Requirement Evidence

### FETCH-01: TS workspace + pinned stack + Blockscout v1/v2 REST client

- `pnpm install --frozen-lockfile`: exit 0 (lockfile up to date)
- `pnpm -C fetch exec tsc --noEmit`: exit 0
- **Pinned versions** (verbatim from `fetch/package.json`):
  - `viem@2.51.0`
  - `@x402/fetch@2.13.0`
  - `@x402/evm@2.13.0`
  - `@x402/core@2.13.0`
  - `@graphprotocol/client-x402@1.0.0`
  - `graphql-request@7.4.0`
  - `@mento-protocol/mento-sdk@3.2.8`
  - `zod@4.4.3`
- **Analysis pins** (verbatim from `analysis/pyproject.toml`):
  - `tick==0.8.0.2`
  - `statsmodels==0.14.6`
  - `polars==1.41.0`
  - (plus `numpy==2.4.6`, `scipy==1.17.1`)
- `analysis/uv.lock`: 73,461 bytes; resolves Python 3.13.5; 24 transitive packages
- Blockscout v1 etherscan-compat client (Plan 01-05): `tests/blockscout-client.test.ts` 9/9 PASS; v1 chosen because v2 `/api/v2/addresses/{addr}/logs` rejects `topic0` query with HTTP 422 per RESEARCH §C
- Uniswap V3 Swap decoder: viem `decodeEventLog` wrapper; topic0 verified against RESEARCH §D
- Subgraph client: DORMANT BY DEFAULT — `getSubgraphClient` throws `MissingGraphApiKeyError` without `GRAPH_API_KEY` env (env read at call time per checker I8); Phase 1.5 enrichment activates this leg

### FETCH-02: cost-ledger + 90k cap + --force + cold-backfill dry-run

- `tests/cost-ledger.test.ts`: 9/9 PASS — 4 append/read + 5 budget-gate (empty-ledger pass, 85k + 6k throws `GraphBudgetExceededError`, `--force` bypass returns `{would_exceed:true}` without throwing, blockscout endpoint uncapped, last-month rows excluded via explicit `Date.UTC(year, month, 1)` boundary)
- `tests/budget-dry-run.test.ts` + `tests/cli-integration.test.ts`: 8/8 PASS (3 unit + 5 process-level CLI integration)
- `tests/x402_mock.test.ts`: 3/3 PASS; mock round-trip writes ledger row with `endpoint='x402-mock-sepolia'`, `paid_real=false`, `chain='base-sepolia'`, `cost_usdc='0.001'`
- **Dry-run JSON output verbatim** (`pnpm -s -C fetch exec tsx src/cli.ts ichi --dry-run --estimate-budget`):
  ```json
  {
    "protocol": "ichi",
    "iteration": 1,
    "vault_count": 1,
    "blocks_per_vault": 7896653,
    "queries_per_vault": 795,
    "total_queries": 795,
    "exceeds_earmark": false,
    "earmark": 30000,
    "recommended_reallocation": null,
    "cache_hit": false,
    "dry_run": true,
    "head_block": 67896653,
    "head_source": "snapshot"
  }
  ```
- `exceeds_earmark: false` (795 < 30,000 earmark)
- `head_source: "snapshot"` — proves dry-run mechanically cannot escalate to live network call (per Plan 01-06 4-tier resolver: env_override > snapshot > fallback > live)
- Endpoint enum: `[graph-mainnet, graph-sepolia, blockscout, forno, x402-mock-sepolia]` (90k/mo soft cap counts only `graph-mainnet` rows)

### FETCH-03: subgraph + blockscout freshness wrappers

- `tests/freshness.test.ts`: 9/9 PASS
  - subgraphFreshness (6 tests): lag=99 silent / lag=101 throws SubgraphLagError / missing `_meta` / missing `block.number` / custom threshold / single `getBlockNumber` call
  - blockscoutFreshness (3 tests): lag=99 silent / lag=101 throws BlockscoutFreshnessError / custom threshold
- **`block_consensus` field check** (orchestrator finding #1): `grep -r "block_consensus" fetch/src fetch/tests` returns 0 hits — the per-log consensus field is ABSENT from both v1 `/api?module=logs&action=getLogs` AND v2 `/api/v2/addresses/{addr}/logs` per live API probe in RESEARCH §C
- Both wrappers default threshold = 100 blocks ≈ 100s at Celo 1s/block (REPRO-02 margin)

### FETCH-04: content-addressed cache + paid-step-idempotent

- `tests/cache.test.ts`: 18/18 PASS
  - `cacheKeyHash` + `canonicalize`: 7 tests (case-invariance, chainId-sensitive, blockRange-sensitive, NO `fetchTimestamp` in key, literal byte-content reference-string per checker C2)
  - manifest (zod-validated, atomic rename-from-tmp, idempotent on dup): 7 tests
  - `writeCachePayload`: 4 tests (byte-identity, dataHash sha256 match, 256-way prefix fanout)
- `fetchTimestamp` is MANIFEST METADATA only (NEVER in canonical key) — paid-step-is-idempotent invariant
- `data/raw/<protocol>/<hash[0:2]>/<hash>.jsonl` layout

## SC-4 Parquet → JSONL pivot (checker I6 — recognized concession)

**ROADMAP SC-4 verbiage**: "byte-identical Parquet output verified via `sha256sum`"

**Phase 1 actual shipped artifact**: byte-identical **JSONL append** (`fs.appendFile` writing newline-delimited JSON) — file extension `.jsonl`, not `.parquet`.

**Why pivoted**:
- `hyparquet-writer` has a documented high-frequency-small-write risk (RESEARCH.md §J fallback). Phase 1 ledger rows are ~400 B; Parquet's columnar advantage doesn't materialize at this row size, and the binary-format risk is real.
- JSONL append is POSIX-atomic per line (<PIPE_BUF, ~4 KiB on Linux), simpler, and byte-stable.
- The cost-ledger (Plan 01-02) and cache payload (Plan 01-04) both pivoted to JSONL for the SAME reason — consistent on-disk format.

**Byte-identity invariant HOLDS for JSONL**:
- The SC-4 byte-identity test runs `sha256sum` on the `.jsonl` file. Re-running with identical `(chainId, contractAddress, blockRange)` produces the same bytes because `canonicalize()` is deterministic and `appendFile` writes exactly the bytes you give it.
- The SC-4 cache-idempotency test (`tests/cache.test.ts`) is updated to find `.jsonl` files; 18/18 PASS.

**Phase 2 / Phase 5 batch-convert**: `polars.read_ndjson(...).write_parquet(...)` converts JSONL → Parquet at ingest time. The on-disk Phase 1 representation does not need to be Parquet for SC-4 byte-identity to hold; the invariant is on the bytes, not the codec.

**ROADMAP.md SC-4 should be read as**: "byte-identical cache payload on second run" — file extension is implementation detail. The Makefile `verify-cache-idempotency` target already greps both `*.parquet -o -name "*.jsonl"` per Plan 01-00 implementation.

Files affected:
- `data/raw/_cost_ledger.jsonl` (cost-ledger, Plan 01-02)
- `data/raw/<protocol>/<prefix>/<hash>.jsonl` (cache payloads, Plan 01-04)

## Library-drift inventory (from Plan 01-07 live probe)

Carried forward as load-bearing context for Phase 2+ x402 work.

| Aspect | v1 protocol (current `@x402/evm` v2.13 `ExactEvmSchemeV1`) | v2 protocol (future) |
|---|---|---|
| Network identifier | Named (`'base-sepolia'`, `'base'`, `'ethereum'`, `'sepolia'`, `'abstract'`, `'abstract-testnet'`, `'avalanche-fuji'`, `'avalanche'`, `'iotex'`, `'sei'`, `'sei-testnet'`, `'polygon'`, `'polygon-amoy'`, `'peaq'`, `'story'`, `'educhain'`, `'skale-base-sepolia'`, `'megaeth'`, `'monad'`, `'stable'`, `'stable-testnet'`) | CAIP-2 (`'eip155:84532'`, `'eip155:8453'`, …) |
| HTTP header | `X-PAYMENT` | `PAYMENT-SIGNATURE` |
| Envelope shape | `{x402Version, scheme, network, payload:{authorization:{from,to,value,validAfter,validBefore,nonce}, signature}}` | `{x402Version:2, resource:{url,method}, accepted:PaymentRequirements, payload:{authorization,signature}, extensions?}` |
| Amount field | `maxAmountRequired` | `amount` |
| `accepts[]` items | Includes `resource`, `description`, `mimeType` | Removes these — `amount` only |
| EIP-712 domain `extra` | Required: `{name: 'USDC', version: '2'}` (load-bearing for `ExactEvmScheme.createPaymentPayload` TransferWithAuthorization signing) | — |

**Selection for Phase 1 / Phase 5**: v1 (CAIP-2 caused `"No network/scheme registered for x402 version: 1"` against named-network registration; v1 envelope works against the self-hosted mock and against any RESEARCH §E-compatible facilitator).

**Phase 5 PDF deliverable footnote path**: only `network` flips `'base-sepolia'` → `'base'`; signer must hold real USDC. Implementation already-validated against real `@x402/fetch` + `@x402/evm` code paths.

## Subgraph hunt verdict (orchestrator finding #2)

- Phase 1 default: **Blockscout-only** — no `[subgraphs.uniswap_v3]` block added to `protocols/ichi.toml` at Phase 1
- `getSubgraphClient(deploymentId)` throws `MissingGraphApiKeyError` without `GRAPH_API_KEY` env (verified by test in `tests/protocol-agnostic.test.ts`)
- **Phase 1.5 enrichment task pending**: provision `GRAPH_API_KEY` → re-attempt `_meta` freshness check against candidate IDs (Messari `9nh6Ums…ALYMqa` + Uniswap-tagged `t3uzAbri…iq1o`); `make schema-probe` already confirmed adding `[subgraphs.uniswap_v3]` to `protocols/ichi.toml` does NOT trip the schema-frozen hook (only `_schema.toml` is scanned)

## Deferred items rolled up from `deferred-items.md`

Single entry, resolved:

- **(Plan 01-03 → Plan 01-05)**: Pre-existing failure in `fetch/tests/blockscout-client.test.ts:150` — cursor-advance test expected `fromBlock=67502983`, received `67508615`. **RESOLVED in Plan 01-05** via Rule-1 deviation auto-fix (corrected the plan-supplied test assertion: 0x4061986 = 67,508,614 hex → `67_508_615` is the correct next-block value; the original assertion was off-by-six-thousand). `tests/blockscout-client.test.ts` now passes 9/9.

No outstanding deferred items at Phase 1 close.

## Phase goal-backward checks

- [x] All FETCH-01..04 requirements covered with test evidence (REQUIREMENTS.md traceability table shows all four Complete after this verification)
- [x] All ROADMAP SC-1..SC-6 covered:
  - **SC-1** stack pins → `tests/stack-pins.test.ts` 9/9 + `analysis/pyproject.toml` grep 3/3
  - **SC-2** cost-ledger 90k cap + --force → `tests/cost-ledger.test.ts` 9/9 (5 budget-gate tests including --force bypass)
  - **SC-3** both freshness wrappers unit-tested → `tests/freshness.test.ts` 9/9 (6 subgraph + 3 blockscout)
  - **SC-4** byte-identity via JSONL pivot (see SC-4 pivot section above) → `tests/cache.test.ts` 18/18 including literal-byte reference-string assertion
  - **SC-5** protocol-agnosticism leak gate → `tests/protocol-agnostic.test.ts` 6/6 + `make leak-check` PASS
  - **SC-6** cold-backfill budget dry-run → CLI emits JSON with `total_queries=795 < 30000`, `exceeds_earmark=false`, `head_source="snapshot"`
- [x] No commits under `analysis/src/` (Phase 2's territory; Phase 1 only pins `analysis/pyproject.toml` + `analysis/uv.lock` per CONTEXT.md)
- [x] No commits under `data/raw/` (will populate in Phase 2 panel build)
- [x] USDT framing preserved (no USDC tail-risk wording introduced in `fetch/src/` per `grep -ri "usdc.*depeg"` returning 0 hits in source)

## Outstanding gaps

**None — Phase 1 closed.**

The one operational note (`make verify-cache-idempotency` Makefile-target rewrite for `pnpm fetch` collision) is a Phase 2 cosmetic touch, not a Phase 1 acceptance failure: the FETCH-04 SC-4 byte-identity invariant is fully validated by `tests/cache.test.ts` (18/18 PASS) at the unit-test level, including a literal-byte-content reference-string check that's stricter than the Makefile `sha256sum` cmp.

## Next step

Run `/gsd:verify-work 01-l1-data-fetch-skeleton-free-tier-discipline` to produce the canonical `01-VERIFICATION.md` and close out Phase 1. Then `/gsd:plan-phase 2` to scope Phase 2 (Panel Build for ICHI cKES/USDT anchor).
