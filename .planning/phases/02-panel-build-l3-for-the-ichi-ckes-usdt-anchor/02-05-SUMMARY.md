---
phase: 02-panel-build-l3-for-the-ichi-ckes-usdt-anchor
plan: 05
subsystem: analysis-revenue-leg
tags: [polars, q96-tick-math, uniswap-v3, lp-fee, int128, ichi-vault]

# Dependency graph
requires:
  - phase: 02
    plan: 00
    provides: revenue_leg.py skeleton + analysis/tests pytest infra + ichi.toml [protocol] fee_tier=100
provides:
  - "compute_swap_fee(df, fee_tier_bps) — Q96 LP-fee decomposition, pure function over polars DataFrame"
  - "Four new String-dtype columns appended: fee_token0, fee_token1, vault_fee_token0, vault_fee_token1 (decimal-strings, NEVER Float64)"
  - "Q128 = 2**128 constant export for any downstream consumer that needs FixedPoint128"
  - "In-range / out-of-range / zero-input / zero-swap.liquidity edge cases covered"
  - "Pitfall 2 mitigation: NET-amount-to-gross-input recovery factor fee_tier_bps/(1e6-fee_tier_bps)"
  - "Pitfall 6 mitigation: explicit Int128 casts in lieu of polars 1.41 Decimal[38,0] (floor_div unsupported on Decimal)"
affects:
  - 02-04 (vault_state.attach_in_range — populates vault_in_range + vault_liquidity columns consumed here)
  - 02-08 (panel build orchestrator — calls compute_swap_fee in pipeline)
  - 03 (DGP estimation — consumes per-Swap vault_fee_token0/1 columns)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "polars Int128 fixed-width BigInt arithmetic for Uniswap on-chain integer math"
    - "Decimal-string emit pattern: arithmetic in Int128, output as pl.String to avoid downstream Float64 coercion"
    - "Edge-case defenses: zero swap.liquidity → zero vault_fee (div-by-zero gate)"

key-files:
  created:
    - analysis/tests/test_revenue_leg.py (135 lines, 7 tests)
  modified:
    - analysis/src/abrigo_x402/revenue_leg.py (was 18-line skeleton; now 104 lines with full Q96 decomposition)

key-decisions:
  - "Use polars Int128 (not Decimal[38,0]) for the BigInt arithmetic — polars 1.41 does not implement floor_div on Decimal; Int128 1.7e38 range safely holds abs(amount) * fee_tier_bps for realistic Uniswap V3 amounts (uint256 input × 1e6 fee_tier ≤ ~6e25)"
  - "Emit fee columns as String (decimal-string) not Int128 so downstream Plan 02-08 / Plan 03 explicitly chooses Int / Decimal arithmetic without silent Float64 coercion"
  - "Defense against degenerate swap.liquidity=0 → vault_fee=0 (defensive; real Swap events never have liquidity=0 but the polars expression already guards `vault_in_range & (swap_L > 0)`)"
  - "Plan's literal expected value 100_010_001_000_100_010 was incorrect (off by ~1000×); the actual Python floor-div result is 100_010_001_000_100 — verified by hand and by Solidity FullMath.mulDiv truncation semantics"

patterns-established:
  - "Pattern: Polars expression-level arithmetic on text columns — cast String→Int128 once, do arithmetic, cast back to String for stable serialization"
  - "Pattern: when/then/otherwise with explicit zero literal of matching dtype (pl.lit(0, dtype=pl.Int128)) for edge-case branches"

requirements-completed: [PANEL-01]

# Metrics
duration: 3min
completed: 2026-05-26
---

# Phase 2 Plan 05: Revenue-leg Q96 LP-fee decomposition Summary

**Pure-function `compute_swap_fee(df, fee_tier_bps)` adds four decimal-string columns (`fee_token0`, `fee_token1`, `vault_fee_token0`, `vault_fee_token1`) to a polars DataFrame of decoded Uniswap V3 Swap events, encoding RESEARCH §A's verbatim formula via polars Int128 arithmetic.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-05-26T17:23:46Z
- **Completed:** 2026-05-26T17:27:05Z
- **Tasks:** 1 (TDD — RED + GREEN)
- **Files modified:** 2

