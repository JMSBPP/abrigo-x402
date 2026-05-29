---
phase: 01-l1-data-fetch-skeleton-free-tier-discipline
plan: 05
subsystem: data-fetch
tags: [blockscout, etherscan-compat, uniswap-v3, viem, zod, graphql, the-graph, protocol-agnosticism, leak-gate, fetch-01]

# Dependency graph
requires:
  - phase: 01-l1-data-fetch-skeleton-free-tier-discipline
    provides: "_helpers.ts (testDirname, fornoMock), loadProtocol, ProtocolSpec, test_fixture.toml (synthetic non-ICHI/Steer fixture)"
  - phase: 01-l1-data-fetch-skeleton-free-tier-discipline
    provides: "fetch/src/constants.ts (BASE_SEPOLIA_*, CELO_*); pinned viem 2.51.0 + zod 4.4.3 + graphql-request 7.4.0; pnpm workspace"
provides:
  - "fetch/src/blockscout/v1-getlogs.ts — etherscan-compat client with auto-pagination + zod-validated response"
  - "fetch/src/decoders/uniswap-v3-swap.ts — UniswapV3SwapEventAbi + UniswapV3SwapTopic0 constant + decodeSwap viem wrapper"
  - "fetch/src/subgraph/client.ts — disabled-by-default Graph gateway client (throws MissingGraphApiKeyError without GRAPH_API_KEY)"
  - "fetch/tests/blockscout-client.test.ts — 9 unit tests using captured fixture (no live HTTP in CI)"
  - "fetch/tests/protocol-agnostic.test.ts — FETCH-01 SC-5 leak-gate (zero offenders) + subgraph dormant-state suite"
  - "fetch/tests/fixtures/blockscout-v1-getlogs-cKES-USDT.json — captured v1 etherscan-compat fixture"
affects:
  - "01-06: CLI ICHI fetch path consumes { getLogsV1, decodeSwap, UniswapV3SwapTopic0 }; gates Graph calls behind getSubgraphClient → MissingGraphApiKeyError check"
  - "01-08: full Wave-3 CLI integration test rides the protocol-agnostic leak gate"
  - "Phase 1.5 enrichment: provisions GRAPH_API_KEY + adds [subgraphs.uniswap_v3] block to protocols/ichi.toml to uncap the dormant subgraph leg"
  - "Phase 6 swap-surface invariant builds on SC-5 leak-gate (`grep -r ichi fetch/src` returns 0 hits)"

# Tech tracking
tech-stack:
  added: []  # all deps were pinned in Plan 01-00 / 01-01; no new packages
  patterns:
    - "etherscan-compat v1 paginated fetch with block-cursor keyset (NOT v2 — v2 rejects topic0)"
    - "viem decodeEventLog wrapper exposing typed Swap args"
    - "fail-closed env-gated client (MissingGraphApiKeyError) read-at-call-time for vi.stubEnv compatibility"
    - "test-side recursive AST-free grep gate over fetch/src for forbidden patterns (Phase-6 invariant precursor)"
    - "captured-once JSON fixture for unit tests instead of live HTTP (CI determinism)"

key-files:
  created:
    - "fetch/src/blockscout/v1-getlogs.ts"
    - "fetch/src/decoders/uniswap-v3-swap.ts"
    - "fetch/src/subgraph/client.ts"
    - "fetch/tests/fixtures/blockscout-v1-getlogs-cKES-USDT.json"
  modified:
    - "fetch/tests/blockscout-client.test.ts (was describe.todo placeholder)"
    - "fetch/tests/protocol-agnostic.test.ts (was describe.todo placeholder)"

