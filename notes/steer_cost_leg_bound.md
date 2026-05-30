---
verdict: FAIL
flag: marginal-demand
firing_condition: null_cost
band_lower: 30000
band_upper: 100000
free_tier_ceiling: 100000
rule: "not strictly > 100k -> FAIL (pre-registered, AF-03)"
---

# Steer cost-leg lower-bound check (REPRO-03 first step)

**Verdict: FAIL** — fires HEDGE-05 condition (a) `null_cost`.

This document is the REPRO-03 first-step artifact. It was emitted by
`scripts/cost_leg_check.py` applying the PRE-REGISTERED conservative-fail
straddle rule (see `notes/PRE_REGISTRATION.md` §"Phase 6 — Steer cost-leg
STRADDLE decision rule") to the pre-committed demand band in
`protocols/steer.toml [protocol.repro_03_verdict]`. **No demand was
re-estimated, re-enumerated, or narrowed** — Phase 6 only OBSERVES the verdict
the pre-committed band yields (AF-03).

## Decision

- Pre-committed band: **30,000–100,000** Celo-attributable Graph queries/mo
  (`STRADDLE`).
- Graph free-tier lower bound (DEMAND-01): **100,000** queries/mo.
- Rule: verdict = FAIL unless the band is STRICTLY ABOVE 100,000.
- 30,000 is **not strictly above** 100,000 → the band straddles / sits
  below the free-tier line → **FAIL** → `null_cost`.

## STRADDLE provenance (verbatim from protocols/steer.toml)

- channel_a: Blockscout factory enumeration: 6 active in-scope vaults (cCOP/USDT x3, cKES/USDT x1, cNGN/USDT x2)
- channel_b: Steer architecture: Gelato keeper-RPC class dominates; Graph subgraph reads are small analytics tail per DEMAND-01 keeper-RPC exclusion
- channel_c: DefiLlama TVL extrapolation: Steer-on-Celo TVL=$855.65 = 0.0041% of $20.64M multi-chain across 42 chains; TVL-proportional 8k-40k/mo; vault-count-proportional 48k-240k/mo; convergent best estimate in 30k-100k STRADDLE band
- synthesis: Two extrapolation channels disagree by ~6x (40k vs 240k upper bounds) — within 1 order of magnitude, not indeterminate. TVL-proportional is the more defensible default; convergent verdict is 30k-50k/mo (lower-leaning STRADDLE).

## Disposition

Steer is the intended FEATURES.md D-08 **negative control**: observing the
`null_cost` path fire at least once confirms the falsification machinery works in
practice. Per Iteration-2 resolution policy, the resolution on this null is to
**substitute a replacement candidate (pending — future milestone)**; that
candidate is NOT named or executed here, and any future substitute MUST be
pre-registered before its own data is seen (AF-03).
