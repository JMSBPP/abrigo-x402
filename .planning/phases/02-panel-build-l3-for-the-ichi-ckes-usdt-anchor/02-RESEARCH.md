# Phase 2: Panel Build (L3) for the ICHI cKES/USDT Anchor — Research

**Researched:** 2026-05-26
**Domain:** Polars panel construction from a Blockscout v1 raw-event Parquet cache; Mento broker historical-block FX-rate snap via viem `readContract({ blockNumber })`; Q96 tick math LP-fee accrual from raw Uniswap V3 Swap events; phantom-transfer filter for Celo fee-abstraction adapters; finality cutoff at 120 blocks behind Forno head; PANEL-02 metadata-header injection via polars 1.41.0 native `write_parquet(metadata=...)`.
**Confidence:** HIGH on Q96 fee formula (verified against `UniswapV3Pool.sol` source); HIGH on Mento Broker addresses + ABI surface (read live from `@mento-protocol/mento-sdk@3.2.8` source in `node_modules`); HIGH on polars 1.41.0 native Parquet metadata round-trip (runtime probe in the workspace's uv venv); HIGH on phantom-transfer adapter mechanics (verified against Celo official fee-abstraction docs); MEDIUM on the specific real on-chain phantom-Transfer fixture (deferred to Plan 02-NN Blockscout probe — see Section D).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Panel scope (carried from Phase 0 + Phase 1)
- Iter-1 panel: **single-vault cKES/USDT microcosm only** per Q-4 (Phase 0 lock). No per-protocol aggregate.
- Anchor pool: cKES/USDT Uniswap V3 (`0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F`) per `protocols/ichi.toml`.
- Anchor vault: single active ICHI cKES/USDT vault `0xe304b980535c29869983BC58d129F984Fec4176F` per `protocols/ichi.toml [vaults.cKES_USDT_anchor] active = true`.
- Cold-backfill from block `60000000` (per `protocols/ichi.toml [protocol] cold_backfill_from_block`).
- ~38 non-anchor ICHI vaults remain `active = false; reason = "v2-deferred"` — NOT in this panel.

#### Event ingest (PANEL-01)
- Source-of-truth: Phase 1's Blockscout v1 etherscan-compat client (`fetch/src/blockscout/v1-getlogs.ts`), output cached as Parquet/JSONL under `data/raw/ichi/<pool>/<block_range>.parquet`.
- Phase 2 reads this cache via the content-addressed key from Phase 1 (`(chainId, contractAddress, blockRange)`); does NOT re-fetch from Blockscout.
- Event panel row schema (minimum): `blockNumber, blockHash, logIndex, txHash, contractAddress, event_name, ...payload_fields_per_event_type`. Zero null `blockNumber` rows (lint-enforced).
- Event types in scope: Uniswap V3 `Swap`, `Mint`, `Burn` on the anchor pool; ICHI vault `Deposit`, `Withdraw` on the anchor vault. Decoded via viem `decodeEventLog` (Phase 1 decoders + new decoders for Mint/Burn/Deposit/Withdraw in Phase 2).
- Polars is the panel-construction library per STACK.md (`polars 1.41.0`); pandas reserved for small estimation frames in Phase 3+.

#### FX-rate snap (PANEL-03)
- **Primary**: Mento broker mid-rate at the event-block for cKES↔USDm conversion, queried via `@mento-protocol/mento-sdk` v3.2.8 (already pinned in `fetch/package.json`) called from a TypeScript helper invoked by the Python panel build, OR equivalent direct broker contract call via viem.
- **USDT/USD**: separate column (`usdt_usd_rate`), NEVER collapsed to 1.0. Per `notes/fx_snap_decision.md` requirement (ROADMAP SC).
- **`notes/fx_snap_decision.md`**: Phase 2 deliverable documenting alternatives considered (USDT/USD=1.0 collapse rejected; Chainlink CELO/USD; Pyth on-Celo; Mento broker mid-rate) and the justification for the Mento broker anchor.
- **Provenance**: every FX snap row carries `(source, block, rate, provenance_url)` so Phase 5 reproducibility manifest can verify each snap independently.
- **Fallback when Mento broker has no rate at a specific block**: Claude's Discretion at /gsd:plan-phase 2 — recommended approach is forward-fill from the most recent prior block where the broker did quote, with explicit `fx_snap_method = "forward_fill" | "exact"` column for provenance.

#### Phantom-transfer filter (PANEL-04)
- **Exclusion set**: hardcoded adapter addresses per ROADMAP — USDC fee-abstraction adapter `0x2F25deB3848C207fc8E0c34035B3Ba7fC157602B`, USDT fee-abstraction adapter `0x0e2a3e05bc9a16f5292a6170456a710cb89c6f72`.
- **Implementation**: any `Transfer` event with `from ∈ {USDC_adapter, USDT_adapter}` OR `to ∈ {USDC_adapter, USDT_adapter}` is excluded from arrival counts. Documented in unit test against a known fee-abstraction transaction.
- **Broader structural heuristic** (Transfer-without-paired-Swap-in-same-tx) is **NOT** the Phase 2 filter — too risky for false-positive filtering of legitimate transfers. Deferred to Phase 7 (cross-iteration synthesis) if needed.

#### Provenance metadata (PANEL-02)
- Every Parquet output + `fit_report.json` scaffold + plot carries the header: `{chainId, contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit}`.
- `make lint-artifacts` (already wired in Phase 1 Makefile) greps each output file for the header fields and exits non-zero on any missing field.
- Header injection: panel construction wraps output writes in a `with_header(...)` helper from `analysis/src/abrigo_x402/provenance.py`.

#### Reorg / finality handling
- Blockscout v2 has no `block_consensus` field (Phase 1 research finding). Phase 2 mitigation: **finality cutoff at N blocks behind Forno head** at panel-build time.
- **N = 120 blocks** (~2 min at Celo 1s block time, matches Celo PoS soft-finality). Configurable via `protocols/ichi.toml [panel] finality_lag_blocks`.
- Events on blocks `> (forno_head - 120)` are EXCLUDED from the Phase 2 panel and flagged for re-ingest on next refresh.
- `notes/forno_head_snapshot.json` (Phase 1 artifact) is the Phase 2 head reference for deterministic dry-run; live refresh uses Forno directly (DEMAND-01-excluded from cost-ledger as Forno is uncapped).

#### LP-fee accrual leg
- **Approach**: Q96 tick math from raw Swap events × pool fee tier × in-range vault liquidity share — per RESEARCH §I fallback path (subgraph dormant per Phase 1 hunt verdict).
- **Vault state ingestion**: direct Forno `eth_call` to the ICHI vault contract per Swap event for `totalAmounts()`, `totalSupply()`, `currentTick()`. Forno is free at any volume (DEMAND-01-excluded), but batched per block for efficiency.
- **Implementation**: `analysis/src/abrigo_x402/revenue_leg.py` — pure-function decomposition: `compute_swap_fee(swap_event, pool_fee_tier_bps, in_range_liquidity_share)` returning fee in token0 + token1 units; then FX-snap to USD via the Phase 2 FX module.
- **Phase 2 ships LP-fee per Swap row**, NOT aggregated. Phase 3 aggregates as needed for DGP estimation.
- **In-range check**: vault is in-range for a Swap if `vault.lower_tick ≤ pool.current_tick ≤ vault.upper_tick` at the event block. Outside-range Swaps accrue zero LP-fees to the vault (verified per ICHI's auto-rebalance mechanics).

#### Provenance + spot-check (PANEL-02 + REPORT-02 prep)
- Per-row `provenance_url` column: Blockscout link of the form `https://celo.blockscout.com/tx/<txHash>#eventlog`.
- 5-row spot-check sample for Phase 5 PDF deliverable derived from the panel's `provenance_url` column.

### Claude's Discretion
- **FX-snap method enum values** (`"exact" | "forward_fill" | "unavailable"`) — Claude proposes at /gsd:plan-phase time; values committed in PRE_REGISTRATION.md before any Phase 3 fit consumes them.
- **Vault state caching strategy** — per-block memoization, per-tx, or per-Swap; Claude chooses based on Forno call volume estimates.
- **Polars schema field types** (specifically `Decimal[38,18]` vs `Float64` for token amounts) — Claude proposes; tests verify byte-stable Parquet output.
- **Panel chunking** within the cache — single Parquet per pool's full block range OR per-1M-block chunk. Defaults to per-1M-block chunk for FETCH-04 cache idempotency granularity.
- **Mento SDK invocation**: TypeScript helper exporting JSON for Python ingestion OR Python-native Web3 contract call. Claude picks; both viable.
- **Phantom-transfer test fixture**: synthetic vs real-on-chain capture. Claude picks; recommended is a real captured fee-abstraction transaction from CANDIDATES.md research.

### Deferred Ideas (OUT OF SCOPE)
- **Broader phantom-transfer heuristic** (Transfer-without-paired-Swap-in-same-tx) — deferred to Phase 7 cross-iteration synthesis if false negatives surface in Phase 2's hardcoded-address filter.
- **Per-vault aggregate panel** (multi-ICHI-vault, Q-4 retrospective substrate) — deferred to v2 per Phase 0 Q-4 lock (single-vault microcosm only in v1).
- **Real Mento V2 Broker + V4 PoolManager event panels** for cCOP corridor — Iter-2 / Phase 6, NOT Iter-1.
- **Steer LP-fee panel** — Phase 6 (which is structurally pre-disqualified at STRADDLE per Phase 0; Steer Iter-2 fires HEDGE-05 memo-only null).
- **Subgraph-based LP-fee** (typed `position` + `feeGrowthGlobal0X128`) — Phase 1.5 enrichment IF subgraph hunt later finds an acceptable Uniswap V3 Celo deployment; until then, Q96 tick math is the canonical Phase 2 path.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| **PANEL-01** | Event-level Parquet panels with on-chain provenance: each row carries `(blockNumber, blockHash, logIndex, txHash, contractAddress, event, ...payload)`, no aggregation/binning | §A (Polars schema field-by-field), §H (panel construction module decomposition), §K (fixture strategy) |
| **PANEL-02** | Every output artifact carries metadata header `{chainId, contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit}`; outputs without header rejected by build | §I (polars 1.41.0 native `write_parquet(metadata=…)` — runtime probe confirmed round-trip; **no JSON sidecar needed**); `make lint-artifacts` greps the Parquet footer directly via `parquet-tools dump --print-key-value` or polars `read_parquet_metadata` |
| **PANEL-03** | FX-rate snap via Mento broker mid-rate at event-block for cKES↔USDm; USDT/USD a separate column never collapsed to 1.0 | §B (Mento Broker `getAmountOut` ABI + Celo mainnet address `0x777A8255cA72412f0d706dc03C9D1987306B4CaD`; viem `readContract({ blockNumber: N })` is the historical-block path because Mento SDK's `QuoteService.getAmountOut` does NOT accept a blockNumber per source inspection), §C (forward-fill fallback) |
| **PANEL-04** | Phantom-transfer filter excludes USDC adapter `0x2F25…` and USDT adapter `0x0e2a…` Transfer events; unit-tested against a known fee-abstraction tx | §D (adapter mechanics verified vs Celo official docs; real-fixture capture task surfaced) |
| **DEMAND-01** (enforce-component) | Forno `eth_call` (vault state, Mento broker rates) is FREE — NOT counted against 90k Graph budget; cost-ledger rows for Phase 2 use `endpoint = "forno"` or `endpoint = "blockscout"`, NEVER `"graph-mainnet"` | §J (no `graph-mainnet` rows in Phase 2; Phase 2 ledger writes verified by SC) |
</phase_requirements>

## Summary

Phase 2 materializes the event-level Parquet panel for the ICHI cKES/USDT anchor vault from the Phase 1 Blockscout-v1 cache. Eight concrete deliverables, every one with primary-source verification:

1. **Q96 LP-fee formula is a single-line read off `UniswapV3Pool.sol`:** `state.feeGrowthGlobalX128 += FullMath.mulDiv(step.feeAmount, FixedPoint128.Q128, state.liquidity)` (lines ~718-719, verified live via WebFetch against `Uniswap/v3-core@main`). For Phase 2's per-Swap LP-fee-to-vault calculation, we deliberately bypass `feeGrowthGlobalX128` accumulation (which we'd need to subtract `feeGrowthInside` from to isolate one Swap's contribution) and use the equivalent **direct decomposition**: `vault_fee_for_swap = step.feeAmount × (vault_in_range_liquidity / swap_liquidity)`, where `step.feeAmount = swap_input_amount × pool_fee_tier_bps / 1e6`, and `vault_in_range_liquidity = vault.liquidity` if `vault.lower_tick ≤ Swap.tick ≤ vault.upper_tick` else 0. The `swap_liquidity` is the `liquidity` field already in the Swap event payload (Phase 1's decoded ABI includes it — see `fetch/src/decoders/uniswap-v3-swap.ts`). The protocol-fee leg (`feeProtocol`) is zero for all V3 pools that have not invoked `setFeeProtocol` — verify per-pool via one-off `eth_call` to `pool.slot0().feeProtocol`.

2. **Mento broker historical-block query MUST drop to raw viem `readContract({ blockNumber: N })`.** Confirmed by source inspection of `@mento-protocol/mento-sdk@3.2.8` in the workspace's `node_modules`: `QuoteService.getAmountOut(tokenIn, tokenOut, amountIn, route?)` calls `publicClient.readContract({...})` without `blockNumber` — it always queries head. The SDK also routes through the **Mento Router** (`0x4861840C2EfB2b98312B0aE34d86fD73E8f9B6f6`) via `getAmountsOut(amountIn, encodedPath[])`, not directly the Broker. For Phase 2 we go **direct to the Broker** (`0x777A8255cA72412f0d706dc03C9D1987306B4CaD`) with the full ABI fragment we supply (the SDK's bundled `BROKER_ABI` only includes `tradingLimits*` reads — verified). Function signature confirmed against the Solidity source: `getAmountOut(address exchangeProvider, bytes32 exchangeId, address tokenIn, address tokenOut, uint256 amountIn) view returns (uint256)`. The `exchangeProvider` for cKES/USDm is the **BiPoolManager** (`0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901`); the `exchangeId` is the `bytes32` keccak256 identifier for the cKES↔USDm pool, fetched once at Phase 2 init via `BiPoolManager.getExchangeIds()` (uncapped Forno call).

3. **Polars 1.41.0 has native Parquet file-level metadata** via `write_parquet(file, metadata={"chainId": "42220", ...})` and round-trip `read_parquet_metadata(file)` — **runtime probe in this workspace's uv venv confirmed it works**. Custom keys survive the binary footer and are grep-visible after a `parquet-tools dump --print-key-value` OR a one-liner Python wrapper. **No JSON sidecar needed.** `make lint-artifacts` calls a tiny Python script that loads `read_parquet_metadata(path)` and asserts the six required keys present. This obsoletes the "JSON sidecar OR Parquet schema metadata" branch in the orchestrator brief — polars 1.41.0 resolves it natively.

4. **Phantom-transfer filter is a one-liner polars expression on the Transfer-event subset of the panel** — `df.filter(~pl.col("from").is_in(ADAPTERS) & ~pl.col("to").is_in(ADAPTERS))`. The two adapter addresses are hardcoded constants in `analysis/src/abrigo_x402/phantom_filter.py` (mirroring `fetch/src/constants.ts` USDT pattern). Per the Celo official fee-abstraction docs, the adapter wraps a low-decimal token (USDT 6 decimals, USDC 6 decimals) and normalizes to 18 decimals for gas accounting; when a tx uses the adapter as `feeCurrency`, a Transfer with `from = tx_origin → to = adapter` (and a paired `adapter → fee_recipient` debit) fires inside the same tx as the user's actual Swap or other event. The user's USDT Transfer to the trading counterparty is unaffected and remains in the panel. **For the load-bearing real fixture: Plan 02-NN executes a targeted Blockscout v1 getLogs against the USDT adapter address over a recent 1000-block window** (uncapped Forno-style; logs `endpoint = "blockscout"` on cost-ledger), captures one canonical tx, and commits it to `analysis/tests/fixtures/phantom_transfer_usdt_real.json`. Synthetic fixtures are wired alongside for fast unit tests.

5. **Finality cutoff = `df.filter(pl.col("blockNumber") <= forno_head - 120)`.** One line, but the planner must decide where in the pipeline it lives. Recommendation: **immediately after JSONL → Parquet load, before any decoding/joining**, so downstream modules have a uniform "panel = finalized events only" invariant. The `forno_head` comes from `notes/forno_head_snapshot.json` for dry-run reproducibility (Plan 01-00 produces this; head currently `67896653`); live refresh uses `celoClient.getBlockNumber()` from `fetch/src/viem-clients.ts` via a small TS helper invoked once per panel build (one Forno eth_blockNumber call — uncapped, no ledger cost).

6. **Polars schema uses `Int64` for `blockNumber`/`tick`/`liquidity-ish` fields that fit, `Decimal[38, 0]` for the canonical Q96 `sqrtPriceX96` (up to 2^160 — fits Decimal[38,0]) so revenue_leg.py can decimal-arithmetic it without precision loss, and `Decimal[38, 18]` for `amount0`/`amount1` after scaling from `Int256` raw event payloads.** `String` (hex) for `blockHash`/`txHash`/`contractAddress`/`event_name`. polars.Decimal arithmetic is supported as of 1.x; verified against polars docs §Datatypes (decimal).

7. **Forno eth_call batching for vault state: use viem `multicall` against Celo Multicall3 (`0xcA11bde05977b3631167028862bE2a173976CA11`, hardcoded in viem's `chains.celo` deployment list).** 4,440 Swaps × 30d × 3 calls/Swap = ~13,320 eth_calls; multicall3 batches up to ~50 calls per RPC round-trip, reducing to ~270 RPC calls — well inside Forno's per-IP rate envelope. Cleaner alternative: **per-block memoization** — `totalAmounts()` and `currentTick()` only change when a Mint/Burn/Deposit/Withdraw fires on the vault, so memoize per block and reuse the same vault state across all Swaps in that block. Combined approach: per-block memo + multicall for the (block, fn_name) misses.

8. **Module decomposition (`analysis/src/abrigo_x402/`):** `ingest.py` (Parquet load + finality cutoff), `decoders.py` (Mint/Burn/Deposit/Withdraw — extends Phase 1 Swap decoder), `phantom_filter.py` (PANEL-04), `vault_state.py` (Forno multicall + per-block memo), `revenue_leg.py` (Q96 fee math), `fx_snap.py` (Mento broker historical-block, forward-fill), `provenance.py` (PANEL-02 `with_header` helper), `panel.py` (orchestrator that calls them in sequence).

**Primary recommendation:** Bypass the Mento SDK entirely for FX snap. Use direct viem `readContract({ address: BROKER, blockNumber: N, ... })` from a thin TypeScript helper (`fetch/src/mento/historical-rate.ts`) that the Python panel build invokes via `subprocess.run([... node script ...])` returning JSON. This is simpler than web3.py in Python (which would require redoing the chain client setup the TS workspace already maintains in `fetch/src/viem-clients.ts`). The TS helper batches all `(block, tokenIn, tokenOut, amountIn=1e18)` tuples for the panel's block range into a multicall, persists the result to `data/raw/ichi/fx_rates/<block_range>.parquet`, and Python's `fx_snap.py` reads that sidecar at panel construction time. Forward-fill happens in Python via `polars.fill_null(strategy="forward")` against the block-indexed sidecar.

## Standard Stack

### Core (Python panel side — `analysis/`)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `polars` | 1.41.0 | Panel construction, schema typing, Parquet I/O with native metadata | Already pinned in `analysis/pyproject.toml` per Phase 1 Plan 01-00. Verified `write_parquet(metadata=...)` round-trip in the workspace uv venv (Plan 02-NN will reproduce). |
| `pyarrow` | 24.0.0 (transitive via polars) | Underlying Parquet I/O; provides `read_parquet_metadata` fallback API surface | Pinned indirectly via polars. polars 1.41's metadata round-trip uses pyarrow under the hood for the file footer. |
| `numpy` | 2.4.6 | Q96 fixed-point arithmetic (sqrtPriceX96 manipulation, tick math); Decimal-array operations | Already pinned. Phase 3 also depends on it. |
| `scipy` | 1.17.1 | (Not strictly needed in Phase 2; available for any rate-table interpolation) | Already pinned. |
| `pytest` | 9.0.3 | Test runner for unit + integration tests | Already in `analysis/pyproject.toml` dev-deps per Phase 1 Plan 01-00 (or to be added if not — verify in Plan 02-00). |

### Supporting (TypeScript side — `fetch/`, for the Mento FX-snap helper + cost-ledger writes)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `viem` | 2.51.0 | `readContract({ blockNumber: N })` for historical Broker queries; `multicall` for batched vault-state reads | Always — Phase 1 establishes the singleton `celoClient` pattern; Phase 2 reuses |
| `@mento-protocol/mento-sdk` | 3.2.8 | Address book lookups (Broker, BiPoolManager) via `getContractAddress(ChainId.CELO, 'Broker')`; reading exchange ID/provider mapping at panel init | Use for static address lookups only; **do NOT use `QuoteService.getAmountOut` — it ignores blockNumber and is wrong for historical snapping** |
| `@iarna/toml` (transitive) | ^2.2 | Read `protocols/ichi.toml` for vault address, anchor pool address, finality_lag_blocks | Already in Phase 1's `protocol-spec.ts` |
| Node 22 LTS | — | `node:child_process` from Python `subprocess.run` | The TS↔Py boundary remains file-handoff JSON per ARCHITECTURE.md Pattern 1 |

### Alternatives Considered (FX-snap invocation model)

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| TS helper → JSON sidecar → polars read (CHOSEN) | `web3.py` in Python directly hitting Forno via Eth JSON-RPC | web3.py adds a second chain-client toolchain on top of TS viem; doubles maintenance surface. Forno RPC URL + ABI fragment + viem.readContract is already a load-bearing piece of `fetch/`; Phase 2 just adds one new TS script next to it. |
| TS helper batch sidecar | Per-event TS subprocess invocation (one Node spawn per Swap) | 4,440 process spawns / 30d is brutal vs one batched call returning a full `(block, rate)` table. Sidecar approach is ~2 orders of magnitude faster. |

### Alternatives Considered (LP-fee approach)

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Q96 tick-math from raw Swap events (CHOSEN) | Subgraph `position.collectedFeesToken0/1` + `pool.feeGrowthGlobal0X128` deltas | The Uniswap V3 Celo subgraph is dormant per Phase 1 hunt verdict (`MissingGraphApiKeyError` on call; two candidates exist but both require API keys + stale curation per Phase 1 RESEARCH §A). Q96 tick math is the pre-registered fallback per Phase 1 CONTEXT.md. |
| Per-Swap Q96 math | Per-block multicall over `pool.feeGrowthGlobal0X128/1X128` deltas, then prorate to Swaps in the block | More accurate (catches protocol-fee curveballs), but adds Forno call volume + complexity for ≤0.5% LP-fee precision gain — not worth it given LP-fees are a small fraction of revenue leg anyway. |
| Direct Q96 fee math | Subgraph-derived `swap.amountUSD * pool.feeTier / 1e6` shortcut | Subgraph dormant; same blocker. |

**Installation:**

```bash
# Python side — already pinned in analysis/pyproject.toml; nothing new to add
cd analysis && uv sync

# Optional: verify versions
uv run python -c "import polars, pyarrow, numpy, scipy; \
  print(polars.__version__, pyarrow.__version__, numpy.__version__, scipy.__version__)"
# Expected: 1.41.0 24.0.0 2.4.6 1.17.1
```

**Version verification:**

```bash
# Workspace uv venv probe (this is the canonical Phase 2 environment)
cd analysis && uv run python -c "
import polars as pl
print('polars:', pl.__version__)
df = pl.DataFrame({'a':[1]})
df.write_parquet('/tmp/probe.parquet', metadata={'chainId':'42220'})
print('metadata round-trip:', pl.read_parquet_metadata('/tmp/probe.parquet'))
"
# Already verified by researcher 2026-05-26:
# polars: 1.41.0
# metadata round-trip: {'ARROW:schema': '...', 'chainId': '42220'}
```

## Architecture Patterns

### Recommended Project Structure

```
analysis/
├── pyproject.toml                # already pinned at Phase 1 Plan 01-00
├── uv.lock                       # already pinned
├── src/abrigo_x402/
│   ├── __init__.py
│   ├── protocol_spec.py          # pydantic mirror of fetch/src/protocol-spec.ts zod schema
│   ├── ingest.py                 # Phase 1 JSONL/Parquet cache → polars DataFrame; finality cutoff
│   ├── decoders.py               # Mint, Burn, Deposit, Withdraw event decoders (extends Phase 1 Swap pattern)
│   ├── phantom_filter.py         # PANEL-04 — adapter address constants + filter expression
│   ├── vault_state.py            # Forno multicall for totalAmounts(), totalSupply(), currentTick(); per-block memo
│   ├── revenue_leg.py            # Q96 tick math: compute_swap_fee(swap, fee_tier_bps, vault_state)
│   ├── fx_snap.py                # Reads fetch/data/raw/ichi/fx_rates/*.parquet sidecar; forward-fill
│   ├── provenance.py             # with_header(df, **metadata) helper; PANEL-02 lint
│   ├── panel.py                  # Orchestrator: ingest → cutoff → decode → filter → state → fee → snap → write
│   └── data_leg.py               # Stipulated NHPP prior reader (per protocol_spec.py); placeholder for Phase 3
├── tests/
│   ├── conftest.py               # shared fixtures (tmp_path, synthetic Parquet, mock vault state)
│   ├── fixtures/
│   │   ├── synthetic_swaps_n10.parquet         # hand-crafted 10-event panel covering edge cases
│   │   ├── phantom_transfer_usdt_real.json     # captured live via Plan 02-NN Blockscout probe
│   │   ├── phantom_transfer_synthetic.json     # deterministic synthetic for fast unit tests
│   │   └── ichi_anchor_block_67000000_67001000.jsonl   # captured slice from Phase 1 cache
│   ├── test_ingest.py            # finality cutoff + null-block enforcement
│   ├── test_decoders.py          # Mint/Burn/Deposit/Withdraw ABI decode
│   ├── test_phantom_filter.py    # synthetic + real-fixture round-trip
│   ├── test_vault_state.py       # mocked multicall response; in-range check
│   ├── test_revenue_leg.py       # Q96 tick math (hand-computed reference + cross-check against captured ICHI vault fee receipt)
│   ├── test_fx_snap.py           # forward-fill behavior + Mento sidecar round-trip
│   ├── test_provenance.py        # PANEL-02 header injection + read-back
│   └── test_panel.py             # end-to-end on synthetic Parquet → panel with all 6 columns

fetch/
├── src/
│   ├── mento/
│   │   └── historical-rate.ts    # NEW Phase 2: batch Broker.getAmountOut(blockNumber=N) → JSON sidecar
│   ├── decoders/
│   │   ├── uniswap-v3-swap.ts    # exists (Phase 1)
│   │   ├── uniswap-v3-mint.ts    # NEW: optional, if Python decoders.py wants TS-side decode
│   │   ├── uniswap-v3-burn.ts    # NEW: same
│   │   ├── ichi-vault-deposit.ts # NEW
│   │   └── ichi-vault-withdraw.ts # NEW
│   └── cli.ts                    # NEW Plan 02-NN: extends with `snap-fx ichi` subcommand
└── tests/
    └── mento-historical-rate.test.ts   # NEW: stub multicall mock, verify blockNumber threading

protocols/
└── ichi.toml                     # extended in Plan 02-NN with [panel] finality_lag_blocks = 120
                                  # — verify schema-frozen-check still PASSes (per-protocol fields legal per RESEARCH note in Phase 1)

data/raw/ichi/
├── <pool_hash>/<block_range>.jsonl    # Phase 1 cache (existing)
├── fx_rates/<block_range>.parquet     # NEW Phase 2: Mento sidecar
├── vault_state/<vault_hash>/<block_range>.parquet   # NEW Phase 2: Forno multicall sidecar
└── panels/<pool_hash>/<block_range>.parquet         # NEW Phase 2 output: the event panel with all enrichments
```

### Pattern 1: Panel Module = Pure Function of (Cache + Spec)

**What:** Every module in `analysis/src/abrigo_x402/` is a pure function: same inputs → same outputs. No network calls inside the panel build (Forno calls live in TS sidecar generators that run *before* the Python panel build).
**When to use:** Always for L3 in this architecture (per ARCHITECTURE.md Pattern 3).
**Trade-offs:** Adds the TS sidecar coordination step; pays for itself the first time you re-run estimation 100×.

**Example (orchestrator pattern):**
```python
# analysis/src/abrigo_x402/panel.py
def build_panel(
    cache_path: Path,
    fx_sidecar_path: Path,
    vault_state_sidecar_path: Path,
    forno_head: int,
    protocol_spec: ProtocolSpec,
) -> pl.DataFrame:
    # 1. Load raw events from Phase 1 cache (JSONL → polars)
    df = ingest.load_jsonl(cache_path)
    # 2. Apply finality cutoff
    df = ingest.apply_finality_cutoff(df, forno_head, lag=protocol_spec.panel.finality_lag_blocks)
    # 3. Decode events (Swap already typed; add Mint/Burn/Deposit/Withdraw)
    df = decoders.decode_all(df, protocol_spec)
    # 4. Phantom-transfer filter (only affects Transfer rows; Swaps pass through)
    df = phantom_filter.exclude_adapters(df)
    # 5. Join vault state per block
    vault_state_df = pl.read_parquet(vault_state_sidecar_path)
    df = df.join(vault_state_df, on="blockNumber", how="left")
    # 6. Compute LP-fee per Swap
    df = revenue_leg.compute_fees(df, protocol_spec.anchor_pool.fee_tier)
    # 7. Join Mento FX rates per block
    fx_df = pl.read_parquet(fx_sidecar_path)
    df = fx_snap.attach_rates(df, fx_df)
    return df

# CLI wrapper writes panel with PANEL-02 header
def write_panel(df: pl.DataFrame, output_path: Path, metadata: dict) -> None:
    provenance.with_header(df, **metadata).write_parquet(output_path, metadata=metadata)
```

### Pattern 2: TS Sidecar Generators Persist to Parquet Before Python Runs

**What:** Mento FX rates and Forno vault state are generated by TS scripts that run BEFORE the Python panel build. Their outputs are Parquet sidecars under `data/raw/ichi/`. Python panel reads sidecars, never hits Forno or the Mento Broker directly.
**When to use:** Whenever a Phase 2+ Python step would need a chain RPC. Keeps the TS↔Py boundary one-directional and the Python pipeline fully offline-reproducible.
**Trade-offs:** Adds the "did you regenerate the sidecar?" coordination problem. Mitigation: each sidecar's filename includes its `(block_range, vault_address)` hash; `panel.py` errors loudly if the sidecar's block range doesn't cover the requested panel's range.

**Example (TS sidecar):**
```typescript
// fetch/src/mento/historical-rate.ts (sketch — full implementation is Plan 02-NN)
import { createPublicClient, http, parseAbi } from 'viem';
import { celo } from 'viem/chains';
import { writeFileSync } from 'node:fs';

const BROKER = '0x777A8255cA72412f0d706dc03C9D1987306B4CaD';  // verified live 2026-05-26 from @mento-protocol/mento-sdk@3.2.8/dist/core/constants/addresses.js
const BIPOOL_MANAGER = '0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901';
const CKES = '0x456a3D042C0DbD3db53D5489e98dFb038553B0d0';
const USDM = '0x765DE816845861e75A25fCA122bb6898B8B1282a';  // USDm, Mento Stable Token per addresses.js

const BROKER_ABI = parseAbi([
  // Verified against UniswapV3Core/mento-core Broker.sol via WebFetch 2026-05-26
  'function getAmountOut(address exchangeProvider, bytes32 exchangeId, address tokenIn, address tokenOut, uint256 amountIn) view returns (uint256 amountOut)',
  'function getAmountIn(address exchangeProvider, bytes32 exchangeId, address tokenIn, address tokenOut, uint256 amountOut) view returns (uint256 amountIn)',
]);

const BIPOOL_ABI = parseAbi([
  'function getExchangeIds() view returns (bytes32[])',
  // PoolExchange struct (mento-core): asset0, asset1, pricingModule, bucket0, bucket1, lastBucketUpdate, config
  'function getPoolExchange(bytes32 exchangeId) view returns ((address asset0, address asset1, address pricingModule, uint256 bucket0, uint256 bucket1, uint256 lastBucketUpdate, (uint256 spread, uint256 referenceRateFeedID, uint256 referenceRateResetFrequency, uint256 minimumReports, uint256 stablePoolResetSize) config))',
]);

const client = createPublicClient({ chain: celo, transport: http(process.env.CELO_RPC_URL ?? 'https://forno.celo.org') });

// Step 1: discover exchangeId for cKES/USDm by enumerating BiPoolManager's exchange list (one-time)
async function findExchangeId(tokenA: string, tokenB: string): Promise<`0x${string}`> {
  const ids = await client.readContract({ address: BIPOOL_MANAGER, abi: BIPOOL_ABI, functionName: 'getExchangeIds' });
  for (const id of ids) {
    const pe = await client.readContract({ address: BIPOOL_MANAGER, abi: BIPOOL_ABI, functionName: 'getPoolExchange', args: [id] });
    const a = pe.asset0.toLowerCase(); const b = pe.asset1.toLowerCase();
    const wanted = [tokenA.toLowerCase(), tokenB.toLowerCase()].sort();
    const have = [a, b].sort();
    if (wanted[0] === have[0] && wanted[1] === have[1]) return id;
  }
  throw new Error(`No Mento exchange found for ${tokenA}↔${tokenB}`);
}

// Step 2: for a list of (block, exchangeId, tokenIn, tokenOut, amountIn) tuples, batch-read the broker rate
async function snapRate(blockNumber: bigint, exchangeId: `0x${string}`, tokenIn: string, tokenOut: string, amountIn: bigint): Promise<bigint | null> {
  try {
    return await client.readContract({
      address: BROKER,
      abi: BROKER_ABI,
      functionName: 'getAmountOut',
      args: [BIPOOL_MANAGER, exchangeId, tokenIn, tokenOut, amountIn],
      blockNumber,  // ← THE LOAD-BEARING FIELD: viem's readContract supports historical block via this param
    });
  } catch (e) {
    // Broker reverts on paused exchange, zero liquidity, or pre-deployment block → return null, polars fill_null handles forward-fill
    return null;
  }
}
```

### Pattern 3: PANEL-02 Header via Polars Native Metadata

**What:** Every panel write uses `df.write_parquet(path, metadata={...})`. The metadata dict carries the six required keys. `make lint-artifacts` greps via a tiny Python script that calls `pl.read_parquet_metadata(path)`.
**When to use:** Every Parquet write under `data/raw/ichi/panels/`, `data/raw/ichi/fx_rates/`, `data/raw/ichi/vault_state/`.
**Trade-offs:** None — runtime probe confirmed it round-trips natively. Replaces the brief's "JSON sidecar OR Parquet schema metadata" branch entirely.

```python
# analysis/src/abrigo_x402/provenance.py
import polars as pl
import subprocess
from pathlib import Path
from typing import TypedDict

class PanelMetadata(TypedDict):
    chainId: str
    contractAddress: str
    blockRange: str   # "[fromBlock,toBlock]"
    fetchTimestamp: str  # ISO-8601 UTC
    dataHash: str     # sha256 of source events
    gitCommit: str

def git_commit_short() -> str:
    return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()

def with_header(df: pl.DataFrame, output_path: Path, **meta) -> Path:
    """Write df to output_path with PANEL-02 metadata header injected.
    All metadata values must be strings (polars metadata is dict[str,str])."""
    md = {k: str(v) for k, v in meta.items()}
    # Sanity-check: PANEL-02 required keys
    required = {"chainId", "contractAddress", "blockRange", "fetchTimestamp", "dataHash", "gitCommit"}
    missing = required - set(md.keys())
    if missing:
        raise ValueError(f"PANEL-02 metadata missing keys: {missing}")
    df.write_parquet(output_path, metadata=md)
    return output_path

def assert_has_header(path: Path) -> None:
    """make lint-artifacts hook calls this; raises if any PANEL-02 key absent."""
    md = pl.read_parquet_metadata(path)
    required = {"chainId", "contractAddress", "blockRange", "fetchTimestamp", "dataHash", "gitCommit"}
    missing = required - set(md.keys())
    if missing:
        raise AssertionError(f"PANEL-02 header missing in {path}: {missing}")
```

### Anti-Patterns to Avoid

- **Calling Mento SDK `QuoteService.getAmountOut` for historical FX:** silently queries head, wrong for any panel block ≠ forno_head. Use direct viem `readContract({ blockNumber })` against the Broker.
- **Collapsing USDT/USD to 1.0:** load-bearing for Phase 4 USDT-depeg sensitivity. Even if USDT/USD ≈ 1.0 in the panel window, the column must exist with provenance.
- **Querying Forno per-Swap:** 4,440 Swaps × 3 calls = 13.3k eth_calls; use multicall + per-block memo.
- **Re-fetching from Blockscout in Phase 2:** Phase 1 cache is canonical; Phase 2 reads, never re-fetches.
- **Writing the panel without metadata:** `make lint-artifacts` will reject it; safer to enforce at write time via `with_header(...)` rather than discover at lint time.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Parquet file-level metadata | Custom JSON sidecar + ad-hoc grep | `polars.DataFrame.write_parquet(metadata=...)` + `polars.read_parquet_metadata(path)` (verified 1.41.0 runtime probe) | Native, byte-stable, no extra file to coordinate with `make lint-artifacts` |
| Q96 fixed-point multiplication | Hand-rolled BigInt mulDiv | numpy uint256 OR Python int (no overflow; Python int is arbitrary precision); for byte-stable Parquet write `Decimal[38, 0]` | Q96 math is already in the V3 spec — copy the formula, don't reinvent FullMath.mulDiv |
| Multicall batching | Custom RPC batch encoder | viem's built-in `multicall` against Celo Multicall3 `0xcA11bde05977b3631167028862bE2a173976CA11` | Already in viem; matches ABI of every other multicall3 deployment; battle-tested |
| ABI event decoding (Mint/Burn/Deposit/Withdraw) | Custom keccak256 + ABI param decoder | viem `decodeEventLog` (same pattern as Phase 1's `decodeSwap`) | Strict mode + named args + first-class TS types |
| FX rate forward-fill | Manual loop over blocks | `polars.DataFrame.fill_null(strategy="forward")` after a left-join + sort by blockNumber | One-liner; vectorized; byte-stable |
| Mento Broker ABI | Manual ABI JSON | Supply `parseAbi([...])` fragment from viem with the two getAmountOut/getAmountIn signatures (the SDK's bundled BROKER_ABI is incomplete — verified) | Minimal surface area; pin the signatures in the TS helper |
| sha256 of source events for `dataHash` | Roll your own | Python `hashlib.sha256` on the deterministic JSONL bytes from Phase 1 cache OR on the polars-serialized Arrow IPC stream | Already canonical via Phase 1 `writeCachePayload` returning `dataHash` |

**Key insight:** Phase 2's value-add is the **glue** between Phase 1's raw event cache and Phase 3's DGP estimator. Every panel-construction primitive (Parquet I/O, ABI decode, multicall batching, fixed-point math) has a battle-tested library form. The custom code surface is module-by-module orchestration — not primitives.

## Common Pitfalls

### Pitfall 1: Mento SDK silently queries head, not historical block

**What goes wrong:** A naive Phase 2 implementation calls `mento.quotes.getAmountOut(cKES, USDm, 1e18)` from Python via subprocess and assumes it returns the rate at the Swap's event-block. It does NOT — it returns the rate at the chain head when the SDK was invoked. The panel ends up with all FX rates pinned to a single moment, defeating the per-event snap that PANEL-03 requires.
**Why it happens:** The SDK README + first-page docs show the simple 3-arg form. The block-aware path is not advertised. Source inspection (`node_modules/.pnpm/@mento-protocol+mento-sdk@3.2.8/.../QuoteService.js`) confirms no `blockNumber` parameter in any public method.
**How to avoid:** Bypass the SDK for FX snap; write a direct viem `readContract({ address: BROKER, abi: BROKER_ABI, blockNumber: N, ... })` call in `fetch/src/mento/historical-rate.ts`. Use the SDK only for the static `getContractAddress(ChainId.CELO, 'Broker')` lookup.
**Warning signs:** Every FX rate in the panel equals the same value; `df.select(pl.col('cKES_per_USDm_rate').n_unique())` returns 1.

### Pitfall 2: Q96 fee formula uses post-fee input amount (off-by-fee-tier error)

**What goes wrong:** The trader's input amount that pays the fee is the gross input — `step.feeAmount = step.amountIn * fee_tier / 1e6` where `amountIn` is BEFORE the fee is taken. The decoded Swap event's `amount0` / `amount1` are NET amounts (i.e., the input is the gross side, output is what's actually delivered). Conflating gross vs net amounts produces a fee estimate that's off by `(1 - fee_tier/1e6)` — about 0.01% for the 100-bps-fee cKES/USDT pool, undetectable in absolute terms but compounds with the in-range share to bias LP-fee estimates downward.
**Why it happens:** The Swap event emits `amount0` and `amount1` AFTER fees are applied (per `UniswapV3Pool.sol` line 753: "the fees are not included in this calculation"). The fee was already deducted upstream in `SwapMath.computeSwapStep`.
**How to avoid:** Reconstruct gross input as `gross_input = abs(amount_in_signed) / (1 - fee_tier/1e6)` OR — equivalently and numerically more stable — compute fee as `fee = abs(amount_in_signed) * fee_tier / (1e6 - fee_tier)`. Document the convention in `revenue_leg.py` with a comment block citing Uniswap V3 whitepaper §6.2.
**Warning signs:** A captured ICHI vault fee receipt (e.g., a `collectFees` event on the ICHI vault contract) over a window matches the panel's summed LP-fees within ~1%. If the panel is off by exactly `fee_tier/1e6` * total_volume, this pitfall fired.

### Pitfall 3: Multicall block-tag mismatch — one call queried `latest`, another queried `N`

**What goes wrong:** viem's `multicall` accepts a single `blockNumber` for the batch; if you forget to set it, all calls return head-of-chain values. For per-block memoized vault state, every multicall batch MUST set `blockNumber` to the block being snapped.
**Why it happens:** The default is `latest`; the omission is invisible.
**How to avoid:** Always thread `blockNumber: N` through `multicall({ ..., blockNumber: N })`. Unit-test the per-block memo by asserting that vault state at block `N₁` != vault state at block `N₂` for two blocks straddling a known ICHI rebalance (`Deposit` or `Withdraw` event between).
**Warning signs:** Vault state in the panel is constant across all blocks ≡ vault state at the panel-build time.

### Pitfall 4: Phantom-transfer filter false-positives on the trader-side leg of a fee-abstraction tx

**What goes wrong:** A fee-abstraction tx has TWO transfer events that involve the adapter: (a) the user's USDT → adapter for gas, (b) the user's USDT → counterparty for the actual swap-out. If the filter naively drops all transfers where `from = adapter` OR `to = adapter`, it might also drop legitimate transfers if the user accidentally transfers TO the adapter directly (unusual but not impossible).
**Why it happens:** The filter is intentionally broad to catch the documented adapter pattern; edge cases are rare but real.
**How to avoid:** In Phase 2 the filter applies ONLY to the `Transfer` event class (i.e., we never apply it to `Swap`, `Mint`, `Burn`, `Deposit`, `Withdraw`). Document this scope explicitly. The trader-counterparty Transfer is preserved because it doesn't touch the adapter address. Capture a real fee-abstraction tx in `phantom_transfer_usdt_real.json` and assert: panel has the Swap row, lacks the adapter-Transfer row, has any user-to-counterparty Transfer if present.
**Warning signs:** Panel arrival counts drop by > 1 per tx when applied to a window with known fee-abstraction-heavy traffic.

### Pitfall 5: Finality cutoff applied AFTER joins inflates intermediate row counts

**What goes wrong:** If you apply the finality cutoff after joining vault state + FX rates, you waste compute building the discarded rows and risk null-prop bugs from late filtering.
**Why it happens:** Easy to write `df.join(...).filter(blockNumber <= cutoff)` instead of `df.filter(blockNumber <= cutoff).join(...)`.
**How to avoid:** Apply finality cutoff in `ingest.py` as the **first** transform after JSONL → polars load. Document the invariant: every downstream module receives a finality-filtered DataFrame.
**Warning signs:** `df.filter(...)` row counts at intermediate stages don't drop monotonically; vault-state Forno multicall batches a higher block range than the panel actually needs.

### Pitfall 6: Polars Decimal precision mismatch causes silent integer→float coercion

**What goes wrong:** `Decimal[38, 18]` for `amount0` and `Decimal[38, 0]` for `liquidity` cannot directly arithmetic without explicit casts. If a `compute_swap_fee` formula multiplies them without `.cast(pl.Decimal(precision=38, scale=18))`, polars may coerce to `Float64`, losing precision at the 16th significant digit (cKES amounts can reach 1e18 wei).
**Why it happens:** polars Decimal arithmetic is column-typed; cross-scale ops fall back to Float64.
**How to avoid:** Define explicit cast functions in `revenue_leg.py`. Unit-test byte-stability: write panel → read panel → assert per-column dtype + sample values match a fixture.
**Warning signs:** `df.schema` shows `Float64` for an `amount` column you expected to be Decimal.

## Code Examples

Verified patterns from primary sources:

### Example 1: Q96 LP-fee per Swap (canonical formula)

**Source:** `UniswapV3Pool.sol` lines ~718-719 (verified live via WebFetch against `Uniswap/v3-core@main` 2026-05-26):
```solidity
if (state.liquidity > 0)
    state.feeGrowthGlobalX128 += FullMath.mulDiv(step.feeAmount, FixedPoint128.Q128, state.liquidity);
```

Phase 2 decomposition (`analysis/src/abrigo_x402/revenue_leg.py`):
```python
import polars as pl

Q128 = 2**128

def compute_swap_fee(
    df: pl.DataFrame,
    fee_tier_bps: int,    # e.g. 100 for the cKES/USDT 0.01% pool
) -> pl.DataFrame:
    """Add columns: fee_token0, fee_token1, vault_fee_token0, vault_fee_token1.

    Per Uniswap V3 spec:
      - The trader's GROSS input amount (before fee) pays a fee of size
        gross_input * fee_tier_bps / 1e6.
      - The Swap event emits NET amounts (amount0, amount1); the input side is
        whichever has the same sign as zeroForOne.
      - Recovering gross from net: gross = abs(net) / (1 - fee_tier_bps/1e6)
        ⇒ fee = abs(net) * fee_tier_bps / (1e6 - fee_tier_bps).

    The vault's share of the fee = fee × (vault_in_range_liquidity / swap.liquidity).
    """
    # zeroForOne ⇒ amount0 > 0 (token0 input); else amount1 > 0 (token1 input).
    # The "input" amount is the positive one; the fee is paid in that token.
    return df.with_columns(
        # Token0 input case
        pl.when(pl.col('amount0') > 0)
          .then(pl.col('amount0').abs() * fee_tier_bps / (1_000_000 - fee_tier_bps))
          .otherwise(0)
          .alias('fee_token0'),
        pl.when(pl.col('amount1') > 0)
          .then(pl.col('amount1').abs() * fee_tier_bps / (1_000_000 - fee_tier_bps))
          .otherwise(0)
          .alias('fee_token1'),
    ).with_columns(
        # Vault share — vault_in_range_liquidity is 0 if vault not in range at swap.tick
        # (see vault_state.py for the in-range flag)
        pl.when(pl.col('vault_in_range'))
          .then(pl.col('fee_token0') * pl.col('vault_liquidity') / pl.col('liquidity'))  # swap.liquidity
          .otherwise(0)
          .alias('vault_fee_token0'),
        pl.when(pl.col('vault_in_range'))
          .then(pl.col('fee_token1') * pl.col('vault_liquidity') / pl.col('liquidity'))
          .otherwise(0)
          .alias('vault_fee_token1'),
    )
```

### Example 2: Mento Broker historical-block rate snap

**Source:** Direct inspection of `@mento-protocol/mento-sdk@3.2.8` addresses table + Broker.sol signatures via WebFetch 2026-05-26.

```typescript
// fetch/src/mento/historical-rate.ts
import { createPublicClient, http, parseAbi, type Address } from 'viem';
import { celo } from 'viem/chains';
import { writeFileSync } from 'node:fs';

const ADDRESSES = {
  Broker: '0x777A8255cA72412f0d706dc03C9D1987306B4CaD' as Address,
  BiPoolManager: '0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901' as Address,
  cKES: '0x456a3D042C0DbD3db53D5489e98dFb038553B0d0' as Address,
  USDm: '0x765DE816845861e75A25fCA122bb6898B8B1282a' as Address,
} as const;

const BROKER_ABI = parseAbi([
  'function getAmountOut(address exchangeProvider, bytes32 exchangeId, address tokenIn, address tokenOut, uint256 amountIn) view returns (uint256)',
]);

const client = createPublicClient({
  chain: celo,
  transport: http(process.env.CELO_RPC_URL ?? 'https://forno.celo.org'),
});

export interface FxSnapRow {
  block: number;
  rate_x1e18: string;  // decimal string; cKES per 1 USDm at this block, scaled 1e18
  method: 'exact' | 'unavailable';
}

export async function snapFxRange(
  fromBlock: number,
  toBlock: number,
  exchangeId: `0x${string}`,
): Promise<FxSnapRow[]> {
  // Snap one rate per block in [fromBlock, toBlock]. For panels with ~7M blocks,
  // do not snap every block — snap only blocks that appear in the event panel.
  // (Caller supplies the deduped block list; signature simplified here.)
  const rows: FxSnapRow[] = [];
  for (let n = fromBlock; n <= toBlock; n++) {
    try {
      const out = await client.readContract({
        address: ADDRESSES.Broker,
        abi: BROKER_ABI,
        functionName: 'getAmountOut',
        args: [ADDRESSES.BiPoolManager, exchangeId, ADDRESSES.cKES, ADDRESSES.USDm, 10n ** 18n],
        blockNumber: BigInt(n),  // LOAD-BEARING — without this viem queries head
      });
      rows.push({ block: n, rate_x1e18: out.toString(), method: 'exact' });
    } catch {
      // Broker reverts ⇒ unavailable; polars forward-fill will substitute upstream
      rows.push({ block: n, rate_x1e18: '0', method: 'unavailable' });
    }
  }
  return rows;
}
```

### Example 3: PANEL-02 metadata via polars native — verified round-trip

**Source:** Runtime probe in `analysis/` uv venv 2026-05-26:
```python
import polars as pl
df = pl.DataFrame({'a': [1, 2, 3]})
df.write_parquet('/tmp/probe.parquet', metadata={
    'chainId': '42220',
    'contractAddress': '0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F',
    'blockRange': '[60000000,67896653]',
    'fetchTimestamp': '2026-05-26T11:00:00Z',
    'dataHash': '0xabc...',
    'gitCommit': '84dfc4d',
})
print(pl.read_parquet_metadata('/tmp/probe.parquet'))
# {'ARROW:schema': '<base64>', 'chainId': '42220', 'contractAddress': '0x61Ef...', ...}
# ✅ All six custom keys round-trip alongside the auto-injected ARROW:schema.
```

### Example 4: Phantom-transfer filter

```python
# analysis/src/abrigo_x402/phantom_filter.py
import polars as pl

USDC_FEE_ADAPTER = '0x2F25deB3848C207fc8E0c34035B3Ba7fC157602B'.lower()
USDT_FEE_ADAPTER = '0x0e2a3e05bc9a16f5292a6170456a710cb89c6f72'.lower()
ADAPTERS = {USDC_FEE_ADAPTER, USDT_FEE_ADAPTER}

def exclude_adapters(df: pl.DataFrame) -> pl.DataFrame:
    """Drop Transfer events where either party is a known fee-abstraction adapter.

    Per PANEL-04 + Celo official fee-abstraction docs: tokens with non-18 decimals
    (USDC=6, USDT=6) cannot be registered as FeeCurrency directly; an adapter
    wraps them for 18-decimal gas accounting. Transfers involving the adapter
    are gas-payment artifacts, not user-meaningful cashflows.

    Scope: only applies to event='Transfer' rows. Swap/Mint/Burn/Deposit/Withdraw
    pass through unchanged.
    """
    return df.filter(
        ~((pl.col('event_name') == 'Transfer') &
          (pl.col('from').str.to_lowercase().is_in(list(ADAPTERS)) |
           pl.col('to').str.to_lowercase().is_in(list(ADAPTERS))))
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Parquet metadata via pyarrow `replace_schema_metadata` + manual table cast | polars native `write_parquet(metadata={...})` | polars #21806 (released in 1.27+; stable in 1.41.0) | One-liner; no pyarrow.Table round-trip; less risk of pyarrow/polars schema-drift bugs. |
| Mento SDK 2.x ethers-native helpers | Mento SDK 3.2.8 viem-native | 2026-04-29 | viem alignment with rest of fetch/ workspace; but `QuoteService` STILL doesn't support historical blockNumber — bypass for FX snap. |
| Subgraph-derived LP-fees via `pool.feeGrowthGlobal0X128` | Q96 tick math from raw Swap events | Phase 1 hunt verdict 2026-05-26: subgraph dormant | More code in `revenue_leg.py`, but zero paid-Graph budget consumption, and the math is canonical (off `UniswapV3Pool.sol`). |
| Forno per-call rate-limit dance | viem `multicall` against Celo Multicall3 | viem 2.x default | Reduces ~13.3k eth_calls to ~270 RPC round-trips; well inside Forno's envelope. |

**Deprecated/outdated:**
- pyarrow direct `Table.from_polars()` + `replace_schema_metadata()` for PANEL-02 — superseded by polars native. **Note for the planner:** ARCHITECTURE.md still mentions a "pyarrow" path for cache metadata; that is outdated as of polars 1.27+.
- Mento V1 broker swap functions on the Reserve contract — fully migrated to BiPoolManager + Broker as of Mento V2. The Broker address (`0x777A82...4CaD`) is canonical.

## Open Questions

1. **Real on-chain phantom-transfer fixture tx hash**
   - What we know: USDT adapter `0x0e2a3e05bc9a16f5292a6170456a710cb89c6f72` exists on Celo mainnet (verified addr); the documented mechanism produces a Transfer involving the adapter in every fee-abstraction tx; per "Celo 2025 Year in Review", 56% of network fees paid in stablecoins via fee abstraction (so adapter txs are abundant).
   - What's unclear: a *specific captured* tx hash for the unit-test fixture. The Blockscout WebFetch returned a soft 404 / scraping block.
   - Recommendation: **Plan 02-NN executes a targeted Blockscout v1 getLogs against the USDT adapter address topic0=Transfer over a recent 1000-block window** (uncapped Forno-style; logs `endpoint = "blockscout"` row), picks the first tx that also contains a cKES/USDT Swap, captures it via `eth_getTransactionReceipt` for fixture. If the cKES/USDT pool doesn't intersect adapter usage in the search window (possible — cKES users may pay gas in CELO, not USDT), broaden to "first tx involving adapter + any DEX swap" as a structurally-equivalent fixture.

2. **ICHI vault `lower_tick` / `upper_tick` ABI fragment**
   - What we know: ICHI vaults are concentrated-liquidity managers wrapping a Uniswap V3 position; they expose vault state via `totalAmounts()` and similar. The exact getter names (`lowerTick()` vs `getLowerTick()` vs `currentTick()`) may vary across ICHI versions.
   - What's unclear: the exact ICHI vault ABI for `0xe304b980535c29869983BC58d129F984Fec4176F` on Celo. No subgraph helps (Phase 1 hunt found no ICHI subgraph).
   - Recommendation: **Plan 02-NN first task is to fetch the verified-source ABI from Blockscout** (`https://celo.blockscout.com/api/v2/smart-contracts/0xe304b9.../methods-read`) and pin the multicall ABI fragment in `fetch/src/decoders/ichi-vault.ts`. If the ABI is unverified on Blockscout, fall back to ICHI's public GitHub `IchiV1.sol` reference contract.

3. **Mento BiPoolManager exchangeId for cKES↔USDm**
   - What we know: `BiPoolManager.getExchangeIds()` returns the list; `getPoolExchange(id)` returns the `(asset0, asset1, ...)` PoolExchange struct. The exchangeId is keccak256-derived (see `mento-core/BiPoolManager.sol :: createExchange`).
   - What's unclear: the specific bytes32 value at panel build time. It's stable post-deployment but we shouldn't hardcode it without verification.
   - Recommendation: `historical-rate.ts` does the lookup ONCE at panel init (one Forno multicall) and persists `(cKES↔USDm, exchangeId)` to `data/raw/ichi/fx_rates/_exchange_ids.json` for cache hits on subsequent runs.

4. **`protocols/ichi.toml [panel] finality_lag_blocks = 120` schema increment**
   - What we know: `protocols/_schema.toml` is frozen at commit `e9b214d`; per-protocol TOML files may legally hold fields NOT in `_schema.toml` (Phase 1 Plan 01-01 already added `cold_backfill_from_block` to `protocols/ichi.toml [protocol]` without tripping `make schema-frozen-check`).
   - What's unclear: whether `[panel]` is fully analogous (extending an existing protocol block) or needs to be a new TOML section. Same precedent applies.
   - Recommendation: Plan 02-NN adds `[panel]` block to `protocols/ichi.toml` and runs `make schema-frozen-check` — expected PASS. If it fails, decompose into a Phase-0-style schema increment with 2-way review.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | **pytest 9.0.3** (Python; analysis/) + **vitest 4.1.7** (TypeScript; fetch/) |
| Config file (Py) | `analysis/pyproject.toml` `[tool.pytest.ini_options]` (Plan 02-00 adds if absent) |
| Config file (TS) | `fetch/vitest.config.ts` (exists; Plan 02-NN extends `testInclude` for new Mento-historical-rate test) |
| Quick run command (Py) | `cd analysis && uv run pytest tests/test_<module>.py -x -q` |
| Quick run command (TS) | `pnpm -C fetch test tests/<file>.test.ts --run` |
| Full suite command | `cd analysis && uv run pytest && pnpm -C fetch test --run` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PANEL-01 | JSONL cache → polars panel with all required event-provenance columns | unit | `uv run pytest analysis/tests/test_ingest.py::test_load_jsonl_provenance_columns -x` | ❌ Wave 0 |
| PANEL-01 | Zero null `blockNumber` rows after ingest | unit | `uv run pytest analysis/tests/test_ingest.py::test_no_null_block_number -x` | ❌ Wave 0 |
| PANEL-01 | Finality cutoff drops blocks > `forno_head - 120` | unit | `uv run pytest analysis/tests/test_ingest.py::test_finality_cutoff_120 -x` | ❌ Wave 0 |
| PANEL-01 | Mint/Burn ABI decode produces typed payload columns | unit | `uv run pytest analysis/tests/test_decoders.py -x` | ❌ Wave 0 |
| PANEL-01 | Deposit/Withdraw ABI decode produces typed payload columns | unit | `uv run pytest analysis/tests/test_decoders.py::test_deposit_withdraw -x` | ❌ Wave 0 |
| PANEL-02 | `with_header` writes Parquet with all six required keys | unit | `uv run pytest analysis/tests/test_provenance.py::test_with_header_round_trip -x` | ❌ Wave 0 |
| PANEL-02 | `make lint-artifacts` rejects Parquet missing any header key | integration | `make lint-artifacts` (already wired Phase 1 — Phase 2 extends to grep ichi panels) | ❌ Wave 0 (extension) |
| PANEL-02 | `dataHash` round-trips byte-identically across two builds with same input | integration | `uv run pytest analysis/tests/test_panel.py::test_byte_identical_rebuild -x` | ❌ Wave 0 |
| PANEL-03 | Mento Broker rate snap at block N != head returns historical rate | integration | `pnpm -C fetch test tests/mento-historical-rate.test.ts --run` (mocked) | ❌ Wave 0 |
| PANEL-03 | USDT/USD column present and non-1.0 (separately sourced) | unit | `uv run pytest analysis/tests/test_fx_snap.py::test_usdt_usd_separate_column -x` | ❌ Wave 0 |
| PANEL-03 | Forward-fill activates when Broker reverts at block N | unit | `uv run pytest analysis/tests/test_fx_snap.py::test_forward_fill_unavailable -x` | ❌ Wave 0 |
| PANEL-03 | Every FX-snap row has `(source, block, rate, provenance_url)` | unit | `uv run pytest analysis/tests/test_fx_snap.py::test_provenance_per_row -x` | ❌ Wave 0 |
| PANEL-04 | Synthetic Transfer with `from = USDC adapter` is dropped | unit | `uv run pytest analysis/tests/test_phantom_filter.py::test_synthetic_usdc -x` | ❌ Wave 0 |
| PANEL-04 | Real captured fee-abstraction tx round-trips through filter correctly | integration | `uv run pytest analysis/tests/test_phantom_filter.py::test_real_usdt_fixture -x` | ❌ Wave 0 (real fixture capture in Plan 02-NN) |
| PANEL-04 | Filter does NOT drop Transfer between user ↔ DEX counterparty in same tx | unit | `uv run pytest analysis/tests/test_phantom_filter.py::test_preserves_legit_transfer -x` | ❌ Wave 0 |
| DEMAND-01 (enforce) | Phase 2 cost-ledger rows have `endpoint ∈ {"forno", "blockscout"}` only (never `"graph-mainnet"`) | integration | `uv run pytest analysis/tests/test_panel.py::test_no_graph_mainnet_in_ledger -x` | ❌ Wave 0 |
| Q96 fee | LP-fee for a hand-crafted in-range Swap matches reference computation | unit | `uv run pytest analysis/tests/test_revenue_leg.py::test_q96_in_range_fee -x` | ❌ Wave 0 |
| Q96 fee | LP-fee for an out-of-range Swap is zero | unit | `uv run pytest analysis/tests/test_revenue_leg.py::test_q96_out_of_range_zero -x` | ❌ Wave 0 |
| Q96 fee | Sum of vault LP-fees over a 1000-block window matches a captured `collectFees` event within 1% | integration | `uv run pytest analysis/tests/test_revenue_leg.py::test_collect_fees_cross_check -x` | ❌ Wave 0 (deferred to Plan 02-NN if collectFees capture is feasible) |

### Sampling Rate
- **Per task commit:** `uv run pytest analysis/tests/test_<just_changed_module>.py -x -q` (< 5s per file).
- **Per wave merge:** `cd analysis && uv run pytest -x` AND `pnpm -C fetch test --run`.
- **Phase gate:** Both suites green; `make lint-artifacts` passes; `make schema-frozen-check` passes; one captured ICHI vault panel byte-identical across two `make panel-ichi` runs.

### Wave 0 Gaps
- [ ] `analysis/tests/conftest.py` — shared fixtures (tmp_path, synthetic 10-Swap Parquet, mock vault state)
- [ ] `analysis/tests/fixtures/synthetic_swaps_n10.parquet` — hand-crafted edge cases (in-range, out-of-range, finality boundary, phantom-paired)
- [ ] `analysis/tests/fixtures/phantom_transfer_usdt_real.json` — captured via Blockscout probe (Plan 02-NN task)
- [ ] `analysis/tests/fixtures/phantom_transfer_synthetic.json` — deterministic synthetic
- [ ] `analysis/tests/fixtures/ichi_anchor_block_67000000_67001000.jsonl` — slice from Phase 1 cache
- [ ] `analysis/tests/test_ingest.py`, `test_decoders.py`, `test_phantom_filter.py`, `test_vault_state.py`, `test_revenue_leg.py`, `test_fx_snap.py`, `test_provenance.py`, `test_panel.py`
- [ ] `fetch/tests/mento-historical-rate.test.ts` — vitest test for the TS sidecar with mocked viem multicall
- [ ] `analysis/pyproject.toml` `[tool.pytest.ini_options]` section if not present (Plan 02-00 to verify)
- [ ] `Makefile` extension: `make panel-ichi` target that orchestrates TS sidecar generation + Python panel build + lint-artifacts in one shot
- [ ] `analysis/src/abrigo_x402/protocol_spec.py` — pydantic mirror of zod schema (Phase 2 introduces; Phase 1 only has zod side)

## Sources

### Primary (HIGH confidence)
- `Uniswap/v3-core` `UniswapV3Pool.sol` lines ~718-719 (`state.feeGrowthGlobalX128 += FullMath.mulDiv(step.feeAmount, FixedPoint128.Q128, state.liquidity)`) — fee accrual formula, verified via WebFetch 2026-05-26: <https://github.com/Uniswap/v3-core/blob/main/contracts/UniswapV3Pool.sol>
- `@mento-protocol/mento-sdk@3.2.8` source inspection in workspace `node_modules`:
  - `dist/core/constants/addresses.js` — confirmed Celo Broker `0x777A8255cA72412f0d706dc03C9D1987306B4CaD`, BiPoolManager `0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901`, USDm `0x765DE816845861e75A25fCA122bb6898B8B1282a`
  - `dist/services/quotes/QuoteService.d.ts` + `.js` — confirmed `getAmountOut` signature has NO `blockNumber` parameter
  - `dist/core/abis/broker.js` — confirmed bundled BROKER_ABI is incomplete (only `tradingLimits*`); full ABI must be supplied via `parseAbi([...])`
- Mento Broker.sol Solidity source (mento-protocol/mento-core) — `getAmountOut(address, bytes32, address, address, uint256)` signature verified via WebFetch 2026-05-26: <https://github.com/mento-protocol/mento-core/blob/develop/contracts/swap/Broker.sol>
- polars 1.41.0 runtime probe in workspace uv venv 2026-05-26 — confirmed `write_parquet(metadata={...})` + `read_parquet_metadata(path)` round-trip
- Celo official fee-abstraction docs <https://docs.celo.org/developer/fee-abstraction> — confirmed adapter address `0x2F25deB3848C207fc8E0c34035B3Ba7fC157602B` for USDC, decimal-adapter mechanism, FeeCurrencyAdapter wraps non-18-decimal tokens
- Phase 1 source-of-truth files in this repo: `fetch/src/blockscout/v1-getlogs.ts`, `fetch/src/decoders/uniswap-v3-swap.ts`, `fetch/src/cache/{key,manifest,parquet-writer}.ts`, `fetch/src/viem-clients.ts`, `fetch/src/constants.ts`, `notes/forno_head_snapshot.json`, `protocols/ichi.toml`

### Secondary (MEDIUM confidence)
- Uniswap V3 fee distribution write-up + RareSkills primer + Uniswap blog math primer — all confirm the `fee_amount × position_liquidity / pool_liquidity_at_swap_time` decomposition matches the canonical pool-side accumulator:
  - <https://blog.uniswap.org/uniswap-v3-math-primer>
  - <https://rareskills.io/post/uniswap-v3-concentrated-liquidity>
  - <https://atiselsts.github.io/pdfs/uniswap-v3-liquidity-math.pdf>
- polars + parquet metadata PR #21806 (added `metadata` param to `write_parquet`): <https://github.com/pola-rs/polars/pull/21806>
- Mento Protocol docs `Integrate the Broker` page (broker conceptual + getAmountOut/getAmountIn shape): <https://docs.mento.org/mento/build-on-mento/integration-overview/integrate-the-broker>
- Mento Protocol addresses page: <https://docs.mento.org/mento/build-on-mento/deployments/addresses>
- Celo Broker Celoscan verification: <https://celoscan.io/address/0x777a8255ca72412f0d706dc03c9d1987306b4cad>
- Celo 2025 Year in Review (fee abstraction abundance — 56% of fees paid in stables): <https://blockchain.news/flashnews/celo-2025-year-in-review-56-of-network-fees-paid-in-stablecoins-usdt-usdc-usdm-via-fee-abstraction>

### Tertiary (LOW confidence — flagged for verification in Plan 02-NN)
- Specific captured fee-abstraction tx hash involving USDT adapter `0x0e2a3e...` (Blockscout WebFetch was soft-blocked; live Blockscout v1 probe planned as Plan 02-NN task)
- Exact ICHI vault ABI surface for `0xe304b9...4176F` (`lowerTick()` vs `getLowerTick()` etc. — Plan 02-NN fetches verified source from Blockscout)
- Exact Mento exchangeId bytes32 for cKES↔USDm (panel-init Forno lookup is the canonical source)

## Metadata

**Confidence breakdown:**
- Q96 LP-fee formula: **HIGH** — directly read off Uniswap V3 source code; canonical formula
- Mento Broker historical-block snap: **HIGH** — addresses + signature verified live in node_modules + Celo official sources; SDK gap (no blockNumber) confirmed by source inspection
- PANEL-02 metadata pattern: **HIGH** — polars 1.41 native API runtime-probed in this workspace
- Phantom-transfer filter (mechanism): **HIGH** — Celo official docs confirm adapter pattern
- Phantom-transfer filter (real fixture): **MEDIUM** — mechanism understood; specific tx hash deferred to Plan 02-NN capture
- Finality cutoff: **HIGH** — one-line polars filter, no ambiguity
- Polars schema (Decimal precision): **MEDIUM** — runtime probe confirms general support; per-column Decimal scale needs unit-test verification
- Forno multicall vault state: **HIGH** — viem multicall against Multicall3 is standard pattern, Celo Multicall3 in viem chains.celo
- TS sidecar pattern: **HIGH** — extends the proven Phase 1 cache-sidecar pattern
- DEMAND-01 enforce-component: **HIGH** — definitional (Phase 2 never calls graph-mainnet)

**Research date:** 2026-05-26
**Valid until:** 2026-06-26 (30 days; library versions stable; chain addresses immutable; primary risk is Phase 2 discovering an unanticipated wrinkle in the ICHI vault ABI or a Mento Broker BiPoolManager-side breaker firing during a panel window)

---

*Researcher's note for the planner:* The two highest-uncertainty items in the brief — Q96 LP-fee math and Mento broker historical-block query — are now both **HIGH confidence**. The remaining LOW-confidence item is the real phantom-transfer fixture tx hash, which is a deterministic single-task capture, not a research gap. Recommend planning a Wave 0 task that runs the Blockscout probe to capture the fixture before any module starts depending on it.

---

## Corrigendum — §D Phantom-Transfer Adapter Mechanism (2026-05-26)

The pre-CIP-64 `FeeCurrencyWrapper` address `0x0e2a3e05bc9a16f5292a6170456a710cb89c6f72` cited in §D and §4 is a **retired contract** (confirmed via Blockscout `has_token_transfers:false`, zero Transfer participation in a 200k-block topic-correct probe back from head 67,896,653). It is the v1 adapter contract from Celo's older fee-abstraction model.

Celo's current (post-CIP-64) fee-currency mechanism whitelists ERC-20 tokens directly. When an EOA pays gas in USDT, the Celo client emits Transfer events **on the underlying USDT contract** (`0x48065fbBE25f71C9282ddf5e1cD6D6A887483D5e`) routed through a protocol-reserved dispatcher pseudo-address. Live distribution chain (empirically observed at head 67,918,258):

1. `EOA → 0x000000000000000000000000000000000ce106a5` — base fee paid into dispatcher (EOA-like, no code)
2. `0x000…Ce106A5 → 0xcd437749e43a154c07f3553504c68fbfd56b8778` — `FeeHandlerProxy` (verified; impl `FeeHandler`)
3. `0x000…Ce106A5 → 0x4200000000000000000000000000000000000011` — OP-Stack `SequencerFeeVault` predeploy (Celo runs as OP L2)
4. `0x000…Ce106A5 → <validator/proposer>` — tip portion (variable)

A canonical fixture is captured at `analysis/tests/fixtures/phantom_transfer_usdt_real.json` (tx `0x41a425582618efc57c412f090d87bf53a4af3867b43601b16e2fe836c1d1f7b5`, USDT value 7,475 wei ≈ $0.0075). The `phantom_filter.ADAPTERS` constant is extended with the three live pseudo-addresses; the original retired-wrapper constants are retained as no-op defenses.

This corrigendum supersedes §D's adapter-address claims; downstream pitfalls and code-path mechanics in §D are otherwise unchanged.
