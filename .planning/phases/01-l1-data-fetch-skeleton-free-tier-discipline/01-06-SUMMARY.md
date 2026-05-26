---
phase: 01-l1-data-fetch-skeleton-free-tier-discipline
plan: 06
subsystem: cli
tags: [cli, budget-estimator, dry-run, forno-head-snapshot, cache-short-circuit, x402, fetch-02-sc-6]

# Dependency graph
requires:
  - phase: 01-00
    provides: "fetch/src/constants.ts loadFornoHeadSnapshot + DRY_RUN_FALLBACK_HEAD; notes/forno_head_snapshot.json (head=67896653)"
  - phase: 01-01
    provides: "loadProtocol + ProtocolSpecSchema (zod); celoClient viem singleton; _helpers.testDirname"
  - phase: 01-02
    provides: "checkBudget + GraphBudgetExceededError (90k/mo graph-mainnet soft cap)"
  - phase: 01-04
    provides: "cacheKeyHash + findByCacheKey (content-addressed cache short-circuit primary key)"
  - phase: 01-05
    provides: "Wave-1b modules (Blockscout v1 client + dormant Graph subgraph client) — imports staged but not exercised on dry-run path"
provides:
  - "fetch/src/budget.ts — pure estimateBudget(spec, fornoHead, earmark=30_000) returning BudgetEstimate JSON"
  - "fetch/src/cli.ts — full ichi|steer subcommand with --dry-run / --estimate-budget / --force / --pool / --from / --to flags"
  - "resolveHead() head-derivation precedence (env_override > snapshot > fallback > live); checker C3 invariant: dry-run path NEVER touches Forno RPC"
  - "JSON output schema augmented with cache_hit, dry_run, head_block, head_source"
affects: [01-08, 01-07]

# Tech tracking
tech-stack:
  added: []  # no new libraries — pure composition of Wave 1 modules
  patterns:
    - "Head-source provenance pattern: 4-tier precedence (env > snapshot > fallback > live) with head_source field in every emit"
    - "Dry-run / live separation: dry-run = no network, no budget gate; live = budget gate + checkBudget(force)"
    - "Cache short-circuit semantics: --pool/--from/--to triggers findByCacheKey(cacheKeyHash({chainId, address, blockRange})) BEFORE any network call"
    - "Synthetic-spec schema round-trip pattern (checker I9): test constructs raw TOML shape -> ProtocolSpecSchema.parse() -> consumer function; catches schema regressions in tests themselves"

key-files:
  created:
    - "fetch/src/budget.ts (87 lines — estimateBudget pure function + BudgetEstimate interface)"
    - "fetch/src/cli.ts (rewrite, 158 lines — full ichi/steer CLI with 4-tier head resolver)"
    - "fetch/tests/budget-dry-run.test.ts (87 lines — 3 unit tests, FETCH-02 SC-6)"
    - "fetch/tests/cli-integration.test.ts (98 lines — 5 process-level integration tests)"
  modified: []  # cli.ts was a stub from 01-01; rewrite supersedes the stub

key-decisions:
  - "JSON output key order: existing BudgetEstimate spread first, then auxiliary CLI-only keys (cache_hit, dry_run, head_block, head_source) appended; downstream JSON consumers should NOT depend on key order beyond what the BudgetEstimate interface guarantees"
  - "Cache short-circuit currently exposes cache_hit flag only — full skip-network behaviour deferred to Plan 01-08 (this plan's dry-run path makes no network calls regardless)"
  - "exit code 2 reserved for GraphBudgetExceededError (non-dry-run); exit code 1 for usage errors / unknown subcommand; exit code 99 for unhandled fatal exceptions"
  - "process.cwd() resolves to fetch/ when invoked via `pnpm -C fetch run fetch ...` or under vitest; spec path is `../protocols/<cmd>.toml`"
  - "pnpm built-in `fetch` command collides with our `fetch` script name — invokers MUST use `pnpm -s -C fetch run fetch ...` (NOT `pnpm -C fetch fetch ...`); documented for Plan 01-08 wiring"