## Accomplishments

- Q96 LP-fee math encoded **verbatim per UniswapV3Pool.sol L718-719** (no paraphrase): `step.feeAmount = abs(swap_input) × fee_tier_bps / (1_000_000 - fee_tier_bps); vault_fee = step.feeAmount × (vault_in_range_liquidity / swap.liquidity)`
- 7/7 tests pass covering: zeroForOne (fee on token0), oneForZero (fee on token1), in-range half-share (vault_fee ≈ pool_fee × 0.5), out-of-range (vault_fee = 0), worked example with full vault-share (fee_token0 = 100_010_001_000_100 wei verbatim), zero-input degenerate, zero swap.liquidity degenerate
- `analysis/src/abrigo_x402/revenue_leg.py` is now production-ready for Plan 02-08 panel orchestration consumption — DataFrame in, DataFrame out, no side effects, no I/O
- Int128 arithmetic mitigates Pitfall 6 (silent Float64 coercion) while remaining within polars 1.41's supported operations (Decimal[38,0] floor_div is NOT supported in 1.41 — discovered live during GREEN-phase regression)

## Task Commits

Each task was committed atomically:

1. **Task 1 — RED phase** — `58acc8f` (test: add failing tests for Q96 LP-fee decomposition)
2. **Task 1 — GREEN phase** — `bf1c6d8` (feat: implement Q96 LP-fee decomposition per RESEARCH §A)

**Plan metadata:** [hash filled in by final commit] (docs: complete 02-05)

## Files Created/Modified

- `analysis/tests/test_revenue_leg.py` — 7 pytest tests; uses `_make_swap()` factory; covers all behavioral edges
- `analysis/src/abrigo_x402/revenue_leg.py` — 104-line module; exports `compute_swap_fee` + `Q128 = 2**128`; full docstring referencing UniswapV3Pool.sol L718-719 and RESEARCH §A

## Decisions Made

- **Int128 over Decimal[38,0]**: discovered via runtime exception in first GREEN attempt that polars 1.41 raises `InvalidOperationError: floor_div operation not supported for dtype 'decimal[38,0]'`. Switched to Int128 (1.7e38 range, supports both `*` and `//`); validated against the worked example value 100_010_001_000_100 byte-exactly.
- **Worked-example expected value corrected**: plan body asserted `100_010_001_000_100_010` (likely a transcription error mis-grouping digits); actual value computed both by hand and by Python = `100_010_001_000_100`. Test now derives expected value from formula directly (`(amount * fee_tier_bps) // (1e6 - fee_tier_bps)`) so it remains correct regardless of future literal-value transcription drift.
- **Emit format**: decimal-string (pl.String) not Int128 — preserves Plan 01-04 cache-side convention (amount0/amount1/liquidity already serialized as decimal-strings); downstream Plan 02-08 / Plan 03 explicitly chooses Int / Decimal arithmetic.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Polars 1.41 Decimal[38,0] does not support floor_div**

- **Found during:** Task 1 GREEN phase (first pytest run after implementing per plan-body code literally)
- **Issue:** Plan-body implementation used `pl.col(...).cast(pl.Decimal(precision=38, scale=0))` then `(expr * num) // den`. Polars 1.41 raises `InvalidOperationError: floor_div operation not supported for dtype 'decimal[38,0]'`. The arithmetic is well-defined mathematically but unimplemented in this polars release.
- **Fix:** Switched the four Decimal cast targets to `pl.Int128`. Int128 (range ~1.7e38) safely holds `abs(amount256_low) * fee_tier_bps`. Updated docstring's Pitfall-6 reference to document the polars-1.41 limitation. Zero-literal in `when/then/otherwise` branches recast to `pl.lit(0, dtype=pl.Int128)`.
- **Files modified:** `analysis/src/abrigo_x402/revenue_leg.py`
- **Verification:** All 7 tests pass; worked-example produces 100_010_001_000_100 wei byte-exactly.
- **Committed in:** `bf1c6d8` (Task 1 GREEN commit)

