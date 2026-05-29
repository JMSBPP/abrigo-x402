# FX-snap decision: Mento broker mid-rate for cKES/USDT panel

**Decision date:** 2026-05-26
**Phase:** 02 (Panel Build — ICHI cKES/USDT)
**Requirement:** PANEL-03
**Plan:** 02-06

## Chosen: Mento Broker mid-rate via raw viem.readContract({ blockNumber })

cKES↔USDm conversion at the event block, queried via the Mento Broker
contract (`0x777A8255cA72412f0d706dc03C9D1987306B4CaD`) calling
`getAmountOut(BiPoolManager, exchangeId, cKES, USDm, 1e18)` at the
specific historical block. The exchangeId
`0x89de88b8eb790de26f4649f543cb6893d93635c728ac857f0926e842fb0d298b`
was live-resolved in Plan 02-00 via
`BiPoolManager.getExchangeIds() → getPoolExchange(id)` iteration on the
on-chain BiPoolManager state and captured at
`analysis/tests/fixtures/mento_cKES_USDm_exchange_id.json`.

The TS sidecar (`fetch/src/mento/historical-rate.ts`) issues one raw
`viem.readContract({ blockNumber: BigInt(N) })` per event block, writes a
JSONL row per block to `data/raw/ichi/fx_rates/<block_range>.jsonl`, and
appends a `endpoint='forno'` cost-ledger row (DEMAND-01 uncapped).

The Python reader (`analysis/src/abrigo_x402/fx_snap.py`) loads the JSONL,
applies a `polars.DataFrame.join_asof(strategy="backward")` to associate
each panel event with the most recent prior 'exact' rate, and injects the
`fx_method` enum and the USDT/USD-separate-column commitment.

## Alternatives considered

### 1. USDT/USD = 1.0 collapse — REJECTED

Per CLAUDE.md the load-bearing tail-risk for Phase 4 hedging analysis is
**USDT depeg + USDT/USDC basis risk** (NOT USDC depeg). Collapsing
USDT/USD to 1.0 in panel construction would destroy the signal Phase 4
needs. Retained as a separate column with default value `'1.0'` AND
explicit `usdt_usd_method='stipulated'` so Phase 4 can swap in
depeg-event data without touching Phase 2 panel construction. The
column's existence is the load-bearing structural commitment; its
default value is not.

### 2. Chainlink CELO/USD on-chain feed — REJECTED

Chainlink on Celo provides CELO/USD but not cKES/USD directly. A
cKES/USD synthesis would require triangulation (cKES/USDC × USDC/USD via
Chainlink), adding an extra hop + price-model assumption per snap. Mento's
broker mid-rate is the on-chain Mento-native source-of-truth for any
Mento stable; using Chainlink as primary would import non-Mento price
formation noise into the FX column.

### 3. Pyth on-Celo — REJECTED

Pyth feeds on Celo are nascent as of 2026-05-26 and the cKES feed
availability is not verified. Mento's broker is the canonical source for
any Mento stable; Pyth could appear as a Phase-4 cross-validation source
if/when cKES coverage lands.

### 4. Mento SDK 3.2.8 `QuoteService.getAmountOut()` — REJECTED for historical queries

Source inspection (RESEARCH §B + Pitfall 1) confirms the SDK's
QuoteService does NOT accept `blockNumber`; it always queries head.
For per-event historical snap we MUST use raw
`viem.readContract({ blockNumber: N })` against the Broker contract
directly. The SDK's `BROKER_ABI` is also incomplete (it bundles only
`tradingLimits*` fragments), so we hand-supply the `getAmountOut`
fragment via `parseAbi(['function getAmountOut(...)'])`.

## Implementation summary

| Component | Path | Role |
|---|---|---|
| TS sidecar | `fetch/src/mento/historical-rate.ts` | Per-block Broker.getAmountOut via raw viem.readContract; JSONL writer; cost-ledger append |
| Python reader | `analysis/src/abrigo_x402/fx_snap.py` | JSONL loader + `attach_rates()` asof-join + USDT/USD column injection |
| exchangeId fixture | `analysis/tests/fixtures/mento_cKES_USDm_exchange_id.json` | Live-resolved cKES↔USDm exchangeId (Plan 02-00) |

## Forward-fill semantics

When the Broker reverts at a block (paused exchange, zero liquidity,
pre-deployment, precision underflow), the most recent prior 'exact' rate
is the best proxy. Marking `fx_method='forward_fill'` explicitly preserves
the provenance signal so Phase 4's USDT-depeg sensitivity can distinguish
exact from interpolated rates.

Sidecar rows with `method='unavailable'` (Broker revert at that block)
are EXCLUDED from the polars asof join — otherwise the join would pick
up the unavailable row's `rate_x1e18='0'` as if it were the most recent
quote. Filtering before the join makes forward-fill skip 'unavailable'
and land on the most recent 'exact' row.

Panel event at block < smallest 'exact' rate block →
`fx_method='unavailable'` with null rate column. Phase 3 fits must
either drop or flag these rows; Phase 5 reproducibility manifest must
emit `unavailable` counts per protocol-vault-window.

## USDT/USD column

ALWAYS present in panel output with `usdt_usd_rate='1.0'` and
`usdt_usd_method='stipulated'` as the Phase 2 default. Phase 4 may
overwrite specific rows with `usdt_usd_method='depeg-event'` and the
actual depeg-window rate when running USDT-depeg + USDT/USDC basis-risk
scenarios.

The column is NEVER dropped, even if all values are `'1.0'` in the
panel window — the column's existence is the load-bearing structural
commitment per CLAUDE.md.

## Pre-registration commitments

`FX_METHODS = ("exact", "forward_fill", "unavailable")` enum committed
to `notes/PRE_REGISTRATION.md` before any Phase 3 fit consumes the FX
column. Adding a new value (e.g., `"triangulated"` if Phase 4 mixes
Chainlink USDC/USD with Mento cKES/USDC) requires PRE_REGISTRATION
update and review-trail entry per GOV-01.
