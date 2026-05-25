---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
last_updated: "2026-05-25T20:24:29.900Z"
progress:
  total_phases: 8
  completed_phases: 0
  total_plans: 7
  completed_plans: 3
---

# State: abrigo-x402

**Last updated:** 2026-05-25

## Project Reference

**Core value:** A pipeline that produces a calibrated joint cashflow function `C(t)` and a falsifiable DGP estimate (NHPP vs Hawkes) for a real Celo LP-aggregator protocol — using only free-tier data resources, with null results explicitly publishable.

**Current focus:** Iteration 1 = ICHI on cKES/USDT anchor pool (locked 2026-05-25 post scope-correction). Iteration 2 = Steer on cCOP/USDT (gated on Iteration 1 PDF deliverable shipping + Steer cost-leg empirical lower-bound check).

**Pipeline shape:** Seven-layer architecture (L0 protocol-spec TOML → L1 TypeScript x402-aware fetch → L2 content-addressed Parquet cache → L3 Python panel → L4 NHPP+Hawkes DGP → L5 cross-leg dependence → L6 Carr–Madan + falsification → L7 PDF report).

## Current Position

**Phase:** 0 — Candidate Eligibility & Pre-Registration
**Plan:** 00-03 complete (Q9_DECISION.md committed `5782527`); 00-04 complete (protocols/_schema.toml frozen baseline committed `e9b214d`); Wave 1 sibling plans 00-01/00-02 in flight
**Status:** In Progress

```
Progress: [........] 0/8 phases complete  (Phase 0: 2/7 plans complete)
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

### Decisions Pending (Phase 0)

- Q-9 [LOCKED 2026-05-25 via Plan 00-03, commit `5782527`]: cCOP panel — V3-anchor-only primary + V3+V4+Broker unified fallback pre-registered (sample<300 OR CI>0.4, AND permutation p>0.05, 1000 reps, K-S D-max). REPRO-02 dead-code obligation on `analysis/src/abrigo_x402/panel/{unified,cross_class_permutation}.py`. REPRO-04 complete. See `notes/Q9_DECISION.md`.
- Q-4: Per-protocol vs per-vault granularity for ICHI Iteration 1 (recommendation per SUMMARY.md: per-protocol-aggregate with single-vault microcosm sensitivity; final lock in Phase 0, retrospective in Phase 7)
- Q-7: TVL-too-thin floor for cXOF/USDm and BRLm/EURm pools (Phase 0 commit; Phase 2 enforce)
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

**Last action:** Completed Plan 00-04 — `protocols/_schema.toml` authored + committed at `e9b214d` (SCHEMA_BASELINE_COMMIT for Plan 00-06/00-07). DEMAND-01 + GOV-03 marked complete in REQUIREMENTS.md.
**Next action:** Continue Wave 1 — siblings 00-01 (PRE_REGISTRATION.md) and 00-02 (PHASE_0_GATE.md) need to complete before Wave 2 (00-05 protocols/ichi.toml, 00-06 .pre-commit-config.yaml, 00-07 final PHASE_0_GATE substitution) can run.
**Resume hint:** SCHEMA_BASELINE_COMMIT = `e9b214dcb26d7a6085aa98765a3f8816950495eb`. Plan 00-06 references this hash in `make schema-frozen-check`; Plan 00-07 substitutes it into `notes/PHASE_0_GATE.md` `<SCHEMA_BASELINE_COMMIT>` placeholder. Plan 00-05 consumes the per-vault schema (`active` boolean + `mixing_class` enum + `address_resolution_status`) to enumerate ICHI's ~40 Celo vaults.

---

*Created: 2026-05-25 by `/gsd:new-project` roadmapper agent*
