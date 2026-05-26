---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: planning
last_updated: "2026-05-26T11:11:23.897Z"
progress:
  total_phases: 8
  completed_phases: 1
  total_plans: 16
  completed_plans: 8
  percent: 100
---

# State: abrigo-x402

**Last updated:** 2026-05-25

## Project Reference

**Core value:** A pipeline that produces a calibrated joint cashflow function `C(t)` and a falsifiable DGP estimate (NHPP vs Hawkes) for a real Celo LP-aggregator protocol — using only free-tier data resources, with null results explicitly publishable.

**Current focus:** Iteration 1 = ICHI on cKES/USDT anchor pool (locked 2026-05-25 post scope-correction). Iteration 2 = Steer on cCOP/USDT (gated on Iteration 1 PDF deliverable shipping + Steer cost-leg empirical lower-bound check).

**Pipeline shape:** Seven-layer architecture (L0 protocol-spec TOML → L1 TypeScript x402-aware fetch → L2 content-addressed Parquet cache → L3 Python panel → L4 NHPP+Hawkes DGP → L5 cross-leg dependence → L6 Carr–Madan + falsification → L7 PDF report).

## Current Position

**Phase:** 1 — L1 Data-Fetch Skeleton + Free-Tier Discipline — **IN PROGRESS (1/9 plans)**
**Current Plan:** 1 of 9
**Total Plans in Phase:** 9
**Last completed:** Plan 01-00 (pnpm workspace + fetch/ TS scaffold + analysis/ Python pins + schema-probe + Forno head snapshot + x402 v2.13 exports inventory). Four atomic 01-00 commits: `c46cbb7` (feat workspace + fetch scaffold) / `682ca13` (chore Python pin) / `eaf7de3` (feat Makefile + schema-probe) / `36dc615` (feat x402 exports + Forno snapshot + constants.ts).
**Status:** Wave 0 complete; Wave 1 unblocked

```
Progress: [█░░░░░░░░░] 11% (1/9 Phase-1 plans complete; 1/8 phases complete)
```

## Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Phases complete | 8/8 | 0/8 |
| Iteration 1 PDF deliverable | `reports/ichi.pdf` shipped | Not started |
| Iteration 2 swap-surface invariant | `grep -r "ichi" fetch/src analysis/src` returns 0 hits | N/A (no source code yet) |
| Free-tier query budget | < 90k Graph queries/mo (soft cap) | 0 consumed |
| v1 requirements complete | 32/32 | 0/32 |
| Phase 00-candidate-eligibility-pre-registration P03 | 15min | 1 tasks | 1 files |
| Phase 00 P04 | 4min | 1 tasks | 1 files |
| Phase 00-candidate-eligibility-pre-registration P01 | 30min | 1 tasks | 2 files |
| Phase 00-candidate-eligibility-pre-registration P02 | 4min | 2 tasks | 1 files |
| Phase 00-candidate-eligibility-pre-registration P05 | 5min | 3 tasks | 2 files |
| Phase 00 P06 | 5min | 3 tasks | 27 files |
| Phase 00 P07 | 30min | 3 tasks | 4 files |
| Phase 01-l1-data-fetch-skeleton-free-tier-discipline P00 | 7min | 4 tasks | 23 files |

## Accumulated Context

### Key Decisions Locked (from PROJECT.md scope-correction block)

