# Roadmap Reality Checker Review

**Artifact:** `.planning/ROADMAP.md` (165 lines, 8 phases, 2026-05-25)
**Reviewer:** Reality Checker (epistemic-skepticism default)
**Date:** 2026-05-25

---

## VERDICT

**NEEDS WORK.**

The discipline here is unusually real — pre-registration ordering enforced via git log, leak-gate via `grep -r "ichi"`, boundary-correct LR test explicitly forbids `statsmodels.likelihood_ratio_test` via grep, the 2026-05-25 thinness retraction is named in the roadmap rather than buried. This is not theater. But four load-bearing elements are written in ways a motivated researcher can satisfy nominally without actually satisfying — most acutely the HEDGE-05 null-result mechanism in Phase 0, the REPRO-03 cost-leg lower-bound gate in Phase 6, and the leak-gate's scope. Fix those four and this is ready to commit.

---

## BLOCKERS

### B1 — HEDGE-05 firing template does not exist at Phase 0, but Phase 0 is one of its declared firing scopes

The roadmap's §"HEDGE-05 Firing Scope" lists **Phase 0** as a firing scope. But Phase 4 success criterion 5 explicitly says the null-result template is **built** in Phase 4. Phase 0 fires before Phase 4 by 4 phases. If Phase 0's eligibility gate fails for, say, Steer (CONDITIONAL row in `PHASE_0_GATE.md`), what does Phase 0 actually emit? The roadmap says "gate exit memo emits null-result and switches/defers candidate" — but the *template that makes that emission a well-formed PDF deliverable* doesn't yet exist. This is exactly the kind of forward-reference that collapses in execution: Phase 0 will either (a) emit a markdown stub and call it done, or (b) inline-construct an ad-hoc null-result document that diverges from the Phase-4 template once it ships.

**Fix:** Either move the null-result template build into Phase 0 (it's a markdown + Quarto skeleton, not estimation work — there's no dependency), or make explicit that Phase 0's "null-result" mechanism for the eligibility gate is a **memo only** (not a PDF deliverable) and the PDF null-result path only opens once the Phase-4 template exists.

### B2 — REPRO-03 cost-leg lower-bound gate is the binding constraint on Iteration 2 but has no concrete pass/fail threshold

Phase 6 success criterion 2: "The cost-leg lower-bound check is the first executed step… the check writes `notes/steer_cost_leg_bound.md` with primary-source enumeration of Steer's Celo-only analytics-query footprint; if the check fails, `reports/steer_null_result.pdf` ships instead."

What does "fails" mean? CANDIDATES §4.2 says Steer-on-Celo's plausible Graph spend is "$0–$40/mo… may sit below the demand window's lower bound." The demand window's lower bound is the 100k-queries/mo free-tier ceiling, expressed in dollars as ~$0 (free). So the test is: *is Steer paying for Graph queries above the free tier?* This needs a numeric threshold. Pitfall 6 explicitly warns: "If the bounds straddle the demand window, the answer is 'data insufficient — falsification gate triggers, stop, document null result.' Do not split-the-difference into the window." But the roadmap's criterion 2 doesn't operationalize that — it leaves "fails" to the researcher's judgment, which is exactly the spec-swap surface AF-03 forbids.

**Fix:** Phase 0's `PRE_REGISTRATION.md` must commit, in advance, the numeric pass condition for REPRO-03 — e.g., "PASS = primary-source evidence (Steer Discord/team confirmation OR on-chain subscription contract OR analytics-team subgraph spend log) shows ≥ 100k Graph queries/mo attributable to Celo deployment; STRADDLE = bounds include the free-tier ceiling, fires null-result; FAIL = primary-source bound is below 100k/mo, fires null-result." Without a pre-committed threshold, a motivated researcher will read "$25/mo equivalent" and rationalize "that's inside the window, ship it."

### B3 — Leak-gate is grep-on-strings, which misses non-string ICHI-specific leakage

REPRO-01: `grep -r "ichi" fetch/src analysis/src` returning zero hits is the leak-gate (Phase 6 criterion 3). The roadmap also names two specific identifiers ("cKES address, ICHI factory address"). But the genuine reproducibility failure mode is **algorithmic**, not string-level:

