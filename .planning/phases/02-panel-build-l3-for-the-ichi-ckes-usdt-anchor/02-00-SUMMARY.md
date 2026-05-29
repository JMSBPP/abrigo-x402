---
phase: 02-panel-build-l3-for-the-ichi-ckes-usdt-anchor
plan: 00
subsystem: infra
tags: [pytest, polars, pydantic, vitest, viem, mento, ichi, blockscout, scaffold]

# Dependency graph
requires:
  - phase: 01-l1-data-fetch-skeleton-free-tier-discipline
    provides: "Blockscout v1 getLogs client (FETCH-01), Forno head snapshot, viem celoClient, cost-ledger, content-addressed cache, protocol-spec loader, [protocol] cold_backfill_from_block precedent for per-protocol TOML fields"
provides:
  - "pytest infrastructure for analysis/ (config + conftest + fixtures dir)"
  - "9 Python module skeletons in abrigo_x402 package (ingest, decoders, phantom_filter, vault_state, revenue_leg, fx_snap, provenance, panel, protocol_spec)"
  - "[panel] finality_lag_blocks=120 field added to protocols/ichi.toml"
  - "ICHI vault ABI fixture (analysis/tests/fixtures/ichi_vault_abi.json) — canonical read-method fragment from Blockscout-v2 verified source"
  - "Mento cKES↔USDm exchangeId fixture (resolved via live Forno call)"
  - "Phantom-transfer real fixture (no-adapter-traffic-found fallback documented; synthetic remains load-bearing)"
  - "TS sidecar scaffolds: fetch/src/mento/historical-rate.ts + fetch/src/vault/state-snap.ts with verified addresses + ABI + signatures"
  - "2 vitest stub files with it.todo() placeholders for Plans 02-04 + 02-06"
affects:
  - "02-01 ingest (reads finality_lag_blocks; loads cache JSONL)"
  - "02-02 decoders (computes ICHI Deposit/Withdraw topic0 from fixture ABI signatures)"
  - "02-03 phantom_filter (consumes phantom_transfer_synthetic.json; phantom_transfer_usdt_real.json activates if adapter traffic surfaces)"
  - "02-04 vault state-snap (drops body into existing TS signature using captured ABI fragment)"
  - "02-05 revenue_leg (Q96 fee math using fee_tier from anchor_pool)"
  - "02-06 mento historical-rate (drops body using resolved exchangeId fixture)"
  - "02-07 provenance (parquet metadata header)"
  - "02-08 panel orchestrator (composes all modules)"

# Tech tracking
tech-stack:
  added:
    - "pytest 9.0.3 (Python test runner)"
    - "pydantic 2.13.4 (protocol_spec.py — typed mirror of TS zod schema)"
  patterns:
    - "Per-protocol TOML field addition gated by `make schema-probe` (PROBE_PASS required before edit; _schema.toml stays frozen)"
    - "TS sidecar scaffold pattern: Wave-0 ships signatures + verified addresses + ABI fragments; Wave-1 drops bodies into existing signatures"
    - "Python module skeleton pattern: docstring + type-hinted function signatures + NotImplementedError('Plan 02-NN') body; importable from tests immediately"
    - "Fixture capture pattern: live network call → JSON written under analysis/tests/fixtures/ with _meta block (source, captured_at, status). Offline tests read fixtures; live probes are one-shot scripts under fetch/scripts/"

key-files:
  created:
    - "analysis/src/abrigo_x402/__init__.py"
    - "analysis/src/abrigo_x402/ingest.py"
    - "analysis/src/abrigo_x402/decoders.py"
    - "analysis/src/abrigo_x402/phantom_filter.py"
    - "analysis/src/abrigo_x402/vault_state.py"
    - "analysis/src/abrigo_x402/revenue_leg.py"
    - "analysis/src/abrigo_x402/fx_snap.py"
    - "analysis/src/abrigo_x402/provenance.py"
    - "analysis/src/abrigo_x402/panel.py"
    - "analysis/src/abrigo_x402/protocol_spec.py"
    - "analysis/tests/__init__.py"
    - "analysis/tests/conftest.py"
    - "analysis/tests/fixtures/.gitkeep"
    - "analysis/tests/fixtures/phantom_transfer_synthetic.json"
    - "analysis/tests/fixtures/ichi_vault_abi.json"
    - "analysis/tests/fixtures/mento_cKES_USDm_exchange_id.json"
    - "analysis/tests/fixtures/phantom_transfer_usdt_real.json"
    - "fetch/src/mento/historical-rate.ts"
    - "fetch/src/vault/state-snap.ts"
    - "fetch/tests/mento-historical-rate.test.ts"
    - "fetch/tests/vault-state-snap.test.ts"
    - "fetch/scripts/resolve-mento-exchange-id.ts"
    - "fetch/scripts/capture-phantom-transfer.ts"
  modified:
    - "analysis/pyproject.toml"
    - "analysis/uv.lock"
    - "protocols/ichi.toml"

