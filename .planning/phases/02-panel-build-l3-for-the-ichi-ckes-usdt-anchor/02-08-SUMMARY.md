---
phase: 02-panel-build-l3-for-the-ichi-ckes-usdt-anchor
plan: 08
subsystem: analysis/panel
tags: [panel, e2e, orchestrator, demand-01, phantom-filter, transfer-decoder, q96-fee, fx-snap, parquet-metadata]
requires:
  - 02-01-ingest (load_jsonl, apply_finality_cutoff, DEFAULT_FINALITY_LAG=120)
  - 02-02-decoders (decode_all + Swap/Mint/Burn/Deposit/Withdraw topic0 dispatch)
  - 02-03-phantom-filter (exclude_adapters; USDC/USDT adapter set)
  - 02-04-vault-state (load_vault_state, attach_in_range — left-join + vault_in_range)
  - 02-05-revenue-leg (compute_swap_fee — Q96 Int128 LP-fee math)
  - 02-06-fx-snap (attach_rates — polars join_asof backward; usdt_usd separate column)
  - 02-07-provenance (with_header — polars 1.41 native Parquet metadata)
provides:
  - panel.build_panel orchestrator (Pattern-1 canonical composition)
  - panel.write_panel (thin wrapper over provenance.with_header)
  - panel.assert_no_graph_mainnet_in_ledger (DEMAND-01 enforce helper)
  - decoders.decode_transfer + TRANSFER_TOPIC0 (Rule-3 integration patch)
  - 100-block synthetic fixtures (swaps/vault_state/fx_rates)
affects: [DEMAND-01, PANEL-01, PANEL-02, PANEL-03, PANEL-04]
tech-stack:
  added: []
  patterns:
    - RESEARCH §H Pattern 1 (sequential pipeline with finality_cutoff FIRST per Pitfall 5)
    - Split-and-rejoin: compute_swap_fee on Swap-rows-only; diagonal_relaxed concat
    - vault_liquidity alias from totalSupply (Phase-2 sentinel per RESEARCH §A)
    - polars.read_parquet_metadata round-trip verification of PANEL-02 header
key-files:
  created:
    - analysis/src/abrigo_x402/panel.py (full implementation — replaces Wave-0 NotImplementedError skeleton)
    - analysis/tests/test_panel_e2e.py (9 e2e tests)
    - analysis/tests/fixtures/synthetic_swaps_n100.jsonl (100 events)
    - analysis/tests/fixtures/synthetic_vault_state_n100.jsonl (100 vault states)
    - analysis/tests/fixtures/synthetic_fx_rates_n100.jsonl (10 fx rates)
  modified:
    - analysis/src/abrigo_x402/decoders.py (added TRANSFER_TOPIC0 + decode_transfer)
    - .gitignore (ignore analysis/tests/fixtures/_gen_n100.py one-off generator)
decisions:
  - "Pipeline order MUST be: finality_cutoff FIRST after load (Pitfall 5)"
  - "Swap-only branch through compute_swap_fee (tick/liquidity payload absent on Mint/Burn/Transfer)"
  - "totalSupply → vault_liquidity alias is the Phase-2 vault-share sentinel; precise pool.positions liquidity deferred to Phase 7 conditional on collectFees >1% drift"
  - "Transfer decoder is required by PANEL-04 phantom_filter contract (event_name+from+to columns)"
  - "DEMAND-01 enforce: graph-mainnet rows raise; missing ledger is no-op"
metrics:
  duration_seconds: 273
  duration_min: 4
  tasks_completed: 2
  files_created: 5
  files_modified: 2
  tests_added: 9
  tests_passing_full_suite: 70
  tests_skipped_full_suite: 1
  commits: 3
  completed: "2026-05-26"
---

# Phase 2 Plan 08: panel.py e2e orchestrator + DEMAND-01 enforce Summary

End-to-end Phase-2 orchestrator wiring all Wave 1 modules into the canonical RESEARCH §H Pattern-1 pipeline, with a 100-block synthetic fixture proving the composition produces the expected 97-row panel (100 raw - 3 phantom Transfers), full PANEL-02 metadata header on Parquet output, and a DEMAND-01 enforce helper that fails the build on any `endpoint='graph-mainnet'` row in the cost-ledger.

## What landed

### `analysis/src/abrigo_x402/panel.py` (full implementation)