**2. [Rule 1 - Bug] Plan-body worked-example literal was off by ~1000×**

- **Found during:** Task 1 GREEN phase (after Int128 fix, the worked-example test still failed because the asserted literal `100_010_001_000_100_010` was incorrect math)
- **Issue:** `(1e18 * 100) // (1_000_000 - 100) = 1e20 // 999_900 = 100_010_001_000_100` (verified by hand: `999_900 × 100_010_001_000_100 = 99_999_999_999_999_999_900`; remainder 100). The plan-body asserted `100_010_001_000_100_010` which is wrong by a factor of ~1000 — likely a transcription error mis-grouping the digit blocks.
- **Fix:** Rewrote the test assertion to derive expected from the formula directly via Python int arithmetic (`expected = (amount0 * fee_tier_bps) // (1_000_000 - fee_tier_bps)`) and added a `100_010_001_000_100` literal docstring sanity-check assertion. The test is now robust to future literal-value transcription drift.
- **Files modified:** `analysis/tests/test_revenue_leg.py`
- **Verification:** `test_worked_example_from_research` passes; the corrected literal `100_010_001_000_100` matches Python int floor-div, polars Int128 floor-div, and Solidity FullMath.mulDiv truncation semantics.
- **Committed in:** `bf1c6d8` (Task 1 GREEN commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 — bug fixes; one library-capability mismatch in plan body, one arithmetic transcription error in plan body)
**Impact on plan:** Zero scope creep; both fixes were necessary for the plan's own acceptance criteria to pass. The formula encoded is verbatim per RESEARCH §A; only the polars expression-tree dtype path differs.

## Issues Encountered

- Plan 02-02's `chore` commit `ea3ab0a` had already logged "Plan 02-05 revenue_leg floor_div failure to deferred-items" — i.e., another parallel-wave executor (02-02) hit this issue first and rolled it forward for this plan. Resolved in this plan via Rule-1 auto-fix above; the deferred-items entry can be marked resolved by Plan 02-08 orchestrator or by an explicit follow-up commit.

## User Setup Required

None — pure Python module; no external service configuration; no new dependencies (polars 1.41.0 already pinned at Phase 1).

## Next Phase Readiness

- Plan 02-08 (panel orchestrator) can now `from abrigo_x402.revenue_leg import compute_swap_fee` and call it on the post-`attach_in_range` DataFrame inline.
- Plan 03 (DGP estimation on revenue leg) has the per-Swap `vault_fee_token0` / `vault_fee_token1` columns ready for arrival-process consumption.
- One follow-up: real on-chain `pool.positions(vault, lower, upper).liquidity` precision check is deferred to Phase 7 if a captured `collectFees` cross-check shows >1% drift between the actual position L and the `totalSupply` proxy (Pitfall 2 warning sign) — see module docstring.
- Polars version sensitivity: if/when polars adds Decimal floor_div support (≥1.42?), the Int128 path can be revisited for symmetry with the upstream Decimal-string ingest pattern; behavior is identical, code-quality only.

## Self-Check: PASSED

- File `analysis/src/abrigo_x402/revenue_leg.py` exists.
- File `analysis/tests/test_revenue_leg.py` exists.
- Commit `58acc8f` exists (RED).
- Commit `bf1c6d8` exists (GREEN).
- `cd analysis && uv run pytest tests/test_revenue_leg.py -x` exits 0 with 7 tests passed.
- `grep -q "fee_factor_den = 1_000_000 - fee_tier_bps" analysis/src/abrigo_x402/revenue_leg.py` exits 0.
- `grep -q "vault_in_range" analysis/src/abrigo_x402/revenue_leg.py` exits 0.

---
*Phase: 02-panel-build-l3-for-the-ichi-ckes-usdt-anchor*
*Completed: 2026-05-26*
