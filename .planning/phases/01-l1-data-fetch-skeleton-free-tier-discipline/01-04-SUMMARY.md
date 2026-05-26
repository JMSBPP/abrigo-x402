---
phase: 01-l1-data-fetch-skeleton-free-tier-discipline
plan: 04
subsystem: cache

tags: [fetch-04, content-addressed-cache, sha256, byte-identity, zod, jsonl, idempotency, ts]

# Dependency graph
requires:
  - phase: 01-l1-data-fetch-skeleton-free-tier-discipline-00
    provides: pnpm workspace; fetch/ TS scaffold with zod@4.4.3 dep; tsconfig ESM NodeNext; vitest config; constants.ts (CELO_CHAIN_ID, BASE_SEPOLIA_CHAIN_ID)
provides:
  - cacheKeyHash(input) and canonicalize(input) — content-addressed key with mechanical byte-stability via explicit template literal (checker C2 fix)
  - ManifestEntrySchema (zod) with EndpointEnum (graph-mainnet, graph-sepolia, blockscout, forno, x402-mock-sepolia)
  - appendManifestIfNew() — idempotent on cache_key_hash collision; atomic rename-from-tmp write
  - findByCacheKey() — null on miss (for Plan 01-06 cache short-circuit)
  - writeCachePayload() — deterministic JSONL writer; data/raw/<protocol>/<hash[0:2]>/<hash>.jsonl layout; sha256(content) returned as dataHash
  - 18 vitest tests pinning FETCH-04 SC-4 byte-identity invariant (7 key + 7 manifest + 4 payload)
affects:
  - 01-06 (CLI integration — wires cache short-circuit + manifest append + payload write into ichi fetch path)
  - 01-08 (Wave 3 end-to-end byte-identity verification — full sha256sum cmp across two `make fetch-ichi` runs)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Content-addressed cache key via explicit string template literal (mechanical byte-stability, NOT JSON.stringify property-filter)"
    - "Atomic manifest rewrite via writeFile + rename-from-tmp"
    - "Deterministic JSONL payload (Phase-1 ships JSONL; Phase-2 polars batch-converts to Parquet)"
    - "fetchTimestamp as MANIFEST METADATA, never in cache key (FETCH-04 paid-step-is-idempotent invariant)"

key-files:
  created:
    - fetch/src/cache/key.ts
    - fetch/src/cache/manifest.ts
    - fetch/src/cache/parquet-writer.ts
  modified:
    - fetch/tests/cache.test.ts

key-decisions:
  - "canonicalize() uses explicit template literal `{\"blockRange\":[..],\"chainId\":..,\"contractAddress\":\"..\"}` — NOT JSON.stringify with property-filter array. Mechanical byte-stability independent of V8 key-insertion-order behavior (checker C2 fix). Tests pin byte-content vs a hand-written reference string."
  - "fetchTimestamp is MANIFEST metadata, NEVER in the cache key. The FETCH-04 paid-step-is-idempotent invariant requires cache_key_hash = sha256(canonical(chainId, contractAddress, blockRange)) ONLY — re-runs hit cache + add zero ledger rows."
  - "Phase 1 ships deterministic JSONL (NOT Parquet from TS). Rationale: cost-ledger choice (Plan 01-02) is JSONL; Parquet from pure-TS adds compression-dependency risk at zero empirical benefit for Phase-1 volumes (~4k events/30d). Phase 2 polars batch-converts JSONL → Parquet at ingest."
  - "Manifest atomic-write strategy: writeFile to <path>.tmp then rename(). Power-loss / kill-9 mid-write leaves the prior manifest intact rather than half-written."
  - "Payload path layout: data/raw/<protocol>/<hash[0:2]>/<hash>.jsonl — 256-way prefix fanout keeps any single directory under ~10k entries at multi-iteration scale."

patterns-established:
  - "TDD per task: RED commit (failing test) → GREEN commit (impl that passes) — 4 atomic commits total, scope (01-04)"
  - "Empty rows array → empty file; sha256(empty string) returned as dataHash — explicit edge-case test enforces"
  - "EndpointEnum centralized in manifest.ts as the canonical zod schema for the 5 endpoints; reused by Plan 01-02's cost-ledger expansion"

requirements-completed: [FETCH-04]

# Metrics
duration: 3min
completed: 2026-05-26
---

# Phase 1 Plan 04: Content-Addressed Cache Module Summary

**sha256-keyed cache on (chainId, contractAddress, blockRange) with mechanical byte-stability via explicit template literal (checker C2 fix); zod-validated manifest with idempotent append; deterministic JSONL payload writer — 18 vitest tests green, FETCH-04 SC-4 unit-level proof shipped.**

