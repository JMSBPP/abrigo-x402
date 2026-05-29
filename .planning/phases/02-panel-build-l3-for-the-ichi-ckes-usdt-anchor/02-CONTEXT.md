# Phase 2: Panel Build (L3) for the ICHI cKES/USDT Anchor - Context

**Gathered:** 2026-05-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Materialize the event-level Parquet panel for ICHI on cKES/USDT (single-vault microcosm per Q-4 lock) from the Phase 1 Blockscout-v1 raw event cache. Each row carries on-chain provenance metadata (`blockNumber`, `blockHash`, `logIndex`, `txHash`, `contractAddress`, `event`, payload). Output Parquet files carry the metadata header (`chainId`, `contractAddress`, `blockRange`, `fetchTimestamp`, `dataHash`, `gitCommit`). FX rates snapped at event-block via Mento broker mid-rate (USDT/USD treated as a separate column, NEVER collapsed to 1.0). Phantom-transfer filter excludes the documented USDC/USDT fee-abstraction adapter Transfers from arrival counts.

</domain>

<decisions>
## Implementation Decisions

### Panel scope (carried from Phase 0 + Phase 1)
- Iter-1 panel: **single-vault cKES/USDT microcosm only** per Q-4 (Phase 0 lock). No per-protocol aggregate.
- Anchor pool: cKES/USDT Uniswap V3 (`0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F`) per `protocols/ichi.toml`.
- Anchor vault: single active ICHI cKES/USDT vault per `protocols/ichi.toml [vaults.<id>] active = true`.
- Cold-backfill from block `60000000` (per `protocols/ichi.toml [protocol] cold_backfill_from_block`).
- ~38 non-anchor ICHI vaults remain `active = false; reason = "v2-deferred"` — NOT in this panel.

### Event ingest (PANEL-01)
- Source-of-truth: Phase 1's Blockscout v1 etherscan-compat client (`fetch/src/blockscout/v1-getlogs.ts`), output cached as Parquet/JSONL under `data/raw/ichi/<pool>/<block_range>.parquet`.
- Phase 2 reads this cache via the content-addressed key from Phase 1 (`(chainId, contractAddress, blockRange)`); does NOT re-fetch from Blockscout.
- Event panel row schema (minimum): `blockNumber, blockHash, logIndex, txHash, contractAddress, event_name, ...payload_fields_per_event_type`. Zero null `blockNumber` rows (lint-enforced).
- Event types in scope: Uniswap V3 `Swap`, `Mint`, `Burn` on the anchor pool; ICHI vault `Deposit`, `Withdraw` on the anchor vault. Decoded via viem `decodeEventLog` (Phase 1 decoders + new decoders for Mint/Burn/Deposit/Withdraw in Phase 2).
- Polars is the panel-construction library per STACK.md (`polars 1.41.0`); pandas reserved for small estimation frames in Phase 3+.

### FX-rate snap (PANEL-03)
- **Primary**: Mento broker mid-rate at the event-block for cKES↔USDm conversion, queried via `@mento-protocol/mento-sdk` v3.2.8 (already pinned in `fetch/package.json`) called from a TypeScript helper invoked by the Python panel build, OR equivalent direct broker contract call via viem.
- **USDT/USD**: separate column (`usdt_usd_rate`), NEVER collapsed to 1.0. Per `notes/fx_snap_decision.md` requirement (ROADMAP SC).
- **`notes/fx_snap_decision.md`**: Phase 2 deliverable documenting alternatives considered (USDT/USD=1.0 collapse rejected; Chainlink CELO/USD; Pyth on-Celo; Mento broker mid-rate) and the justification for the Mento broker anchor.
- **Provenance**: every FX snap row carries `(source, block, rate, provenance_url)` so Phase 5 reproducibility manifest can verify each snap independently.
- **Fallback when Mento broker has no rate at a specific block**: Claude's Discretion at /gsd:plan-phase 2 — recommended approach is forward-fill from the most recent prior block where the broker did quote, with explicit `fx_snap_method = "forward_fill" | "exact"` column for provenance.

