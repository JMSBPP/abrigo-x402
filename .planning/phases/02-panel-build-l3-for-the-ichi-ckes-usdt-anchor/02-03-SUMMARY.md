---
phase: 02-panel-build-l3-for-the-ichi-ckes-usdt-anchor
plan: 03
subsystem: panel
tags: [panel, phantom-filter, fee-abstraction, polars, transfer-events, celo]

# Dependency graph
requires:
  - phase: 02-panel-build-l3-for-the-ichi-ckes-usdt-anchor/02-00
    provides: phantom_filter.py skeleton; phantom_transfer_synthetic.json (load-bearing); phantom_transfer_usdt_real.json (status=no-adapter-traffic-found fallback)
provides:
  - PANEL-04 exclude_adapters(df) — polars filter dropping Transfer events where from∈ADAPTERS or to∈ADAPTERS
  - ADAPTERS frozenset {USDC_FEE_ADAPTER, USDT_FEE_ADAPTER} canonical lowercase
  - USDC_FEE_ABSTRACTION_ADAPTER / USDT_FEE_ABSTRACTION_ADAPTER aliases (plan-frontmatter naming)
  - 12 unit tests (11 pass + 1 conditional skip on real-fixture fallback)
affects: [02-08 panel-build orchestrator (decode_all→exclude_adapters chain); Phase 3 DGP estimation (arrival counts must exclude gas-payment artifacts)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Filter scope is event-name-gated (Transfer-only) — non-Transfer events pass through unconditionally even if from/to look adapter-like, since those columns are not load-bearing for Swap/Mint/Burn/Deposit/Withdraw"
    - "Single polars filter expression with str.to_lowercase().is_in() for case-insensitive matching — no row-by-row Python loop"
    - "Defensive passthrough: empty DataFrame OR missing event_name/from/to columns → input returned unchanged"

key-files:
  created:
    - analysis/tests/test_phantom_filter.py
  modified:
    - analysis/src/abrigo_x402/phantom_filter.py

key-decisions:
  - "Filter scope intentionally narrow: only the two hardcoded Celo fee-abstraction adapter addresses (USDC 0x2f25... + USDT 0x0e2a...). Broader Transfer-without-paired-Swap-in-same-tx heuristic deferred to Phase 7 per CONTEXT.md."
  - "Filter operates on event_name=='Transfer' only — adapter-shaped from/to on Swap/Mint/Burn events pass through (those columns aren't load-bearing for non-Transfer types)."
  - "Address matching is case-insensitive via pl.col('from').str.to_lowercase().is_in(adapter_list) — Blockscout sometimes emits checksummed addresses but ADAPTERS is the lowercase canonical form."
  - "Real fixture (phantom_transfer_usdt_real.json) test conditionally skips on _meta.status=='no-adapter-traffic-found' — Plan 02-00's documented fallback when Blockscout probes returned empty across 10k/50k/200k/1M block windows. Synthetic fixture remains the load-bearing test input."
  - "Added USDC_FEE_ABSTRACTION_ADAPTER / USDT_FEE_ABSTRACTION_ADAPTER aliases alongside USDC_FEE_ADAPTER / USDT_FEE_ADAPTER so both naming conventions in the plan's success-criteria spec resolve to identical canonical values."

patterns-established:
  - "Event-name-gated filter: filter conditions guarded by (pl.col('event_name')=='Transfer') so non-Transfer rows skip the from/to predicate entirely"
  - "Defensive column-existence check before filter: required = {'event_name','from','to'}; if not required.issubset(df.columns): return df (no-op when upstream didn't decode any Transfers)"
  - "Case-insensitive address matching via str.to_lowercase() (NOT a stored upper/lower hash column) — keeps schema flat"

requirements-completed: [PANEL-04]

# Metrics
duration: 3min
completed: 2026-05-26
---

# Phase 02 Plan 03: phantom_filter.exclude_adapters Summary

**PANEL-04 phantom-Transfer filter — `exclude_adapters(df)` drops `event_name='Transfer'` rows where `from ∈ ADAPTERS` OR `to ∈ ADAPTERS` using a single polars filter expression; gas-payment legs to USDC/USDT fee-abstraction adapters are removed while user-to-counterparty Transfers in the same tx are preserved.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-05-26T17:23:02Z
- **Completed:** 2026-05-26T17:24:29Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 2

## Accomplishments

- `analysis/src/abrigo_x402/phantom_filter.py` implements `exclude_adapters(df: pl.DataFrame) -> pl.DataFrame` as a single polars filter expression — no row-by-row Python loop.
- `ADAPTERS: frozenset[str]` = `{USDC_FEE_ADAPTER, USDT_FEE_ADAPTER}` populated with the lowercase canonical Celo fee-abstraction adapter addresses verified against CONTEXT.md.
- Exports both `USDC_FEE_ADAPTER` / `USDT_FEE_ADAPTER` and aliases `USDC_FEE_ABSTRACTION_ADAPTER` / `USDT_FEE_ABSTRACTION_ADAPTER` (resolving the plan-spec naming variant).
- `analysis/tests/test_phantom_filter.py` ships 12 tests covering: USDC/USDT as `from` (dropped); USDC/USDT as `to` (dropped); user→counterparty Transfer preserved; non-Transfer events (Swap, Mint, Burn, Deposit, Withdraw) pass through; case-insensitive matching; synthetic-fixture full round-trip (3 logs → 2 surviving); real-fixture conditional skip on `no-adapter-traffic-found`; empty DataFrame; missing-columns defensive passthrough.
- 11 passed / 1 skipped (real-fixture conditional skip per Plan 02-00 documented fallback).

## Task Commits

1. **Task 1 RED — test(02-03): add failing tests for phantom_filter.exclude_adapters** — `055ccdc` (test)
2. **Task 1 GREEN — feat(02-03): implement phantom_filter.exclude_adapters (PANEL-04)** — `987060f` (feat)

_TDD task: RED commit raised `NotImplementedError('Plan 02-03')` on first behavioral test; GREEN commit landed the polars filter expression and turned the 11 passing tests green (12th conditionally skipped)._

## Files Created/Modified

- `analysis/src/abrigo_x402/phantom_filter.py` — `exclude_adapters` body + alias exports + expanded docstring with scope/rationale
- `analysis/tests/test_phantom_filter.py` — 12 unit tests including synthetic-fixture round-trip and real-fixture conditional

## Decisions Made

- Filter scope is **Transfer-only** by event_name gate. Swap/Mint/Burn/Deposit/Withdraw events pass through unconditionally even if their `from`/`to` columns look adapter-shaped — those columns aren't load-bearing for non-Transfer event types in the panel-row schema.
- Broader heuristic (Transfer-without-paired-Swap-in-same-tx, group-by-tx structural filter) **deferred to Phase 7** per CONTEXT.md; Phase 2 keeps the hardcoded-adapter exclusion narrow.
- Case-insensitive address matching via `pl.col('from').str.to_lowercase().is_in(adapter_list)` instead of normalizing addresses at ingest. Keeps the panel-row schema flat (no separate `from_lower` column) and absorbs the inconsistency at the filter boundary.
- Defensive column-existence check `required.issubset(df.columns)` returns the input unchanged if upstream produced a Swap-only DataFrame (no Transfer decoding). This makes `exclude_adapters` safe to call unconditionally in the Plan 02-08 `build_panel` orchestrator pipeline.
- Both naming conventions in the plan's frontmatter (`USDC_FEE_ADAPTER` and `USDC_FEE_ABSTRACTION_ADAPTER`) are exported as aliases to identical string values — no callsite has to choose between them.

## Deviations from Plan

None — plan executed exactly as written. RED → GREEN TDD cycle clean. No deviation rules triggered.

## Issues Encountered

None. The synthetic fixture (Plan 02-00) drove the test design; the real fixture's `no-adapter-traffic-found` status was anticipated by the plan body and handled via `pytest.skip` rather than a hard failure.

## User Setup Required

None — pure Python module with no external service dependencies.

## Next Phase Readiness

- **Plan 02-08 (panel orchestrator)** can wire `exclude_adapters(df)` directly after `decode_all` in the `build_panel` pipeline. The defensive missing-columns passthrough means it's safe to call even on Swap-only intermediate frames.
- **Phase 3 DGP estimation** consumes arrival counts cleaned by this filter — gas-payment artifacts excluded, user→counterparty Transfers preserved.
- **Phase 6 (Iter-2 Steer cCOP/USDT)** inherits the same filter; if the real-fixture `no-adapter-traffic-found` flips on the cCOP/USDT pool, the conditional skip auto-activates and exercises the real on-chain shape.
- **Phase 7 (cross-iteration synthesis)** owns the broader Transfer-without-paired-Swap-in-same-tx heuristic; this plan deliberately deferred it.

## Self-Check: PASSED

- `analysis/src/abrigo_x402/phantom_filter.py` — FOUND
- `analysis/tests/test_phantom_filter.py` — FOUND
- commit `055ccdc` (test RED) — FOUND
- commit `987060f` (feat GREEN) — FOUND
- `cd analysis && uv run pytest tests/test_phantom_filter.py -x` exit 0 (11 passed, 1 skipped)
- `grep -q "0x2f25deb3848c207fc8e0c34035b3ba7fc157602b" analysis/src/abrigo_x402/phantom_filter.py` exit 0
- `grep -q "0x0e2a3e05bc9a16f5292a6170456a710cb89c6f72" analysis/src/abrigo_x402/phantom_filter.py` exit 0
- ADAPTERS == {USDC_FEE_ADAPTER, USDT_FEE_ADAPTER} verified via importable runtime assert

---
*Phase: 02-panel-build-l3-for-the-ichi-ckes-usdt-anchor*
*Plan: 03*
*Completed: 2026-05-26*
