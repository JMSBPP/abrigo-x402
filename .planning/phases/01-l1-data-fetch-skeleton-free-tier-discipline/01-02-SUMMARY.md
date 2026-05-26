---
phase: 01-l1-data-fetch-skeleton-free-tier-discipline
plan: 02
subsystem: fetch
tags: [cost-ledger, jsonl, budget-gate, free-tier, fetch-02, graph-mainnet]

requires:
  - phase: 01-l1-data-fetch-skeleton-free-tier-discipline
    plan: 00
    provides: "pnpm workspace + fetch/ TS scaffold; fetch/package.json pinned zod@4.4.3; tsc clean baseline"

provides:
  - "fetch/src/cost-ledger.ts exports: appendLedger(row, path?), readLedger(path?), checkBudget(opts), GraphBudgetExceededError, CostLedgerRow (zod schema + type), Endpoint enum, Chain enum"
  - "Endpoint enum: graph-mainnet | graph-sepolia | blockscout | forno | x402-mock-sepolia (CONTEXT.md FETCH-02 cost-ledger schema)"
  - "90k/mo Graph soft cap: counts only endpoint='graph-mainnet' rows in current UTC month; blockscout/forno/x402-mock-sepolia/graph-sepolia rows uncapped"
  - "--force override via checkBudget({force: true}) — returns {would_exceed: true} without throwing, lets caller decide policy"
  - "JSONL on-disk format: one JSON object per line; atomic append via fs.appendFile (POSIX <PIPE_BUF guarantees no interleave)"
  - "Default ledger path: data/raw/_cost_ledger.jsonl (auto-creates parent dir on first append)"
  - "Default cap: 90_000 graph-mainnet queries per UTC month (overridable via checkBudget({cap}))"

affects:
  - "01-06-PLAN.md (CLI integration): consumes checkBudget + appendLedger; surfaces --force flag"
  - "01-07-PLAN.md (x402 mock test): logs paid_real=false x402-mock-sepolia rows via appendLedger"
  - "01-04-PLAN.md (Blockscout client + cache): emits blockscout rows via appendLedger (uncapped)"
  - "Phase 2 panel build: cold-backfill budget envelope (30k cold + 15k incremental + 45k reserve from CONTEXT.md) consumed via checkBudget at fetch entry"

tech-stack:
  added: []
  patterns:
    - "Append-only JSONL with fs.appendFile — atomic per-line; auto-parent-dir creation; readLedger handles missing-file as empty array"
    - "zod schema mirrors disk format: every row read via CostLedgerRowSchema.parse(JSON.parse(line)), so disk corruption surfaces as ZodError at read time, not as silent NaN propagation"
    - "Month-boundary handling via Date.UTC(year, monthIdx, 1).toISOString() — explicit construction prevents setUTCMonth(-1) ambiguity (M12 fix)"
    - "Day-15 clamp in test fixtures: graphRow(i, monthOffset) uses day=15 to avoid month-overflow normalization landing back in the current month (Jan 31 -1mo would resolve to Dec 31 same year unless year-adjusted; using day=15 stays within target month)"

key-files:
  created:
    - "fetch/src/cost-ledger.ts (179 lines) — append+read+checkBudget"
  modified:
    - "fetch/tests/cost-ledger.test.ts — replaced describe.todo stub with 9 real tests (4 append/read + 5 budget-gate)"
    - ".gitignore — added fetch/data/ ignore (vitest cwd resolves test paths to fetch/data/)"
  removed:
    - "fetch/src/cost-ledger/.gitkeep + directory — plan spec is a single file (cost-ledger.ts), not a barrel module"

