---
phase: 01-l1-data-fetch-skeleton-free-tier-discipline
plan: 03
subsystem: fetch-freshness-gates
tags: [viem, subgraph, blockscout, freshness, lag-detection, fetch-03]

# Dependency graph
requires:
  - phase: 01-l1-data-fetch-skeleton-free-tier-discipline
    provides: "Plan 01-01 — `fetch/tests/_helpers.ts` exports `testDirname` + `fornoMock` (shared mock factory)"
  - phase: 01-l1-data-fetch-skeleton-free-tier-discipline
    provides: "Plan 01-00 — `fetch/src/viem-clients.ts` + `forno_head_snapshot.json` + workspace scaffolding"
provides:
  - "`fetch/src/subgraph/freshness.ts` — `subgraphFreshness<T>(input, threshold=100): Promise<T>` + `SubgraphLagError`"
  - "`fetch/src/blockscout/freshness.ts` — `blockscoutFreshness(input, threshold=100): Promise<{lag, fresh: true}>` + `BlockscoutFreshnessError`"
  - "9 vitest unit tests covering both wrappers (lag-pass, lag-throw, missing-meta, custom threshold, call-count)"
  - "Authoritative resolution: Blockscout v2 logs lack the per-log consensus field → wrappers rely on lag-vs-Forno only"
affects: [01-05, 01-06, 01-07, 01-08]

# Tech tracking
tech-stack:
  added: []  # No new deps; consumes viem PublicClient type already pinned in 01-00
  patterns:
    - "Single-file two-describe test pattern with shared imported mock (checker C4 invariant)"
    - "Threshold-default-100 freshness gate symmetric across subgraph + blockscout legs"
    - "Endpoint-agnostic generic-T response shape for subgraphFreshness (REPRO-02-compatible)"

key-files:
  created:
    - "fetch/src/subgraph/freshness.ts"
    - "fetch/src/blockscout/freshness.ts"
    - ".planning/phases/01-l1-data-fetch-skeleton-free-tier-discipline/deferred-items.md"
  modified:
    - "fetch/tests/freshness.test.ts (was Plan 01-00 describe.todo placeholder; now 9 live tests)"

key-decisions:
  - "Both wrappers default threshold = 100 blocks ≈ 100s at Celo 1s/block — matches FETCH-03 SC-3 spec and gives ~70-block margin over typical 10–30-block indexer reorg buffers"
  - "blockscoutFreshness checks lag-vs-Forno ONLY — NO `block_consensus` field (RESEARCH §H + orchestrator finding #1 supersede Phase-0 CONTEXT.md draft; field absent from v1 getLogs AND v2 /addresses/{addr}/logs per live probe)"
  - "Subgraph freshness throws on missing _meta OR missing _meta.block.number (subgraph_block = -1 sentinel) — defensive against malformed Graph responses"

patterns-established:
  - "FRESHNESS-WRAPPER-DEFAULT-100: every block-anchored response leg in fetch/src must compare against forno.getBlockNumber() with default 100-block threshold"
  - "SHARED-FORNO-MOCK: tests import `fornoMock` from `./_helpers` (NEVER redeclare) — single source of truth for the PublicClient.getBlockNumber stub"
  - "ERROR-DETAILS-CARRY-ENDPOINT: BlockscoutFreshnessError.details.endpoint is required so the cost-ledger / log aggregator can attribute stale-data alerts to the specific Blockscout host"

requirements-completed: [FETCH-03]

# Metrics
duration: 4min
completed: 2026-05-26
---

# Phase 01 Plan 03: FETCH-03 Freshness Wrappers Summary

**Two lag-vs-Forno freshness gates (subgraph `_meta.block.number` + Blockscout `most_recent_log_block`) with 100-block default threshold and explicit typed errors, gating every Phase-1 indexer-backed fetch against silent-stale-data.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-05-26T13:55:35Z
- **Completed:** 2026-05-26T13:59:28Z
- **Tasks:** 2 (each TDD: RED → GREEN)
- **Commits:** 4 atomic
- **Files modified:** 3 source/test files + 1 deferred-items doc

## Accomplishments

- `subgraphFreshness<T>` ships endpoint-agnostic: same code gates Uniswap-V3-on-Celo (Messari fork), Mento Broker, and any future Graph deployment, since it only inspects `response._meta.block.number`.
- `blockscoutFreshness` ships with the corrected spec — relies exclusively on `most_recent_log_block` lag (no `block_consensus` per-log check, since Blockscout v2 does not expose that field; verified via live probe in RESEARCH §C/§H).
- Both wrappers default to a 100-block threshold (~100s at Celo 1s/block) and emit typed errors (`SubgraphLagError`, `BlockscoutFreshnessError`) with structured `details` so the cost-ledger / monitoring layer can attribute stale-data alerts to a specific endpoint.
- 9 vitest unit tests pass; full Phase-1 test suite still green for 01-03's territory (one pre-existing failure in 01-05's `blockscout-client.test.ts` cursor-advance logic is logged to `deferred-items.md` — out of scope for 01-03).
- `pnpm -C fetch exec tsc --noEmit` exits 0.

## Task Commits

Each task was committed atomically (TDD RED → GREEN):

1. **Task 1 RED: failing subgraphFreshness tests** — `d48b51f` (test)
2. **Task 1 GREEN: subgraphFreshness wrapper + SubgraphLagError** — `ceec9c4` (feat)
3. **Task 2 RED: failing blockscoutFreshness tests appended to same file** — `92eab70` (test)
4. **Task 2 GREEN: blockscoutFreshness wrapper + BlockscoutFreshnessError** — `c477604` (feat)

