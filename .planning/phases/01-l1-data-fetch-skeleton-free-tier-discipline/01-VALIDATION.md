---
phase: 1
slug: l1-data-fetch-skeleton-free-tier-discipline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-25
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework (TS)** | vitest 4.1.7 |
| **Framework (Python)** | pytest 9.0.3 (Phase 2 — placeholder only at Phase 1) |
| **Config file** | `fetch/vitest.config.ts` (Wave 0 creates) |
| **Quick run command** | `pnpm -C fetch test:unit --run` |
| **Full suite command** | `pnpm -C fetch test --run && pnpm -C fetch tsc --noEmit` |
| **Estimated runtime** | ~30–60 seconds full suite |

Source-of-truth: `01-RESEARCH.md §Validation Architecture` + STACK.md vitest pin.

---

## Sampling Rate

- **After every task commit:** Run `pnpm -C fetch test:unit --run` (subset matching the touched module)
- **After every plan wave:** Run `pnpm -C fetch test --run && pnpm -C fetch tsc --noEmit`
- **Before `/gsd:verify-work`:** Full suite must be green; `make verify-cache-idempotency` must pass
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-00-01 | 01-00 | 0 | (infra) | scaffold | `pnpm install && pnpm -C fetch tsc --noEmit` | ❌ W0 | ⬜ pending |
| 01-00-02 | 01-00 | 0 | (infra) | scaffold | `test -f fetch/vitest.config.ts` | ❌ W0 | ⬜ pending |
| 01-01-* | 01-01 | 1 | FETCH-01 | unit | `pnpm -C fetch test fetch/tests/stack-pins.test.ts --run` | ❌ W0 | ⬜ pending |
| 01-02-* | 01-02 | 1 | FETCH-02 | unit | `pnpm -C fetch test fetch/tests/cost-ledger.test.ts --run` | ❌ W0 | ⬜ pending |
| 01-03-* | 01-03 | 1 | FETCH-03 | unit | `pnpm -C fetch test fetch/tests/freshness.test.ts --run` (covers BOTH subgraph + blockscout paths per SC-3) | ❌ W0 | ⬜ pending |
| 01-04-* | 01-04 | 1 | FETCH-04 | integration | `pnpm -C fetch fetch ichi --pool 0x61Ef…829F --block-range 67800000-67800100 --dry-run && sha256sum data/raw/ichi/.../<file>.parquet (twice, byte-identical)` | ❌ W0 | ⬜ pending |
| 01-05-* | 01-05 | 1 | FETCH-01 SC-5 | lint+unit | `pnpm -C fetch test analysis/tests/test_panel_agnostic.py --run && pre-commit run leak-check --all-files` | ❌ W0 | ⬜ pending |
| 01-06-* | 01-06 | 2 | FETCH-02 SC-6 | unit | `pnpm -C fetch fetch ichi --dry-run --estimate-budget | jq '.total_queries < 30000'` | ❌ W0 | ⬜ pending |
| 01-07-* | 01-07 | 2 | (x402 mock) | integration | `pnpm -C fetch test fetch/tests/x402_mock.test.ts --run` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

Planner will refine task IDs and module names at /gsd:plan-phase 1 plan-authoring time; this table is a scaffold derived from the locked CONTEXT.md decisions + 01-RESEARCH.md sections A–M.

---

## Wave 0 Requirements

- [ ] **Workspace scaffolding** — `pnpm-workspace.yaml` at root listing `fetch/`; `fetch/package.json` with pinned versions per STACK.md (FETCH-01 SC-1); `fetch/tsconfig.json`; root `package.json` reduced to workspace metadata + dev tools
- [ ] **vitest config** — `fetch/vitest.config.ts` with ESM, no watch mode in CI, coverage off by default
- [ ] **biome config** — `fetch/biome.json` per STACK.md defaults
- [ ] **`analysis/uv.lock` pinned at Phase 1** per FETCH-01 SC-1 — `tick==0.8.0.2`, `statsmodels==0.14.6`, `polars==1.41.0`, `numpy==2.4.6`, `scipy==1.17.1`. `analysis/pyproject.toml` with empty src layout
- [ ] **`fetch/src/` skeleton** — empty directories for `cost-ledger/`, `cache/`, `freshness/`, `endpoints/blockscout/`, `endpoints/forno/`, `endpoints/graph/` (disabled-by-default), `x402-mock/`
- [ ] **`fetch/tests/` skeleton** — `stack-pins.test.ts`, `cost-ledger.test.ts`, `freshness.test.ts`, `cache-idempotency.test.ts`, `x402_mock.test.ts`, `protocol_agnostic.test.ts` — each as a `describe.todo` stub before the corresponding Wave 1 task fills it
- [ ] **`.env.example`** at repo root listing `PRIVATE_KEY` (Base Sepolia test-only), `CELO_RPC_URL` (defaults to forno), `BASE_SEPOLIA_RPC_URL` (defaults to sepolia.base.org), `BLOCKSCOUT_API_KEY` (optional free email signup), `GRAPH_API_KEY` (optional, only used if subgraph path is enabled)
- [ ] **`Makefile`** additions — `fetch-ichi`, `lint-artifacts`, `verify-cache-idempotency`, `schema-probe` targets
- [ ] **Schema-probe utility** — checks whether adding `[subgraphs.uniswap_v3]` block to `protocols/ichi.toml` would trigger the schema-frozen-check hook. Outputs PASS/FAIL before any subgraph wiring lands

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Base Sepolia faucet end-to-end | x402 product test | Faucet requires human interaction (CAPTCHA or wallet-connect); CI can't drain testnet ETH automatically | Run `pnpm -C fetch fetch ichi --dry-run --x402-mock-real-settle` from a developer machine with a faucet-funded wallet; verify `cost-ledger.parquet` contains `paid_real: true; chain: "base-sepolia"; tx_hash: "0x..."`; verify the tx on `sepolia.basescan.org` |
| Subgraph hunt verdict | Hybrid plan viability | Live indexer-count + lag verification needs network access from the developer machine; Phase 1 researcher already attempted but found candidates API-key-gated and 2-3yr stale | Developer provisions a Graph API key per their own account, runs `pnpm -C fetch verify-subgraph` against the candidate deployment IDs in 01-RESEARCH.md §A, decides PASS/FAIL/DOWNGRADE-TO-BLOCKSCOUT-ONLY. Default outcome (no key provisioned): downgrade per CONTEXT.md pre-registered fallback |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter after planner reconciles task IDs

**Approval:** pending — planner reconciles after Wave 0 scaffold lands
