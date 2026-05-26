# Requirements: abrigo-x402

**Defined:** 2026-05-25
**Core Value:** A pipeline that produces a calibrated joint cashflow function `C(t)` and a falsifiable DGP estimate (NHPP vs Hawkes) for a real Celo LP-aggregator protocol — using only free-tier data resources, with null results explicitly publishable.

## v1 Requirements

Requirements for Iteration 1 (ICHI on cKES/USDT) + Iteration 2 (Steer on cCOP/USDT). Each maps to a phase in `research/SUMMARY.md §Implications for Roadmap`. Categories follow the seven-layer architecture from `research/ARCHITECTURE.md`.

### Governance (pre-registration, anti-fishing discipline)

- [x] **GOV-01**: Pipeline must commit a pre-registration document (`notes/PRE_REGISTRATION.md`) listing kernel forms, prior parameters, test statistics, acceptance regions, and decision rules BEFORE any vault-level estimation runs
- [x] **GOV-02**: Each candidate protocol must pass the five-check Phase-0 eligibility gate (mainnet contract verified + Mento local-stable cashflow medium + ≥30 events/30d + ≥300 events lifetime + ≥60-day deployment age) before its iteration starts; gate result documented per candidate
- [x] **GOV-03**: Pipeline must reject all 12 anti-features from FEATURES.md (AF-01 mock-data validation, AF-02 hand-tuned p-values, AF-03 spec swap after seeing results, AF-04 retrospective category invention, AF-05 binning that destroys arrival signal, AF-06 strip-without-gate, AF-07 forced-Hawkes claim, AF-08 dashboard scope-creep, AF-09 single-fit no-comparison, AF-10 Dune-Plus-to-validate, AF-11 untimestamped fits, AF-12 silent re-scope); pre-commit lint/CI gate enforces

### Demand window (cost-leg definition)

- [x] **DEMAND-01**: Pipeline must verify the candidate's data-cost leg sits inside the demand window `[100k Graph queries/mo free-tier ceiling, $390/mo Dune Plus]`, defined narrowly as **indexer-backed analytics/UI queries only** (Graph subgraphs + Dune analytics); Forno RPC `eth_call` keeper polling is explicitly excluded as it falls below the lower bound at any volume

### Data fetch (L1 + L2)

- [x] **FETCH-01**: TypeScript `fetch/` workspace must bootstrap with viem 2.51 + `@x402/fetch 2.13` + `@graphprotocol/client-x402 1.0.0` + `graphql-request 7.4` + `@mento-protocol/mento-sdk 3.2.8` + Blockscout v2 REST client
- [x] **FETCH-02**: Cost-ledger module (`cost-ledger.ts`) must record every paid request with USDC cost in Parquet and abort cumulative monthly Graph spend at 90k queries (soft cap, 10k headroom below the 100k free-tier ceiling); `--force` flag required to bypass
- [ ] **FETCH-03**: Subgraph-freshness wrapper must include `_meta { block { number hash } }` in every Graph query and abort if lag vs Forno `eth_blockNumber` exceeds 100 blocks (~8 minutes); failure propagates with explicit error, never silently
- [x] **FETCH-04**: Cache layer (`data/raw/`) must be content-addressed by `(chainId, contractAddress, blockRange, fetchTimestamp)`; the paid-step-is-idempotent invariant must hold (re-running a fetch with identical inputs must produce identical outputs without re-paying)

### Panel construction (L3)

- [ ] **PANEL-01**: Pipeline must build event-level Parquet panels with on-chain provenance: each row carries `(blockNumber, blockHash, logIndex, txHash, contractAddress, event, ...payload)` columns, no aggregation/binning at this stage
- [ ] **PANEL-02**: Every fit artifact (parquet, fit_report.json, plots, PDF) must carry a metadata header listing `chainId, contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit`; outputs without the header are rejected by the build
- [ ] **PANEL-03**: FX-rate snap must use Mento broker mid-rate at the event block for cKES↔USDm (and equivalent pairs); USDT/USD must be treated explicitly with provenance, never collapsed to 1:1
- [ ] **PANEL-04**: Phantom-transfer filter must exclude USDC fee-abstraction adapter (`0x2F25deB3848C207fc8E0c34035B3Ba7fC157602B`) and USDT fee-abstraction adapter (`0x0e2a3e05bc9a16f5292a6170456a710cb89c6f72`) transfer events from arrival counts; the filter must be unit-tested against a known fee-abstraction transaction

### DGP estimation (L4)