- Magic-number `0.0001` fee tier hard-coded in falsification.py because all ICHI pools surveyed are fee=100 — Steer's cCOP/USDT is also fee=100 so this hides until a fee-1500 vault enters scope, but it's still a leak.
- Schema assumption that there's exactly one ICHIVault owner per pool (Phase 2 phantom-transfer filter logic) vs. Steer's beacon-proxy multi-vault-per-pool pattern (CANDIDATES §3 shows 3 Steer BeaconProxies on cCOP/USDT alone). The phantom-transfer filter in PANEL-04 is keyed on the USDC/USDT fee-abstraction adapter addresses; that part is protocol-agnostic. But if any ICHI-shaped assumption ("vault has exactly one owner") seeps into panel construction, `grep "ichi"` will not find it.
- Q-9 conditional logic: if cCOP panel construction is "unified V3+V4+Broker," that's a code path that didn't exist for Iteration 1. The REPRO-02 invariant — `git diff fetch/src analysis/src` is empty between iterations — is in direct tension with Q-9 unified panel mode existing in `analysis/src/`. Either the unified panel code is in `analysis/src/` from Iteration 1 (dead code in Iteration 1, exercised in Iteration 2), or REPRO-02 fails for the unified path.

**Fix:** Phase 1 PLAN.md must add a positive integration test, not just the grep negative: a contract-style assertion `analysis/src/abrigo_x402/panel.py` accepts an arbitrary `protocols/*.toml` and constructs a panel with no protocol-name conditional branches (CI lints for `if config.name == "ichi"` patterns). The grep stays as a cheap pre-commit hook, but the load-bearing check is the contract test. Also: Phase 0 must lock the Q-9 decision such that *if unified is chosen, the V3+V4+Broker pooling code lives in analysis/src from the start of Iteration 1* (exercised by a unit test on synthetic data), not added at Phase 6.

### B4 — Phase 7's "fires SYNTH-V2-01 and SYNTH-V2-02" creates a deferred-requirement loophole

Phase 7 lists `(none new; fires the SYNTH-V2-01 and SYNTH-V2-02 v2 requirements that are intentionally deferred)`. REQUIREMENTS.md classifies SYNTH-V2-01/02 as **v2 (deferred, not in Iteration 1 or Iteration 2 scope)**. So Phase 7 is doing v2 work inside the v1 roadmap. Either it's v1 (then promote the reqs out of v2), or it's v2 (then drop Phase 7 from this roadmap). As written, the success criteria of Phase 7 (3 `notes/*.md` files) are not tied to any v1 requirement — there is no v1 gate that fails if Phase 7 doesn't ship. Therefore Phase 7 can be silently skipped while the v1 roadmap reports "complete."

**Fix:** Either (a) demote Phase 7 to a v2 phase listed for context but not gated as v1-complete; or (b) promote SYNTH-V2-01/02 into v1 (with traceability table updated). Pick one. The current straddle is exactly the kind of "implicit deferral" that erodes anti-fishing discipline.

---

## CONCERNS

### C1 — Agent assignments are mostly load-bearing, with two decorative ones

Reviewed phase-by-phase:
- Phase 0 *Senior Project Manager* + *DevOps Automator* + *Blockchain Security Auditor*: **load-bearing**. Security Auditor verifying Blockscout URLs for the two factory addresses is a real, verifiable subtask.
- Phase 1 *Backend Architect* + *DevOps Automator*: **load-bearing**. Cost-ledger as middleware is a concrete deliverable.
- Phase 2 *Data Engineer* + *Analytics Reporter (consult on FX-rate snap)*: **Analytics Reporter consult is borderline decorative** — "confirms Mento broker mid-rate at event block is the correct anchor" is a one-paragraph methodological sign-off that doesn't require a dedicated agent. Either fold it into the primary or specify *what* the consult produces (e.g., a 1-page `notes/fx_snap_decision.md` with the alternatives considered and rejected).
- Phase 3 *Analytics Reporter* + *Model QA Specialist*: **load-bearing**. Model QA against tick synthetic ground truth is exactly the binding check.
- Phase 4 *Analytics Reporter* + *Model QA Specialist*: **load-bearing**.
- Phase 5 *Technical Writer* + *Document Generator* + *Analytics Reporter*: **three agents for a PDF render is over-staffed**. Document Generator is plausibly decorative — Quarto/nbconvert is a tool, not a subtask requiring a specialized agent. Fold into Technical Writer or drop.
- Phase 6 **dual primary** *Data Engineer + Analytics Reporter*: this is correct (two distinct workstreams). Model QA Specialist consult on leak verification is load-bearing.
- Phase 7 *Analytics Reporter* + *Technical Writer* + *Model QA Specialist*: load-bearing if Phase 7 survives B4.

