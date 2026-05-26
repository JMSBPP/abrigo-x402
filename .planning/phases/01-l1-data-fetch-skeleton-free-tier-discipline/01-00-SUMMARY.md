---
phase: 01-l1-data-fetch-skeleton-free-tier-discipline
plan: 00
subsystem: infra
tags: [pnpm, typescript, viem, x402, uv, python, makefile, schema-frozen-check]

requires:
  - phase: 00-candidate-eligibility-pre-registration
    provides: "protocols/_schema.toml frozen baseline e9b214d; pre-commit hooks (af_lint, review_trail, schema_frozen); protocols/ichi.toml + protocols/steer.toml L0 protocol-spec TOMLs"

provides:
  - "pnpm workspace at root listing fetch/ + analysis/; pnpm-lock.yaml deterministic"
  - "fetch/package.json pinned: viem@2.51.0, @x402/fetch@2.13.0, @x402/evm@2.13.0, @x402/core@2.13.0, @graphprotocol/client-x402@1.0.0, @graphprotocol/client-cli@3.0.7 (dev), graphql-request@7.4.0, @mento-protocol/mento-sdk@3.2.8, zod@4.4.3, @iarna/toml@^2.2"
  - "fetch/tsconfig.json strict ESM NodeNext with rootDir=src + verbatimModuleSyntax; fetch/vitest.config.ts no-watch ESM"
  - "fetch/src skeleton: cost-ledger/, cache/, freshness/, endpoints/{blockscout,forno,graph}/, x402-mock/ — all gitkeep-anchored, Wave 1 fills"
  - "fetch/src/constants.ts: loadFornoHeadSnapshot + DRY_RUN_FALLBACK_HEAD (67896653) + CELO_USDT_ADDRESS + BASE_SEPOLIA_USDC_ADDRESS"
  - "fetch/tests skeleton: _helpers.ts + 10 describe.todo files (vitest run reports 10 skipped, no failures)"
  - "analysis/pyproject.toml + analysis/uv.lock: tick==0.8.0.2, statsmodels==0.14.6, polars==1.41.0, numpy==2.4.6, scipy==1.17.1 (Python >=3.13,<3.14, hatchling backend)"
  - "Makefile Phase-1 targets: fetch-ichi, lint-artifacts, verify-cache-idempotency, schema-probe, leak-check (full Phase-1 gate replacing Phase-0 stub)"
  - "scripts/schema_probe.sh: PROBE_PASS — schema-frozen hook scans _schema.toml only; safe to defer [subgraphs.uniswap_v3] block to Phase 1.5"
  - "notes/forno_head_snapshot.json: {head: 67896653, snapshotted_at: 2026-05-26T11:01:00Z} — deterministic dry-run source"
  - ".planning/phases/01-l1-.../01-00-x402-exports.txt: enumerated v2.13 exports of @x402/fetch + @x402/core + @x402/evm + @x402/evm/exact/client — load-bearing for Plan 01-07"
  - ".env.example: PRIVATE_KEY / CELO_RPC_URL / BASE_SEPOLIA_RPC_URL / BLOCKSCOUT_API_KEY / GRAPH_API_KEY"

affects:
  - "01-01-PLAN.md (stack-pins test reads fetch/package.json)"
  - "01-02-PLAN.md (cost-ledger writes to data/raw/, gitignore-protected)"
  - "01-03-PLAN.md (freshness wrappers consume fetch/src/constants.ts CELO_CHAIN_ID)"
  - "01-04-PLAN.md (Blockscout v1 client + cache module land in fetch/src/cache + fetch/src/endpoints/blockscout)"
  - "01-05-PLAN.md (protocols/*.toml zod parse; leak-check pre-commit complement)"
  - "01-06-PLAN.md (dry-run reads notes/forno_head_snapshot.json via constants.ts)"
  - "01-07-PLAN.md (x402 mock + Base Sepolia round-trip; imports from @x402/fetch + @x402/evm/exact/client per 01-00-x402-exports.txt)"
  - "01-08-PLAN.md (CLI integration; ARGS pass-through via make fetch-ichi)"

