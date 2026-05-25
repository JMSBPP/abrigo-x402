# Roadmap: abrigo-x402

**Created:** 2026-05-25
**Granularity:** coarse (8 phases — justified by strict L1→L2→L3→L4→L5+L6 dependency chain from `research/ARCHITECTURE.md` "Build Order" + Iteration-1/Iteration-2 separation; compressing further would collapse verifiable phase-exit artifacts)
**Coverage:** 32/32 v1 requirements mapped (0 orphaned)
**Iterations:** Iteration 1 = ICHI on cKES/USDT (Phases 0–5); Iteration 2 = Steer on cCOP/USDT (Phase 6); Cross-iteration synthesis (Phase 7)

---

## Execution discipline

**Specialized-agent assignment** (per memory `feedback_specialized_agent_per_subtask`): every phase below lists a *Primary Agent* (executor) + *Audit/Review Agents*. Subtasks within phase plans (created via `/gsd:plan-phase N`) must each tag the specialized agent that executes them. Mismatches between plan-time assignment and dispatch-time `subagent_type` require explicit re-planning.

**Agent-name resolution:** Agent names refer to definitions under `~/.claude/agents/` across both the active subtree and `_archived/`. Where the named agent is in `_archived/` (notably *Senior Project Manager* and *Analytics Reporter* as of 2026-05-25), the dispatcher must explicitly opt in via `subagent_type` override; this is intentional and documented in `feedback_specialized_agent_per_subtask`.

**Two-way plan review** (per memory `feedback_2way_plan_review`): this ROADMAP.md and every subsequent phase PLAN.md must pass a parallel review by **Reality Checker** (epistemic skepticism; evidence-based "NEEDS WORK" default) + **Code Reviewer** (technical correctness, design coherence) before commit. Blocking findings (either reviewer marks a load-bearing element BLOCKER / NEEDS WORK) force revision; non-blocking findings get TODO trails.

**Review-trail enforcement** (on-disk contract):
- Review artifacts live at `.planning/_reviews/<artifact_basename>_reality_checker.md` and `.planning/_reviews/<artifact_basename>_code_reviewer.md`.
- Each review file MUST have a `## VERDICT` section as its first H2, with the value PASS / NEEDS REVISION / NEEDS WORK / BLOCKED.
- A pre-commit hook (introduced in Phase 0 SC-4 extension) rejects commits modifying `.planning/**/PLAN.md` or `.planning/ROADMAP.md` unless both paired review files exist, are newer than the artifact, and neither carries an unresolved BLOCKER finding. Override flag `--allow-revision` requires an explicit human acknowledgement on a NEEDS REVISION verdict.
- A phase cannot be marked **Complete** in the Progress table until both paired review files exist under `.planning/_reviews/phase_N_*.md`. This forces the trail.

---

## Phases

- [x] **Phase 0: Candidate Eligibility & Pre-Registration** — Lock GOV/DEMAND artifacts + resolve Q-9 (cCOP panel construction) + commit pre-reg before any data-fetch
- [ ] **Phase 1: L1 Data-Fetch Skeleton + Free-Tier Discipline** — TS workspace + cost ledger + subgraph-freshness wrapper + content-addressed cache
- [ ] **Phase 2: Panel Build (L3) for ICHI cKES/USDT Anchor** — Event-level Parquet panel with provenance + FX-rate snap + phantom-transfer filter
- [ ] **Phase 3: DGP Estimation (L4) with Boundary-Correct LR Test** — Kirchner NHPP + tick Hawkes + boundary-correct LR test + KS rescaled-time + held-out evaluation
- [ ] **Phase 4: Cross-Leg Dependence (L5) + Falsification & Carr–Madan Strip (L6)** — Empirical copula + four-condition gate (USDT-reparameterized) + grid-verified Carr–Madan + null-result template
- [ ] **Phase 5: Reporting + Iteration-1 PDF Deliverable (L7)** — `reports/ichi.pdf` + spot-check + cost-leg sensitivity sweep + reproducibility manifest
- [ ] **Phase 6: Iteration-2 Swap-Surface Validation (Steer on cCOP/USDT)** — Cost-leg lower-bound check first; if pass, re-run Phases 2–5 with zero code edits
- [ ] **Phase 7: Cross-Iteration Synthesis & Methodological Refinements** — Per-protocol-vs-per-vault retrospective + USDT-depeg overlay documentation + `notes/methodological-refinements.md`

---

## Phase Details