### Phantom-transfer filter (PANEL-04)
- **Exclusion set**: hardcoded adapter addresses per ROADMAP — USDC fee-abstraction adapter `0x2F25deB3848C207fc8E0c34035B3Ba7fC157602B`, USDT fee-abstraction adapter `0x0e2a3e05bc9a16f5292a6170456a710cb89c6f72`.
- **Implementation**: any `Transfer` event with `from ∈ {USDC_adapter, USDT_adapter}` OR `to ∈ {USDC_adapter, USDT_adapter}` is excluded from arrival counts. Documented in unit test against a known fee-abstraction transaction.
- **Broader structural heuristic** (Transfer-without-paired-Swap-in-same-tx) is **NOT** the Phase 2 filter — too risky for false-positive filtering of legitimate transfers. Deferred to Phase 7 (cross-iteration synthesis) if needed.

### Provenance metadata (PANEL-02)
- Every Parquet output + `fit_report.json` scaffold + plot carries the header: `{chainId, contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit}`.
- `make lint-artifacts` (already wired in Phase 1 Makefile) greps each output file for the header fields and exits non-zero on any missing field.
- Header injection: panel construction wraps output writes in a `with_header(...)` helper from `analysis/src/abrigo_x402/provenance.py`.

### Reorg / finality handling
- Blockscout v2 has no `block_consensus` field (Phase 1 research finding). Phase 2 mitigation: **finality cutoff at N blocks behind Forno head** at panel-build time.
- **N = 120 blocks** (~2 min at Celo 1s block time, matches Celo PoS soft-finality). Configurable via `protocols/ichi.toml [panel] finality_lag_blocks`.
- Events on blocks `> (forno_head - 120)` are EXCLUDED from the Phase 2 panel and flagged for re-ingest on next refresh.
- `notes/forno_head_snapshot.json` (Phase 1 artifact) is the Phase 2 head reference for deterministic dry-run; live refresh uses Forno directly (DEMAND-01-excluded from cost-ledger as Forno is uncapped).