tech-stack:
  added:
    - "pnpm 10.33.0 workspace (root package.json + pnpm-workspace.yaml)"
    - "TypeScript 6.0.3 + tsx 4.22 + vitest 4.1.7 + @biomejs/biome 2.4.15 (root devDeps)"
    - "viem 2.51.0 + @x402/fetch 2.13.0 + @x402/evm 2.13.0 + @x402/core 2.13.0 (fetch/)"
    - "@graphprotocol/client-x402 1.0.0 + @graphprotocol/client-cli 3.0.7 (build-only) + graphql-request 7.4.0 + graphql ^16"
    - "@mento-protocol/mento-sdk 3.2.8 + zod 4.4.3 + dotenv ^16 + @iarna/toml ^2.2"
    - "uv 0.9.26 + hatchling Python build backend"
    - "tick 0.8.0.2 + statsmodels 0.14.6 + polars 1.41.0 + numpy 2.4.6 + scipy 1.17.1 (analysis/)"
  patterns:
    - "Pnpm workspace with `fetch/` (L1 TS substrate) + `analysis/` (L3+ Python) — matches ROADMAP.md SC paths verbatim"
    - "Pinned-exact (no caret) dependency versions in fetch/package.json — STACK.md drift detection at install time"
    - "Skeleton directories with `.gitkeep` anchors — Wave 1 plans fill modules without re-introducing the dir tree"
    - "describe.todo test stubs — vitest run summarizes Wave-1 work backlog without false test passes/failures"
    - "Deterministic dry-run substrate: notes/forno_head_snapshot.json + DRY_RUN_FALLBACK_HEAD constant (network-free CI)"
    - "Schema-probe utility: introspects scripts/pre-commit/schema_frozen.sh to verify it scans _schema.toml only (per-protocol TOMLs out of scope)"

key-files:
  created:
    - "pnpm-workspace.yaml — workspace manifest"
    - "package.json — root workspace meta + shared devDeps"
    - "fetch/package.json — pinned-version dependency manifest"
    - "fetch/tsconfig.json — strict ESM NodeNext"
    - "fetch/vitest.config.ts — ESM, no watch in CI"
    - "fetch/biome.json — recommended rules, 2-space single-quote"
    - "fetch/src/index.ts — barrel export skeleton"
    - "fetch/src/constants.ts — Forno snapshot loader + chain IDs + canonical token addresses"
    - "fetch/tests/_helpers.ts + 10 describe.todo test files"
    - "analysis/pyproject.toml + analysis/uv.lock + analysis/src/abrigo_x402/__init__.py"
    - ".env.example — Phase-1 environment variables"
    - "scripts/schema_probe.sh — load-bearing schema-frozen probe"
    - "notes/forno_head_snapshot.json — deterministic dry-run head"
    - ".planning/phases/01-l1-.../01-00-x402-exports.txt — Plan 01-07 read_first"
  modified:
    - ".gitignore — anchor /out/ /cache/ /broadcast/ to root; ignore data/raw/* except manifest.json + _cost_ledger.{jsonl,parquet}"
    - "Makefile — added Phase-1 targets (fetch-ichi, lint-artifacts, verify-cache-idempotency, schema-probe); replaced Phase-0 leak-check stub with full Phase-1 three-class gate"

key-decisions:
  - "Replaced Phase-0 stub leak-check with full Phase-1 gate (3 classes: protocol-name branches + factory-addr literals + magic fee-tier ints) rather than appending a new target. Rationale: existing target was a Phase-0-era stub that only scanned for `ichi` string — strict superset of behavior preserves intent."
  - "Dropped tsconfig include of vitest.config.ts + tests/ to satisfy rootDir=src invariant (load-bearing per Plan 01-00 frontmatter key_links). Tests are still type-checked at vitest-run time via vitest's own TS pipeline; explicit tests/tsconfig.json deferred to Wave 1 if any plan needs tighter test type-checking."
  - "Forno head snapshot taken live during Task 4 (head=67896653, source=https://forno.celo.org eth_blockNumber 0x40bf54d). Embedded in BOTH notes/forno_head_snapshot.json (canonical) and fetch/src/constants.ts DRY_RUN_FALLBACK_HEAD (last-resort fallback for partial checkouts)."
  - "x402 exports probe confirms x402Client + wrapFetchWithPayment live in @x402/fetch (NOT @x402/core as RESEARCH §E speculated). Plan 01-07 imports accordingly. registerExactEvmScheme lives in @x402/evm/exact/client subpath, also confirmed."
  - "Added 4 constants to fetch/src/constants.ts beyond plan spec (CELO_CHAIN_ID, BASE_SEPOLIA_CHAIN_ID, CELO_USDT_ADDRESS, BASE_SEPOLIA_USDC_ADDRESS) per Rule 2 — Wave 1 plans need these single-source-of-truth values; the alternative is N copies of the same hex string in N modules, which leak-check would later flag."

