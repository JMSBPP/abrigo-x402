# Phase 4: Cross-Leg Dependence (L5) + Falsification & Carr–Madan Strip (L6) - Context

**Gathered:** 2026-05-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Three sequenced deliverables on top of Phase 3's `fit_report.json` substrate, all written into the same `data/fits/ichi/<run_id>/` directory:

1. **L5 dependence (DEPEND-01/02):** cross-correlogram + permutation null + empirical copula (vine fallback only if BIC prefers) on the bivariate (`leg_0`, `leg_1`) arrival streams → `joint_dist.json`.
2. **L6 falsification (HEDGE-01/03):** four-condition convex-dominance gate — (1) vol-of-vol > 0, (2) positive skew / fat tails, (3) Hawkes self-excitation, (4) **USDT depeg + USDT/USDC basis jump** (NOT USDC) → `gate_report.json`.
3. **L6 hedge sketch (HEDGE-02/04):** Carr–Madan replicating strip on a convergence-tested grid (2¹¹ → 2¹², abort to `strip_degenerate.json`) + three-way stress test (independence / fitted-joint / comonotone) → `strip.json` + `stress_report.json`, **only if at least one gate condition passes**; otherwise HEDGE-05 auto-fires and `reports/ichi.pdf` is rendered as a null-result PDF via `hedge/null_result.py`.

Out of scope (locked by ROADMAP / PRE_REGISTRATION / ROADMAP-EXTENSIONS): power-law Hawkes kernel, bootstrap CIs on all DGP params, structural-break test, streaming-tokenization Phase 4 generalization, Solidity hedge contract deployment, subscription/recurring x402 payment overlay.

</domain>

<decisions>
## Implementation Decisions

### HEDGE-05 firing wiring + PDF toolchain

- **Firing decision lives in a dedicated `analysis/src/abrigo_x402/hedge/null_result.py` module.** Single entry point. Reads `fit_report.json` + `gate_report.json` + (optionally) the per-candidate `notes/<protocol>_cost_leg_bound.md`, decides which of the three firing conditions tripped — (a) Phase-0 cost-leg gate fail, (b) DGP-03 LR-indistinguishable at α=0.05, (c) HEDGE-01 zero convex-dominance conditions — and either invokes the strip pipeline (no firing) or renders the null-result PDF (firing). Mirrors Phase 3's `orchestrator.py` single-entry pattern. The hedge CLI subcommand calls it.
- **PDF rendering toolchain: Quarto** (`.qmd` template with embedded Python code blocks, renders to PDF via LaTeX). Adds a TeX dependency to the dev environment. Supports cross-references and citations natively → plays cleanly with `notes/PRE_REGISTRATION.md` citations in Phase 5.
- **One template, three context-block branches:** `reports/_templates/null_result.qmd` carries a single signature header + a switch on the firing condition that swaps in the relevant evidence block. Same template is reused by Phase 5 for the positive-result case as a sub-template. One file to maintain.
- **PDF signature for grep-based detection: dual.** Top of every null-result PDF carries (a) visible heading `# HEDGE-05 NULL RESULT — <firing-condition>` and (b) a machine-readable marker `HEDGE05-NULL-RESULT-V1` (in PDF footer or metadata field). `tests/test_null_result_template.py` greps both via `pdftotext` so it survives font/PDF library quirks.
- **Three fixture sets at `analysis/tests/fixtures/hedge_05_{null_cost,null_lr,null_convex}/`**, each a synthetic `fit_report.json` + `gate_report.json` + `cost_leg_bound.md` triplet that forces exactly one firing condition. `pytest tests/test_null_result_template.py` confirms `reports/ichi.pdf` is regenerated as a null-result PDF in each case (verified by grep on the rendered PDF text for both signature markers).

### USDT-depeg jump-leg calibration (HEDGE-03)

