# Phase 4: Cross-Leg Dependence (L5) + Falsification & Carr–Madan Strip (L6) - Research

**Researched:** 2026-05-27
**Domain:** Multivariate copula inference, four-condition convex-dominance falsification gate (USDT-reparameterized), Carr–Madan static replication on a convergence-tested FFT grid, three-way joint-distribution stress test, HEDGE-05 null-result Quarto PDF pipeline.
**Confidence:** HIGH on substrate consumed (Phase 3 fit_report.json schema, residuals.parquet shape, provenance + lint patterns), HIGH on the locked-decision constraints from CONTEXT.md, HIGH on library + version availability (copulae 0.8.0, pyvinecopulib 0.7.6, scipy 1.17 LatinHypercube), MEDIUM on Carr–Madan FFT implementation choices (textbook formula + 1706.05935 truncation guidance; no canonical Python reference implementation surfaced), LOW-MEDIUM on the HEDGE-03 calibration "port" (the cited primary sources do NOT publish jump-diffusion parameters — this is a structural research gap that the plan must handle explicitly).

## Summary

Phase 4 is a three-deliverable phase wired entirely on top of Phase 3's `data/fits/ichi/<run_id>/{fit_report.json, residuals.parquet}` substrate. Every architectural pattern is already established (PANEL-02 header → SC-1 schema → `lint_artifacts.py` extension; orchestrator-as-single-entry; canonical-LL contract; thread-pinning for byte-identity; AF-XX pre-commit lint gates). The novelty is statistical (bivariate cross-correlogram + permutation null; 5-family copula BIC with vine fallback; four-condition convex-dominance gate with USDT/USDC basis reparameterization; FFT-based Carr–Madan strip; Fréchet-upper-bound comonotone scenario; Latin hypercube sensitivity) and procedural (HEDGE-05 firing wiring; Quarto null-result PDF rendering with dual signature markers; PRE_REGISTRATION amendment for the 0.1% positivity tolerance).

CONTEXT.md has locked every high-level "what" decision — there are no library-shopping or design questions left for the planner to ask the user. Planner's job is to:
1. Sequence the work as one Wave-0 scaffold + one Wave-1 amendment + ~6 Wave-1 implementation plans + one Wave-2 orchestrator + one Wave-3 acceptance, mirroring Phase 3's plan shape (00 scaffold → 01..06 modules → 07 orchestrator → 08 acceptance).
2. Treat the PRE_REGISTRATION 0.1%-tolerance amendment as a **blocking** prerequisite — its commit hash must predate any `analysis/src/abrigo_x402/hedge/*` commit per AF-03 discipline. No precedent for in-band amendment exists in the repo; Phase 4 sets it.
3. Surface a structural research gap to the user: the cited "primary source" for HEDGE-03 (Hernandez Cruz 2024, arxiv 2407.11716) does NOT actually publish Merton/Kou jump-diffusion parameters — it is a transparency/MCI paper on USDC liquidity around SVB. Wu & Liu 2026 (arxiv 2602.18820) uses QVAR, not jump-diffusion. The "methodological port" therefore requires stipulating Merton/Kou parameters from raw March-2023 USDC tick data (or accepting a defensibly stipulated triple `(λ, μ_J, σ_J)` with explicit provenance to a non-jump-diffusion source). The Latin hypercube ±50% sensitivity sweep CONTEXT.md locks is a fully adequate honesty-of-port mitigation, but the planner should NOT use the phrase "port from Hernandez Cruz 2024" without first reading the paper and choosing a defensible stipulated triple.

**Primary recommendation:** Adopt `copulae==0.8.0` for the 5-family BIC menu (HIGH library compatibility, single-source dependency, Python 3.13 + numpy 2.x verified), add `pyvinecopulib==0.7.6` ONLY if Wave-1 empirical runs trigger the ΔBIC≥5 vine fallback (defer install to a follow-up plan to avoid AF-12 silent re-scope from an unused C++ binary dependency), pin Quarto via system package + add `jupyter` to the analysis dev deps, and structure the Carr–Madan strip module around a `payoff: Callable[[np.ndarray], np.ndarray]` parameter from day one per `notes/ROADMAP-EXTENSIONS.md` v2.0 streaming-tokenization polymorphism guidance.

## User Constraints (from CONTEXT.md)

### Locked Decisions

**HEDGE-05 firing wiring + PDF toolchain:**
- Firing decision lives in a dedicated `analysis/src/abrigo_x402/hedge/null_result.py` module. Single entry point. Reads `fit_report.json` + `gate_report.json` + (optionally) the per-candidate `notes/<protocol>_cost_leg_bound.md`, decides which of the three firing conditions tripped — (a) Phase-0 cost-leg gate fail, (b) DGP-03 LR-indistinguishable at α=0.05, (c) HEDGE-01 zero convex-dominance conditions — and either invokes the strip pipeline (no firing) or renders the null-result PDF (firing). Mirrors Phase 3's `orchestrator.py` single-entry pattern. The hedge CLI subcommand calls it.
- PDF rendering toolchain: **Quarto** (`.qmd` template with embedded Python code blocks, renders to PDF via LaTeX). Adds a TeX dependency to the dev environment. Supports cross-references and citations natively → plays cleanly with `notes/PRE_REGISTRATION.md` citations in Phase 5.
- One template, three context-block branches: `reports/_templates/null_result.qmd` carries a single signature header + a switch on the firing condition that swaps in the relevant evidence block. Same template is reused by Phase 5 for the positive-result case as a sub-template. One file to maintain.
- PDF signature for grep-based detection: **dual**. Top of every null-result PDF carries (a) visible heading `# HEDGE-05 NULL RESULT — <firing-condition>` and (b) a machine-readable marker `HEDGE05-NULL-RESULT-V1` (in PDF footer or metadata field). `tests/test_null_result_template.py` greps both via `pdftotext` so it survives font/PDF library quirks.
- Three fixture sets at `analysis/tests/fixtures/hedge_05_{null_cost,null_lr,null_convex}/`, each a synthetic `fit_report.json` + `gate_report.json` + `cost_leg_bound.md` triplet that forces exactly one firing condition.

**USDT-depeg jump-leg calibration (HEDGE-03):**
- Primary calibration source: methodological port from USDC. Use Hernandez Cruz 2024 (USDC, March-2023 depeg) Merton/Kou parameters as the base calibration. Port is documented explicitly in `notes/usdt_depeg_calibration.md` — never silently substituted.
- Sensitivity analysis: 3-parameter Latin hypercube, N=64. Jointly vary `jump_intensity λ`, `jump_size_mean μ_J`, `jump_size_std σ_J` ±50% around base. Compute strip price + gate decision per sample. Locked seed for reproducibility. If the gate decision flips on any cell, the result is surfaced as `sensitivity_fragile: true` in `gate_report.json`.
- Calibration applies to condition 4 ONLY. USDT depeg jump-leg parameters drive only the fourth convex-dominance condition's evidence check. Conditions 1–3 remain independent.
- `gate_report.json` flagging: when condition 4 fires solely on the port (no USDT-specific evidence), the gate records `condition_4: {passed: true, evidence: {source: "methodological_port", base_paper: "Hernandez Cruz 2024", sensitivity_fragile: <bool>, sensitivity_summary: {...}}}`.

**DEPEND-01 cross-correlogram + copula + vine fallback:**
- Cross-correlogram lag domain: event-index lags, ±50 events. Bowsher-2007-style intensity-based cross-correlogram convention. Deliberate divergence from Phase 3's wall-clock-split discipline — justified because the statistic is well-defined on the event-rank domain even when arrival rates are non-stationary.
- Permutation test statistic: `max |ρ(h)|` over the lag grid. 1000 permutation reps (locked in PRE_REGISTRATION §Test Statistics). Within-window shuffle of `leg_1` timestamps; recompute cross-correlogram; record `max |ρ(h)|` over all lags; `p_value` = empirical fraction of perm-max exceeding observed-max.
- Copula family menu for BIC comparison: 5 families. Gaussian + t + Clayton + Frank + Gumbel. BIC-min wins. Vine copula fallback fires only if no single bivariate copula has BIC within 5 units of the best 2D vine pair-copula construction (ΔBIC ≥ 5 in favor of vine).
- `joint_dist.json` schema: SC-1 metadata header (chainId, contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit, run_id) PLUS the four SC-1-mandated keys (`cross_correlogram: {lags, values}`; `permutation_null: {n_reps, p_value}`; `empirical_copula: {family, params, bic, all_candidates_bic}`; `vine_fallback_used: bool`). `REQUIRED_JOINT_DIST_KEYS` tuple lives in `analysis/src/abrigo_x402/dependence/copula.py` + sync'd in `scripts/lint_artifacts.py`. `make lint-artifacts` now tracks parquet + `fit_report.json` + `joint_dist.json` + `gate_report.json` + `stress_report.json`.

**Carr–Madan grid + three-way stress test (HEDGE-02 + HEDGE-04):**
- Positivity-check tolerance: **relaxed**. Negative implied-density mass < 0.1% of total integrated `|q(k)|` is acceptable. Implementation: compute total `∫ |q(k)| dk` on the grid; if `∑ q(k)⁻ / ∑ |q(k)| < 0.001`, treat as numerical FFT-truncation noise and proceed. Otherwise escalate (2¹¹ → 2¹²) per SC-3. **PRE-REGISTRATION AMENDMENT REQUIRED** — 0.1% is a new numeric value not in `notes/PRE_REGISTRATION.md`.
- Fallback after 2¹² fails: abort to `strip_degenerate.json`. Do NOT silently switch to COS or PROJ methods. Write diagnostic file with `{max_negative_value, total_negative_mass, characteristic_function_decay_rate, recommended_method: "COS"|"PROJ"|"none"}` and stop.
- Comonotone-scenario construction: **Fréchet upper bound** (`U_2 = U_1` rank-comonotone). Computes via shared uniform: `U_1 ~ U(0,1), U_2 = U_1`, push through inverse marginal CDFs. No free parameters; reproducible from the empirical marginals alone without fitting another copula.
- HEDGE-04 divergence flagging: **flag-only at >30%**. When strip prices under {independence, fitted_joint, comonotone} diverge by >30% (spread / mean of the three prices), set `divergence_flag: true` in `stress_report.json`. No hard-fail.

### Claude's Discretion

- Hedge CLI subcommand shape (one `hedge` subcommand with `--stage {dependence,gate,strip,stress}` flags, OR per-step subcommands `hedge-dependence`, `hedge-gate`, `hedge-strip`, `hedge-stress`).
- Internal compute layout of the four-condition gate module (one file with four functions vs four condition-specific files).
- How rate-comonotone marginal CDFs are computed (rank transform vs PIT through fitted parametric marginals).
- Latin hypercube library choice (`scipy.stats.qmc.LatinHypercube` recommended).
- Quarto chunk caching / freeze policy.

### Deferred Ideas (OUT OF SCOPE)