**Fix:** Drop Document Generator from Phase 5. Specify Analytics Reporter's Phase 2 deliverable as `notes/fx_snap_decision.md` or fold into primary.

### C2 — Phase 1 success criterion 1 pins viem@2.51 but doesn't pin Solidity-side or Python-side versions

Criterion 1: "package.json lists `viem@2.51`, `@x402/fetch@2.13`…" — TS side is pinned to specific minor versions. But Phase 1 doesn't touch Python and the Python tooling (`uv.lock`, polars, statsmodels, tick) isn't pinned until Phase 5's REPORT-04 manifest. Tick is the load-bearing one (DGP-01 says "implementation validated against `tick.hawkes.SimuHawkesExpKernels` synthetic data"); tick has a history of breaking changes between minor versions and pulls in scipy/sklearn pin constraints. If Phase 3 starts and tick installs at whatever pip resolves, the validation in DGP-01 is non-reproducible.

**Fix:** Phase 1 success criterion 1 should also require `uv.lock` exists with `tick`, `statsmodels`, `polars`, `numpy`, `scipy` pinned, even though the Python code lands in Phases 2–4. Pin once, at the start.

### C3 — "Subgraph-freshness wrapper" assumes a subgraph exists; CANDIDATES §1.10 says no subgraph was used in discovery (Blockscout only)

PITFALLS §2 and Phase 1 FETCH-03 both presume the Iteration 1 pipeline consumes Graph subgraph data. But CANDIDATES §7.1 explicitly says "No subgraph use. All counts are from Blockscout pagination of decoded logs." If Iteration 1's revenue-leg arrival event class is "Uniswap V3 Swap events on the anchor pool" (per §7.3), is that data sourced from a Uniswap V3 Celo subgraph (if one exists with adequate freshness) or from direct Blockscout/Forno pagination? If the latter, the subgraph-freshness wrapper is unused dead code in Iteration 1, and the Graph budget allocation (next concern) is overstated.

**Fix:** Phase 1 PLAN.md must explicitly state which data source provides V3 Swap events for the panel (subgraph vs Blockscout RPC). If Blockscout RPC, FETCH-03 becomes a Blockscout-pagination-freshness wrapper (different shape — Blockscout returns latest first, freshness is per-page not per-meta-block), and the Graph budget question (next) needs re-grounding.

### C4 — Graph budget allocation may have a phantom 25k earmark for "Halo (now Steer)" but Steer's spend profile is fundamentally smaller

ARCHITECTURE.md §"Free-Tier Resource Budget" allocates:
- 30k L1 cold backfill (one-shot, per protocol)
- 15k L1 incremental (~500/day)
- 10k κ-instrumentation experiments
- 25k Iteration-2 cold backfill ("Halo")
- 20k reserve

Two issues:
1. The 25k Iteration-2 line is named "Halo" — Halo is disqualified (PROJECT.md scope-correction). Iteration 2 is Steer. CANDIDATES §4.2 estimates Steer-on-Celo plausibly spends $0–$40/mo on Graph — so the 25k allocation is *probably* an overestimate for Steer's *own* operational footprint, but the project's *backfill* spend is independent of the protocol's *operational* spend. Need to disambiguate which 25k we mean.
2. ICHI scope expanded from "one anchor vault" to "multiple ICHI vaults on Celo" (per PROJECT.md scope correction "Allow Minteo COPM into scope" + Phase 2 mention of "Q4 single-vault microcosm as sensitivity"). If the Iteration-1 panel covers ≥ 40 ICHI vaults' Mint/Burn events across multiple pools, the 30k cold-backfill allocation could blow up. ARCHITECTURE.md was written before this scope correction (note: I haven't dated it but the scope correction explicitly post-dates the v1 plan).

