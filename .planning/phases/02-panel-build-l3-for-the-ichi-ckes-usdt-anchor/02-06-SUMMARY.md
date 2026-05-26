---
phase: 02-panel-build-l3-for-the-ichi-ckes-usdt-anchor
plan: 06
subsystem: panel-build-fx-snap
tags: [mento, broker, viem, readContract, blockNumber, polars, join_asof, forward_fill, USDT, usdt-usd-separate, fx-snap, PANEL-03]

# Dependency graph
requires:
  - phase: 02-00
    provides: scaffold for fetch/src/mento/historical-rate.ts + analysis/src/abrigo_x402/fx_snap.py + cKES↔USDm exchangeId fixture (mento_cKES_USDm_exchange_id.json)
  - phase: 01-02
    provides: cost-ledger schema (endpoint='forno', uncapped per DEMAND-01)
  - phase: 01-01
    provides: celoClient PublicClient singleton via fetch/src/viem-clients.ts
provides:
  - Mento Broker historical-block FX snap (raw viem.readContract with blockNumber threaded, bypassing SDK 3.2.8 QuoteService head-only quote)
  - JSONL sidecar writer with per-block dedup + revert handling (method='unavailable' on Broker revert)
  - Python polars asof-join + forward-fill (sidecar 'unavailable' rows excluded before join so fill takes most recent 'exact')
  - USDT/USD-as-separate-column commitment (default '1.0' + method='stipulated'; CLAUDE.md non-negotiable)
  - notes/fx_snap_decision.md PANEL-03 deliverable documenting 4 alternatives + Mento broker rationale
affects: [02-08 panel assembly, 03 demand-window fits, 04 USDT-depeg sensitivity, 05 reproducibility manifest]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Raw viem.readContract({ blockNumber: BigInt(N) }) per-block-threaded historical query — bypasses Mento SDK 3.2.8 QuoteService head-only quote (Pitfall 1)"
    - "JSONL sidecar with method enum ('exact' | 'unavailable') written by TS, downstream Python adds 'forward_fill' via polars.join_asof"
    - "polars.DataFrame.join_asof(strategy='backward') with pre-filter to method=='exact' rows so forward-fill skips reverted Broker quotes"
    - "USDT/USD as separate panel column with method='stipulated' default — never collapsed to 1.0 implicitly"

key-files:
  created:
    - notes/fx_snap_decision.md
    - analysis/tests/test_fx_snap.py
  modified:
    - fetch/src/mento/historical-rate.ts
    - fetch/tests/mento-historical-rate.test.ts
    - analysis/src/abrigo_x402/fx_snap.py

key-decisions:
  - "Chose raw viem.readContract({ blockNumber }) over Mento SDK 3.2.8 QuoteService — SDK silently queries head (RESEARCH §B + Pitfall 1)"
  - "USDT/USD as separate column with default '1.0' + method='stipulated' — NEVER collapsed (CLAUDE.md non-negotiable for Phase 4 USDT-depeg sensitivity)"
  - "Sidecar rows with method='unavailable' EXCLUDED before polars join_asof so forward-fill picks the most recent 'exact' rate (not a zero from a reverted Broker quote)"
  - "Rejected alternatives: USDT/USD=1.0 collapse, Chainlink CELO/USD triangulation, Pyth on-Celo, Mento SDK QuoteService — all documented in notes/fx_snap_decision.md"

patterns-established:
  - "blockNumber-threaded readContract pattern is canonical for any historical-block Celo on-chain query (template for Plan 02-04 vault state-snap if it goes historical)"
  - "TS sidecar JSONL + Python polars asof-join + method-enum is the canonical pattern for off-chain↔on-chain rate snapping across the panel"

requirements-completed: [PANEL-03]

# Metrics
duration: 8min
completed: 2026-05-26
---

# Phase 02 Plan 06: Mento Broker Historical-Block FX Snap (PANEL-03) Summary

**Per-event Mento Broker mid-rate snap via raw viem.readContract({ blockNumber }) (bypassing SDK 3.2.8 QuoteService head-only quote) + polars asof-join forward-fill in Python + USDT/USD-as-separate-column non-negotiable**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-05-26T17:24:00Z
- **Completed:** 2026-05-26T17:28:39Z
- **Tasks:** 2 (each TDD: RED + GREEN commits)
- **Files modified:** 5

## Accomplishments