- **PRE-REGISTRATION AMENDMENT (MUST be discharged BEFORE Phase 4 execute-phase):** Add a `notes/PRE_REGISTRATION.md` entry locking the 0.1% positivity tolerance for the Carr–Madan grid. Per AF-03, amendment commit MUST predate any `analysis/src/abrigo_x402/hedge/*` commit. Suggested location: §Test Statistics, new sub-section "Carr–Madan Grid Numerical Tolerances." Planner: include this as the FIRST task of Plan 04-00 (or a Plan 04-pre).
- Hedge CLI subcommand shape (one `hedge` vs four separate) — Claude's Discretion; planner picks.
- Switch to COS or PROJ method after 2¹² failure — currently locked to abort-only. Reconsider in v2.0.
- USDT-specific primary calibration source — if a future paper provides USDT-specific parameters, the port assumption can be replaced. Not in Phase 4 scope.
- 2D vine vs single-bivariate-copula formal equivalence — in 2D the vine reduces to a bivariate + uniform marginals. "Vine fallback only if BIC prefers" is mostly defensive scaffolding; planner can decide if a meaningful vine construction is worth implementing.
- Cross-leg copula tail dependence coupled to HEDGE-03 calibration — explicitly rejected (HEDGE-03 calibration applies to condition 4 only).
- Hard-fail on >100% stress-test divergence (two-tier threshold) — rejected; flag-only at >30% is the single-threshold policy.
- Streaming-tokenization Phase 4 generalization — v2.0 milestone. **Phase 4's Carr–Madan replicating-strip module API SHOULD accept an arbitrary payoff `f(S_T)`, not just LP-fee revenue, to keep the v2.0 stream-PV payoff drop-in.**
- Power-law Hawkes kernel (DGP-V2-01), bootstrap CIs on all DGP params (DGP-V2-02), structural-break test (DGP-V2-03) — all v2.0; Phase 4 does not re-litigate.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEPEND-01 | Pipeline must compute cross-correlogram between `dK_revenue(t)` and `dK_cost(t)` arrivals + permutation null; report empirical copula per FEATURES.md TS-09; vine copula fallback only if BIC prefers. | `copulae==0.8.0` provides Gaussian + t + Clayton + Frank + Gumbel families with `.fit()` + `.log_lik()` for BIC computation; `pyvinecopulib==0.7.6` (May 2026) provides vine fallback with Py3.13 wheels. Bowsher-2007 event-index lag-domain (locked CONTEXT.md decision) implementable via numpy broadcasting against `residuals.parquet :: rescaled_dt` per leg. Within-window permutation: numpy `default_rng(seed).permutation(leg_1_times)` 1000-rep loop; `max |ρ(h)|` statistic. |
| DEPEND-02 | Any "joint" cashflow claim in the report must be backed by a cross-correlogram + permutation null + copula fit; a single bivariate scatter is insufficient evidence. | `JOINT_DIST_REQUIRED_KEYS` schema enforced via lint-artifacts extension (Phase 3 Pattern G applied to Phase 4 artifact); REPORT-level lint in Phase 5 reads `joint_dist.json` existence + schema validity. |
| HEDGE-01 | Pipeline must run all four convex-dominance conditions from SOMNIA_DRAFT.md §FUNCTIONAL FORM against the joint cashflow before any Carr–Madan strip is computed: (1) vol-of-vol > 0, (2) positive skew / fat tails, (3) Hawkes self-excitation, (4) USDT depeg + USDT/USDC basis jump. At least one condition must hold. | Conditions implemented as `analysis/src/abrigo_x402/hedge/falsification.py` functions (one per condition or four files — Claude's Discretion). Condition 3 reuses `fit_report.json :: hawkes_mv_params :: branching_ratio` + `:: gate_criteria.eta_floor_met` from Phase 3 (no re-fit). Conditions 1, 2 reuse `residuals.parquet` per-leg moments. Condition 4 consumes `notes/usdt_depeg_calibration.md` triple `(λ, μ_J, σ_J)` + Latin hypercube N=64 sensitivity. SC-2 grep gate: `grep -i "usdc" analysis/src/abrigo_x402/hedge/falsification.py` returns ONLY comment/historical-reference hits. |
| HEDGE-02 | Carr–Madan strip implementation must use a convergence-tested grid (start 2^11 points, escalate to 2^12 if positivity check fails); implied density must be checked for negativity before strip emission; switch to COS or PROJ method when standard FFT-truncation produces negatives. | `analysis/src/abrigo_x402/hedge/carr_madan_strip.py` runs `numpy.fft.fft` on characteristic function of fitted joint cashflow distribution; positivity check uses `q(k) = np.real(np.fft.ifft(...))` with the 0.1% tolerance amendment (CONTEXT.md locked). 2¹¹ → 2¹² escalation per SC-3. Abort-to-`strip_degenerate.json` rather than silent COS/PROJ swap (CONTEXT.md locked). |
| HEDGE-03 | USDT depeg jump leg must be calibrated on USDT-specific depeg history (Merton or Kou jump-diffusion), not by porting USDC-anchored parameters; if a USDT-specific source is unavailable, the port must be explicitly documented as a methodological assumption with bounded sensitivity. | **CRITICAL RESEARCH GAP** — verified that Hernandez Cruz 2024 (arxiv 2407.11716) is a transparency/MCI paper that does NOT publish Merton/Kou parameters, and Wu & Liu 2026 (arxiv 2602.18820) uses QVAR not jump-diffusion. The "port" therefore requires stipulating `(λ, μ_J, σ_J)` from a defensible derivation (e.g., from raw March-2023 USDC tick data) rather than copying published parameters. `notes/usdt_depeg_calibration.md` MUST document this gap explicitly. Latin hypercube ±50% sensitivity sweep (locked) is an adequate honesty-of-port mitigation. |
| HEDGE-04 | Strip-price stress test must run three-way joint-distribution scenarios (independence / fitted-joint / comonotone) and report all three; large divergence between scenarios is itself a finding. | `analysis/src/abrigo_x402/hedge/stress_test.py`. Independence: marginal CDF of leg_0 ⊗ marginal CDF of leg_1, inverse-transform draws. Fitted-joint: empirical copula sample (`copulae.fit().random(N)`). Comonotone: shared uniform `U_1 ~ U(0,1), U_2 = U_1`, inverse-transform per leg. Locked Fréchet upper bound (CONTEXT.md). >30% spread/mean flagging via `divergence_flag` field in `stress_report.json`. |
| HEDGE-05 | Null-result emission template must fire when any of: (a) Phase-0 cost-leg gate fails for a candidate, (b) NHPP-vs-Hawkes is indistinguishable at conventional α per DGP-03, (c) no convex-dominance condition holds per HEDGE-01. In each case, deliverable PDF must document the null with disqualifying evidence. | `analysis/src/abrigo_x402/hedge/null_result.py` orchestrator (single-entry per CONTEXT.md). Reads `fit_report.json :: dgp_indistinguishable` flag + `gate_report.json :: any_condition_passed` + optionally `notes/<protocol>_cost_leg_bound.md`. Quarto template at `reports/_templates/null_result.qmd` rendered via `quarto render`. Dual signature markers: visible H1 + machine-readable `HEDGE05-NULL-RESULT-V1` in PDF metadata. Three fixture triplets in `analysis/tests/fixtures/hedge_05_{null_cost,null_lr,null_convex}/` each forcing one firing condition; `pytest tests/test_null_result_template.py` greps the rendered PDF via `pdftotext` for both signature markers. |

## Standard Stack

### Core (additions over Phase 3 baseline)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `copulae` | 0.8.0 | Gaussian + Student-t + Clayton + Frank + Gumbel copula fits with `.fit()`, `.log_lik()`, `.random()` API for BIC ranking + dependence-scenario sampling. | "Second most popular copula package in Python" per its README; covers exactly the 5 families CONTEXT.md locked; verified Python 3.13 + numpy 2.x support; pure-Python install (no C++ binary risk). |
| `pyvinecopulib` | 0.7.6 | Vine copula fallback (fires only if `ΔBIC ≥ 5` in favor of vine vs the BIC-min bivariate). Released 2026-05-07 with Python 3.9–3.14 wheels on Linux/macOS/Windows. | Header-only C++ via nanobind bindings; the canonical vine implementation. Defer to a follow-up plan or guard install behind a feature flag — adding a C++ binary dependency for a near-defensive fallback in 2D is AF-12-adjacent (silent re-scope risk) unless the empirical ΔBIC actually warrants it. |
| `quarto` (system) | ≥1.6 | PDF rendering of `reports/_templates/null_result.qmd` via embedded Python code chunks → LaTeX → PDF. CLI invocation only; no Python binding. | CONTEXT.md locked. Quarto handles citations + cross-references natively, plays cleanly with `notes/PRE_REGISTRATION.md` citations in Phase 5. Install via system package manager (apt / pacman / dnf) or `quarto install tinytex` for the bundled TeX. |
| `jupyter` (dev) | latest | Required by Quarto to execute Python code chunks inside `.qmd`. | Per Quarto docs: "if you have Python and the jupyter package installed then you have all you need to render documents that contain embedded Python code." Add to `analysis/pyproject.toml [dependency-groups] dev`. |
| `texlive-luatex` (system) OR Quarto's bundled TinyTeX | latest | LaTeX engine. Quarto defaults to LuaTeX for PDF output; `quarto install tinytex` is the lowest-friction option (`~250MB` self-managed). | TinyTeX is officially recommended by Quarto when the system has no TeX. For CI determinism, prefer pinning system `texlive-luatex` to a distro version. |

### Already in stack (consumed by Phase 4)

| Library | Version | Purpose | Phase 4 Use |
|---------|---------|---------|-------------|
| `numpy` | 2.4.6 | FFT (`np.fft.fft`/`np.fft.ifft`) for Carr–Madan; broadcasting for cross-correlogram; `default_rng(seed)` for reproducible permutations + Latin hypercube. | Carr–Madan FFT on 2¹¹/2¹² grids; permutation null for DEPEND-01. |
| `scipy` | 1.17.1 | `scipy.stats.qmc.LatinHypercube` for 3-parameter HEDGE-03 sensitivity; `scipy.stats.kendalltau` / `pearsonr` for cross-correlogram; `scipy.fft` as drop-in alternative if `numpy.fft` precision proves insufficient. | LHS sampling; correlation statistics. |
| `polars` | 1.41.0 | Read `residuals.parquet` from Phase 3; write fixture parquets for `hedge_05_*` triplets. | Substrate I/O. |
| `tick` | 0.8.0.2 | `SimuHawkesExpKernels` for synthetic-fixture generation (null_convex triplet: zero off-diagonal adjacency forces condition 3 to fail). | Test-fixture-only; not exercised in production fit path. |
| `statsmodels` | 0.14.6 | Holds Phase 3 NHPP fits; not invoked anew in Phase 4. | (substrate) |
| `pydantic` | ≥2 | (optional) Schema validation for `joint_dist.json` / `gate_report.json` / `stress_report.json` / `strip.json` / `strip_degenerate.json` if planner chooses dataclass-with-validator over plain dict. | Discretion. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `copulae==0.8.0` | `copulas==0.14.1` (DataCebo, BUSL-1.1 licence) | DataCebo's package is BUSL-licensed (production use restrictions); `copulae` is unrestricted. `copulas` is built for synthetic-data generation, not BIC-ranked dependence inference. Stick with `copulae`. |
| `copulae==0.8.0` | `statsmodels.distributions.copula` | statsmodels 0.14.6 provides only Gaussian, Student-t, and a few Archimedean (Clayton, Frank, Gumbel) but the API surface for BIC ranking is hand-rolled (no `.bic()` method). Manual BIC = `-2*log_lik + k*log(n)` is 2 lines but introduces three calling conventions vs `copulae`'s one. Not worth the friction for 5 families. |
| `pyvinecopulib==0.7.6` | Roll a 2D vine pair-copula manually | 2D vine reduces to a single bivariate + uniform marginals (per Deferred Ideas note). Rolling it is 30 lines but requires re-implementing 5 pair-copula CDFs/PDFs that `pyvinecopulib` already vectorizes. Use `pyvinecopulib` only if BIC actually prefers vine; otherwise the dependency is dead weight. |
| Quarto | `nbconvert --to pdf` (Jupyter native) | nbconvert produces PDF via LaTeX too, but no native cross-references / citations / templating. CONTEXT.md locked Quarto. |
| `numpy.fft.fft` | `scipy.fft.fft` | scipy.fft uses pocketfft (same backend), with bit-better precision controls. Either works; `numpy.fft` keeps the Phase 4 dep surface smaller. |
| `scipy.stats.qmc.LatinHypercube` | `pyDOE2`, hand-rolled stratified sampling | scipy.stats.qmc is in the locked scipy 1.17.1; pyDOE2 adds a dep for no benefit. CONTEXT.md recommends scipy.stats.qmc. |

**Installation (additions to analysis/pyproject.toml):**

```toml
[project]
dependencies = [
  # ... existing pins ...
  "copulae==0.8.0",  # DEPEND-01 5-family BIC + dependence sampling
]

[dependency-groups]
dev = [
  # ... existing dev pins ...
  "jupyter",  # required by Quarto Python code chunks
]

# pyvinecopulib==0.7.6 deferred — install in a follow-up plan ONLY IF
# Wave-1 empirical fit triggers the ΔBIC>=5 vine fallback.
```

**System dependency** (NOT pip-installable):

```bash
# Ubuntu / Debian
sudo apt-get install quarto texlive-luatex

# Arch
sudo pacman -S quarto texlive-luatex texlive-latexextra

# Alternative (cross-platform, self-managed by Quarto):
quarto install tinytex
```

**Version verification commands** (planner should run before pinning into Plan 04-00):

```bash
# Confirm copulae current version
pip index versions copulae  # or: pip show copulae
# Confirm pyvinecopulib current version + Python 3.13 wheel
pip index versions pyvinecopulib
# Confirm Quarto installed
quarto --version
# Confirm LaTeX engine
which lualatex && lualatex --version
```

## Architecture Patterns

### Recommended Project Structure

```
analysis/src/abrigo_x402/
├── dependence/
│   ├── __init__.py
│   ├── cross_correlogram.py    # Bowsher-2007 event-index lag-domain ρ(h)
│   ├── permutation_null.py     # 1000-rep within-window shuffle of leg_1 timestamps; max|ρ(h)|
│   └── copula.py               # 5-family BIC ranking + vine fallback gate
│                               # + REQUIRED_JOINT_DIST_KEYS tuple
├── hedge/
│   ├── __init__.py
│   ├── falsification.py        # 4-condition gate; writes gate_report.json
│   │                           # + REQUIRED_GATE_REPORT_KEYS tuple
│   ├── carr_madan_strip.py     # FFT strip + 2^11 → 2^12 escalation + abort-to-strip_degenerate.json
│   │                           # + REQUIRED_STRIP_KEYS / STRIP_DEGENERATE_KEYS tuples
│   ├── stress_test.py          # independence + fitted_joint + comonotone three-way
│   │                           # + REQUIRED_STRESS_REPORT_KEYS tuple
│   ├── usdt_depeg.py           # condition-4 helpers; Merton/Kou simulator; Latin hypercube N=64
│   ├── null_result.py          # HEDGE-05 firing decision (single entry); calls quarto render
│   └── orchestrator.py         # CLI subcommand wiring; reads fit_report.json + writes the 4 artifacts

reports/
├── _templates/
│   └── null_result.qmd         # Quarto template; 3 conditional branches per firing condition;
│                               # dual signature markers (H1 + PDF-metadata HEDGE05-NULL-RESULT-V1)
└── ichi.pdf                    # produced by quarto render on HEDGE-05 firing

notes/
└── usdt_depeg_calibration.md   # methodological-port assumption + Latin hypercube sensitivity table
                                # + EXPLICIT note that arxiv 2407.11716 does NOT publish Merton/Kou
                                # parameters and the triple (λ, μ_J, σ_J) is stipulated

analysis/tests/
├── fixtures/
│   └── hedge_05_null_cost/{fit_report.json, gate_report.json, cost_leg_bound.md}
│   └── hedge_05_null_lr/      (same triplet)
│   └── hedge_05_null_convex/  (same triplet)
├── test_cross_correlogram.py
├── test_permutation_null.py
├── test_copula_bic.py
├── test_falsification.py
├── test_carr_madan_strip.py
├── test_stress_test.py
├── test_usdt_depeg_lhs.py
├── test_null_result_template.py  # pdftotext-based dual-marker grep
└── test_joint_dist_provenance.py
```

### Pattern 1: Mirror Phase 3 Orchestrator → SC-1 → Lint Chain

**What:** Every new JSON artifact gets a `REQUIRED_<X>_KEYS` tuple in the module that writes it, mirrored verbatim in `scripts/lint_artifacts.py`, and the `Makefile :: lint-artifacts` target is extended to walk the new artifact pattern. Pre-write `KeyError` guard prevents malformed files from landing on disk. Phase 3 Pattern G.

**When to use:** Every Phase 4 artifact (`joint_dist.json`, `gate_report.json`, `stress_report.json`, `strip.json`, `strip_degenerate.json`).

**Example** (verbatim Phase 3 pattern, generalizable):

```python
# Source: analysis/src/abrigo_x402/dgp/orchestrator.py:71-90 (Phase 3 substrate)
REQUIRED_FIT_REPORT_KEYS: tuple[str, ...] = (
    "chainId", "contractAddress", "blockRange",
    "fetchTimestamp", "dataHash", "gitCommit",
    "run_id", "tick_lib_version",
    "nhpp_inar_params", "hawkes_mv_params", "lr_test",
    "ks_rescaled_time", "held_out_loglik", "branching_ratio_ci",
    "baseline_stationarity_check", "input_diagnostics",
    "gate_passes", "gate_criteria",
)

# Pre-write invariant — Phase 3 Pattern G
missing = [k for k in REQUIRED_FIT_REPORT_KEYS if k not in fit_report]
if missing:
    raise KeyError(f"fit_report.json assembly bug: missing required SC-1 keys: {missing}")
```

**Phase 4 generalization** — five new tuples to add, one per artifact:

```python
# analysis/src/abrigo_x402/dependence/copula.py
REQUIRED_JOINT_DIST_KEYS: tuple[str, ...] = (
    "chainId", "contractAddress", "blockRange",
    "fetchTimestamp", "dataHash", "gitCommit", "run_id",
    "cross_correlogram",   # {lags: [...], values: [...]}
    "permutation_null",    # {n_reps: int, p_value: float, max_abs_rho_observed: float}
    "empirical_copula",    # {family, params, bic, all_candidates_bic: {gaussian, t, clayton, frank, gumbel}}
    "vine_fallback_used",  # bool
)

# analysis/src/abrigo_x402/hedge/falsification.py
REQUIRED_GATE_REPORT_KEYS: tuple[str, ...] = (
    "chainId", "contractAddress", "blockRange",
    "fetchTimestamp", "dataHash", "gitCommit", "run_id",
    "vol_of_vol_gt_zero",         # {passed: bool, evidence: dict}
    "positive_skew_fat_tails",    # {passed: bool, evidence: dict}
    "hawkes_self_excitation",     # {passed: bool, evidence: dict}
    "usdt_depeg_basis_jump",      # {passed: bool, evidence: dict (incl. sensitivity_fragile flag)}
    "any_condition_passed",       # bool (HEDGE-05 firing-condition (c) consumes this)
)
```

Mirror in `scripts/lint_artifacts.py` as `JOINT_DIST_REQUIRED_KEYS = frozenset({...})` etc., and extend `Makefile :: lint-artifacts` to scan `data/fits/**/{joint_dist,gate_report,stress_report,strip,strip_degenerate}.json` in addition to existing parquet + fit_report.json sweeps.

### Pattern 2: Canonical-LL Contract Reuse (Phase 3 Pattern F)

**What:** When Phase 4 needs to RE-evaluate a Hawkes log-likelihood (e.g., condition-3 evidence in `falsification.py` "is the in-sample Hawkes fit good enough to count as evidence?"), import `_hawkes_loglik_vectorized` from `lr_test.py` rather than calling `tick.score()` directly. Tick's score returns the LS objective under the LS fallback (Phase 3 03-02 documented this), not the canonical continuous-time point-process LL.

**When to use:** Anywhere in `hedge/falsification.py` or `hedge/null_result.py` that consumes Hawkes LL.

**Example:**

```python
# Source: analysis/src/abrigo_x402/dgp/orchestrator.py:53-59 (Phase 3 substrate)
from abrigo_x402.dgp.lr_test import (
    _hawkes_loglik_vectorized,
    _nhpp_pointprocess_loglik,
)

# Phase 4 use (in falsification.py condition 3 evidence check)
ll_hawkes = _hawkes_loglik_vectorized(
    baseline, adjacency, decays, leg_0, leg_1
)
# DO NOT use tick_learner.score() — wrong probability space under LS fallback
```

### Pattern 3: Provenance Header on All Artifacts (PANEL-02 + SC-1)

**What:** Every new JSON artifact carries the 6-key PANEL-02 metadata header (chainId, contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit) PLUS the Phase 3 run_id (so artifacts in the same `data/fits/<run_id>/` directory share a common index). Reuse `analysis/src/abrigo_x402/provenance.py :: with_header` API for parquet sidecars (if any), and hand-build the JSON header for `.json` artifacts via the orchestrator pattern.

**Example:**

```python
# Source: analysis/src/abrigo_x402/dgp/orchestrator.py:163-188 (Phase 3 substrate)
def _panel_provenance(panel_path, chain_id, contract_address) -> dict:
    return {
        "chainId": int(chain_id),
        "contractAddress": str(contract_address),
        "blockRange": [from_block, to_block],
        "fetchTimestamp": datetime.now(timezone.utc).isoformat(),
        "dataHash": _compute_data_hash(panel_path),
        "gitCommit": _git_commit(),
    }
# Plus the Phase 3 run_id from the existing fit_report.json header.
```

### Pattern 4: Thread-pin-before-import for Byte-Identity (Phase 3 Pattern I)

**What:** Any Phase 4 test asserting byte-identical output from FFT-driven Carr–Madan or copula MLE MUST pin BLAS/OMP/MKL/OpenBLAS/NumExpr to 1 via `os.environ.setdefault` BEFORE the first numpy/scipy/polars import. The pinning block MUST be the first executable code in the test file.

**When to use:** `test_byte_identical_stress_report.py`, `test_byte_identical_strip.py`, `test_byte_identical_joint_dist.py` (any Phase 4 byte-identity assertion test).

**Example:**

```python
# Source: analysis/tests/test_byte_identical.py:1-15 (Phase 3 substrate)
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

# NOW safe to import numpy/scipy/polars
import numpy as np
# ... rest of test
```

### Pattern 5: Polymorphic Carr–Madan API for v2.0 Streaming-Tokenization

**What:** Per `notes/ROADMAP-EXTENSIONS.md`, the Carr–Madan replicating-strip module's API MUST accept an arbitrary payoff `f: ndarray → ndarray`, not just LP-fee revenue. v2.0 will pass a stream-PV payoff into the same strip generator.

**When to use:** Designing the function signature for `hedge/carr_madan_strip.py :: compute_strip`.

**Example:**

```python
# v1.0 design (Phase 4)
def compute_strip(
    payoff: Callable[[np.ndarray], np.ndarray],  # f(S_T) -> ndarray
    char_func: Callable[[np.ndarray], np.ndarray],  # φ(u) for fitted joint distribution
    n_grid: int = 2**11,
    positivity_tolerance: float = 0.001,  # CONTEXT.md locked; PRE_REG amendment
    max_escalations: int = 1,             # 2^11 -> 2^12 once
) -> dict:
    """Return {strip_prices, strikes, escalated_to_2_12, negative_mass_fraction}."""
    ...

# v1.0 caller passes LP-fee payoff
strip = compute_strip(payoff=lp_fee_revenue, char_func=phi_fitted_joint, ...)

# v2.0 caller passes stream-PV payoff — same function, no API change
strip = compute_strip(payoff=stream_pv, char_func=phi_fitted_stream_joint, ...)
```

### Anti-Patterns to Avoid

- **`scipy.integrate.quad` in `hedge/carr_madan_strip.py`:** the Carr–Madan inverse Fourier integral MUST be discretized via FFT (or COS/PROJ), NOT numerical integration. Add a grep gate: `! grep -rE "from scipy.integrate import (quad|fixed_quad|romberg)" analysis/src/abrigo_x402/hedge/carr_madan_strip.py` MUST exit 0.
- **`loglik_in_sample_raw` consumption in `hedge/*`:** Phase 3 Pattern F established that `loglik_in_sample_raw` is the upstream LS-fallback objective (tick.score()) NOT the canonical Hawkes LL. Phase 4 reads only the canonical `loglik` field from `fit_report.json :: hawkes_mv_params`. Add a grep gate: `! grep -rn "loglik_in_sample_raw" analysis/src/abrigo_x402/hedge/` MUST exit 0.
- **`usdc` literals in `analysis/src/abrigo_x402/hedge/*`** (except as comparison/historical-reference comments): SC-2 mandates the condition-4 framing is **USDT depeg + USDT/USDC basis**, not USDC alone. Grep gate: `grep -in "usdc" analysis/src/abrigo_x402/hedge/falsification.py` returns ONLY comment lines matching `^\s*#`. Extend grep to ALL `hedge/*.py` for defence in depth.
- **`from statsmodels.distributions.copula import` and `from scipy.stats import (multivariate_normal|t)` in `dependence/copula.py`:** CONTEXT.md locked `copulae` as the BIC menu source; mixing libraries silently invites parameter-convention drift. Grep gate at plan-acceptance time.
- **Silent vine-copula activation:** if `pyvinecopulib` is installed but `ΔBIC < 5`, the vine MUST NOT be the chosen empirical copula. The decision logic in `dependence/copula.py` must record `vine_fallback_used: false` and choose the BIC-min bivariate. Test: synthetic Gaussian-copula fixture where the bivariate Gaussian wins by 100+ BIC points; vine_fallback_used MUST be False.
- **Hardcoded jump-diffusion parameters in `hedge/falsification.py` or `hedge/carr_madan_strip.py`:** the `(λ, μ_J, σ_J)` triple lives ONLY in `notes/usdt_depeg_calibration.md` and is loaded via `usdt_depeg.load_calibration()`. Grep gate: `grep -rE 'lambda_J\s*=\s*0\.|mu_J\s*=\s*-?0\.|sigma_J\s*=\s*0\.' analysis/src/abrigo_x402/hedge/{falsification,carr_madan_strip}.py` MUST exit non-zero (no hits).
- **Re-fitting NHPP/Hawkes in any Phase 4 module:** all parameters come from `fit_report.json`. Grep gate: `! grep -rn "fit_nhpp_inar\|fit_hawkes_expkern\|HawkesExpKern" analysis/src/abrigo_x402/hedge/` and `! grep -rn "fit_nhpp_inar\|fit_hawkes_expkern\|HawkesExpKern" analysis/src/abrigo_x402/dependence/` MUST both exit 0 (excluding test fixtures where synthetic NHPP/Hawkes generation IS allowed via SimuHawkesExpKernels).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 5-family copula BIC ranking | Hand-coded Gaussian + t + Clayton + Frank + Gumbel pdf/CDF/MLE | `copulae==0.8.0` | Edge cases: parameter boundaries (Clayton θ→0 = independence; t ν→∞ = Gaussian); identifiability under near-perfect dependence; numerical stability of bivariate t-CDF. Library handles all. |
| 2D vine pair-copula construction | Hand-rolled R-vine on 2 variables | `pyvinecopulib==0.7.6` (IF triggered) | C++ vinecopulib + nanobind bindings; battle-tested in financial risk; Py 3.13 wheels available. Don't reinvent. |
| Latin hypercube sampling on 3 dimensions, N=64 | Hand-rolled stratified random sampling | `scipy.stats.qmc.LatinHypercube(d=3, seed=...)` | scipy 1.17.1 already locked; deterministic via `seed=` kwarg; `qmc.scale()` maps `[0,1]^3` to `[lo, hi]^3` bounds. |
| FFT for inverse characteristic function | Hand-coded `np.exp(-1j * u * k)` loops | `np.fft.fft` / `np.fft.ifft` | numpy uses pocketfft; vectorized; 100× faster than Python loops at 2¹¹ points. |
| Permutation null distribution under within-window shuffle | Hand-coded for-loop with `random.shuffle` | `np.random.default_rng(seed).permutation(arr)` 1000-rep loop, vectorized | seedable, reproducible, no GIL contention if needed. |
| PDF rendering with embedded Python output + LaTeX-quality math | Hand-rolled matplotlib → PNG → ReportLab → PDF | Quarto + `.qmd` template + `quarto render` | CONTEXT.md locked; Quarto handles citations + cross-references + Python chunk caching + LaTeX engine selection. |
| Empirical CDF inverse transform for comonotone scenario | Hand-coded `np.interp(quantiles, sorted_x, np.linspace(0, 1, n))` | `scipy.stats.rankdata` for PIT → inverse-transform via `np.interp` on sorted marginals | scipy's rankdata handles ties correctly (average method); hand-coded inverse-CDF is one numpy line BUT must handle ties + endpoint extrapolation explicitly. Use scipy where it exists. |
| Permutation-null `max |ρ(h)|` over a lag grid | Loop over lags inside the 1000-rep loop | Vectorize: compute the full cross-correlogram in one numpy call per rep, then `np.max(np.abs(corr))` | Inner-loop vectorization gets the 1000-rep cost from ~minutes to ~seconds. Phase 3 Pattern F (vectorized loglik) is the model. |

**Key insight:** Phase 4 is heavy on numerical stochastic-process work where library-provided implementations have absorbed years of edge-case bug fixes. The few hand-rolled pieces (Bowsher-2007 event-index cross-correlogram, four-condition gate evidence computation, Carr–Madan strip with custom payoff hook, Fréchet-upper-bound comonotone sampler) are short (≤50 lines each) and either domain-specific (Bowsher) or trivially correct (Fréchet upper bound is `U_2 = U_1`).

## Common Pitfalls

### Pitfall 1: Hernandez Cruz 2024 doesn't actually publish jump-diffusion parameters

**What goes wrong:** The CONTEXT.md HEDGE-03 calibration cites "Hernandez Cruz 2024 Merton/Kou parameters" as the base for the methodological port. Verified via WebFetch on arxiv 2407.11716 and arxiv abstract pages: the paper is a transparency/MCI (Marginal Cost of Immediacy) study on USDC liquidity around SVB, using Difference-in-Differences on Uniswap AMM data — it does NOT publish Merton or Kou jump-diffusion calibration parameters. Wu & Liu 2026 (arxiv 2602.18820, the other cited source) uses Quantile VAR, also not jump-diffusion.

**Why it happens:** The SOMNIA_DRAFT.md condition-4 row cites these two papers as "Primary source," which in the upstream draft's context means "primary evidence that the depeg jump class is real," not "primary source for jump-diffusion parameters." The leap from "depeg observed → jump-diffusion calibration parameters" requires a SEPARATE step (fitting Merton/Kou to raw USDC tick data from March 2023, or accepting a defensibly stipulated triple).

**How to avoid:** `notes/usdt_depeg_calibration.md` MUST explicitly say:
1. "Hernandez Cruz 2024 establishes the depeg event as load-bearing; it does NOT publish jump-diffusion parameters."
2. "The stipulated triple `(λ, μ_J, σ_J) = (..., ..., ...)` is derived from <fit-on-raw-March-2023-USDC-tick-data | analyst stipulation calibrated against the literature range>."
3. "The N=64 Latin hypercube ±50% sensitivity sweep around this triple is the honesty-of-port mitigation — if the gate decision is stable across the sweep, the stipulated triple is not load-bearing."

The planner SHOULD NOT use the phrase "port from Hernandez Cruz 2024 Merton/Kou parameters" in Plan 04-NN bodies without first reading the paper. The CONTEXT.md wording is aspirational; the planner needs to disambiguate.

**Warning signs:** Plan body says "uses the Hernandez Cruz 2024 calibration"; `notes/usdt_depeg_calibration.md` cites a `(λ, μ_J, σ_J)` triple with "per Hernandez Cruz 2024 Table X" — there is no such table in 2407.11716.

### Pitfall 2: Vine copula fallback fires spuriously in 2D

**What goes wrong:** In 2 dimensions, a vine pair-copula construction reduces to a single bivariate copula + uniform marginals. The "vine fallback only if BIC prefers" clause from DEPEND-01 is mostly defensive scaffolding for the >2D generalization deferred to v2.0. If `pyvinecopulib` is naively given the same 2D data, its default canonical/D-vine selection over the 5-family bivariate set may produce a `vinecop.bic()` that is MARGINALLY different from the best `copulae` bivariate fit due to differences in parameter initialization, optimizer convergence tolerance, and how each library counts degrees of freedom. A 1–2 BIC unit gap that flips the `vine_fallback_used` flag is meaningless.

**Why it happens:** The two libraries are independent implementations with different MLE start values. ΔBIC < 5 is below the noise floor for cross-library agreement.

**How to avoid:** The CONTEXT.md ΔBIC ≥ 5 threshold is designed exactly to avoid this — but the planner MUST ensure the comparison is apples-to-apples by either (a) computing BOTH BICs via the same library if possible, OR (b) accepting that the ΔBIC ≥ 5 threshold is generous enough to absorb cross-library noise. In 2D, the most defensible thing is to LOG both BICs but conservatively set `vine_fallback_used = false` unless `vine_bic + 5 < bivariate_bic_min` AND the vine's first-tree pair-copula is materially different from the bivariate winner.

**Warning signs:** `vine_fallback_used == true` but the vine's selected first-tree pair-copula is the SAME family as the bivariate BIC winner.

### Pitfall 3: Quarto chunk caching + freeze gives false-determinism

**What goes wrong:** Quarto's `freeze: true` directive caches the output of executed Python chunks in `_freeze/`. If the underlying data (`fit_report.json`, `gate_report.json`) changes but the `.qmd` source doesn't, Quarto re-uses the cached output and the PDF reflects STALE numbers. Same hazard with `cache: true` at the chunk level.

**Why it happens:** Quarto's freeze/cache invalidation is based on `.qmd` source hash, not on the input data files the chunks read.

**How to avoid:** For the HEDGE-05 null-result PDF rendering pipeline, set `execute: { freeze: false, cache: false }` in the `.qmd` YAML header — always re-execute. The build target `make render-null-result-pdf` runs `quarto render --no-cache` to belt-and-suspenders the invariant. Trade-off: every render re-executes the chunks (~10s for a null-result PDF), which is fine. Determinism > render speed.

**Warning signs:** `_freeze/` directory exists in the repo; the PDF's numbers don't update after `gate_report.json` is regenerated; reviewer asks "are these the latest numbers?" and the answer is "let me re-run with --no-cache to be sure."

### Pitfall 4: Permutation null preserves wrong invariant under non-stationary baseline

**What goes wrong:** The within-window shuffle of `leg_1` timestamps destroys cross-leg dependence BUT also destroys leg_1's own marginal arrival-time structure if the baseline is non-stationary. If both legs trend upward in arrival rate over the window (common when ICHI's TVL grows), the un-shuffled cross-correlogram captures (true cross-dependence) + (spurious common-trend artifact); the shuffled null captures only the spurious artifact; the test under-rejects.