- Iteration 1 = ICHI on cKES/USDT anchor pool
- Iteration 2 = Steer Protocol on cCOP/USDT (conditional on cost-leg empirical lower bound)
- Tail-risk reframe: USDT depeg + USDT/USDC basis risk (NOT USDC depeg)
- Minteo COPM allowed into scope under controlled-broadening flag
- Cost-leg = indexer-backed analytics/UI queries only (Forno RPC keeper polling excluded)
- MiniPay-by-preference filter retired (anti-correlated with FX-hedge thesis)
- Myriad / Halo excluded (primary-source disqualification)
- **Plan 00-04 SCHEMA-FROZEN BASELINE** [LOCKED 2026-05-25, commit `e9b214d` (full SHA `e9b214dcb26d7a6085aa98765a3f8816950495eb`)]: `protocols/_schema.toml` is the frozen baseline for `make schema-frozen-check`. `data_cost_class` enum = `[indexer-analytics-queries, per-event-oracle-stretch, per-scan-ocr-stretch]`. `mixing_class` enum = `[mento-native, minteo-fintech, mento-bridged]`. Demand-window scope (DEMAND-01) and AF-12 silent re-scope defense encoded in schema. Closes DEMAND-01 + GOV-03.
- **Plan 00-01 PRE-REGISTRATION LOCKED** [LOCKED 2026-05-25, commit `6cd61ed`]: `notes/PRE_REGISTRATION.md` (160 lines) commits all pre-fit thresholds — kernel forms (Kirchner INAR(p) NHPP + bivariate HawkesExpKern off-diagonal); priors (α=0.01, η≥0.2, rate_per_event grid (1,5,10), USD_per_query $5e-6 ±50%); bootstrap-LR 50:50 χ²(0):χ²(1) mixture; PITFALLS §4 four-criterion gate; REPRO-03 two-tier threshold (PASS ≥100k/mo, STRADDLE 30-100k marginal-demand, FAIL <30k below-window); Q-9 V3-only-primary + V3+V4+Broker-unified-fallback (trigger: sample<300 OR CI>0.4, AND cross-class permutation p>0.05); Q-7 floor (TVL<$10k OR events<30/30d); deferred substrate (COPM, cXOF/USDm, BRLm/EURm, ~38 non-anchor ICHI vaults); condition-4 reparam to USDT depeg + USDT/USDC basis (NOT USDC depeg) per CLAUDE.md. AF-03 audit anchor. Closes GOV-01 + REPRO-04.
- **Plan 00-02 PHASE_0_GATE LOCKED** [LOCKED 2026-05-25, commit `a669d37`]: `notes/PHASE_0_GATE.md` (117 lines) commits five-check eligibility outcome per candidate. **ICHI on cKES/USDT = PASS verbatim per CANDIDATES §4.1** (with §7.3 thinness retraction upgrading check 4 from BORDERLINE to PASS) — eligible for Iteration 1 anchor. **Steer on cCOP/USDT REPRO-03 verdict = STRADDLE** (30k–100k Celo-attributable Graph queries/mo per Phase-0 three-channel triangulation: Blockscout factory enumeration (6 active in-scope vaults), Steer architecture (Gelato keeper-RPC class excluded per DEMAND-01), DefiLlama TVL extrapolation ($855.65 = 0.0041% of $20.64M multi-chain across 42 chains)). Fires HEDGE-05 memo-only null with `marginal-demand` flag at Phase 0; Iteration 2 does NOT run Phase 1–5 cycle. `<SCHEMA_BASELINE_COMMIT>` placeholder embedded for Plan 07 substitution (target: schema baseline `e9b214dcb26d7a6085aa98765a3f8816950495eb`). Closes GOV-02 + DEMAND-01 (verify component).
- **Plan 00-05 PROTOCOL-SPEC TOMLS LOCKED** [LOCKED 2026-05-25, commits `aa2fcc8` (ichi.toml) + `24d054b` (steer.toml)]: `protocols/ichi.toml` (299 lines, 27 vault rows — 10 verified + 17 pending zero-address placeholders; 1 active anchor cKES_USDT_anchor at `0xe304b9...4176F` mento-native; 2 COPM Minteo vaults at `0x9F2bB8...FFce8` + `0xB52CfF...3FBF5` v2-deferred minteo-fintech; full ICHI Celo footprint enumeration deferred to Phase-1 factory-log pagination per [enumeration_status] block). `protocols/steer.toml` (166 lines, 6 vaults all verified) — Iter-2 stub; cCOP/USDT anchor `0x2AC5ba...17B0`; factory `0x116Dba...014C`; `panel_construction = "v3-anchor-only"`; `phase_0_repro_03_verdict = "STRADDLE"`; `phase_0_repro_03_flag = "marginal-demand"`; `hedge_05_fires = true`; Q-9 fallback metadata embedded verbatim from Q9_DECISION.md (sample_floor=300, ci_width_floor=0.4, permutation_reps=1000, p_threshold=0.05; V4 PoolManager `0x288dc8...87BC`; Mento V2 Broker `0x777A82...4CaD`). AF-12 silent re-scope defense active at L0; M12 verified-before-fetch invariant enforced. Closes GOV-03 + REPRO-04 at the L0 protocol-spec layer.
- **Plan 00-07 PRE-COMMIT HOOKS INSTALLED + VALIDATED** [LOCKED 2026-05-25, commits `59f43f7` + `b68cefa` + `13ccdf6` + `09e9b1a` + `d87abef` + `3d2af6b`]: pre-commit v4.6.0 installed via `uv tool install pre-commit`; `.git/hooks/pre-commit` dispatcher active; `notes/PHASE_0_GATE.md` schema-baseline placeholder substituted with `e9b214dcb26d7a6085aa98765a3f8816950495eb` (full SHA of `protocols/_schema.toml` Phase-0 commit); `make schema-frozen-check` exits 0 with PASS. 9 negative-case hook validations passed (Tests 1-9 in 00-07-SUMMARY.md): all 7 active AF fixtures (AF-01 mock-data, AF-03 structural-passthrough, AF-04 invalid-mixing-class, AF-06 strip-without-gate, AF-08 dashboard-dir, AF-10 Dune-Plus-permanently-active, AF-12 silent-re-scope) plus review-trail + schema-frozen demonstrably trigger exit-nonzero on their violating fixtures and exit-0 after cleanup. **3 Rule-1 hook auto-fixes applied during validation:** (1) AF-01 filename-pattern check added (`find -name "*fake_panel*"` etc.) so binary parquet fixtures are detected — original content-grep was blind to binary files; (2) AF-03 empty-operand guard added (`:-0` defaults on PRE_REG_TS / ANALYSIS_FIRST_TS) to prevent `integer expected` stderr noise when `analysis/src` exists without git history; (3) `review_trail.sh` + `.pre-commit-config.yaml` regex broadened from `^.planning/(.*/)?PLAN.md$` to `^.planning/.*PLAN.md$` so GSD convention `00-NN-PLAN.md` filenames are matched (original regex would have silently skipped enforcement on all actual plan files). **AF-10 `.env.violating` fixture is permanently active in repo by design (C2);** workflow for future commits: temporarily remove fixture + commit + `--no-verify` restore, OR `--no-verify` with documented rationale. Closes GOV-03 enforcement at the runtime pre-commit-gate layer. **Phase 0 complete: 7/7 plans landed.**
- **Plan 00-06 PRE-COMMIT INFRASTRUCTURE LOCKED** [LOCKED 2026-05-25, commits `fc653e8` (Makefile) + `ec5c492` (scripts/pre-commit/) + `13a7c99` (.pre-commit-config.yaml + 12 AF fixtures)]: Three-layer hook scaffolding for GOV-03 + review-trail + schema-frozen invariant. `.pre-commit-config.yaml` deploys 3 local-repo hooks via `pre-commit install` (Plan 00-07). `Makefile` with `schema-frozen-check` target reads `<SCHEMA_BASELINE_COMMIT>` from notes/PHASE_0_GATE.md and runs `git diff <baseline> -- protocols/_schema.toml`; defers to no-op while placeholder unsubstituted. `scripts/pre-commit/af_lint.sh` (154 lines) covers all 12 AFs — 7 active (AF-01, AF-03, AF-04, AF-06, AF-08, AF-10, AF-12) + 5 Phase-3+ deferred passthroughs (AF-02, AF-05, AF-07, AF-09, AF-11). C2 fix: AF-10 grep excludes `tests/unit` not `tests/`, so af_10_dune_plus/.env.violating IS detected by design. C3 fix: AF-12 uses `git cat-file -e HEAD:$f` for initial-commit handling. M13 fix: AF-08 find excludes `./tests/*`. `review_trail.sh` (76 lines) enforces paired `_reality_checker.md` + `_code_reviewer.md` with `## VERDICT` first H2; `--allow-revision` overrides NEEDS REVISION but never BLOCKER. `schema_frozen.sh` (4 lines) wraps `make schema-frozen-check`. 12 AF fixture dirs + 2 auxiliary (af_review_trail_missing + af_schema_frozen_diff). `tests/fixtures/README.md` (70 lines) resolves the AF-04 label drift: FEATURES.md "Hand-tuned bin width for INAR(p)" is canonical for *labels*; active hook check enforces REQUIREMENTS.md GOV-03 mixing_class enum interpretation since INAR(p) code is Phase-3+ deferred. Hooks NOT installed in this plan; Plan 00-07 runs install + validates each hook via negative-case tests. Closes GOV-03 operationalization at the pre-commit layer.
- **Plan 01-00 WORKSPACE BOOTSTRAP LOCKED** [LOCKED 2026-05-26, commits `c46cbb7` (feat workspace + fetch scaffold) + `682ca13` (chore Python pin) + `eaf7de3` (feat Makefile + schema-probe) + `36dc615` (feat x402 exports + Forno snapshot + constants.ts)]: pnpm workspace bootstrapped (pnpm-workspace.yaml lists fetch/ + analysis/); fetch/package.json pins exact-version deps per STACK.md (viem@2.51.0 / @x402/fetch@2.13.0 / @x402/evm@2.13.0 / @x402/core@2.13.0 / @graphprotocol/client-x402@1.0.0 / @graphprotocol/client-cli@3.0.7 dev-only / graphql-request@7.4.0 / @mento-protocol/mento-sdk@3.2.8 / zod@4.4.3); analysis/uv.lock pins tick==0.8.0.2 / statsmodels==0.14.6 / polars==1.41.0 / numpy==2.4.6 / scipy==1.17.1 (24 transitive packages against Python 3.13.5 via `uv lock`); fetch/src skeleton dirs (cost-ledger/, cache/, freshness/, endpoints/{blockscout,forno,graph}/, x402-mock/) + fetch/tests 10 describe.todo files (vitest run reports 10 skipped); Makefile Phase-1 targets (fetch-ichi / lint-artifacts / verify-cache-idempotency / schema-probe / full Phase-1 leak-check replacing Phase-0 stub); scripts/schema_probe.sh returns PROBE_PASS (schema-frozen hook scans _schema.toml only; [subgraphs.uniswap_v3] block deferred to Phase 1.5 retroactive enrichment); notes/forno_head_snapshot.json {head: 67896653, snapshotted_at: 2026-05-26T11:01:00Z} (Forno eth_blockNumber 0x40bf54d live pull); .planning/phases/01-l1-.../01-00-x402-exports.txt enumerates x402 v2.13 exports — x402Client + wrapFetchWithPayment + wrapFetchWithPaymentFromConfig + decodePaymentResponseHeader + x402HTTPClient in `@x402/fetch`; registerExactEvmScheme + ExactEvmScheme + createPermit2ApprovalTx in `@x402/evm/exact/client` subpath; `@x402/core` only exports x402Version (Plan 01-07 import resolution); fetch/src/constants.ts exports loadFornoHeadSnapshot + DRY_RUN_FALLBACK_HEAD (67896653) + CELO_CHAIN_ID (42220) + BASE_SEPOLIA_CHAIN_ID (84532) + CELO_USDT_ADDRESS (per _schema.toml canonical_celo_usdt) + BASE_SEPOLIA_USDC_ADDRESS; .env.example with PRIVATE_KEY / CELO_RPC_URL / BASE_SEPOLIA_RPC_URL / BLOCKSCOUT_API_KEY / GRAPH_API_KEY (empty/public defaults). 5 Rule-1/2/3 deviations auto-fixed (tsconfig rootDir/include narrowing; src/index.ts stub for TS18003; .gitignore /cache/ anchor fix to unmask fetch/src/cache/; extra constants for Wave 1 single-source-of-truth; Phase-0 leak-check stub replaced by Phase-1 three-class gate). pnpm install clean from fresh state; pnpm -C fetch exec tsc --noEmit exits 0; make schema-frozen-check PASS (baseline e9b214d unchanged); make leak-check PASS. **Wave 1 unblocked**: 01-01..01-05 parallelizable; 01-06 dry-run reads forno_head_snapshot.json; 01-07 x402 mock imports per 01-00-x402-exports.txt; 01-08 CLI integration uses `make fetch-ichi ARGS=...` pass-through.

