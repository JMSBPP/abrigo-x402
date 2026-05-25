# Pitfalls Research

**Domain:** Empirical cashflow modeling on emerging-market on-chain prediction-market data; joint stochastic process estimation (NHPP vs Hawkes) under free-tier substrate constraints; convex-hedge instrument design.
**Researched:** 2026-05-25
**Confidence:** HIGH on the two structural Myriad findings (verified against Myriad's own docs + MiniPay's announcement post); MEDIUM-HIGH on the econometric pitfalls (peer-reviewed sources); MEDIUM on the operational/free-tier pitfalls (extrapolated from Graph + Celo subgraph community evidence).

> **READ THIS FIRST.** Pitfall 1 below is not a generic warning — it is a *current, verified blocker* on Iteration 1 as scoped in `PROJECT.md`. The substrate-too-young analog the question asks about exists, was found, and is more severe than expected. Do not begin estimation work before resolving it.

---

## Critical Pitfalls

### Pitfall 1: Myriad-on-Celo is substrate-too-young AND cashflow-medium-wrong (the E10 analog, doubled)

**What goes wrong:**
The Iteration 1 candidate fails two prerequisites the project assumed were satisfied:

(a) **Mainnet not deployed.** Myriad's own contract-address registry at `docs.myriad.markets/builders/contract-addresses` lists Celo mainnet (chain 42220) `PredictionMarket`, `PredictionMarketQuerier`, and `USDT` as **"Coming soon."** Only Celo *testnet* (chain 44787) has live addresses (`0x289E3908ECDc3c8CcceC5b6801E758549846Ab19`, `0x49c86faa48facCBaC75920Bb0d5Dd955F8678e15`). The "Myriad joins Celo ecosystem" Celo Foundation announcement (2026-02-25/26) and the MiniPay launch post both predate any verified mainnet contract publication. Even if contracts shipped quietly after those posts (≤ 90 days as of 2026-05-25), the sample window is structurally short for Hawkes/NHPP estimation that the project requires.

(b) **Wrong cashflow medium.** MiniPay's own post (`minipay.to/blog/myriad-markets-is-now-live-inside-minipay`) describes the integration as **"points-based"** with **"no financial commitment required"** — users predict with in-app points, and USDT is used only for top-leaderboard *rewards distribution*, not for the bet-inflow / settlement-payout legs that the project's two-leg cashflow model assumes are denominated in a local Mento stablecoin (cCOP, cKES, cGHS, …). The MiniPay variant therefore has no Mento-denominated revenue leg to estimate. The FX-hedge thesis presupposes the very thing that is absent.

The E10 analog is exact and worse: E10's x402-on-Base was 13 days old (calendar-too-young). Myriad-on-MiniPay is ~90 days old by calendar but **medium-too-wrong by design** — it would still be unhedgeable even if it were five years old, because points are not a currency.

**Why it happens:**
Press releases conflate "Myriad is live on Celo" (true: testnet + MiniPay integration of a points UX) with "Myriad has real-money on-chain bets denominated in Mento stablecoins on Celo mainnet" (false as of 2026-05-25). The project's `PROJECT.md` "Key Decisions" table commits to Myriad without an explicit verification that mainnet contracts exist and that bets settle in a local Mento stablecoin. Celopedia notes the substrate-maturity discipline ("verify each subgraph's `_meta.block.number`"); the same discipline was not applied to the candidate's contracts.

**How to avoid:**
Before any estimation work, run a **Candidate Eligibility Gate** with five hard checks:

1. **Mainnet contract existence**: query Celoscan for the candidate's `PredictionMarket` (or equivalent) address on chain 42220 and confirm it is verified (source code present, not just a proxy stub).
2. **Cashflow-medium check**: read the contract's token ERC-20 references; confirm at least one is a Mento stablecoin (`cUSD = 0x765DE...`, `cCOP`, `cKES`, etc.) — not just USDT or points.
3. **Event observability**: confirm bet-placement, market-resolution, and payout-claim events exist on the verified ABI, and that at least one event has actually been emitted on mainnet in the last 30 days (Celoscan event log filter).
4. **Sample size floor**: with the project's NHPP-vs-Hawkes goal, require ≥ 300 bet-placement events and ≥ 30 settlement events on mainnet before fitting (Hawkes branching-ratio estimates show substantial bias and identifiability failure below this scale; see Pitfall 4).
5. **Deployment-age floor**: ≥ 60 days from first mainnet emission. Combined with (4), this rules out projects that are "live" but functionally pre-data.

If any check fails: candidate is ineligible. Document the null result (which is itself a valid deliverable per project epistemics) and move to the Iteration 2 candidate or a different MiniPay app — *do not* relax the gate, *do not* swap the spec to make Myriad fit.

**Warning signs:**
- The candidate's docs page says "coming soon" anywhere near Celo.
- Marketing copy says "live on Celo" but contract-addresses page disagrees.
- The MiniPay app description uses words like "points," "in-app," "leaderboard," "no commitment," "for fun."
- USDT or USDC appears as the *only* token; no Mento local stablecoin.
- Celoscan event-log filter for the alleged contract returns < 30 events in the last 30 days.

**Phase to address:**
**Phase 0 — Candidate Eligibility (BLOCKING)**, before any DGP-estimation phase. This pitfall *is* Phase 0. The phase must terminate with either a "GO with candidate X, contracts verified at addresses A/B/C, ≥ N events on mainnet" memo, or a documented null result and a switch to an alternative candidate.