### Phase 0: Candidate Eligibility & Pre-Registration
**Goal**: Commit all pre-fit governance artifacts (pre-registration, anti-feature gate, demand-window definition, Q-9 cCOP-panel decision) so no downstream phase can spec-swap after seeing results.
**Depends on**: Nothing (first phase; consumes existing `research/CANDIDATES.md` + `research/PITFALLS.md`)
**Requirements**: GOV-01, GOV-02, GOV-03, DEMAND-01 (verify component), REPRO-04 (decision component)
**Primary Agent**: **Senior Project Manager** *(archived — explicit subagent_type opt-in required)* (composes the governance artifacts: PRE_REGISTRATION.md, PHASE_0_GATE.md, Q9_DECISION.md, demand-window schema commentary; PM authors the outline + acceptance regions)
**Consult**: **Model QA Specialist** (authors the statistical content inside PRE_REGISTRATION.md — kernel forms, prior parameters, test statistics, REPRO-03 numeric thresholds — this is exactly Phase-0-prevention of AF-03 spec-swap) + **DevOps Automator** (pre-commit hook for anti-feature lint gate + review-trail enforcement hook) + **Blockchain Security Auditor** (verifies the Phase-0-gate on-chain claims for ICHI factory `0x9FAb…418F` + Steer factory `0x116Dba…014C`)
**Audit/Review**: Reality Checker + Code Reviewer (mandatory 2-way review of all four governance artifacts before commit)
**Success Criteria** (observable artifacts):
  1. `notes/PRE_REGISTRATION.md` exists in the repo with kernel forms, prior parameters, test statistics, acceptance regions, and decision rules for both ICHI (Iteration 1) and Steer (Iteration 2), committed BEFORE any commit under `analysis/src/` or `data/raw/`. Git log proves the ordering. **MUST include the Phase-6 REPRO-03 numeric pass/straddle/fail thresholds**: `PASS = primary-source evidence shows ≥ 100k Graph queries/mo attributable to Steer's Celo deployment; STRADDLE = primary-source bounds include 100k/mo (fires null-result); FAIL = primary-source bound < 100k/mo (fires null-result)`. Threshold committed BEFORE Phase 6 first execution; rationale per PITFALLS §6.
  2. `notes/PHASE_0_GATE.md` exists with the five-check Phase-0 eligibility outcome for ICHI (PASS, verbatim per CANDIDATES §4.1) and Steer (CONDITIONAL on Phase 6 cost-leg empirical lower-bound check) — each row carries the verifying Blockscout URL.
  3. `notes/Q9_DECISION.md` exists documenting the cCOP panel construction decision (V3-anchor-only OR V3+V4+Broker unified, with the pooling-assumption argument if unified); decision is committed BEFORE Phase 6 fetch starts. **If unified mode is selected, the V3+V4+Broker pooling code must live in `analysis/src/` from Phase 2 onwards (dead-code-exercised by synthetic unit tests in Iteration 1), not deferred to Phase 6** — otherwise REPRO-02's `git diff fetch/src analysis/src` empty-set invariant is violated.
  4. A pre-commit hook in `.pre-commit-config.yaml` enforces three layers: (a) the 12 anti-features from FEATURES.md AF-01..AF-12 (running it on a synthetic violating fixture exits non-zero); (b) the 2-way review-trail contract — rejects commits to `.planning/**/PLAN.md` or `.planning/ROADMAP.md` unless paired `.planning/_reviews/<basename>_{reality_checker,code_reviewer}.md` exist with `## VERDICT` headers and no unresolved BLOCKER, override flag `--allow-revision`; (c) `make schema-frozen-check` rejects any diff to `protocols/_schema.toml` after the Phase-0 commit hash recorded in `notes/PHASE_0_GATE.md`.
  5. The demand-window definition (indexer-backed analytics/UI queries only; Forno RPC keeper polling explicitly excluded) is reflected in `protocols/_schema.toml` as a comment + the `data_cost_class` enum. **The enum MUST be pre-populated at Phase 0 with all values anticipated across Iteration 1 + Iteration 2 + COPM mixing-class** (e.g. `["indexer-analytics-queries", "per-event-oracle-stretch", "per-scan-ocr-stretch"]`), so that Iteration 2 adds *only* `protocols/steer.toml`, never edits `_schema.toml` — enforced by the schema-frozen check in SC-4.
**Plans**: 7 plans (Wave 1: 01 PRE_REGISTRATION + 02 PHASE_0_GATE + 03 Q9_DECISION + 04 _schema.toml; Wave 2: 05 ichi.toml + steer.toml + 06 pre-commit hooks + Makefile + AF fixtures; Wave 3: 07 install hooks + record baseline + validate)
- [x] 00-01-PLAN.md — Author notes/PRE_REGISTRATION.md (GOV-01 + REPRO-04 decision)
- [x] 00-02-PLAN.md — Author notes/PHASE_0_GATE.md + Steer REPRO-03 primary-source pre-validation (GOV-02 + DEMAND-01)
- [x] 00-03-PLAN.md — Author notes/Q9_DECISION.md (REPRO-04 + REPRO-02 dead-code-exercise obligation)
- [x] 00-04-PLAN.md — Author protocols/_schema.toml frozen baseline with demand-window comment + enums (DEMAND-01 + GOV-03 / AF-12)
- [x] 00-05-PLAN.md — Author protocols/ichi.toml (full ~40-vault enumeration) + protocols/steer.toml (Iter-2 stub with Q-9 lock)
- [x] 00-06-PLAN.md — Pre-commit hook config + Makefile + 3 hook scripts + AF violation fixtures (GOV-03)
- [x] 00-07-PLAN.md — Install pre-commit hooks + substitute schema baseline hash + validate each hook against fixture