Replaces the Wave-0 `NotImplementedError("Plan 02-08")` skeleton with:

- **`build_panel(cache_path, fx_sidecar_path, vault_state_sidecar_path, forno_head, protocol_spec) -> pl.DataFrame`** — composes all 8 Wave-1 modules in the strict Pattern-1 order. `apply_finality_cutoff` runs FIRST after `load_jsonl` per Pitfall 5 (volatile-head drop before any join or decode).

- **Split-and-rejoin around `compute_swap_fee`** — Q96 fee math requires Swap-specific payload columns (`tick`, `liquidity`) that are absent on Mint/Burn/Transfer rows. The orchestrator filters to Swap rows, runs the fee computation, then re-concatenates with non-Swap rows via `pl.concat(..., how="diagonal_relaxed")` so fee_token{0,1} + vault_fee_token{0,1} are null on non-Swap rows. `vault_state.attach_in_range` had already joined the vault columns onto every row before the split, so non-Swap rows correctly carry vault metadata.

- **`vault_liquidity` alias** — `revenue_leg.compute_swap_fee` expects a column named `vault_liquidity` (Phase-2 sentinel per RESEARCH §A docstring) but `vault_state.attach_in_range` emits `totalSupply`. The orchestrator aliases `totalSupply` → `vault_liquidity` on the Swap branch immediately before invoking `compute_swap_fee`. Precise `pool.positions(vault, lower, upper).liquidity` computation remains deferred to Phase 7 conditional on a captured `collectFees` cross-check exceeding 1% drift.

- **`write_panel(df, output_path, **metadata) -> Path`** — thin wrapper over `provenance.with_header`. Raises ValueError if any of the 6 PANEL-02 keys (`chainId`, `contractAddress`, `blockRange`, `fetchTimestamp`, `dataHash`, `gitCommit`) is missing.

- **`assert_no_graph_mainnet_in_ledger(ledger_path) -> None`** — DEMAND-01 enforce. Walks the JSONL cost-ledger and raises AssertionError on any row with `endpoint == "graph-mainnet"`. Missing ledger file is a no-op (no ledger = no offending rows). Phase 2 only writes `endpoint='forno'` (vault state reads) or `endpoint='blockscout'` (event log fetches) — any `graph-mainnet` row indicates a 90k/mo soft-cap budget-policy violation.

### `analysis/src/abrigo_x402/decoders.py` (Rule-3 integration patch)

Added `TRANSFER_TOPIC0 = "0xddf252...3b3ef"` (canonical ERC-20 `Transfer(address,address,uint256)` keccak), registered `"Transfer"` in `TOPIC0_TO_EVENT`, and added `decode_transfer(topics, data)` emitting `from`, `to`, `value` columns. This patch is required because `phantom_filter.exclude_adapters` checks `event_name == "Transfer"` and matches against `from` / `to` columns; without the patch, Transfer rows decoded to `event_name='Unknown'` with no `from`/`to`, the `required = {event_name, from, to}` issubset guard in `exclude_adapters` short-circuited, and the 100 → 97 phantom-filter assertion silently failed (`df.height` stayed at 100). See "Deviations" below.

### `analysis/tests/test_panel_e2e.py` (9 tests, all passing)

| # | Test | Asserts |
| - | ---- | ------- |
| 1 | `test_build_panel_row_count` | 100 raw events → 97 rows after phantom-filter |
| 2 | `test_build_panel_schema` | 12 required columns from full pipeline |
| 3 | `test_build_panel_phantom_filtered_out` | zero rows with `to=USDT_FEE_ADAPTER` |
| 4 | `test_write_panel_has_metadata` | 6 PANEL-02 keys present in Parquet footer |
| 5 | `test_build_panel_idempotent` | two invocations equal on stable subset |
| 6 | `test_vault_fee_zero_when_out_of_range` | out-of-range Swaps accrue zero vault_fee |
| 7 | `test_cKES_rate_populated` | forward-fill exercised; non-null rate on every row |
| 8 | `test_usdt_usd_separate_column` | `usdt_usd_rate` present, method='stipulated' |
| 9 | `test_demand_01_no_graph_mainnet` | enforce helper raises on graph-mainnet rows |

### Synthetic 100-block fixtures