patterns-established:
  - "Workspace bootstrap: `rm -rf node_modules package-lock.json && pnpm install` is the canonical clean-start for the repo (npm-era artifacts deleted at Plan 01-00)"
  - "Per-task atomic commit with `(01-NN)` scope; conventional-commit types feat/fix/test/chore/refactor"
  - "Vitest describe.todo stubs serve as Wave-1 work tracker — `pnpm -C fetch test` reports N skipped instead of 0 tests"

requirements-completed: []

duration: 7min
completed: 2026-05-26
---

# Phase 1 Plan 00: Bootstrap Pnpm Workspace + Fetch/ TS Scaffold + Python Pin + Schema-Probe Summary

**Pnpm workspace + viem/x402/Mento dep tree pinned + Python env locked + Forno head snapshot + x402 v2.13 exports inventory — every gate Wave 1 needs to start parallel work.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-05-26T11:01:43Z
- **Completed:** 2026-05-26T11:08:49Z
- **Tasks:** 4
- **Files modified:** 23 (20 created + 3 modified)

## Accomplishments

- pnpm workspace bootstrapped from clean state — old npm-era `node_modules/` + `package-lock.json` removed, fresh `pnpm install` resolves 638 packages cleanly
- `pnpm -C fetch exec tsc --noEmit` passes against the skeleton `src/` + the new `fetch/src/constants.ts` + `fetch/src/index.ts`
- `make schema-frozen-check` still PASS against the Phase-0 baseline `e9b214d` — no regression
- `make schema-probe` returns PROBE_PASS: the schema-frozen pre-commit hook scans `protocols/_schema.toml` only, so adding `[subgraphs.uniswap_v3]` to `protocols/ichi.toml` at Phase 1.5 is hook-safe
- `analysis/uv.lock` resolved with 24 transitive packages against Python 3.13.5; the five required pins (tick/statsmodels/polars/numpy/scipy) all present
- x402 v2.13 exports probe captured: `x402Client` + `wrapFetchWithPayment` are in `@x402/fetch`; `registerExactEvmScheme` is at `@x402/evm/exact/client` (subpath); `@x402/core` only exports `x402Version` — resolves RESEARCH §E speculation, load-bearing for Plan 01-07
- Forno head snapshot captured live (`head=67896653` at `2026-05-26T11:01:00Z` from `forno.celo.org eth_blockNumber 0x40bf54d`) — Plan 01-06 dry-run is deterministic + network-free
- 10 `describe.todo` test stubs land under `fetch/tests/` as Wave-1 work tracker — vitest run reports `10 skipped` rather than 0 tests
- `fetch/src/` skeleton dirs (cost-ledger/, cache/, freshness/, endpoints/{blockscout,forno,graph}/, x402-mock/) committed via `.gitkeep` anchors — Wave 1 plans fill them without re-introducing the directory tree

## Task Commits

Each task committed atomically with `(01-00)` scope:

1. **Task 1: pnpm workspace + fetch/ TS scaffold** — `c46cbb7` (feat)
2. **Task 2: analysis/ Python skeleton + uv.lock pinning** — `682ca13` (chore)
3. **Task 3: Makefile additions + schema-probe utility** — `eaf7de3` (feat)
4. **Task 4: x402 v2.13 exports probe + Forno head snapshot + constants.ts** — `36dc615` (feat)

**Plan metadata commit:** appended at end of execution.

## Files Created/Modified