### Phase 1: L1 Data-Fetch Skeleton + Free-Tier Discipline
**Goal**: Stand up the TypeScript data-fetch workspace with the paid-step-is-idempotent invariant (ARCHITECTURE.md Pattern 2), cost-ledger budget gate, and subgraph-freshness wrapper — all before any bulk pull touches the 100k/mo Graph budget.
**Depends on**: Phase 0 (pre-reg + demand-window definition + Q-9 must be locked)
**Requirements**: FETCH-01, FETCH-02, FETCH-03, FETCH-04
**Primary Agent**: **Backend Architect** (TypeScript workspace architecture, viem + Graph + Mento SDK wiring, idempotent cache layer)
**Consult**: **DevOps Automator** (cost-ledger budget gate + `--force` flag + subgraph-freshness wrapper as a reusable middleware)
**Audit/Review**: Reality Checker + Code Reviewer (parallel review of the PLAN.md before any code lands; particularly the idempotency claim of FETCH-04 — must be unit-testable via sha256sum, not just asserted)
**Success Criteria** (observable artifacts):
  1. `cd fetch && pnpm install` completes; `pnpm tsc --noEmit` exits zero; `package.json` lists `viem@2.51.0`, `@x402/fetch@2.13.0`, `@graphprotocol/client-x402@1.0.0`, `graphql-request@7.4.0`, `@mento-protocol/mento-sdk@3.2.8` at the full semver pins matching STACK.md exactly, and a Blockscout v2 REST client. **Also**: `analysis/uv.lock` exists with pinned versions of `tick==0.8.0.2`, `statsmodels==0.14.6`, `polars==1.41`, `numpy==2.4.x`, `scipy==1.17.1` — pinned at Phase 1 (not deferred to Phase 5) because `tick` validation in DGP-01 is non-reproducible without it.
  2. Running `pnpm fetch ichi --dry-run` against a fixture subgraph response prints a non-zero cost-ledger row (USDC denominated, written to `data/raw/manifest.json`); attempting a fetch projected to exceed 90k queries/mo exits non-zero unless `--force` is passed.
  3. A unit test (`fetch/tests/freshness.test.ts`) validates the freshness wrapper for **both** data-source paths: (a) subgraph path — injects a synthetic response with `_meta.block.number` 101 blocks behind a mocked Forno head and asserts the wrapper throws an explicit `SubgraphLagError`; same test with lag 99 blocks passes silently. (b) Blockscout RPC path — asserts the wrapper rejects a paginated response whose `block_consensus = false` or whose most-recent block lags Forno head by > 100 blocks. Phase 1 PLAN.md must explicitly commit to which data-source path is used for the V3 Swap event panel (subgraph vs Blockscout RPC pagination); the wrapper applies to whichever path is chosen.
  4. Re-running `pnpm fetch ichi --pool 0x61Ef…829F --block-range 67000000-67100000` twice produces byte-identical Parquet output (verified via `sha256sum`) and the second run emits zero new cost-ledger rows; the cache key is `(chainId, contractAddress, blockRange, fetchTimestamp)` and is observable in `data/raw/<protocol>/manifest.json`.
  5. **Protocol-agnosticism contract test**: `analysis/tests/test_panel_agnostic.py` constructs a panel from a synthetic `protocols/test_fixture.toml` (cKES-like + COP-like + a Steer-shaped multi-vault-per-pool layout) with no protocol-name conditional branches in `analysis/src/`; a CI lint rejects any string match of `if config.name ==`, `if protocol ==`, `if vault_owner == "ichi"`, or any hard-coded fee-tier magic number (`0.0001`, `100`, `500`) outside `protocols/*.toml`. This is the load-bearing leak-gate (the string grep at Phase 6 is the cheap pre-commit version).
  6. **Cold-backfill budget dry-run**: `pnpm fetch ichi --dry-run --estimate-budget` prints the projected total Graph queries for the in-scope vault set (anchor-only OR full ICHI Celo footprint per Q-9 / Phase-0 decision); if projection > 30k, the cold-backfill must be re-scoped or budget reallocated from the 20k reserve before any production fetch. Note: the ARCHITECTURE.md budget line still labeled "Halo" (now Steer) is corrected here — 25k earmark is now Iteration-2 cold-backfill on Steer.
**Plans**: TBD