### LP-fee accrual leg
- **Approach**: Q96 tick math from raw Swap events × pool fee tier × in-range vault liquidity share — per RESEARCH §I fallback path (subgraph dormant per Phase 1 hunt verdict).
- **Vault state ingestion**: direct Forno `eth_call` to the ICHI vault contract per Swap event for `totalAmounts()`, `totalSupply()`, `currentTick()`. Forno is free at any volume (DEMAND-01-excluded), but batched per block for efficiency.
- **Implementation**: `analysis/src/abrigo_x402/revenue_leg.py` — pure-function decomposition: `compute_swap_fee(swap_event, pool_fee_tier_bps, in_range_liquidity_share)` returning fee in token0 + token1 units; then FX-snap to USD via the Phase 2 FX module.
- **Phase 2 ships LP-fee per Swap row**, NOT aggregated. Phase 3 aggregates as needed for DGP estimation.
- **In-range check**: vault is in-range for a Swap if `vault.lower_tick ≤ pool.current_tick ≤ vault.upper_tick` at the event block. Outside-range Swaps accrue zero LP-fees to the vault (verified per ICHI's auto-rebalance mechanics).

### Provenance + spot-check (PANEL-02 + REPORT-02 prep)
- Per-row `provenance_url` column: Blockscout link of the form `https://celo.blockscout.com/tx/<txHash>#eventlog`.
- 5-row spot-check sample for Phase 5 PDF deliverable derived from the panel's `provenance_url` column.

### Claude's Discretion
- **FX-snap method enum values** (`"exact" | "forward_fill" | "unavailable"`) — Claude proposes at /gsd:plan-phase time; values committed in PRE_REGISTRATION.md before any Phase 3 fit consumes them.
- **Vault state caching strategy** — per-block memoization, per-tx, or per-Swap; Claude chooses based on Forno call volume estimates.
- **Polars schema field types** (specifically `Decimal[38,18]` vs `Float64` for token amounts) — Claude proposes; tests verify byte-stable Parquet output.
- **Panel chunking** within the cache — single Parquet per pool's full block range OR per-1M-block chunk. Defaults to per-1M-block chunk for FETCH-04 cache idempotency granularity.
- **Mento SDK invocation**: TypeScript helper exporting JSON for Python ingestion OR Python-native Web3 contract call. Claude picks; both viable.
- **Phantom-transfer test fixture**: synthetic vs real-on-chain capture. Claude picks; recommended is a real captured fee-abstraction transaction from CANDIDATES.md research.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase-0 + Phase-1 governance carried forward
- `.planning/phases/00-candidate-eligibility-pre-registration/00-CONTEXT.md` — Q-4 single-vault, Q-7 floor, REPRO-03, pre-reg priors
- `.planning/phases/01-l1-data-fetch-skeleton-free-tier-discipline/01-CONTEXT.md` — hybrid Blockscout primary + subgraph dormant; cache key; cost-ledger schema
- `.planning/phases/01-l1-data-fetch-skeleton-free-tier-discipline/01-RESEARCH.md` — Blockscout v1/v2 split; no block_consensus on v2; Q96 tick math fallback (§I); subgraph downgrade verdict
- `.planning/phases/01-l1-data-fetch-skeleton-free-tier-discipline/01-VERIFICATION.md` — Phase 1 goal-backward verification (6/6 must-haves)
- `notes/PRE_REGISTRATION.md` — kernel forms, priors, acceptance regions
- `notes/PHASE_0_GATE.md` — ICHI five-check PASS; baseline `e9b214d`
- `notes/Q9_DECISION.md` — V3-only primary (cCOP only, not relevant to Iter-1)
- `notes/forno_head_snapshot.json` — Phase 1 head snapshot `67896653`
- `protocols/_schema.toml` (frozen at `e9b214d`)
- `protocols/ichi.toml` — full vault enumeration with `active`/`deferred` flags; `cold_backfill_from_block = 60000000`

### Project-level
- `.planning/PROJECT.md` — free-tier-only; USDT (not USDC) tail-risk framing; cost-leg modeled
- `.planning/REQUIREMENTS.md` — PANEL-01..PANEL-04 acceptance criteria; DEMAND-01 enforce-component
- `.planning/ROADMAP.md` — Phase 2 §Phase Details: 4 verbatim SCs

### Research substrate
- `.planning/research/STACK.md` — polars 1.41.0, Mento SDK 3.2.8, pyarrow 24.0.0
- `.planning/research/ARCHITECTURE.md` — L3 panel-build pattern; Parquet/JSON-manifest boundary; phantom-transfer rationale
- `.planning/research/PITFALLS.md` — §2 subgraph lag (mitigated via finality cutoff at 120 blocks); §5 phantom-transfer pollution rationale
- `.planning/research/CANDIDATES.md` — §7 hidden-volume audit (cKES/USDT ~4,440 swaps/30d); BrokerProxy + V4 PoolManager excluded from Iter-1 (cCOP-only contributions)

### Phase 1 source-of-truth
- `fetch/src/cost-ledger.ts` — Phase 2 writes ledger rows for any Forno `eth_call` (uncapped) or Blockscout call (uncapped) it makes
- `fetch/src/blockscout/v1-getlogs.ts` — bulk event source
- `fetch/src/decoders/uniswap-v3-swap.ts` — Phase 2 extends with Mint/Burn/Deposit/Withdraw decoders
- `fetch/src/cache/{key,manifest,parquet-writer}.ts` — Phase 2 reads from this cache layer
- `fetch/src/viem-clients.ts` — celoClient (used for `eth_call` to ICHI vault contracts at Forno)
- `fetch/src/constants.ts` — chain IDs, token addresses, Forno snapshot loader

### Phase 2 external dependencies (already pinned in analysis/pyproject.toml + uv.lock)
- `polars==1.41.0` — panel construction
- `pyarrow` (transitive via polars) — Parquet I/O
- `numpy==2.4.6`, `scipy==1.17.1` — numerical helpers

### Phase 2 deliverable docs (created by this phase)
- `notes/fx_snap_decision.md` — alternatives considered for FX snap source + justification
- `analysis/src/abrigo_x402/{ingest,revenue_leg,data_leg,provenance,fx_snap,phantom_filter}.py` — panel construction modules

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets (from Phase 1)
- `fetch/src/blockscout/v1-getlogs.ts` — bulk event fetcher; output already cached as Parquet under `data/raw/`
- `fetch/src/decoders/uniswap-v3-swap.ts` — Phase 2 extends pattern for Mint/Burn/Deposit/Withdraw
- `fetch/src/cache/{key,manifest,parquet-writer}.ts` — Phase 2 reads cache + manifest; new outputs written via the same provenance pattern
- `fetch/src/constants.ts` — addresses, chain IDs, Forno snapshot loader (Phase 2 uses for ICHI vault address + cKES/USDT pool address)
- `analysis/pyproject.toml` + `analysis/uv.lock` — Python deps pinned at Phase 1; Phase 2 fills `analysis/src/abrigo_x402/`
- `Makefile` — `lint-artifacts` target already exists; Phase 2 wires the metadata-header lint into it
- `.env.example` — env vars defined at Phase 1

### Established Patterns (from Phase 0 + Phase 1)
- Atomic plan-scoped commits (`feat(02-NN): ...`, `test(02-NN): ...`)
- 2-way review-trail hook fires only on `.planning/**/PLAN.md` or `.planning/ROADMAP.md` — Phase 2 source-code commits pass freely
- AF-10 fixture permanent-active workflow: temp-park (`tests/fixtures/af_10_dune_plus/.env.violating` → `env_violating_parked.txt`) for Phase 2 execution duration, restore at end with `--no-verify`
- Schema-frozen-check: do NOT modify `protocols/_schema.toml`; Phase 2 fields fit existing `[panel]` block or extend per `[panel].finality_lag_blocks` if needed (schema-probe required before any addition)
- Test framework: vitest 4.1.7 for TS (Phase 1 establishes pattern); pytest 9.0.3 for Python (Phase 2 introduces; pytest in analysis/pyproject.toml dev-deps)
- ESM `__dirname` rule via `testDirname(import.meta.url)` from `fetch/tests/_helpers.ts` (still applies for any new TS tests in Phase 2; Python uses standard `Path(__file__).parent`)

### Integration Points
- **Phase 2 → Phase 1**: reads `data/raw/ichi/<pool>/<block_range>.parquet` via the content-addressed cache; writes new Parquet panels under `data/raw/ichi/<pool>/panels/<block_range>.parquet`
- **Phase 2 → Phase 3**: produces `data/raw/ichi/<pool>/panels/<block_range>.parquet` + `analysis/src/abrigo_x402/{revenue_leg,data_leg}.py` modules that Phase 3 imports for DGP estimation
- **Phase 2 → cost-ledger**: any Forno `eth_call` for vault state writes a `forno`-endpoint row (uncapped per DEMAND-01)
- **Mento SDK invocation**: from Python via subprocess (Node script writes JSON, Python reads) OR via web3.py with hardcoded broker addresses. Claude's Discretion.

</code_context>

<specifics>
## Specific Ideas

- "Modeled cost-leg, real product test on Sepolia" framing from Phase 1 CONTEXT carries here: Phase 2 ingests free-tier data (Blockscout + Forno), no paid Graph queries, no real-USD outflow.
- Per-row provenance URLs (`https://celo.blockscout.com/tx/<txHash>#eventlog`) are the basis for Phase 5's 5-row spot-check sample — design the row schema to surface these directly.
- USDT/USD as a separate column with explicit provenance per snap is load-bearing for the eventual USDT-depeg sensitivity in Phase 4. Phase 2 ships the column even if no depeg has occurred in the panel window.
- Finality cutoff at 120 blocks (~2min Celo) is the cheap-and-defensible alternative to the missing `block_consensus` field; documented in `notes/fx_snap_decision.md` alongside the FX source choice.

</specifics>

<deferred>
## Deferred Ideas

- **Broader phantom-transfer heuristic** (Transfer-without-paired-Swap-in-same-tx) — deferred to Phase 7 cross-iteration synthesis if false negatives surface in Phase 2's hardcoded-address filter.
- **Per-vault aggregate panel** (multi-ICHI-vault, Q-4 retrospective substrate) — deferred to v2 per Phase 0 Q-4 lock (single-vault microcosm only in v1).
- **Real Mento V2 Broker + V4 PoolManager event panels** for cCOP corridor — Iter-2 / Phase 6, NOT Iter-1.
- **Steer LP-fee panel** — Phase 6 (which is structurally pre-disqualified at STRADDLE per Phase 0; Steer Iter-2 fires HEDGE-05 memo-only null).
- **Subgraph-based LP-fee** (typed `position` + `feeGrowthGlobal0X128`) — Phase 1.5 enrichment IF subgraph hunt later finds an acceptable Uniswap V3 Celo deployment; until then, Q96 tick math is the canonical Phase 2 path.

</deferred>

---

*Phase: 02-panel-build-l3-for-the-ichi-ckes-usdt-anchor*
*Context gathered: 2026-05-26*