patterns-established:
  - "Pattern (head-source provenance): every JSON emit from a CLI flag-driven entrypoint carries `head_source` so consumers can audit network provenance. Future Phase-2 panel construction inherits this for `data_source` field on Parquet rows."
  - "Pattern (4-tier head resolver): env override (FETCH_HEAD_OVERRIDE) > committed snapshot (notes/forno_head_snapshot.json) > constants fallback (DRY_RUN_FALLBACK_HEAD) > live RPC. Generalizable to any deterministic-required CI path that occasionally needs live values."
  - "Pattern (synthetic-spec round-trip, checker I9): tests that construct domain objects MUST round-trip through the validating schema parser before calling the consumer-under-test, so schema regressions break the test itself rather than silently allowing invalid shapes to flow into the consumer."

requirements-completed: [FETCH-02]

# Metrics
duration: 3min
completed: 2026-05-26
---

# Phase 01 Plan 06: CLI dry-run budget estimator with 4-tier Forno head resolver Summary

**`pnpm -s -C fetch run fetch ichi --dry-run --estimate-budget` outputs deterministic BudgetEstimate JSON (head_source: snapshot, total_queries=795, exceeds_earmark=false) with ZERO network calls per checker C3.**

## Performance

- **Duration:** 3 min (225 seconds)
- **Started:** 2026-05-26T14:10:32Z
- **Completed:** 2026-05-26T14:14:30Z (approximate)
- **Tasks:** 2 (both TDD, RED+GREEN pairs)
- **Files created:** 2 (`fetch/src/budget.ts`, `fetch/tests/budget-dry-run.test.ts` rewrite, `fetch/tests/cli-integration.test.ts` rewrite)
- **Files modified:** 1 (`fetch/src/cli.ts` — supersedes 01-01 stub)
- **Tests added:** 8 (3 unit + 5 process-level integration); all green
- **Full Phase-1 suite at completion:** 10 passed / 1 skipped / 77 tests passing / 0 fail

## Accomplishments

- **`estimateBudget(spec, fornoHead, earmark=30_000)` pure function** (RESEARCH §M cold-backfill formula):
  - blocks_per_vault = max(0, fornoHead - cold_backfill_from_block)
  - subgraph_queries_per_vault = ceil(blocks_per_vault / 10_000)
  - blockscout_queries_per_vault = ceil(observed_swaps_30d / 1000)
  - exceeds_earmark gates ONLY the graph leg (blockscout uncapped per FETCH-02)
- **CLI ichi/steer subcommand** with full flag matrix (`--dry-run` / `--estimate-budget` / `--force` / `--pool` / `--from` / `--to`)
- **4-tier head resolver** (checker C3): env_override > snapshot > fallback > live; dry-run path mechanically cannot escalate to live
- **JSON output schema augmented** with `cache_hit`, `dry_run`, `head_block`, `head_source` for downstream audit
- **Synthetic-spec schema round-trip pattern** (checker I9): test builds raw TOML shape and runs it through `ProtocolSpecSchema.parse()` BEFORE feeding to `estimateBudget()` — catches schema regressions in tests themselves
- **`pnpm -s -C fetch run fetch ichi --dry-run --estimate-budget` verbatim output for ICHI Iter-1:**
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

## Task Commits

Each task was committed atomically (TDD RED+GREEN pairs):

1. **Task 1 RED: estimateBudget unit tests (FETCH-02 SC-6)** — `f8b7df8` (`test(01-06)`)
2. **Task 1 GREEN: estimateBudget cold-backfill dry-run estimator** — `388379f` (`feat(01-06)`)
3. **Task 2 RED: CLI integration suite** — `1d8c515` (`test(01-06)`)
4. **Task 2 GREEN: CLI ichi/steer subcommand with dry-run/budget/cache short-circuit** — `1321d11` (`feat(01-06)`)

**Plan metadata commit:** pending (final commit captures SUMMARY.md + STATE.md + ROADMAP.md).

_TDD discipline: each task contributed RED + GREEN commit pair; no refactor needed (both implementations passed cleanly with no cleanup pass required)._

## Files Created/Modified

- `fetch/src/budget.ts` (CREATED, 87 lines) — `estimateBudget` + `BudgetEstimate` interface; pure function, no I/O
- `fetch/src/cli.ts` (REWRITTEN from 01-01 stub, 158 lines) — full ichi/steer CLI with parseArgs / resolveHead / cache short-circuit / budget gate
- `fetch/tests/budget-dry-run.test.ts` (REWRITTEN from describe.todo placeholder, 87 lines) — 3 unit tests
- `fetch/tests/cli-integration.test.ts` (REWRITTEN from describe.todo placeholder, 98 lines) — 5 process-level tests via execSync(tsx)

## Decisions Made

