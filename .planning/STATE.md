# State: abrigo-x402

**Last updated:** 2026-05-25

## Project Reference

**Core value:** A pipeline that produces a calibrated joint cashflow function `C(t)` and a falsifiable DGP estimate (NHPP vs Hawkes) for a real Celo LP-aggregator protocol — using only free-tier data resources, with null results explicitly publishable.

**Current focus:** Iteration 1 = ICHI on cKES/USDT anchor pool (locked 2026-05-25 post scope-correction). Iteration 2 = Steer on cCOP/USDT (gated on Iteration 1 PDF deliverable shipping + Steer cost-leg empirical lower-bound check).

**Pipeline shape:** Seven-layer architecture (L0 protocol-spec TOML → L1 TypeScript x402-aware fetch → L2 content-addressed Parquet cache → L3 Python panel → L4 NHPP+Hawkes DGP → L5 cross-leg dependence → L6 Carr–Madan + falsification → L7 PDF report).

## Current Position

**Phase:** 0 — Candidate Eligibility & Pre-Registration
**Plan:** (none yet — phase planning pending)
**Status:** Not started

```
Progress: [........] 0/8 phases complete
```

## Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Phases complete | 8/8 | 0/8 |
| Iteration 1 PDF deliverable | `reports/ichi.pdf` shipped | Not started |
| Iteration 2 swap-surface invariant | `grep -r "ichi" fetch/src analysis/src` returns 0 hits | N/A (no source code yet) |
| Free-tier query budget | < 90k Graph queries/mo (soft cap) | 0 consumed |
| v1 requirements complete | 32/32 | 0/32 |

## Accumulated Context

### Key Decisions Locked (from PROJECT.md scope-correction block)

- Iteration 1 = ICHI on cKES/USDT anchor pool
- Iteration 2 = Steer Protocol on cCOP/USDT (conditional on cost-leg empirical lower bound)
- Tail-risk reframe: USDT depeg + USDT/USDC basis risk (NOT USDC depeg)
- Minteo COPM allowed into scope under controlled-broadening flag
- Cost-leg = indexer-backed analytics/UI queries only (Forno RPC keeper polling excluded)
- MiniPay-by-preference filter retired (anti-correlated with FX-hedge thesis)
- Myriad / Halo excluded (primary-source disqualification)

### Decisions Pending (Phase 0)

- Q-9: cCOP panel construction — V3-anchor-only OR V3+V4+Broker unified (per CANDIDATES §7 Hidden-Volume Audit + REPRO-04). Must be locked in `notes/Q9_DECISION.md` before Phase 6.
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

**Last action:** Roadmap created (8 phases, 32/32 requirements mapped, 0 orphaned)
**Next action:** Plan Phase 0 (`/gsd:plan-phase 0`) — derive must-haves from Phase 0 success criteria
**Resume hint:** Phase 0 success criteria are concrete on-disk artifacts (`notes/PRE_REGISTRATION.md`, `notes/PHASE_0_GATE.md`, `notes/Q9_DECISION.md`, pre-commit hook, `protocols/_schema.toml` demand-window comment). Plan-phase should decompose these into executable plans + must-haves.

---

*Created: 2026-05-25 by `/gsd:new-project` roadmapper agent*