key-decisions:
  - "JSONL not Parquet (Phase 1) — orchestrator finding #5: hyparquet-writer's small-write profile adds binary-format risk without empirical benefit at Phase 1 volumes (~few k rows/month). fs.appendFile is POSIX-atomic for <PIPE_BUF (4096B) payloads; one ledger row JSON-encoded is ~300-400B. Phase 2 / Phase 5 may batch-convert to Parquet via polars if ledger grows past ~10M rows."
  - "checkBudget + GraphBudgetExceededError bundled into the same file as append/read (NOT split across Task 1/Task 2). Rationale: schema/enum constants are single-source-of-truth; splitting into two files would either duplicate the Endpoint enum or create a circular import. Atomic commits still separate (RED+GREEN per task)."
  - "Default cap = 90_000 (not 100_000). The Graph free tier is 100k/mo per API key; CONTEXT.md FETCH-02 sets the soft cap at 90k to leave 10k headroom for one-off interactive queries that don't go through the cost-ledger gate (researcher ad-hoc Subgraph Studio probes during Wave 1.5 enrichment per RESEARCH §A recommendation)."
  - "Day-15 clamp in graphRow test helper. Initial design used now.getUTCDate() but May 31 + monthOffset=-1 normalizes to May 1 (April 31 → May 1), landing BACK in the current month and breaking the 'last-month' assertion. Day=15 is far enough from month boundaries that any monthOffset resolves within the intended month."

patterns-established:
  - "Cost-ledger row schema is the contract surface for all paid-fetch logging across endpoints (graph + blockscout + forno + x402-mock). Every endpoint module in Wave 1/2 imports CostLedgerRow + appendLedger from cost-ledger.ts — no per-endpoint ledger types."
  - "Budget gate is endpoint-scoped (graph-mainnet only). Adding new capped endpoints in a future iteration requires extending checkBudget's filter predicate (currently `r.endpoint === 'graph-mainnet'`), NOT introducing a parallel ledger schema."

requirements-completed: [FETCH-02]

duration: 3min
completed: 2026-05-26
---

# Phase 1 Plan 02: Cost-Ledger JSONL + 90k Graph Budget Gate Summary

**Append-only JSONL cost-ledger module with per-endpoint accounting and the 90k/mo Graph-mainnet soft cap — the load-bearing FETCH-02 free-tier discipline gate for every paid fetch in Phase 2+.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-05-26T13:42:48Z
- **Completed:** 2026-05-26T13:46:00Z
- **Tasks:** 2 (TDD: RED → GREEN per task)
- **Files modified:** 4 (1 created + 2 modified + 1 dir removed)

## Accomplishments

- `fetch/src/cost-ledger.ts` lands with three exported functions + 1 error class + 2 enums + 1 row schema (179 lines)
- 9 vitest assertions pass: 4 append/read round-trip + 5 budget-gate
- 90k/mo cap fires only on `endpoint='graph-mainnet'` rows in the current UTC month; blockscout/forno/x402-mock-sepolia/graph-sepolia rows are logged but uncapped
- `--force` override is observable: `checkBudget({force: true})` returns `{would_exceed: true}` without throwing, letting the CLI surface a user-acknowledged budget-burn warning instead of aborting
- Month-boundary test asserts the UTC reset semantics: 50k graph-mainnet rows from last month + 50k projected for this month passes (`current=0` because the filter scopes to `timestamp >= monthStart`)
- `pnpm -C fetch tsc --noEmit` exits 0
- Pre-commit hooks (af_lint, review_trail, schema_frozen) PASS on all 3 task commits

## Task Commits

Each TDD step committed atomically with `(01-02)` scope:

1. **Task 1 RED — failing append+read tests** — `b951b22` (test)
2. **Task 1 GREEN — cost-ledger.ts implementation (append + read + checkBudget)** — `e569d2f` (feat)
3. **Task 2 — 90k budget-gate tests + .gitignore fix** — `729a17e` (test)

**Plan metadata commit:** appended at end of execution.

## Files Created/Modified

### Created
- `fetch/src/cost-ledger.ts` — append-only JSONL writer + reader + 90k Graph-mainnet budget gate (179 lines)