key-decisions:
  - "v1 etherscan-compat (/api?module=logs&action=getLogs) NOT v2 (/api/v2/addresses/.../logs) — RESEARCH §C verified v2 rejects topic0 with HTTP 422; URL shape pinned in unit test"
  - "Subgraph DISABLED by default per orchestrator finding #2 + RESEARCH §A; client exists so Phase 1.5 wires without import-graph reshape, but every call path throws MissingGraphApiKeyError until GRAPH_API_KEY is set"
  - "process.env.GRAPH_API_KEY read at CALL TIME (not module-load) — enables vi.stubEnv tests with natural static-import pattern (checker I8)"
  - "Auto-pagination via block-cursor keyset (fromBlock = parseInt(lastLog.blockNumber, 16) + 1); 1000-log/page hard cap is the trigger"
  - "Captured fixture lives in fetch/tests/fixtures/blockscout-v1-getlogs-cKES-USDT.json — synthetic 1-log shape mirroring real v1 response (RESEARCH §C verified-live); ABI-valid synthetic data field decodes cleanly via viem"
  - "Fee-tier leak gate uses anchored pattern `\\bfee[_a-zA-Z]*\\s*[:=]\\s*(0\\.0001|100|500|3000|10000)\\b` — flags fee=100 but not naked '100' in array sizes or hex offsets (research-trail false positives avoided)"
  - "MissingGraphApiKeyError carries a descriptive name and message referencing Phase 1 Blockscout-only default — surfaces the design intent at the failure site"

patterns-established:
  - "Pattern A — RED-then-GREEN TDD with separate commits per phase (test commit before feat commit); failing test must demonstrate the missing module / wrong arithmetic before the feat lands"
  - "Pattern B — captured-fixture pattern for HTTP clients: tests inject a synchronous `fetcher` (typeof fetch) override; CI runs offline; fixture lives under tests/fixtures/ with `.json` suffix"
  - "Pattern C — fail-closed env-gated module pattern: read `process.env.X` inside function body, throw typed Error subclass when unset, test via vi.stubEnv + afterEach unstub"
  - "Pattern D — leak-gate via test-side recursive grep over fetch/src/ with anchored regex patterns; complements Makefile leak-check (defense-in-depth at both pre-commit and unit-test layers)"

requirements-completed: [FETCH-01]

# Metrics
duration: 6min
completed: 2026-05-26
---

# Phase 01 Plan 05: Blockscout v1 Client + Uniswap V3 Swap Decoder + Dormant Subgraph + Leak Gate Summary

**Blockscout v1 etherscan-compat client (auto-paginated, zod-validated) + viem Uniswap V3 Swap decoder + dormant-by-default Graph subgraph client + FETCH-01 SC-5 protocol-agnosticism leak-gate test (zero offenders) — the load-bearing contract for Phase-6 swap-surface invariant.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-05-26T13:56:08Z
- **Completed:** 2026-05-26T14:02:33Z
- **Tasks:** 2 (both TDD; 4 atomic commits total)
- **Files modified:** 6 (4 new src + 2 test overwrites + 1 fixture)

## Accomplishments

- **Blockscout v1 client** with auto-pagination via block-cursor keyset (1000-log/page Hardlimit), zod-validated response shape, fetcher injection for offline tests, and explicit error contracts (`status='0' + No records` → empty success; `status='0' + non-empty result` → throw; HTTP non-ok → throw).
- **Uniswap V3 Swap decoder** with the verified topic0 constant `0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67` pinned + viem `decodeEventLog` wrapper returning typed `{ sender, recipient, amount0, amount1, sqrtPriceX96, liquidity, tick }`.
- **Dormant subgraph client** that ships but throws `MissingGraphApiKeyError` on every call path until `process.env.GRAPH_API_KEY` is set (read at call time per checker I8, so `vi.stubEnv` tests work with natural static imports).
- **SC-5 protocol-agnosticism leak gate** — recursive grep over `fetch/src/**/*.{ts,tsx,js,mjs}` rejects protocol-name branches (`config.name === 'ichi'/'steer'`), hard-coded factory addresses (ICHI `0x9FAb…418F`, Steer `0x116Dba…014C`), and magic fee-tier literals (`fee=0.0001|100|500|3000|10000`). Offender count = 0.
- **Synthetic test_fixture.toml proof** — `loadProtocol()` accepts `name='synthetic-test'` + `fee_tier=7777` through the SAME code path as `ichi.toml`, proving no name-based or magic-number branches exist in the loader.

