# Project Research Summary

**Project:** abrigo-x402
**Domain:** Empirical FX-cashflow DGP-estimation pipeline for LP-aggregator applications on Celo Uniswap V3 pools that pair Mento *local* stablecoins against USD-stables; Carr–Madan strip output as hedge-design sketch.
**Researched:** 2026-05-25 (post scope-correction)
**Confidence:** MEDIUM-HIGH (HIGH on stack + architecture + most pitfalls; MEDIUM on sample sufficiency of the chosen substrate; LOW on x402-on-Celo settlement infra, which does not exist yet and is modeled, not paid).

## Executive Summary

The project's original Iteration 1 candidate (Myriad-on-MiniPay) and its fallback (Halo) were both **disqualified during research** via primary-source verification: Myriad's own contract registry lists Celo mainnet as "Coming soon" and the MiniPay variant is points-based with no Mento-denominated cashflow leg; Halo's production JS bundle is reward/points-dominant with OP-stack predeploys indicating non-Celo settlement. The MiniPay-by-preference scope filter was itself retired because MiniPay's enforced wallet scope is USDT / USDC / USDM only — structurally anti-correlated with the *local* Mento stables (cCOP, cKES, cNGN, cGHS, cZAR, cXOF, BRLm) the FX-hedge thesis requires. Scope was broadened to **Celo apps with observable cashflows in Mento *local* stablecoins** (Path B2), and LP-aggregator discovery on Uniswap V3 Celo pools cleared exactly two applications out of an 8-entry anti-shortlist: **ICHI** (factory `0x9FAb…418F`, ≥ 40 vaults across every Mento local-stable pool surveyed — Iteration 1 anchor) and **Steer Protocol** (factory `0x116Dba…014C`, the only LP-aggregator on cCOP/USDT — Iteration 2).