### Decisions Pending (Phase 0)

- Q-9 [LOCKED 2026-05-25 via Plan 00-03, commit `5782527`]: cCOP panel — V3-anchor-only primary + V3+V4+Broker unified fallback pre-registered (sample<300 OR CI>0.4, AND permutation p>0.05, 1000 reps, K-S D-max). REPRO-02 dead-code obligation on `analysis/src/abrigo_x402/panel/{unified,cross_class_permutation}.py`. REPRO-04 complete. See `notes/Q9_DECISION.md`.
- Q-4: Per-protocol vs per-vault granularity for ICHI Iteration 1 (recommendation per SUMMARY.md: per-protocol-aggregate with single-vault microcosm sensitivity; final lock in Phase 0, retrospective in Phase 7)
- Q-7 [LOCKED 2026-05-25 via Plan 00-01, commit `6cd61ed`]: TVL floor = `TVL < $10k OR events < 30/30d`. cXOF/USDm `0xAA97…381a` (~$11k TVL) flagged marginal; BRLm/EURm `0xb6c8…dab5` (<$10k) deferred. Reconsideration triggers: cXOF/USDm if TVL≥$20k; BRLm/EURm if events/30d≥60. See `notes/PRE_REGISTRATION.md` §Q-7 Floor + §Deferred Substrate.
- USDT depeg jump-leg calibration source (Phase 4 lock)

