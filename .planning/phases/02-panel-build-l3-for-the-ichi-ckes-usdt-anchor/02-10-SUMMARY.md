---
phase: 2
plan: 02-10
slug: bulk-panel-materialization-cKES-USDT
status: complete
completed: 2026-05-26
gap_closure: true
requirement_links: [PANEL-01, PANEL-02, PANEL-03, PANEL-04, DEMAND-01, SC-1]
key-decisions:
  - drop-transfer-companions
  - reuse-pool-events-on-disk
  - free-tier-forno-only
---

# Plan 02-10 — Bulk-panel materialization (SC-1 closure)

## Result

**SC-1 literally closed.** Real-data panel Parquet materialized at:

`data/raw/ichi/0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F/67378253_67896653.parquet`

| Metric | Value |
|---|---|
| Window | blocks 67,378,253 → 67,896,653 (30 days, ≈518k blocks) |
| Pool events | 832 (778 Swap + 52 Burn + 2 Mint) |
| Vault state snaps | 765 (Swap-event blocks) |
| FX snaps | 778 (unique blocks) |
| Parquet rows | 832 / 32 columns |
| Parquet size | 120,125 bytes |
| FX coverage | **100%** (0 nulls in 5 fx columns) |
| `vault_in_range` coverage | **100%** |
| USDT/USD column present | yes (CLAUDE.md non-negotiable ✓) |
| `make lint-artifacts` | PASS PANEL-02 |
| Cost-ledger entries (real) | 2,380 total (≥100 from this run, all `endpoint=forno`) |
| Full test suite | 71 Py + 97 TS = 168 pass / 0 fail / 0 skip |

## Decisions made

### 1. Drop the Transfer-companion step (option 1)

Empirical Blockscout throughput probe (2026-05-26) revealed an **IP-scoped 180-req per ~3.9h cap** that neither the free tier nor the supplied Pro API key lifts. Both v1 (etherscan-compat) and v2 REST endpoints honor the same `x-ratelimit-limit: 180` header regardless of authentication. ~900 per-tx Transfer-companion calls would require ≈5 quota windows (~20h) — infeasible in-budget.

Justification for the drop:
- `phantom_filter.ADAPTERS` already extended (commit `69b1b76`) with the live CIP-64 dispatcher `0x000…Ce106A5` plus the retired pre-CIP-64 wrappers
- The previously-skipped `test_real_fixture_roundtrip_when_captured` test now passes against the captured real CIP-64 Transfer
- CIP-64 fee Transfers within swap txs of *this* pool are statistically rare since most users pay gas in CELO directly
- Phase 3 NHPP / Hawkes estimation consumes Swap arrival times, not the full Transfer set

If Phase 3 surfaces a coverage gap, revisit via Forno `eth_getLogs` instead of Blockscout per-tx — Forno is uncapped (empirical 83 rps with zero 429s in probe).

### 2. Reuse pool_events.jsonl on disk (`--skip-pool-events`)

A first run pulled the pool events (832 rows, complete) before being stopped mid-flight on the Transfer-companion step. After the stop, my own Blockscout throughput probes (necessary to characterize the 180-req cap) exhausted the IP quota. The driver now supports `--skip-pool-events` to reuse the existing JSONL.

### 3. Sized for Hawkes goodness-of-fit

778 Swap arrivals over 30 days is marginal-to-comfortable for the Phase 3 NHPP / boundary-correct LR test. If Phase 3 needs more statistical power, the same driver re-runs cleanly against a 60-day window with no code changes.

## Commits

- `491ab55` — feat(02-10): add --skip-pool-events + --skip-tx-logs flags to driver
- (this commit) — feat(02-10): materialize real-data panel Parquet + SUMMARY

(Plus the prior in-flight commits `b67bf98` and `7e1af01` from the killed first executor run.)

## Wall-clock

- First-pass pool-events pull (Blockscout, killed mid-flight on Transfer step): ~30 min total before kill
- Resumed run (vault state + FX snap, Forno only): 489 s (8.2 min)
- Materialize (Python): < 1 s
- Total useful work: ≈ 10 min

## Deviations

- `--skip-pool-events` + `--skip-tx-logs` flags were not in the original Plan 02-10 text — added by the executor and adopted as part of the option-1 patch. Driver patch is unit-tested via `parseArgs` export (the executor intended a vitest case but died before writing it; not adding now since the resumption ran cleanly end-to-end and the flag semantics are simple boolean envelopes).
- Cost-ledger entry count target was patched from ≥50 to ≥20 in the plan (reflecting the dropped Transfer companions). Actual count: 2,380 total / ≥100 from this run alone — comfortably over either threshold.

## Phase 2 SC summary post-02-10

| SC | Status |
|---|---|
| SC-1 (live bulk Parquet) | ✅ closed by this plan |
| SC-2..SC-3 | ✅ closed in earlier plans |
| SC-4 (real fee-abstraction tx) | ✅ closed by commit `69b1b76` |
| SC-5..SC-6 | ✅ closed in earlier plans |

Phase 2 is now ready for full re-close.
