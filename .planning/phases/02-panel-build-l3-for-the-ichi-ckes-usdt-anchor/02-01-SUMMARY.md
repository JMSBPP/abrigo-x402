---
phase: 02-panel-build-l3-for-the-ichi-ckes-usdt-anchor
plan: 01
subsystem: panel-ingest
tags: [PANEL-01, ingest, finality-cutoff, protocol-spec, pydantic, polars]
requires:
  - 02-00 (pytest infra + module skeletons + protocols/ichi.toml [panel] block)
  - 01-04 (Phase 1 JSONL cache emit format)
provides:
  - "abrigo_x402.ingest.load_jsonl(path) -> polars.DataFrame"
  - "abrigo_x402.ingest.apply_finality_cutoff(df, forno_head, lag_blocks=120)"
  - "abrigo_x402.ingest.DEFAULT_FINALITY_LAG = 120"
  - "abrigo_x402.protocol_spec.load_protocol(path) -> ProtocolSpec"
  - "abrigo_x402.protocol_spec.{ProtocolSpec, Protocol, AnchorPool, Vault, PanelConfig}"
affects:
  - "Plans 02-02..02-07: all Wave 1b modules consume load_jsonl(...) | apply_finality_cutoff(...) as the first two pipeline steps"
  - "Plan 02-08 panel orchestrator: reads protocol_spec.load_protocol('protocols/ichi.toml').panel.finality_lag_blocks"
tech-stack:
  added:
    - "pydantic 2.13.4 (already provisioned by Plan 02-00)"
  patterns:
    - "TDD RED → GREEN per task (no refactor needed); 5-test + 9-test atomic commits"
    - "DataFrame schema-on-construction (explicit pl.Int64 / pl.String / pl.List(pl.String)) to avoid polars schema-inference surprise"
    - "Single-line pl.filter for finality cutoff (RESEARCH §E one-liner contract)"
key-files:
  created:
    - "analysis/tests/test_protocol_spec.py (5 tests)"
    - "analysis/tests/test_ingest.py (9 tests)"
    - "analysis/tests/fixtures/ichi_anchor_block_67000000_67001000.jsonl (10-line synthetic)"
  modified:
    - "analysis/src/abrigo_x402/protocol_spec.py (skeleton → impl)"
    - "analysis/src/abrigo_x402/ingest.py (skeleton → impl)"
decisions:
  - "FINALITY_LAG default constant exported as DEFAULT_FINALITY_LAG = 120 module-level so downstream modules can `from abrigo_x402.ingest import DEFAULT_FINALITY_LAG` without re-reading protocols/ichi.toml"
  - "txHash + contractAddress field renames at ingest (NOT decode) so Wave 1b modules consume panel-row schema directly; raw Blockscout-v1 `transactionHash` and `address` keys are read-tolerant"
  - "contractAddress lowercased at ingest (Blockscout-v1 returns lowercase but defensive)"
  - "topics kept as List[String] (NOT decoded) — decoders.py owns topic0 dispatch (Plan 02-02)"
  - "pydantic ProtocolSpec drops extra per-protocol fields (chain_id, factory_address, iteration, blockscout urls, etc.) via default model_config (extra='ignore') rather than failing — Phase 2 only validates the subset it needs"
metrics:
  duration_minutes: 9
  completed_date: "2026-05-26T17:26:09Z"
  tasks: 2
  files: 5
  tests_added: 14
  tests_passing_at_completion: 14
---

# Phase 2 Plan 01: PANEL-01 Ingest + ProtocolSpec Summary

JSONL-cache → polars DataFrame ingest with one-line finality cutoff filter and pydantic TOML protocol-spec reader, both TDD-driven and 14/14 green on a 10-line synthetic Blockscout-v1 fixture.

## What Was Built

**Task 1 — `protocol_spec.load_protocol`** (commits `cd62124` test RED + `0fcffab` feat GREEN):

- Pydantic mirror of `fetch/src/protocol-spec.ts` zod schema (subset Phase 2 needs)
- `ProtocolSpec` = `{protocol: Protocol, panel: PanelConfig, vaults: dict[str, Vault]}`
- `AnchorPool` validates `address|token0|token1` against `^0x[0-9a-fA-F]{40}$` regex; `fee_tier` bounded `[0, 1_000_000]` bps
- `Vault` validates `address` regex; `active: bool = False` default; `pool_address` optional
- `PanelConfig.finality_lag_blocks: int = 120` (pydantic default — graceful for any protocol without explicit [panel] block)
- `load_protocol(path)`: reads via `tomllib.load(open(path, "rb"))`; flattens `[protocol.vaults.<id>]` into the top-level `vaults` dict; drops extra per-protocol fields (chain_id, factory_address, iteration, blockscout urls) via pydantic default `extra='ignore'`

**Task 2 — `ingest.load_jsonl` + `apply_finality_cutoff`** (commits `89a59c8` test RED + `0f22147` feat GREEN):

