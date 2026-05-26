---
phase: 02-panel-build-l3-for-the-ichi-ckes-usdt-anchor
verified: 2026-05-26T18:17:17Z
verifier: gsd-verifier (goal-backward, post-hoc against working tree)
git_commit_at_run: 69b1b76
status: conditional
score: 5/6 truths fully verified; 1/6 conditional (single documented scope carve-out — SC-1 deferred to Phase 3 bulk pull to avoid double on-chain consumption)
re_verification: true
predecessor_artifact: 02-VERIFICATION.md (initial, 2026-05-26T18:00:00Z, status=conditional, score=4/6)
predecessor_predecessor_artifact: 02-VERIFICATION-pre.md (Plan 02-09 acceptance gate)
re_verification_delta:
  previous_status: conditional
  previous_score: 4/6
  previous_carve_outs:
    - "SC-4 literal: real on-chain fee-abstraction Transfer captured against live USDT-adapter bytes (Blockscout returned empty across 4 windows)"
    - "SC-1 literal: live data/raw/ichi/<pool>/<range>.parquet on disk (bulk on-chain pull deferred to Phase 3)"
  gaps_closed:
    - truth: "Truth 5 — PANEL-04 phantom-transfer filter unit-tested against real on-chain fee-abstraction tx per ROADMAP SC-4"
      closure_evidence: |
        Commit 69b1b76 ('feat(02-03): capture live CIP-64 fee dispatcher; close SC-4 real fixture').
        Architectural pivot uncovered: the previously-cited adapter at 0x0e2a3e05bc9a16f5292a6170456a710cb89c6f72
        is a retired pre-CIP-64 FeeCurrencyWrapper (Blockscout has_token_transfers:false, zero participation in
        200k-block topic-correct probe). Celo's live mechanism uses a protocol-reserved dispatcher pseudo-address
        0x000...Ce106A5 which routes USDT gas-fee Transfers to 0xcD437...8778 (FeeHandlerProxy) and 0x42...0011
        (OP-Stack SequencerFeeVault, since Celo runs as OP L2). Empirically captured live tx
        0x41a425582618efc57c412f090d87bf53a4af3867b43601b16e2fe836c1d1f7b5 at block 67,918,154 (head was
        67,918,258 at capture): EOA 0x71fb1bbf...11481d paid 7,475 wei USDT (~$0.0075) gas via CIP-64.
        Changes:
          - analysis/src/abrigo_x402/phantom_filter.py: ADAPTERS extended from 2 → 5 addresses
            (added CELO_CIP64_DISPATCHER + CELO_FEE_HANDLER + OP_SEQUENCER_FEE_VAULT; retained the two
            retired pre-CIP-64 wrappers as no-op safety constants). Filter logic unchanged.
          - analysis/tests/fixtures/phantom_transfer_usdt_real.json: replaced no-adapter-traffic-found
            stub with the real captured tx (_meta.status flipped from "no-adapter-traffic-found" to "captured").
          - analysis/tests/test_phantom_filter.py: test_adapters_constant_matches_individual_exports now
            asserts a 5-address set; test_real_fixture_roundtrip_when_captured is no longer skipped and
            passes against live USDT bytes (verified: pytest -v reports PASSED, not SKIPPED).
          - .planning/phases/02-…/02-RESEARCH.md: §D Corrigendum (lines 754-767) supersedes the §D
            adapter-address claim and documents the architectural pivot.
        SC-4 literal "real on-chain fee-abstraction tx" is now satisfied with live bytes, not just
        synthetic-real-shape. The human_verification entry from the initial verification ("re-probe
        Blockscout for USDT-adapter traffic") is consequently closed: traffic was found by probing the
        CORRECT dispatcher (CIP-64), not the deprecated wrapper.
  gaps_remaining:
    - truth: "Truth 2 — live data/raw/ichi/<pool>/<block_range>.parquet on disk per ROADMAP SC-1 literal"
      status: conditional
      reason: "Intentionally deferred to Phase 3 driver per pre-verification must_haves to avoid double on-chain pull (Phase 3 ingest re-runs the live pull anyway). Orchestrator code path remains fully validated by tests/test_panel_e2e.py (97-row panel from 100-block synthetic, 9/9 PASS)."
  regressions: []
  test_count_delta:
    py_before: "70 passed + 1 skipped (71 collected) across 8 files"
    py_after:  "71 passed + 0 skipped (71 collected) across 8 files"
    ts_before: "96 passed across 13 files"
    ts_after:  "96 passed across 13 files"
    total_before: "166 passing + 1 skipped"
    total_after:  "167 passing + 0 skipped"
human_verification:
  - test: "Live cKES/USDT panel Parquet on disk (ROADMAP SC-1 literal)"
    expected: "data/raw/ichi/<pool>/<block_range>.parquet exists and python -c 'import polars; df = polars.read_parquet(...); assert df.null_count().sum_horizontal()[0] == 0' exits zero"
    why_human: "Phase 2 deliberately defers the bulk on-chain pull to the Phase 2 → Phase 3 handoff (per must_haves.truths 'pre-panel-build skip OR post-panel-build pass'); orchestrator code path is fully validated by tests/test_panel_e2e.py (97-row panel from 100-block synthetic). Running the bulk pull is a budget-consuming Iteration-1 action that the verifier cannot trigger; verification deferred to next-phase entry."
---

# Phase 2 — Panel Build (L3) for ICHI cKES/USDT Anchor — Verification Report (Re-Verified)

**Phase Goal (per ROADMAP):** Materialize the event-level Parquet panel for ICHI on cKES/USDT (and the Q4 single-vault microcosm as sensitivity) with full on-chain provenance, Mento broker mid-rate FX snap, and the phantom-transfer filter for USDC/USDT fee-abstraction adapters.

**Verified:** 2026-05-26T18:17:17Z (working-tree commit `69b1b76`)
**Status:** `conditional` — 5 of 6 observable truths fully VERIFIED; 1 of 6 conditional (sole remaining carve-out is ROADMAP SC-1, deferred to Phase 3 bulk pull by design)
**Re-verification:** Yes — supersedes the initial `02-VERIFICATION.md` issued at 2026-05-26T18:00:00Z (status=conditional, score=4/6). One of the two prior carve-outs has been closed by commit `69b1b76`; the other remains by deliberate scope decision.
**Mode:** Goal-backward; full 3-level audit of the SC-4 closure delta; regression check on all other truths

## Re-Verification Delta vs Predecessor (2026-05-26T18:00:00Z)

### Closure of Truth 5 / ROADMAP SC-4 (previously CONDITIONAL → now VERIFIED)

The prior verification flagged Truth 5 as conditional because `test_real_fixture_roundtrip_when_captured` was gated on a `_meta.status == "no-adapter-traffic-found"` skip path — Blockscout returned empty USDT-adapter traffic across 4 probed windows. Commit `69b1b76` resolves this by uncovering an architectural error in RESEARCH §D and capturing real bytes against the **correct** dispatcher:

| Aspect | Before (initial verification) | After (this re-verification) |
| ------ | ----------------------------- | ---------------------------- |
| Adapter mechanism cited | Pre-CIP-64 `FeeCurrencyWrapper` at `0x0e2a3e05...c6f72` (RESEARCH §D / §4) | **Pre-CIP-64 wrapper retired** (Blockscout confirms `has_token_transfers:false`, zero participation). Live mechanism is CIP-64 protocol-reserved dispatcher `0x000…Ce106A5` (EOA-like, no code) which redistributes to `FeeHandlerProxy` (`0xcd437749…8778`) and OP-Stack `SequencerFeeVault` (`0x4200…0011`, Celo runs as OP L2). |
| `ADAPTERS` frozenset cardinality | 2 (`USDC_FEE_ADAPTER`, `USDT_FEE_ADAPTER`) | **5** (added `CELO_CIP64_DISPATCHER`, `CELO_FEE_HANDLER`, `OP_SEQUENCER_FEE_VAULT`; retained the 2 retired wrappers as no-op safety) |
| Real-fixture `_meta.status` | `"no-adapter-traffic-found"` | `"captured"` |
| Real-fixture tx | absent (stub) | `0x41a425582618efc57c412f090d87bf53a4af3867b43601b16e2fe836c1d1f7b5` (block 67,918,154; EOA `0x71fb1bbf…11481d` paid 7,475 wei USDT ≈ $0.0075 gas via CIP-64) |
| `test_real_fixture_roundtrip_when_captured` | SKIPPED | **PASSED** (verified live this run: `pytest -v` reports `PASSED [100%]`) |
| `test_adapters_constant_matches_individual_exports` | asserts 2-address set | asserts **5-address set** (updated) |
| RESEARCH.md §D | claims retired wrapper is the active adapter | **§D Corrigendum** at lines 754-767 explicitly supersedes the prior claim and documents the live dispatcher → FeeHandler → SequencerFeeVault distribution chain |
| Phase total tests | 70 Py pass + 1 skip + 96 TS = 166 pass + 1 skip | **71 Py pass + 0 skip + 96 TS = 167 pass + 0 skip** (verified live this run) |
| `human_verification[0]` from initial report ("re-probe Blockscout for USDT-adapter traffic") | open | **closed** — traffic was found by probing the correct CIP-64 dispatcher, not the deprecated wrapper |

This is not merely "the skip was removed." The closure required identifying that the address documented in REQUIREMENTS / RESEARCH §D was the wrong contract entirely (retired in CIP-64's rollout) and replacing it with the live dispatcher + downstream fee-distribution addresses. The phantom filter is now defended against the **actual** USDT fee-abstraction surface that Phase 3 DGP estimation will encounter.

### No regressions

- All 11 Wave-1 production modules unchanged outside `phantom_filter.py`; their predecessor VERIFIED status carries forward.
- All 11 key links remain WIRED (re-checked: `panel.build_panel` still chains the same 7-module pipeline; `phantom_filter.exclude_adapters` is still called at line 86 of `panel.py`).
- All other tests still pass with identical counts (8 Python test files, 13 TS test files; only `test_phantom_filter.py` increased from 11+1skip to **12+0skip**).
- `make schema-frozen-check`, `make schema-probe`, `make leak-check`, `pnpm exec tsc --noEmit`, `make lint-artifacts` (skip path) all still clean.

### Persisting carve-out

Truth 2 / ROADMAP SC-1 (live `data/raw/ichi/<pool>/<block_range>.parquet`) remains CONDITIONAL by deliberate scope decision: the bulk on-chain pull is reserved for the Phase 2 → Phase 3 handoff to avoid double-pulling (Phase 3 ingest re-runs it). The orchestrator code path is fully validated by `test_panel_e2e.py` (9/9, 97-row panel from 100-block synthetic). This carve-out was pre-disclosed in `02-VERIFICATION-pre.md` and is not a stub.

## Goal Achievement — Observable Truths (Updated)

| # | Truth                                                                               | Status        | Evidence                                                                                                                                                                                                                                                                                       |
| - | ----------------------------------------------------------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | Event-level Parquet panel code path exists, wires all 7 Wave-1 modules, idempotent  | VERIFIED      | `analysis/src/abrigo_x402/panel.py:50-111` (`build_panel` chains `ingest → finality cutoff → decode → phantom filter → vault state → revenue leg → fx snap`); `tests/test_panel_e2e.py` 9/9 pass including `test_build_panel_row_count` (`df.height == 97`) + `test_build_panel_idempotent`     |
| 2 | Live `data/raw/ichi/<pool>/<block_range>.parquet` on disk per ROADMAP SC-1 literal  | CONDITIONAL   | `find data/raw -name "*.parquet"` returns empty + `data/raw` directory does not exist (no bulk on-chain pull this phase); deferred to Phase 3 driver per `must_haves.truths` "pre-panel-build skip OR post-panel-build pass" — legitimate budget-discipline carve-out (Phase 3 ingest re-runs the live pull, avoiding double metered consumption) |
| 3 | PANEL-02 6-key metadata header on every output (`chainId, contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit`) | VERIFIED      | `analysis/src/abrigo_x402/provenance.py` (polars 1.41 native `write_parquet(metadata=...)` + REQUIRED_KEYS pre-write check + `assert_has_header`); 6/6 unit tests + `test_write_panel_has_metadata`; `make lint-artifacts` operational (skip path while panel dir empty)        |
| 4 | PANEL-03 Mento broker mid-rate FX snap with `(source, block, rate, provenance_url)` provenance; USDT/USD a SEPARATE column never collapsed to 1.0 (CLAUDE.md non-negotiable) | VERIFIED      | `notes/fx_snap_decision.md` (4 alternatives evaluated incl. USDT/USD=1 collapse explicitly rejected); `analysis/src/abrigo_x402/fx_snap.py:65-133` emits `cKES_per_USDm_rate + fx_method + fx_provenance_url + usdt_usd_rate + usdt_usd_method`; TS sidecar uses raw `viem.readContract({ blockNumber })` per Mento SDK 3.2.8 limitation; `test_usdt_usd_separate_column` + `test_cKES_rate_populated` PASS |
| 5 | PANEL-04 phantom-transfer filter excludes USDT/USDC fee-abstraction adapters AND CIP-64 dispatcher chain; unit-tested against real on-chain fee-abstraction tx per ROADMAP SC-4 | **VERIFIED** ↑ | **Closed by commit 69b1b76.** `phantom_filter.ADAPTERS` extended to 5 addresses (`CELO_CIP64_DISPATCHER` `0x000…Ce106A5` + `CELO_FEE_HANDLER` `0xcd437…8778` + `OP_SEQUENCER_FEE_VAULT` `0x42…0011` + retained retired wrappers as no-op safety). Real fixture `phantom_transfer_usdt_real.json` now carries live tx `0x41a4255826…c1d1f7b5` (USDT 7,475 wei via CIP-64). `test_real_fixture_roundtrip_when_captured` — verified live this run as **PASSED** (no longer skipped). 12 phantom-filter tests pass, 0 skip. Synthetic + real coverage both green. RESEARCH §D Corrigendum at lines 754-767 documents the architectural pivot (pre-CIP-64 wrapper is dead; CIP-64 dispatcher is live). |
| 6 | DEMAND-01 enforce: zero `endpoint='graph-mainnet'` ledger rows attributable to Phase 2 | VERIFIED      | `panel.assert_no_graph_mainnet_in_ledger` raises on any offending row; `test_demand_01_no_graph_mainnet` PASS; `data/raw/_cost_ledger.jsonl` does not exist (no metered traffic this phase — synthetic-only build, no Forno/Blockscout/Graph pulls); vacuous satisfaction is the correct verdict per protocol-spec invariant |

**Score:** **5/6 fully VERIFIED** + 1/6 CONDITIONAL (single remaining scope carve-out with documented human-verification entry above).

**Delta vs predecessor:** Score improved from 4/6 → 5/6. Truth 5 promoted from CONDITIONAL to VERIFIED. Truth 2 remains CONDITIONAL by design.

## Required Artifacts — Three-Level Check (Updated)

| Artifact                                                          | Lines | Exists | Substantive | Wired | Status       |
| ----------------------------------------------------------------- | ----- | ------ | ----------- | ----- | ------------ |
| `analysis/src/abrigo_x402/panel.py`                               | 160   | ✓      | ✓           | ✓     | VERIFIED     |
| `analysis/src/abrigo_x402/ingest.py`                              | 105   | ✓      | ✓           | ✓     | VERIFIED     |
| `analysis/src/abrigo_x402/protocol_spec.py`                       | 83    | ✓      | ✓           | ✓     | VERIFIED     |
| `analysis/src/abrigo_x402/decoders.py`                            | 275   | ✓      | ✓           | ✓     | VERIFIED     |
| `analysis/src/abrigo_x402/phantom_filter.py`                      | **84** ↑ | ✓ | ✓ (ADAPTERS expanded 2 → 5 incl. live CIP-64 dispatcher; docstring rewritten to document mechanism pivot) | ✓ | **VERIFIED** (delta-checked) |
| `analysis/src/abrigo_x402/vault_state.py`                         | 87    | ✓      | ✓           | ✓     | VERIFIED     |
| `analysis/src/abrigo_x402/revenue_leg.py`                         | 111   | ✓      | ✓           | ✓     | VERIFIED     |
| `analysis/src/abrigo_x402/fx_snap.py`                             | 133   | ✓      | ✓           | ✓     | VERIFIED     |
| `analysis/src/abrigo_x402/provenance.py`                          | 65    | ✓      | ✓           | ✓     | VERIFIED     |
| `fetch/src/mento/historical-rate.ts`                              | 151   | ✓      | ✓           | ✓     | VERIFIED     |
| `fetch/src/vault/state-snap.ts`                                   | 171   | ✓      | ✓           | ✓     | VERIFIED     |
| `notes/fx_snap_decision.md`                                       | 115   | ✓      | ✓           | n/a   | VERIFIED     |
| `protocols/ichi.toml [panel] finality_lag_blocks = 120`           | —     | ✓      | ✓           | ✓     | VERIFIED     |
| `analysis/tests/fixtures/ichi_vault_abi.json`                     | —     | ✓      | ✓           | ✓     | VERIFIED     |
| `analysis/tests/fixtures/mento_cKES_USDm_exchange_id.json`        | —     | ✓      | ✓           | ✓     | VERIFIED     |
| `analysis/tests/fixtures/phantom_transfer_usdt_real.json`         | —     | ✓      | **✓ live** ↑ | ✓     | **VERIFIED** (was ORPHANED/inert; now carries captured tx `0x41a4255826…c1d1f7b5` with `_meta.status="captured"`) |

**Stub check:** zero TODO / FIXME / XXX / HACK / PLACEHOLDER / NotImplementedError matches across all production modules (`grep -rn -E "TODO|FIXME|XXX|HACK|PLACEHOLDER|NotImplementedError" analysis/src/abrigo_x402/ fetch/src/mento/ fetch/src/vault/` returns empty — re-verified this run).

## Key Link Verification (Re-Checked)

| From                                | To                                       | Via                                                                | Status |
| ----------------------------------- | ---------------------------------------- | ------------------------------------------------------------------ | ------ |
| `panel.build_panel`                 | `ingest.load_jsonl + apply_finality_cutoff` | direct call chain, lines 79-84                                  | WIRED  |
| `panel.build_panel`                 | `decoders.decode_all`                    | direct call line 85                                                | WIRED  |
| `panel.build_panel`                 | `phantom_filter.exclude_adapters`        | direct call line 86 (filter now defends against 5 addresses, not 2) | WIRED  |
| `panel.build_panel`                 | `vault_state.load_vault_state + attach_in_range` | direct calls lines 88-89                                   | WIRED  |
| `panel.build_panel`                 | `revenue_leg.compute_swap_fee`           | Swap-only branch line 102 with `vault_liquidity` alias bridge      | WIRED  |
| `panel.build_panel`                 | `fx_snap.load_fx_sidecar + attach_rates` | direct calls lines 109-110                                         | WIRED  |
| `panel.write_panel`                 | `provenance.with_header`                 | direct call line 123 (thin wrapper)                                | WIRED  |
| `ingest.apply_finality_cutoff`      | `protocol_spec.panel.finality_lag_blocks` | `lag_blocks=protocol_spec.panel.finality_lag_blocks` line 83      | WIRED  |
| TS `fetch/src/mento/historical-rate.ts` | Python `fx_snap.load_fx_sidecar`     | JSONL contract (block, source, rate_x1e18, method, provenance_url) | WIRED  |
| TS `fetch/src/vault/state-snap.ts`  | Python `vault_state.load_vault_state`    | JSONL contract                                                     | WIRED  |
| `panel.assert_no_graph_mainnet_in_ledger` | `data/raw/_cost_ledger.jsonl`      | `endpoint='graph-mainnet'` row scan                                | WIRED  |

All 11 load-bearing links remain WIRED. No new orphans introduced by the SC-4 closure.

## Requirements Coverage (Updated)

| Requirement | Primary Phase | Description (REQUIREMENTS.md)                                                          | Status                        | Evidence                                                                                       |
| ----------- | ------------- | -------------------------------------------------------------------------------------- | ----------------------------- | ---------------------------------------------------------------------------------------------- |
| PANEL-01    | Phase 2       | Event-level Parquet with `(blockNumber, blockHash, logIndex, txHash, contractAddress, event, ...payload)` columns; no aggregation/binning | SATISFIED (code path) + NEEDS HUMAN (live parquet on disk) | `panel.build_panel` + `decoders.decode_all` + 9 e2e tests; bulk pull deferred to Phase 3 handoff |
| PANEL-02    | Phase 2       | 6-key metadata header on every output; build rejects header-less outputs               | SATISFIED                     | `provenance.with_header` enforces pre-write; `make lint-artifacts` operational; 6/6 unit tests + e2e metadata test |
| PANEL-03    | Phase 2       | Mento broker mid-rate at event block; USDT/USD separate column never collapsed to 1.0  | SATISFIED                     | `fx_snap.py` + TS sidecar + `notes/fx_snap_decision.md` (CLAUDE.md USDT non-negotiable enforced); 7 unit tests + 8 TS tests + e2e |
| PANEL-04    | Phase 2       | Exclude USDC + USDT fee-abstraction adapters; unit-tested against known fee-abstraction tx | **FULLY SATISFIED** ↑ | Adapter set now matches the **live** CIP-64 dispatcher chain (5 addresses), not just the retired wrappers; real-fixture roundtrip test PASSES against captured tx `0x41a4255826…c1d1f7b5`; RESEARCH §D Corrigendum (lines 754-767) documents the mechanism pivot |
| DEMAND-01   | Phase 0 verify + Phase 2 enforce | Pipeline enforces zero `endpoint='graph-mainnet'` ledger rows from indexer-only definition | SATISFIED (enforce component) | `panel.assert_no_graph_mainnet_in_ledger` raises on offending row; e2e test PASS; vacuous satisfaction this phase (no ledger file) |

**No orphaned requirements:** REQUIREMENTS.md maps PANEL-01..04 + DEMAND-01-enforce-component to Phase 2; every one is claimed by at least one plan's `requirements:` field. PANEL-04 has been materially strengthened by the SC-4 closure (live-bytes coverage, not just synthetic-real-shape).

## Anti-Patterns

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |

Empty — `grep -rn -E "TODO|FIXME|XXX|HACK|PLACEHOLDER|NotImplementedError" analysis/src/abrigo_x402/ fetch/src/mento/ fetch/src/vault/` returns zero hits (re-verified this run). The previous lone `pytest.skip` in `test_phantom_filter.py:162` is still present as defensive code (guards against a future fixture regression where `_meta.status` flips back to `no-adapter-traffic-found`), but it is no longer reached at runtime — the live fixture now satisfies the `status == "captured"` branch and the test PASSES rather than SKIPS.

## Live Verification Runs

All commands executed against working tree `69b1b76` at 2026-05-26T18:17Z:

| Command                                                 | Exit | Output Summary                                                                                                                                    |
| ------------------------------------------------------- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cd analysis && uv run pytest -q`                       | 0    | `71 passed in 0.32s` — **0 skipped** (delta: was 70 passed + 1 skipped at predecessor verification)                                                |
| `cd analysis && uv run pytest tests/test_phantom_filter.py::test_real_fixture_roundtrip_when_captured -v` | 0 | `1 passed in 0.01s` — explicit PASSED, not SKIPPED (this is the smoking-gun line for SC-4 closure)                                                |
| `pnpm -C fetch test --run`                              | 0    | `Test Files 13 passed (13); Tests 96 passed (96)` in 3.84s — unchanged from predecessor                                                            |
| `find data/raw -name "*.parquet"`                       | 0    | (no output; `data/raw` directory does not exist) — confirms Truth 2 remains CONDITIONAL by design                                                  |
| `grep -rn -E "TODO|FIXME|XXX|HACK|PLACEHOLDER" analysis/src/abrigo_x402/ fetch/src/mento/ fetch/src/vault/` | 0 | (no output) — zero anti-patterns in production modules                                                                                            |

Total: **71 Py + 96 TS = 167 pass / 0 skip / 0 fail** (matches the user-supplied claim verbatim).

## Goal-Backward Conclusion

**The codebase delivers what Phase 2 promised, with only one remaining documented scope carve-out (SC-1, deferred by design to the Phase 3 bulk-pull handoff).**

The SC-4 closure is substantive, not cosmetic. The prior verification correctly flagged the real-fixture test as skipped, but the root cause turned out to be deeper than "Blockscout returned empty windows" — RESEARCH §D had documented the wrong adapter contract. The pre-CIP-64 `FeeCurrencyWrapper` at `0x0e2a3e05…c6f72` is empirically dead (zero Transfer participation in a topic-correct 200k-block probe), and Celo's live CIP-64 native fee-currency mechanism routes USDT gas-fee Transfers through a different surface entirely: a protocol-reserved dispatcher pseudo-address (`0x000…Ce106A5`) that redistributes to `FeeHandlerProxy` and OP-Stack `SequencerFeeVault`. The phantom filter has been correctly extended to defend against all three live distribution-chain addresses (plus the two retired wrappers retained as no-op safety), and the real-fixture test now passes against captured tx `0x41a4255826…c1d1f7b5` (EOA paid 7,475 wei USDT ≈ $0.0075 gas via CIP-64). The §D Corrigendum at lines 754-767 of `02-RESEARCH.md` explicitly supersedes the prior claim. This is exactly the architectural pivot the phantom filter must encode to be useful in Phase 3 — otherwise DGP arrival counts would be inflated by exactly the gas-fee Transfers the filter was supposed to exclude.

**Gap 1 (CONDITIONAL — Truth 2 / ROADMAP SC-1 literal):** Unchanged from predecessor verification. No live `data/raw/ichi/<pool>/<block_range>.parquet` exists on disk. The orchestrator code path is fully validated against synthetic fixtures (97-row panel from 100-block synthetic). The bulk on-chain pull is deferred to the Phase 2 → Phase 3 handoff to avoid double-pulling (Phase 3 ingest re-runs the live pull). Documented as `must_haves.truths` "pre-panel-build skip OR post-panel-build pass." Single remaining human-verification entry. Not a stub — a deliberate budget-discipline carve-out.

**Gap 2 (CLOSED — Truth 5 / ROADMAP SC-4 literal):** Closed by commit `69b1b76`. See "Closure of Truth 5" section above.

**Blockers for Phase 3:** None. Phase 3 (DGP estimation) consumes the panel parquet via the same `ingest.load_jsonl` path the orchestrator already invokes. The live parquet write happens when the Phase-3-driver runs the bulk pull; the orchestrator code path is byte-stable, idempotent (`test_build_panel_idempotent` PASS), and now defends against the **correct** CIP-64 fee-abstraction surface — meaning Phase 3 arrival counts will not be polluted by gas-fee Transfers.

**Verdict:** `conditional` — phase goal achieved at code-path level **and** at live-bytes level for the phantom filter (5 of 6 truths fully verified); 1 of 6 truths remains conditional on a deliberate scope carve-out (SC-1 bulk-pull deferred to Phase 3 driver to avoid double on-chain consumption). The phase is **ready to proceed to Phase 3** with one residual human-verification item tracked above (re-run `make lint-artifacts` after Phase 3 bulk pull writes the first live panel parquet).

**Score progression:** 4/6 (initial, 2026-05-26T18:00Z) → **5/6** (this re-verification, 2026-05-26T18:17Z). Two carve-outs → **one carve-out**.

---

_Verified: 2026-05-26T18:17:17Z_
_Verifier: gsd-verifier (Claude Opus 4.7) — re-verification against working tree `69b1b76`; supersedes the initial `02-VERIFICATION.md` issued at 2026-05-26T18:00:00Z. Independent goal-backward audit of the SC-4 closure delta plus regression check on all other truths._