**Fix:** Phase 1 PLAN.md should re-validate the 30k/15k/25k budget against the actual ICHI vault count in scope. If the panel is anchor-only (cKES/USDT $130k pool) the 30k is fine; if it's all 40+ ICHI vaults the budget needs a dry-run estimate (count distinct subgraph pages × pages-per-vault × vaults) before any production fetch.

### C5 — Two-way review discipline documented in §"Execution discipline" but not gated in the Progress table

The roadmap describes the two-way review process (lines 13–14) and every phase's `Audit/Review` line names "Reality Checker + Code Reviewer". But the §Progress table at the bottom tracks only "Plans Complete" and "Status". There's no column tracking "Review Status" — so a phase can be marked Complete without the review trail being observable. The mechanism that forces future phases to actually run the review is the human running `/gsd:plan-phase N`, which presumably triggers the review. If that command doesn't reliably trigger both reviewers in parallel, the discipline collapses on phase 2.

**Fix:** Add a "Review Status" column to the Progress table (`pending / RC ok / CR ok / both ok`) and document in §"Execution discipline" that a phase cannot be marked Complete until both reviewers' artifacts exist under `.planning/_reviews/phase_N_*.md`. This is cheap and forces the trail.

### C6 — Held-out temporal split is "last 20% of window" but ICHI's vault deployment history spans ~1 year with bursty rebalance activity

DGP-04 / Phase 3 criterion 4: "Held-out temporal split: `held_out_loglik.nhpp` and `.hawkes` are computed on a strict time-split (last 20% of window)."

For the cKES/USDT V3 Swap stream (the recommended dependent variable per CANDIDATES §7.3), 30-day swap counts of ~4,440 mean a "last 20%" split is the last ~6 days = ~880 events. That's fine. But if the panel extends to the full lifetime window (~1+ year per CANDIDATES §4.1 "earliest vault at block 28527843, mid-2024"), and rebalance/swap intensity has visibly drifted (very plausible for a young pool), then "last 20%" tests the tail of a non-stationary process against a stationary model fit on the prior. The held-out loglik will look worse than in-sample purely from time-varying baseline, indistinguishably from genuine overfit.

This is exactly Pitfall 4's warning about misspecified immigration absorbing into spurious self-excitation. The roadmap mentions held-out evaluation but doesn't require a stationarity diagnostic.

**Fix:** Phase 3 success criterion 4 should add: "the train/held-out split's first-moment (mean event rate) must be within ±X% of the train segment's, OR the fit must use a non-stationary baseline (piecewise-constant or spline NHPP)." Either matches Pitfall 4's prescription; the current spec doesn't pin which way.

---

## WHAT IT GETS RIGHT

Genuine, not theatrical:

1. **Phase 0's git-log-ordering rule** ("PRE_REGISTRATION.md committed BEFORE any commit under `analysis/src/` or `data/raw/`. Git log proves the ordering."): this is a force-functioning anti-fishing mechanism. A pre-commit hook can mechanically verify the ordering. Strong.

2. **Phase 3 criterion 3's negative grep** (`grep -r "likelihood_ratio_test" analysis/src` returns zero hits): explicitly forbids the most common DGP-03 failure mode. Reality Checker–style "prove the bad shortcut isn't present" rather than "prove the good thing is present." Excellent.

3. **Phase 4 criterion 2's negative grep on `usdc`**: enforces the USDT-reparameterization of condition 4 at code level, not just narrative. Matches the 2026-05-25 thinness-retraction discipline of catching errors at the artifact, not at the report.

4. **The thinness retraction is named in the roadmap** (lines 105–123 of PROJECT.md and the explicit footnote in HEDGE-05 firing-condition (b)): the project survived a contradiction and updated its own record. That is the rare case of "we noticed the spec was wrong and changed it" rather than "we noticed the spec was wrong and rationalized." Honest.

5. **Phase 6 criterion 4's `git diff` empty-set test** between iteration-1-complete and iteration-2-complete commits is a stronger reproducibility gate than the grep alone. If both gates pass, the swap-surface is real.

6. **HEDGE-05 has four enumerated firing conditions** (Phases 0, 3, 4, 6) and the roadmap explicitly says "null results are valid completions, not failures." The framing is correct even if Blocker B1 needs to be fixed.

7. **Phase 4 criterion 3's grid escalation** (2^11 → 2^12 → abort with `strip_degenerate.json`): force-functions the Pitfall 7 negative-density problem at code level. The abort path is named, not implicit.