- [ ] **DGP-01**: Pipeline must fit a non-homogeneous Poisson process via Kirchner 2015 INAR(p) on `statsmodels.tsa.api.VAR` with non-negativity projection; implementation validated against `tick.hawkes.SimuHawkesExpKernels` synthetic data within tolerance before any production fit
- [ ] **DGP-02**: Pipeline must fit a multivariate Hawkes process via `tick.HawkesExpKern` with the full off-diagonal excitation matrix (no diagonal-only shortcut that masks cross-leg self-excitation)
- [ ] **DGP-03**: Pipeline must perform the NHPP-vs-Hawkes likelihood-ratio test with the 50:50 χ²(0):χ²(1) mixture as the null distribution (per Filimonov & Sornette 2014, Wheatley ETH thesis, arxiv 2410.05008); bootstrap-LR rig must be used; vanilla `statsmodels.likelihood_ratio_test` is rejected
- [ ] **DGP-04**: Pipeline must run a held-out temporal evaluation (train/test split by time) and report out-of-sample log-likelihood for both models; in-sample fit alone is insufficient
- [ ] **DGP-05**: Pipeline must run the Brown et al. 2002 time-rescaling KS test on Hawkes residuals; failure to reject under NHPP rescaling is required before claiming the data is fit
- [ ] **DGP-06**: Pipeline must report branching-ratio confidence intervals via profile likelihood, not Hessian standard errors (per PITFALLS §4)

### Cross-leg dependence (L5)

- [ ] **DEPEND-01**: Pipeline must compute the cross-correlogram between `dK_revenue(t)` and `dK_cost(t)` arrivals + permutation null; report empirical copula on (dK_revenue, dK_cost) per FEATURES.md TS-09; vine copula fallback only if BIC prefers
- [ ] **DEPEND-02**: Any "joint" cashflow claim in the report must be backed by a cross-correlogram + permutation null + copula fit; a single bivariate scatter is insufficient evidence

### Hedge design (L6)

- [ ] **HEDGE-01**: Pipeline must run all four convex-dominance conditions from `SOMNIA_DRAFT.md §FUNCTIONAL FORM` against the joint cashflow before any Carr–Madan strip is computed: (1) vol-of-vol > 0, (2) positive skew / fat tails, (3) Hawkes self-excitation, (4) **USDT depeg + USDT/USDC basis jump** (substituted for the original USDC-depeg formulation). At least one condition must hold to justify the convex framing; otherwise the linear hedge is preferred and the strip is suppressed
- [ ] **HEDGE-02**: Carr–Madan strip implementation must use a convergence-tested grid (start 2^11 points, escalate to 2^12 if positivity check fails); implied density must be checked for negativity before strip emission; switch to COS or PROJ method when standard FFT-truncation produces negatives
- [ ] **HEDGE-03**: USDT depeg jump leg must be calibrated on USDT-specific depeg history (Merton or Kou jump-diffusion), not by porting USDC-anchored parameters; if a USDT-specific source is unavailable, the port must be explicitly documented as a methodological assumption with bounded sensitivity
- [ ] **HEDGE-04**: Strip-price stress test must run three-way joint-distribution scenarios (independence / fitted-joint / comonotone) and report all three; large divergence between scenarios is itself a finding
- [ ] **HEDGE-05**: Null-result emission template must fire when any of: (a) Phase-0 cost-leg gate fails for a candidate (this is now the leading firing condition for Steer Iteration 2 per CANDIDATES §6 Q6b — sample-size is no longer the binding constraint after the 2026-05-25 thinness-retraction audit), (b) NHPP-vs-Hawkes is indistinguishable at conventional α per DGP-03 (less acute than originally framed given the corrected swap counts: cKES/USDT ~4,440/30d, cCOP/USDT ~580–625/30d — but the boundary-correct LR test from DGP-03 can still fail to reject NHPP at moderate N if true η is small), (c) no convex-dominance condition holds per HEDGE-01. In each case, the deliverable PDF must document the null with the disqualifying evidence; null results are valid completions, not failures

### Reporting (L7)

- [ ] **REPORT-01**: Pipeline must render Iteration-1 deliverable as `reports/ichi.pdf` via Quarto or nbconvert; markdown-only artifacts are not acceptable final deliverables (per memory `feedback_pdf_deliverable.md`)
- [ ] **REPORT-02**: Report must include a spot-check checklist: 5 randomly-chosen panel rows with Blockscout URLs, manually verifiable by the reviewer (per FEATURES.md D-07)
- [ ] **REPORT-03**: Report must include cost-leg prior sensitivity sweep: ±50% perturbation of stipulated `(rate_per_event, USD_per_query)` parameters with all downstream estimates re-run (per FEATURES.md D-09)
- [ ] **REPORT-04**: Report must include reproducibility manifest: subgraph block-pins, `uv.lock`, `package-lock.json`, output checksums (per FEATURES.md TS-14); manifest must be sufficient for a fresh clone to reproduce the headline numbers

