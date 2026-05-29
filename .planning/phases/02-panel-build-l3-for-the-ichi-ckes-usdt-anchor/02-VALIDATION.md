---
phase: 2
slug: panel-build-l3-for-the-ichi-ckes-usdt-anchor
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-26
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework (Python)** | pytest 9.0.3 (introduced this phase) |
| **Framework (TS sidecars)** | vitest 4.1.7 (Phase 1 inheritance) |
| **Config file (Python)** | `analysis/pyproject.toml` `[tool.pytest.ini_options]` (Wave 0 creates) |
| **Quick run command** | `cd analysis && uv run pytest -x` |
| **Full suite command** | `cd analysis && uv run pytest && pnpm -C fetch test --run` |
| **Estimated runtime** | ~60–120 seconds full suite (panel construction + sidecar tests) |

Source-of-truth: `02-RESEARCH.md §Validation Architecture` + `analysis/pyproject.toml`.

---

## Sampling Rate

- **After every task commit:** Run `cd analysis && uv run pytest -x -k <module_pattern>` (subset matching the touched module)
- **After every plan wave:** Run `cd analysis && uv run pytest && pnpm -C fetch test --run`
- **Before `/gsd:verify-work`:** Full suite must be green; `make lint-artifacts` must pass on a sample panel Parquet
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-00-* | 02-00 | 0 | (infra) | scaffold | `cd analysis && uv sync && uv run pytest --collect-only` | ❌ W0 | ⬜ pending |
| 02-00-* | 02-00 | 0 | (probe) | acceptance | `make schema-probe && grep -c "finality_lag_blocks" protocols/ichi.toml` | ❌ W0 | ⬜ pending |
| 02-01-* | 02-01 | 1 | PANEL-01 | unit | `cd analysis && uv run pytest tests/test_ingest.py` | ❌ W0 | ⬜ pending |
| 02-02-* | 02-02 | 1 | PANEL-01 (decoders) | unit | `cd analysis && uv run pytest tests/test_decoders.py` (Swap/Mint/Burn/Deposit/Withdraw) | ❌ W0 | ⬜ pending |
| 02-03-* | 02-03 | 1 | PANEL-04 | unit | `cd analysis && uv run pytest tests/test_phantom_filter.py` (synthetic + real captured tx) | ❌ W0 | ⬜ pending |
| 02-04-* | 02-04 | 1 | PANEL-01 (vault state) | integration | `pnpm -C fetch test fetch/tests/vault-state.test.ts --run` (sidecar) + `cd analysis && uv run pytest tests/test_vault_state.py` | ❌ W0 | ⬜ pending |
| 02-05-* | 02-05 | 1 | (LP-fee Q96 math) | unit | `cd analysis && uv run pytest tests/test_revenue_leg.py` (worked example from RESEARCH §A) | ❌ W0 | ⬜ pending |
| 02-06-* | 02-06 | 1 | PANEL-03 | integration | `pnpm -C fetch test fetch/tests/mento-historical.test.ts --run` (sidecar) + `cd analysis && uv run pytest tests/test_fx_snap.py` | ❌ W0 | ⬜ pending |
| 02-07-* | 02-07 | 1 | PANEL-02 | unit | `cd analysis && uv run pytest tests/test_provenance.py` (polars 1.41 native metadata round-trip) | ❌ W0 | ⬜ pending |
| 02-08-* | 02-08 | 2 | PANEL-01..04 + DEMAND-01 | integration | `cd analysis && uv run pytest tests/test_panel_e2e.py` (full panel construction; ≥ 100 rows; provenance complete) | ❌ W0 | ⬜ pending |
| 02-09-* | 02-09 | 3 | (acceptance) | gate | `make lint-artifacts && cd analysis && uv run pytest && pnpm -C fetch test --run` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

Planner refines task IDs and module names at /gsd:plan-phase 2 plan-authoring time; this table is a scaffold derived from 02-CONTEXT.md decisions + 02-RESEARCH.md sections A–M.

---

## Wave 0 Requirements

- [ ] **pytest config** — `analysis/pyproject.toml [tool.pytest.ini_options]` with `testpaths = ["tests"]`, `addopts = "-ra --strict-markers"`
- [ ] **pytest-cov** (optional, deferred to Phase 5 if not needed at Phase 2) — added to `analysis/pyproject.toml` dev-deps if Wave 0 surfaces a coverage requirement
- [ ] **`analysis/src/abrigo_x402/__init__.py`** + module skeletons: `ingest.py`, `decoders.py`, `phantom_filter.py`, `vault_state.py`, `revenue_leg.py`, `fx_snap.py`, `provenance.py`, `panel.py`
- [ ] **`analysis/tests/conftest.py`** with shared polars DataFrame fixtures + `tmp_path` artifact paths
- [ ] **`analysis/tests/fixtures/`** directory for synthetic + real-captured fixtures
- [ ] **TS sidecar scaffolds** — `fetch/src/mento/historical-rate.ts` + `fetch/src/vault/state-snap.ts` (Phase 2 introduces these new modules in `fetch/src/`)
- [ ] **`protocols/ichi.toml [panel] finality_lag_blocks = 120`** field addition (schema-probe required first to verify no schema-frozen-check violation; precedent: Plan 01-01's `cold_backfill_from_block`)
- [ ] **Real phantom-transfer tx fixture capture** — Blockscout v1 probe for a recent cKES/USDT Swap tx with USDC/USDT fee-abstraction Transfer; snapshot to `analysis/tests/fixtures/`
- [ ] **ICHI vault ABI capture** — Blockscout verified-source fetch for the cKES/USDT anchor vault's actual `lowerTick()` / `upperTick()` / `totalAmounts()` / `totalSupply()` / `currentTick()` ABI surface
- [ ] **Mento exchangeId bytes32 for cKES↔USDm** — Forno lookup; cached to `data/raw/ichi/fx_rates/_exchange_ids.json`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Mento broker historical-block query against real Celo mainnet | PANEL-03 | Requires live Forno access; CI runs against synthetic fixtures only | Developer runs `pnpm -s -C fetch run mento:probe --block 67896653 --token-in cKES --token-out USDm` and verifies the returned rate matches the Celoscan event-log at that block |
| Full 30-day cKES/USDT panel build | PANEL-01..04 | Long-running (~5-15 min); CI smoke uses 100-block synthetic | Developer runs `cd analysis && uv run python -m abrigo_x402.panel --pool 0x61Ef…829F --block-range 67800000-67896653` and verifies output Parquet has ≥ 4000 swaps, provenance header complete, FX snap present for ≥ 99% of rows |
| Vault state Forno multicall throughput | PANEL-01 (vault state component) | Real Forno latency varies; CI mocks at fixed latency | Developer runs `pnpm -s -C fetch run vault-state:probe --pool 0x61Ef…829F --block-range 67800000-67896653` and measures wall-clock; flags if > 60s for 4400 events |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s for full Python suite
- [ ] `nyquist_compliant: true` set in frontmatter after planner reconciles task IDs

**Approval:** pending — planner reconciles after Wave 0 scaffold lands