**Why it happens:** Permutation tests preserve marginal distributions but break temporal structure. For arrival-time processes where the marginal IS the temporal structure, this is sharp.

**How to avoid:** Two options:
1. **(preferred)** Use the time-rescaled residuals from `residuals.parquet :: rescaled_dt` (already produced by Phase 3 DGP-05) as the substrate for the cross-correlogram + permutation. Under correctly-specified Hawkes, `rescaled_dt` is exp(1)-distributed iid per leg → permutation preserves the iid invariant correctly.
2. (fallback) Block-permutation in event-index lags (Politis-Romano 1994 style) — shuffle 5-event blocks rather than individual events. Preserves local arrival-rate structure.

CONTEXT.md doesn't explicitly mandate (1) but the "Bowsher-2007-style intensity-based cross-correlogram convention" clue plus the existence of `residuals.parquet` strongly suggests (1) is the intended substrate. **Planner should confirm with user OR explicitly document the choice in Plan 04-NN body.**

**Warning signs:** Permutation p-value is much LARGER than expected on a synthetic fixture with known cross-dependence; the cross-correlogram on raw timestamps has a slow trend not present on residuals.

### Pitfall 5: Carr–Madan FFT precision on slow-decaying char functions

**What goes wrong:** PITFALLS §7 already flagged this — under fat-tailed joint distributions (Hawkes self-excitation + USDT depeg jump), the characteristic function decays slowly. Standard 2^11 grid produces negative implied densities at extreme strikes; even 2^12 may not suffice. The CONTEXT.md 0.1% tolerance is calibrated for FFT-truncation artifacts at 2^11/2^12, NOT for genuine fat-tail blowups.