**Plan metadata:** _final docs commit on this branch_ (docs: complete plan)

## Files Created/Modified

- `fetch/src/subgraph/freshness.ts` (created, 72 lines) — exports `SubgraphMeta`, `SubgraphFreshnessInput<T>`, `SubgraphLagError`, async `subgraphFreshness<T>(input, threshold=100)`.
- `fetch/src/blockscout/freshness.ts` (created, 60 lines) — exports `BlockscoutFreshnessError`, async `blockscoutFreshness({ most_recent_log_block, forno, endpoint, threshold=100 })`.
- `fetch/tests/freshness.test.ts` (rewritten from describe.todo placeholder, 109 lines) — single file, two `describe()` blocks, shared `fornoMock` imported from `./_helpers` (checker C4 invariant).
- `.planning/phases/01-l1-data-fetch-skeleton-free-tier-discipline/deferred-items.md` (created) — logs the pre-existing 01-05-owned `blockscout-client.test.ts` cursor pagination failure as out-of-scope for 01-03.

## Decisions Made

- **`block_consensus` permanently dropped from blockscoutFreshness spec** (orchestrator finding #1 + RESEARCH §H): the field is absent from both `/api/v2/addresses/{addr}/logs` and the v1 `/api?module=logs&action=getLogs` shapes (confirmed via live Blockscout response in RESEARCH §C). Phase-0 CONTEXT.md's draft check is unfounded; any future plan re-introducing `block_consensus` is a regression and must be flagged by the reality-checker.
- **Both wrappers default threshold = 100 blocks**, symmetric for subgraph + blockscout legs to keep the freshness gate easy to reason about. 100 blocks ≈ 100s on Celo (1s/block post-2024-hardfork) and gives ~70-block margin over typical 10–30-block indexer reorg buffers.
- **Missing `_meta` → `SubgraphLagError` with sentinel subgraph_block = -1**: rather than a separate "malformed response" error class, the same `SubgraphLagError` covers stale + malformed cases since both block the data pipeline identically. Caller can disambiguate via `details.subgraph_block === -1`.
- **`fornoMock` shared via `./_helpers` import, never redeclared** (checker C4): keeps the Forno-RPC stub in one place; subgraph + blockscout halves of the test file use the same factory.

## Deviations from Plan

None — plan executed exactly as written. No Rule-1 / Rule-2 / Rule-3 auto-fixes triggered; no Rule-4 architectural checkpoints. Two minor wording adjustments inside source-file comments to remove the string `block_consensus` (since the plan's verification grep is `! grep -r "block_consensus" fetch/src fetch/tests`, even comment mentions count toward the gate); these are not deviations from the spec, just literal-byte-content compliance with the grep gate.

## Issues Encountered

- **Pre-existing 01-05 test failure surfaced by full-suite run** (`fetch/tests/blockscout-client.test.ts:150` — cursor pagination expects `fromBlock=67502983`, receives `67508615`). This file is owned by Plan 01-05 (Wave 1b parallel sibling), not 01-03. Logged to `deferred-items.md` per the scope-boundary rule; 01-05 executor will address. 01-03's territory (the `freshness.test.ts` file + `src/subgraph/freshness.ts` + `src/blockscout/freshness.ts`) shows 9/9 passing.

## User Setup Required

None — pure unit-level wrappers with no external service dependency. The wrappers consume a viem `PublicClient` injected by callers (production: `celoClient` from 01-01; tests: `fornoMock` from `./_helpers`).

## Next Phase Readiness

**Wave 1b unblocked for 01-05 (Blockscout client):** imports `{ blockscoutFreshness, BlockscoutFreshnessError } from '../blockscout/freshness'` and wraps every `/api?module=logs&action=getLogs` response with the freshness gate.

**Wave 2 unblocked for 01-06 (CLI integration):** the ichi fetch path threads each Blockscout response through `blockscoutFreshness({ most_recent_log_block: response.result.at(-1).blockNumber, forno: celoClient, endpoint: 'https://celo.blockscout.com' })` before handing off to the parser. Subgraph leg (`subgraphFreshness`) is wired but disabled by default in Phase 1 (GRAPH_API_KEY not provisioned; Phase 1.5 retroactive enrichment will activate it).

**Wave 3 (01-08) impact:** `make verify-cache-idempotency` will run twice through the same code path; freshness wrappers are deterministic (no side effects beyond the single `forno.getBlockNumber()` call), so cache idempotency is unaffected.

**Verification commands (for future re-validation):**

```bash
pnpm -C fetch test tests/freshness.test.ts --run   # 9/9 pass
pnpm -C fetch exec tsc --noEmit                     # exit 0
grep -rc "block_consensus" fetch/src fetch/tests    # 0 hits
grep -c "^const fornoMock" fetch/tests/freshness.test.ts   # 0 (not redeclared)
grep -c "from './_helpers'" fetch/tests/freshness.test.ts  # 1 (imported)
```

## Self-Check: PASSED

All declared artifacts verified on disk; all 4 commit hashes verified in `git log`:

- `fetch/src/subgraph/freshness.ts` FOUND
- `fetch/src/blockscout/freshness.ts` FOUND
- `fetch/tests/freshness.test.ts` FOUND
- `.planning/phases/01-l1-data-fetch-skeleton-free-tier-discipline/deferred-items.md` FOUND
- `.planning/phases/01-l1-data-fetch-skeleton-free-tier-discipline/01-03-SUMMARY.md` FOUND
- Commits `d48b51f`, `ceec9c4`, `92eab70`, `c477604` all present in `git log --oneline --all`.

---
*Phase: 01-l1-data-fetch-skeleton-free-tier-discipline*
*Completed: 2026-05-26*