### Iteration-2 reproducibility (Steer swap)

- [ ] **REPRO-01**: Protocol-spec layer (`protocols/*.toml`) must be the only file class that changes between Iteration 1 (ICHI) and Iteration 2 (Steer); a `grep -r "ichi" fetch/src analysis/src` must return zero hits before Iteration 2 starts
- [ ] **REPRO-02**: Iteration 2 must run the same Phase 2–5 pipeline end-to-end on Steer-on-cCOP/USDT with no edits to `fetch/src` or `analysis/src`, demonstrating the parameter-driven re-runnability invariant (per FEATURES.md TS-12 + D-08)
- [ ] **REPRO-03**: Steer-on-Celo cost-leg lower-bound check must run as the first step of Iteration 2 (per CANDIDATES §6 Q6b); if the check fails, Steer drops to a documented null-result and Iteration 2 either defers or substitutes a replacement candidate — neither path involves modifying the pipeline code
- [x] **REPRO-04**: cCOP panel construction decision must be made and documented before Phase 6 estimation begins — either V3-anchor-only (~625 swaps/30d) or unified across V3 + V4 PoolManager + Mento V2 Broker (~900 events/30d per CANDIDATES.md §7). If unified, the pooling assumption (common arrival-process structure across the three event classes) must be either argued from primary sources or tested empirically (cross-class permutation test) before joint Hawkes estimation

## v2 Requirements

Acknowledged but deferred. Not in Iteration 1 or Iteration 2 scope.

### DGP refinements (Iteration 3+)

- **DGP-V2-01**: Kernel-class robustness test (exponential vs power-law Hawkes) per FEATURES.md D-02 — fires only if Hawkes wins the LR test in Iteration 1
- **DGP-V2-02**: Bootstrap confidence intervals on all DGP parameters per FEATURES.md D-04 — fires only if Hawkes wins the LR test in Iteration 1
- **DGP-V2-03**: Structural-break test on the arrival process per FEATURES.md D-06

### Hedge refinements (Iteration 3+)

- **HEDGE-V2-01**: Cross-protocol hedge-strip cost decomposition per FEATURES.md D-10 — requires at least two completed iterations
- **HEDGE-V2-02**: Deployed Solidity hedge contracts implementing the Carr–Madan strip on Celo (contingent on positive Iteration 1 result and a real-world counterparty)

### Multi-iteration synthesis

- **SYNTH-V2-01**: Per-protocol-vs-per-vault granularity retrospective with cross-iteration evidence (resolves CANDIDATES §6 Q4)
- **SYNTH-V2-02**: Updated `notes/methodological_refinements.md` documenting empirical findings on cost-leg lower bounds, sample-thinness thresholds, USDT depeg parameter ranges

**Note on Phase 7:** ROADMAP.md Phase 7 ("Cross-Iteration Synthesis") fires these two v2 requirements but is explicitly marked **PROCEDURAL — non-gating on v1**. v1 is complete when Phases 0–6 ship (REPORT-01..04 + REPRO-01..04 are the v1 closing requirements). Phase 7 may be deferred to a follow-on milestone without violating the v1 contract; running it in this milestone is optional substrate for the next iteration cycle.

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| MiniPay-hosted-app candidate filter | Superseded; MiniPay's enforced wallet scope (USDT/USDC/USDM only) is anti-correlated with the *local* Mento cashflows the FX-hedge thesis requires. See memory `project_abrigo_x402_minipay_scope` (SUPERSEDED) |
| Myriad / Halo as candidates | Disqualified primary-source: Myriad lists Celo mainnet as "Coming soon" and is points-based; Halo's production JS bundle is reward/points-dominant with non-Celo OP-stack predeploys |
| Mento Rewards as a candidate | Wrong demand structure — reward is a MENTO governance-token incentive, not data-cost-against-local-revenue |
| Walapay / Bridgers / generic SwapPools / Mento DAO Safes / SubsidyProgram / Sushi fee-collector / Ubeswap LP-token wrapper / bare-EOA top-holders | Anti-shortlist disqualifications per CANDIDATES.md §5 |
| Mento V3 FPMM as a candidate venue | Verified to hold zero local Mento stables via `FPMMDeployed` event log enumeration |
| Forno RPC `eth_call` keeper polling as the cost leg | Free at any volume → below the demand-window lower bound; not the cost class the hedge demand is defined for |
| Dune Plus subscription as a data source | Project's thesis is that x402 dominates Dune Plus for protocols in the demand window; purchasing it would invert the argument (per FEATURES.md AF-10) |
| Real x402 settlement on Celo | x402-foundation facilitator monorepo lists no Celo facilitator as of 2026-05-25; cost leg is modeled, not paid, in Iterations 1+2 |
| Deployed Solidity hedge contracts in Iterations 1+2 | Iteration 3+ stretch contingent on positive Iteration 1 result |
| All 12 anti-features (AF-01 through AF-12) from FEATURES.md | Listed individually in GOV-03 enforcement |

