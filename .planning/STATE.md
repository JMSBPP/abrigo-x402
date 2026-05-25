---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
last_updated: "2026-05-25T20:37:25.440Z"
progress:
  total_phases: 8
  completed_phases: 0
  total_plans: 7
  completed_plans: 6
  percent: 71
---

# State: abrigo-x402

**Last updated:** 2026-05-25

## Project Reference

**Core value:** A pipeline that produces a calibrated joint cashflow function `C(t)` and a falsifiable DGP estimate (NHPP vs Hawkes) for a real Celo LP-aggregator protocol — using only free-tier data resources, with null results explicitly publishable.

**Current focus:** Iteration 1 = ICHI on cKES/USDT anchor pool (locked 2026-05-25 post scope-correction). Iteration 2 = Steer on cCOP/USDT (gated on Iteration 1 PDF deliverable shipping + Steer cost-leg empirical lower-bound check).

**Pipeline shape:** Seven-layer architecture (L0 protocol-spec TOML → L1 TypeScript x402-aware fetch → L2 content-addressed Parquet cache → L3 Python panel → L4 NHPP+Hawkes DGP → L5 cross-leg dependence → L6 Carr–Madan + falsification → L7 PDF report).

## Current Position

**Phase:** 0 — Candidate Eligibility & Pre-Registration
**Plan:** 00-06 complete (`.pre-commit-config.yaml` + Makefile + 3 hook scripts + 12 AF fixtures committed `fc653e8`, `ec5c492`, `13a7c99`). Waves 1+2 all complete (00-01..00-06); Wave 3 plan 00-07 pending (`pre-commit install` + PHASE_0_GATE.md placeholder substitution + hook negative-case validation).
**Status:** In Progress

```
Progress: [████████░░] 86% (6/7 Phase-0 plans complete; 0/8 phases complete)
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

**Last action:** Completed Plan 00-05 — `protocols/ichi.toml` (299 lines, commit `aa2fcc8`) + `protocols/steer.toml` (166 lines, commit `24d054b`). L0 protocol-spec layer operationalized. GOV-03 + REPRO-04 closed at L0. AF-12 silent re-scope defense active at config layer (substrate expansion = boolean toggle, never row addition). M12 verified-before-fetch invariant enforced (10 verified + 17 pending in ichi.toml; 6 verified in steer.toml).
**Next action:** Verify parallel Wave-2 sibling 00-06 (.pre-commit-config.yaml + Makefile + scripts/pre-commit/) schema-frozen-check hook validates both committed TOMLs against `protocols/_schema.toml` (commit `e9b214d`). Then Wave 3 plan 00-07 substitutes SCHEMA_BASELINE_COMMIT hash into PHASE_0_GATE.md.
**Resume hint:** SCHEMA_BASELINE_COMMIT = `e9b214dcb26d7a6085aa98765a3f8816950495eb`. STEER_VERDICT_COMMIT = `a669d37` (PHASE_0_GATE.md STRADDLE). Q9_DECISION_COMMIT = `5782527`. ICHI_TOML = `aa2fcc8`. STEER_TOML = `24d054b`. Plan 00-07 PHASE_0_GATE.md placeholder substitution is independent of these TOMLs.

---

*Created: 2026-05-25 by `/gsd:new-project` roadmapper agent*