key-decisions:
  - "ICHIVault canonical function names: getTotalAmounts (NOT totalAmounts), baseLower/baseUpper (NOT lowerTick/upperTick), currentTick — pinned in fetch/src/vault/state-snap.ts VAULT_ABI verbatim from Blockscout-v2 verified source"
  - "Mento cKES↔USDm exchangeId 0x89de88b8eb790de26f4649f543cb6893d93635c728ac857f0926e842fb0d298b resolved live from BiPoolManager.getPoolExchange iteration (16 exchanges total)"
  - "Phantom-transfer real fixture: USDT-adapter saw zero Transfer activity in a 1M-block lookback (~11.6 days at Celo 1s/block); per plan-body authorization, status=no-adapter-traffic-found is documented and the synthetic fixture remains load-bearing"
  - "pydantic added to runtime deps (not just dev) — protocol_spec.py is imported by panel.py orchestrator and must be available at runtime"
  - "[panel] block landed in protocols/ichi.toml after schema-probe PROBE_PASS; same precedent as Plan 01-01's [protocol] cold_backfill_from_block (per-protocol field, _schema.toml untouched)"

patterns-established:
  - "Schema-probe-before-TOML-edit: every per-protocol field addition must run `make schema-probe` first; PROBE_PASS confirms the schema-frozen hook scans _schema.toml only"
  - "Sidecar-script-with-absolute-paths: one-shot probes in fetch/scripts/ resolve repo root via fileURLToPath(import.meta.url) join('..','..') because tsx cwd is fetch/ not repo-root"
  - "Fixture _meta block: every captured fixture starts with _meta = {source, url, captured_at, status} so downstream tests can detect resolved/unresolved/fallback states"

requirements-completed: [PANEL-01, PANEL-02, PANEL-03, PANEL-04, DEMAND-01]

# Metrics
duration: 9min
completed: 2026-05-26
---

# Phase 2 Plan 00: Panel-Build Scaffold + Load-Bearing Probes Summary

**Wave-0 scaffold: pytest config + 9 Python module skeletons + conftest + 4 fixtures + 2 TS sidecar scaffolds + `[panel] finality_lag_blocks=120` schema-probed addition + Mento cKES↔USDm exchangeId live-resolved + ICHIVault ABI captured from Blockscout-v2 verified source. Gates Wave 1b (02-01..02-07).**

## Performance

- **Duration:** 9 min
- **Started:** 2026-05-26T17:04:51Z
- **Completed:** 2026-05-26T17:13:18Z
- **Tasks:** 3
- **Files modified:** 23

## Accomplishments

- pytest infrastructure live in `analysis/`: `[tool.pytest.ini_options]` with `testpaths=["tests"]`, `pythonpath=["src"]`, dev-deps pytest 9.0.3 + runtime pydantic 2.13.4. `cd analysis && uv run pytest --collect-only` exits 0 with `collected 0 items`.
- 9 Python module skeletons under `analysis/src/abrigo_x402/` — each importable, each with module docstring + type-hinted function signatures + `NotImplementedError("Plan 02-NN")` body. `from abrigo_x402 import ingest, decoders, phantom_filter, vault_state, revenue_leg, fx_snap, provenance, panel, protocol_spec` returns clean.
- `protocols/ichi.toml` carries `[panel] finality_lag_blocks = 120` after `make schema-probe` returned PROBE_PASS; `make schema-frozen-check` still PASS against baseline `e9b214d`.
- 3 load-bearing fixtures captured to `analysis/tests/fixtures/`: ICHIVault ABI (13 entries: 9 view fns + 4 events from Blockscout-v2 verified source), Mento cKES↔USDm exchangeId (`0x89de88b8...d298b` resolved live from BiPoolManager among 16 exchanges), USDT-adapter phantom-transfer real (`status=no-adapter-traffic-found` fallback documented per plan-body authorization).
- 2 TS sidecar scaffolds: `fetch/src/mento/historical-rate.ts` (MENTO_ADDRESSES + BROKER_ABI + BIPOOL_ABI + FxSnapRow/Options + snapFxBlocks stub) and `fetch/src/vault/state-snap.ts` (VAULT_ADDRESSES + MULTICALL3_CELO + VAULT_ABI pinning canonical ICHIVault names + VaultStateRow/Options + snapVaultState stub). Plan 02-04 / 02-06 drop bodies into existing signatures.
- 4 new vitest test files (2 source + 2 test): 6 new tests passing + 10 `it.todo()` placeholders. Full Phase 1+2 suite: 13 files, 86 passed + 10 todo (Phase-1 80 baseline preserved + 6 new).
- `pnpm -C fetch exec tsc --noEmit` exits 0 across all new sidecar code.