### Active Todos

(none — phase planning pending)

### Active Blockers

(none — Phase 0 ready to plan)

### Substrate Findings (from research, 2026-05-25)

- cKES/USDT ~4,440 swaps/30d (14.8× above 300-event Hawkes floor) — SAMPLE-SIZE PASS for Iteration 1
- cCOP/USDT ~580–625 swaps/30d on V3 anchor; +185 Broker swap-equivalents/30d (cCOP only); +90 V4 swaps/30d (cCOP only) — SAMPLE-SIZE PASS for Iteration 2 (boundary on V3-only; comfortable if unified)
- PITFALLS §1 sample-thinness application to abrigo-x402 RETRACTED (was counting-artifact false positive due to 5s/block assumption; actual Celo block time is 1s/block post-2024 hardfork)
- Steer-on-Celo TVL $855 — cost-leg empirical lower-bound check is the binding constraint for Iteration 2 (Phase 6 first step per REPRO-03)
- x402-on-Celo settlement: no Celo facilitator in x402-foundation monorepo as of 2026-05-25; cost leg is MODELED, not paid, in Iterations 1+2

## Session Continuity

**Last session:** 2026-05-26T11:08:49Z
**Last action:** Completed Plan 01-00 (Wave 0 — pnpm workspace + fetch/ TS scaffold + analysis/ Python pin + Makefile Phase-1 targets + schema-probe utility + x402 v2.13 exports probe + Forno head snapshot + fetch/src/constants.ts). Four atomic 01-00 commits: `c46cbb7` (feat workspace + fetch scaffold; viem@2.51.0 + @x402/fetch@2.13.0 + @graphprotocol/client-x402@1.0.0 + @mento-protocol/mento-sdk@3.2.8 pinned exact) / `682ca13` (chore Python pins tick==0.8.0.2 + statsmodels==0.14.6 + polars==1.41.0 + numpy==2.4.6 + scipy==1.17.1 via `uv lock`) / `eaf7de3` (feat Makefile fetch-ichi+lint-artifacts+verify-cache-idempotency+schema-probe targets + scripts/schema_probe.sh PROBE_PASS) / `36dc615` (feat 01-00-x402-exports.txt — x402Client+wrapFetchWithPayment in @x402/fetch, registerExactEvmScheme in @x402/evm/exact/client subpath; notes/forno_head_snapshot.json head=67896653; fetch/src/constants.ts loadFornoHeadSnapshot+DRY_RUN_FALLBACK_HEAD+CELO_USDT_ADDRESS+BASE_SEPOLIA_USDC_ADDRESS; fetch/src skeleton dirs + 10 describe.todo tests; .gitignore Foundry anchor fix). 5 Rule-1/2/3 deviations documented in 01-00-SUMMARY.md (tsconfig rootDir/include fix; src/index.ts stub; .gitignore /cache/ anchoring; extra constants for Wave 1 single-source-of-truth; Phase-0 leak-check stub replaced by Phase-1 three-class gate).
**Next action:** Wave 1 plans (01-01 stack-pins test, 01-02 cost-ledger, 01-03 freshness wrappers, 01-04 Blockscout client + cache, 01-05 protocol-spec zod parse + leak gate) — parallelizable, all depend only on 01-00 outputs.
**Resume hint:** `pnpm install` resolves cleanly; `pnpm -C fetch exec tsc --noEmit` exits 0; `make schema-frozen-check` PASS; `make schema-probe` PROBE_PASS; `make leak-check` PASS. Wave 1 plans should import constants from `fetch/src/constants.ts` (single-source-of-truth for chain IDs + canonical token addresses) rather than re-declaring hex strings — `make leak-check` enforces this. AF-10 fixture remains parked (`env_violating_parked.txt`) for Phase 1 duration; orchestrator restores at end of phase.

---

*Created: 2026-05-25 by `/gsd:new-project` roadmapper agent*
