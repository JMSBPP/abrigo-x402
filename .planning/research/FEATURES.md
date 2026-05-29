# Feature Research

**Domain:** Empirical econometrics / DGP-estimation pipeline for two-leg cashflow processes, with output = falsifiable arrival-process estimate + Carr–Madan strip parameterization for FX-hedge instrument design. Iteration 1 = Myriad (Mento-denominated prediction market on Celo); pipeline must re-run on Iteration 2 (Halo, receipt OCR) with parameter swap only.
**Researched:** 2026-05-25
**Confidence:** HIGH for table stakes (anchored in SOMNIA_DRAFT.md primary sources: Kirchner 2015, Daw & Pender 2017, Chen et al. 2017, Ma et al. 2014, Carr & Madan 1998). MEDIUM for differentiator catalog (composed from cross-domain best practices in point-process econometrics + static-replication numerics). HIGH for anti-features (anchored in user memory: `feedback_prototype_evidence_bar`, `anti-fishing-replication`, `project_msc_applied_math` review standard).

## Scope discipline

This research deliberately scopes "features" to **pipeline capabilities and outputs**, not UI affordances. The end-user is the project author + an MSc Matemática Aplicada examiner + downstream hedge-instrument designers. A "feature" here is a thing the pipeline *does or produces* that materially affects the empirical validity, falsifiability, or re-runnability of the result. Cosmetic features (dashboards, web UIs, real-time streaming) are out of scope because the deliverable is a research artifact, not a deployed product (locked in PROJECT.md Key Decisions, 2026-05-25).

---

## Feature Landscape

### Table Stakes (Without These, the Pipeline Is Empirically Invalid)

These are the features whose **absence** would make a reviewer reject the work as not-econometrics. Each is justified against an empirical-validity threshold, not against "everyone does it."