- TS sidecar `fetch/src/mento/historical-rate.ts` calls Broker.getAmountOut(BiPoolManager, exchangeId, cKES, USDm, 1e18) via raw viem.readContract with `blockNumber: BigInt(block)` threaded per call (RESEARCH §B + Pitfall 1 mitigated — Mento SDK 3.2.8 QuoteService silently queries head)
- Per-block dedup + sorted output; revert handling marks method='unavailable' with rate='0'; downstream Python forward-fills from most recent prior 'exact' row
- JSONL sidecar writer (one row per block) at `outputPath` with Blockscout block-URL provenance
- Cost-ledger append per readContract call: endpoint='forno', chain='celo', cost_usdc='0', paid_real=false (DEMAND-01 uncapped)
- Python `attach_rates()` uses `polars.DataFrame.join_asof(strategy='backward')` after pre-filtering sidecar to `method=='exact'` rows so forward-fill skips Broker reverts
- USDT/USD column always present: `usdt_usd_rate='1.0'`, `usdt_usd_method='stipulated'` (Phase 4 may overwrite with depeg-event data)
- `notes/fx_snap_decision.md` documents all 4 alternatives + rationale (USDT/USD=1.0 collapse REJECTED, Chainlink CELO/USD REJECTED, Pyth on-Celo REJECTED, Mento SDK QuoteService REJECTED for historical queries)

## Task Commits

Each task TDD-committed atomically:

1. **Task 1 RED: TS sidecar failing tests** — `8afcbd9` (test) — 8 vitest tests for snapFxBlocks: per-block dedup, blockNumber threading (Pitfall 1), exact/unavailable methods, JSONL sidecar shape, broker argument tuple
2. **Task 1 GREEN: TS sidecar implementation** — `561707a` (feat) — snapFxBlocks() with raw viem.readContract per-block; revert handling; cost-ledger append; JSONL writer
3. **Task 2 RED: Python fx_snap failing tests** — `0d5a2be` (test) — 7 pytest tests: enum, load, exact asof, forward-fill, pre-window unavailable, USDT/USD-separate non-negotiable
4. **Task 2 GREEN: Python fx_snap + decision notes** — `5e19d07` (feat) — load_fx_sidecar + attach_rates with polars join_asof + USDT/USD separate column + notes/fx_snap_decision.md

**Plan metadata:** _to be appended in final-commit step_

## Files Created/Modified

- `fetch/src/mento/historical-rate.ts` (MODIFIED) — Implementation body added; per-block readContract with blockNumber threaded; JSONL writer; cost-ledger append
- `fetch/tests/mento-historical-rate.test.ts` (MODIFIED) — 8 vitest tests (replaced 5 it.todo + 2 import smoke + 1 ABI sanity)
- `analysis/src/abrigo_x402/fx_snap.py` (MODIFIED) — load_fx_sidecar + attach_rates implemented; polars join_asof(strategy='backward'); USDT/USD column always present
- `analysis/tests/test_fx_snap.py` (CREATED) — 7 pytest tests
- `notes/fx_snap_decision.md` (CREATED) — PANEL-03 deliverable: 4 alternatives + Mento broker rationale + USDT/USD column commitment + forward-fill semantics

## Decisions Made

- **Raw viem.readContract over SDK QuoteService**: Mento SDK 3.2.8's QuoteService does NOT accept blockNumber. For per-event historical snap we MUST use raw `viem.readContract({ blockNumber: BigInt(N) })` against the Broker contract directly. Hand-supplied `parseAbi(['function getAmountOut(...)'])` because SDK's bundled BROKER_ABI is incomplete (tradingLimits-only).
- **Pre-filter to method='exact' before asof join**: If 'unavailable' sidecar rows were left in the join, polars would pick up `rate_x1e18='0'` as the most recent quote at a block where the Broker reverted. Filtering BEFORE the join makes forward-fill skip 'unavailable' and land on the most recent 'exact' row, preserving the provenance signal.
- **USDT/USD as separate column with stipulated method**: CLAUDE.md non-negotiable. Default `'1.0'` with `method='stipulated'` so Phase 4 can swap in USDT-depeg data without touching Phase 2 panel construction. Column existence is the structural commitment; default value is not.
- **rate_x1e18 stays a String, not polars Decimal**: polars Decimal is not yet round-trip stable for >38-digit uint256 values. Decimal-string preserves precision across the TS↔Python boundary.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Adapted cost-ledger appendLedger row shape to actual schema**
- **Found during:** Task 1 GREEN (TS sidecar implementation)
- **Issue:** Plan body called `appendLedger({ts, endpoint, chain, usdc_cost, paid_real, blocks_queried, request_id})` but the real `CostLedgerRowSchema` (Plan 01-02, `fetch/src/cost-ledger.ts`) requires `{timestamp, endpoint, query_id, cost_usdc, paid_real, tx_hash, chain, response_bytes, response_sha256, fetch_id}`. The plan-body shape would fail zod validation at runtime.
- **Fix:** Mapped fields to the real schema: `timestamp = new Date().toISOString()`, `query_id = mento-fx-<block>-<exchangeId[0:10]>`, `cost_usdc = '0'`, `tx_hash = null`, `chain = 'celo'`, `response_bytes = rate_x1e18.length`, `response_sha256 = sha256(rate_x1e18)`, `fetch_id = query_id`. endpoint='forno' invariant preserved.
- **Files modified:** fetch/src/mento/historical-rate.ts
- **Verification:** All 8 vitest tests pass including the dedup test that triggers multiple appendLedger calls; full Phase 1+2 fetch suite remained at 96/96
- **Committed in:** 561707a (Task 1 GREEN commit)