## Task Commits

Each task was committed atomically (TDD RED → GREEN):

1. **Task 1 RED: failing tests for blockscout v1 client + swap decoder** — `3d7bb04` (test)
2. **Task 1 GREEN: blockscout v1 client + uniswap v3 swap decoder** — `b24f8d5` (feat)
3. **Task 2 RED: protocol-agnosticism leak gate + subgraph dormant-state** — `969676d` (test)
4. **Task 2 GREEN: dormant-by-default subgraph client** — `d3f1c64` (feat)

## Files Created/Modified

- `fetch/src/blockscout/v1-getlogs.ts` (new, 105 lines) — etherscan-compat client; auto-pagination; zod validation; URL shape pinned by unit test
- `fetch/src/decoders/uniswap-v3-swap.ts` (new, 53 lines) — `UniswapV3SwapEventAbi as const satisfies Abi` + `UniswapV3SwapTopic0` + `decodeSwap(topics, data)`
- `fetch/src/subgraph/client.ts` (new, 51 lines) — `MissingGraphApiKeyError` + `getSubgraphClient(deploymentId)` with call-time env read
- `fetch/tests/blockscout-client.test.ts` (overwrote describe.todo placeholder, 211 lines) — 9 tests (7 client + 2 decoder)
- `fetch/tests/protocol-agnostic.test.ts` (overwrote describe.todo placeholder, 167 lines) — 6 tests (3 leak-gate + 3 subgraph dormant)
- `fetch/tests/fixtures/blockscout-v1-getlogs-cKES-USDT.json` (new) — synthetic 1-log v1 response mirroring RESEARCH §C verified-live shape

## Decisions Made

- **v1 endpoint NOT v2.** Plan + operational context were explicit: v2 `/api/v2/addresses/<addr>/logs` rejects `topic0` with HTTP 422 (RESEARCH §C verified). Pinned URL shape (`module=logs&action=getLogs`) in the first unit test so any future refactor to v2 fails CI before it lands.
- **Subgraph dormant by default.** Per orchestrator finding #2 + RESEARCH §A downgrade verdict, the subgraph leg ships as a fail-closed module — never imported in Phase 1's hot path, ready for Phase 1.5 to provision a key.
- **Read env at call time, not module load.** `process.env.GRAPH_API_KEY` reads happen inside `getSubgraphClient()` so `vi.stubEnv` + static imports work without dynamic-import workarounds (checker I8).
- **Block-cursor keyset for pagination** (not page-number pagination). The v1 etherscan-compat module doesn't expose `next_page_params` like v2 does — we advance `fromBlock = parseInt(lastLog.blockNumber, 16) + 1` when a page returns the 1000-row cap.
- **Forbidden-fee regex anchored to `fee*` lvalue.** Naked `100` / `500` / `3000` in array sizes, hex offsets, etc. are legitimate; only literals assigned to `fee*` identifiers indicate a magic Uniswap V3 tier. Pattern: `\bfee[_a-zA-Z]*\s*[:=]\s*(0\.0001|100|500|3000|10000)\b`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected hex-arithmetic in pagination test assertion**
- **Found during:** Task 1 GREEN run (immediately after `getLogsV1` implementation landed)
- **Issue:** The plan body comment in the pagination test claimed `0x4061986 = 67_502_982` and asserted `fromBlock=67502983`. Actual value: `0x4061986 = 67_508_614` → cursor → `67_508_615`. Test failed against correct implementation.
- **Fix:** Updated the assertion + comment to `67_508_615`. Implementation arithmetic (`parseInt(lastEntry.blockNumber, 16) + 1`) was correct; only the test expectation was off.
- **Files modified:** `fetch/tests/blockscout-client.test.ts` (lines 149–150)
- **Verification:** `pnpm -C fetch test tests/blockscout-client.test.ts --run` → 9/9 pass.
- **Committed in:** `b24f8d5` (rolled into GREEN commit since the test commit alone would have been red against the actual hex value).

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug in plan-supplied test expectation).
**Impact on plan:** Single arithmetic correction; no architectural change; no scope creep. The plan body's `0x4061986` hex value was authoritative (it is the fixture's actual blockNumber); the plan's decimal annotation was wrong.