- **Primary calibration source: defensible literature-range stipulation + bounded sensitivity.** Phase 4 RESEARCH verified that the original CONTEXT draft's "port from Hernandez Cruz 2024" path is unworkable: arxiv 2407.11716 is a Difference-in-Differences transparency/MCI study and arxiv 2602.18820 (Wu & Liu 2026) is a QVAR analysis — neither publishes Merton/Kou jump-diffusion parameters. The base triple `(λ, μ_J, σ_J)` is therefore **stipulated from defensible literature ranges** (Merton 1976 ballpark for stablecoin-class single-event jumps: `λ≈0.05/yr`, `μ_J≈-0.05` log-return, `σ_J≈0.02`; planner refines specific defaults). The honesty mechanism is the N=64 ±50% Latin hypercube sensitivity bracket — if the gate decision is robust under that bracket, the stipulation is defensible; if it flips, the stipulation is fragile and that is itself the headline finding.
- **`notes/usdt_depeg_calibration.md` documentation discipline:** the document MUST NOT cite Hernandez Cruz 2024 or Wu & Liu 2026 as parameter sources (they aren't). It must say verbatim: "Base triple stipulated from literature-range Merton 1976 defaults for stablecoin-class jumps. NOT calibrated from cited primary data — Hernandez Cruz 2024 and Wu & Liu 2026 do not publish jump-diffusion parameters; cited only as methodological-context references for stablecoin tail-risk discussion. Sensitivity bracket (±50% N=64 Latin hypercube) is the uncertainty mechanism."
- **Sensitivity analysis: 3-parameter Latin hypercube, N=64.** Jointly vary `jump_intensity λ`, `jump_size_mean μ_J`, `jump_size_std σ_J` ±50% around the stipulated base. Compute strip price + gate decision per sample. Locked seed for reproducibility. If the gate decision flips on any cell (literal semantics — even one flip), the result is surfaced as `sensitivity_fragile: true` in `gate_report.json`. Histogram + cell table rendered into the Phase 5 PDF.
- **Calibration applies to condition 4 ONLY.** USDT depeg jump-leg parameters drive only the fourth convex-dominance condition's evidence check (does USDT/USDC basis exhibit jump-class behavior over the panel window?). Conditions 1–3 remain independent of the depeg calibration. Clean separation; no cross-coupling to the DEPEND-01 copula tail diagnostic.
- **`gate_report.json` flagging:** when condition 4 fires on the stipulation alone (no USDT-specific empirical evidence), the gate records `condition_4: {passed: true, evidence: {source: "literature_range_stipulation", base_triple: {lambda, mu_J, sigma_J}, sensitivity_fragile: <bool>, sensitivity_summary: {n_samples: 64, n_flips: <int>, flip_examples: [...]}}}`. Phase 5's report build is required to cite the stipulation assumption + sensitivity result next to the gate result. The `source: "methodological_port"` field name is replaced with `source: "literature_range_stipulation"` to match the corrected framing.

### DEPEND-01 cross-correlogram + copula + vine fallback

- **Cross-correlogram lag domain: event-index lags, ±50 events.** Bowsher-2007-style intensity-based cross-correlogram convention. (Note: this is event-index, not wall-clock — a deliberate divergence from Phase 3's wall-clock-split discipline, justified because the cross-correlogram statistic is well-defined on the event-rank domain even when arrival rates are non-stationary.)
- **Permutation test statistic: max |ρ(h)| over the lag grid.** 1000 permutation reps (locked in PRE_REGISTRATION §Test Statistics). Within-window shuffle of `leg_1` timestamps; recompute cross-correlogram; record max |ρ(h)| over all lags; `p_value` = empirical fraction of perm-max exceeding observed-max. Robust to multiple-comparisons across lags.
- **Copula family menu for BIC comparison: 5 families.** Gaussian + t + Clayton + Frank + Gumbel. Covers elliptical (symmetric tails) + Archimedean (lower-tail / symmetric-no-tail / upper-tail) coverage. BIC-min wins. Vine copula fallback fires only if no single bivariate copula has BIC within 5 units of the best 2D vine pair-copula construction (per `DEPEND-01` "vine fallback only if BIC prefers" — operationalized as Δ_BIC ≥ 5 in favor of vine).
- **`joint_dist.json` schema discipline: mirror Phase 3 `fit_report.json` pattern.** Carries SC-1 metadata header (chainId, contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit, run_id) PLUS the four SC-1-mandated keys (cross_correlogram: {lags, values}; permutation_null: {n_reps, p_value}; empirical_copula: {family, params, bic, all_candidates_bic}; vine_fallback_used: bool). `REQUIRED_JOINT_DIST_KEYS` tuple lives in `analysis/src/abrigo_x402/dependence/copula.py` + sync'd in `scripts/lint_artifacts.py`. `make lint-artifacts` now tracks parquet + `fit_report.json` + `joint_dist.json` + `gate_report.json` + `stress_report.json`.

### Carr–Madan grid + three-way stress test (HEDGE-02 + HEDGE-04)

- **Positivity-check tolerance: relaxed.** Negative implied-density mass < 0.1% of total integrated |q(k)| is acceptable. Implementation: compute total `∫ |q(k)| dk` on the grid; if `∑ q(k)⁻ / ∑ |q(k)| < 0.001`, treat as numerical FFT-truncation noise and proceed. Otherwise escalate (2¹¹ → 2¹²) per SC-3. **PRE-REGISTRATION AMENDMENT REQUIRED:** this 0.1% threshold is a new numeric value not in `notes/PRE_REGISTRATION.md`; per AF-03 discipline, it must be entered into PRE_REGISTRATION.md with a git commit predating any Phase 4 code commit. See `<deferred>` for the amendment task.
- **Fallback after 2¹² fails: abort to `strip_degenerate.json`.** Do NOT silently switch to COS or PROJ methods. Write diagnostic file with `{max_negative_value, total_negative_mass, characteristic_function_decay_rate, recommended_method: "COS"|"PROJ"|"none"}` and stop. Phase 5 reads `strip_degenerate.json` and emits a "strip-not-emittable" note alongside the gate report.
- **Comonotone-scenario construction: Fréchet upper bound (`U_2 = U_1` rank-comonotone).** Textbook strongest-positive-dependence scenario. Computes via shared uniform: `U_1 ~ U(0,1), U_2 = U_1`, push through inverse marginal CDFs. No free parameters; reproducible from the empirical marginals alone without fitting another copula.
- **HEDGE-04 divergence flagging: flag-only at >30%.** When strip prices under {independence, fitted_joint, comonotone} diverge by >30% (spread / mean of the three prices), set `divergence_flag: true` in `stress_report.json`. Phase 5 PDF gets an automatic callout box. The strip still ships; the divergence is itself a documented finding (per HEDGE-04 SC-4 framing: "large divergence between scenarios is itself a finding"). No hard-fail.

### Claude's Discretion

- Hedge CLI subcommand shape (one `hedge` subcommand with `--stage {dependence,gate,strip,stress}` flags, or per-step subcommands `hedge-dependence`, `hedge-gate`, `hedge-strip`, `hedge-stress`).
- Internal compute layout of the four-condition gate module (one file with four functions vs four condition-specific files).
- How rate-comonotone marginal CDFs are computed (rank transform vs PIT through fitted parametric marginals).
- Latin hypercube library choice (`scipy.stats.qmc.LatinHypercube` recommended).
- Quarto chunk caching / freeze policy.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Pre-registration (locked parameters — NEVER post-hoc revise)
- `notes/PRE_REGISTRATION.md` §Decision Rules — HEDGE-05 firing conditions (a)(b)(c); USDT condition-4 framing
- `notes/PRE_REGISTRATION.md` §Test Statistics — cross-correlogram + 1000-rep permutation null; empirical copula + vine BIC fallback
- `notes/PRE_REGISTRATION.md` §Acceptance Regions — four-criterion gate (consumed by HEDGE-01 condition 3 evidence check)
- `notes/PRE_REGISTRATION.md` §Q-9 Fallback — V3-only primary panel (Iter-1 ICHI), V3+V4+Broker switch trigger
- `notes/PRE_REGISTRATION.md` §Pre-Registration Discipline — AF-03 no-post-hoc-revision rule (gates the 0.1% positivity tolerance amendment)

### Pitfalls (architectural risks)
- `.planning/research/PITFALLS.md` §4 — boundary-correct LR (consumed via Phase 3 `fit_report.json :: lr_test`)
- `.planning/research/PITFALLS.md` §5 — cross-leg dependence assumed independent when self-excitation is bivariate (mandates full off-diagonal Hawkes adjacency, already produced in Phase 3)
- `.planning/research/PITFALLS.md` §1 — substrate-too-young / sample-thinness discipline (cKES/USDT 30-day ~4,440 swaps anchor; Steer cCOP/USDT ~580–625/30d may STRADDLE)

### Phase 3 source-of-truth (upstream substrate Phase 4 consumes)
- `.planning/phases/03-dgp-estimation-l4-with-boundary-correct-lr-test/03-CONTEXT.md` — Phase 3 user decisions; STRADDLE expectation on real ICHI panel
- `.planning/phases/03-dgp-estimation-l4-with-boundary-correct-lr-test/03-VERIFICATION.md` — Phase 3 verifier sign-off (`status: passed`)
- `analysis/src/abrigo_x402/dgp/orchestrator.py` — `REQUIRED_FIT_REPORT_KEYS` tuple Phase 4 reads from; canonical-LL contract (Hawkes/NHPP loglik sources)
- `analysis/src/abrigo_x402/dgp/lr_test.py` — exports `_hawkes_loglik_vectorized` + `_nhpp_pointprocess_loglik` (canonical sources Phase 4 must use, not raw `tick.score()` / `VAR.llf`)
- `data/fits/ichi/<run_id>/fit_report.json` — Phase 4 input; `gate_passes`, `gate_criteria`, `hawkes_mv_params`, `branching_ratio_ci`, `baseline_stationarity_check` all consumed
- `data/fits/ichi/<run_id>/residuals.parquet` — Phase 4 reads rescaled-time residuals for empirical-copula PIT marginals
- `scripts/lint_artifacts.py` — Phase 4 extends `FIT_REPORT_SC1_KEYS` pattern with `JOINT_DIST_REQUIRED_KEYS`, `GATE_REPORT_REQUIRED_KEYS`, `STRESS_REPORT_REQUIRED_KEYS`

### Phase 0–2 governance carried forward
- `.planning/phases/00-candidate-eligibility-pre-registration/00-CONTEXT.md` — Q-7 floor, REPRO-03 two-tier semantics (consumed by HEDGE-05 firing condition (a))
- `notes/PHASE_0_GATE.md` — ICHI five-check PASS; Steer-Iter2 STRADDLE expectation; HEDGE-05 firing-condition-(a) primary trigger for Steer
- `notes/Q9_DECISION.md` — Iter-2 (Steer) V3-only primary panel decision (relevant for Phase 4 Iter-2 re-run)
- `.planning/research/CANDIDATES.md` §6 Q6b + §7 thinness-retraction audit — Steer Iter-2 cost-leg STRADDLE is the leading firing condition

### Project-level
- `.planning/PROJECT.md` — free-tier-only; USDT (not USDC) tail-risk framing; cost-leg modeled
- `./CLAUDE.md` — USDT/USDC framing non-negotiable; convex-perpetual-dominates-linear-hedge rationale
- `.planning/REQUIREMENTS.md` — DEPEND-01..DEPEND-02, HEDGE-01..HEDGE-05 acceptance criteria
- `.planning/ROADMAP.md` §Phase 4 — six verbatim SCs

### Sibling-repo cost model (the source theory)
- `../abrigo-analytics/notes/SOMNIA_DRAFT.md` §FUNCTIONAL FORM — four convex-dominance conditions; condition 4 USDT reparameterization rationale; Carr–Madan replicating-strip derivation
- `../abrigo-analytics/notes/SOMNIA_DRAFT.md` §ARRIVAL PROCESS — DGP baseline (already operationalized in Phase 3)
- `../abrigo-analytics/notes/SOMNIA_DRAFT.md` §TAIL RISK / DEPEG — USDC historical depeg parameter reference (used as Hernandez Cruz 2024 methodological-port base for HEDGE-03)

### v2.0 polymorphism notes (don't bake v1.0-only assumptions)
- `notes/ROADMAP-EXTENSIONS.md` — v2.0 streaming-tokenization extension; "Phase 4 Carr–Madan replicating-strip module — design the API for an arbitrary payoff f(S_T), not just LP-fee revenue. v2.0 will pass a stream-PV payoff into the same strip generator."

### Library / tooling expectations
- `analysis/pyproject.toml` — current locked stack (tick 0.8.0.2, statsmodels 0.14.6, polars 1.41.0, numpy 2.4.6, scipy 1.17.1, matplotlib, numpydoc); Phase 4 adds: `copulae` (5-family copula fits + BIC), optionally `pyvinecopulib` (vine fallback), `quarto` system dep + `jupyter` for Quarto chunk execution
- `analysis/src/abrigo_x402/cli.py` — Phase 4 extends with `hedge` subcommand(s)
- `Makefile` — Phase 4 extends `lint-artifacts` target and adds `render-null-result-pdf` + `render-strip-diagnostic` targets

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets (from Phase 3)

- **`analysis/src/abrigo_x402/dgp/orchestrator.py :: REQUIRED_FIT_REPORT_KEYS`** — exact tuple Phase 4 reads from `fit_report.json`. Pattern Phase 4 mirrors for `JOINT_DIST_REQUIRED_KEYS`, `GATE_REPORT_REQUIRED_KEYS`, `STRESS_REPORT_REQUIRED_KEYS`.
- **`analysis/src/abrigo_x402/dgp/lr_test.py :: _hawkes_loglik_vectorized` + `_nhpp_pointprocess_loglik`** — canonical Hawkes / NHPP log-likelihood functions Phase 4 imports for any condition-3 evidence recomputation (does NOT call `tick.score()` directly).
- **`analysis/src/abrigo_x402/provenance.py`** — `with_header` / `assert_has_header` API that Phase 4 reuses verbatim for `joint_dist.json`, `gate_report.json`, `stress_report.json`, `strip.json`, `strip_degenerate.json`, `stress_report.json` provenance metadata header.
- **`analysis/tests/conftest.py`** — extended Phase 2 + Phase 3 conftest already has `panel_fixture` + synthetic Hawkes/NHPP fixture generators via `SimuHawkesExpKernels`. Phase 4 extends with `joint_dist_fixture`, `gate_report_fixture`, `null_result_fixture_triplet` (three subdirs under `analysis/tests/fixtures/hedge_05_*/`).
- **`scripts/lint_artifacts.py`** — dual-track parquet + `fit_report.json` lint already in place. Phase 4 extends to a five-track lint: parquet + fit_report + joint_dist + gate_report + stress_report.
- **`Makefile :: lint-artifacts`** — target already exists; Phase 4 extends.
- **Locked-seed synthetic fixtures (`analysis/tests/fixtures/synthetic_hawkes_eta_05.parquet` + `synthetic_nhpp_baseline_only.parquet`)** — Phase 4's HEDGE-05 null_lr fixture and the condition-3 sensitivity test reuse these.

### Established Patterns (Phase 2 + Phase 3)

- **`<X>_REQUIRED_KEYS` + `scripts/lint_artifacts.py` extension + `make lint-artifacts` track** — established Phase 2 → Phase 3 pattern for every new JSON artifact. Phase 4 follows for joint_dist + gate_report + stress_report + strip.
- **Thread-pinning before first `import numpy`** (Phase 3 Pattern I) — applies to any Phase 4 byte-identity test (e.g., `test_byte_identical_stress_report`).
- **Canonical-LL contract** (Phase 3 Pattern F) — Phase 4 reads `hawkes_mv_params :: loglik` from `fit_report.json` (the canonical Phase 3 source), never the `loglik_in_sample_raw` provenance field.
- **Acceptance grid as commands+codes+verdicts** (Phase 3 Pattern K) — Phase 4 produces `04-VERIFICATION-pre.md` in the same format covering DEPEND-01/02 + HEDGE-01/02/03/04/05 + ROADMAP SC-1..6.
- **2-way review-trail enforcement** — pre-commit hook requires paired `.planning/_reviews/04-NN-PLAN_{reality_checker,code_reviewer}.md` files with `## VERDICT` headers per PLAN.md.
- **TDD discipline** — RED then GREEN per task, atomic per-task commits.

### Integration Points

- **`fit_report.json` consumption** — Phase 4 reads from `data/fits/ichi/<run_id>/`. The `<run_id>` is derived in Phase 3; Phase 4 uses the same run directory for its own writes (no new run_id).
- **`reports/ichi.pdf`** — currently does not exist. Phase 4 creates it via either (a) Quarto render of the null-result template (HEDGE-05 fires) OR (b) Phase 5 takes over in the positive-result case. Phase 4 owns the null-result path only.
- **`notes/usdt_depeg_calibration.md`** — currently does not exist. Phase 4 creates it as part of HEDGE-03 with the methodological-port assumption explicit + Latin hypercube sensitivity results recorded.

</code_context>

<specifics>
## Specific Ideas

- The Phase 3 STRADDLE expectation on the real ICHI panel means HEDGE-05 firing is the likely headline output, not a corner case. Phase 4 must wire `reports/ichi.pdf` rendering for the null-result path as a first-class deliverable — no "TODO: handle null case" stub.
- HEDGE-03 calibration deliberately chooses the most-honest path (literature-range stipulation + bounded sensitivity) over the most-impressive path (USDT-specific primary calibration we don't have, and as Phase 4 RESEARCH discovered, the cited reference papers don't actually publish jump-diffusion parameters either). The transparency is itself a methodological contribution; the bounded sensitivity analysis is the evidence the stipulation doesn't matter materially.
- The 0.1% positivity tolerance for the Carr–Madan grid was a deliberate divergence from the strict-zero default to avoid spurious aborts on tiny FFT-truncation artifacts — but it carries an AF-03 pre-registration amendment obligation that must be discharged before Phase 4 code commits.

</specifics>

<deferred>
## Deferred Ideas

- **PRE-REGISTRATION AMENDMENT (must be discharged BEFORE Phase 4 execute-phase):** Add a `notes/PRE_REGISTRATION.md` entry locking the 0.1% positivity tolerance for the Carr–Madan grid. Per AF-03 discipline, the amendment commit must predate any `analysis/src/abrigo_x402/hedge/*` commit. Suggested location: §Test Statistics, new sub-section "Carr–Madan Grid Numerical Tolerances." Planner: include this as the FIRST task of Plan 04-00 (or a Plan 04-pre).
- **Hedge CLI subcommand shape** — one `hedge` subcommand with `--stage` flag vs four separate subcommands. Claude's Discretion; planner picks.
- **Switch to COS or PROJ method** — currently locked to abort-only after 2¹² failure. Reconsider in v2.0 if real-data jump-diffusion characteristic functions consistently defeat Carr–Madan FFT inversion.
- **USDT-specific primary calibration source** — if a future paper (Wu & Liu 2026 extension? on-chain USDT depeg event in 2026?) provides USDT-specific Merton/Kou parameters, the methodological-port assumption can be replaced. Documented at decision time in `notes/usdt_depeg_calibration.md`. Not in Phase 4 scope.
- **2D vine vs single-bivariate-copula formal equivalence** — in 2D the vine pair-copula construction reduces to a single bivariate copula plus uniform marginals. The "vine fallback only if BIC prefers" clause is therefore mostly defensive scaffolding for future >2-dimensional generalizations. Locked semantics: ΔBIC ≥ 5 in favor of vine triggers fallback; planner can decide if a meaningful vine construction exists in 2D worth implementing.
- **Cross-leg copula tail dependence coupled to HEDGE-03 calibration** — explicitly rejected per Area 2 Q3: HEDGE-03 calibration applies to condition 4 only, never feeds into the DEPEND-01 copula tail diagnostic.
- **Hard-fail on >100% stress-test divergence (two-tier threshold)** — rejected; flag-only at >30% is the single-threshold policy. HEDGE-04 framing of divergence as a finding (not a failure) is preserved.
- **Streaming-tokenization Phase 4 generalization** — v2.0 milestone per `notes/ROADMAP-EXTENSIONS.md`. Phase 4's Carr–Madan replicating-strip module API should accept an arbitrary payoff `f(S_T)`, not just LP-fee revenue, to keep the v2.0 stream-PV payoff drop-in.
- **Power-law Hawkes kernel** (DGP-V2-01), **bootstrap CIs on all DGP params** (DGP-V2-02), **structural-break test** (DGP-V2-03) — all v2.0 per Phase 3 deferred list; Phase 4 does not re-litigate.

</deferred>

---

*Phase: 04-cross-leg-dependence-l5-falsification-carr-madan-strip-l6*
*Context gathered: 2026-05-27*