## Traceability

Each v1 requirement is mapped to exactly one phase as its primary phase (the phase where the requirement's deliverable artifact is produced). Some requirements have noted secondary fire/enforcement scope, but the primary phase assignment is the authoritative roadmap mapping per `.planning/ROADMAP.md`.

| Requirement | Primary Phase | Secondary Scope | Status |
|-------------|---------------|------------------|--------|
| GOV-01 | Phase 0 | — | Complete (Plan 00-01, commit `6cd61ed`) |
| GOV-02 | Phase 0 | Re-fires per candidate in Phase 6 | Complete (Plan 00-02, commit `a669d37`) |
| GOV-03 | Phase 0 | CI gate active in all phases | Complete (Plans 00-04 / 00-05 / 00-06 / 00-07, commits `e9b214d` schema + `aa2fcc8`+`24d054b` protocols + `fc653e8`+`ec5c492`+`13a7c99` hooks + `59f43f7`+`d87abef` install/validate) |
| DEMAND-01 | Phase 0 | Enforce-component in Phase 2 | Complete (Plan 00-02 verify-component, commit `a669d37`; enforce-component pending in Phase 2) |
| FETCH-01 | Phase 1 | — | Pending |
| FETCH-02 | Phase 1 | — | Pending |
| FETCH-03 | Phase 1 | — | Pending |
| FETCH-04 | Phase 1 | — | Pending |
| PANEL-01 | Phase 2 | — | Pending |
| PANEL-02 | Phase 2 | Headers required in all downstream artifact phases | Pending |
| PANEL-03 | Phase 2 | — | Pending |
| PANEL-04 | Phase 2 | — | Pending |
| DGP-01 | Phase 3 | — | Pending |
| DGP-02 | Phase 3 | — | Pending |
| DGP-03 | Phase 3 | LR test result feeds HEDGE-05 firing in Phase 4 | Pending |
| DGP-04 | Phase 3 | — | Pending |
| DGP-05 | Phase 3 | — | Pending |
| DGP-06 | Phase 3 | — | Pending |
| DEPEND-01 | Phase 4 | — | Pending |
| DEPEND-02 | Phase 4 | Enforced in Phase 5 report build | Pending |
| HEDGE-01 | Phase 4 | — | Pending |
| HEDGE-02 | Phase 4 | — | Pending |
| HEDGE-03 | Phase 4 | — | Pending |
| HEDGE-04 | Phase 4 | — | Pending |
| HEDGE-05 | Phase 4 (template built) | Firing conditions active in Phases 0, 3, 4, 6 | Pending |
| REPORT-01 | Phase 5 | Re-fires for Iteration 2 in Phase 6 | Pending |
| REPORT-02 | Phase 5 | Re-fires for Iteration 2 in Phase 6 | Pending |
| REPORT-03 | Phase 5 | Re-fires for Iteration 2 in Phase 6 | Pending |
| REPORT-04 | Phase 5 | Re-fires for Iteration 2 in Phase 6 | Pending |
| REPRO-01 | Phase 6 | Leak-check CI gate active continuously after Phase 1 | Pending |
| REPRO-02 | Phase 6 | — | Pending |
| REPRO-03 | Phase 6 (first step) | HEDGE-05 firing condition on failure | Pending |
| REPRO-04 | Phase 0 (decision artifact) | Enforcement in Phase 6 (panel construction follows the lock) | Complete (Plan 00-03 `5782527` + Plan 00-01 `6cd61ed`) |

**Coverage:**
- v1 requirements: 32 total
- Mapped to phases: 32 (REPRO-04 split across Phase 0 *decision component* + Phase 6 *enforcement component* per ROADMAP.md; counted once in the 32, not double-counted)
- Unmapped: 0 ✓
- Phase distribution: Phase 0 (5) + Phase 1 (4) + Phase 2 (4) + Phase 3 (6) + Phase 4 (7) + Phase 5 (4) + Phase 6 (3) + Phase 7 (0; consumes prior results, fires deferred v2 SYNTH reqs)

---
*Requirements defined: 2026-05-25*
*Last updated: 2026-05-25 after roadmap creation — Traceability section updated with final phase assignments per `.planning/ROADMAP.md`*