- `synthetic_swaps_n100.jsonl` (100 events: 80 Swap + 10 Mint + 5 Burn + 3 phantom Transfer + 2 user-counterparty Transfer)
- `synthetic_vault_state_n100.jsonl` (100 vault states; tick range `[10_000, 20_000]` for in-range coverage on Swap rows whose tick drifts inside that band)
- `synthetic_fx_rates_n100.jsonl` (10 fx rates, one per 10 blocks → forward-fill exercised on the 90 intermediate event blocks)

### Cutoff arithmetic (Pitfall 5)

`FORNO_HEAD = 67_000_220`, `lag_blocks = 120` → `cutoff = 67_000_100`. Max fixture block = 67_000_099 ≤ 67_000_100 → all 100 fixture rows kept. If FORNO_HEAD drops below 67_000_220, finality_cutoff silently drops fixture rows and the `df.height == 97` assertion fails (height collapses to 0). The test file embeds this arithmetic in a load-bearing comment.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Added ERC-20 Transfer decoder to bridge phantom_filter integration gap**
- **Found during:** Task 2 GREEN — first run of `test_build_panel_row_count` returned `df.height == 100`, not 97.
- **Issue:** `decoders.TOPIC0_TO_EVENT` did not register `TRANSFER_TOPIC0`, so Transfer rows decoded as `event_name='Unknown'` with no `from`/`to` columns. `phantom_filter.exclude_adapters` guards `required = {event_name, from, to}.issubset(df.columns)` and returns the DataFrame unchanged when the guard fails — silently defeating the 3-row phantom drop.
- **Fix:** Added `TRANSFER_TOPIC0`, `TOPIC0_TO_EVENT["Transfer"] = ...`, and `decode_transfer(topics, data)` emitting `{from, to, value}`. Re-ran `test_panel_e2e.py` — all 9 tests pass. Re-ran the full Phase 2 Python suite — 70 passed / 1 skipped / 0 fail (no regressions).
- **Files modified:** `analysis/src/abrigo_x402/decoders.py`
- **Commit:** `4ae857f` (bundled with the panel.py GREEN commit per task-commit protocol)

**Note on plan acceptance grep:** The plan body's `grep -c "0x0e2a3e05bc9a16f5292a6170456a710cb89c6f72"` assertion expected `0x`-prefixed adapter matches and showed 0 hits because the fixture embeds the adapter address INSIDE the 32-byte zero-padded topic word (no inline `0x` prefix). The semantic count is 3 phantom Transfers (`grep -c "0e2a3e05bc9a16f5292a6170456a710cb89c6f72"` = 3). The downstream pipeline test (`test_build_panel_row_count` asserting `df.height == 97`) is the load-bearing oracle and passes.

## Acceptance grid

| Acceptance criterion | Verdict | Evidence |
| -------------------- | ------- | -------- |
| `pytest tests/test_panel_e2e.py -x` exits 0 with ≥9 tests passed | PASS | `9 passed in 0.23s` |
| Full Phase 2 Python suite exits 0 | PASS | `70 passed, 1 skipped in 0.31s` |
| Pipeline-order grep over `panel.py` (all 6 modules referenced) | PASS | All 6 substring greps return hit |
| DEMAND-01 enforce wired (`grep "graph-mainnet" panel.py`) | PASS | Match present |
| End-to-end produces 97 rows on the 100-block synthetic | PASS | `test_build_panel_row_count` asserts `df.height == 97` |
| All 6 PANEL-02 keys in output Parquet | PASS | `test_write_panel_has_metadata` reads via `pl.read_parquet_metadata` |
| Re-build idempotency | PASS | `test_build_panel_idempotent` equals stable subset |

## Self-Check: PASSED

Files verified on disk:
- FOUND: `analysis/src/abrigo_x402/panel.py`
- FOUND: `analysis/tests/test_panel_e2e.py`
- FOUND: `analysis/tests/fixtures/synthetic_swaps_n100.jsonl`
- FOUND: `analysis/tests/fixtures/synthetic_vault_state_n100.jsonl`
- FOUND: `analysis/tests/fixtures/synthetic_fx_rates_n100.jsonl`
- FOUND: `.planning/phases/02-panel-build-l3-for-the-ichi-ckes-usdt-anchor/02-08-SUMMARY.md`

Commits verified in `git log`:
- FOUND: `cfe7c3f` (test fixtures)
- FOUND: `ce3e929` (RED tests)
- FOUND: `4ae857f` (GREEN — panel + Transfer decoder)