## Task Commits

Each task was committed atomically:

1. **Task 1: pytest infra + 9 Python module skeletons + conftest + synthetic fixture** — `07edf46` (feat)
2. **Task 2: Schema-probe + add [panel] finality_lag_blocks=120 + capture 3 fixtures** — `d418a5a` (feat)
3. **Task 3: TS sidecar scaffolds + vitest stubs for Mento + ICHI vault** — `36f298b` (feat)

**Plan metadata commit:** pending (final commit will include this SUMMARY + STATE.md + ROADMAP updates)

## Files Created/Modified

### Created (analysis/)
- `analysis/src/abrigo_x402/__init__.py` — Python package docstring
- `analysis/src/abrigo_x402/ingest.py` — `load_jsonl` + `apply_finality_cutoff` signatures (PANEL-01)
- `analysis/src/abrigo_x402/decoders.py` — Uniswap V3 + ICHI vault topic0 constants + `decode_all` signature (PANEL-01)
- `analysis/src/abrigo_x402/phantom_filter.py` — `ADAPTERS` frozenset + `exclude_adapters` signature (PANEL-04)
- `analysis/src/abrigo_x402/vault_state.py` — `load_vault_state` + `attach_in_range` signatures
- `analysis/src/abrigo_x402/revenue_leg.py` — `compute_swap_fee` signature with Q96 docstring
- `analysis/src/abrigo_x402/fx_snap.py` — `FX_METHODS` enum + `load_fx_sidecar` + `attach_rates` signatures (PANEL-03)
- `analysis/src/abrigo_x402/provenance.py` — `REQUIRED_KEYS` + `with_header` + `assert_has_header` signatures (PANEL-02)
- `analysis/src/abrigo_x402/panel.py` — `build_panel` orchestrator signature
- `analysis/src/abrigo_x402/protocol_spec.py` — pydantic models (Protocol, AnchorPool, Vault, PanelConfig, ProtocolSpec)
- `analysis/tests/__init__.py` — test package marker
- `analysis/tests/conftest.py` — shared fixtures (fixtures_dir, tmp_panel, synthetic_swap_row_n10 10-row polars DataFrame)
- `analysis/tests/fixtures/.gitkeep` — track empty dir
- `analysis/tests/fixtures/phantom_transfer_synthetic.json` — 3-log deterministic fixture (Swap + adapter Transfer + counterparty Transfer)
- `analysis/tests/fixtures/ichi_vault_abi.json` — 13 ABI entries (9 view fns + 4 events) from Blockscout-v2 verified source for ICHIVault `0xe304b9...4176F`
- `analysis/tests/fixtures/mento_cKES_USDm_exchange_id.json` — exchangeId `0x89de88b8...d298b` resolved live from BiPoolManager
- `analysis/tests/fixtures/phantom_transfer_usdt_real.json` — fallback with `status=no-adapter-traffic-found` (zero adapter traffic in 1M-block window)

### Created (fetch/)
- `fetch/src/mento/historical-rate.ts` — Plan 02-06 scaffold; MENTO_ADDRESSES + BROKER_ABI + BIPOOL_ABI + types + snapFxBlocks throwing stub
- `fetch/src/vault/state-snap.ts` — Plan 02-04 scaffold; VAULT_ADDRESSES + MULTICALL3_CELO + VAULT_ABI (canonical ICHIVault names) + types + snapVaultState throwing stub
- `fetch/tests/mento-historical-rate.test.ts` — 2 describe blocks; 3 passing (snapFxBlocks signature, address book, ABI parse) + 5 it.todo for Plan 02-06
- `fetch/tests/vault-state-snap.test.ts` — 2 describe blocks; 3 passing (snapVaultState signature, address book, ABI pin) + 5 it.todo for Plan 02-04
- `fetch/scripts/resolve-mento-exchange-id.ts` — one-shot Forno probe (Plan 02-00); resolves cKES↔USDm exchangeId by iterating BiPoolManager.getPoolExchange
- `fetch/scripts/capture-phantom-transfer.ts` — one-shot Blockscout v1 probe (Plan 02-00); progressive-window scan for USDT-adapter Transfer logs; documented "No logs found" exception handling