### Created
- `pnpm-workspace.yaml` — workspace manifest (fetch + analysis)
- `pnpm-lock.yaml` — deterministic lock (638 packages resolved)
- `fetch/package.json` — pinned exact versions per STACK.md
- `fetch/tsconfig.json` — strict ESM NodeNext, rootDir=src, verbatimModuleSyntax
- `fetch/vitest.config.ts` — ESM, no-watch CI
- `fetch/biome.json` — recommended rules, 2-space indent, single quotes
- `fetch/src/index.ts` — barrel skeleton (satisfies rootDir invariant)
- `fetch/src/constants.ts` — Forno snapshot loader + chain IDs + canonical token addresses
- `fetch/src/{cost-ledger,cache,freshness,endpoints/blockscout,endpoints/forno,endpoints/graph,x402-mock}/.gitkeep` — Wave-1 skeleton anchors
- `fetch/tests/_helpers.ts` + 10 `describe.todo` test files (stack-pins, cost-ledger, freshness, cache, protocol-spec, blockscout-client, protocol-agnostic, budget-dry-run, cli-integration, x402_mock)
- `fetch/tests/{,fixtures}/.gitkeep` — test scaffold
- `analysis/pyproject.toml` — Python project metadata + 5 required pins
- `analysis/uv.lock` — 24 packages resolved against Python 3.13.5
- `analysis/src/abrigo_x402/__init__.py` — Phase-2 entry stub
- `.env.example` — PRIVATE_KEY / CELO_RPC_URL / BASE_SEPOLIA_RPC_URL / BLOCKSCOUT_API_KEY / GRAPH_API_KEY
- `scripts/schema_probe.sh` (executable) — schema-frozen probe; returns PROBE_PASS
- `notes/forno_head_snapshot.json` — `{head: 67896653, snapshotted_at: 2026-05-26T11:01:00Z}`
- `.planning/phases/01-l1-.../01-00-x402-exports.txt` — load-bearing exports inventory for Plan 01-07

### Modified
- `package.json` — re-scoped from hand-prototyped Graph deps (now in fetch/) to workspace meta + shared devDeps (typescript@6, tsx, vitest@4.1.7, biome, @types/node)
- `.gitignore` — anchored Foundry `/out/` `/cache/` `/broadcast/` to root (was masking `fetch/src/cache/`); added `data/raw/` allow-list pattern
- `Makefile` — appended Phase-1 targets (fetch-ichi, lint-artifacts, verify-cache-idempotency, schema-probe); REPLACED Phase-0 stub leak-check with full Phase-1 three-class gate

## Decisions Made

Documented in frontmatter `key-decisions`. Summary:

1. **Foundry-anchored gitignore.** Pre-existing `cache/` rule was masking `fetch/src/cache/`. Anchoring `/out/`, `/cache/`, `/broadcast/` to repo root keeps Foundry-cache ignored without shadowing workspace dirs. Rule 1 (Bug).
2. **`tsconfig.json` include narrowed to `src/**/*`.** The plan's draft `include: ["src/**/*", "tests/**/*", "vitest.config.ts"]` conflicts with `rootDir: "src"` (TS6059). Per plan frontmatter `key_links` the `rootDir + include` pattern with `"rootDir": "src"` is load-bearing, so I narrowed `include` to keep rootDir intact and added explicit `exclude` for tests + vitest.config.ts. Wave 1 may add a separate `tests/tsconfig.json` if tighter type-check is needed.
3. **`fetch/src/index.ts` stub created.** Without at least one file, tsc reports TS18003. The stub is a single `export const FETCH_PHASE = '01-l1-...' as const`. Rule 3 (Blocking).
4. **Extra constants in `fetch/src/constants.ts` (Rule 2).** Plan spec required only `loadFornoHeadSnapshot` + `DRY_RUN_FALLBACK_HEAD`; added `CELO_CHAIN_ID`, `BASE_SEPOLIA_CHAIN_ID`, `CELO_USDT_ADDRESS`, `BASE_SEPOLIA_USDC_ADDRESS` so Wave 1 plans (01-03 freshness wrappers, 01-04 Blockscout client, 01-07 x402 mock) have a single source-of-truth — alternative is N copies of the same hex literal in N modules, which `make leak-check` would later flag as protocol-factory leakage.
5. **Replaced Phase-0 leak-check stub.** The existing Makefile target only scanned for `"ichi"` string and was explicitly labelled "Phase-0/pre-Phase-1 stub". The plan's new gate is a strict superset (3 classes: branches + addrs + fees). Rather than introduce a second `leak-check` target, I replaced the stub. Existing pre-commit hooks do not invoke `leak-check` directly, so no behavioral surprise.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] tsconfig rootDir conflict with include**
- **Found during:** Task 1 (initial tsc run)
- **Issue:** `"include": ["src/**/*", "tests/**/*", "vitest.config.ts"]` conflicts with `"rootDir": "src"` — TS6059: "File 'vitest.config.ts' is not under 'rootDir' '.../fetch/src'"
- **Fix:** Narrowed `include` to `["src/**/*"]`; added explicit `exclude` for `node_modules`, `dist`, `tests`, `vitest.config.ts`. Preserved `rootDir: "src"` (load-bearing per plan frontmatter key_links pattern).
- **Files modified:** `fetch/tsconfig.json`
- **Verification:** `pnpm -C fetch exec tsc --noEmit` exits 0.
- **Committed in:** `c46cbb7` (Task 1 commit)