**Why it happens:** Bates-class models and Merton jump-diffusion have characteristic functions with `|φ(u)| ~ exp(-α|u|^β)` for β<1, requiring exponentially more grid points for the same error. arxiv 1706.05935 documented 2^11–2^12 for 10^-10 accuracy on Bates.

**How to avoid:** The locked SC-3 escalation (2^11 → 2^12 → abort-to-`strip_degenerate.json`) is the right discipline. Phase 4 must NOT silently swap to COS/PROJ method (CONTEXT.md locked). The `strip_degenerate.json` payload includes `{max_negative_value, total_negative_mass, characteristic_function_decay_rate, recommended_method: "COS"|"PROJ"|"none"}` so the Phase 5 report can document the failure publicly.

**Warning signs:** Test asserts strip emits cleanly on a synthetic fat-tail fixture (Hawkes with η=0.8 + Merton jumps); reality is the test should assert `strip_degenerate.json` is written and the abort path is exercised.

### Pitfall 6: Comonotone scenario double-counts marginal CDFs computed at fitted vs empirical level

**What goes wrong:** The Fréchet upper bound is `(F^{-1}_1(U), F^{-1}_2(U))` for `U ~ U(0,1)`. If the marginal CDFs `F_1, F_2` are estimated by fitting parametric distributions to the residuals (PIT through fitted marginals), the comonotone samples reflect the fitted marginals' tail behavior — which may misrepresent the empirical tail. If `F_1, F_2` are empirical (rank transform), the tails are bounded by `±1/n` of the observed range — which under-represents the true tail.