### Modified
- `analysis/pyproject.toml` — add `[tool.pytest.ini_options]`, `[dependency-groups] dev` (pytest), `pydantic>=2.0` to deps
- `analysis/uv.lock` — refreshed (10 packages added: pytest, pydantic, etc.)
- `protocols/ichi.toml` — add `[panel] finality_lag_blocks = 120` block after `[protocol.anchor_pool]`

## Decisions Made

1. **ICHIVault canonical function names pinned to on-chain reality**: The contract exposes `getTotalAmounts`, `baseLower`, `baseUpper`, `currentTick`, `totalSupply` — NOT the plan-body-mentioned `totalAmounts`/`lowerTick`/`upperTick`. `VAULT_ABI` in `fetch/src/vault/state-snap.ts` reflects the Blockscout-v2 verified source verbatim; the fixture `_meta._naming_note` field documents this for Plan 02-04 consumers.

2. **Mento exchangeId resolved live, not stubbed**: The probe iterated all 16 exchanges in `BiPoolManager.getExchangeIds()` and matched by asset0/asset1 against `(cKES, USDm)`. Result `0x89de88b8eb790de26f4649f543cb6893d93635c728ac857f0926e842fb0d298b` cached to fixture for offline Plan 02-06 tests.

3. **Phantom-transfer real fixture: no-adapter-traffic-found is the documented status**: USDT-adapter `0x0e2a...c6f72` saw zero Transfer activity across windows 10k/50k/200k/1M blocks back from Forno head 67,896,653 (≈11.6 days). Plan body authorizes this fallback explicitly; `phantom_transfer_synthetic.json` remains the load-bearing fixture for Plan 02-03 unit tests until adapter traffic surfaces (potentially in Phase 6 with Steer iteration).

4. **pydantic moved to runtime deps**: `protocol_spec.py` is imported by `panel.py` orchestrator, so pydantic is a runtime dependency, not just dev/test. Bumped from 0 to 2.13.4 via `pydantic>=2.0` in `[project] dependencies`.

5. **Sidecar scripts use absolute path resolution**: `fileURLToPath(import.meta.url) → dirname → join('..', '..')` to compute repo root. tsx runs the scripts with `cwd = fetch/`, not repo root, so relative paths to `analysis/tests/fixtures/` would have broken without absolute-path resolution.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Doc] Plan-body acceptance assertion checked wrong ABI function name**

- **Found during:** Task 2 (ICHI vault ABI capture)
- **Issue:** Plan body's verification step (line 626) asserts `any(e.get('name')=='totalAmounts' for e in d.get('abi', d))`, but the ICHIVault contract on Celo exposes `getTotalAmounts` (with the `get` prefix). The plan-body acceptance test would have failed against a faithfully-captured fixture.
- **Fix:** Captured fixture reflects on-chain reality (`getTotalAmounts` is in the function set); SUMMARY documents the naming-note in the fixture's `_meta._naming_note`. Plan 02-04 + decoders.py pin canonical names from the fixture, not from the plan-body's draft assertion.
- **Files modified:** `analysis/tests/fixtures/ichi_vault_abi.json` (Task 2)
- **Verification:** Re-ran acceptance check with corrected name (`getTotalAmounts`, `baseLower`, `baseUpper`); all expected functions present.
- **Committed in:** `d418a5a` (Task 2 commit, with explicit `[Rule 1 - Doc]` note in commit body)

**2. [Rule 3 - Blocking] Phase-1 v1-getlogs client throws on "No logs found" upstream message**

- **Found during:** Task 2 (phantom-transfer capture script first run)
- **Issue:** The Phase-1 `getLogsV1` function in `fetch/src/blockscout/v1-getlogs.ts` treats `status=='0' && /No records/i.test(message) && result.length==0` as success-empty. Blockscout actually returns `"No logs found"` (not `"No records"`) for the USDT-adapter empty-result case, so the client throws an Error.
- **Fix:** Wrapped the `getLogsV1` call in the one-shot capture script in a try/catch that matches `/No (logs|records) found/i` and treats it as empty result. Did NOT modify `fetch/src/blockscout/v1-getlogs.ts` (out-of-scope per Scope Boundary: pre-existing-warning-in-unrelated-file). Logged to `deferred-items.md` is not warranted here — the client behavior is documented Phase-1 territory.
- **Files modified:** `fetch/scripts/capture-phantom-transfer.ts` (Task 2)
- **Verification:** Re-ran script; gracefully handled empty results across all 4 window sizes; fallback fixture written with documented status.
- **Committed in:** `d418a5a` (Task 2 commit)