The recommended approach is the seven-layer pipeline already specified in ARCHITECTURE.md (L0 protocol-spec TOML → L1 TypeScript x402-aware data-fetch → L2 content-addressed Parquet cache → L3–L6 Python panel / NHPP+Hawkes / dependence / Carr–Madan + falsification → L7 PDF reports), with two material adjustments forced by the candidate correction. **First**, the swap surface (`protocols/*.toml`) now needs an `ichi.toml` (Iteration 1, anchored on cKES/USDT at $130k TVL — the densest pool in the surveyed substrate) and a `steer.toml` (Iteration 2, on cCOP/USDT, contingent on a cost-leg lower-bound check because Steer's Celo footprint is small enough that its per-Celo data spend may sit *below* the demand-window lower bound). **Second**, the tail-risk parameterization in `SOMNIA_DRAFT.md §FUNCTIONAL FORM` condition (4) shifts from USDC-depeg (Hernandez Cruz 2024, Wu & Liu 2026) to **USDT depeg + USDT/USDC basis risk**, because the empirical counter-stable in every Celo Mento-local pool is USDT (`0x4806…3D5e`), not USDC. The USDC citations remain useful as methodological references but the actual stability anchor of the observed cashflow leg is USDT.

The key risks have all been catalogued in PITFALLS.md and mostly survive the scope correction; PITFALLS §1 (substrate-too-young / cashflow-medium-wrong, the Myriad-specific blocker) is *resolved* by the candidate switch but its *spirit* now applies as **sample-thinness on the chosen anchor pool**: cKES/USDT at $130k TVL is the densest available substrate but at ~130 swaps/30d still sits at-or-near the 300-event Hawkes floor, and cCOP/USDT at ~100–150 swaps/30d is below it. This forces an explicit accommodation in the estimation pipeline: report Hawkes-vs-NHPP indistinguishability as a publishable null when it occurs, lift the panel to ICHI's full multi-pool aggregate when feasible, and treat any cross-pool pooling as a modeling decision with provenance — not a sample-size laundering trick.

## Key Findings

### Recommended Stack

The stack is materially unchanged by the candidate correction — all libraries chosen in STACK.md (verified live via npm + PyPI on 2026-05-25) remain optimal for the new candidate set. The pipeline is TypeScript (data-fetch) + Python (estimation) with a Parquet/JSON-manifest file boundary; every dependency has a verified free-tier path. The single stack-level implication of the correction is that the protocol-spec TOMLs now describe LP-aggregator vault factories and their underlying Uniswap V3 pools, not prediction-market settlement contracts — a configuration change, not a code change.

**Core technologies:**
- **viem 2.51** + `@x402/fetch` / `@x402/evm` / `@x402/core` 2.13 — TS-side EVM and x402-aware payment plumbing; required because every adjacent EVM library here is viem-first.
- **`@graphprotocol/client-x402` 1.0.0** + **`@graphprotocol/client-cli` 3.0.7** (build-only) + **`graphql-request` 7.4** — paid-when-needed Graph access with the free-tier (`graphql-request`) carrying Iteration 1; verified that `@graphprotocol/client-x402` settles in USDC on **Base**, not Celo — see Pitfall flag below.
- **`@mento-protocol/mento-sdk` 3.2.8** — Mento broker / token / pair access; replaces hard-coded address lists for the local-stable side.
- **Python 3.12 + uv 0.11** + **`tick` 0.8.0.2** — only actively-maintained Python library with multivariate parametric Hawkes (`HawkesExpKern`, `HawkesSumExpKern`, EM, conditional-law) and fast C++-backed MLE; `hawkeslib` is dead and univariate-only.
- **`statsmodels` 0.14.6** for Kirchner 2015 INAR(p) (~80-line constrained-VAR implementation); **`scipy` 1.17.1** for the Chen et al. 2017 LR test and Carr–Madan numerical integration; **`polars` 1.41** for panel construction over millions of Transfer rows.
- **Blockscout v2 REST + Forno RPC** — free, no-key endpoints used in `research/CANDIDATES.md` to enumerate ICHI/Steer vaults and validate Phase-0 eligibility; remain the canonical fallback when subgraph staleness blocks the panel build.

### Expected Features

The feature catalogue from FEATURES.md (15 table stakes TS-01 through TS-15, 10 differentiators D-01 through D-10, 12 anti-features AF-01 through AF-12) was authored against a generic two-leg cashflow framing and survives the candidate correction *intact* — none of the features are Myriad-specific. Two features become more load-bearing after the correction:

**Must have (table stakes that bind harder now):**
- **TS-09 cross-leg dependence diagnostic** — with ICHI managing a portfolio of vaults whose pool-state polling is plausibly coupled, the *revenue* leg (LP fees aggregated across vaults) and the *cost* leg (analytics queries supporting the same vault dashboards) are unlikely to be independent. The cross-correlogram + permutation null is now first-class.
- **TS-11 four-condition convex-dominance check** — must run against ICHI's *joint* cashflow (LP-fee revenue + analytics-query cost across multiple vaults), not against a single point process. Specifically: vol-of-vol on the multi-pool fee stream, skew/fat tails on the LP-fee distribution, Hawkes self-excitation from TS-06, and the **rewritten** stablecoin-jump condition (USDT depeg / USDT-USDC basis, not USDC depeg).
- **TS-04 demand-window gate** — now applies with two distinct empirical lower-bound checks: (a) Forno `eth_call` keeper polling is free at any volume → below the demand window's lower bound (this is the cost-leg-as-keeper definition, which we reject per CANDIDATES §6 Q6); (b) indexer-backed analytics/UI queries (Graph subgraphs, Dune analytics) → this is the cost-leg definition that *does* land inside the demand window. Steer-on-Celo at $855 TVL may fail this gate; ICHI almost certainly passes it.
- **TS-15 null-result emission** — the null-result template now has two realistic firing modes: (i) Steer's Celo-only data spend below the lower bound (cost-leg gate); (ii) cKES/cCOP swap counts too thin for Hawkes ID (sample-thinness gate, the PITFALLS §1 spirit reapplied).

**Should have (competitive):**
- **D-03 pre-registration** — the only defense against retroactively explaining whatever the cKES/USDT or cCOP/USDT panel shows. Must be committed before any vault-level estimation.
- **D-08 Iteration-2 dry-run** — now naturally instantiated by the ICHI → Steer transition; Steer's structural difference (strategist-curated rebalance vs ICHI's single-asset auto-rebalance) is itself the DGP-generality test.
- **D-09 cost-leg prior sensitivity** — load-bearing because the cost leg is stipulated (Q6 in CANDIDATES) and no public Graph-spend figure exists for either protocol.