**Why it happens:** Both choices have well-known pathologies. CONTEXT.md flags this as Claude's Discretion: "How rate-comonotone marginal CDFs are computed (rank transform vs PIT through fitted parametric marginals)."

**How to avoid:** Recommendation: use the **rank transform** (empirical CDF) for the marginal-CDF construction in the comonotone scenario, BUT extend the empirical CDF tail beyond the observed range via the **fitted parametric tail** of the BIC-winning copula's univariate marginal model. This gives empirical-body + parametric-tail. Document the choice in the Plan 04-NN body and in `stress_report.json :: comonotone_method: "empirical_body_parametric_tail"`.

**Warning signs:** Comonotone strip price is suspiciously close to the independence strip price (suggests empirical tails are too short — the rank transform is one-sided) OR suspiciously divergent (suggests fitted tail is over-extending). Reviewer should look at a quantile-quantile plot of comonotone draws vs empirical samples.

### Pitfall 7: AF-03 amendment ordering invariant is non-obvious

**What goes wrong:** CONTEXT.md `<deferred>` mandates the PRE_REGISTRATION amendment for the 0.1% positivity tolerance be committed BEFORE any `analysis/src/abrigo_x402/hedge/*` commit. The pre-commit hook (Phase 0 SC-4) enforces review-trail discipline on `.planning/**/PLAN.md` artifacts but NOT on `notes/PRE_REGISTRATION.md` edits per se — the AF-03 ordering invariant is documented but not yet machine-enforced.

**Why it happens:** No precedent for in-band PRE_REGISTRATION amendments in the repo (verified — only the initial 2026-05-25 commit by Plan 00-01 exists). Phase 4 sets the precedent.