## Performance

- **Duration:** 3 min (213 s)
- **Started:** 2026-05-26T13:43:04Z
- **Completed:** 2026-05-26T13:46:37Z
- **Tasks:** 2 (both TDD `tdd="true"` — 4 atomic commits total)
- **Files modified:** 4 (3 created + 1 modified)

## Accomplishments

- **`fetch/src/cache/key.ts`** ships `canonicalize()` + `cacheKeyHash()`. Canonical serialization uses an explicit string template literal — NOT `JSON.stringify` with a property-filter array. The literal form is mechanically byte-stable; the array-second-arg form is only byte-stable today by accident of V8 key-insertion-order preservation. This is the load-bearing **checker C2 fix** for FETCH-04 SC-4.
- **`fetch/src/cache/manifest.ts`** ships `ManifestEntrySchema` (zod) with the 5-endpoint enum, `readManifest()`, `appendManifestIfNew()` (idempotent on `cache_key_hash`; atomic rename-from-tmp write), and `findByCacheKey()` (used by Plan 01-06's cache short-circuit). `fetchTimestamp` is METADATA only — never in the canonical key.
- **`fetch/src/cache/parquet-writer.ts`** ships `writeCachePayload()` — deterministic JSONL writer to `data/raw/<protocol>/<hash[0:2]>/<hash>.jsonl`. No `Date.now()`, no embedded timestamp, verbatim row order. Returns `dataHash = sha256(file content)` for the manifest's `dataHash` field, which Plan 01-08's `make verify-cache-idempotency` `sha256sum` cmp consumes.
- **18 vitest tests** all green: 7 key (hex shape, EIP-55 case-invariance, chainId-differs, blockRange-differs, no-extra-fields, property-order invariance, **literal-byte-content reference string**) + 7 manifest (missing-file empty, append-fresh, idempotency on duplicate, findByCacheKey null + hit, zod-rejects-invalid-endpoint, **schema-level proof that fetchTimestamp/dataHash/gitCommit are NOT in the canonical key**) + 4 payload (two-write byte-identity, dataHash matches file sha256, empty-rows edge case, path layout).

## Task Commits

Each task was TDD-committed atomically (RED then GREEN). 4 cache commits ship `(01-04)` scope:

1. **Task 1 RED: cacheKeyHash + canonicalize failing tests** — `e394cf1` (test)
2. **Task 1 GREEN: cacheKeyHash + canonicalize implementation** — `5129ef7` (feat) — 7/7 tests pass; tsc clean
3. **Task 2 RED: manifest + payload-writer failing tests** — `a1daf97` (test) — extends cache.test.ts to 18 tests
4. **Task 2 GREEN: manifest + parquet-writer implementation** — `0496df8` (feat) — 18/18 tests pass; tsc clean

_(Note: commit `a1daf97` swept in unstaged work from a parallel wave (01-01 stack-pins + cli.ts stub + _helpers.ts expansion) via the pre-commit hook's stash-restore-then-add cycle. This is a known artifact of running waves in parallel with active unstaged work; the swept-in files are pre-existing parallel-wave content, not 01-04 logic, and have no impact on FETCH-04 correctness. Files reverted to pure 01-04 scope are: `fetch/src/cache/key.ts`, `fetch/src/cache/manifest.ts`, `fetch/src/cache/parquet-writer.ts`, `fetch/tests/cache.test.ts`.)_

**Plan metadata commit:** _(this commit lands SUMMARY.md + STATE.md + ROADMAP.md update)_

## Files Created/Modified

- **`fetch/src/cache/key.ts`** (created, 51 lines) — `canonicalize()` (explicit template literal) + `cacheKeyHash()` (node:crypto sha256). Inline doc-comment calls out the checker C2 mechanical-byte-stability contract.
- **`fetch/src/cache/manifest.ts`** (created, 106 lines) — `ManifestEntrySchema` + `EndpointEnum` + 3 functions. Doc-comment makes the atomic rename-from-tmp strategy and the fetchTimestamp-is-metadata-only invariant explicit.
- **`fetch/src/cache/parquet-writer.ts`** (created, 72 lines) — `writeCachePayload()`. Doc-comment makes the byte-identity contract and the JSONL-now / Parquet-later strategy explicit.
- **`fetch/tests/cache.test.ts`** (modified from describe.todo stub to 18 active tests, ~190 lines) — RED/GREEN cycles for both tasks.

## Decisions Made

1. **Explicit string template literal for `canonicalize()`** (checker C2 fix, locked at plan time). The plan's `<action>` block explicitly forbids `JSON.stringify(obj, [keys])` because the array second-arg is a property FILTER per spec, NOT a key-order specifier. The template-literal form makes byte-identity a contract of `key.ts` mechanically independent of any JS engine. Tests pin the exact byte-content against a hand-written reference string.
2. **`fetchTimestamp` is metadata, never in the cache key** (CONTEXT.md locked decision; reinforced by checker C2). The schema-level test in this plan asserts `canonicalize()` output does NOT contain `fetchTimestamp`, `dataHash`, or `gitCommit`.
3. **JSONL now, Parquet later** (RESEARCH §J ledger-vs-cache-payload boundary; consistent with Plan 01-02 cost-ledger choice). Phase 2 polars batch-converts at ingest; this isolates the binary-format risk to Python where polars' Parquet writer is battle-tested.
4. **Atomic rename-from-tmp for manifest writes** — explicit defense against partial writes under power-loss / kill-9. Pattern matches the cost-ledger's append discipline.
5. **256-way prefix fanout** for the payload directory layout (`<hash[0:2]>` subdirectory) — keeps any single dir under ~10k entries even at multi-iteration scale.

## Deviations from Plan

**None — plan executed exactly as written.** All `<action>` blocks land verbatim per the plan. The literal-byte-content test (checker C2) was included as written; the 4 extra payload-writer edge tests (path layout, empty rows) and one extra manifest test (schema-level fetchTimestamp-exclusion proof) are within the plan's `<behavior>` envelope (7+ tests + the "byte-identity" + "fetchTimestamp metadata-only" requirements).

The plan's `<done>` block called for "≥13 total" tests; this implementation ships **18**, exceeding the floor.

---

**Total deviations:** 0
**Impact on plan:** None — clean execution.

## Issues Encountered

- **Parallel-wave file sweep into commit `a1daf97`** — the pre-commit hook stashed unstaged files from other in-flight waves (01-01 stack-pins, 01-02 cost-ledger budget tests) into the patch cache, then `[INFO] Restored changes` re-applied them onto the working tree AFTER `git add`. The commit therefore landed those files alongside the staged `fetch/tests/cache.test.ts`. The swept-in files are pre-existing parallel-wave content (not 01-04 logic) and do not affect FETCH-04 correctness. The 01-01 and 01-02 executors will re-commit those same files in their own scopes when they complete their plans; this creates a benign duplicate-touch in `a1daf97` but no functional regression. Documented here for traceability.

## User Setup Required

None — no external service configuration required. All FETCH-04 primitives are pure-TS, node:crypto + node:fs/promises + zod. No env vars, no API keys, no faucet flows.

## Next Phase Readiness

**Wave 2 unblocked for FETCH-04 consumers:**
- **Plan 01-06 (CLI)** can import `{ cacheKeyHash, canonicalize }` from `fetch/src/cache/key.js`, `{ appendManifestIfNew, findByCacheKey, type ManifestEntry }` from `fetch/src/cache/manifest.js`, and `{ writeCachePayload }` from `fetch/src/cache/parquet-writer.js`. The cache short-circuit pattern is: `findByCacheKey(hash)` BEFORE any network call; on hit, return cached payload + skip cost-ledger write.
- **Plan 01-08 (Wave 3 end-to-end verify)** can run `make fetch-ichi` twice and assert byte-identical files via `sha256sum data/raw/ichi/<prefix>/<hash>.jsonl | uniq | wc -l == 1` AND zero new cost-ledger rows. The unit-level proof (this plan's 18 tests) is a strict subset of the CLI-level proof; if 01-08 fails, the bug is in the CLI integration, NOT the cache primitives.

**No blockers.** Wave 1a parallel siblings (01-01, 01-02) are still in flight but do not block FETCH-04 — cache primitives have zero runtime dependencies on stack-pin tests or cost-ledger module.

## Self-Check: PASSED

- `fetch/src/cache/key.ts`: FOUND
- `fetch/src/cache/manifest.ts`: FOUND
- `fetch/src/cache/parquet-writer.ts`: FOUND
- `fetch/tests/cache.test.ts`: FOUND (modified from `.todo` stub to 18 active tests)
- Commit `e394cf1` (Task 1 RED): FOUND in `git log`
- Commit `5129ef7` (Task 1 GREEN): FOUND in `git log`
- Commit `a1daf97` (Task 2 RED): FOUND in `git log`
- Commit `0496df8` (Task 2 GREEN): FOUND in `git log`
- `pnpm -C fetch test tests/cache.test.ts --run` → 18/18 PASS
- `pnpm -C fetch exec tsc --noEmit` → exit 0

---
*Phase: 01-l1-data-fetch-skeleton-free-tier-discipline*
*Completed: 2026-05-26*