### Modified
- `fetch/tests/cost-ledger.test.ts` — replaced Plan 01-00's `describe.todo` stub with 9 real tests (4 append/read + 5 budget-gate)
- `.gitignore` — added `fetch/data/` ignore (vitest cwd resolves test paths to `fetch/data/raw/` not repo-root `data/raw/`)

### Removed
- `fetch/src/cost-ledger/.gitkeep` + parent directory — Plan 01-00 scaffolded `cost-ledger/` as a barrel-module-ready directory; Plan 01-02 spec is a single `cost-ledger.ts` file, so the empty subdir was removed to prevent ambiguous ESM resolution (`import '../src/cost-ledger'` could otherwise resolve to either `.ts` file OR `/index.ts`)

## Decisions Made

Documented in frontmatter `key-decisions`. Summary:

1. **JSONL not Parquet at Phase 1.** Orchestrator finding #5: `fs.appendFile` of one line at a time is POSIX-atomic for payloads under `PIPE_BUF` (~4KB); a JSON-encoded ledger row is ~300-400 bytes, well within the guarantee. `hyparquet-writer`'s small-write profile (binary-format buffering, schema-evolution complexity) adds risk without empirical benefit at Phase 1 row counts. Phase 2 / Phase 5 may batch-convert via polars if the ledger grows past ~10M rows.

2. **`checkBudget` bundled into `cost-ledger.ts` (not split into a `budget.ts`).** Plan defines two "tasks" but they share the `Endpoint` enum, the schema, and the on-disk format. Splitting would either duplicate the enum (drift risk) or force a circular import. Atomic commits per task are preserved (RED+GREEN per task = 3 commits total).

3. **Default cap = 90,000 (not 100,000).** The Graph free tier is 100k/mo per API key; CONTEXT.md FETCH-02 sets the soft cap at 90k to leave 10k headroom for one-off interactive queries (Wave 1.5 subgraph hunt + ad-hoc Subgraph Studio probes) that don't route through the cost-ledger gate.

4. **Day-15 clamp in `graphRow` test helper.** Initial design used `now.getUTCDate()` for the synthetic timestamp's day, but on May 31 + `monthOffset=-1` JS normalizes "April 31" → "May 1", which lands BACK in the current month and breaks the "last-month rows don't count" assertion. Day=15 is far enough from month boundaries that any reasonable `monthOffset` resolves within the intended month.

5. **Removed `fetch/src/cost-ledger/` empty directory.** Plan 01-00 scaffolded it as a barrel-module-ready dir; Plan 01-02 spec uses a single `.ts` file. Keeping the empty dir creates ambiguous ESM resolution semantics (`import '../src/cost-ledger'` could resolve to either path). Rule 3 (Blocking — preempts a Wave 1 import ambiguity).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Empty `cost-ledger/` directory creates ambiguous ESM resolution**
- **Found during:** Task 1 setup
- **Issue:** Plan 01-00 created `fetch/src/cost-ledger/.gitkeep`. Plan 01-02 spec is `fetch/src/cost-ledger.ts` (file). With both present, `import '../src/cost-ledger'` is ambiguous — TypeScript NodeNext might resolve to either the `.ts` file OR a (nonexistent) `/index.ts` inside the dir.
- **Fix:** Removed `fetch/src/cost-ledger/.gitkeep` and the now-empty parent directory.
- **Files modified:** `fetch/src/cost-ledger/.gitkeep` (deleted), `fetch/src/cost-ledger/` (rmdir)
- **Verification:** `pnpm -C fetch exec tsc --noEmit` exits 0; tests import from `'../src/cost-ledger'` resolve unambiguously to `cost-ledger.ts`.
- **Committed in:** `b951b22` (Task 1 RED commit)