**Defer (v2+):**
- D-02 (kernel-class robustness), D-06 (structural-break test), D-10 (hedge-strip cost decomposition) — all Iteration 3+ once at least two protocols have been characterized.
- Deployed Solidity hedge contracts — explicitly out of scope (PROJECT.md), Iteration 3+ contingent on positive Iteration 1.

### Architecture Approach

The seven-layer architecture (L0 protocol-spec TOML → L1 TypeScript fetch → L2 Parquet cache → L3 panel → L4 DGP estimation → L5 cross-leg dependence → L6 Carr–Madan + falsification → L7 PDF report) is the right shape for the corrected scope. The single material adjustment is that the `protocols/*.toml` swap surface that ARCHITECTURE.md sized for `myriad.toml` / `halo.toml` now houses `ichi.toml` and `steer.toml`. Each spec lists a *vault factory* address, an enumeration of vault contracts (pulled from the factory's `VaultCreated` / `ICHIVaultCreated` event log), the underlying Uniswap V3 pool addresses, the local-Mento and counter-stable token addresses, and the data-cost class (`"indexer-analytics-queries"`, replacing Myriad's `"per-event-oracle"`).

**Major components (post-correction):**
1. **L0 `protocols/ichi.toml`** — Iteration 1 swap surface; anchor pool `0x61Ef…829F` (cKES/USDT @ $130k TVL); includes the COPM Minteo vaults (`0xC92E8Fc…`) under the controlled-broadening Key Decision; flags `mixing = "Mento-native + Minteo-fintech"` for joint-analysis diagnostics.
2. **L0 `protocols/steer.toml`** — Iteration 2 swap surface; primary pool cCOP/USDT `0x2AC5…17B0`; carries a `cost_leg_lower_bound_verified = false` flag that L1 must clear before estimation proceeds (CANDIDATES §6 Q6 part b).
3. **L1 `fetch/`** — TS data-fetch unchanged (Blockscout v2 REST already proven against ICHI/Steer in CANDIDATES; subgraph reads remain optional cache); `@graphprotocol/client-x402` is installed but never triggers in the free-tier baseline.
4. **L3 panel** — Python ingest now consumes Uniswap V3 `Mint` / `Burn` / `Swap` events on the underlying pools *plus* `Deposit` / `Withdraw` events on the ICHI/Steer vault contracts. The revenue leg is LP-fee accrual (computed from `Swap` events × pool fee tier × in-range vault liquidity share).
5. **L4 DGP estimation** — Kirchner INAR(p) for NHPP + tick multivariate Hawkes for the alternative; LR test with the boundary correction from PITFALLS §4.
6. **L6 falsification + Carr–Madan strip** — gate 4 (stablecoin jump) reparameterized for USDT instead of USDC; jump-leg overlay calibrated on USDT depeg history.
7. **L7 PDF report** — unchanged.

### Critical Pitfalls

Top five from PITFALLS.md, re-anchored against the corrected scope:

1. **Substrate-too-young → sample-thinness on the chosen anchor pool (PITFALLS §1 reframed).** The Myriad-specific blocker resolves via the candidate switch, but cKES/USDT at ~130 swaps/30d is at-or-near the 300-event Hawkes floor, and cCOP/USDT at ~100–150 swaps/30d sits below it. **Avoid by:** anchoring Iteration 1 on cKES/USDT (densest), reporting NHPP/Hawkes indistinguishability as a publishable null when it occurs, lifting to ICHI multi-pool aggregate panels when justified (with the per-protocol-vs-per-vault decision from CANDIDATES §6 Q4 documented), and never relaxing the floor to force a Hawkes claim.
2. **Subgraph silent lag on Celo (PITFALLS §2).** Every Graph query must include `_meta { block { number hash } }` and compare against Forno `eth_blockNumber`; abort if lag > 100 blocks (~ 8 minutes). The CANDIDATES discovery phase already used Blockscout direct as the canonical path — keep this discipline through the panel build.
3. **In-sample optimism + LR test boundary error (PITFALLS §3–§4).** NHPP nests in Hawkes at the boundary (η = 0) → the asymptotic χ²(1) over-rejects the null. **Avoid by:** pre-registering the bootstrap-based LR test with the 50:50 χ²(0):χ²(1) mixture as the null distribution; reporting branching-ratio CIs via profile likelihood (not Hessian standard errors); requiring all four conditions (η ≥ 0.2, bootstrap LR rejects at α = 0.01, held-out KS test rejects NHPP residuals, time-varying-baseline NHPP fits worse than Hawkes) before claiming self-excitation.
4. **Cost-leg stipulation error (PITFALLS §6, sharpened by CANDIDATES §6 Q6).** Steer-on-Celo at $855 TVL may fail the demand-window lower bound entirely. **Avoid by:** defining the cost-leg narrowly as **indexer-backed analytics/UI queries only** (the locked Key Decision from PROJECT.md scope-correction block) and verifying empirical lower bounds for Steer *before* estimation proceeds; failing this check is a clean null-result candidate switch back to Iteration 1 polish.
5. **Carr–Madan strip pitfalls under fat tails / USDT depeg jump (PITFALLS §7).** Standard FFT-based Carr–Madan with 256 grid points is insufficient when condition 4 fires; the implied density can go negative under jump-diffusion. **Avoid by:** convergence-testing the grid up to 2^11–2^12 points; switching to COS or PROJ method when standard truncation produces negatives; pricing the jump leg separately via Merton or Kou calibration on **USDT** depeg history (not USDC's Mar-2023 anchor); framing the deliverable as a "static replication blueprint under counterfactual liquid strikes" rather than a "tradeable hedge instrument."

Pitfalls 5 (cross-leg dependence misspecification), 8 (reproducibility break across iterations), and 9 (free-tier exhaustion mid-iteration) all survive intact and are addressed by the table-stakes set (TS-09, TS-12, and the L1 90k-cap budget gate respectively).

**Standing stack-pitfall that remains:** `@graphprotocol/client-x402` settles in USDC on **Base**, not Celo; the x402-foundation facilitator monorepo lists no Celo facilitator. The "x402-on-Celo" framing is forward-looking — for Iteration 1 the cost leg is **modeled, not paid**, and any paid demo would settle on Base. This is a research finding to surface in the report, not a blocker for the empirical pipeline.

## Implications for Roadmap

Based on the synthesis above, suggested phase structure (eight phases, mapping cleanly onto ARCHITECTURE.md's build order and PITFALLS.md's phase-mapping):

### Phase 0: Candidate Eligibility & Pre-Registration
**Rationale:** PITFALLS §1 is blocking by design; CANDIDATES.md has already cleared ICHI and conditionally cleared Steer, but the open methodological questions from CANDIDATES §6 (per-protocol vs per-vault granularity Q4; cost-leg empirical lower bound Q6b for Steer; TVL-too-thin floor Q7) must be resolved *and* the pre-registration document (D-03) must be committed before any data-fetch occurs.
**Delivers:** `protocols/ichi.toml`, `protocols/steer.toml` (stub), `notes/PRE_REGISTRATION.md` with kernel forms / prior parameters / test statistics / acceptance regions / decision rules on Q4 + Q6 + Q7. A formal Phase-0 exit memo per PITFALLS §1.
**Addresses:** TS-04 demand-window gate setup, TS-12 parameter-driven re-runnability, TS-15 null-result template, D-03 pre-registration.
**Avoids:** PITFALLS §1 substrate-too-young (resolved via ICHI), §3 mock-data optimism (forbidden once pre-reg lands), §6 cost-leg stipulation error (decided pre-fetch).

### Phase 1: L1 Data-Fetch Skeleton + Free-Tier Discipline
**Rationale:** Establish the paid-step-is-idempotent invariant (ARCHITECTURE.md Pattern 2) before any bulk pull; sequence into the existing 100k/mo Graph budget.
**Delivers:** `fetch/` workspace bootstrapped; `cost-ledger.ts` with 90k-soft-cap budget gate; `kappa-meter.ts` for Agora cost-decomposition instrumentation; one verified end-to-end paid-query demo (settled on Base, not Celo — see standing pitfall) to validate the x402 wiring; subgraph-freshness wrapper (`_meta.block.number` + Forno head check) with the 100-block abort threshold.
**Uses:** STACK.md TypeScript layer in full (`viem 2.51`, `@x402/fetch 2.13`, `@graphprotocol/client-x402 1.0.0`, `graphql-request 7.4`, `@mento-protocol/mento-sdk 3.2.8`).
**Implements:** ARCHITECTURE.md L1 + L2 (cache hygiene).
**Avoids:** PITFALLS §2 silent subgraph lag (wrapper), §9 free-tier exhaustion (cost ledger).

### Phase 2: Panel Build (L3) for the ICHI cKES/USDT Anchor
**Rationale:** TS-01 event-level panel with on-chain provenance is the foundational gate; everything downstream depends on it.
**Delivers:** `data/raw/ichi/<pool>/<block_range>.parquet` for the cKES/USDT anchor pool and a configurable selection of additional ICHI vaults per the Q4 decision; `analysis/src/abrigo_x402/ingest.py` + `revenue_leg.py` (LP-fee accrual from Swap events × in-range vault liquidity share) + `data_leg.py` (stipulated NHPP prior, parameters loaded from `ichi.toml :: [data_leg_prior]`); FX-rate snap (TS-03) via Mento broker mid-rate at event block for cKES↔USDm and explicit USDT/USD treatment with provenance.
**Uses:** Python stack (uv + polars + pandas + Mento SDK reads via the cached snapshots).
**Implements:** ARCHITECTURE.md L3 (panel construction).
**Avoids:** PITFALLS §2 (freshness wrapper runs on every fetch), §5 phantom-transfer pollution from USDC/USDT fee-abstraction adapters (`0x2F25…7602B`, `0x0e2a…6f72`), AF-05 binning that destroys arrival signal.

### Phase 3: DGP Estimation (L4) with Boundary-Correct LR Test
**Rationale:** TS-05 + TS-06 + TS-07 + TS-08 are P1 table stakes; PITFALLS §4 requires the bootstrap LR distribution + boundary correction + KS rescaled-time test as the headline procedure, not the one-line `statsmodels.likelihood_ratio_test` call.
**Delivers:** `dgp/nhpp_inar.py` (Kirchner 2015 INAR(p) on `statsmodels.VAR` with non-negativity projection, validated against tick synthetic data per the STACK.md test plan); `dgp/hawkes_mv.py` (bivariate Hawkes via `tick.HawkesExpKern` with full off-diagonal excitation matrix per PITFALLS §5); `dgp/lr_test.py` with the 50:50 χ²(0):χ²(1) mixture + bootstrap-LR rig; held-out temporal evaluation (TS-13); `fit_report.json` with source-of-truth metadata header (chainId, contractAddress, blockRange, fetchTimestamp, dataHash).
**Uses:** `tick 0.8.0.2`, `statsmodels 0.14.6`, `scipy 1.17.1`.
**Implements:** ARCHITECTURE.md L4 (DGP estimation).
**Avoids:** PITFALLS §3 (metadata header refuses anonymous fits), §4 (boundary-correct LR test, EM branching-ratio CIs, four-criterion gate before any self-excitation claim).

### Phase 4: Cross-Leg Dependence (L5) and Falsification + Carr–Madan Strip (L6)
**Rationale:** TS-09 + TS-11 + TS-10 must run in order; the strip is gated on at least one falsification condition passing (AF-06 made positive).
**Delivers:** `dependence/joint_dist.py` (empirical copula on (dK_revenue, dK_cost), vine fallback only if BIC prefers); `hedge/falsification.py` with all four `SOMNIA_DRAFT.md §FUNCTIONAL FORM` conditions reparameterized for **USDT** depeg (not USDC); `hedge/carr_madan_strip.py` with convergence-tested grid (2^11+ points) + positivity check + jump-leg overlay; three-way strip-price stress test (independence / fitted-joint / comonotone) per PITFALLS §5.
**Uses:** numpy + scipy; QuantLib Garman-Kohlhagen as sanity cross-check only.
**Implements:** ARCHITECTURE.md L5 + L6.
**Avoids:** PITFALLS §5 cross-leg independence assumption, §7 Carr–Madan strip pitfalls under fat tails / jumps, AF-06 strip-without-gate.

### Phase 5: Reporting + Iteration-1 PDF Deliverable (L7)
**Rationale:** PDF is the deliverable per memory `feedback_pdf_deliverable.md`; D-07 (spot-check checklist) and D-09 (cost-leg prior sensitivity) are P1.
**Delivers:** `notebooks/ichi_iteration.ipynb` as thin orchestrator (ARCHITECTURE.md Pattern 5); `reports/ichi.pdf` rendered via Quarto/nbconvert; spot-check checklist of 5 randomly-chosen panel rows with Blockscout URLs; cost-leg prior sensitivity sweep (±50% on stipulated `(rate_per_event, USD_per_query)`); reproducibility manifest (TS-14) with subgraph block-pins, `uv.lock`, `package-lock.json`, output checksums.
**Avoids:** AF-08 dashboard scope-creep; AF-10 Dune-Plus-to-validate temptation.

### Phase 6: Iteration-2 Swap-Surface Validation on Steer
**Rationale:** D-08 dry-run validates TS-12 re-runnability without the AF-01 mock-data landmine; Steer-on-cCOP is the structurally distinct rebalance class that tests DGP generality.
**Delivers:** `protocols/steer.toml` filled in; the Phase-0 cost-leg lower-bound check on Steer-on-Celo (CANDIDATES §6 Q6b) — if it fails, emit null-result documenting "Steer-on-Celo data spend below demand-window lower bound, hedge thesis structurally inapplicable to this protocol-slice, Iteration 1 result stands"; if it passes, full Phase 2–5 re-run against the Steer panel with **no edits to `fetch/src/` or `analysis/src/`**.
**Uses:** Same stack; `grep -r "ichi" fetch/src analysis/src` must return zero hits before this phase begins (ARCHITECTURE.md leak-detection).
**Avoids:** PITFALLS §8 reproducibility break.

### Phase 7: Cross-Iteration Synthesis & Methodological Refinements
**Rationale:** Three open methodological questions remain after CANDIDATES.md and cannot be fully resolved without empirical results from Phases 3–6.
**Delivers:** Per-protocol vs per-vault granularity decision documented with retrospective evidence on whether the multi-vault aggregate or the single-vault microcosm gave the cleaner DGP fit (Q4); empirical resolution of the cost-leg lower bound for both ICHI and Steer with provenance log (Q6); TVL-too-thin floor inclusion rule for cXOF/USDm and BRLm/EURm pools (Q7) — either drop with documented reasoning or include with substrate-too-thin flags propagated into the Hawkes branching-ratio CI; an updated `notes/methodological-refinements.md` for future iterations.

### Phase Ordering Rationale

- **Phase 0 is blocking** because PITFALLS §1's spirit (substrate-too-young / cashflow-medium-wrong) reapplies as the sample-thinness / cost-leg ambiguity question; pre-registration (D-03) must precede any fit to prevent retroactive spec-swapping (AF-03, AF-04).
- **Phases 1 → 2 → 3 → 4** follow the strict L1 → L2 → L3 → L4 → L5+L6 dependency chain from ARCHITECTURE.md "Build Order". Each phase ships a verifiable artifact (parquet, fit_report.json, falsification gate result) that the next phase can either consume or short-circuit on (null-result path is live at every gate per TS-15).
- **Phase 5 is gated on Phase 4** because PDF rendering without the strip gate having run would publish an unjustified design (AF-06).
- **Phase 6 (Iteration 2) is gated on Phase 5** because Iteration 1 must finish with either a positive result or a documented null *before* Iteration 2 starts (PROJECT.md Constraints).
- **Phase 7 is a synthesis phase** that consumes results from Phases 3–6 and cannot be done earlier without becoming speculative.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 0:** CANDIDATES §6 Q6 part b — verify empirical cost-leg lower bound for Steer-on-Celo (only ~5–10 vaults, $855 TVL); needs primary-source enumeration of Steer's analytics-query footprint slice on Celo specifically (the protocol-wide spend across 42 chains is irrelevant).
- **Phase 2:** ICHI vault rebalance cadence per pool — required to calibrate the per-protocol-vs-per-vault granularity (Q4); needs primary-source vault-event-log analysis.
- **Phase 3:** Boundary-corrected LR test implementation — PITFALLS §4 sources (Wheatley ETH thesis, arxiv 2410.05008, Filimonov & Sornette 2014) need close reading to confirm the bootstrap rig design before coding.
- **Phase 4:** USDT depeg jump-leg calibration — original sources (Hernandez Cruz 2024, Wu & Liu 2026) were USDC-centric; need a USDT-specific equivalent or a methodological argument that USDC-calibrated parameters port to USDT.

Phases with standard patterns (skip research-phase):
- **Phase 1:** TS data-fetch wiring — STACK.md verified live, no surprises expected.
- **Phase 5:** PDF rendering pipeline — Quarto + nbconvert is standard; memory `feedback_pdf_deliverable.md` is well-trodden.
- **Phase 6:** Iteration-2 dry-run — the *test* of the swap surface, not a research effort; success is binary (clean swap or leak).

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Every npm + PyPI version verified live 2026-05-25; viem + tick + statsmodels + Mento SDK all primary-source confirmed. Single standing flag: `@graphprotocol/client-x402` settles on Base, not Celo (acknowledged, modeled, not paid). |
| Features | HIGH | Anchored in primary econometric sources (Kirchner 2015, Daw & Pender 2017, Chen et al. 2017, Ma et al. 2014, Carr & Madan 1998); user-memory disciplines (`feedback_prototype_evidence_bar`, `anti-fishing-replication`, `project_msc_applied_math`) ground every anti-feature. |
| Architecture | MEDIUM-HIGH | Seven-layer pipeline + Parquet/manifest boundary is the right shape and has primary-source backing in PROJECT.md and SOMNIA_DRAFT.md. Free-tier budget allocations (30k cold-backfill / 15k incremental / etc.) are calibrated against the Myriad-scale assumption and may need re-allocation for the multi-vault ICHI panel — flagged for Phase 1 re-baseline. |
| Pitfalls | HIGH | PITFALLS §1 was *verified true* and forced the candidate switch (Myriad/Halo disqualified primary-source); §2 (subgraph lag) and §9 (free-tier exhaustion) survived intact; §4 (LR boundary error) has multiple peer-reviewed sources; §7 (Carr–Madan under fat tails) is methodologically mature. The §1 spirit reapplies as sample-thinness — explicit and documented. |
| Substrate density | MEDIUM | cKES/USDT $130k TVL is the densest available substrate but at ~130 swaps/30d sits at-or-near the 300-event Hawkes floor; cCOP/USDT at ~100–150 swaps/30d is below it. This is a known constraint, not a discovery. |
| Cost-leg empirical bound | LOW for Steer, MEDIUM for ICHI | ICHI's ≥ 40 Celo vaults plausibly clear the demand-window lower bound; Steer's 5–10 vaults at $855 Celo TVL may not. Q6b in CANDIDATES is the live ambiguity. |
| x402-on-Celo settlement infra | LOW | Does not exist in the x402-foundation monorepo today; modeled cost leg is the only mode for Iteration 1 + 2. Forward-looking research finding to report, not a blocker. |

**Overall confidence:** MEDIUM-HIGH. The stack, architecture, feature catalogue, and pitfall catalogue are highly verified; the live ambiguities are concentrated in (a) sample density on the chosen substrate (manageable via null-result discipline), (b) Steer-on-Celo cost-leg lower bound (resolved by Phase 0 / 6 empirical check), and (c) per-protocol-vs-per-vault granularity (Q4, resolved by Phase 7 retrospective). None of these block the start of Phase 0; all of them have explicit null-result paths.

### Gaps to Address

- **Cost-leg lower-bound verification for Steer-on-Celo (CANDIDATES §6 Q6b).** Resolve in Phase 0 with primary-source on-chain enumeration of Steer's Celo-only analytics-query footprint; if it fails, Steer drops to null-result + Iteration 2 deferred or replaced.
- **Per-protocol vs per-vault granularity (Q4).** Cannot be resolved a priori; Phase 2 commits to one choice via `ichi.toml` (recommendation: start per-protocol-aggregate on ICHI Celo footprint, with single-vault microcosm as sensitivity check) and Phase 7 evaluates retrospectively.
- **TVL-too-thin floor for cXOF/USDm and BRLm/EURm (Q7).** Phase 0 commits to either drop-with-reasoning or include-with-flag in the pre-registration; Phase 2 enforces.
- **USDT depeg parameterization for Carr–Madan condition 4.** Original USDC-anchored sources (Wu & Liu 2026, Hernandez Cruz 2024) need a USDT-specific overlay or a documented methodological port; resolve in Phase 4.
- **ICHI Minteo COPM vault inclusion.** PROJECT.md locked the controlled-broadening Key Decision (allow COPM into scope, flag the Mento-native + Minteo-fintech mixing in any joint analysis); Phase 0 must operationalize the flag in `ichi.toml :: [vaults.<COPM_vault>] mixing_class = "minteo-fintech"` so downstream estimation can either segregate or aggregate with provenance.

## Sources

### Primary (HIGH confidence)
- `/home/jmsbpp/apps/d2p/abrigo/abrigo-x402/.planning/PROJECT.md` (post-correction; scope-correction block is authoritative)
- `/home/jmsbpp/apps/d2p/abrigo/abrigo-analytics/notes/SOMNIA_DRAFT.md`
- `.planning/research/STACK.md` — every version verified live via npm + PyPI on 2026-05-25.
- `.planning/research/FEATURES.md` — anchored in Kirchner 2015, Daw & Pender 2017, Chen et al. 2017, Ma et al. 2014.
- `.planning/research/ARCHITECTURE.md` — seven-layer pipeline + protocols-as-swap-surface pattern.
- `.planning/research/PITFALLS.md` — Myriad disqualification primary-source verified via `docs.myriad.markets/builders/contract-addresses` + `minipay.to/blog/myriad-markets-is-now-live-inside-minipay`.
- `.planning/research/CANDIDATES.md` — ICHI factory `0x9FAb…418F` + Steer factory `0x116Dba…014C` confirmed via Blockscout v2 + Forno RPC + ICHI docs + DefiLlama.
- Blockscout v2 API on Celo — head block 67821539.
- Celo Forno RPC — direct `eth_call` token / fee / liquidity reads.

### Secondary (MEDIUM confidence)
- Kirchner 2015 INAR(p) `arxiv.org/abs/1509.02017`; Daw & Pender 2017 `arxiv.org/pdf/1707.05143v3`; Chen et al. 2017 `arxiv.org/pdf/1702.06055v2`; Ma et al. 2014 `arxiv.org/pdf/1406.5430v1`.
- Filimonov & Sornette 2014 `arxiv.org/pdf/1403.5227`; arxiv 2410.05008 LR overacceptance; Wheatley ETH thesis on robust Hawkes estimation.
- Hernandez Cruz et al. 2024 `arxiv.org/pdf/2407.11716v1`; Wu & Liu 2026 `arxiv.org/pdf/2602.18820v1` — methodological references; cashflow leg's actual stability anchor is USDT.
- graph-node #3060 — subgraph `_meta.block` lacks timestamp.
- DefiLlama Steer entry — Celo TVL $855.

### Tertiary (LOW confidence)
- arxiv 1706.05935 — Carr–Madan FFT grid sizing under Bates (2^11–2^12 grid points for 10^-10 accuracy).
- x402-foundation monorepo state for Celo facilitator support — not present today.
- TVL figures for individual Celo Mento-local pools — computed at ad-hoc FX rates, coarse.

---
*Research completed: 2026-05-25 (post-correction synthesis)*
*Ready for roadmap: yes*