**3. [Rule 3 - Blocking] Sidecar script cwd vs fixture path**

- **Found during:** Task 2 (Mento exchangeId probe first run)
- **Issue:** `pnpm -C fetch exec tsx scripts/resolve-mento-exchange-id.ts` runs with `cwd = fetch/`, so a relative write to `analysis/tests/fixtures/...` resolves under `fetch/analysis/...` and fails with `ENOENT`.
- **Fix:** Added `const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..')`; resolved `fixturePath = join(REPO_ROOT, 'analysis/tests/fixtures/...')` in both `resolve-mento-exchange-id.ts` and `capture-phantom-transfer.ts`. Pattern documented in SUMMARY as a sidecar-script-with-absolute-paths convention.
- **Files modified:** `fetch/scripts/resolve-mento-exchange-id.ts`, `fetch/scripts/capture-phantom-transfer.ts` (Task 2)
- **Verification:** Re-ran both scripts; fixtures written to correct locations.
- **Committed in:** `d418a5a` (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (1 doc, 2 blocking)
**Impact on plan:** All deviations were execution-mechanics adjustments, not scope changes. Plan-body's spec was preserved; only an incorrect acceptance assertion and two cwd-vs-message-format issues required minor adjustments. No fixture capture or module skeleton was redesigned.

## Issues Encountered

- USDT-adapter phantom-Transfer activity is zero in the last 1M Celo blocks. This is an empirical observation about the current Celo fee-abstraction layer (USDT gas-payments are rare on Celo as of 2026-05-26); the plan-body explicitly authorized this fallback so it is **not** a deviation. The synthetic fixture remains load-bearing for Plan 02-03; the real fixture activates if adapter traffic surfaces, e.g., in Phase 6 Steer iteration over cCOP/USDT where USDT gas-payments are more common.

## User Setup Required

None — no external service configuration required. The Forno endpoint at `https://forno.celo.org` is public and uncapped per DEMAND-01.

## Next Phase Readiness

**Wave 1b (Plans 02-01..02-07) unblocked.** Each Wave-1b plan can:
- `from abrigo_x402.<module> import <fn>` without `ImportError` (9 modules ship the import surface)
- Read fixtures from `analysis/tests/fixtures/` for offline unit tests (4 fixtures committed)
- Read `protocols/ichi.toml [panel] finality_lag_blocks = 120` via toml/pydantic at runtime
- Drop full implementations into existing TS signatures (`snapFxBlocks` in 02-06, `snapVaultState` in 02-04)
- Compute ICHI Deposit/Withdraw topic0 in 02-02 from the captured ABI's canonical event signatures

Per-plan downstream pickup:
- **02-01 ingest**: reads cache JSONL + applies finality cutoff using the 120-block field
- **02-02 decoders**: computes ICHI topic0 = keccak256('Deposit(address,address,uint256,uint256,uint256)') etc. from the captured ABI's event signatures
- **02-03 phantom_filter**: tests against `phantom_transfer_synthetic.json` (real fixture marked no-adapter-traffic-found per plan-body authorization)
- **02-04 vault_state**: drops `snapVaultState` body using VAULT_ABI canonical names (getTotalAmounts, baseLower, baseUpper, currentTick, totalSupply); Python `vault_state.py` reads the resulting Parquet
- **02-05 revenue_leg**: Q96 fee math using `fee_tier=100` from `protocols/ichi.toml [protocol.anchor_pool]`
- **02-06 fx_snap**: drops `snapFxBlocks` body using the resolved exchangeId fixture
- **02-07 provenance**: implements `with_header` + `assert_has_header` using polars 1.41 native `write_parquet(metadata=...)`
- **02-08 panel**: orchestrates all of the above end-to-end

No outstanding blockers. AF-10 fixture remains parked at `tests/fixtures/af_10_dune_plus/env_violating_parked.txt`.

## Self-Check: PASSED

All 26 claimed files exist on disk; all 3 task commits (`07edf46`, `d418a5a`, `36f298b`) verified in `git log`.

---
*Phase: 02-panel-build-l3-for-the-ichi-ckes-usdt-anchor*
*Completed: 2026-05-26*