---

## SPECIFIC FIXES

Edits to ROADMAP.md, line-targeted:

1. **B1 fix** — In §"HEDGE-05 Firing Scope" (line ~177), change Phase 0 entry to: "Phase 0 — if any Phase-0 eligibility check fails, gate-exit emits a *memo-only* null-result (`notes/PHASE_0_GATE.md` documents the disqualification). PDF null-result deliverable not available until Phase 4 builds the template; therefore Phase 0 firing produces no `reports/*.pdf`."

2. **B2 fix** — In Phase 0 success criterion 1 (PRE_REGISTRATION.md content), append: "PRE_REGISTRATION.md must include the Phase-6 REPRO-03 numeric pass/straddle/fail thresholds: PASS = primary-source ≥ 100k Graph queries/mo attributable to Steer's Celo deployment; STRADDLE = bounds include 100k/mo (fires null-result); FAIL = primary-source bound < 100k/mo (fires null-result). Threshold committed BEFORE Phase 6 first execution."

3. **B3 fix** — In Phase 1 success criterion (new criterion 5): "Protocol-agnosticism contract test: `analysis/tests/test_panel_agnostic.py` constructs a panel from a synthetic `protocols/test_fixture.toml` with no protocol-name conditional branches in `analysis/src/`; a CI lint rejects any string match of `if config.name ==` or `if protocol ==` patterns in `analysis/src/`." Also: append to Phase 0 Q-9 decision artifact: "If unified panel mode is selected, the V3+V4+Broker pooling code lives in `analysis/src/` from Phase 2 onwards (exercised by synthetic unit tests in Iteration 1), not deferred to Phase 6."

4. **B4 fix** — Either (option A) demote Phase 7 to "v2 substrate, not gated as v1-complete; listed for continuity"; or (option B) promote SYNTH-V2-01/02 to v1 in REQUIREMENTS.md and update the traceability table. Pick one explicitly in §Phase Ordering Rationale.

5. **C1 fix** — Phase 2 *Consult*: replace "confirms Mento broker mid-rate at event block is the correct anchor" with "produces `notes/fx_snap_decision.md` documenting the alternatives considered (USDT/USD=1.0 collapse; Chainlink CELO/USD; Pyth on-Celo; Mento broker mid-rate) and the justification for the chosen anchor." Phase 5: drop Document Generator; fold tool selection into Technical Writer.

6. **C2 fix** — Phase 1 success criterion 1 append: "and `analysis/uv.lock` exists with pinned versions of `tick`, `statsmodels`, `polars`, `numpy`, `scipy`."

7. **C3 fix** — Phase 1 PLAN.md (when written) must commit to data source for V3 Swap event panel: subgraph (then FETCH-03 wrapper applies as written) or Blockscout RPC pagination (then FETCH-03 reshaped to a Blockscout-pagination-freshness wrapper).

8. **C4 fix** — Phase 1 success criterion (new criterion 5 or appended to criterion 2): "Cold-backfill budget dry-run: `pnpm fetch ichi --dry-run --estimate-budget` prints the projected total Graph queries for the in-scope vault set; if projection > 30k, the cold-backfill must be re-scoped or the budget reallocated from reserve before any production fetch."

9. **C5 fix** — Append column to Progress table (line ~153): `| Review Status (RC / CR) |`. Append to §"Execution discipline": "A phase is not marked Complete in the Progress table until both `.planning/_reviews/phase_N_reality_checker.md` and `.planning/_reviews/phase_N_code_reviewer.md` exist and neither contains a BLOCKER finding."

10. **C6 fix** — Phase 3 success criterion 4 append: "the held-out segment's mean event rate must be within ±25% of the train segment's; if outside, the NHPP/Hawkes fits must use a piecewise-constant or spline baseline (Pitfall 4 prescription) and the diagnostic is logged in `fit_report.json :: baseline_stationarity_check`."

---

**Bottom line:** Fix B1–B4 before commit; address C1–C6 as TODO trail in the relevant phase PLAN.md files. The roadmap is structurally sound and the discipline is real where it counts. The blockers are concentrated at the gates (Phase 0 null-result, Phase 6 cost-leg, leak-gate scope, Phase 7 categorization), not in the methodology.