**2. [Rule 3 - Blocking] Empty src/ directory triggers TS18003**
- **Found during:** Task 1 (post-tsconfig-fix tsc run)
- **Issue:** With `include: ["src/**/*"]` and only `.gitkeep` in src/, tsc reports TS18003 "No inputs were found in config file".
- **Fix:** Created `fetch/src/index.ts` with a single substantive const export (`FETCH_PHASE`). Doubles as the Wave-1 barrel file that downstream modules re-export through.
- **Files modified:** `fetch/src/index.ts` (created)
- **Verification:** `pnpm -C fetch exec tsc --noEmit` exits 0.
- **Committed in:** `c46cbb7` (Task 1 commit)

**3. [Rule 1 - Bug] .gitignore Foundry rules masked fetch/src/cache/**
- **Found during:** Task 4 (`git add fetch/src/cache/.gitkeep`)
- **Issue:** Pre-existing top-level `cache/` ignore rule (Foundry/forge build dir) is unanchored — it matches any `cache/` subdirectory including `fetch/src/cache/`. `git add` rejected the .gitkeep file.
- **Fix:** Anchored `out/`, `cache/`, `broadcast/` to repo root as `/out/`, `/cache/`, `/broadcast/`. Foundry's build dirs are always top-level, so this preserves the original intent while unmasking workspace subdirs.
- **Files modified:** `.gitignore`
- **Verification:** `git add fetch/src/cache/.gitkeep` succeeds. `git check-ignore /cache` still reports `/cache` ignored at repo root.
- **Committed in:** `36dc615` (Task 4 commit)

**4. [Rule 2 - Missing Critical] Additional constants for Wave 1 single-source-of-truth**
- **Found during:** Task 4 (writing fetch/src/constants.ts)
- **Issue:** Plan spec required only `loadFornoHeadSnapshot` + `DRY_RUN_FALLBACK_HEAD`. Wave 1 plans (01-03 freshness, 01-04 Blockscout, 01-07 x402 mock) ALL need `CELO_CHAIN_ID=42220`, `BASE_SEPOLIA_CHAIN_ID=84532`, the canonical Celo USDT address per `_schema.toml`, and the Base Sepolia USDC address. Distributing these across N modules creates a leak vector that `make leak-check` would flag.
- **Fix:** Added 4 `as const` exports to `fetch/src/constants.ts`. Canonical USDT is read directly from `protocols/_schema.toml [schema_documentation] canonical_celo_usdt`.
- **Files modified:** `fetch/src/constants.ts`
- **Verification:** tsc clean; `make leak-check` PASS.
- **Committed in:** `36dc615` (Task 4 commit)

**5. [Rule 1 - Bug] Replaced Phase-0 leak-check stub rather than appending**
- **Found during:** Task 3 (Makefile edit)
- **Issue:** Existing `leak-check` Makefile target was explicitly labelled "Phase-0/pre-Phase-1 stub" and only scanned for `"ichi"` string. Plan Task 3 specified a 3-class gate (protocol-name branches + factory addresses + magic fees) as a strict superset of the stub.
- **Fix:** Replaced the stub block with the new gate. `.PHONY: leak-check` declaration preserved (now alongside new Phase-1 phony targets).
- **Files modified:** `Makefile`
- **Verification:** `make leak-check` returns "PASS: leak-check clean"; no pre-commit hook invokes `leak-check` directly (verified by `grep leak-check .pre-commit-config.yaml scripts/pre-commit/*.sh` returning no matches), so no behavioral surprise.
- **Committed in:** `eaf7de3` (Task 3 commit)

---

**Total deviations:** 5 auto-fixed (2 bug, 1 missing critical, 1 blocking, 1 design clarification absorbed as Rule 1)
**Impact on plan:** All auto-fixes load-bearing for correctness or for Wave 1 unblocking. No scope creep — every deviation maps to an explicit Wave 1 dependency on this plan's output.

## Issues Encountered

- **Initial `pnpm install` peer-dep warnings on `@graphprotocol/client-cli@3.0.7`** — expected per STACK.md ("21 months stale; build-only role; do NOT use for runtime queries"). The mismatches are entirely inside the `client-cli` build-tool tree (`@graphql-mesh/*` versions). No runtime path imports `client-cli`. Documented in commit message of `c46cbb7`.
- **`pnpm` reported "Ignored build scripts: esbuild@0.28.0, node-libcurl@4.1.0"** — these are transitive dev-tool builds (esbuild is bundled into vitest/tsx; node-libcurl is bundled into the @graphql-mesh tree). The default-ignore behavior under pnpm 10 is the correct security posture for a fresh clone; no action needed. If a Wave 1 plan needs them, it can run `pnpm approve-builds`.

## Authentication Gates

None — no external auth was required. The Graph API key + Base Sepolia faucet wallet are documented in `.env.example` but Phase 1 does not exercise them until Plan 01-07 (x402 mock) and the deferred Graph subgraph leg.

## User Setup Required

None. `.env.example` documents env vars that will be required by Wave 1 plans (`PRIVATE_KEY` for Plan 01-07 x402 mock; `GRAPH_API_KEY` if subgraph leg is enabled in Phase 1.5). No external services configured at Plan 01-00.

## Next Phase Readiness

**Wave 1 unblocked.** Every gate listed in the wave-context section of the prompt has been delivered:

- pnpm workspace bootstraps cleanly from `rm -rf node_modules pnpm-lock.yaml && pnpm install`
- `pnpm -C fetch exec tsc --noEmit` exits 0
- `analysis/uv.lock` pins the 5 Phase-1 Python packages
- `notes/forno_head_snapshot.json` provides deterministic dry-run head (Plan 01-06)
- `.planning/phases/01-l1-.../01-00-x402-exports.txt` resolves x402-export ambiguity (Plan 01-07)
- `fetch/src/constants.ts` exports `DRY_RUN_FALLBACK_HEAD` + chain IDs + canonical token addresses (Wave 1 single-source-of-truth)
- `Makefile` has `fetch-ichi`, `lint-artifacts`, `verify-cache-idempotency`, `schema-probe`, `leak-check` targets
- `make schema-probe` returns PROBE_PASS (Plan 01-05 can defer `[subgraphs.uniswap_v3]` to Phase 1.5 retroactive enrichment)

**No blockers.** Subgraph downgrade path remains pre-registered: if Plan 01-04 / Plan 01-05 cannot obtain a Graph API key, Blockscout-only is the canonical fallback per CONTEXT.md and RESEARCH.md.

**Watch items for Wave 1:**
- `@graphprotocol/client-cli@3.0.7` peer-dep mismatches are tolerated because it's a build-only dep. If any Wave 1 plan attempts to import `@graphprotocol/client-cli` at runtime, STACK.md drift flag fires.
- AF-10 fixture (`tests/fixtures/af_10_dune_plus/.env.violating`) remains parked as `env_violating_parked.txt` for Phase 1 duration — the orchestrator restores at end of Phase 1.

## Self-Check: PASSED

All 36 claimed files exist on disk; all 4 task commits (`c46cbb7`, `682ca13`, `eaf7de3`, `36dc615`) verified in `git log --oneline --all`.

---
*Phase: 01-l1-data-fetch-skeleton-free-tier-discipline*
*Completed: 2026-05-26*