**2. [Rule 3 - Blocking] `fetch/data/` not ignored — vitest cwd creates scratch test artifacts**
- **Found during:** Task 2 (post-test-run `git status`)
- **Issue:** Vitest runs with `cwd=fetch/`, so the test helpers' relative paths `data/raw/_cost_ledger.test.jsonl` + `data/raw/_cost_ledger.budget-test.jsonl` resolve to `fetch/data/raw/*` rather than repo-root `data/raw/*`. The existing `.gitignore` rule `data/raw/` is unanchored and matches only at repo root. Test scratch artifacts would otherwise become untracked clutter.
- **Fix:** Added `fetch/data/` rule to `.gitignore` (with comment explaining the vitest cwd). The real production ledger remains at repo-root `data/raw/_cost_ledger.jsonl`, governed by the pre-existing allow-list.
- **Files modified:** `.gitignore`
- **Verification:** `git check-ignore fetch/data/raw/_cost_ledger.test.jsonl` returns the path (ignored); `git status` shows no untracked test artifacts.
- **Committed in:** `729a17e` (Task 2 commit; bundled with the budget tests since both are part of "Task 2 lands cleanly")

---

**Total deviations:** 2 auto-fixed (both Rule 3 — Blocking, both preempt Wave 1 ambiguity / clutter)
**Impact on plan:** No scope creep. Both deviations are housekeeping that the plan should have specified but didn't; neither alters the FETCH-02 contract surface.

## Issues Encountered

- **None.** Both TDD cycles ran cleanly; no test debugging required after GREEN; no tsc errors after the initial Task 1 GREEN commit.

## Authentication Gates

None — Plan 01-02 is pure offline code + tests. No external services touched.

## User Setup Required

None. Plan 01-02 ships a pure-function module + tests. Downstream plans (01-06 CLI, 01-07 x402-mock) will integrate this module without any environment-variable additions.

## Next Phase Readiness

**Wave 1 unblocked for cost-ledger consumers:**

- Plan 01-04 (Blockscout client + cache) may now call `appendLedger({ endpoint: 'blockscout', paid_real: false, ... })` from its fetch wrapper.
- Plan 01-06 (CLI integration) may now call `checkBudget({ projected_graph_queries: estimate, force: argv.force })` before any Graph fetch, and surface the `GraphBudgetExceededError` as a non-zero exit code with the budget snapshot in stderr.
- Plan 01-07 (x402 mock test) may now log `paid_real=false`, `chain='base-sepolia'`, `endpoint='x402-mock-sepolia'` rows for each mock round-trip; rows count toward the audit trail but NOT toward the 90k cap.

**Watch items:**
- The `EndpointEnum` is the contract surface — any new endpoint introduced in a future iteration must extend it AND decide whether to add a new branch to `checkBudget`'s filter predicate (currently `'graph-mainnet'`-only). Single-line change but flag-worthy because it's the gate that prevents free-tier exhaustion.
- The `DEFAULT_LEDGER` path is `data/raw/_cost_ledger.jsonl` (repo-root). If a future plan moves the cost-ledger under a per-iteration directory (e.g., `data/raw/iter1/_cost_ledger.jsonl`), this constant + the `.gitignore` allow-list at lines 44-45 both need updating in lockstep.

## Self-Check: PASSED

- `fetch/src/cost-ledger.ts` exists on disk (179 lines, 4 exports + 1 error class).
- `fetch/tests/cost-ledger.test.ts` exists on disk (205 lines, 9 tests passing).
- `.gitignore` contains `fetch/data/` rule (line 50 area).
- Commits verified in `git log --oneline -10`: `b951b22` (RED), `e569d2f` (GREEN/feat), `729a17e` (Task 2 tests).
- `pnpm -C fetch test tests/cost-ledger.test.ts --run` exits 0 with `9 passed (9)`.
- `pnpm -C fetch exec tsc --noEmit` exits 0.

---
*Phase: 01-l1-data-fetch-skeleton-free-tier-discipline*
*Completed: 2026-05-26*