**How to avoid:** Plan 04-pre (or the first task of Plan 04-00) commits the amendment as a SOLO commit with message `docs(pre-reg): AF-03 amendment — Carr-Madan grid 0.1% positivity tolerance`. Plan 04-01 onward then commits `hedge/*` code; `git log --oneline -- notes/PRE_REGISTRATION.md analysis/src/abrigo_x402/hedge/` MUST show the amendment commit predates ALL hedge/* commits. The acceptance grid for Phase 4 (`04-VERIFICATION-pre.md`) should include this ordering check verbatim.

**Warning signs:** Plan 04-01 commits the amendment and code together; `git log --reverse --oneline -- analysis/src/abrigo_x402/hedge/ | head -1` returns a commit earlier than `git log -1 --oneline -- notes/PRE_REGISTRATION.md` — that's an AF-03 violation.

### Pitfall 8: tick polars.to_numpy() shape mismatch (carried over from Phase 3)

**What goes wrong:** `polars.Series.to_numpy()` returns a 2-D `(N, 1)` array; `tick.HawkesExpKern.set_data()` and the closed-form `_hawkes_loglik_vectorized` expect flat 1-D float64. Phase 3 03-08 documented this in `03-VERIFICATION-pre.md`. Any Phase 4 fixture-generation code that creates synthetic Hawkes samples for `hedge_05_null_convex` MUST cast via `.ravel().astype(np.float64)`.

**How to avoid:** In all Phase 4 test fixtures and any direct CLI invocations, mirror the conftest pattern: `leg_0 = pl.read_parquet(p).get_column("ts").to_numpy().ravel().astype(np.float64)`. Confer with `analysis/tests/conftest.py` for the canonical cast.

## Code Examples

Verified patterns from project substrate + official sources.

### Reading the Phase 3 substrate (entry point for every Phase 4 module)

```python
# Source: analysis/src/abrigo_x402/dgp/orchestrator.py (Phase 3 production code)
import json
import polars as pl
from pathlib import Path

run_dir = Path("data/fits/ichi") / run_id  # 12-hex from Phase 3 orchestrator
fit_report = json.loads((run_dir / "fit_report.json").read_text())

# Substrate available:
adjacency = np.array(fit_report["hawkes_mv_params"]["adjacency"])  # 2x2 off-diagonal
branching_ratio = float(fit_report["hawkes_mv_params"]["branching_ratio"])
eta_ci = fit_report["branching_ratio_ci"]  # {lower, upper, method, ...}
gate_passes = bool(fit_report["gate_passes"])
gate_criteria = fit_report["gate_criteria"]  # {lr_rejects, eta_floor_met, ...}
stationarity = fit_report["baseline_stationarity_check"]  # {train_rate, held_out_rate, ratio, decision}

residuals = pl.read_parquet(run_dir / "residuals.parquet")
# Schema (from analysis/src/abrigo_x402/dgp/time_rescaling.py:build_residuals_dataframe):
#   leg: int (0 or 1)
#   event_time: float64 (seconds)
#   Lambda_at_event: float64 (compensator integrated to each event time)
#   rescaled_dt: float64 (exp(1)-distributed under correct Hawkes specification)
```

### 5-family copula BIC ranking (DEPEND-01)

```python
# Source: copulae 0.8.0 README + standard BIC formula
import numpy as np
from copulae import NormalCopula, StudentCopula, ClaytonCopula, FrankCopula, GumbelCopula

def fit_5_families_bic(u_data: np.ndarray) -> dict:
    """u_data: (N, 2) PIT-uniform samples from residuals."""
    families = {
        "gaussian": NormalCopula(dim=2),
        "t":        StudentCopula(dim=2),
        "clayton":  ClaytonCopula(dim=2),
        "frank":    FrankCopula(dim=2),
        "gumbel":   GumbelCopula(dim=2),
    }
    results = {}
    for name, cop in families.items():
        cop.fit(u_data)
        k = cop.dim  # crude proxy; some families have k=1, t has k=2
        n = u_data.shape[0]
        bic = -2.0 * cop.log_lik(u_data) + k * np.log(n)
        results[name] = {
            "params": cop.params.tolist() if hasattr(cop.params, "tolist") else float(cop.params),
            "log_lik": float(cop.log_lik(u_data)),
            "bic": float(bic),
        }
    bic_min_family = min(results, key=lambda f: results[f]["bic"])
    return {
        "winner": bic_min_family,
        "all_candidates": results,
    }
```

### Cross-correlogram + permutation null (Bowsher 2007 event-index domain)

```python
# Source: Bowsher 2007 (event-index cross-correlogram); standard permutation test
import numpy as np
from numpy.random import default_rng

def cross_correlogram_event_index(leg_0_times, leg_1_times, max_lag=50):
    """ρ(h) for h in -max_lag..+max_lag, event-index domain.

    For each event in leg_0, find the index-h-nearest event in leg_1 and
    correlate the inter-arrival times. CONTEXT.md locks max_lag=50.
    """
    lags = np.arange(-max_lag, max_lag + 1)
    # ... implementation: rank-transform timestamps to event-index, compute Pearson r at each lag ...
    return lags, rho_values  # shape: (2*max_lag + 1,)

def permutation_null(leg_0_times, leg_1_times, max_lag=50, n_reps=1000, seed=0xC0PA):
    """Within-window shuffle of leg_1; record max|ρ(h)| over all lags per rep."""
    rng = default_rng(seed)
    _, observed_rho = cross_correlogram_event_index(leg_0_times, leg_1_times, max_lag)
    observed_stat = float(np.max(np.abs(observed_rho)))
    perm_stats = np.empty(n_reps, dtype=np.float64)
    for r in range(n_reps):
        shuffled_leg_1 = rng.permutation(leg_1_times)
        _, perm_rho = cross_correlogram_event_index(leg_0_times, shuffled_leg_1, max_lag)
        perm_stats[r] = float(np.max(np.abs(perm_rho)))
    p_value = float(np.mean(perm_stats >= observed_stat))
    return {
        "observed_stat": observed_stat,
        "n_reps": n_reps,
        "p_value": p_value,
        "perm_null_summary": {
            "mean": float(perm_stats.mean()),
            "q95": float(np.quantile(perm_stats, 0.95)),
        },
    }
```

### Carr–Madan FFT strip (HEDGE-02)

```python
# Source: Carr & Madan 1999; Lewis 2001 + arxiv 1706.05935 truncation guidance
import numpy as np
from typing import Callable

def carr_madan_strip(
    char_func: Callable[[np.ndarray], np.ndarray],
    payoff: Callable[[np.ndarray], np.ndarray],
    *,
    n_grid: int = 2**11,
    eta_u: float = 0.25,         # spacing in Fourier domain
    alpha: float = 1.5,          # damping (Carr-Madan convention)
    positivity_tolerance: float = 0.001,  # CONTEXT.md locked
) -> dict:
    """Compute static-replication strip for payoff f(S) via FFT.

    Returns dict with:
      - strip_prices: array[n_grid]
      - strikes: array[n_grid]
      - max_negative_value: float
      - total_negative_mass_fraction: float
      - positivity_check_passed: bool
      - n_grid_used: int (2**11 or 2**12)
    """
    u = np.arange(n_grid) * eta_u
    # ... Carr-Madan kernel: integrate char_func(u - (alpha+1)j) / (alpha^2 + alpha - u^2 + j(2*alpha+1)*u) ...
    phi_u = char_func(u - (alpha + 1) * 1j)
    integrand = np.exp(-alpha * 0.0) * phi_u / (alpha**2 + alpha - u**2 + 1j * (2*alpha + 1) * u)
    # ... FFT inversion ...
    raw = np.fft.fft(integrand * np.exp(-1j * u * 0.0))  # placeholder; full formula in Carr-Madan 1999
    q = np.real(raw)  # implied density
    # ... map back to strike grid; apply damping correction ...
    negative_mass = float(np.sum(q[q < 0.0]))
    total_mass = float(np.sum(np.abs(q)))
    fraction = abs(negative_mass) / total_mass if total_mass > 0 else 1.0
    return {
        "strip_prices": q,  # placeholder
        "max_negative_value": float(q.min()),
        "total_negative_mass_fraction": fraction,
        "positivity_check_passed": fraction < positivity_tolerance,
        "n_grid_used": n_grid,
    }

def carr_madan_with_escalation(char_func, payoff) -> dict:
    """SC-3 escalation: 2^11 -> 2^12 -> abort to strip_degenerate.json."""
    result = carr_madan_strip(char_func, payoff, n_grid=2**11)
    if result["positivity_check_passed"]:
        return {"status": "ok", "strip": result, "escalated_to_2_12": False}
    result_12 = carr_madan_strip(char_func, payoff, n_grid=2**12)
    if result_12["positivity_check_passed"]:
        return {"status": "ok", "strip": result_12, "escalated_to_2_12": True}
    # Abort path
    return {
        "status": "degenerate",
        "strip_degenerate_payload": {
            "max_negative_value": result_12["max_negative_value"],
            "total_negative_mass": result_12["total_negative_mass_fraction"],
            "characteristic_function_decay_rate": "TODO: fit |phi(u)| ~ exp(-alpha*|u|^beta) and report alpha, beta",
            "recommended_method": "COS",
        },
    }
```

### Fréchet-upper-bound comonotone sampler (HEDGE-04)

```python
# Source: standard copula theory (Nelsen 2006 ch. 3); Phase 4 CONTEXT.md lock
import numpy as np
from scipy.stats import rankdata

def comonotone_sample(leg_0_residuals, leg_1_residuals, n_samples, seed=0xCAFE):
    """Fréchet upper bound: U_2 = U_1, inverse-transform via empirical CDFs.

    Empirical-body, parametric-tail extension recommended (Pitfall 6).
    For v1, plain empirical CDF (np.interp) is the simplest defensible choice.
    """
    rng = np.random.default_rng(seed)
    u = rng.uniform(size=n_samples)  # shared uniform
    # Empirical CDF inverse via interpolation
    sorted_0 = np.sort(leg_0_residuals)
    sorted_1 = np.sort(leg_1_residuals)
    n_0 = sorted_0.size
    n_1 = sorted_1.size
    samples_0 = np.interp(u, np.linspace(0, 1, n_0), sorted_0)
    samples_1 = np.interp(u, np.linspace(0, 1, n_1), sorted_1)
    return np.column_stack([samples_0, samples_1])
```

### Latin hypercube for HEDGE-03 sensitivity (N=64, ±50%)

```python
# Source: scipy.stats.qmc.LatinHypercube docs v1.17
from scipy.stats import qmc
import numpy as np

def lhs_jump_diffusion_sensitivity(
    base_lambda: float,
    base_mu_J: float,
    base_sigma_J: float,
    n_samples: int = 64,
    seed: int = 0xD55D,
):
    """Generate N=64 LHS samples in the +-50% box around the base triple.

    Locked CONTEXT.md: 3 parameters, N=64, ±50%, deterministic seed.
    """
    sampler = qmc.LatinHypercube(d=3, seed=seed)
    unit_samples = sampler.random(n=n_samples)  # in [0, 1)^3
    lower = np.array([0.5 * base_lambda, 0.5 * base_mu_J, 0.5 * base_sigma_J])
    upper = np.array([1.5 * base_lambda, 1.5 * base_mu_J, 1.5 * base_sigma_J])
    scaled = qmc.scale(unit_samples, lower, upper)
    # scaled.shape == (64, 3); columns are (lambda, mu_J, sigma_J)
    return scaled
```

### HEDGE-05 firing decision (single-entry orchestrator)

```python
# Source: pattern mirrors analysis/src/abrigo_x402/dgp/orchestrator.py:run_fit
from pathlib import Path
import json
import subprocess

FIRING_CONDITIONS = ("null_cost", "null_lr", "null_convex")
HEDGE05_SIGNATURE = "HEDGE05-NULL-RESULT-V1"

def decide_and_emit(
    fit_report_path: Path,
    gate_report_path: Path,
    cost_leg_bound_md: Path | None,
    out_pdf: Path = Path("reports/ichi.pdf"),
) -> dict:
    """Single-entry HEDGE-05 firing decision. Returns the firing record."""
    fit = json.loads(fit_report_path.read_text())
    gate = json.loads(gate_report_path.read_text()) if gate_report_path.exists() else None

    # Condition (a): Phase-0 cost-leg gate fail (memo predates this run)
    if cost_leg_bound_md and cost_leg_bound_md.exists():
        text = cost_leg_bound_md.read_text()
        if "verdict: FAIL" in text or "verdict: STRADDLE" in text:
            return _render_null_result(out_pdf, firing="null_cost", evidence={"cost_leg_bound": str(cost_leg_bound_md)})
    # Condition (b): DGP-03 LR indistinguishable
    if not fit["gate_criteria"]["lr_rejects"]:
        return _render_null_result(out_pdf, firing="null_lr", evidence={"lr_test": fit["lr_test"]})
    # Condition (c): zero convex-dominance conditions
    if gate is not None and not gate["any_condition_passed"]:
        return _render_null_result(out_pdf, firing="null_convex", evidence={"gate_report": str(gate_report_path)})
    return {"firing": None, "next_step": "compute_strip"}

def _render_null_result(out_pdf: Path, *, firing: str, evidence: dict) -> dict:
    """Invoke quarto render with the firing-specific evidence injected."""
    template = Path("reports/_templates/null_result.qmd")
    # Pass firing condition + evidence via Quarto parameters (or env vars consumed by .qmd YAML)
    env = {"HEDGE05_FIRING_CONDITION": firing, "HEDGE05_EVIDENCE_JSON": json.dumps(evidence)}
    subprocess.run(
        ["quarto", "render", str(template), "--output", out_pdf.name, "--no-cache"],
        env={**os.environ, **env}, check=True,
    )
    return {
        "firing": firing,
        "evidence": evidence,
        "pdf_path": str(out_pdf),
        "signature_marker": HEDGE05_SIGNATURE,
    }
```

### Quarto template signature markers (dual: visible H1 + PDF metadata)

```yaml
---
# reports/_templates/null_result.qmd YAML header
title: "HEDGE-05 NULL RESULT — {{< meta firing-condition >}}"
format:
  pdf:
    pdf-engine: lualatex
    include-in-header:
      text: |
        \pdfinfo{
          /Hedge05Signature (HEDGE05-NULL-RESULT-V1)
          /Hedge05FiringCondition (\getMacro{firingCondition})
        }
execute:
  freeze: false  # Pitfall 3 mitigation
  cache: false
---

# HEDGE-05 NULL RESULT — `r Sys.getenv("HEDGE05_FIRING_CONDITION")`

<!-- Visible signature for pdftotext grep; PDF metadata signature above for pdfinfo grep -->
HEDGE05-NULL-RESULT-V1

::: {.callout-warning}
This is a null-result deliverable per HEDGE-05 firing condition `{{< meta firing-condition >}}`.
Null results are valid completions, not failures, per project epistemics.
:::

# Disqualifying Evidence

```{python}
import json, os
evidence = json.loads(os.environ["HEDGE05_EVIDENCE_JSON"])
# ... render firing-condition-specific evidence block ...
```
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `statsmodels.distributions.copula` for BIC ranking | `copulae==0.8.0` | Phase 4 design (CONTEXT.md) | Single library, consistent API, 5-family menu pre-built. |
| `chi2(1).sf` for boundary LR test | Phase 3 already moved to 50:50 bootstrap mixture | Phase 3 Plan 03-03 | Phase 4 inherits the correct null distribution — no rework. |
| `nbconvert --to pdf` for report rendering | Quarto `.qmd` → LaTeX → PDF | CONTEXT.md Phase 4 lock | Native citations, cross-refs, templating, conditional content. |
| Hand-rolled stratified sampling for sensitivity | `scipy.stats.qmc.LatinHypercube` | Phase 4 design | scipy 1.17 native; deterministic via `seed=`. |
| Carr–Madan via `scipy.integrate.quad` | Carr–Madan via `np.fft.fft` | Phase 4 design (HEDGE-02 SC-3 escalation rule + grep gate) | FFT is 100× faster + correctly handles slow-decaying char functions with the 2^11/2^12 escalation. |
| Single-bivariate copula assumption | 5-family BIC + vine fallback gate | Phase 4 design (DEPEND-01) | Honest dependence inference; explicit BIC-based selection rule. |

**Deprecated/outdated:**

- `scipy.integrate.quad` for the Carr–Madan inversion → forbidden by grep gate; use FFT.
- `tick.HawkesExpKern.score()` for Hawkes log-likelihood → wrong probability space under LS fallback (Phase 3 03-02); use canonical `_hawkes_loglik_vectorized` import.
- `fit_report.json :: hawkes_mv_params :: loglik_in_sample_raw` field as a log-likelihood source → it's the raw LS objective; use canonical `loglik` field per Phase 3 Pattern F.

## Open Questions

1. **HEDGE-03 calibration source — "port" semantics need disambiguation**
   - What we know: CONTEXT.md says "methodological port from Hernandez Cruz 2024 Merton/Kou parameters" but verified that 2407.11716 doesn't publish jump-diffusion parameters; Wu & Liu 2026 uses QVAR not jump-diffusion.
   - What's unclear: where does the base triple `(λ, μ_J, σ_J)` come from? Stipulated from raw USDC tick data? Stipulated from literature range without primary-source citation? Stipulated from a different paper not in the CONTEXT.md citation list?
   - Recommendation: Plan 04-NN body MUST select one path: (a) derive from raw March-2023 USDC tick data (adds a data-fetch dependency to Phase 4 — out of scope per CONTEXT.md `<deferred>`); (b) accept a defensibly stipulated triple in `notes/usdt_depeg_calibration.md` with explicit "this is a stipulation, not a published-paper port" framing; (c) ask the user. The N=64 ±50% Latin hypercube sweep is an adequate honesty mitigation for any of (a)/(b) — but the "port" language must be replaced with "stipulation" if (b).

2. **DEPEND-01 substrate: residuals.parquet vs raw timestamps**
   - What we know: `residuals.parquet :: rescaled_dt` is exp(1)-distributed iid per leg under correct Hawkes; raw timestamps carry non-stationary baseline structure.
   - What's unclear: CONTEXT.md says "event-index lags" but doesn't say whether the variables are raw timestamps or rescaled residuals.
   - Recommendation: use `rescaled_dt` as the substrate (Pitfall 4 mitigation). Document choice in Plan 04-NN body; if the user prefers raw timestamps, switch to block-permutation (Politis-Romano).

3. **Vine copula fallback in 2D: dead-code or live-code?**
   - What we know: 2D vine reduces to bivariate + uniform marginals (CONTEXT.md `<deferred>` note acknowledges this).
   - What's unclear: should `pyvinecopulib==0.7.6` be installed in Plan 04-00 (eager, anticipating ΔBIC≥5 trigger) or in a follow-up plan (lazy, only if Wave-1 empirical fit triggers)?
   - Recommendation: lazy. Install in a follow-up plan IF AND ONLY IF Wave-1 empirical BIC produces a meaningful margin for vine. Otherwise the C++ binary dependency is dead weight + AF-12-adjacent.

4. **Latin hypercube N=64 cell-decision flip threshold**
   - What we know: CONTEXT.md says "If the gate decision flips on any cell, the result is surfaced as `sensitivity_fragile: true`."
   - What's unclear: "any cell" means any 1-of-64 flip → trivially triggers sensitivity_fragile under any non-deterministic gate. Is the intended semantics "any cell" (strict, sensitivity_fragile fires often) or "majority of cells" (loose)?
   - Recommendation: literal "any cell" per CONTEXT.md. The flag is informational, not gate-failing — Phase 5 PDF renders the cell table + flag side-by-side. Document this in Plan 04-NN body.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (already in analysis/pyproject.toml dev deps; per `analysis/pyproject.toml [tool.pytest.ini_options]`) |
| Config file | `analysis/pyproject.toml [tool.pytest.ini_options]` (testpaths = ["tests"], addopts = "-ra --strict-markers", pythonpath = ["src"]) |
| Quick run command | `cd analysis && uv run pytest tests/test_<module>.py -x` |
| Full suite command | `cd analysis && uv run pytest tests/` |
| Acceptance grid command | `make phase-4-acceptance` (planner adds Makefile target wrapping the grid) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| DEPEND-01 | 5-family BIC + cross-correlogram + permutation null produce `joint_dist.json` with all `REQUIRED_JOINT_DIST_KEYS` present | unit + integration | `cd analysis && uv run pytest tests/test_copula_bic.py tests/test_cross_correlogram.py tests/test_permutation_null.py tests/test_joint_dist_provenance.py -x` | ❌ Wave 0 |
| DEPEND-02 | Lint asserts `joint_dist.json` schema before Phase 5 build | lint | `make lint-artifacts` exits non-zero on malformed `joint_dist.json` | ❌ Wave 0 (lint-artifacts.py extension) |
| HEDGE-01 | Four-condition gate writes `gate_report.json` with each condition `{passed, evidence}`; SC-2 grep gate `grep -i "usdc" analysis/src/abrigo_x402/hedge/falsification.py` returns only comment hits | unit + grep | `cd analysis && uv run pytest tests/test_falsification.py -x && ! grep -i "^[^#]*usdc" analysis/src/abrigo_x402/hedge/falsification.py` | ❌ Wave 0 |
| HEDGE-02 | Carr–Madan strip on synthetic Gaussian fixture emits at 2^11; on fat-tail fixture escalates to 2^12 OR aborts to `strip_degenerate.json` | unit | `cd analysis && uv run pytest tests/test_carr_madan_strip.py -x` (must cover both escalation paths + abort path) | ❌ Wave 0 |
| HEDGE-03 | Latin hypercube N=64 sensitivity sweep around `(λ, μ_J, σ_J)` ±50% produces `gate_report :: usdt_depeg_basis_jump :: evidence :: sensitivity_summary` with N=64 cells | unit | `cd analysis && uv run pytest tests/test_usdt_depeg_lhs.py -x` | ❌ Wave 0 |
| HEDGE-04 | Three-way stress test produces `stress_report.json` with `{independence, fitted_joint, comonotone}` prices + `divergence_flag` set when spread/mean > 30% | unit + integration | `cd analysis && uv run pytest tests/test_stress_test.py -x` | ❌ Wave 0 |
| HEDGE-05 | All three firing-condition fixtures (`hedge_05_null_{cost,lr,convex}`) regenerate `reports/ichi.pdf` as null-result PDF; `pdftotext reports/ichi.pdf - \| grep HEDGE05-NULL-RESULT-V1` and `pdfinfo reports/ichi.pdf \| grep HEDGE05-NULL-RESULT-V1` both exit 0 | integration + grep | `cd analysis && uv run pytest tests/test_null_result_template.py -x` (parametrized over the three firing conditions) | ❌ Wave 0 (fixtures + .qmd template + render-null-result-pdf Makefile target) |
| ROADMAP SC-1 (Phase 4) | All four artifacts carry the 6-key PANEL-02 metadata header | unit | `make lint-artifacts` exit 0 on clean tree | ❌ Wave 0 (lint extension) |
| ROADMAP SC-2 (Phase 4) | `grep -i "usdc" analysis/src/abrigo_x402/hedge/falsification.py` returns only comment hits | grep gate | inline in test_falsification.py + pre-commit hook | ❌ Wave 0 |
| ROADMAP SC-3 (Phase 4) | Convergence-tested grid; abort-to-`strip_degenerate.json` after 2^12 fail | unit | included in test_carr_madan_strip.py | ❌ Wave 0 |
| ROADMAP SC-4 (Phase 4) | `stress_report.json` includes all three scenarios + divergence flag | unit | included in test_stress_test.py | ❌ Wave 0 |
| ROADMAP SC-5 (Phase 4) | HEDGE-05 template fires automatically; three fixture triplets verify | integration | included in test_null_result_template.py | ❌ Wave 0 |
| ROADMAP SC-6 (Phase 4) | USDT-depeg calibration documented in `notes/usdt_depeg_calibration.md` | manual + lint | `test -f notes/usdt_depeg_calibration.md && grep -q 'methodological_port\|stipulation' notes/usdt_depeg_calibration.md` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `cd analysis && uv run pytest tests/test_<changed_module>.py -x` (single-file run, ~10–30s)
- **Per wave merge:** `cd analysis && uv run pytest tests/ -x` (full Phase 2+3+4 suite — expected ~3–5 min wall-clock under thread-pinned BLAS)
- **Phase gate:** Full suite green + `make lint-artifacts` exit 0 + `make phase-4-acceptance` exit 0 before `/gsd:verify-work`

### Wave 0 Gaps

Plan 04-00 (Wave 0 scaffold) MUST land these BEFORE Wave-1 plans begin:

- [ ] **`notes/PRE_REGISTRATION.md` AF-03 amendment** — locks the 0.1% positivity tolerance. SOLO commit, predates all `analysis/src/abrigo_x402/hedge/*` commits (Pitfall 7). Suggested location: §Test Statistics, new sub-section "Carr–Madan Grid Numerical Tolerances."
- [ ] **`analysis/src/abrigo_x402/dependence/{__init__,cross_correlogram,permutation_null,copula}.py`** — module skeletons with canonical Wave-1 symbol names locked; `REQUIRED_JOINT_DIST_KEYS` tuple forward-declared.
- [ ] **`analysis/src/abrigo_x402/hedge/{__init__,falsification,carr_madan_strip,stress_test,usdt_depeg,null_result,orchestrator}.py`** — module skeletons; `REQUIRED_GATE_REPORT_KEYS`, `REQUIRED_STRESS_REPORT_KEYS`, `REQUIRED_STRIP_KEYS`, `STRIP_DEGENERATE_KEYS`, `HEDGE05_SIGNATURE` constants forward-declared.
- [ ] **`analysis/tests/test_{cross_correlogram,permutation_null,copula_bic,falsification,carr_madan_strip,stress_test,usdt_depeg_lhs,null_result_template,joint_dist_provenance,gate_report_provenance,stress_report_provenance,byte_identical_phase_4}.py`** — skip-marked stubs at canonical Wave-1 symbol surface.
- [ ] **`analysis/tests/conftest.py` extension** — add `joint_dist_fixture`, `gate_report_fixture`, `null_result_fixture_triplet` (parametrized over `["null_cost", "null_lr", "null_convex"]`) fixtures.
- [ ] **`analysis/tests/fixtures/hedge_05_{null_cost,null_lr,null_convex}/{fit_report.json, gate_report.json, cost_leg_bound.md}`** — three synthetic triplets, each forcing exactly one HEDGE-05 firing condition. Use `synthetic_nhpp_baseline_only.parquet` (Phase 3 fixture) as the substrate for `null_lr`; synthesize NHPP-only Hawkes adjacency for `null_convex`; hand-author `cost_leg_bound.md` with `verdict: FAIL` for `null_cost`.
- [ ] **`reports/_templates/null_result.qmd`** — Quarto template scaffold with dual signature markers (H1 + `pdfinfo` injection) + three conditional-content branches.
- [ ] **`scripts/lint_artifacts.py` extension** — add `JOINT_DIST_REQUIRED_KEYS`, `GATE_REPORT_REQUIRED_KEYS`, `STRESS_REPORT_REQUIRED_KEYS`, `STRIP_REQUIRED_KEYS`, `STRIP_DEGENERATE_REQUIRED_KEYS` frozensets + `lint_<artifact>_json` helpers + glob walkers per pattern.
- [ ] **`Makefile`** — extend `lint-artifacts` target to walk the five new JSON artifact patterns; add `render-null-result-pdf` + `render-strip-diagnostic` + `phase-4-acceptance` targets.
- [ ] **`analysis/pyproject.toml`** — add `copulae==0.8.0` to `[project] dependencies`; add `jupyter` to `[dependency-groups] dev`. Defer `pyvinecopulib==0.7.6` to a follow-up plan (lazy install — Pitfall 2 + Open Question 3).
- [ ] **System dependency install instructions** (`README.md` or `analysis/README.md`) — document `quarto` + `texlive-luatex` (or `quarto install tinytex`) install path.
- [ ] **Pre-commit hook extensions** (`.pre-commit-config.yaml`) — add SC-2 grep gate for `usdc` literals in `analysis/src/abrigo_x402/hedge/*.py` (excluding comment lines); add `scipy.integrate.quad` grep gate in `hedge/carr_madan_strip.py`; add `loglik_in_sample_raw` grep gate in `hedge/*`; add hardcoded-jump-diffusion-params grep gate.

## Sources

### Primary (HIGH confidence)

- **Phase 3 substrate (verified by direct file read):**
  - `analysis/src/abrigo_x402/dgp/orchestrator.py` — `REQUIRED_FIT_REPORT_KEYS` tuple (18 keys), canonical-LL contract, run_id derivation, PANEL-02 → SC-1 header
  - `analysis/src/abrigo_x402/dgp/lr_test.py` — `_hawkes_loglik_vectorized` + `_nhpp_pointprocess_loglik` exports (canonical-LL sources for Phase 4 condition-3 evidence)
  - `analysis/src/abrigo_x402/dgp/time_rescaling.py:build_residuals_dataframe` — `residuals.parquet` schema (leg, event_time, Lambda_at_event, rescaled_dt)
  - `analysis/src/abrigo_x402/provenance.py` — `with_header` + `assert_has_header` API (PANEL-02 reuse)
  - `scripts/lint_artifacts.py` — dual-track parquet + fit_report.json pattern; `_find_repo_root` walker; Pattern G enforcement
  - `analysis/tests/test_byte_identical.py` — Phase 3 Pattern I (thread-pin-before-import) verbatim template
  - `.planning/phases/03-dgp-estimation-l4-with-boundary-correct-lr-test/03-07-SUMMARY.md` — Pattern F/G/H establishment (canonical-LL contract; complete-artifact-on-failure; deterministic content-addressed run_id)
  - `.planning/phases/03-dgp-estimation-l4-with-boundary-correct-lr-test/03-08-SUMMARY.md` — Patterns I/J/K (thread-pinning; runtime sanity-guard; acceptance-grid format)
- **Project governance (verified by direct file read):**
  - `notes/PRE_REGISTRATION.md` — locked α=0.01, 1000-rep bootstrap, four-criterion gate, USDT condition-4 framing, AF-03 discipline
  - `notes/ROADMAP-EXTENSIONS.md` — v2.0 streaming-tokenization polymorphism guidance for Carr–Madan API
  - `.planning/research/PITFALLS.md` — §4 (boundary-correct LR), §5 (cross-leg dependence), §7 (Carr–Madan fat-tail / 2^11–2^12 grid sizing)
  - `.planning/research/CANDIDATES.md` — §6 Q6b + §7 thinness-retraction audit (Steer Iter-2 cost-leg STRADDLE = leading HEDGE-05 firing condition)
  - `.planning/REQUIREMENTS.md` — DEPEND-01/02 + HEDGE-01..05 acceptance criteria verbatim
  - `.planning/ROADMAP.md` §Phase 4 — six SC verbatim
  - `./CLAUDE.md` — USDT/USDC framing non-negotiable; git fork/upstream
- **Sibling-repo theory:**
  - `../abrigo-analytics/notes/SOMNIA_DRAFT.md` §FUNCTIONAL FORM — four convex-dominance conditions; condition 4 USDT reparameterization rationale; Carr–Madan replicating-strip derivation. **NOTE:** the upstream draft cites Hernandez Cruz 2024 + Wu & Liu 2026 as "Primary source" for condition 4 — verified these are evidence-of-event sources, NOT jump-diffusion calibration sources. See Pitfall 1.
- **Library docs (HIGH-MEDIUM, single-source-verified):**
  - [pyvinecopulib on PyPI](https://pypi.org/project/pyvinecopulib/) — confirmed 0.7.6 release 2026-05-07 with Python 3.9–3.14 wheels (Linux/macOS/Windows). HIGH.
  - [Copulas on PyPI](https://pypi.org/project/copulas/) — DataCebo's `copulas==0.14.1`, BUSL-1.1, Python 3.9–3.14. HIGH (license decision: prefer `copulae`).
  - [Copulae GitHub](https://github.com/DanielBok/copulae) — 0.8.0 supports Python 3.13 + numpy 2.x; 5-family set verified. MEDIUM (single-source via WebFetch).
  - [scipy.stats.qmc.LatinHypercube v1.17 manual](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.qmc.LatinHypercube.html) — signature, seed semantics, `qmc.scale()` for bounds mapping. HIGH.
  - [Quarto Computations: Python](https://quarto.org/docs/computations/python.html) — Python chunk execution requires `jupyter`. HIGH.
  - [Quarto Caching](https://quarto.org/docs/computations/caching.html) — `freeze:` semantics (Pitfall 3 source). HIGH.
  - [Quarto Troubleshooting](https://quarto.org/docs/troubleshooting/) — TeX install guidance (`quarto install tinytex` vs system `texlive`). HIGH.
  - [Quarto PDF Options](https://quarto.org/docs/reference/formats/pdf.html) — `pdf-engine`, `include-in-header` for custom `\pdfinfo` metadata injection. HIGH.

### Secondary (MEDIUM confidence)

- [Carr–Madan formula (Keith A. Lewis notes)](https://keithalewis.github.io/math/cm.html) — twice-differentiable payoff decomposition `f(x) = f(a) + f'(a)(x-a) + ∫(k-x)^+ f''(k)dk + ∫(x-k)^+ f''(k)dk`. Standard reference.
- [arxiv 1706.05935 — characteristic-function truncation under Bates](https://arxiv.org/pdf/1706.05935) — 2^11–2^12 grid points for 10^-10 accuracy. Cited in PITFALLS §7.
- [Ma et al. 2014 Carr–Madan static-replication algorithm](https://arxiv.org/pdf/1406.5430v1) — convergence analysis for nonlinear payoffs (PRE_REGISTRATION cites this as the Phase 4 Carr–Madan primary).
- [Bossu — Generalizations of the Carr-Madan spanning formula (NYU 2022)](https://bpb-us-e1.wpmucdn.com/wp.nyu.edu/dist/b/24047/files/2022/06/22-Sebastien-Bossu-20220604-NYU-FRE-Carr-Madan-Generalizations.pdf) — multi-dimensional payoff extensions (informs v2.0 stream-PV API design).

### Tertiary (LOW confidence — flagged for validation)

- **Hernandez Cruz 2024 (arxiv 2407.11716)** as a jump-diffusion-parameter source — **REFUTED by WebFetch verification**. The paper is a transparency/MCI study, not a jump-diffusion calibration. See Pitfall 1. Planner must NOT cite this as a "port" source in Plan 04-NN bodies without explicit disclaimer.
- **Wu & Liu 2026 (arxiv 2602.18820)** as a jump-diffusion-parameter source — **REFUTED by WebFetch verification**. The paper uses Quantile VAR, not jump-diffusion. See Pitfall 1.
- pyvinecopulib + copulae cross-library BIC comparison in 2D — Pitfall 2 hazard; no source verified the gap is small enough to be safe.

## Metadata

**Confidence breakdown:**

- Standard stack — **HIGH**. All library + version availability verified (PyPI WebFetch + scipy 1.17 manual). Single MEDIUM is copulae 0.8.0 Python 3.13 support (single-source via GitHub WebFetch).
- Architecture patterns — **HIGH**. Direct mirror of Phase 3 Patterns F/G/H/I/J/K, all verified in 03-07-SUMMARY.md and 03-08-SUMMARY.md.
- Pitfalls — **HIGH on substrate (1, 7, 8 are verified gaps/locks)**, **MEDIUM on FFT precision (5) and comonotone marginal-CDF choice (6)** — these are domain-best-practice rather than verified primary-source claims, but the choices are conservative.
- HEDGE-03 calibration source — **LOW on the "port" semantics; HIGH on the gap being real**. The CONTEXT.md "port from Hernandez Cruz 2024" wording is aspirational — the paper doesn't publish the required parameters. The planner needs to disambiguate; the N=64 ±50% sweep is an adequate honesty mitigation regardless of the source of the base triple.
- Quarto + PDF signature markers — **MEDIUM**. The pattern (visible H1 + `\pdfinfo` injection + `pdftotext`/`pdfinfo` grep verification) is plausible from Quarto docs but no Phase 3-style verified working example in the repo. First implementation; may need iteration.

**Research date:** 2026-05-27
**Valid until:** 2026-06-27 (30 days for stable library landscape; re-verify if any of `copulae`, `pyvinecopulib`, `scipy`, or `quarto` ship a major version in the interval).