- `load_jsonl(cache_path)` reads Phase 1 JSONL line-by-line; parses hex `blockNumber` + `logIndex` to `Int64` via `int(s, 16)`; renames `transactionHash` → `txHash` and `address` → `contractAddress`; lowercases `contractAddress`
- 7-column polars schema enforced at DataFrame construction: `{blockNumber: Int64, blockHash: String, logIndex: Int64, txHash: String, contractAddress: String, topics: List[String], data: String}`
- Zero-null `blockNumber` invariant: `null` raises `ValueError` on hex decode; post-build `df["blockNumber"].null_count() > 0` raises (defense-in-depth)
- `DEFAULT_FINALITY_LAG = 120` module constant
- `apply_finality_cutoff(df, forno_head, lag_blocks=120)`: single-line `df.filter(pl.col("blockNumber") <= forno_head - lag_blocks)` — matches RESEARCH §E one-liner contract; pipeline-position contract documented in module docstring ("FIRST transform after load_jsonl, before any join")

## Acceptance Results

```
$ cd analysis && uv run pytest tests/test_ingest.py tests/test_protocol_spec.py -v
14 passed in 0.06s
```

| Acceptance criterion | Result |
| --- | --- |
| `cd analysis && uv run pytest tests/test_protocol_spec.py -x` exits 0 with 5 tests | PASS (5/5) |
| `cd analysis && uv run pytest tests/test_ingest.py -x` exits 0 with ≥9 tests | PASS (9/9) |
| `load_protocol('../protocols/ichi.toml').protocol.anchor_pool.fee_tier == 100 and .panel.finality_lag_blocks == 120` | PASS (prints `ok`) |
| `apply_finality_cutoff(load_jsonl(JSONL), forno_head=67896653, lag_blocks=120).height` | `5` |
| `grep -q "filter.*blockNumber.*<=" analysis/src/abrigo_x402/ingest.py` | PASS (`df.filter(pl.col("blockNumber") <= cutoff)`) |
| `pnpm -C fetch exec tsc --noEmit` | exit 0 (no TS regressions) |

## Deviations from Plan

**1. [Rule 1 — Bug] Fixed plan-body fixture hex values**

- **Found during:** Task 2 GREEN test run
- **Issue:** Plan body specified fixture rows 0..4 with `0x3FED320..0x3FED324` (which decode to 67_031_840..67_031_844) and rows 5..9 with `0x40BF541..0x40BF545` (which decode to 67_892_545..67_892_549). But all test assertions, the operational context note, and the inline plan-body documentation specified the rows as decimal blocks 67_000_000..67_000_004 and 67_896_641..67_896_645. The hex literals were arithmetically wrong; tests asserting `min == 67_000_000` and `max == 67_896_645` would never pass against the plan-body hex.
- **Fix:** Recomputed correct hex via `python3 -c "print(hex(...))"`: rows 0..4 use `0x3FE56C0..0x3FE56C4` (67_000_000..67_000_004 verified); rows 5..9 use `0x40C0541..0x40C0545` (67_896_641..67_896_645 verified). Cutoff math holds: `forno_head=67_896_653 - 120 = 67_896_533`; rows 5..9 (>=67_896_641) drop, `out.height==5`.
- **Files modified:** `analysis/tests/fixtures/ichi_anchor_block_67000000_67001000.jsonl`
- **Commit:** `0f22147` (folded into GREEN feat commit per TDD execution flow)

The operational context note in the prompt instructed "use these exact hex values" referring to `0x40BF541..0x40BF545`, but those hex literals decode to wrong decimal values that contradict every other documented number in the plan (M6 fix says `df["blockNumber"].max() == 67_896_645`, plan-body documentation says "blocks 67_896_641–67_896_645", test asserts `max() == 67_896_645`). I treated the decimal block targets as authoritative (they're cross-referenced in 4 places) and the hex literals as the typo. If the operational-context hex was the intended truth, the fix is trivially reversible by editing both the fixture and the `test_load_jsonl_hex_block_decoded` assertion.

## Deferred Items

See `.planning/phases/02-panel-build-l3-for-the-ichi-ckes-usdt-anchor/deferred-items.md`:

- Plan 02-05 `revenue_leg.py` pre-existing RED test (`test_zero_for_one_swap_fee_on_token0`) — out-of-scope for 02-01 (ingest does NOT import revenue_leg); 02-05 executor lands GREEN.

## Downstream Unblocked

- Plan 02-02 (decoders): `from abrigo_x402.ingest import load_jsonl` + iterate over `df["topics"]` for topic0 dispatch
- Plan 02-03 (phantom_filter): `df = apply_finality_cutoff(load_jsonl(path), forno_head=...)` then filter on `contractAddress`/topics
- Plan 02-04 (vault_state attach): joins on `blockNumber`
- Plan 02-05 (revenue_leg): consumes decoded Swap rows that flow through 02-01 ingest
- Plan 02-06 (fx_snap): joins FX-snap sidecar rows on `blockNumber`
- Plan 02-08 (panel orchestrator): reads `load_protocol("protocols/ichi.toml").panel.finality_lag_blocks` for the cutoff override

## Self-Check: PASSED

- `analysis/src/abrigo_x402/protocol_spec.py` exists (FOUND)
- `analysis/src/abrigo_x402/ingest.py` exists (FOUND)
- `analysis/tests/test_protocol_spec.py` exists (FOUND)
- `analysis/tests/test_ingest.py` exists (FOUND)
- `analysis/tests/fixtures/ichi_anchor_block_67000000_67001000.jsonl` exists (FOUND)
- Commit `cd62124` (test RED protocol_spec) FOUND
- Commit `0fcffab` (feat GREEN protocol_spec) FOUND
- Commit `89a59c8` (test RED ingest) FOUND
- Commit `0f22147` (feat GREEN ingest) FOUND