- **CLI invocation form:** `pnpm -s -C fetch run fetch ichi ...` (NOT `pnpm -C fetch fetch ichi ...` — collides with pnpm's built-in `fetch` command). The integration test sidesteps this by invoking `pnpm -s exec tsx src/cli.ts ...` directly.
- **Exit codes:** `0` success; `1` usage error / unknown subcommand; `2` GraphBudgetExceededError (non-dry-run only); `99` unhandled fatal exception.
- **Cache short-circuit:** the dry-run path surfaces `cache_hit` boolean but does NOT skip estimation when a hit is found (estimation is informational; no network call to skip). Full skip-network behaviour lands in Plan 01-08.
- **Spec resolution:** `process.cwd()` resolves to `fetch/` under both vitest and `pnpm -C fetch run fetch` invocations, so `../protocols/<cmd>.toml` is correct for both.
- **`exceeds_earmark` semantics:** counts ONLY the graph (subgraph) leg against the 30k earmark (per FETCH-02 schema: blockscout / forno / x402-mock-sepolia uncapped). For ICHI Iter-1 single-vault, graph_total = 1 × 790 = 790 << 30000.

## Deviations from Plan

None — plan executed exactly as written. The plan-supplied implementation was correct verbatim; both budget.ts and cli.ts compile clean and pass all tests on first GREEN. The plan-supplied test code had a path resolution pattern (`testDirname` + `import.meta.url`) that worked identically to the existing 01-03/01-05 callers — no I7 fix-up required.

## Issues Encountered

- **pnpm command-name collision:** `pnpm -C fetch fetch ichi ...` triggers pnpm's built-in `fetch` command (unknown-options error). Resolution: `pnpm -s -C fetch run fetch ichi ...` (with explicit `run` prefix). The integration test bypasses this by spawning `tsx src/cli.ts` directly via `pnpm -s exec`. Documented in key-decisions for Plan 01-08 awareness. Not a Phase-1 blocker.

## User Setup Required

None — no external service configuration required. The dry-run path is fully self-contained (head from committed snapshot file; no API keys consumed).

## Next Phase Readiness

**Wave 3 unblocked:**
- Plan 01-08 (end-to-end CLI integration with full Blockscout v1 getLogs + cache write + cost-ledger append) inherits the CLI scaffold from this plan. It extends `cli.ts` non-dry-run path to actually call `getLogsV1` + `writeCachePayload` + `appendLedger` + `appendManifestIfNew` for the cKES/USDT cold-backfill. The 4-tier head resolver, parseArgs, and exit-code conventions established here remain intact.
- Plan 01-08 `make verify-cache-idempotency` uses `dataHash` field returned by `writeCachePayload` (from 01-04) as the byte-identity oracle; this plan does not exercise that path on dry-run.

**Wave 2 sibling (01-07):** Already complete (`4718946`). No coupling to this plan.

**Operational notes for Phase 2+:**
- The `head_source` field is now part of the CLI contract; Phase-2 panel construction should propagate it onto Parquet rows as `data_source` provenance.
- `cold_backfill_from_block` is required for any protocol shipped to 01-06 dry-run; `protocols/ichi.toml` has it (`60_000_000`); `protocols/steer.toml` does NOT (Iter-2 stub deferred per Plan 00-05); Plan 01-08 will surface a clear error if a Steer dry-run is attempted without it.

## Self-Check: PASSED

Verified files exist:
- `fetch/src/budget.ts` — FOUND
- `fetch/src/cli.ts` — FOUND (rewritten)
- `fetch/tests/budget-dry-run.test.ts` — FOUND (rewritten)
- `fetch/tests/cli-integration.test.ts` — FOUND (rewritten)

Verified commits exist:
- `f8b7df8` — FOUND
- `388379f` — FOUND
- `1d8c515` — FOUND
- `1321d11` — FOUND

Verified gates:
- `pnpm -C fetch test --run` -> 10 passed / 1 skipped / 77 tests / 0 fail — PASS
- `pnpm -C fetch exec tsc --noEmit` -> exit 0 — PASS
- `pnpm -s -C fetch run fetch ichi --dry-run --estimate-budget | node -e "..."` -> GATE: PASS (`total_queries < 30000 AND exceeds_earmark === false AND head_source !== 'live' AND dry_run === true`)

---
*Phase: 01-l1-data-fetch-skeleton-free-tier-discipline*
*Plan: 06*
*Completed: 2026-05-26*