| # | Feature | Why Required (Empirical-Validity Justification) | Complexity | Notes |
|---|---------|--------------------------------------------------|------------|-------|
| TS-01 | **Event-level cashflow panel with on-chain provenance per row** (block_number, tx_hash, log_index, event_signature, contract_address, leg ∈ {revenue, cost}, amount_native, amount_USDC_at_settlement, timestamp_utc) | The DGP estimate is a function of arrival times. Aggregated (daily/hourly) panels destroy the arrival structure that distinguishes NHPP from Hawkes (clustering shows up at the sub-minute scale per Daw & Pender 2017). Each row must be re-derivable from a public RPC call — otherwise the result is not reproducible. | M | Pull via `@graphprotocol/client-x402` for Myriad subgraph; verify `_meta.block.number` matches Blockscout for spot-check rows (PROJECT.md Constraints flags Celo subgraph lag). |
| TS-02 | **Subgraph freshness gate** (`_meta.block.number` vs Celo head; abort if lag > N blocks) | PROJECT.md Context explicitly warns: "Subgraph availability on Celo lags other chains." A stale subgraph produces a panel that is missing recent events → biases arrival-rate estimates downward → fits a slower-arrival model than the true DGP. This is a silent failure mode. | S | One-liner check before any estimation runs. |
| TS-03 | **Currency-leg labeling and FX-rate-at-event join** (each revenue-leg row carries both `amount_cCOP` and `amount_USDC` snapped to the event's block timestamp via an explicit rate source) | The Core Value is FX-cashflow modeling. Without an FX-rate join at event time, the "FX risk" claim is unmeasurable. Snapping at settlement time (not query time) avoids look-ahead bias. | M | Source for cCOP/USDC: Mento on-chain oracle if available at the event block, else nearest Mento broker mid-rate; document the choice and timestamp gap per row. |
| TS-04 | **Stipulated-prior data-cost leg with explicit demand-window check** (the cost-leg arrivals are NOT observed on-chain for Myriad; the prior must be stated as a `(rate_per_event, USD_per_query)` tuple with the window check `Graph_free_tier ≤ implied_monthly_cost ≤ $390`) | PROJECT.md Active requirements list this as the falsification gate. If the implied cost lands outside `[free tier, Dune Plus $390/mo]`, the hedge thesis is structurally inapplicable to this protocol — a null result, which is itself a valid deliverable per Core Value. Without this gate, the project becomes unfalsifiable. | M | Document the prior as a function of observed event count; show the window computation in the notebook. |
| TS-05 | **NHPP fit via INAR(p) bin-count estimator (Kirchner 2015)** with reported log-likelihood, AIC, BIC, and chosen bin width | This is the null model specified in SOMNIA_DRAFT.md §ARRIVAL PROCESS. Reporting only the alternative without the null forecloses the likelihood-ratio test (TS-07). Bin width must be reported because the INAR(p) likelihood depends on it. | M | `statsmodels` does not ship INAR(p) — implement directly from Kirchner 2015 §3, or wrap an R `tscount` call. |
| TS-06 | **Multivariate Hawkes fit (Daw & Pender 2017 spec) with exponential kernel baseline + reported parameters** `(μ, α, β)` per leg, branching ratio, and condition `||α/β||_∞ < 1` for stationarity | Hawkes is the alternative model. Reporting fit parameters without the stationarity condition lets a non-stationary fit slip through silently (a non-stationary Hawkes is an unbounded process and its hedge implications are meaningless). | L | Use `tick.hawkes` (Python) or implement EM per Veen & Schoenberg 2008. Exponential kernel first because closed-form MLE; flag non-parametric alternatives as differentiators. |
| TS-07 | **Likelihood-ratio test NHPP vs Hawkes (Chen et al. 2017)** with explicit reporting of: test statistic, degrees of freedom, p-value, and a *pre-registered* α (e.g. 0.01) chosen **before** running the test | This is the model-selection mechanism specified in SOMNIA_DRAFT.md. The pre-registered α is what separates this from p-hacking. The Chen et al. 2017 paper specifically validates AIC/BIC/HQ behaviour for Hawkes vs Poisson model selection. | M | Pre-register the α in the notebook prologue (in a markdown cell, before any data is loaded). |
| TS-08 | **Time-rescaling-theorem goodness-of-fit diagnostic** (rescaled inter-event times against unit-exponential via KS test + QQ plot) for both NHPP and Hawkes fits | A higher likelihood for Hawkes vs NHPP does not establish that Hawkes *fits well* — only that it fits *better*. The time-rescaling theorem is the standard residual diagnostic; failing it on both models is a valid null result ("neither family describes Myriad's arrivals"). | M | `ppdiag` (R) or implement directly: Ozaki (1979) / Brown et al. (2002) time-rescaling. |
| TS-09 | **Cross-leg dependence diagnostic at the arrival level** (cross-correlogram of revenue-leg events vs cost-leg events at lags from −T to +T, plus a permutation null) | The "joint" stochastic process in PROJECT.md Core Value requires evidence of joint structure. If the legs are independent, the multivariate Hawkes degenerates and a univariate model per leg suffices. The permutation null is needed because raw correlogram peaks are not significance-tested. | M | Cost-leg events are stipulated under TS-04 → cross-correlation is between observed revenue events and the prior-implied cost arrivals; document this clearly to avoid overclaiming. |
| TS-10 | **Carr–Madan strip parameterization output** (a callable `payoff(C_t) → strip = [(K_i, w_i, type_i)]` where strikes K_i, weights w_i, and types ∈ {call, put} are explicit; plus a numerical integration error bound) | This is the hedge-instrument design output specified in PROJECT.md Active req #5 and SOMNIA_DRAFT.md §FUNCTIONAL FORM. Without the explicit strip, the project ships an abstract claim, not a design. Without the error bound, downstream consumers cannot tell whether the discretization is fit for purpose. | L | Use Ma et al. 2014 Algorithm 1; report L²(K_min, K_max) error vs the true twice-differentiable payoff per Balder & Mahayni 2006. |
| TS-11 | **Convex-dominance condition check** (run all four conditions from SOMNIA_DRAFT.md §FUNCTIONAL FORM table — vol-of-vol, skew/fat-tails, Hawkes self-excitation, USDC depeg-jump — and report TRUE/FALSE per condition with a 95% bootstrap CI) | The Carr–Madan strip is only justified when *any* of the four conditions holds. Outputting a strip without checking these is publishing an unjustified design. Failing all four is itself a valid null result. | M | Vol-of-vol via Akdogan 2019 / Rolloos 2020 estimator; skew via standardized 3rd moment with bootstrap CI; Hawkes self-excitation already from TS-06 (branching ratio > 0); USDC depeg via Hernandez Cruz 2024 / Wu & Liu 2026 calibration. |
| TS-12 | **Parameter-driven re-runnability** (the pipeline takes `(contract_addresses, leg_token_addresses, fx_rate_source, data_cost_class, demand_window)` as a config object; no Myriad-specific constants in the estimation code) | PROJECT.md Active req #6: "Iteration 2 (Halo) must reuse the same Python + TypeScript stack with only the contract-address and data-cost-class parameters changed." Without this, Iteration 2 becomes a fork-and-rewrite. | M | Config in TOML/YAML; estimation modules accept the config dict; protocol-specific code lives only in the `adapters/` directory. |
| TS-13 | **Out-of-sample / temporal hold-out** (last 20% of the panel held out; fit on first 80%, evaluate likelihood + GoF on held-out portion) | In-sample likelihood is monotonic in parameter count → in-sample Hawkes will always beat in-sample NHPP. Without a temporal hold-out, the likelihood-ratio test is not testing predictive structure, only fit. | S | Standard practice; cheap to add once estimation is in place. |
| TS-14 | **Deterministic reproducibility manifest** (lockfile of all subgraph queries with `block_number` pins; Python `uv.lock`; TypeScript `package-lock.json`; final cell of notebook writes a JSON manifest with input checksums, parameter values, and output file checksums) | The deliverable is "research artifact + reproducible pipeline" (PROJECT.md Key Decisions). A non-reproducible result is, for an MSc examiner, indistinguishable from a fabricated one. Block-number pins are how on-chain analysis achieves bit-exact reproducibility. | M | Use a fixed `block_number` in subgraph queries via `_meta` argument; manifest format borrowed from `abrigo-analytics` if a convention exists there. |
| TS-15 | **Null-result template + auto-emission** (if any of the falsification gates trip — demand-window TS-04, both models fail GoF TS-08, no convex-dominance condition holds TS-11 — the pipeline writes a `NULL_RESULT.md` documenting which gate tripped and why, and *does not* emit a Carr–Madan strip) | PROJECT.md Core Value: "If `C(t)` is unrecoverable from free-tier data, the project's hedge-design thesis itself is unsupported, and that null result is the deliverable." A pipeline that silently emits a strip after gates failed is publishing a false design. | S | Just a conditional at the end of the notebook; the discipline is what matters. |

### Differentiators (Scientific Credibility Above Naive Panel + OLS)

Features that lift this from "I downloaded some events and ran a regression" to something a structural econometrician would accept. Each maps to a known landmine in naive empirical work.

| # | Feature | Value Proposition | Complexity | Notes |
|---|---------|-------------------|------------|-------|
| D-01 | **Sample-window perturbation robustness sweep** (re-fit NHPP and Hawkes on rolling 70%/80%/90% panels and on calendar-month sub-panels; report parameter stability and LR-test sign-stability) | A single-window result is one draw from a sampling distribution. Robustness sweeps show whether the conclusion ("Hawkes wins") is a real DGP property or a fluke of the window. This is what an MSc reviewer looks for after the headline number. | M | Adds maybe 5 minutes of compute; the report table is the real cost. |
| D-02 | **Kernel-class robustness sweep** (re-fit Hawkes under exponential, power-law, and one non-parametric kernel; report whether the convex-dominance conclusion is invariant to kernel choice) | The Hawkes literature is full of results that flip when the kernel changes. Reporting only the exponential-kernel fit hides this. Power-law in particular is known to better fit financial-data clustering (Bacry et al.). | L | Non-parametric kernel via `tick.hawkes.HawkesEM`; or skip and document why. Power-law via standard parameterization. |
| D-03 | **Pre-registered analysis plan** (a `PRE_REGISTRATION.md` written before any data is pulled, fixing: α level, model classes, kernel families, GoF tests, robustness sweeps, and falsification gates) | This is the strongest defense against p-hacking and post-hoc model selection — both are the user's stated landmines (`anti-fishing-replication` discipline). Pre-registration is the gold standard in empirical econometrics; for an MSc-level deliverable it elevates the work substantially. | S | One markdown file; the discipline cost is real but the writing cost is small. |
| D-04 | **Bootstrap confidence intervals on Hawkes parameters** (parametric bootstrap by simulating from the fitted process; report 95% CI on μ, α, β, and branching ratio) | Point estimates without CIs are uninterpretable for hypothesis testing. The asymptotic CIs from the MLE Hessian are known to under-cover for Hawkes with small samples (Ogata 1978); bootstrap is the standard fix. | M | Simulate via Ogata's thinning; 500 reps is sufficient for 95% CI. |
| D-05 | **Strip-pricing sensitivity to FX-rate model assumptions** (price the Carr–Madan strip under (a) constant ρ, (b) GBM ρ, (c) ρ with depeg-jump per Wu & Liu 2026; report strip-price spread) | The strip price depends on the FX-rate model. Reporting one number hides the model risk. The spread across the three models *is* a quantified model-risk premium — exactly what a hedge-instrument designer needs. | M | Pricing under (a) is closed-form; (b)(c) by Monte Carlo with 50k paths. |
| D-06 | **Cross-leg structural-break test** (CUSUM or Chow-style break test on the cross-correlogram across the panel) | If cross-leg dependence is non-stationary, a single Hawkes fit is misspecified globally. Detecting and reporting breaks lets the design either restrict to a stationary regime or argue for a regime-switching extension. | M | `ruptures` Python package; one-liner once panel is built. |
| D-07 | **Public spot-check reproducibility checklist** (a one-page list of 5 randomly-chosen panel rows with the exact Blockscout URL and the expected `amount_native` value; a reviewer can verify in 60 seconds) | This is how an MSc examiner verifies the work without re-running the pipeline. It costs almost nothing to produce and substantially raises trust. | S | Just generate 5 random row indices and emit URLs. |
| D-08 | **Iteration-2 dry-run validation** (before submitting Iteration 1, run the pipeline end-to-end on a *third* MiniPay candidate that's expected to fail the demand-window gate; verify the null-result emission works) | This validates TS-12 (re-runnability) and TS-15 (null-result emission) without waiting for Iteration 2. The third candidate is a "negative control" — a known-bad case that should trip the falsification gate. | M | Pick e.g. a Mento-Rewards-style protocol (PROJECT.md Out of Scope) — expected to fail TS-04 demand window. |
| D-09 | **Cost-leg sensitivity analysis under prior misspecification** (vary the stipulated `(rate_per_event, USD_per_query)` tuple by ±50% and report which conclusions change) | The cost-leg is stipulated, not observed (TS-04). Anyone reviewing the work will (correctly) ask: "what if the prior is wrong?" Pre-empting this with a sensitivity sweep neutralizes the criticism. | M | Reuse the existing pipeline; just vary one config parameter and re-run. |
| D-10 | **Hedge-strip cost decomposition** (decompose the strip price into: FX-vol component, SOMI-vol component, depeg-jump component, Hawkes-clustering component; report the share of strip price attributable to each) | The Core Value is composing two volatility channels (SOMNIA_DRAFT.md §FUNCTIONAL FORM). A decomposition tells a hedge designer *which channel* dominates — the actionable output for protocol selection in Iteration 2+. | L | Use Di Tella, Haubold & Keller-Ressel 2017 decomposition; or numerical attribution via shutting off one channel at a time and re-pricing. |

### Anti-Features (Things to Deliberately NOT Build)

These are features that look like good empirical practice but are landmines in this specific project. Each maps to a user-stated discipline (memory or the prompt's `anti-fishing-replication` reference).

| # | Anti-Feature | Why It Looks Appealing | Why It's a Landmine Here | Alternative |
|---|--------------|------------------------|--------------------------|-------------|
| AF-01 | **Mock / synthetic-data validation** (testing the pipeline by generating fake events from a known DGP and showing it recovers the parameters) | Standard ML/stats hygiene; reviewers expect it. | The user's evidence-bar memory (`feedback_prototype_evidence_bar`) explicitly rejects "works on synthetic data" as evidence of shipped work. Synthetic-data success creates false confidence — a pipeline that recovers a Hawkes process it generated itself does NOT show it will recover the actual DGP from messy on-chain data. The substrate-specific failure modes (subgraph lag, FX-rate snapping, Mento broker latency) only appear with real data. | Validate on real Myriad data only. The "Iteration-2 dry-run" (D-08) is the proper validation — running on a *different real protocol* expected to fail. |
| AF-02 | **In-sample model selection without held-out evaluation** (picking NHPP vs Hawkes based on training-set likelihood alone) | The Chen et al. 2017 LR test is in-sample by construction; it's the canonical procedure. | In-sample likelihood is monotonic in model flexibility → Hawkes will always win in-sample. Reporting only the in-sample LR test is statistically defensible but practically misleading. | Always pair the LR test with the temporal hold-out (TS-13) + time-rescaling GoF (TS-08). Report all three together so the reader sees the full picture. |
| AF-03 | **P-value scanning across kernels / windows / α-levels** (running many specifications and reporting only the ones that crossed significance) | This is how applied econometrics is often actually practiced. | This is exactly the `anti-fishing-replication` discipline the user explicitly named. The MSc Matemática Aplicada reviewer will detect this immediately (large robustness sweeps without pre-registration ⇒ fishing). | Pre-register the primary specification (D-03). Report all robustness sweeps as **secondary** with an explicit "exploratory, no claim attached" label. Do not change the primary spec after seeing results. |
| AF-04 | **Hand-tuned bin width for INAR(p)** (sweeping bin width until the LR test crosses significance) | Bin-width choice in Kirchner 2015 is a free parameter; sweeping it feels like sensitivity analysis. | Same fishing landmine as AF-03, dressed differently. Bin width selection should follow Kirchner 2015's stated procedure (or AIC-based selection within a pre-registered grid), not be tuned to outcome. | Pre-register the bin-width selection rule (e.g. "AIC-min over `{1m, 5m, 15m, 1h}`") in D-03. |
| AF-05 | **Aggregating to daily / hourly bars before fitting** (smooths out noise; reduces compute) | Reduces noise; faster fits; "standard" in macro-finance. | Clustering structure that distinguishes NHPP from Hawkes lives at the inter-event-time scale (often sub-minute). Daily aggregation destroys exactly the signal the model selection depends on. The result is a guaranteed "NHPP wins" finding — but it's an artifact of binning, not the DGP. | Fit on event-level data. If memory becomes an issue, downsample by random thinning (preserves arrival statistics) not aggregation. |
| AF-06 | **Reporting the Carr–Madan strip without the convex-dominance condition check** | The strip is the headline output; it's tempting to lead with it. | If none of the four conditions in SOMNIA_DRAFT.md §FUNCTIONAL FORM hold, the convex strip is dominated by a linear hedge — the strip is the *wrong* design. Reporting it anyway misleads the downstream designer. | TS-11 is mandatory; TS-15 enforces that the strip is only emitted when the gate passes. |
| AF-07 | **Smoothing / interpolating across gaps in the on-chain panel** (filling in missing days; KNN imputation; etc.) | Standard time-series hygiene. | On-chain panels have meaningful gaps — they encode the actual arrival process. Imputing them is equivalent to inserting fake events into the very process you're trying to characterize. | Leave gaps. Document them. If a gap is due to subgraph lag (not absence of activity), TS-02 should have caught it before estimation. |
| AF-08 | **Dashboard / web UI / streaming pipeline** | "Polished" deliverables look more credible. | The deliverable is a research artifact (PROJECT.md Key Decisions). A dashboard adds engineering surface that doesn't advance the empirical question and consumes the build-energy budget (user memory `feedback_energy_budget_tier_z`). | Static notebooks + markdown. PDF render only for the final write-up (memory `feedback_pdf_deliverable.md`). |
| AF-09 | **Deploying Solidity hedge contracts in this iteration** | The strip parameterization "wants to be" a contract. | PROJECT.md Out of Scope: "Deployed Solidity hedge contracts in this iteration — Iteration 3+ stretch." Deploying before the DGP is identified means deploying a contract whose payoff function is structurally unjustified. | Ship the strip as Python `payoff(C_t)` function + a markdown design sketch. Solidity is Iteration 3+, contingent on a positive Iteration 1 result. |
| AF-10 | **Buying Dune Plus to "validate" against a paid baseline** | "We should check our work against the gold-standard data source." | PROJECT.md Out of Scope explicitly: "we are *proving the case against buying it*." Buying Dune Plus to compare results would invert the project's thesis (memory `feedback_phased_buy_discipline.md`). | The free-tier-only constraint *is* the experimental condition. The pipeline either succeeds under it (positive result) or fails (null result is the deliverable). |
| AF-11 | **Using "MiniPay app names" or marketing copy as evidence of revenue structure** | Public listings claim FX exposure; easy to cite. | Marketing claims are not on-chain evidence. The pipeline must derive revenue currency from actual settlement-event token addresses, not from app descriptions. Memory `feedback_prototype_evidence_bar` rejects "claimed" as evidence. | Derive leg currency from the `token` field of observed transfer events. If no Mento-stablecoin transfers are observed, the protocol fails the FX-exposure premise — null result, document and stop. |
| AF-12 | **Cross-protocol pooling in Iteration 1** (combining Myriad + Halo data to "boost statistical power") | More data = tighter estimates. | Iteration 1 must finish *before* Iteration 2 starts (PROJECT.md Constraints). Pooling forecloses the per-protocol re-runnability test (TS-12, D-08) and entangles two DGPs whose similarity is itself an empirical question, not an assumption. | Fit each protocol separately. Cross-protocol meta-analysis is an Iteration 3+ topic after both per-protocol fits are stable. |

---

## Feature Dependencies

```
TS-01 (event panel)
  │
  ├──> TS-02 (freshness gate)               ── blocks all estimation
  │
  ├──> TS-03 (FX-rate join)
  │     └──> TS-10 (Carr-Madan strip)       ── needs USD-denominated cashflow
  │
  ├──> TS-04 (cost-leg prior + demand-window gate)
  │     └──> TS-15 (null-result emission)   ── falsification gate
  │
  ├──> TS-05 (NHPP fit) ──┐
  │                       ├──> TS-07 (LR test)
  ├──> TS-06 (Hawkes fit)─┘    └──> TS-08 (GoF time-rescaling, both models)
  │     │
  │     └──> TS-11 (convex-dominance check, condition #3 Hawkes self-excite)
  │             └──> TS-10 (Carr-Madan strip)
  │             └──> TS-15 (null-result emission)
  │
  ├──> TS-09 (cross-leg dependence)
  │     └──> TS-06 (informs whether to use multivariate Hawkes vs two univariate)
  │
  ├──> TS-13 (temporal hold-out)
  │     └──> TS-07 (out-of-sample LR test)
  │
  └──> TS-14 (reproducibility manifest)     ── wraps everything

TS-12 (parameter-driven re-runnability) ── orthogonal to estimation, enables D-08

Differentiators all hang off table stakes:
  D-01, D-02 enhance ──> TS-05, TS-06
  D-03 (pre-reg)   enhances ──> TS-07, TS-11   ← anti-fishing discipline
  D-04 enhances ──> TS-06
  D-05 enhances ──> TS-10
  D-06 enhances ──> TS-09
  D-07 enhances ──> TS-14
  D-08 validates ──> TS-12, TS-15
  D-09 enhances ──> TS-04
  D-10 enhances ──> TS-10

Conflicts (must NOT coexist):
  AF-05 (aggregation) ──conflicts──> TS-05, TS-06   (binning destroys arrival signal)
  AF-07 (imputation)  ──conflicts──> TS-01           (fake events corrupt the panel)
  AF-01 (mock data)   ──conflicts──> D-08            (synthetic ≠ negative control)
  AF-12 (pooling)     ──conflicts──> TS-12           (per-protocol re-runnability)
```

### Dependency Notes

- **TS-01 (event panel) is the foundational gate.** Every estimation feature depends on it. If the panel cannot be built from free-tier sources, TS-15 triggers immediately and Iteration 1 ends with a null result. This is by design (PROJECT.md Core Value).
- **TS-02 (freshness gate) blocks all estimation.** Running estimation on a stale panel is silently invalid; this check must be the first thing the pipeline does after panel construction.
- **TS-07 (LR test) and TS-08 (GoF) must be reported together.** TS-07 alone is fishable; TS-08 alone doesn't choose a model. The pair is the actual model-selection feature.
- **TS-10 (Carr-Madan strip) is gated on TS-11 (convex-dominance) and TS-15 (null-result).** The strip is the headline output but it must not be emitted if the gates fail. This is the anti-feature AF-06 made positive.
- **D-03 (pre-registration) enhances every estimation feature.** Without it, every other robustness sweep can be retroactively redescribed as fishing. With it, the same sweeps are credible.
- **D-08 (Iteration-2 dry-run) validates TS-12 + TS-15.** This is the substitute for AF-01 (mock data validation) — it provides the same "does the pipeline work?" assurance without the synthetic-data landmine.

---

## MVP Definition

### Launch With (Iteration 1 / Myriad)

All 15 table stakes (TS-01 through TS-15). They are non-negotiable for empirical validity. None can be cut without invalidating the deliverable.

Minimum differentiator set for an MSc-credible artifact:
- [ ] D-03 (pre-registration) — without this, fishing accusations are unanswerable
- [ ] D-07 (public spot-check checklist) — cheap and disproportionately raises trust
- [ ] D-08 (Iteration-2 dry-run on a known-bad candidate) — validates TS-12 and TS-15 without mock-data landmines
- [ ] D-09 (cost-leg prior sensitivity) — pre-empts the most obvious reviewer question

### Add Before Iteration 2 (v1.x)

These elevate the work but are not required to ship Iteration 1:

- [ ] D-01 (sample-window robustness) — trigger: a clean Iteration 1 result that needs hardening
- [ ] D-04 (bootstrap CIs on Hawkes parameters) — trigger: Hawkes wins the LR test, parameters need defensible uncertainty
- [ ] D-05 (strip-price model-risk sensitivity) — trigger: TS-11 passes, strip is emitted, downstream designer asks "how confident?"

### Future Consideration (Iteration 3+)

- [ ] D-02 (kernel-class robustness across power-law / non-parametric) — defer until exponential-kernel Hawkes is well-understood for the protocol class
- [ ] D-06 (structural-break test) — defer until enough history exists per protocol to meaningfully test stationarity
- [ ] D-10 (hedge-strip cost decomposition) — defer until at least two protocols have been characterized; the decomposition is most informative comparatively
- [ ] Deployed Solidity hedge instrument — PROJECT.md Out of Scope; Iteration 3+

---

## Feature Prioritization Matrix

| Feature | Empirical-Validity Value | Implementation Cost | Priority |
|---------|--------------------------|---------------------|----------|
| TS-01 event-level panel | HIGH | M | P1 |
| TS-02 subgraph freshness gate | HIGH | S | P1 |
| TS-03 FX-rate-at-event join | HIGH | M | P1 |
| TS-04 cost-leg prior + demand-window gate | HIGH | M | P1 |
| TS-05 NHPP fit (Kirchner) | HIGH | M | P1 |
| TS-06 Hawkes fit (Daw & Pender) | HIGH | L | P1 |
| TS-07 LR test (Chen et al.) | HIGH | M | P1 |
| TS-08 time-rescaling GoF | HIGH | M | P1 |
| TS-09 cross-leg dependence | HIGH | M | P1 |
| TS-10 Carr-Madan strip | HIGH | L | P1 |
| TS-11 convex-dominance condition check | HIGH | M | P1 |
| TS-12 parameter-driven re-runnability | HIGH | M | P1 |
| TS-13 temporal hold-out | HIGH | S | P1 |
| TS-14 reproducibility manifest | HIGH | M | P1 |
| TS-15 null-result emission | HIGH | S | P1 |
| D-03 pre-registration | HIGH | S | P1 |
| D-07 spot-check checklist | MEDIUM | S | P1 |
| D-08 Iteration-2 dry-run | HIGH | M | P1 |
| D-09 cost-leg sensitivity | MEDIUM | M | P1 |
| D-01 window robustness | MEDIUM | M | P2 |
| D-04 Hawkes bootstrap CIs | MEDIUM | M | P2 |
| D-05 strip model-risk sensitivity | MEDIUM | M | P2 |
| D-02 kernel-class robustness | MEDIUM | L | P3 |
| D-06 structural-break test | MEDIUM | M | P3 |
| D-10 strip cost decomposition | MEDIUM | L | P3 |

**Priority key:**
- P1: Launch blocker for Iteration 1
- P2: Add before Iteration 2 if Iteration 1 ships positive
- P3: Iteration 3+

---

## Comparator Analysis: Naive Pipeline vs This Pipeline

| Feature | Naive Panel + OLS | "Standard" Hawkes paper | This pipeline |
|---------|-------------------|--------------------------|---------------|
| Panel granularity | Daily aggregates | Event-level intra-day | Event-level on-chain, block-pinned |
| Arrival model | Linear regression on counts | Hawkes only (no null) | NHPP **and** Hawkes with LR test |
| GoF check | R² | Often omitted | Time-rescaling KS + QQ on both fits |
| Held-out evaluation | Train/test random split | Frequently in-sample only | Temporal hold-out (no look-ahead) |
| Cross-leg structure | Pearson correlation | Univariate per series | Multivariate with cross-correlogram + permutation null |
| FX-rate treatment | Constant or end-of-day | N/A | Snapped at event block; sensitivity to model in D-05 |
| Hedge output | None | None | Carr-Madan strip with discretization error bound |
| Convex-vs-linear justification | None | None | Four-condition gate from SOMNIA_DRAFT.md |
| Falsification gate | None | Rarely explicit | Three explicit gates (demand-window, GoF, dominance) |
| Reproducibility | "Code on GitHub" | "Code available upon request" | Block-pinned subgraph queries + manifest |
| Pre-registration | None | None | `PRE_REGISTRATION.md` before data pull |
| Re-runnability across protocols | Bespoke per dataset | Bespoke per dataset | Config-driven; Iteration-2 dry-run validated |

---

## Sources

Primary (anchored in SOMNIA_DRAFT.md and PROJECT.md):
- [Kirchner 2015 — INAR(p) bin-count estimator for NHPP](https://arxiv.org/pdf/1509.02017v2)
- [Daw & Pender 2017 — multivariate Hawkes moments and self-excitation variance](https://arxiv.org/pdf/1707.05143v3)
- [Chen et al. 2017 — information criteria for Hawkes process model selection](https://arxiv.org/pdf/1702.06055v2)
- [Ma et al. 2014 — robust algorithm and convergence analysis for static replication](https://arxiv.org/pdf/1406.5430v1)
- [Akdogan 2019 — vol-of-vol estimation](https://arxiv.org/pdf/1910.03245v4)
- [Rolloos 2020 — vol-of-vol](https://arxiv.org/pdf/2001.02404v4)
- [Selmi & Bouchaud 2000 — skew/fat-tail diagnostics](https://arxiv.org/pdf/cond-mat/0005148v1)
- [Wu & Liu 2026 — stablecoin tail-risk parameterization](https://arxiv.org/pdf/2602.18820v1)
- [Hernandez Cruz et al. 2024 — USDC depeg jump calibration](https://arxiv.org/pdf/2407.11716v1)
- [Di Tella, Haubold & Keller-Ressel 2017 — convex dominance under stochastic vol](https://arxiv.org/pdf/1709.05527v1)
- [De Vries 2026 — FX-tail update for Carr-Madan](https://arxiv.org/pdf/2601.14852v1)
- [Lambert & Kristensen 2022 — Panoptic perpetuals as long-gamma instrument](https://arxiv.org/pdf/2204.14232v3)
- [Luo et al. 2022 — Hawkes rejection of Poisson on Bitcoin block arrivals](https://arxiv.org/pdf/2203.16666v1)

Secondary (best-practice context for goodness-of-fit, kernel selection, and discretization):
- [Statistical significance of multivariate Hawkes fits to limit-order-book data (Lallouache & Challet 2016)](https://arxiv.org/pdf/1604.01824)
- [ppdiag — diagnostic tools for temporal point processes](https://cran.rstudio.com/web/packages/ppdiag/vignettes/ppdiag.html)
- [Hawkes-driven stochastic volatility, GoF testing on S&P 500 (Ann Oper Res 2022)](https://link.springer.com/article/10.1007/s10479-022-04924-9)
- [Detecting mutual excitations in non-stationary Hawkes processes (2026)](https://arxiv.org/pdf/2601.11717)
- [Coarse-grained Hawkes processes](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12191576/)
- [A functional analysis approach to static replication of European options (Bossu, Carr, Papanicolaou)](https://engineering.nyu.edu/sites/default/files/2020-11/AfunctionalanalysisapproachtothestaticreplicationofEuropeanoptions_0.pdf)
- [Robust replication of barrier-style claims (Bossu 2015)](https://arxiv.org/pdf/1508.00632)

Project context (read at start of research):
- `/home/jmsbpp/apps/d2p/abrigo/abrigo-x402/.planning/PROJECT.md`
- `/home/jmsbpp/apps/d2p/abrigo/abrigo-x402/notes/DRAFT.md`
- `/home/jmsbpp/apps/d2p/abrigo/abrigo-analytics/notes/SOMNIA_DRAFT.md`

User-memory discipline anchors:
- `feedback_prototype_evidence_bar` (no claimed-only work; on-chain evidence required) → grounds AF-01, AF-11
- `feedback_phased_buy_discipline` (evidence-before-spend) → grounds AF-10
- `project_msc_applied_math` (MSc Matemática Aplicada review standard) → grounds D-03, D-07, D-08
- `anti-fishing-replication` discipline (per prompt) → grounds AF-03, AF-04, D-03
- `feedback_pdf_deliverable` → grounds AF-08

---
*Feature research for: empirical FX-cashflow DGP-estimation pipeline with Carr-Madan strip output*
*Researched: 2026-05-25*
