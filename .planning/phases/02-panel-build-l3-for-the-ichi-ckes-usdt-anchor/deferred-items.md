# Phase 2 Deferred Items

Items discovered out-of-scope during Phase 2 plan execution. Logged per execute-plan scope-boundary rule.

## From Plan 02-01

- **Plan 02-05 territory**: `analysis/tests/test_revenue_leg.py::test_zero_for_one_swap_fee_on_token0` fails with `polars.InvalidOperationError` on Decimal/Int multiply path inside the Q96-tick-math implementation (`analysis/src/abrigo_x402/revenue_leg.py`). Pre-existing failure on disk from parallel-wave Plan 02-05 in-flight work (commit `58acc8f` test RED — no GREEN commit landed yet). NOT a 02-01 regression; ingest.py + protocol_spec.py do NOT import revenue_leg. Resolution: Plan 02-05 executor lands the GREEN commit for `compute_swap_fee`. Affects: full-suite `uv run pytest` is currently red; per-plan suites for 02-01 (`tests/test_ingest.py tests/test_protocol_spec.py`) remain 14/14 green.

## From Plan 02-02

- **Plan 02-05 territory (same failure as 02-01)**: `test_revenue_leg.py::test_zero_for_one_swap_fee_on_token0` still failing with `polars.exceptions.InvalidOperationError: floor_div operation not supported for dtype decimal[38,0]` on `[(col("_amt0_dec")) * 100] // 999900`. NOT a 02-02 regression — decoders.py does not import or affect revenue_leg.py. Per-plan suite `tests/test_decoders.py` = 10/10 green. Hint for Plan 02-05 GREEN: polars 1.41.0 needs `.cast(pl.Int128)` before floor-div on decimal columns, OR use Decimal-typed lit operand + `/` followed by `.floor()`.