### Phase 2: Panel Build (L3) for the ICHI cKES/USDT Anchor
**Goal**: Materialize the event-level Parquet panel for ICHI on cKES/USDT (and the Q4 single-vault microcosm as sensitivity) with full on-chain provenance, Mento broker mid-rate FX snap, and the phantom-transfer filter for USDC/USDT fee-abstraction adapters.
**Depends on**: Phase 1 (L1 + L2 must be producing cached Parquet + manifest)
**Requirements**: PANEL-01, PANEL-02, PANEL-03, PANEL-04, DEMAND-01 (enforce component)
**Primary Agent**: **Data Engineer** (Parquet panel construction, polars ingestion, event-level provenance schema)
**Consult**: **Analytics Reporter** *(archived — explicit opt-in)* — produces `notes/fx_snap_decision.md` documenting alternatives considered (USDT/USD=1.0 collapse; Chainlink CELO/USD; Pyth on-Celo; Mento broker mid-rate) and the justification for the chosen anchor. Concrete artifact, not a one-paragraph sign-off.
**Audit/Review**: Reality Checker + Code Reviewer (focus: phantom-transfer filter must be unit-tested against a real on-chain fee-abstraction tx, not synthetic — this is exactly the kind of detail Reality Checker catches)
**Success Criteria** (observable artifacts):
  1. `data/raw/ichi/<pool>/<block_range>.parquet` exists for the cKES/USDT anchor pool with columns `(blockNumber, blockHash, logIndex, txHash, contractAddress, event, ...payload)` and zero rows where `blockNumber` is null; `python -c "import polars; df = polars.read_parquet(...); assert df.null_count().sum_horizontal()[0] == 0"` exits zero.
  2. Every output artifact (parquet, fit_report.json scaffolds, plots) carries the metadata header `{chainId, contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit}`; a build script `make lint-artifacts` greps each output file and exits non-zero if any header field is missing.
  3. FX-rate snap unit test: given a synthetic cKES→USDm transfer event at a fixed block, `revenue_leg.snap_fx(event, block)` calls the Mento broker mid-rate at that block and returns a rate with explicit `(source, block, mid_rate, provenance_url)` provenance; USDT/USD is treated as a separate column, never collapsed to 1.0.
  4. Phantom-transfer filter unit test: a fixture transaction containing one real cKES Swap + one USDC fee-abstraction Transfer (`from = 0x2F25deB3848C207fc8E0c34035B3Ba7fC157602B`) results in exactly one row in the panel (the Swap); the fee-abstraction Transfer is excluded; the test fails if the filter is bypassed.
**Plans**: TBD

### Phase 3: DGP Estimation (L4) with Boundary-Correct LR Test
**Goal**: Fit NHPP (Kirchner INAR(p)) and bivariate Hawkes (tick with full off-diagonal excitation matrix), then run the boundary-correct bootstrap LR test, time-rescaling KS test, held-out temporal evaluation, and profile-likelihood branching-ratio CIs — producing `fit_report.json` that survives a metadata audit.
**Depends on**: Phase 2 (panel parquet + provenance metadata must exist)
**Requirements**: DGP-01, DGP-02, DGP-03, DGP-04, DGP-05, DGP-06
**Primary Agent**: **Analytics Reporter** (NHPP + Hawkes fits, LR test orchestration, KS rescaled-time test, held-out evaluation)
**Consult / Audit**: **Model QA Specialist** (this is exactly their charter: "audits ML and statistical models end-to-end — from documentation review and data reconstruction to replication, calibration testing, interpretability analysis"; verifies boundary-correct LR test bootstrap rig + profile-likelihood CIs + Kirchner-INAR(p) implementation against tick synthetic ground truth)
**Audit/Review**: Reality Checker + Code Reviewer (parallel review of the PLAN.md; particular attention to DGP-03 boundary correction — the most common failure mode is silently using vanilla `statsmodels.likelihood_ratio_test`)
**Success Criteria** (observable artifacts):
  1. `data/fits/ichi/<run_id>/fit_report.json` exists with metadata header (chainId, contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit) AND keys `{nhpp_inar_params, hawkes_mv_params (full 2x2 alpha matrix, no diagonal-only shortcut), lr_test: {observed_stat, bootstrap_null_dist_50_50_chi2_0_chi2_1, p_value}, ks_rescaled_time: {p_value, residuals_hash}, held_out_loglik: {nhpp, hawkes}, branching_ratio_ci: {method: "profile_likelihood", lower, upper}}`.
  2. NHPP-INAR(p) implementation validation: `analysis/tests/test_nhpp_inar.py` simulates 1000 paths from `tick.hawkes.SimuHawkesExpKernels` with known parameters, refits via the Kirchner estimator, and asserts recovered parameters fall within ±10% (or documented tolerance) of ground truth; CI fails if validation regresses.
  3. Bootstrap LR rig: `dgp/lr_test.py --bootstrap-reps 1000` produces a null distribution that visibly mixes χ²(0) point mass at zero with a χ²(1) continuous component (verifiable via histogram in `reports/_diagnostics/lr_null_dist.png`); the vanilla `statsmodels.likelihood_ratio_test` call is absent from the source (`grep -r "likelihood_ratio_test" analysis/src` returns zero hits).
  4. Held-out temporal split: `fit_report.json :: held_out_loglik.nhpp` and `.hawkes` are computed on a strict time-split (last 20% of window), and the split block boundary is logged with provenance; an in-sample-only fit attempt raises `InsufficientEvaluationError`. **Stationarity diagnostic** (per PITFALLS §4): the held-out segment's mean event rate must be within ±25% of the train segment's, OR the NHPP/Hawkes fits must use a piecewise-constant or spline baseline; the diagnostic is logged in `fit_report.json :: baseline_stationarity_check` with `{train_rate, held_out_rate, ratio, decision: stationary|piecewise_required}`.
  5. The same `fit_report.json` is produced byte-identically across two runs with identical input panel + git commit (modulo wall-clock fields), demonstrating fit-step reproducibility.