**Sources:**
- [Myriad Contract Addresses](https://docs.myriad.markets/builders/contract-addresses) — Celo mainnet "Coming soon" (HIGH; primary)
- [Myriad Markets is Now Live Inside MiniPay](https://minipay.to/blog/myriad-markets-is-now-live-inside-minipay) — points-based, USDT for rewards (HIGH; primary)
- [Myriad Joins the Celo Ecosystem](https://www.cryptowisser.com/news/myriad-joins-the-celo-ecosystem) — Feb 2026 announcement (MEDIUM; secondary)
- Project memory `project_e10_x402_substrate_pending_maturity_2026_11.md` — the original substrate-too-young rule

---

### Pitfall 2: Subgraph silent lag (Celo-specific)

**What goes wrong:**
The Graph's Celo subgraphs historically index slower than mainnet head — sometimes by hours, occasionally by days during indexer outages. The subgraph query *succeeds* and returns *data*, but the data is from block `N - k` for some unknown `k`. The estimation pipeline interprets the missing recent events as "no events," compressing arrival intensities downward, biasing rate estimates, and making both NHPP and Hawkes fits *look better-converged than they are* because the tail of the window is artificially quiet. The bias is one-sided (always toward lower intensity) and undetectable without an external freshness check.

**Why it happens:**
The default subgraph query returns whatever is indexed without a freshness header. Developers ship pipelines that assume `query → ground truth` when actually `query → ground-truth-as-of-some-stale-block`. The Graph community has open issues (graph-node #3060) noting `_meta.block` lacks a timestamp, so freshness must be computed by cross-referencing an RPC endpoint.

**How to avoid:**
Every subgraph query in the pipeline must follow this contract:

1. Include `_meta { block { number hash } }` in every query.
2. After receiving the response, fetch the current Celo head block from `forno.celo.org` (free RPC) via `eth_blockNumber`.
3. Compute `lag = headBlock - _meta.block.number`. Celo block time is ~5s, so `lag * 5s` gives staleness in seconds.
4. Define a freshness budget: **abort the analysis run if `lag > 100 blocks (~ 8 minutes)`**. Log the lag in the run's metadata regardless.
5. Persist the `(timestamp, lag)` series across runs. A monotonically-increasing lag is the warning sign that the indexer is stalled, not slow.

For the data-cost-class estimation, also pin a fixed `block: { number: $blockNumber }` argument on every historical query — this makes runs idempotent and reveals indexer reorganizations.

**Warning signs:**
- Estimated daily intensity drops sharply for the last 1–2 days of the window vs the prior trend.
- Two consecutive runs of the same query return different counts for the same date range.
- `_meta.block.number` is unchanged across two queries five minutes apart.
- Subgraph deployment shows recent failed indexing on graph-explorer.

**Phase to address:**
**Phase 1 — Data Acquisition.** The freshness wrapper should be part of the data-fetch client (`@graphprotocol/client-x402`) from the first query, not bolted on later. Include the freshness check in CI for any cached fixture.

**Sources:**
- [graph-node #3060: add timestamp to `_meta.block`](https://github.com/graphprotocol/graph-node/issues/3060)
- `PROJECT.md` celopedia note: "Subgraph availability on Celo has historically lagged other chains. Always verify `_meta.block.number` vs current block."

---

### Pitfall 3: Mock data and in-sample optimism in DGP estimation

**What goes wrong:**
While the mainnet contract gate (Pitfall 1) is unresolved, there is overwhelming temptation to "make progress" by fitting NHPP/Hawkes to (a) testnet data, (b) synthetic Poisson draws, or (c) a different protocol's data with Myriad's name on the variable. The fit succeeds — synthetic data fits the model that generated it. The likelihood-ratio test happily distinguishes the two models on the data, the Carr-Madan strip computes cleanly, the notebook runs end-to-end. The pipeline appears done. None of it is a finding about Myriad.

The anti-fishing discipline forbids the inverse trap as well: looking at testnet results, then writing the spec to "explain" them.

**Why it happens:**
Estimation code is reusable across data sources, so swapping the input is a one-line change. Internal pressure to ship something during the Proof of Ship cycle (May 2026) creates a strong incentive to demonstrate a working pipeline even without real data behind it. In-sample fit metrics (log-likelihood, AIC) cannot distinguish "modeled real protocol" from "modeled the synthetic draws I made yesterday."

**How to avoid:**
- **Source-of-truth metadata in every fitted artifact.** Every saved estimator output must include `{ source: "mainnet" | "testnet" | "synthetic", chainId, contractAddress, blockRange, fetchTimestamp, dataHash }`. Refuse to render plots without this header.
- **Forbid testnet → mainnet variable renaming.** If the gate (Pitfall 1) fails, the estimation phase does not start with testnet data masquerading as production. Either the candidate is mainnet-ready and we estimate, or the candidate is not and we ship a null result and switch.
- **Out-of-sample test discipline.** Hold out the last 20% of the window from fitting; report goodness-of-fit on the held-out segment. If the held-out fit is materially worse than in-sample, the model is overfit and the headline result is unreliable.
- **Pre-register the spec.** Before running the estimator on real data, commit the `notes/estimation_spec.md` containing the kernel form, prior parameters, test statistics, and acceptance regions. The diff log on this file is the audit trail against spec-swapping.
- **Null-result publishability.** Make explicit, in the deliverable plan, that "fitted NHPP and Hawkes on K events; LR test inconclusive at p > 0.1; convex-hedge framing therefore unjustified" is a valid Iteration 1 outcome.

**Warning signs:**
- A notebook plots "Myriad arrival intensity" without an upstream cell that includes a verified mainnet contract address.
- The fitted parameters are suspiciously clean (e.g., branching ratio exactly 0.5, baseline intensity exactly 1.0/day).
- Tests pass on data the user generated to test the estimator.
- The roadmap card says "DGP estimation complete" but no Celoscan query log accompanies it.

**Phase to address:**
**Phase 2 — DGP Estimation.** This pitfall is the spine of the project's epistemics. The pre-registration document is a Phase 1 deliverable; the source-of-truth metadata is a Phase 1 invariant; the held-out evaluation is a Phase 2 gate.

**Sources:**
- User memory `anti-fishing-replication` discipline (referenced in question)
- Standard econometric out-of-sample practice — Hawkes-specific overfit risk discussed in [Filimonov & Sornette branching-ratio bias](https://arxiv.org/pdf/1403.5227)

---

### Pitfall 4: NHPP-vs-Hawkes misidentification and LR-test false confidence (small samples + estimated parameters)

**What goes wrong:**
The project plans to use a likelihood-ratio test (Chen et al. 2017) to choose between NHPP (null) and Hawkes (alternative). The LR test is asymptotically chi-squared, but:

1. **Hawkes nests NHPP at branching ratio η = 0**, which is *on the boundary of the parameter space*. The standard chi-squared null distribution is wrong on a boundary; the correct asymptotic mixture is a 50:50 of χ²(0) and χ²(1). Using χ²(1) over-rejects the null (false Hawkes claims).
2. **Small samples**: with the Myriad sample plausibly ≤ 1000 events (and possibly far less; see Pitfall 1), the asymptotic distribution is itself a poor approximation. Empirical literature on Hawkes branching-ratio estimation reports substantial upward bias in η, especially with power-law kernels and edge effects — meaning the alternative model "wins" by absorbing finite-sample noise that an NHPP fit would have left as residual.
3. **Injecting MLE-estimated parameters into the null** (a common shortcut) causes the test to *over-accept* the null in the opposite direction — exactly the opposite bias from (1). The literature explicitly documents this (`arxiv.org/pdf/2410.05008`).
4. **Misspecified immigration**: if the true baseline intensity is non-stationary (very likely for a young prediction market with events resolving on news cycles), and the fit imposes a constant baseline, the unexplained non-stationarity gets absorbed into a spurious self-excitation signal.

The net effect: the LR test can give either false positives or false negatives for Hawkes, depending on which shortcut was taken, and the project would commit to a convex-hedge framing (or reject it) on the wrong basis.

**Why it happens:**
LR test code is a 3-line wrapper around `statsmodels.likelihood_ratio_test` and gives a single p-value. The boundary-of-parameter-space issue is not flagged automatically. Branching-ratio identifiability problems require either an EM-style estimator or a re-parameterization; default MLE silently produces a number regardless of whether the parameter is identified.

**How to avoid:**
- **Use the correct null distribution.** For nested boundary tests, use the 50:50 mixture χ²(0):χ²(1), equivalent to halving the p-value from the naive χ²(1) test. Document this explicitly in the estimation spec.
- **Bootstrap the test statistic.** Generate 1000 synthetic samples *under the fitted NHPP*, refit both models on each, compute the LR statistic distribution empirically. Compare the observed LR against the bootstrap distribution — this sidesteps the asymptotic-approximation question entirely.
- **Report branching-ratio confidence intervals via profile likelihood or EM-based estimator** (rather than the Hessian-based MLE standard error), per Wheatley's ETH thesis on Hawkes robustness.
- **Time-varying baseline diagnostic.** Before claiming self-excitation, run a Kolmogorov-Smirnov test against time-rescaled inter-arrival times under the fitted NHPP. Significant non-uniformity that the NHPP fit didn't absorb *could* be Hawkes — but could equally be a misspecified baseline. Fit a piecewise-constant or spline baseline before invoking Hawkes.
- **Pre-commit a minimum effect size.** "Branching ratio η must be ≥ 0.2 AND the bootstrapped LR test must reject NHPP at α = 0.01, AND the held-out KS test must show non-uniformity, AND the time-varying baseline alternative must fit worse than Hawkes" — all four, not any one. This is the anti-fishing safeguard at the test-statistic level.
- **Be willing to publish "indistinguishable."** If the sample is small, the honest finding is often that NHPP and Hawkes are statistically indistinguishable on this dataset — a null result that *prevents* an unsupported convex-hedge claim downstream.

**Warning signs:**
- LR test p-value just below 0.05 with no bootstrap confirmation.
- Branching ratio estimate near 0.95 (near the explosive boundary; almost certainly finite-sample bias or non-stationary baseline absorption).
- Hawkes fit's residual rescaled times pass a KS test but the NHPP's do too with a flexible baseline.
- The chosen model changes when the time window is shifted by ±10%.

**Phase to address:**
**Phase 2 — DGP Estimation.** The bootstrap rig, the boundary correction, and the four-criterion gate must all be in the estimation spec *before* the test is run on real data.

**Sources:**
- [Testing procedures based on maximum likelihood estimation for Marked Hawkes processes](https://arxiv.org/pdf/2410.05008) — overacceptance under naive plug-in
- [Filimonov & Sornette — Branching ratio approximation](https://arxiv.org/pdf/1403.5227) — bias of η estimation
- [Wheatley ETH thesis](https://ethz.ch/content/dam/ethz/special-interest/mtec/chair-of-entrepreneurial-risks-dam/documents/dissertation/wheatleythesis.pdf) — robust Hawkes estimation
- [Hypothesis Tests for Comparing Point Processes (MDPI 2026)](https://www.mdpi.com/2227-7390/14/4/727)

---

### Pitfall 5: Cross-leg dependence assumed independent when self-excitation is bivariate

**What goes wrong:**
The two-leg cashflow model (data leg + revenue leg) is naturally bivariate. If the actual generating process has cross-excitation — e.g., a wave of user activity causes both data queries *and* bet inflows to spike together — fitting two univariate models and combining them assumes independence and *systematically underestimates* the variance of the joint cashflow. The Carr-Madan strip then prices the convex hedge using a too-thin joint distribution; the resulting "hedge" is structurally under-collateralized for the true tail. Worse, the Daw & Pender 2017 moment formulas the project relies on are precisely the formulas that surface this — `Var(K(t)) >> E[K(t)]` under self-excitation, and the cross-term explodes faster than either marginal.

**Why it happens:**
Bivariate Hawkes is harder to fit than two univariate Hawkes. The cross-excitation matrix `[[α_DD, α_DR], [α_RD, α_RR]]` has 4× the parameters of a single univariate model, and identifiability worsens. Defaulting to "fit each leg independently, multiply the marginals" is a tractable shortcut that destroys exactly the property the convex hedge is supposed to insure against.

**How to avoid:**
- **Fit the bivariate model first.** Even if the marginal models are reported, the headline estimator must be the bivariate Hawkes with full excitation matrix.
- **Test independence as a restriction.** Wald test on `α_DR = α_RD = 0` from the full bivariate fit. Report the cross-excitation magnitudes regardless of significance — small but consistent positive cross-excitation can matter for tail pricing even when it doesn't pass a 5% test.
- **Stress-test the strip under cross-dependence.** Re-price the Carr-Madan replication under (i) fitted joint distribution, (ii) independence-product joint, (iii) comonotone joint (perfect dependence). The spread across these three is the model-risk envelope; if the hedge price is highly sensitive to it, the hedge spec is fragile.
- **Use copula-based marginals if bivariate Hawkes fails to converge.** Better an explicit Gaussian or t-copula on the empirical marginals than an implicit independence assumption.

**Warning signs:**
- The data-leg arrival counts and revenue-leg arrival counts have Pearson correlation > 0.3 at daily granularity, but the model treats them as independent.
- The bivariate Hawkes off-diagonal estimates are reported as "small" without confidence intervals.
- The hedge price computed under independence and under comonotonicity differ by > 20% — and the analyst picks the cheaper one without justification.

**Phase to address:**
**Phase 2 — DGP Estimation** (bivariate fit) and **Phase 3 — Instrument Design** (the three-way stress test).

**Sources:**
- Daw & Pender 2017 (`arxiv.org/pdf/1707.05143`)
- `SOMNIA_DRAFT.md` §FUNCTIONAL FORM condition 3 (Hawkes self-excitation in either leg)

---

### Pitfall 6: Demand-window stipulation error (Myriad's actual data spend may be outside `[free tier, $390/mo]`)

**What goes wrong:**
The project asserts (`PROJECT.md` Key Decisions) that the demand window is `[Graph free tier, Dune Plus $390/mo]` and stipulates the data-cost leg is anchored "inside" this window with a calibrated prior. If Myriad's actual monthly data spend is *below* the free tier, there is no economic problem to hedge — free dominates. If it is *above* $390/mo, Dune Plus flat-dominates and there is no x402 demand. Either way, the FX-hedge thesis is irrelevant for this protocol. The stipulation cannot be assumed — it has to be measured or rebutted.

The trap: the project can produce a self-consistent estimate with a stipulated cost-leg prior that *no actual Myriad team member has seen*. The estimate is then accurate *given the prior* but the prior itself is fabricated.

**Why it happens:**
Real per-protocol data spend is not public. Estimating it requires either (a) talking to the Myriad team, (b) deducing from on-chain oracle-subscription contract calls, or (c) modeling from observed event volume × per-query price. (b) only works if Myriad's oracles are on-chain (most prediction markets use off-chain resolution feeds — Reality.eth is on-chain, Pyth/Chainlink push feeds are on-chain, but external custom feeds may not be). The lazy path is to stipulate a midpoint in the demand window and move on.

**How to avoid:**
- **Falsification gate from `PROJECT.md` is real, not decorative.** Before stipulating the cost-leg prior, attempt empirical lower- and upper-bound estimates:
  - *Lower bound*: count distinct on-chain oracle reads / settlement events × known oracle per-call cost (Chainlink ~$0.50/read, Reality.eth gas-only). Multiply by 30 days.
  - *Upper bound*: assume one paid data query per market resolution × maximum plausible market count × $0.01 (The Graph unbatched rate).
- **If the bounds straddle the demand window**, the answer is "data insufficient — falsification gate triggers, stop, document null result." Do not split-the-difference into the window.
- **Talk to the team** (low-effort, high-yield): one Discord/Telegram message to a Myriad infra contact resolves the question in hours. The user's `evidence-before-spend` discipline applies recursively — *evidence before stipulation*.
- **Sensitivity-analyze the cost-leg prior**. Re-run the hedge calibration at the demand-window endpoints and at the midpoint. If the hedge design changes materially across the window, the result is prior-driven, not data-driven.

**Warning signs:**
- The cost-leg parameter has no provenance log entry — just a number.
- Sensitivity to the cost-leg prior is > 30% on the headline hedge metric.
- The on-chain panel has zero direct oracle-query events but the cost-leg model says oracle queries are the dominant data cost.

**Phase to address:**
**Phase 0 — Candidate Eligibility** (lower/upper bound estimate as part of the gate). **Phase 3 — Instrument Design** (sensitivity analysis on the prior).

**Sources:**
- `PROJECT.md` "Demand window" key decision, `SOMNIA_DRAFT.md` §DATA UNIT-COST
- Project memory `feedback_phased_buy_discipline.md` — evidence-before-spend

---

### Pitfall 7: Carr-Madan strip pitfalls under fat tails / jumps

**What goes wrong:**
The Carr-Madan static replication formula expresses any twice-differentiable payoff as an integral over a continuum of European calls and puts. In practice the strip is truncated and discretized. Under fat-tailed joint distributions (USDC depeg risk; Hawkes-driven super-Poisson variance) the truncation error blows up because:

1. **Slow characteristic-function decay** (Bates and similar models) inflates truncation error and *requires* up to 2^11–2^12 grid points for 10^-10 accuracy — orders of magnitude more than for Black-Scholes. Free-tier compute time is not infinite.
2. **Negative density artifacts**: standard FFT-based Carr-Madan can produce negative implied probabilities at extreme strikes; downstream code that integrates them silently propagates the error into the hedge weight.
3. **Static replication assumes a continuous strip of liquid strikes.** No Mento-stablecoin options market exists. The "strip" is therefore a *theoretical decomposition*, not a tradeable hedge — calling the Iteration 1 deliverable a "hedge instrument" rather than a "design sketch under counterfactual strike availability" overstates what was produced.
4. **Jump risk is invisible to Carr-Madan's smoothness assumption.** A USDC depeg jump (the project explicitly cites this as a hedge-justifying condition) is a discontinuity — the formula handles it formally but the truncation error compounds, and the replicating portfolio must be re-formed *instantly* at the jump, which no static portfolio can do.

**Why it happens:**
Carr-Madan is presented in textbooks as a clean closed-form result. The practical truncation, discretization, and tradeability constraints live in implementation footnotes that get skipped under deadline pressure. The "hedge instrument" framing conflates *what the math says* with *what a counterparty would actually quote*.

**How to avoid:**
- **Compute the strip on a robust grid.** Use Lewis (2001) or Andersen & Andreasen for Bates-class models; explicitly truncate at strikes where the implied tail probability is below a documented threshold (e.g., 10^-6). Log the truncation strikes in the artifact.
- **Verify positivity of the implied density at every grid point.** If negative, reduce the grid spacing or switch to COS-method or PROJ method (which preserve positivity by construction).
- **Frame the deliverable correctly.** Iteration 1 ships a *static replication blueprint* under the counterfactual of liquid strikes — not a tradeable instrument. The Iteration 3+ work is what would turn it into a quoted product (and per `PROJECT.md` is explicitly out of scope).
- **Add a separate jump-risk overlay.** Price the static strip *plus* a CDS-style jump-protection leg priced under a Merton or Kou jump-diffusion calibration on USDC depeg history (Hernandez Cruz et al. 2024). Report them as two components, not one collapsed number.

**Warning signs:**
- The replication notebook silently uses 256 grid points (standard textbook default) without a documented convergence test.
- Implied density goes negative at any strike; the warning is suppressed.
- The deliverable is described as a "hedge instrument" rather than a "replication sketch."
- Jump risk is mentioned in the motivation but absent from the priced object.

**Phase to address:**
**Phase 3 — Instrument Design.**

**Sources:**
- [Robust Replication of Volatility and Hybrid Derivatives on Jump Diffusions](https://arxiv.org/pdf/2107.00554)
- [arXiv 1706.05935 — characteristic function truncation under Bates](https://arxiv.org/pdf/1706.05935) — 2^11–2^12 grid points for 10^-10 accuracy
- `SOMNIA_DRAFT.md` §FUNCTIONAL FORM — explicit citation of USDC depeg as condition 4

---

### Pitfall 8: Reproducibility break — Iteration 2 fails to swap into the pipeline

**What goes wrong:**
The project's reusability promise (Iteration 2 = Halo, just swap contract addresses and data-cost class) breaks because:

1. Halo's event schema (per-scan receipt OCR events) does not match Myriad's (bet placement / market resolution). The estimator code, written against Myriad's event names, fails on Halo.
2. The data-cost class is structurally different: Myriad's is per-event oracle reads (lumpy, news-driven); Halo's is per-scan OCR calls (continuous, user-driven). The bivariate Hawkes model with kernel families fitted to Myriad will be misspecified for Halo even before parameter re-estimation.
3. The free-tier query budget was sized for one iteration; running two consumes 200k Graph queries against a 100k/mo allowance.
4. The Iteration 1 notebook hard-codes Celo chainId (42220), USDT addresses, and Mento decimal scaling — Iteration 2's chain or token set differs.

**Why it happens:**
"Swap one parameter" is rarely literally one parameter. Differences that look incidental at design time (event names, decimals, chain config, oracle modality) accrete into hundreds of lines of branching logic by Iteration 2. The 100k/mo Graph cap is a hard ceiling that doesn't appear as a code parameter.

**How to avoid:**
- **Parameterize from day one.** Every chain-specific or protocol-specific value lives in `configs/iteration_1.yaml` and `configs/iteration_2.yaml` — chain id, RPC URL, contract addresses, event names + ABI fragments, token decimals, Mento stablecoin selection, expected per-event data-cost class.
- **Define a canonical event schema** the estimator consumes: `{ timestamp, leg ∈ {data, revenue}, amount_local, amount_usd, market_id, user_id_hash }`. Each iteration's adapter is responsible for mapping its native events into this schema. The estimator code never sees protocol-specific event names.
- **Free-tier budget accounting.** Maintain a `query_log.jsonl` that records `(timestamp, queryHash, queryCost)` for every Graph call. Reserve 30k queries/mo as Iteration-2 buffer; abort if the rolling 30-day count exceeds 70k.
- **Adapter contract tests.** Before Iteration 2 begins, run the existing test suite against the Halo adapter producing canonical events from fixtures. Failures here are pipeline gaps, not Halo problems.

**Warning signs:**
- The estimator imports anything named `myriad_*` or `prediction_market_*` directly.
- Adding a new chain requires editing > 3 files.
- The `query_log` is missing or unmonitored.
- Iteration 1 notebooks contain hard-coded `0x` addresses outside the config file.

**Phase to address:**
**Phase 1 — Data Acquisition** (canonical-schema adapter contract). **Phase 5 — Iteration 2 prep** (adapter tests before Iteration 2 starts).

**Sources:**
- `PROJECT.md` Active requirement #6 — reproducibility
- Standard adapter-pattern reproducibility practice in scientific Python

---

### Pitfall 9: Free-tier resource exhaustion mid-iteration

**What goes wrong:**
The 100k/mo Graph free-tier ceiling is non-negotiable and resets monthly. A naïve pipeline that paginates over a full year of Myriad events with `first: 1000, skip: $offset` and re-runs on every notebook execution can burn 10k–30k queries in a single afternoon. The pipeline hits 100k mid-month; subsequent queries are rate-limited or fail; the analyst pays the project's own evidence-against-Dune-Plus thesis with a real $390 subscription "just to finish the iteration," contradicting the project's own argument.

The Celo RPC (`forno.celo.org`) and Blockscout API also have rate limits — not hard caps per month but per-IP per-second limits. Bursting a 30-day event scan via RPC `eth_getLogs` can trip these and lock the IP for a window.

**Why it happens:**
Subgraph queries are cheap-feeling (a query feels like one HTTP request) but pagination, `_meta` polls, and re-runs multiply quickly. RPC scans for historical events touch every block in the range. Neither has a visible meter until the cap is hit.

**How to avoid:**
- **Cache aggressively.** Every query response writes to a content-addressed cache (`data/cache/{queryHash}.json`); reruns hit the cache by default. Invalidation is explicit and logged.
- **Snapshot the full event panel exactly once per epoch.** Daily snapshot, not per-notebook-run. Estimation reads from snapshot, not from live subgraph.
- **Plan the monthly budget.** Estimate before running: `expected_queries = ceil(event_count / page_size) + meta_polls + ad_hoc_queries`. Commit to a budget < 30k/mo; alarm at 50k.
- **Use Blockscout for one-off contract reads** rather than Graph queries — Blockscout's API has no per-month cap (only per-IP rate limits) and can resolve transaction-level reads that don't need subgraph indexing.
- **For RPC: batch and back off.** Use `eth_getLogs` with chunked block ranges (10k blocks/call), exponential backoff on 429s, and a sleep budget. Never `eth_getLogs` from genesis.
- **Treat any "buy Dune Plus to unblock" temptation as a project-level failure mode.** The point of the project is that this temptation is what x402 is supposed to defuse. Hitting it means the experiment found something — document it.

**Warning signs:**
- Two consecutive notebook runs that "just refit the model" trigger 5k+ Graph queries.
- `eth_getLogs` requests on Forno return 429 or empty results during a scan.
- Monthly query log exceeds 30k by day 15.
- Someone proposes "we'll just buy one month of Dune Plus."

**Phase to address:**
**Phase 1 — Data Acquisition** (cache + snapshot + budget). **All phases** (monitoring).

**Sources:**
- `PROJECT.md` Constraints — free-tier-only discipline
- The Graph Network free-tier limit of 100k queries/mo

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Use testnet data to develop the estimator while waiting for mainnet contracts | Unblocks Phase 2 code work | High risk of conflating dev results with findings; pressure to ship the testnet numbers | Acceptable for *code* development only, with a hard rule that no fitted estimate from testnet data enters a roadmap or report artifact |
| Stipulate the cost-leg prior without empirical bounds | Closes Phase 0 quickly | Makes the entire hedge calibration a prior-elicitation exercise rather than an empirical one — destroys the project's thesis | Never |
| Hard-code Celo addresses and chainId in notebooks | Faster initial wiring | Breaks Iteration 2 swap, breaks adapter pattern | Acceptable in a `scratch/` directory excluded from the reproducible pipeline |
| Single univariate Hawkes per leg, no bivariate fit | Simpler estimator, fewer parameters | Misses cross-excitation, biases hedge pricing low | Never as a headline result; acceptable as a comparison baseline |
| Use χ²(1) for the LR test | One-line call to statsmodels | Wrong null distribution at boundary; over-rejects NHPP | Never for the headline test; acceptable as a sanity check alongside the bootstrap |
| Default 256-point Carr-Madan grid | Fast computation | Truncation error at the fat-tail regime the project explicitly motivates | Acceptable only if a documented convergence test shows 256 suffices for the fitted distribution; otherwise bump to 2^11+ |
| Skip the `_meta.block.number` freshness check | One fewer RPC call per query | Silent stale-data bias; one-sided downward intensity estimates | Never in production pipeline; acceptable in throwaway exploration |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| The Graph (Celo subgraphs) | Trust query results without freshness check | Always include `_meta { block }`, cross-check against `forno.celo.org` head; abort if lag > 100 blocks |
| Celo Forno RPC | Burst `eth_getLogs` without backoff | Chunk into ≤ 10k block ranges, exponential backoff on 429, log every retry |
| Mento stablecoins | Assume `cUSD = USDC` for FX purposes | They differ — cUSD is a Mento-Reserve-backed soft-peg, USDC is a Circle-issued centralized token. Use the Mento on-chain oracle (`MentoBroker.getAmountOut`) for cUSD ↔ cCOP, not generic 1:1 |
| MiniPay Myriad | Assume real-money cashflows | Read the MiniPay app description for the word "points" — current Myriad-on-MiniPay is points-based; no Mento-denominated cashflows exist to model |
| Reality.eth / Pyth oracles on Celo | Assume oracle calls are observable as on-chain events | Pyth pull-based feeds emit on update only; Reality.eth has its own event schema; some oracle reads happen via `staticcall` and emit nothing — verify per-protocol |
| Blockscout vs Celoscan | Treat them as identical | Both index Celo mainnet but have different ABI verification rates and different rate limits; cross-check verified ABIs on both before trusting one |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Unbounded subgraph pagination | Notebook takes 20+ minutes; query log shows thousands of calls | Snapshot once per day to local Parquet; estimator reads from local | At ~5k events, single-protocol; immediately at multi-protocol scale |
| Hawkes MLE on raw timestamps without bucketing | Optimization slow; convergence fragile | Use Kirchner 2015 INAR(p) bin-count estimator for the NHPP baseline; for Hawkes, use a coarse-grained time grid (1-minute bins) | At ~1k events per leg |
| Carr-Madan FFT with 2^12 grid points × bootstrap × 1000 reps | Hedge-design notebook runs for hours | Vectorize via `numpy.fft`; cache characteristic-function evaluations | At any non-trivial bootstrap size |
| Refit-on-every-notebook-run | Days of cumulative compute; query budget destruction | Persist fitted estimators as pickled artifacts with metadata header; reload by default | After first week |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Committing `.env` with Graph API key | Public key abuse, free-tier quota exhausted by third party | `.env` in `.gitignore`; use `direnv` or `pass`; CI uses GitHub secret |
| Trusting subgraph data as ground truth without cross-check | Indexer can serve incorrect or outdated data | Cross-verify a sample of subgraph events against Celoscan / Blockscout direct receipts |
| Reading mainnet writes from a private RPC URL with a personal key | Key leakage in logs / notebook outputs | Use public `forno.celo.org`; never put a write-capable key in the analytics pipeline (this project is read-only) |
| Treating `tx.origin` or `from` as the bet "user" identity | Wrong subject of analysis; MiniPay routes through a relayer/router | Trace through the MiniPay router contract; use the bet-event's `bettor` parameter, not the transaction sender |

## UX Pitfalls

(Not the primary risk surface — this is a research pipeline, not a user-facing product. Listed for completeness re: the eventual user-facing deliverable.)

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Reporting a single point estimate for the hedge weight | Reader takes it as precise; the confidence interval is enormous on this sample size | Always report 90% bootstrap CIs and a sensitivity-to-prior analysis |
| Claiming "Myriad-on-Celo is hedgeable" when the underlying may not have real-money cashflows | Misleads downstream stakeholders / readers / Proof of Ship reviewers | Foreground the candidate-eligibility outcome before any modeling result |
| Suppressing the null-result branch | Reader assumes the convex hedge framing is justified | Lead with the falsification gate's status; null results get equal page space |

## "Looks Done But Isn't" Checklist

- [ ] **Mainnet contracts identified:** Verify on Celoscan that the address is verified (source visible) AND has ≥ 30 events in the last 30 days — *not* just listed in a press release.
- [ ] **Cashflow medium confirmed:** Verify the contract's stablecoin token reference resolves to a Mento address (cUSD, cCOP, cKES, …) — *not* just "the protocol supports Celo."
- [ ] **Subgraph freshness:** Every artifact contains `_meta.block.number` AND the head-block lag at fetch time — *not* just the query result.
- [ ] **NHPP-vs-Hawkes test:** The reported p-value comes from a bootstrap with the correct boundary distribution — *not* a one-line `statsmodels` call.
- [ ] **Bivariate fit:** The Hawkes excitation matrix is reported with cross-terms — *not* two independent univariate fits multiplied.
- [ ] **Cost-leg prior:** The prior has empirical lower/upper bounds from on-chain observation — *not* a mid-window stipulation.
- [ ] **Carr-Madan strip:** The grid passed a documented convergence test AND the implied density is positive everywhere — *not* a textbook default with no diagnostics.
- [ ] **Reproducibility:** The Iteration 1 pipeline runs end-to-end against a `configs/iteration_2.yaml` with only the config swapped — *not* with manual code edits.
- [ ] **Free-tier accounting:** The monthly query count is logged AND under 70k as of report-time — *not* "we didn't track it."
- [ ] **Null-result path:** The Phase 0 candidate-eligibility memo exists in the repo with explicit GO / NO-GO — *not* implicit in the existence of downstream notebooks.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Myriad mainnet contracts genuinely not deployed (Pitfall 1) | HIGH | (1) Document the null result formally; (2) re-survey MiniPay catalog for candidates with verified-mainnet + Mento-denominated bets (consider Halo earlier, or a sports-betting MiniPay app if any qualify); (3) if no qualifying candidate exists in MiniPay, the *project itself* has produced a finding ("the MiniPay ecosystem at 2026-05 does not yet contain a candidate satisfying the FX-hedge two-leg structure") — that finding is the deliverable. |
| Subgraph silently stale (Pitfall 2) | LOW | Re-run with the freshness wrapper; discard the affected partial-window estimates; rerun on the corrected window. Days of work, not weeks. |
| Found Hawkes self-excitation that turned out to be misspecified baseline (Pitfall 4) | MEDIUM | Refit with piecewise-constant or spline baseline NHPP; re-run the LR test; if Hawkes still wins, conclusion stands; if not, the prior "convex-hedge justified" claim must be retracted. |
| Cross-leg independence assumed but cross-excitation present (Pitfall 5) | MEDIUM | Refit bivariate; re-price the strip under the new joint; the hedge weight likely *increases* (the project under-hedged in the independent fit). Report the correction openly. |
| Free-tier exhausted mid-month (Pitfall 9) | LOW-MEDIUM | Switch to Blockscout for direct contract reads; wait for monthly reset; if absolutely blocked, document as a finding ("100k/mo insufficient for this protocol's panel at daily granularity") — that finding *supports* the project's thesis. |
| Carr-Madan strip with negative implied densities (Pitfall 7) | MEDIUM | Switch to COS or PROJ method; document the change; re-run the hedge calibration. |
| Spec swapped after seeing results (anti-fishing violation) | HIGH | Revert to the pre-registered spec; report both the pre-reg result and the post-hoc variant separately and labeled. Treat the post-hoc variant as exploratory, never as headline. |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1. Substrate-too-young + cashflow-medium-wrong | **Phase 0 — Candidate Eligibility (blocking)** | Phase 0 exit memo: mainnet contract addresses + Mento-token reference + ≥ 30 day event activity, OR explicit null-result and candidate switch |
| 2. Subgraph silent lag | Phase 1 — Data Acquisition | Every artifact stores `(meta.block, headBlock, lag)`; CI rejects artifacts missing this header |
| 3. Mock data / in-sample optimism | Phase 1 (metadata invariant) and Phase 2 (held-out + pre-registration) | Pre-registration commit predates first fit; held-out goodness-of-fit reported |
| 4. NHPP/Hawkes misidentification | Phase 2 — DGP Estimation | Bootstrap LR distribution + boundary correction + EM branching-ratio + KS rescaled-time test all present in the artifact |
| 5. Cross-leg dependence misspecification | Phase 2 (bivariate fit) + Phase 3 (three-way joint stress test) | Bivariate Hawkes excitation matrix reported with CIs; strip priced under three joints |
| 6. Demand-window stipulation error | Phase 0 (cost-leg bounds in candidate eligibility) + Phase 3 (sensitivity) | Cost-leg lower/upper bound documented with provenance; hedge sensitivity-to-prior reported |
| 7. Carr-Madan strip pitfalls | Phase 3 — Instrument Design | Grid convergence diagnostic + positive density check + jump-leg overlay |
| 8. Reproducibility break | Phase 1 (adapter contract) + Phase 5 (Iteration 2 prep) | Iteration 2 config swap runs end-to-end without code edits |
| 9. Free-tier exhaustion | Phase 1 (cache, snapshot, budget) + ongoing | Monthly query log; budget alarm at 50k; project terminates the iteration cleanly at 70k rather than buying Dune Plus |

## Sources

- [Myriad Contract Addresses](https://docs.myriad.markets/builders/contract-addresses) — primary, HIGH confidence
- [Myriad Markets is Now Live Inside MiniPay (minipay.to)](https://minipay.to/blog/myriad-markets-is-now-live-inside-minipay) — primary, HIGH confidence (points-based, USDT for rewards)
- [Myriad Joins the Celo Ecosystem (cryptowisser)](https://www.cryptowisser.com/news/myriad-joins-the-celo-ecosystem) — secondary, MEDIUM confidence (announcement Feb 2026)
- [Building Decentralized Prediction Markets Across Three Blockchains With Myriad Protocol (HackerNoon)](https://hackernoon.com/building-decentralized-prediction-markets-across-three-blockchains-with-myriad-protocol) — Myriad multi-chain architecture context
- [graph-node #3060 — `_meta.block` lacks timestamp](https://github.com/graphprotocol/graph-node/issues/3060) — subgraph freshness gap
- [Testing procedures based on maximum likelihood estimation for Marked Hawkes processes](https://arxiv.org/pdf/2410.05008) — LR test overacceptance under naive plug-in
- [Filimonov & Sornette — Branching ratio approximation for the self-exciting Hawkes process](https://arxiv.org/pdf/1403.5227) — branching-ratio bias and identifiability
- [Wheatley ETH thesis — Extending the Hawkes process, general outlier test](https://ethz.ch/content/dam/ethz/special-interest/mtec/chair-of-entrepreneurial-risks-dam/documents/dissertation/wheatleythesis.pdf)
- [Hypothesis Tests for Comparing Point Processes (MDPI 2026)](https://www.mdpi.com/2227-7390/14/4/727) — point-process testing under small samples
- [Daw & Pender 2017 — Queues driven by Hawkes processes](https://arxiv.org/pdf/1707.05143) — bivariate Hawkes moment formulas
- [Robust Replication of Volatility and Hybrid Derivatives on Jump Diffusions](https://arxiv.org/pdf/2107.00554) — Carr-Madan extensions
- [arXiv 1706.05935 — characteristic-function truncation under Bates](https://arxiv.org/pdf/1706.05935) — 2^11–2^12 grid points for 10^-10 accuracy
- Project memory `project_e10_x402_substrate_pending_maturity_2026_11.md` — substrate-maturity discipline
- Project memory `feedback_phased_buy_discipline.md` — evidence-before-spend
- Project file `PROJECT.md` (2026-05-25) — Iteration 1 scope, demand window, falsification gate
- Project file `../abrigo-analytics/notes/SOMNIA_DRAFT.md` §FUNCTIONAL FORM — convex-hedge dominance conditions; §"Items left UNVERIFIED" — known gaps catalog

---
*Pitfalls research for: empirical cashflow modeling on emerging-market on-chain prediction-market data (Iteration 1 = Myriad on Celo); free-tier substrate constraints; anti-fishing epistemics.*
*Researched: 2026-05-25*