**2. [Rule 3 - Blocking] Per-test ephemeral tmpdir for JSONL sidecar**
- **Found during:** Task 1 RED test setup
- **Issue:** Plan body used a single `TMP` constant at file scope (`join(tmpdir(), 'fx_snap_test.jsonl')`). Multiple beforeEach()-resets across 6 tests could leave stale state if any test leaked.
- **Fix:** Replaced with per-test `mkdtempSync(tmpdir + 'fx_snap_test_')` so each test gets a fresh isolated directory. Cleaner test isolation, no shared-state risk.
- **Files modified:** fetch/tests/mento-historical-rate.test.ts
- **Verification:** 8/8 tests pass
- **Committed in:** 8afcbd9 (Task 1 RED commit)

**3. [Rule 2 - Missing critical] Added 8th test verifying exact Broker call arguments**
- **Found during:** Task 1 RED authoring
- **Issue:** Plan body 5 tests + 1 address sanity = 6 tests. None of them asserted the full `args` tuple passed to `readContract` (BiPoolManager, exchangeId, cKES, USDm, 1e18 in that order). A future regression that reordered tokenIn/tokenOut would not be caught.
- **Fix:** Added "passes correct args to broker getAmountOut" test asserting `args[0..4]` matches BiPoolManager+exchangeId+cKES+USDm+1e18 verbatim. Caught the load-bearing tuple contract that the plan's acceptance grep only verified at the ABI-fragment level.
- **Files modified:** fetch/tests/mento-historical-rate.test.ts
- **Verification:** 8/8 tests pass
- **Committed in:** 8afcbd9 (Task 1 RED commit)

---

**Total deviations:** 3 auto-fixed (1 bug — schema-shape mismatch, 1 blocking — test isolation, 1 missing critical — argument tuple test)
**Impact on plan:** All auto-fixes necessary for correctness. No scope creep. Deviation 1 was load-bearing — the plan-body cost-ledger shape would have crashed at runtime; aligning to the actual zod-validated schema preserves DEMAND-01 audit-trail invariant.

## Issues Encountered

None — both Task 1 and Task 2 reached GREEN on first implementation pass after RED commits.

## Self-Check: PASSED

- `fetch/src/mento/historical-rate.ts` exists; modified contents present
- `fetch/tests/mento-historical-rate.test.ts` exists; 8 tests defined
- `analysis/src/abrigo_x402/fx_snap.py` exists; load_fx_sidecar + attach_rates implemented
- `analysis/tests/test_fx_snap.py` exists; 7 tests defined
- `notes/fx_snap_decision.md` exists; all 4 alternatives documented
- Commit 8afcbd9 present in git log
- Commit 561707a present in git log
- Commit 0d5a2be present in git log
- Commit 5e19d07 present in git log
- `pnpm -C fetch test tests/mento-historical-rate.test.ts --run` → 8/8 pass
- `cd analysis && uv run pytest tests/test_fx_snap.py -x -q` → 7/7 pass
- `pnpm -C fetch exec tsc --noEmit` → exit 0
- Full Phase 1+2 fetch suite: 96/96 pass; analysis suite: 61/61 + 1 skipped (pre-existing phantom_filter real-fixture skip per Plan 02-00 fallback)

## User Setup Required

None — no external service configuration required. Phase 2 default operates entirely offline against the JSONL sidecar; Phase 5 may add a Forno-live retake task to repopulate the sidecar before the PDF deliverable.

## Next Phase Readiness

- PANEL-03 deliverable complete; FX snap module ready for Plan 02-08 panel assembly to call `attach_rates(panel_df, load_fx_sidecar(path))`
- TS sidecar ready for Phase 2 live-Forno retake (operator runs `tsx fetch/src/mento/historical-rate.ts` against a deduped block list once panel events are gathered in Plan 02-08)
- Forward-fill enum committed for PRE_REGISTRATION; Phase 3 NHPP fit can consume `fx_method` column without enum drift
- Phase 4 USDT-depeg sensitivity has its load-bearing structural commitment in place (usdt_usd_rate/usdt_usd_method columns always present); Phase 4 will overwrite specific rows with depeg-event rates without touching Phase 2

---
*Phase: 02-panel-build-l3-for-the-ichi-ckes-usdt-anchor*
*Plan: 06*
*Completed: 2026-05-26*