**Plans**: TBD

### Phase 4: Cross-Leg Dependence (L5) + Falsification & Carr–Madan Strip (L6)
**Goal**: Quantify cross-leg dependence (cross-correlogram + permutation null + empirical copula), then run the four-condition convex-dominance gate (USDT-depeg-reparameterized for condition 4) and emit the Carr–Madan strip on a convergence-tested grid IF AND ONLY IF at least one condition passes — otherwise emit a null-result PDF via the HEDGE-05 template.
**Depends on**: Phase 3 (`fit_report.json` with NHPP/Hawkes params + LR result must exist as input to the gate)
**Requirements**: DEPEND-01, DEPEND-02, HEDGE-01, HEDGE-02, HEDGE-03, HEDGE-04, HEDGE-05 (template, where built)
**Primary Agent**: **Model QA Specialist** (falsification gate math + Carr–Madan grid convergence + USDT-depeg jump-leg calibration + three-way independence/fitted-joint/comonotone stress test — these are math-validation-heavy components that match the agent's documented charter directly; separation-of-concerns from Phase 3's Analytics Reporter primary)
**Consult**: **Analytics Reporter** *(archived — explicit opt-in)* (cross-correlogram + permutation null + empirical-copula fitting; conducts the empirical estimation that the Model QA Specialist then validates)
**Audit/Review**: Reality Checker + Code Reviewer (parallel review of the PLAN.md; particular attention to HEDGE-05 firing template — must auto-fire on the three documented conditions, not require manual override; HEDGE-03's USDT-port assumption must be explicit, not silently substituted from USDC)
**Success Criteria** (observable artifacts):
  1. `data/fits/ichi/<run_id>/joint_dist.json` exists with `{cross_correlogram: [lags, values], permutation_null: {n_reps, p_value}, empirical_copula: {family, params, bic}, vine_fallback_used: bool}`; any "joint cashflow" claim in the report (Phase 5) links to this file or the build fails (REPORT-level lint).
  2. `analysis/src/abrigo_x402/hedge/falsification.py` runs all four conditions and writes `gate_report.json` with `{vol_of_vol_gt_zero, positive_skew_fat_tails, hawkes_self_excitation, usdt_depeg_basis_jump}`, each as `{passed: bool, evidence: dict}`; condition 4 source reads "USDT depeg + USDT/USDC basis" (not USDC), verifiable via `grep -i "usdc" analysis/src/abrigo_x402/hedge/falsification.py` returning only comparison/historical-reference hits.
  3. Carr–Madan grid convergence test: `hedge/carr_madan_strip.py` starts at 2^11 grid points, escalates to 2^12 if positivity check fails, and aborts (writing `strip_degenerate.json`) if 2^12 still produces negatives — never silently emits a strip with negative implied density. Unit test simulates a fat-tail distribution that requires 2^12 and asserts the escalation triggered.
  4. Three-way joint stress test: `hedge/stress_test.py` outputs `stress_report.json` with strip prices under `{independence, fitted_joint, comonotone}` scenarios; divergence is reported as a percentage spread; large divergence (>30%) is flagged in the report build.
  5. HEDGE-05 null-result template (`reports/_templates/null_result.md`) exists and is wired such that when **any** of the three firing conditions occurs — (a) Phase-0 cost-leg gate fails (REPRO-03 threshold from `PRE_REGISTRATION.md`), (b) DGP-03 LR test is indistinguishable at α=0.05, (c) HEDGE-01 finds zero convex-dominance conditions pass — the template fires automatically and `reports/ichi.pdf` becomes a documented null-result PDF. **Three fixture sets** at `analysis/tests/fixtures/hedge_05_{null_cost,null_lr,null_convex}/` each force one firing condition (synthetic `fit_report.json` + `gate_report.json` + `cost_leg_bound.md` triplet per fixture); `pytest analysis/tests/test_null_result_template.py` confirms `reports/ichi.pdf` is regenerated as a null-result PDF in each case (verified by grep on the rendered PDF text for the null-result template's signature header).
  6. USDT-depeg jump-leg calibration source is documented in `notes/usdt_depeg_calibration.md` — either a USDT-specific Merton/Kou calibration with primary-source citations OR an explicit methodological-port assumption with bounded sensitivity analysis attached.
**Plans**: TBD

### Phase 5: Reporting + Iteration-1 PDF Deliverable (L7)
**Goal**: Ship the Iteration-1 PDF deliverable (`reports/ichi.pdf`) via Quarto/nbconvert with the spot-check checklist, cost-leg prior sensitivity sweep, and reproducibility manifest — completing Iteration 1 with either a positive convex-hedge result or a documented null-result, in PDF form (per memory `feedback_pdf_deliverable.md`).
**Depends on**: Phase 4 (gate report + strip OR null-result template fire must be resolved)
**Requirements**: REPORT-01, REPORT-02, REPORT-03, REPORT-04
**Primary Agent**: **Technical Writer** (writeup of the iteration's findings + null-result framing if applicable; also owns the Quarto/nbconvert rendering pipeline — tool selection, not subtask)
**Consult**: **Analytics Reporter** *(archived — explicit opt-in)* (substantive analytical correctness — verifies that the numbers in the PDF actually match the underlying `fit_report.json` / `gate_report.json`)
**Audit/Review**: Reality Checker + Code Reviewer (parallel review of the PLAN.md; particular attention to REPORT-04 reproducibility manifest — fresh-clone `make verify-reproducibility` must actually pass, not just nominally exist; spot-check Blockscout URLs must return HTTP 200)
**Success Criteria** (observable artifacts):
  1. `reports/ichi.pdf` exists in the repo (git-tracked), renders successfully from a fresh clone via `make report-ichi` (which invokes Quarto or `nbconvert --to pdf` against `notebooks/ichi_iteration.ipynb`), and the PDF is non-empty (size > 50KB); markdown-only output is rejected by the build target.
  2. The PDF contains a spot-check section with 5 randomly-chosen panel rows, each carrying a clickable Blockscout URL of the form `https://celo.blockscout.com/tx/0x...`; running the URLs through `curl -I` returns HTTP 200 (or the PDF build script logs the verification per row).
  3. The PDF contains a cost-leg prior sensitivity section showing headline DGP/strip metrics under `{rate_per_event × 0.5, rate_per_event × 1.0, rate_per_event × 1.5}` and the same sweep on `USD_per_query`; the underlying `sensitivity_sweep.json` artifact lives at `data/fits/ichi/<run_id>/sensitivity_sweep.json` with all downstream estimates re-run (not approximated).
  4. `reports/MANIFEST.md` (reproducibility manifest) exists listing subgraph block-pins, `uv.lock` SHA, `package-lock.json` SHA, and output checksums for every artifact `reports/ichi.pdf` depends on; a fresh clone running `make verify-reproducibility` recomputes checksums and exits zero only if they match.
**Plans**: TBD

### Phase 6: Iteration-2 Swap-Surface Validation on Steer (cCOP/USDT)
**Goal**: Validate the swap-surface invariant by running the same Phase 2–5 pipeline on Steer on cCOP/USDT with ZERO edits to `fetch/src/` or `analysis/src/` — and emit a null-result if the Steer cost-leg empirical lower-bound check fails (first step of Iteration 2). **Steer's expected-failure path on the cost-leg lower-bound check is itself the FEATURES.md D-08 negative-control validation** — null-result emission must be observed at least once across the two iterations to confirm the falsification machinery works in practice.
**Depends on**: Phase 5 (Iteration 1 PDF deliverable must have shipped — *process gate*, not artifact consumption; Phase 6 consumes no data artifact from Phase 5, but REPRO-02 cannot validate the parameter-driven swap until Iteration 1 has actually shipped a complete output set); also implicit dependency on Phase 0 Q-9 decision
**Requirements**: REPRO-01, REPRO-02, REPRO-03 (first-step), REPRO-04 (enforcement component), HEDGE-05 (firing condition for Steer cost-leg failure)
**Primary Agent**: **Data Engineer** (Steer protocol-spec TOML authoring + iteration-2 data-fetch re-run via swap-surface) + **Analytics Reporter** *(archived — explicit opt-in)* (Phase 2–5 estimation re-run) + **Reality Checker** primary on REPRO-03's cost-leg lower-bound check — this is the binding gate for Iteration 2 and Reality Checker's "needs overwhelming proof" default is exactly the right epistemic posture for the binding-gate verification
**Consult / Audit (sub-task)**: **Model QA Specialist** (verifies the re-run is byte-equivalent on the pipeline side; that Steer's cCOP results aren't contaminated by ICHI's cKES priors)
**Audit/Review (PLAN.md)**: **Code Reviewer + Model QA Specialist** (parallel review of the PLAN.md; Reality Checker is *not* on the PLAN.md audit for Phase 6 since they're consumed by the REPRO-03 primary work above — separation of concerns; particular attention to leak-gate enforcement — `grep -r "ichi"` must actually be in CI, not just specified)
**Success Criteria** (observable artifacts):
  1. `protocols/steer.toml` exists fully populated with the cCOP/USDT primary pool, Steer factory address, vault enumeration, and a `cost_leg_lower_bound_verified` field set to `true` only after the empirical check (REPRO-03) runs.
  2. The cost-leg lower-bound check is the first executed step of Iteration 2 (timestamped commit precedes any Phase 2–5 re-run for Steer); the check writes `notes/steer_cost_leg_bound.md` with primary-source enumeration of Steer's Celo-only analytics-query footprint; if the check fails, `reports/steer_null_result.pdf` ships instead and Phase 6 exits cleanly (no fetch/src or analysis/src edits attempted).
  3. Leak gate (two layers): (a) `grep -ri "ichi" fetch/src analysis/src` returns zero hits before Phase 6 fetch begins; CI enforces via `make leak-check` (matches inside `protocols/*.toml` and `protocols/_schema.toml` comments are explicitly excluded by being outside the searched roots). Same check passes for any other Iteration-1-specific identifier (cKES address, ICHI factory address) outside `protocols/ichi.toml`. (b) The Phase 1 SC-5 protocol-agnosticism contract test (lint rejecting `if config.name ==`, magic fee-tier numbers, single-owner-per-pool assumptions) continues to pass — this is the load-bearing algorithmic-leak gate; the string grep is the cheap pre-commit complement.
  4. End-to-end re-run: `make iteration-2-full` invokes the same Phase 2–5 pipeline against `protocols/steer.toml` and produces `reports/steer.pdf` (or `reports/steer_null_result.pdf`); `git diff fetch/src analysis/src` between Iteration-1-complete and Iteration-2-complete commits returns an empty diff.
  5. cCOP panel construction follows the Phase-0-locked Q-9 decision (V3-only or V3+V4+Broker unified, per `notes/Q9_DECISION.md`); if unified, the cross-class permutation test result is committed at `data/fits/steer/<run_id>/q9_pooling_test.json` with a documented `pass` or `fail` verdict before joint Hawkes estimation runs.
**Plans**: TBD

### Phase 7: Cross-Iteration Synthesis & Methodological Refinements (PROCEDURAL — non-gating on v1)
**Status**: **PROCEDURAL phase, listed for continuity, NOT gating v1-completion.** v1 is complete when Phases 0–6 ship (REPORT-01..04 in Phase 5 and REPRO-01..04 in Phase 6 are the v1 closing reqs). Phase 7 fires the *v2-deferred* SYNTH-V2-01 and SYNTH-V2-02 requirements (per REQUIREMENTS.md "v2 Requirements" section) and produces input substrate for the next iteration cycle. It MAY be deferred to a follow-on milestone without violating the v1 contract.
**Goal**: Consume results from Iterations 1 + 2 (or the null-result outcomes) to resolve the three remaining open methodological questions from CANDIDATES §6 (Q4 per-protocol-vs-per-vault granularity; Q6 cost-leg empirical bounds; Q7 TVL-too-thin floor) and update v2-iteration guidance.
**Depends on**: Phase 6 (both iterations' results — positive or null — must be on disk)
**Requirements**: (no v1 requirements; fires v2 SYNTH-V2-01 + SYNTH-V2-02 only)
**Primary Agent**: **Analytics Reporter** *(archived — explicit opt-in)* (cross-iteration retrospective; Q4 per-protocol-vs-per-vault verdict; Q6 empirical cost-leg bound consolidation)
**Consult**: **Technical Writer** (`methodological_refinements.md` authoring) + **Model QA Specialist** (Q7 substrate-floor inclusion-rule sign-off)
**Audit/Review**: Reality Checker + Code Reviewer (parallel review of the PLAN.md, *if* this phase is executed; verifying retrospective claims trace back to specific `fit_report.json` / `gate_report.json` files, not vibes)
**Success Criteria** (observable artifacts — fire SYNTH-V2-01/02, do not gate v1):
  1. `notes/methodological_refinements.md` exists with retrospective evidence resolving Q4 (per-protocol vs per-vault granularity) — citing which choice gave the cleaner DGP fit across both iterations, with `fit_report.json` references.
  2. `notes/cost_leg_empirical_bounds.md` exists with the empirical Graph-spend bounds for both ICHI-on-Celo and Steer-on-Celo, with provenance log entries; the file documents whether each cleared the demand window's lower bound.
  3. `notes/tvl_thin_floor_decision.md` exists committing the cXOF/USDm and BRLm/EURm pool inclusion/exclusion rule for future iterations, with the substrate-too-thin flag propagation rule (if any) into Hawkes branching-ratio CIs.
**Plans**: TBD

---

## Progress

| Phase | Plans Complete | Status | Review Status (RC / CR) | Completed |
|-------|----------------|--------|--------------------------|-----------|
| 0. Candidate Eligibility & Pre-Registration | 7/7 | Complete | pending / pending | 2026-05-25 |
| 1. L1 Data-Fetch Skeleton | 0/0 | Not started | pending / pending | - |
| 2. Panel Build (ICHI cKES/USDT) | 0/0 | Not started | pending / pending | - |
| 3. DGP Estimation | 0/0 | Not started | pending / pending | - |
| 4. Dependence + Falsification + Strip | 0/0 | Not started | pending / pending | - |
| 5. Reporting + Iteration-1 PDF | 0/0 | Not started | pending / pending | - |
| 6. Iteration-2 Steer Swap | 0/0 | Not started | pending / pending | - |
| 7. Cross-Iteration Synthesis (procedural, non-gating) | 0/0 | Not started | pending / pending | - |

**Review Status semantics**: column reads `<Reality Checker verdict> / <Code Reviewer verdict>`. A phase cannot be marked Complete until both paired review files exist under `.planning/_reviews/phase_N_{reality_checker,code_reviewer}.md` AND neither carries an unresolved BLOCKER finding. Pre-commit hook (Phase 0 SC-4 (b)) enforces this contract.

---

## Phase Ordering Rationale

- **Phase 0 is blocking** because GOV-01 pre-registration must precede any vault-level estimation (anti-fishing discipline; AF-03/AF-04 prevention) and REPRO-04's cCOP-panel-construction decision must be locked before Iteration 2 fetch starts. Phase 0 also operationalizes the demand-window definition that Phase 2 enforces.
- **Phases 1 → 2 → 3 → 4 → 5** follow the strict L1 → L2 → L3 → L4 → L5+L6 → L7 dependency chain from `research/ARCHITECTURE.md` "Build Order". Each phase ships a verifiable on-disk artifact (parquet, fit_report.json, gate_report.json, ichi.pdf) that the next phase consumes or short-circuits on (null-result path live at every gate per HEDGE-05).
- **Phase 5 is gated on Phase 4** because PDF rendering without the falsification gate having run would publish an unjustified hedge design (FEATURES.md AF-06 strip-without-gate).
- **Phase 6 (Iteration 2) is gated on Phase 5 (Iteration 1 PDF deliverable shipped)** per PROJECT.md Constraints. REPRO-03's cost-leg lower-bound check runs as Phase 6's first step; failure routes to a documented null-result without modifying `fetch/src/` or `analysis/src/` (REPRO-01's grep-leak gate enforces this).
- **Phase 7 is a synthesis phase** that consumes results from Phases 3–6 and cannot be done earlier without becoming speculative.

## HEDGE-05 Firing Scope (Null-Result Template)

The HEDGE-05 null-result **PDF template** is built in Phase 4 (see Phase 4 success criterion 5). Phase-0 firing produces a **memo-only** null-result (no PDF deliverable available pre-Phase-4). Firing scopes:

- **Phase 0** — if any Phase-0 eligibility check fails for a candidate, gate-exit emits a *memo-only* null-result. `notes/PHASE_0_GATE.md` documents the disqualification (e.g., Steer's `CONDITIONAL` row becomes `FAIL` if the REPRO-03 threshold check has already been pre-validated below 100k/mo). PDF null-result deliverable not available at this phase — Phase 0 fires **no** `reports/*.pdf`. Candidate switch or defer happens at memo level.
- **Phase 3** — if NHPP-vs-Hawkes is indistinguishable at conventional α per DGP-03 boundary-correct LR test (HEDGE-05 firing condition b). PDF template now exists (built in Phase 4 but Phase 3 fires *into* Phase 4's gate, so Phase 4 actually emits the PDF in this case). In practice Phase 3 sets a flag in `fit_report.json :: dgp_indistinguishable = true` which Phase 4 reads.
- **Phase 4** — if no convex-dominance condition holds per HEDGE-01 (HEDGE-05 firing condition c). PDF template fires *in-phase*; this is the template's "home" phase.
- **Phase 6** — if Steer cost-leg empirical lower-bound check fails per REPRO-03 / CANDIDATES §6 Q6b against the threshold pre-committed in `notes/PRE_REGISTRATION.md` (HEDGE-05 firing condition a — now the leading firing condition for Steer Iteration 2 after the 2026-05-25 thinness-retraction audit). PDF template exists from Phase 4; Phase 6 emits `reports/steer_null_result.pdf`.

In each case, the deliverable (memo or PDF) documents the null with disqualifying evidence; null results are valid completions, not failures.

---

*Created: 2026-05-25*
*Roadmap source: `.planning/REQUIREMENTS.md` (32 v1 reqs) + `.planning/research/SUMMARY.md` (suggested 8-phase structure) + `.planning/research/ARCHITECTURE.md` (L1→L7 build order) + `.planning/research/PITFALLS.md` (phase-to-pitfall mapping) + `.planning/research/CANDIDATES.md` (§7 hidden-volume audit + Q-9)*