## Issues Encountered

- **`describe.todo` placeholder collision.** Both `fetch/tests/blockscout-client.test.ts` and `fetch/tests/protocol-agnostic.test.ts` already existed as `describe.todo(...)` stubs from earlier scaffolding. The `Write` tool requires a prior `Read` before overwriting, so each was Read first then overwritten — adds two harmless round-trips but no functional impact.
- **Pre-existing `deferred-items.md` in phase directory.** Plan 01-03 (sibling, parallel Wave 1b) logged the test arithmetic bug as a cross-plan deferred item. The 01-05 GREEN commit resolves it; the deferred-items.md entry can now be marked closed (left to phase-level housekeeping — not part of Plan 01-05 scope).
- **Unstaged sibling-plan file (`fetch/tests/freshness.test.ts`)** remained in working tree throughout 01-05 execution. Untouched — owned by Plan 01-03. Pre-commit hooks stashed it cleanly across each commit.

## User Setup Required

None — no external service configuration required at Phase 1. Phase 1.5 will provision `GRAPH_API_KEY` to uncap the dormant subgraph leg; until then `MissingGraphApiKeyError` is the expected behavior.

## Next Phase Readiness

- **Wave 2 / Plan 01-06 unblocked.** CLI integration imports:
  - `{ getLogsV1, type BlockscoutLog } from '../blockscout/v1-getlogs.js'`
  - `{ UniswapV3SwapTopic0, decodeSwap } from '../decoders/uniswap-v3-swap.js'`
  - `{ getSubgraphClient, MissingGraphApiKeyError } from '../subgraph/client.js'` (kept dormant)
- **Wave 3 / Plan 01-08 leak-gate inheritance.** `make leak-check` (Makefile-level) + `fetch/tests/protocol-agnostic.test.ts` (unit-test-level) form defense in depth — both must pass on every commit touching `fetch/src/`.
- **Phase 1.5 retroactive enrichment path.** Add `[subgraphs.uniswap_v3]` block to `protocols/ichi.toml` + provision `GRAPH_API_KEY` to flip the subgraph leg live. No code change required in 01-05 modules.
- **No blockers** — full vitest suite at 8 files passed + 3 skipped + 69 tests passing; `tsc --noEmit` clean; `make leak-check` PASS.

## Self-Check: PASSED

- `fetch/src/blockscout/v1-getlogs.ts` — FOUND
- `fetch/src/decoders/uniswap-v3-swap.ts` — FOUND
- `fetch/src/subgraph/client.ts` — FOUND
- `fetch/tests/blockscout-client.test.ts` — FOUND
- `fetch/tests/protocol-agnostic.test.ts` — FOUND
- `fetch/tests/fixtures/blockscout-v1-getlogs-cKES-USDT.json` — FOUND
- Commit `3d7bb04` (test RED blockscout+decoder) — FOUND
- Commit `b24f8d5` (feat GREEN blockscout+decoder) — FOUND
- Commit `969676d` (test RED protocol-agnostic+subgraph) — FOUND
- Commit `d3f1c64` (feat GREEN subgraph client) — FOUND

---
*Phase: 01-l1-data-fetch-skeleton-free-tier-discipline*
*Completed: 2026-05-26*
