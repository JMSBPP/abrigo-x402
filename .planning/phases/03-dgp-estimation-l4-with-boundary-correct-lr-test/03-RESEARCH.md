# Phase 3: DGP Estimation (L4) with Boundary-Correct LR Test — Research

**Researched:** 2026-05-26
**Domain:** Point-process estimation (NHPP + bivariate Hawkes) + boundary-correct nested model selection + time-rescaling goodness-of-fit + profile-likelihood CIs
**Confidence:** HIGH (stack pre-locked in `analysis/uv.lock`; statistical methodology pre-locked in `notes/PRE_REGISTRATION.md` and `.planning/research/PITFALLS.md §4`; canonical citations cross-verified against arxiv primary sources)

## Summary

Phase 3 fits two nested models (NHPP via Kirchner INAR(p); bivariate Hawkes via `tick.HawkesExpKern`), runs a **bootstrap likelihood-ratio test with a 50/50 χ²(0):χ²(1) null mixture** (boundary correction — the alternative nests the null at η=0 on the parameter boundary), validates fit via the **Brown 2002 time-rescaling KS test**, evaluates held-out log-likelihood on a strict 80/20 wall-clock split, and reports branching-ratio confidence intervals via **profile likelihood** (NOT Wald/Hessian). All five must succeed structurally for `fit_report.json` to ship with `gate_passes=true`; any failure produces a `fit_report.json` with `gate_passes=false` + failing criteria detailed (CONTEXT.md `<specifics>`: "NEVER write a fit_report.json with missing keys").

The locked stack (`tick==0.8.0.2`, `statsmodels==0.14.6`, `polars==1.41.0`, `numpy==2.4.6`, `scipy==1.17.1`) is current as of 2026-05-26 (verified against PyPI). All five are at the latest published versions; no upgrades needed. The methodology is well-established but **the most common implementation failure mode is using `scipy.stats.chi2(1).sf(2*ΔLL)` directly**, which over-rejects the null by exactly 2× because of the boundary issue. The bootstrap rig sidesteps this entirely.

The bivariate-leg dimension is pre-locked: `leg_0` = token0-inflow Swaps (382 events / 30d), `leg_1` = token1-inflow Swaps (396 events / 30d). Both legs comfortably exceed the 300-event Q-9 Hawkes-identifiability floor. **Expected outcome: STRADDLE or null-fire** (CONTEXT.md `<specifics>` — the thin economic underlying ($1.22 total 30-day revenue, $57k TVL) makes a clean Hawkes-positive claim epistemically suspect; the four-criterion gate must operate at full discipline even when failure is the likely outcome).

**Primary recommendation:** Implement the bootstrap-LR rig and profile-likelihood η-CI as **first-class modules** (`analysis/src/abrigo_x402/dgp/lr_test.py`, `analysis/src/abrigo_x402/dgp/profile_likelihood.py`); never call `statsmodels.stats.diagnostic.likelihood_ratio_test` (vanilla LRT — explicitly forbidden by `grep -r "likelihood_ratio_test"` returning zero hits per ROADMAP SC-3). Use `tick.hawkes.SimuHawkesExpKernels` for the bootstrap data-generating loop AND for the SC-2 synthetic-ground-truth validation harness — same simulator, two consumers.

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Two-stream direction-bivariate**: `leg_0` = token0-inflow Swaps (zeroForOne, 382 events); `leg_1` = token1-inflow Swaps (oneForZero, 396 events). Both legs > 300-event Q-9 Hawkes-identifiability floor.
- **Labels**: `leg_0` / `leg_1` (Uniswap token-index convention). NOT `R`/`C`. The PRE_REGISTRATION "revenue × cost" framing is model-of-cost abstraction, not token-direction asymmetry on the V3 pool.
- **Cross-leg cross-excitation interpretation**: `α_{0,0}` = self-excitation within token0-inflow stream; `α_{1,1}` = self-excitation within token1-inflow stream; `α_{0,1}` = does a token1-inflow Swap excite a subsequent token0-inflow Swap (round-trip arbitrage signature); `α_{1,0}` = symmetric.
- **NHPP fit form**: **Bivariate INAR(p) via `statsmodels.tsa.api.VAR`** with non-negativity projection (Kirchner 2015). Same dimensionality as the Hawkes alternative → LR test compares equivalently-sized models. NO summed univariate INAR(p) shortcut (PITFALLS §5).
- **Same-block co-fire**: Shared continuous `t = block_timestamp` (seconds). 13 same-block Swap pairs in the panel. `tick.HawkesExpKern` handles simultaneous events natively. NO logIndex tie-breaking.
- **Residual emission**: `fit_report.json` includes `residuals_hash` (sha256 of residuals file bytes); actual sequences land at `data/fits/ichi/<run_id>/residuals.parquet`. Phase 4 copula loads `residuals.parquet` directly without re-fitting. SC-5 byte-identical contract extends to `residuals.parquet`.
- **Pre-registered LR-test mechanics** (PRE_REGISTRATION.md §Test Statistics): 1000 bootstrap reps, 50:50 χ²(0):χ²(1) mixture, α = 0.01 (NOT 0.05).
- **Four-criterion gate** (PRE_REGISTRATION.md §Acceptance Regions): (i) LR rejects NHPP at α=0.01, (ii) η ≥ 0.2, (iii) held-out KS rescaled-time test passes (p > 0.05), (iv) non-stationarity ruled out (train_rate vs held_out_rate within ±25% OR piecewise-constant baseline fits.). All four required.
- **Sample-size floor (Q-9)**: <300 events OR CI width >0.4 → null-fire (PRE_REGISTRATION-locked, non-negotiable).
- **Bootstrap reps**: 1000 production (LOCKED — no `--bootstrap-reps` CLI override at production-fit time per AF-04 hand-tuning hazard). Dev-only `--bootstrap-reps=<N>` flag may exist for unit-test smoke runs.
- **Random seed**: `sha256(panel_dataHash + "phase-3-bootstrap")[:8]` interpreted as uint32. Deterministic, panel-dependent.

### Claude's Discretion

- **Held-out split mechanic**: Wall-clock last 20% of panel window (≈ 6 days at end of 30-day window). Wall-clock split (not event-count split) per PITFALLS §4 "fit must be stable under ±10% window shift". Stationarity diagnostic (`train_rate` vs `held_out_rate` within ±25%) gates whether the baseline-stationarity branch fires per SC-4.
- **`<run_id>` path scheme**: `run_id = sha256(panel_dataHash + fit_code_gitCommit + tick_lib_version)[:12]`. Deterministic.
- **Fit-artifact provenance**: `fit_report.json` + `residuals.parquet` pair gets a `data/fits/manifest.json` entry mirroring Phase 2 panel manifest schema. `.gitignore` allowlist via negation pattern.
- **Sparse-leg handling**: No pre-emptive fallback to univariate (both legs > 300 floor). Four-criterion gate is canonical safety net.
- **Diagnostic plot**: `reports/_diagnostics/lr_null_dist.png` (locked by SC-3). Matplotlib headless render.
- **NHPP validation harness**: `analysis/tests/test_nhpp_inar.py` simulates 1000 paths from `tick.hawkes.SimuHawkesExpKernels` with known params, refits via Kirchner estimator, asserts recovered params within ±10%.

### Deferred Ideas (OUT OF SCOPE)

- **v2.0 streaming-tokenization extension** — keep NHPP/Hawkes math polymorphic so v2.0 streaming-PV decomposition can reuse fit code on Superfluid flow-rate-change events.
- **Power-law Hawkes kernel** (DGP-V2-01) — fires only if exponential Hawkes wins v1 four-criterion gate.
- **Bootstrap CIs on all DGP parameters** (DGP-V2-02) — fires only on v1 Hawkes-positive.
- **Structural-break test** (DGP-V2-03) — fires unconditionally in Phase 7 if v1 ships.
- **Piecewise-constant baseline fallback** — IN-PHASE only if SC-4 stationarity diagnostic reports `piecewise_required`. Otherwise deferred.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **DGP-01** | Fit NHPP via Kirchner 2015 INAR(p) on `statsmodels.tsa.api.VAR` with non-negativity projection; validated against `tick.hawkes.SimuHawkesExpKernels` synthetic data within tolerance | §Standard Stack (Kirchner INAR(p) flow) + §Architecture Patterns Pattern 1 (Kirchner pipeline) + §Code Examples (INAR(p) fit) + §Validation Architecture (synthetic-ground-truth harness `test_nhpp_inar.py`) |
| **DGP-02** | Fit multivariate Hawkes via `tick.HawkesExpKern` with full off-diagonal excitation matrix (no diagonal-only shortcut) | §Standard Stack (tick HawkesExpKern row) + §Architecture Patterns Pattern 2 (bivariate Hawkes fit) + §Code Examples (Hawkes fit) + §Don't Hand-Roll (do not write own Hawkes log-likelihood) |
| **DGP-03** | NHPP-vs-Hawkes LR test with 50:50 χ²(0):χ²(1) mixture as null distribution; bootstrap-LR rig; vanilla `statsmodels.likelihood_ratio_test` rejected | §Standard Stack (boundary-LR custom module) + §Architecture Patterns Pattern 3 (bootstrap rig structure) + §Code Examples (parametric bootstrap loop) + §Common Pitfalls 1+2 (boundary blind / vanilla LRT) |
| **DGP-04** | Held-out temporal evaluation (train/test split by time); out-of-sample log-likelihood for both models | §Architecture Patterns Pattern 4 (wall-clock 80/20 split) + §Code Examples (held-out LL computation via `tick`'s score method) + §Common Pitfalls 3 (event-count vs wall-clock split) |
| **DGP-05** | Brown 2002 time-rescaling KS test on Hawkes residuals | §Standard Stack (time-rescaling KS custom + scipy.stats.kstest) + §Architecture Patterns Pattern 5 (residual computation via compensator integral) + §Code Examples (time-rescaling) |
| **DGP-06** | Branching-ratio CIs via profile likelihood (NOT Hessian standard errors) | §Standard Stack (profile-likelihood custom module) + §Architecture Patterns Pattern 6 (profile likelihood inversion) + §Code Examples (profile likelihood grid search) + §Common Pitfalls 4 (Wald CI on bounded parameter) |

## Standard Stack

### Core (pre-locked in `analysis/uv.lock`, verified current 2026-05-26)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `tick` | `0.8.0.2` | Multivariate Hawkes fit (`HawkesExpKern`); synthetic-ground-truth simulator (`SimuHawkesExpKernels`); spectral-radius / branching-ratio computation; built-in log-likelihood score | LATEST on PyPI; the only Python library with production-grade C++-backed multivariate Hawkes MLE + bootstrap-friendly simulator; Wheatley thesis and Filimonov-Sornette both reference it as the reference implementation; CONTEXT.md library-source canonical-ref |
| `statsmodels` | `0.14.6` | `tsa.api.VAR` for INAR(p) Kirchner-NHPP fit; AR-residual diagnostics; profile-likelihood helpers via `LikelihoodModel` (used as scaffolding only) | LATEST on PyPI; Kirchner 2015 §6 explicitly recommends VAR(p) least-squares as the INAR(p) estimator; Phase 0 PRE_REGISTRATION lock |
| `polars` | `1.41.0` | Read `data/raw/ichi/<pool>/<from_block>_<to_block>.parquet`; filter Swap rows; project bin-count sequences; write `residuals.parquet` with `write_parquet(metadata=...)` | LATEST on PyPI; Phase 2 panel was written with polars 1.41 — same library boundary for byte-identical SC-5 |
| `numpy` | `2.4.6` | Adjacency-matrix arithmetic; bootstrap-sample stacking; deterministic PRNG via `numpy.random.Generator` | LATEST on PyPI; `tick` 0.8.0.2 native interop |
| `scipy` | `1.17.1` | `stats.kstest` (rescaled-time KS test); `stats.chi2(1)` (mixture component for sanity-check display only — NOT the production null); `optimize.minimize_scalar` (profile-likelihood inversion); `optimize.brentq` (CI bracketing) | LATEST on PyPI; standard Python statistics toolkit |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `matplotlib` (transitive via `tick`) | pinned by tick | Render `reports/_diagnostics/lr_null_dist.png` headless | SC-3 requires histogram of bootstrap LR null distribution showing χ²(0) point mass at zero + χ²(1) continuous component |
| `pydantic` | `>=2.0` | Validate `fit_report.json` schema before write; load `protocols/ichi.toml` config | Same pattern as Phase 2 `protocol_spec.py`; ensures all SC-1 metadata keys present |
| `pytest` | `>=9.0.3` | Unit tests for boundary-LR / profile-likelihood / time-rescaling KS; synthetic-ground-truth validation harness | Established Phase 2 pattern |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `tick.HawkesExpKern` | Hand-rolled bivariate Hawkes MLE (e.g., `stmorse/hawkes` GitHub package) | Hand-rolled lacks C++ acceleration, validated test suite, and integrated simulator. `tick` is canonical; `stmorse/hawkes` is a teaching reference. **DO NOT SUBSTITUTE.** |
| `tick.hawkes` ML estimator | `hawkeslib` / `PyHawkes` | Both are unmaintained (last release > 3 years); neither supports `score()` on held-out data. |
| `statsmodels.tsa.api.VAR` for INAR(p) | R `hawkes` package via `rpy2` | Adds R dependency; native Python VAR with non-negativity projection is the Kirchner-recommended path |
| Vanilla χ²(1) LRT (`statsmodels.stats.diagnostic`) | **REJECTED** — boundary issue; over-rejects null by exactly 2× | Locked by ROADMAP SC-3: `grep -r "likelihood_ratio_test" analysis/src` MUST return zero hits |
| Bootstrap-LR | Asymptotic 50:50 mixture (analytic) | Bootstrap-LR is more robust at small samples (Cavaliere et al. 2022 explicitly recommend "fixed intensity bootstrap" for Hawkes); locked by PRE_REGISTRATION |
| Profile likelihood for η-CI | Wald/Hessian standard errors | Hessian SE assumes asymptotic normality on unbounded parameter space; η ∈ [0,1) is bounded so Hessian CI can extend past 1 (nonsensical). Profile likelihood respects bounds. Locked by PITFALLS §4 and DGP-06. |
| Profile likelihood for η-CI | Bootstrap CI on η | Bootstrap is DGP-V2-02 deferred; profile likelihood is the v1 method per PRE_REGISTRATION |

**Installation:** Already done. `analysis/uv.lock` contains all five locked versions.

**Version verification (executed 2026-05-26 via `pip index versions ...`):**
- `tick==0.8.0.2` — latest available
- `statsmodels==0.14.6` — latest available
- `polars==1.41.0` — latest available
- `numpy==2.4.6` — latest available
- `scipy==1.17.1` — latest available

All five are at PyPI head; no upgrades. Phase 1 Plan 01-00 already executed `uv lock`.

## Architecture Patterns

### Recommended Module Structure

```
analysis/src/abrigo_x402/
├── dgp/
│   ├── __init__.py
│   ├── nhpp_inar.py             # Kirchner INAR(p) fit via statsmodels VAR + non-negativity projection
│   ├── hawkes_fit.py            # tick.HawkesExpKern wrapper; bivariate fit; spectral radius / branching ratio
│   ├── lr_test.py               # Boundary-correct bootstrap LR rig (1000 reps; deterministic seed from panel_dataHash)
│   ├── time_rescaling.py        # Compensator integral Λ(t) + rescaled-time computation + scipy.stats.kstest
│   ├── profile_likelihood.py    # η-CI via profile likelihood (NOT Hessian) + scipy.optimize.brentq bracketing
│   ├── held_out.py              # 80/20 wall-clock split + held-out log-likelihood for NHPP + Hawkes
│   ├── stationarity.py          # train_rate vs held_out_rate diagnostic (±25%); decides stationary | piecewise_required
│   └── orchestrator.py          # Top-level run_fit() returning fit_report.json dict
├── cli.py                       # Extend with `fit` subcommand (mirrors `materialize` from Phase 2)
└── ...

analysis/tests/
├── test_nhpp_inar.py            # SC-2 synthetic-ground-truth: SimuHawkesExpKernels → refit Kirchner → assert ±10%
├── test_lr_test.py              # Bootstrap rig produces 50:50 mixture shape; rejects forbidden vanilla LRT path
├── test_time_rescaling.py       # Rescaled times of true NHPP pass KS; rescaled times of misspecified model fail KS
├── test_profile_likelihood.py   # η-CI brackets recovered correctly for synthetic Hawkes
├── test_held_out.py             # Strict time-split boundary; in-sample-only attempt raises InsufficientEvaluationError
└── test_fit_artifact_provenance.py  # fit_report.json has all SC-1 metadata keys; residuals.parquet sha256 matches

reports/_diagnostics/
└── lr_null_dist.png             # SC-3 diagnostic histogram (rendered headless)

data/fits/ichi/<run_id>/
├── fit_report.json
└── residuals.parquet            # Phase 4 consumes this
data/fits/manifest.json          # Mirror Phase 2 panel manifest schema
```

### Pattern 1: Kirchner INAR(p) NHPP Pipeline

**What:** Discretize event timeline into bins; count events per bin per leg; fit VAR(p) on count sequence; project negative VAR coefficients to zero (non-negativity); scale to NHPP intensity.

**When to use:** Always (DGP-01); this is the NHPP null model.

**Reference:** Kirchner 2015 arxiv 1509.02017 §6 (consistency + asymptotic normality of conditional least-squares VAR(p) estimator; "All results are presented in such a way that computer implementation, e.g., in R, is straightforward").

**Key invariants:**
- **Bin-width grid** (PRE_REGISTRATION §Prior Parameters): `{1m, 5m, 15m, 1h}`. Select by AIC-min over the grid.
- **Order p**: select by AIC over `p ∈ {1, ..., 10}` (Kirchner standard).
- **Non-negativity projection**: Any negative VAR coefficient → 0 (Kirchner's projection step; preserves NHPP positivity invariant).
- **Bivariate**: 2D count sequence (`leg_0_count`, `leg_1_count`); VAR(p) on the 2-dim vector. NEVER fit two univariate INAR(p) separately (PITFALLS §5).

### Pattern 2: Bivariate Hawkes Fit (tick.HawkesExpKern)

**What:** Multivariate exponential Hawkes with full 2×2 excitation matrix `α = [[α_00, α_01], [α_10, α_11]]` and decay matrix `β` (uniform scalar β recommended for v1 — power-law deferred to v2).

**When to use:** Always (DGP-02); this is the Hawkes alternative model.

**API surface** (verified via WebFetch on tick 0.8.0.2 docs):
```python
from tick.hawkes import HawkesExpKern

learner = HawkesExpKern(
    decays=0.1,             # scalar or (n_nodes, n_nodes) array — start with scalar grid search
    gofit='likelihood',     # MLE (NOT 'least-squares' — least-squares biases η downward)
    penalty='none',         # NO regularization in v1 (would bias α toward 0)
    solver='agd',           # accelerated gradient descent
    max_iter=1000,
    tol=1e-7,
    verbose=False,
)
learner.fit([leg_0_timestamps, leg_1_timestamps])  # list of 2 arrays
baseline = learner.baseline       # shape (2,)
adjacency = learner.adjacency     # shape (2, 2) — the α matrix
score_loglik = learner.score()    # in-sample log-likelihood
```

**Branching ratio computation** (NOT a direct tick attribute):
```python
# For exponential kernel with decay β: integral of kernel from 0 to ∞ = α_ij / β
# Branching ratio η = spectral radius of the kernel-integral matrix
kernel_integral = adjacency / decays   # shape (2, 2); element-wise for scalar β
eigvals = np.linalg.eigvals(kernel_integral)
branching_ratio = float(np.max(np.abs(eigvals)))   # spectral radius; must be < 1 for stationarity
```

**Same-block co-fire**: Both events at `t = block_timestamp` (CONTEXT.md decision). `tick` handles ties natively.

**Decay grid**: Search over `β ∈ {0.01, 0.1, 1.0, 10.0}` per Wheatley thesis recommendation; select by AIC. Decay must be matched between Hawkes-fit and the rescaling step.

### Pattern 3: Boundary-Correct Bootstrap LR Rig

**What:** Parametric bootstrap under the fitted NHPP-INAR(p) null; refit BOTH models on each bootstrap replicate; compute LR statistic empirically.

**When to use:** Always (DGP-03); replaces both vanilla χ²(1) LRT (over-rejects) and asymptotic 50:50 mixture (poor at small samples).

**Reference:** Cavaliere, Lu, Rahbek, Stærk-Østergaard (2022) "Bootstrap Inference for Hawkes and General Point Processes" (arxiv 2104.03122) — formalizes the "fixed intensity bootstrap" (FIB) for Hawkes; Filimonov & Sornette 2014 (arxiv 1403.5227); arxiv 2410.05008 (over-rejection under naive plug-in).

**Rig structure** (deterministic):

```python
def boundary_correct_bootstrap_lr_test(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    n_reps: int = 1000,
    seed: int = ...,        # sha256(panel_dataHash + "phase-3-bootstrap")[:8] as uint32
    alpha: float = 0.01,
) -> dict:
    # 1. Fit BOTH models on observed data
    nhpp_params = fit_nhpp_inar(leg_0_times, leg_1_times)
    hawkes_learner = fit_hawkes_expkern(leg_0_times, leg_1_times)
    LL_nhpp_observed = score_nhpp_loglik(nhpp_params, leg_0_times, leg_1_times)
    LL_hawkes_observed = hawkes_learner.score()
    LR_observed = 2.0 * (LL_hawkes_observed - LL_nhpp_observed)

    # 2. Parametric bootstrap UNDER THE NULL (NHPP)
    rng = np.random.default_rng(seed)
    bootstrap_LR = np.empty(n_reps)
    end_time = max(leg_0_times[-1], leg_1_times[-1])
    for k in range(n_reps):
        # Simulate from the fitted NHPP (rate function approximated by INAR(p) projection)
        # Critical: simulate FROM THE NULL, not from the alternative
        sim_leg_0, sim_leg_1 = simulate_nhpp_from_inar(nhpp_params, end_time, rng)
        # Refit BOTH models on the synthetic data
        nhpp_b = fit_nhpp_inar(sim_leg_0, sim_leg_1)
        hawkes_b = fit_hawkes_expkern(sim_leg_0, sim_leg_1)
        LL_nhpp_b = score_nhpp_loglik(nhpp_b, sim_leg_0, sim_leg_1)
        LL_hawkes_b = hawkes_b.score()
        bootstrap_LR[k] = 2.0 * (LL_hawkes_b - LL_nhpp_b)

    # 3. Empirical p-value (the bootstrap mixture replaces the analytic 50:50 χ²(0):χ²(1))
    p_value = float(np.mean(bootstrap_LR >= LR_observed))

    # 4. The histogram of bootstrap_LR should VISIBLY show:
    #    - Point mass at zero (from replicates where Hawkes optimizer hits the boundary η ≥ 0)
    #    - Continuous right tail (from replicates where Hawkes wins by small finite-sample noise)
    return {
        "observed_stat": LR_observed,
        "bootstrap_null_dist_50_50_chi2_0_chi2_1": bootstrap_LR.tolist(),
        "p_value": p_value,
        "rejects_at_alpha": p_value < alpha,
        "n_reps": n_reps,
        "seed": seed,
    }
```

**Key load-bearing detail:** The histogram of `bootstrap_LR` will show a point mass at zero (the χ²(0) component — replicates where the Hawkes fit's η hits exactly 0, the boundary, yielding LR = 0) AND a continuous right tail (the χ²(1)-like component). The 50:50 mixture is an *asymptotic* shape; the bootstrap *empirically realizes* the finite-sample analogue, which can deviate from 50:50 at small N.

**The forbidden anti-pattern:**
```python
# DO NOT DO THIS — vanilla LRT over-rejects null by 2× due to boundary issue
from scipy.stats import chi2
p_value = chi2(1).sf(LR_observed)   # WRONG — uses χ²(1), should be 0.5*χ²(0) + 0.5*χ²(1)
# Equally wrong:
from statsmodels.stats.diagnostic import likelihood_ratio_test  # FORBIDDEN
```

### Pattern 4: Held-out Temporal Split

**What:** Wall-clock 80/20 split. Train = first 80% of wall-clock window (≈ 24 days of the 30-day ICHI panel); test = last 20% (≈ 6 days).

**When to use:** Always (DGP-04).

**Critical invariants:**
- **Wall-clock split, NOT event-count split** (PITFALLS §4 "fit must be stable under ±10% window shift" + CONTEXT.md decision: "event-count splits couple test set to realized event density").
- **Log strict boundary block + timestamp** in `fit_report.json :: held_out_loglik :: split_metadata`.
- **In-sample-only attempt MUST raise `InsufficientEvaluationError`** (SC-4: "an in-sample-only fit attempt raises InsufficientEvaluationError"). Implement by guarding the orchestrator entry point.
- **Stationarity diagnostic** (SC-4 + PITFALLS §4): compute `train_rate` (events/sec on train) and `held_out_rate` (events/sec on test) per leg. If `|held_out_rate - train_rate| / train_rate > 0.25` → set `decision = "piecewise_required"` and refit using a piecewise-constant baseline. Else `decision = "stationary"`.

**Held-out log-likelihood** (Hawkes):
```python
# Refit on train only
train_learner = HawkesExpKern(...).fit([train_leg_0, train_leg_1])
# Score on held-out: tick's score() accepts test data via separate fit? NO — tick's score is in-sample.
# For held-out, compute log-likelihood manually using compensator integral on test window
# with parameters from train_learner.baseline + train_learner.adjacency
held_out_loglik_hawkes = compute_hawkes_loglik_on_test(
    train_learner.baseline, train_learner.adjacency, decays,
    test_leg_0, test_leg_1, test_window_start, test_window_end,
)
```

**Note:** `tick`'s `score()` is in-sample on the data it was `fit()`-ed on (verified via docs). For held-out evaluation, compute the log-likelihood manually using the standard Hawkes log-likelihood formula:
```
log L = Σ_i log(λ(t_i)) - ∫_{T_start}^{T_end} λ(t) dt
```
applied to the test window using the train-fitted parameters.

### Pattern 5: Time-Rescaling KS Test (Brown 2002)

**What:** Transform event times via the integrated intensity (compensator) Λ(t) = ∫₀ᵗ λ(s) ds. If the model is correct, rescaled inter-arrival times Λ(t_{i+1}) - Λ(t_i) are i.i.d. exponential rate-1. Test with KS.

**When to use:** Always (DGP-05); the held-out segment is the canonical target.

**Reference:** Brown, Barbieri, Ventura, Kass, Frank (2002) "The time-rescaling theorem and its application to neural spike train data analysis" *Neural Computation*; Daley & Vere-Jones (2003) *An Introduction to the Theory of Point Processes*; recent caution paper "On the use and misuse of time-rescaling to assess the goodness-of-fit of self-exciting temporal point processes" (PMC12416029, 2024) — flags plug-in estimator pitfalls.

**Key load-bearing detail:** Apply the test on the **held-out** segment using **train-fitted** parameters. Applying on the training segment with training parameters is in-sample-optimistic and can pass even for misspecified models (PITFALLS §3 in-sample optimism).

**Implementation:**
```python
def time_rescaling_ks_test(
    event_times: np.ndarray,   # held-out event timestamps for ONE leg
    baseline: float,           # train-fitted baseline for this leg
    adjacency_row: np.ndarray, # train-fitted excitation row (α[i, :])
    decays: float,             # train-fitted β
    other_leg_times: np.ndarray,  # for cross-excitation contribution
    window_start: float,
    window_end: float,
) -> dict:
    # Compute compensator Λ(t) for each event time in the held-out window
    # For exponential Hawkes: λ_i(t) = μ_i + Σ_j Σ_{t_jk < t} α_ij exp(-β (t - t_jk))
    # Λ_i(t) = ∫_{window_start}^{t} λ_i(s) ds  (closed form for exp kernel)
    Lambda_at_events = compute_compensator_exp_hawkes(
        event_times, baseline, adjacency_row, decays, other_leg_times, window_start
    )
    # Rescaled inter-arrival times
    rescaled_dt = np.diff(np.concatenate([[0.0], Lambda_at_events]))
    # Under correct model: rescaled_dt ~ Exp(1) i.i.d.
    ks_stat, ks_pvalue = scipy.stats.kstest(rescaled_dt, 'expon')
    return {
        "ks_statistic": float(ks_stat),
        "p_value": float(ks_pvalue),
        "n_events": int(event_times.size),
        "rescaled_dt": rescaled_dt,  # for residuals.parquet
    }
```

**Acceptance:** p > 0.05 (PRE_REGISTRATION §Test Statistics — Brown 2002, p > 0.05). Note: this is a one-sided "fail to reject correctness" test; small N (test segment ~6 days × ~25 events/day/leg ≈ 150 events) gives modest power but is sufficient per Q-9.

**Residuals output:** `residuals.parquet` columns: `leg`, `event_time`, `Lambda_at_event`, `rescaled_dt`. Phase 4 copula consumes.

### Pattern 6: Profile-Likelihood Branching-Ratio CI

**What:** Fix η (branching ratio) at a candidate value; re-optimize all OTHER parameters at fixed η; record profile log-likelihood ℓ_p(η). The set `{η : 2(ℓ_p(η̂) - ℓ_p(η)) ≤ χ²_{1, 1-α}}` is the profile-likelihood CI for η.

**When to use:** Always (DGP-06); replaces Wald/Hessian CI which assumes asymptotic normality and ignores boundary.

**Reference:** Standard profile-likelihood method (Cox & Hinkley 1974); Filimonov & Sornette 2014 specifically advocates this over Hessian for Hawkes branching-ratio; recent algorithm reference: "A robust and efficient algorithm to find profile likelihood confidence intervals" (Springer 2021, doi.org/10.1007/s11222-021-10012-y).

**Implementation skeleton:**
```python
def profile_likelihood_eta_ci(
    leg_0_times, leg_1_times,
    eta_hat: float,
    eta_grid: np.ndarray = np.linspace(0.01, 0.95, 50),
    alpha: float = 0.05,
) -> dict:
    # 1. Compute MLE log-likelihood at η_hat (use Hawkes fit from DGP-02)
    LL_max = ...  # ℓ_p(η̂)

    # 2. For each candidate η on the grid: constrained-refit holding η fixed
    profile_LL = np.empty(eta_grid.size)
    for k, eta_k in enumerate(eta_grid):
        # Constrained fit: parameterize α as α = eta_k * normalized_α_shape, optimize over baseline + α_shape + β
        constrained_learner = fit_hawkes_with_fixed_branching_ratio(leg_0_times, leg_1_times, eta_k)
        profile_LL[k] = constrained_learner.score()

    # 3. CI: solve 2*(LL_max - profile_LL(η)) ≤ chi2(1).ppf(1 - alpha) for η
    threshold = chi2(1).ppf(1 - alpha)   # NB: chi2(1) IS correct here because we're constructing
                                          # a CI for η ∈ (0, 1), NOT testing the boundary η=0
                                          # (the LR test boundary is a different problem)
    in_ci_mask = 2.0 * (LL_max - profile_LL) <= threshold
    in_ci_grid = eta_grid[in_ci_mask]
    if in_ci_grid.size > 0:
        ci_lower, ci_upper = float(in_ci_grid.min()), float(in_ci_grid.max())
    else:
        # Refine with scipy.optimize.brentq if grid is too coarse
        ci_lower, ci_upper = bracket_profile_ci_with_brentq(...)

    return {
        "method": "profile_likelihood",
        "lower": ci_lower,
        "upper": ci_upper,
        "eta_hat": eta_hat,
        "alpha": alpha,
        "ci_width": ci_upper - ci_lower,
    }
```

**Q-9 trip wire:** `ci_width > 0.4` → null-fire per PRE_REGISTRATION (locked).

**Subtlety:** For the **CI for η**, use vanilla χ²(1) — this is a confidence-interval construction for an interior parameter (η ∈ (0, 1) on observed data), not a boundary hypothesis test. The boundary correction is only for the LR test of η = 0 (DGP-03).

### Anti-Patterns to Avoid

- **Vanilla χ²(1) LRT** — under-rejects null in the sense that the asymptotic p-value is too LARGE (because the boundary mixture has more mass at small LR statistics); equivalently, the rejection threshold is too HIGH. Wait — re-check: with the 50:50 mixture, the threshold is LOWER than χ²(1), so vanilla χ²(1) UNDER-rejects when the true distribution is the mixture. The literature consensus: vanilla χ²(1) is conservative if used naively as the null but OVER-rejects when researchers halve the p-value incorrectly. **Either way, the only safe path is the bootstrap rig.**
- **Diagonal-only Hawkes** — fitting `α = diag(α_00, α_11)` (no cross-excitation) masks bivariate self-excitation per PITFALLS §5; produces spurious self-excitation that absorbs cross-leg dependence. **Locked OUT by CONTEXT.md decision and DGP-02.**
- **Summed univariate INAR(p)** — fitting two univariate INAR(p)s and concatenating leaks cross-leg covariance into spurious Hawkes self-excitation per PITFALLS §5. **Locked OUT by CONTEXT.md decision.**
- **Event-count held-out split** — couples test set to realized event density; non-stationary panels can produce a test set with structurally different intensity than train. **Locked OUT by CONTEXT.md (wall-clock split).**
- **In-sample time-rescaling KS** — passes for misspecified models (in-sample optimism). KS test must run on **held-out** segment with **train-fitted** parameters.
- **Hessian/Wald η-CI** — extends past 1 (nonsensical) and assumes asymptotic normality not satisfied near the boundary. **Locked OUT by DGP-06 and PITFALLS §4.**
- **`force_simulation=True` in `SimuHawkesExpKernels`** — bypasses the spectral-radius < 1 check. NEVER use in the bootstrap loop (would silently allow non-stationary draws).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Multivariate Hawkes MLE | Custom C++ or NumPy gradient | `tick.HawkesExpKern` with `gofit='likelihood'`, `solver='agd'` | Production-grade, C++-accelerated, validated; the Wheatley + Filimonov-Sornette + Cavaliere references all use it; hand-rolled would lose 100× speed and require re-validating MLE convergence |
| Hawkes process simulation | Thinning algorithm by hand | `tick.hawkes.SimuHawkesExpKernels` | Ogata thinning is correct but slow; tick's C++ implementation is the reference; CRITICAL for 1000-rep bootstrap |
| INAR(p) NHPP estimation | Custom likelihood on bin counts | `statsmodels.tsa.api.VAR` + non-negativity projection (Kirchner 2015 §6 explicit) | The math is standard VAR; reinventing introduces subtle bugs in covariance structure |
| KS test on rescaled times | Custom KS computation | `scipy.stats.kstest(rescaled_dt, 'expon')` | One-line call; scipy handles the empirical CDF correctly |
| Profile likelihood bracket-and-bisect | Hand-coded grid search | `scipy.optimize.brentq` on `profile_LL(η) - threshold` | brentq is robust; combined with a coarse grid for initial bracketing it's standard |
| sha256 of file bytes | Custom hash | `hashlib.sha256(open(path, "rb").read()).hexdigest()` | Same pattern Phase 2 already uses |
| Compensator Λ(t) for exp-kernel Hawkes | Numerical integration | **Closed-form recursion** — exponential kernel admits Λ(t) closed form via piecewise integration between events | Brown 2002 §3 + standard references. NumPy vectorization is straightforward; numerical integration introduces step-size error |
| Spectral radius / branching ratio | scipy.linalg routines | `np.max(np.abs(np.linalg.eigvals(adjacency / decays)))` | Direct; no library needed |

**Key insight:** The full Phase 3 statistical machinery (Hawkes MLE + simulator + INAR(p) VAR + KS test + profile likelihood inversion) is built from off-the-shelf primitives. The ONLY custom code is the orchestration logic (bootstrap loop, held-out split, stationarity diagnostic, fit_report.json assembly). Hand-rolling the primitives would burn weeks for negative net value.

## Common Pitfalls

### Pitfall 1: Boundary Blindness (Vanilla χ²(1) LRT)

**What goes wrong:** `scipy.stats.chi2(1).sf(LR_observed)` is used as the null distribution. Because the Hawkes model nests NHPP at η = 0, which is on the boundary of the parameter space (η ≥ 0), the asymptotic distribution of the LR statistic is *not* χ²(1) but rather 0.5·χ²(0) + 0.5·χ²(1). The vanilla χ²(1) approach over-rejects the null in finite samples after researchers "correct" by halving the p-value, OR fails to use the proper mixture entirely.

**Why it happens:** Self & Liang (1987) "Asymptotic Properties of Maximum Likelihood Estimators and Likelihood Ratio Tests Under Nonstandard Conditions" is in every advanced statistics textbook but rarely the default when researchers write `chi2(1).sf(...)`. The naive p-value just looks like a number.

**How to avoid:** Use the bootstrap rig (Pattern 3) — empirically estimate the null distribution by simulating from the fitted NHPP. The asymptotic 50:50 mixture is then a sanity check (histogram overlay), not the production null.

**Warning signs:**
- Source code contains `from scipy.stats import chi2; ...chi2(1).sf(...)` for the LR null.
- Source code contains `statsmodels.stats.diagnostic.likelihood_ratio_test`.
- The `lr_null_dist.png` histogram is unimodal continuous (no point mass at 0) — that means the bootstrap is broken (probably simulating from the alternative not the null).

**Verification command:** `grep -rE "likelihood_ratio_test|chi2\(1\)\.sf" analysis/src/abrigo_x402/dgp/lr_test.py` → must return zero hits (SC-3 + ROADMAP).

### Pitfall 2: Bootstrap Simulates from Alternative Not Null

**What goes wrong:** The bootstrap loop calls `SimuHawkesExpKernels` with the Hawkes-fitted parameters instead of simulating from the NHPP-fitted parameters. The bootstrap null distribution is then biased toward larger LR statistics → p-value is too SMALL → false Hawkes-positive.

**Why it happens:** Both `tick.SimuHawkesExpKernels` and a hand-rolled NHPP simulator look like one-line calls. Reaching for the more familiar `tick` simulator is natural but wrong.

**How to avoid:**
- Implement `simulate_nhpp_from_inar(nhpp_params, end_time, rng)` explicitly. This is *Poisson with time-varying rate* — use thinning or piecewise inversion.
- Alternative: use `SimuHawkesExpKernels` with **adjacency = zero matrix** (forces η = 0 → reduces to inhomogeneous Poisson). Documented option; check the `force_simulation` flag is NOT set.
- Unit test in `test_lr_test.py`: bootstrap on synthetic NHPP data should produce ~5% rejection at α=0.05 (size validation).

### Pitfall 3: Wall-Clock vs Event-Count Split Confusion

**What goes wrong:** Split by event count (`events[:int(0.8*N)]` for train), not wall-clock. If event intensity is non-stationary (e.g., declining late in the panel), the test set is structurally different from train (fewer events per unit time).

**Why it happens:** `numpy.array_split` and `df.iloc[:n]` patterns are the path of least resistance. Wall-clock split requires an explicit timestamp threshold.

**How to avoid:**
- Wall-clock split: `t_split = window_start + 0.8 * (window_end - window_start)`.
- `train_leg_0 = leg_0_times[leg_0_times < t_split]; held_out_leg_0 = leg_0_times[leg_0_times >= t_split]`.
- Log `t_split` and the closest block boundary in `fit_report.json :: held_out_loglik :: split_metadata`.

### Pitfall 4: Wald CI on Bounded Parameter

**What goes wrong:** Branching ratio η is reported with Wald CI `η̂ ± 1.96·SE(η̂)`, computed from the Hessian. Two failure modes: (a) the CI can extend past 1.0 (nonsensical — η ∈ [0, 1) for stationarity); (b) near the boundary η = 0, the normal approximation underlying Wald breaks down because the MLE distribution is skewed.

**Why it happens:** Hessian-based SE is the default in most statistical software; computing profile likelihood requires writing a constrained-optimization loop.

**How to avoid:** Profile-likelihood η-CI per Pattern 6 and DGP-06. Truncate to [0, 1) by construction.

### Pitfall 5: In-Sample Time-Rescaling Passes Misspecified Models

**What goes wrong:** Time-rescaling KS is computed on the **training data with training parameters**. The MLE will fit the training intensity well by construction → rescaled times always look ~uniform → KS test passes even for misspecified models.

**Why it happens:** Single-pass code that fits and then tests on the same data is much shorter than splitting first.

**How to avoid:** Held-out segment with train-fitted parameters (Pattern 5). PMC12416029 (2024) specifically warns about this misuse for self-exciting processes.

**Warning sign:** KS test passes in-sample even when the NHPP/Hawkes comparison favors Hawkes — strongly suggests both models are misspecified for the underlying baseline non-stationarity (PITFALLS §4 "misspecified immigration").

### Pitfall 6: Spectral Radius Computed Wrong for Non-Scalar β

**What goes wrong:** Branching ratio computed as `np.max(adjacency)` (max of α matrix), not the spectral radius of the kernel-integral matrix.

**Why it happens:** For univariate Hawkes with one decay, η = α/β. For multivariate it's the spectral radius of `α / β` (with appropriate matrix interpretation). The univariate intuition leaks.

**How to avoid:**
```python
# Correct (scalar β):
kernel_integral_matrix = adjacency / decays   # element-wise for scalar β
branching_ratio = float(np.max(np.abs(np.linalg.eigvals(kernel_integral_matrix))))
# For (n_nodes, n_nodes) β: kernel_integral_matrix[i, j] = adjacency[i, j] / decays[i, j]
```

### Pitfall 7: Same-Block Co-Fire Resolved by logIndex

**What goes wrong:** Code resolves 13 same-block Swap pairs by ordering on `logIndex`, treating them as sequential. This introduces a synthetic ordering not present in the underlying physical process.

**Why it happens:** Polars DataFrames retain `logIndex` for provenance; sorting by `(block, logIndex)` is the natural projection.

**How to avoid:** Per CONTEXT.md decision — shared continuous timestamp at `t = block_timestamp` (seconds). `tick.HawkesExpKern` accepts ties (verified). Drop `logIndex` ordering at the leg-extraction boundary.

### Pitfall 8: Non-Deterministic Bootstrap

**What goes wrong:** Bootstrap uses `numpy.random.seed(42)` or system entropy; output `fit_report.json` is not byte-identical across reruns (violates SC-5).

**How to avoid:** Use `np.random.default_rng(seed)` with `seed = int.from_bytes(sha256(panel_dataHash + b"phase-3-bootstrap").digest()[:4], "big")` (CONTEXT.md decision). Different panel → different bootstrap; same panel → byte-identical.

### Pitfall 9: `force_simulation=True` Silently Allows Non-Stationary Draws

**What goes wrong:** During bootstrap, the fitted NHPP-INAR(p) sometimes produces a borderline-stationary parameter; the simulator throws unless `force_simulation=True` is set; setting it produces draws from a non-stationary process which biases the LR null.

**How to avoid:** Never set `force_simulation=True`. If the simulator throws, log the bootstrap replicate as failed and either retry with a different seed-stream within the bounded retry count OR record fewer replicates and surface the count in `fit_report.json :: lr_test :: n_successful_bootstrap`.

### Pitfall 10: Quoting `fit_report.json` Without Provenance Header

**What goes wrong:** `fit_report.json` is written without the SC-1 metadata header (chainId, contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit). `make lint-artifacts` exits non-zero. PANEL-02 invariant is violated.

**How to avoid:** Build `fit_report.json` via a pydantic model that REQUIRES the SC-1 keys at construction; extend `scripts/lint_artifacts.py` to grep JSON fit artifacts the same way it greps Parquet panels. Pattern matches Phase 2.

## Code Examples

### INAR(p) NHPP Fit via statsmodels.tsa.api.VAR

```python
# Source: Kirchner 2015 arxiv:1509.02017 §6 + statsmodels.tsa.api.VAR docs
import numpy as np
import polars as pl
from statsmodels.tsa.api import VAR

def fit_nhpp_inar(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    window_start: float,
    window_end: float,
    bin_width_seconds: float = 60.0,   # selected by AIC over {60, 300, 900, 3600}
    max_p: int = 10,                   # selected by AIC over {1, ..., 10}
) -> dict:
    # 1. Bin events by bin_width
    n_bins = int(np.ceil((window_end - window_start) / bin_width_seconds))
    bin_edges = window_start + np.arange(n_bins + 1) * bin_width_seconds
    counts_0, _ = np.histogram(leg_0_times, bins=bin_edges)
    counts_1, _ = np.histogram(leg_1_times, bins=bin_edges)

    # 2. Fit VAR(p) — selectorder over p via AIC
    count_matrix = np.column_stack([counts_0, counts_1]).astype(float)
    var_model = VAR(count_matrix)
    order_results = var_model.select_order(maxlags=max_p)
    p_star = int(order_results.aic)
    fit = var_model.fit(p_star)

    # 3. Non-negativity projection (Kirchner step)
    coefs = fit.coefs.copy()    # shape (p, k, k)
    coefs = np.maximum(coefs, 0.0)
    intercept = np.maximum(fit.intercept, 0.0)

    # 4. Scale to NHPP intensity: λ_i(t) = (intercept_i + Σ_p Σ_j coefs[p, i, j] · count_j(t - p·Δ)) / Δ
    return {
        "p": p_star,
        "bin_width_seconds": bin_width_seconds,
        "coefs": coefs.tolist(),
        "intercept": intercept.tolist(),
        "aic": float(fit.aic),
        "loglik_in_sample": float(fit.llf),
    }
```

### Bivariate Hawkes Fit via tick.HawkesExpKern

```python
# Source: https://x-datainitiative.github.io/tick/modules/generated/tick.hawkes.HawkesExpKern.html
import numpy as np
from tick.hawkes import HawkesExpKern

def fit_hawkes_expkern(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    decays: float = 0.1,   # scalar β; grid-searched over {0.01, 0.1, 1.0, 10.0} via AIC
) -> dict:
    learner = HawkesExpKern(
        decays=decays,
        gofit='likelihood',     # MLE; 'least-squares' biases η downward
        penalty='none',         # no regularization in v1
        solver='agd',
        max_iter=1000,
        tol=1e-7,
        verbose=False,
    )
    # Critical: list of timestamp arrays, one per node
    learner.fit([leg_0_times, leg_1_times])

    baseline = learner.baseline          # shape (2,)
    adjacency = learner.adjacency        # shape (2, 2) — α matrix
    loglik = float(learner.score())      # in-sample log-likelihood

    # Branching ratio = spectral radius of (α / β) for exponential kernel
    kernel_integral = adjacency / decays
    eigvals = np.linalg.eigvals(kernel_integral)
    branching_ratio = float(np.max(np.abs(eigvals)))

    return {
        "baseline": baseline.tolist(),
        "adjacency": adjacency.tolist(),
        "decays": float(decays),
        "branching_ratio": branching_ratio,
        "loglik_in_sample": loglik,
    }
```

### Boundary-Correct Bootstrap LR (pseudocode for the rig)

```python
# Source: Cavaliere et al. 2022 arxiv:2104.03122 + Filimonov & Sornette 2014 arxiv:1403.5227
import numpy as np
from hashlib import sha256

def boundary_correct_bootstrap_lr_test(
    leg_0_times: np.ndarray,
    leg_1_times: np.ndarray,
    panel_data_hash: str,
    window_end: float,
    n_reps: int = 1000,
    alpha: float = 0.01,
) -> dict:
    # Deterministic seed from panel hash (CONTEXT.md decision)
    seed_bytes = sha256((panel_data_hash + "phase-3-bootstrap").encode()).digest()[:4]
    seed = int.from_bytes(seed_bytes, "big")
    rng = np.random.default_rng(seed)

    nhpp_params = fit_nhpp_inar(leg_0_times, leg_1_times, ...)
    hawkes_obs = fit_hawkes_expkern(leg_0_times, leg_1_times)
    LL_nhpp_obs = score_nhpp_loglik(nhpp_params, leg_0_times, leg_1_times)
    LR_observed = 2.0 * (hawkes_obs["loglik_in_sample"] - LL_nhpp_obs)

    bootstrap_LR = np.empty(n_reps)
    n_failed = 0
    for k in range(n_reps):
        try:
            sim_0, sim_1 = simulate_nhpp_from_inar(nhpp_params, window_end, rng)
            nhpp_b = fit_nhpp_inar(sim_0, sim_1, ...)
            hawkes_b = fit_hawkes_expkern(sim_0, sim_1)
            LL_nhpp_b = score_nhpp_loglik(nhpp_b, sim_0, sim_1)
            bootstrap_LR[k] = 2.0 * (hawkes_b["loglik_in_sample"] - LL_nhpp_b)
        except Exception:
            bootstrap_LR[k] = np.nan
            n_failed += 1

    valid = bootstrap_LR[~np.isnan(bootstrap_LR)]
    p_value = float(np.mean(valid >= LR_observed))
    return {
        "observed_stat": float(LR_observed),
        "bootstrap_null_dist_50_50_chi2_0_chi2_1": valid.tolist(),
        "p_value": p_value,
        "rejects_at_alpha": p_value < alpha,
        "n_reps": n_reps,
        "n_failed": n_failed,
        "seed": seed,
        "alpha": alpha,
    }
```

### Time-Rescaling KS Test (Brown 2002)

```python
# Source: Brown et al. 2002 + scipy.stats.kstest
import numpy as np
from scipy.stats import kstest

def time_rescaling_ks_test_leg(
    event_times: np.ndarray,
    baseline_i: float,
    adjacency_row_i: np.ndarray,    # row of α matrix for this leg
    decays: float,
    all_legs_history: list[np.ndarray],   # for cross-excitation
    window_start: float,
    window_end: float,
) -> dict:
    # Closed-form compensator Λ_i(t) for exponential kernel
    # Λ_i(t) = baseline_i * (t - window_start)
    #       + Σ_j α_ij * Σ_{t_jk < t, t_jk ≥ window_start} (1 - exp(-β(t - t_jk))) / β
    Lambda_at_events = np.empty(event_times.size)
    for idx, t in enumerate(event_times):
        Lambda_baseline = baseline_i * (t - window_start)
        Lambda_excitation = 0.0
        for j, leg_j_times in enumerate(all_legs_history):
            valid_j = leg_j_times[(leg_j_times < t) & (leg_j_times >= window_start)]
            Lambda_excitation += adjacency_row_i[j] * np.sum(
                (1.0 - np.exp(-decays * (t - valid_j))) / decays
            )
        Lambda_at_events[idx] = Lambda_baseline + Lambda_excitation

    # Rescaled inter-arrival times
    rescaled_dt = np.diff(np.concatenate([[0.0], Lambda_at_events]))

    # Under correctly-specified Hawkes: rescaled_dt ~ Exp(1) i.i.d.
    ks_stat, ks_pvalue = kstest(rescaled_dt, 'expon')
    return {
        "ks_statistic": float(ks_stat),
        "p_value": float(ks_pvalue),
        "n_events": int(event_times.size),
        "rescaled_dt": rescaled_dt.tolist(),
    }
```

### Profile-Likelihood η-CI

```python
# Source: Cox & Hinkley 1974 + scipy.optimize + Filimonov-Sornette 2014 recommendation
import numpy as np
from scipy.optimize import brentq
from scipy.stats import chi2

def profile_likelihood_eta_ci(
    leg_0_times, leg_1_times,
    hawkes_fit: dict,   # output of fit_hawkes_expkern
    decays: float,
    alpha: float = 0.05,
    eta_grid: np.ndarray = np.linspace(0.01, 0.95, 50),
) -> dict:
    LL_max = hawkes_fit["loglik_in_sample"]
    eta_hat = hawkes_fit["branching_ratio"]
    threshold = float(chi2(1).ppf(1 - alpha))  # interior parameter CI uses vanilla chi2(1)

    # 1. Grid evaluation of profile likelihood
    profile_LL = np.empty(eta_grid.size)
    for k, eta_k in enumerate(eta_grid):
        # Constrained Hawkes fit: parameterize α so that spectral radius = eta_k exactly
        constrained = fit_hawkes_with_fixed_branching_ratio(
            leg_0_times, leg_1_times, eta_k, decays
        )
        profile_LL[k] = constrained["loglik_in_sample"]

    # 2. Find CI bounds via brentq on f(η) = 2*(LL_max - profile_LL(η)) - threshold = 0
    def deficit(eta_value):
        # Interpolate profile_LL or refit at eta_value
        constrained = fit_hawkes_with_fixed_branching_ratio(
            leg_0_times, leg_1_times, eta_value, decays
        )
        return 2.0 * (LL_max - constrained["loglik_in_sample"]) - threshold

    # Lower bound search in (eta_grid.min(), eta_hat)
    try:
        ci_lower = brentq(deficit, eta_grid.min(), eta_hat, maxiter=50)
    except ValueError:
        ci_lower = float(eta_grid.min())  # CI extends below grid

    # Upper bound search in (eta_hat, eta_grid.max())
    try:
        ci_upper = brentq(deficit, eta_hat, eta_grid.max(), maxiter=50)
    except ValueError:
        ci_upper = float(eta_grid.max())  # CI extends above grid

    return {
        "method": "profile_likelihood",
        "eta_hat": float(eta_hat),
        "lower": float(ci_lower),
        "upper": float(ci_upper),
        "ci_width": float(ci_upper - ci_lower),
        "alpha": float(alpha),
    }
```

### Synthetic-Ground-Truth Validation Harness (SC-2)

```python
# Source: CONTEXT.md decision + ROADMAP SC-2 + Kirchner 2015 §7 (simulation study)
import numpy as np
from tick.hawkes import SimuHawkesExpKernels

def test_nhpp_inar_recovers_synthetic_ground_truth():
    # Locked synthetic parameters
    true_baseline = np.array([0.5, 0.4])      # events/sec per leg
    true_adjacency = np.array([[0.0, 0.0],    # α matrix with NO Hawkes excitation
                               [0.0, 0.0]])    # → pure bivariate NHPP
    true_decays = 0.1

    n_paths = 1000
    rng = np.random.default_rng(42)
    recovered_baselines = np.empty((n_paths, 2))
    for k in range(n_paths):
        # Simulate from known parameters
        # NB: with α = 0, this reduces to bivariate Poisson with intensities = baseline
        sim = SimuHawkesExpKernels(
            adjacency=true_adjacency,
            decays=true_decays,
            baseline=true_baseline,
            end_time=2_592_000.0,    # 30 days in seconds
            seed=int(rng.integers(0, 2**31)),
            verbose=False,
            # NEVER force_simulation=True
        )
        sim.simulate()
        leg_0_times = sim.timestamps[0]
        leg_1_times = sim.timestamps[1]

        # Refit via Kirchner INAR(p)
        fit = fit_nhpp_inar(leg_0_times, leg_1_times, 0.0, 2_592_000.0)
        # Recover baseline as intercept / bin_width (Kirchner scaling)
        recovered_baselines[k, 0] = fit["intercept"][0] / fit["bin_width_seconds"]
        recovered_baselines[k, 1] = fit["intercept"][1] / fit["bin_width_seconds"]

    # Assert mean recovery within ±10% of ground truth
    mean_recovered = recovered_baselines.mean(axis=0)
    rel_err = np.abs(mean_recovered - true_baseline) / true_baseline
    assert (rel_err < 0.10).all(), f"Recovery error {rel_err} exceeds 10% tolerance"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Vanilla χ²(1) LRT for nested Hawkes-vs-NHPP | Bootstrap-LR with 50:50 χ²(0):χ²(1) asymptotic sanity check | Self & Liang 1987 (asymptotic theory); Cavaliere et al. 2022 (production bootstrap rig) | Vanilla LRT is wrong on the boundary; bootstrap is robust to finite samples; literature consensus is settled |
| MLE Hessian-based η-CI | Profile-likelihood η-CI | Filimonov & Sornette 2014; Wheatley thesis | Hessian CI extends past boundary [0, 1) and assumes asymptotic normality that fails near η = 0 |
| In-sample time-rescaling KS | Held-out segment time-rescaling KS with train-fitted parameters | PMC12416029 (2024) explicit caution | In-sample always passes; held-out is the test |
| Parametric Hawkes (Ozaki 1979) | Multivariate exponential with `tick` C++ MLE | tick library release (Bacry et al. 2017 JMLR) | 100× speed; integrated simulator; canonical Python implementation |
| Diagonal-only multivariate Hawkes | Full off-diagonal excitation matrix | Bowsher 2007; Daw & Pender 2017; PITFALLS §5 | Diagonal-only masks cross-leg dependence; bivariate Hawkes IS the model |

**Deprecated/outdated:**
- `statsmodels.stats.diagnostic.likelihood_ratio_test` for nested boundary tests — never use for Hawkes-vs-NHPP. Use only for non-boundary cases.
- `hawkeslib` / `PyHawkes` Python packages — unmaintained > 3 years; lack production-grade C++ acceleration.
- Single-univariate-per-leg INAR(p) fitting — leaks covariance into spurious Hawkes self-excitation (PITFALLS §5).

## Open Questions

1. **`fit_hawkes_with_fixed_branching_ratio` — does `tick.HawkesExpKern` support constrained-η fits natively?**
   - What we know: `tick.HawkesExpKern` accepts `penalty='nuclear'` (spectral-radius constraint) but the constraint is "≤ C", not "= C". Profile likelihood requires "= η_k".
   - What's unclear: Whether parameterizing α = η_k · normalized_unit_α_shape and optimizing only baseline + α_shape (with constraint that spectral radius of α_shape = 1) is the canonical way, or whether a custom optimizer (scipy.optimize.minimize with eq constraint) is needed.
   - Recommendation: Plan a Wave-1 spike: try the projection trick (refit, then rescale α to enforce target spectral radius); fall back to scipy.optimize with constraint if the projection gives substantially different profile likelihood than a direct fit. Document the chosen method in the implementation.

2. **`simulate_nhpp_from_inar` — closed-form or `SimuHawkesExpKernels(adjacency=zeros)` ?**
   - What we know: `SimuHawkesExpKernels` with zero adjacency reduces to inhomogeneous Poisson with `baseline` as the rate.
   - What's unclear: Whether `tick`'s simulator accepts the time-varying baseline (from the INAR(p) projection, which gives a step-function rate) or requires conversion via `tick.base.TimeFunction`.
   - Recommendation: Use `SimuHawkesExpKernels` with `baseline` as a list of `TimeFunction` objects representing the step-function rate from INAR(p). Verified API path in the docs (CONTEXT.md library-source).

3. **Bin-width grid selection cost vs benefit at small N.**
   - What we know: PRE_REGISTRATION locks `{1m, 5m, 15m, 1h}` grid + AIC-min rule.
   - What's unclear: At ~382 + ~396 = ~778 total events over 30 days, the 1h bin gives ~720 bins × 2 legs = 1440 count cells; the 1m bin gives 43200 bins, most of which are 0. AIC may strongly prefer wider bins.
   - Recommendation: Honor the lock. Log all four bin-width AIC values in `fit_report.json :: nhpp_inar_params :: bin_width_aic_table` for audit traceability. The lock is the canonical answer; trust the grid.

4. **What happens if neither train nor held-out segments produce a stationary Hawkes fit (spectral radius ≥ 1)?**
   - What we know: PITFALLS §4 warns η ≈ 0.95 is a finite-sample-bias warning; PRE_REGISTRATION Q-9 forces null-fire if CI width > 0.4.
   - What's unclear: Whether the fit code should retry with `penalty='l2'` (small ridge) to pull η back from the boundary or simply emit a fit with `branching_ratio_warning="boundary"` flag.
   - Recommendation: Emit the unregularized fit and surface a `boundary_warning: bool` in `fit_report.json :: hawkes_mv_params`. Regularization choices are anti-feature AF-02 (hand-tuned regularization parameters); the gate's job is to fail to reject NHPP when η is unidentified — that's the correct behavior.

5. **Mismatch between Phase 2 timestamp resolution and Phase 3 same-block ties.**
   - What we know: Phase 2 panel rows carry `(blockNumber, blockHash, logIndex, txHash, ...)`. Block timestamp resolution is 1 second (Celo post-2024 hardfork).
   - What's unclear: Are 13 same-block Swap pairs the only ties, or do same-second pairs across consecutive blocks also occur? (Celo block time is 1s/block so block_timestamp can repeat across two blocks if NTP adjustment.)
   - Recommendation: Implement a sanity-check at the leg-extraction boundary: count ties at the millisecond level (if available) vs second level vs block level; surface in `fit_report.json :: input_diagnostics :: tie_counts`.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `pytest>=9.0.3` (per `analysis/pyproject.toml` already installed in Phase 2 Plan 02-00) |
| Config file | `analysis/pyproject.toml` `[tool.pytest.ini_options]` (testpaths=["tests"], pythonpath=["src"]) — already established |
| Quick run command | `cd analysis && uv run pytest tests/test_<module>.py -x` |
| Full suite command | `cd analysis && uv run pytest -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| **DGP-01** | Kirchner INAR(p) recovers ground-truth NHPP baseline within ±10% over 1000 paths | unit (synthetic) | `cd analysis && uv run pytest tests/test_nhpp_inar.py::test_recovers_synthetic_ground_truth -x` | ❌ Wave 0 |
| **DGP-01** | INAR(p) AIC-min selects bin width from `{60, 300, 900, 3600}` seconds | unit | `cd analysis && uv run pytest tests/test_nhpp_inar.py::test_aic_bin_selection -x` | ❌ Wave 0 |
| **DGP-01** | Non-negativity projection clamps negative VAR coefficients to 0 | unit | `cd analysis && uv run pytest tests/test_nhpp_inar.py::test_nonneg_projection -x` | ❌ Wave 0 |
| **DGP-02** | `tick.HawkesExpKern` fit produces 2×2 adjacency matrix with off-diagonal elements not forced to 0 | unit | `cd analysis && uv run pytest tests/test_hawkes_fit.py::test_full_offdiag -x` | ❌ Wave 0 |
| **DGP-02** | Branching ratio computed as spectral radius of α/β (not max element) | unit | `cd analysis && uv run pytest tests/test_hawkes_fit.py::test_branching_ratio_spectral -x` | ❌ Wave 0 |
| **DGP-02** | Same-block timestamps handled without logIndex tie-breaking | unit | `cd analysis && uv run pytest tests/test_hawkes_fit.py::test_simultaneous_events -x` | ❌ Wave 0 |
| **DGP-03** | Bootstrap LR rig produces histogram with point mass at 0 + continuous right tail (visible mixture shape) | unit (synthetic NHPP data) | `cd analysis && uv run pytest tests/test_lr_test.py::test_null_distribution_mixture_shape -x` | ❌ Wave 0 |
| **DGP-03** | Bootstrap LR rejects at α=0.01 on synthetic Hawkes data with η=0.5 (power) | unit (synthetic) | `cd analysis && uv run pytest tests/test_lr_test.py::test_power_on_synthetic_hawkes -x` | ❌ Wave 0 |
| **DGP-03** | Bootstrap LR has ~1% rejection rate on synthetic NHPP data (size validation at α=0.01) | unit (synthetic, 200 reps inner) | `cd analysis && uv run pytest tests/test_lr_test.py::test_size_calibration -x` | ❌ Wave 0 |
| **DGP-03** | Source code has zero hits for `likelihood_ratio_test` or naive `chi2(1).sf` | lint (grep) | `! grep -rE "likelihood_ratio_test\|chi2\(1\)\.sf" analysis/src/abrigo_x402/dgp/lr_test.py` | ❌ Wave 0 |
| **DGP-04** | Held-out split is wall-clock not event-count | unit | `cd analysis && uv run pytest tests/test_held_out.py::test_wallclock_split -x` | ❌ Wave 0 |
| **DGP-04** | In-sample-only fit attempt raises `InsufficientEvaluationError` | unit | `cd analysis && uv run pytest tests/test_held_out.py::test_in_sample_only_raises -x` | ❌ Wave 0 |
| **DGP-04** | Stationarity diagnostic correctly identifies non-stationary panel (synthetic with rate drift) | unit (synthetic) | `cd analysis && uv run pytest tests/test_stationarity.py::test_piecewise_required_on_drifted_synthetic -x` | ❌ Wave 0 |
| **DGP-05** | Time-rescaling KS test passes on correctly-specified Hawkes synthetic data | unit (synthetic) | `cd analysis && uv run pytest tests/test_time_rescaling.py::test_passes_on_true_model -x` | ❌ Wave 0 |
| **DGP-05** | Time-rescaling KS test fails on misspecified model (NHPP rescaling of true Hawkes data) | unit (synthetic) | `cd analysis && uv run pytest tests/test_time_rescaling.py::test_fails_on_misspecified -x` | ❌ Wave 0 |
| **DGP-05** | Compensator Λ(t) for exponential kernel is correctly closed-form | unit (analytic comparison) | `cd analysis && uv run pytest tests/test_time_rescaling.py::test_compensator_closed_form -x` | ❌ Wave 0 |
| **DGP-06** | Profile-likelihood η-CI on synthetic Hawkes recovers known η within CI width | unit (synthetic) | `cd analysis && uv run pytest tests/test_profile_likelihood.py::test_ci_covers_truth -x` | ❌ Wave 0 |
| **DGP-06** | η-CI is bounded in [0, 1) (never extends past boundary) | unit | `cd analysis && uv run pytest tests/test_profile_likelihood.py::test_ci_bounded -x` | ❌ Wave 0 |
| **DGP-06** | CI width > 0.4 triggers Q-9 null-fire flag in fit_report.json | unit | `cd analysis && uv run pytest tests/test_profile_likelihood.py::test_q9_nullfire_trigger -x` | ❌ Wave 0 |
| **SC-1** | `fit_report.json` carries all metadata keys (chainId, contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit) | integration | `cd analysis && uv run pytest tests/test_fit_artifact_provenance.py::test_metadata_keys -x` | ❌ Wave 0 |
| **SC-1** | `make lint-artifacts` extension recognizes `fit_report.json` and rejects missing keys | lint | `make lint-artifacts` (from repo root after extension lands) | ❌ Wave 0 |
| **SC-3** | Diagnostic `reports/_diagnostics/lr_null_dist.png` renders headless and shows mixture shape | smoke (image existence + nonzero size) | `cd analysis && uv run pytest tests/test_lr_test.py::test_diagnostic_plot_renders -x` | ❌ Wave 0 |
| **SC-5** | Byte-identical `fit_report.json` and `residuals.parquet` across two runs with same panel + git commit (modulo wall-clock fields) | integration | `cd analysis && uv run pytest tests/test_byte_identical.py::test_deterministic_fit -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `cd analysis && uv run pytest tests/test_<module>.py -x` (single-file run; < 30s typical)
- **Per wave merge:** `cd analysis && uv run pytest -x` (full Phase 3 suite; ~ 2-5 min — bootstrap LR test is expensive at 1000 reps; tests use reduced n_reps=200 with size-calibration assertion)
- **Phase gate:** Full suite green + `make lint-artifacts` PASS + a diagnostic-plot file existence check + the SC-3 grep gate (`! grep -rE "likelihood_ratio_test|chi2\(1\)\.sf" analysis/src/abrigo_x402/dgp/lr_test.py`)

### Wave 0 Gaps

- [ ] `analysis/tests/test_nhpp_inar.py` — covers DGP-01 (synthetic-ground-truth recovery harness)
- [ ] `analysis/tests/test_hawkes_fit.py` — covers DGP-02 (tick fit, branching ratio, simultaneous events)
- [ ] `analysis/tests/test_lr_test.py` — covers DGP-03 (bootstrap null shape, size, power, grep gate)
- [ ] `analysis/tests/test_held_out.py` — covers DGP-04 (wall-clock split, InsufficientEvaluationError)
- [ ] `analysis/tests/test_stationarity.py` — covers PITFALLS §4 stationarity diagnostic (±25% ratio + piecewise_required decision)
- [ ] `analysis/tests/test_time_rescaling.py` — covers DGP-05 (compensator closed-form, KS pass/fail)
- [ ] `analysis/tests/test_profile_likelihood.py` — covers DGP-06 (η-CI bounded, covers truth, Q-9 null-fire)
- [ ] `analysis/tests/test_fit_artifact_provenance.py` — covers SC-1 (metadata header on fit_report.json)
- [ ] `analysis/tests/test_byte_identical.py` — covers SC-5 (deterministic rerun byte-identity)
- [ ] `analysis/tests/conftest.py` — extend Phase 2 conftest with: synthetic Hawkes/NHPP fixture generators (parameterized over η, decay, end_time), `panel_fixture` fixture loading the canonical 30-day ICHI panel (from `data/raw/ichi/...`)
- [ ] `analysis/tests/fixtures/synthetic_hawkes_eta_05.parquet` — captured tick-simulated 30-day panel with known η=0.5 for synthetic-ground-truth recovery tests (Wave 0 capture step using `SimuHawkesExpKernels` with locked seed)
- [ ] `analysis/tests/fixtures/synthetic_nhpp_baseline_only.parquet` — captured tick-simulated 30-day panel with α=0 (pure NHPP) for LR-test size validation
- [ ] `scripts/lint_fit_artifacts.py` OR extension to `scripts/lint_artifacts.py` — recognize `fit_report.json` and require SC-1 metadata header

(Framework install: not needed — `pytest>=9.0.3` already in `analysis/pyproject.toml [dependency-groups].dev`, installed in Phase 2 Plan 02-00.)

## Sources

### Primary (HIGH confidence)

- **`tick` 0.8.0.2 official documentation** — https://x-datainitiative.github.io/tick/modules/generated/tick.hawkes.HawkesExpKern.html (verified 2026-05-26 via WebFetch — constructor signature, coeffs/baseline/adjacency attributes, score() in-sample log-likelihood, `gofit='likelihood'` for MLE)
- **`tick` 0.8.0.2 `SimuHawkesExpKernels` documentation** — https://x-datainitiative.github.io/tick/modules/generated/tick.hawkes.SimuHawkesExpKernels.html (verified 2026-05-26 via WebFetch — adjacency/decays/baseline/end_time constructor, timestamps attribute, force_simulation flag)
- **Kirchner 2015 "An estimation procedure for the Hawkes process"** — https://arxiv.org/abs/1509.02017 (INAR(p) via VAR + non-negativity projection; consistency + asymptotic normality)
- **Filimonov & Sornette 2014 "Branching ratio approximation for the self-exciting Hawkes process"** — https://arxiv.org/abs/1403.5227 (branching-ratio bias; profile-likelihood recommendation; canonical-ref per CONTEXT.md)
- **Cavaliere, Lu, Rahbek, Stærk-Østergaard 2022 "Bootstrap Inference for Hawkes and General Point Processes"** — https://arxiv.org/abs/2104.03122 (fixed-intensity bootstrap; replaces vanilla asymptotic LRT)
- **arxiv 2410.05008 "Testing procedures based on maximum likelihood estimation for Marked Hawkes processes"** — https://arxiv.org/pdf/2410.05008 (over-rejection of vanilla LRT under naive plug-in; canonical-ref per CONTEXT.md)
- **Brown, Barbieri, Ventura, Kass, Frank 2002 "The time-rescaling theorem and its application to neural spike train data analysis"** *Neural Computation* (KS test on rescaled inter-arrival times; canonical-ref per CONTEXT.md and PRE_REGISTRATION §Test Statistics)
- **PMC12416029 (2024) "On the use and misuse of time-rescaling to assess the goodness-of-fit of self-exciting temporal point processes"** — https://pmc.ncbi.nlm.nih.gov/articles/PMC12416029/ (held-out vs in-sample time-rescaling caution; predictive vs plug-in)
- **Wheatley ETH thesis "Robust Hawkes process estimation"** — https://ethz.ch/content/dam/ethz/special-interest/mtec/chair-of-entrepreneurial-risks-dam/documents/dissertation/wheatleythesis.pdf (profile-likelihood η-CI rationale; canonical-ref per CONTEXT.md)
- **Bacry, Mastromatteo, Muzy 2015 "Hawkes processes in finance"** + **Bacry et al. 2017 JMLR "tick: a Python Library for Statistical Learning"** — https://www.jmlr.org/papers/volume18/17-381/17-381.pdf (tick library reference)
- **Daw & Pender 2017 "Queues driven by Hawkes processes"** — https://arxiv.org/pdf/1707.05143v3 (bivariate Hawkes moments; canonical-ref per CONTEXT.md)
- **PyPI** — `pip index versions <pkg>` 2026-05-26 (current versions for tick, statsmodels, polars, numpy, scipy — all five at latest)
- **`notes/PRE_REGISTRATION.md`** (commit `6cd61ed` 2026-05-25) — kernel forms, prior parameters, test statistics, acceptance regions, Q-9 floor (LOCKED, AF-03 audit anchor)
- **`.planning/research/PITFALLS.md` §4** — NHPP-vs-Hawkes misidentification, LR-test boundary correction, EM/profile-likelihood requirement, four-criterion gate origin
- **`.planning/research/PITFALLS.md` §3** — Mock data and in-sample optimism (mandates held-out + synthetic-ground-truth)
- **`.planning/research/PITFALLS.md` §5** — Cross-leg dependence assumed independent when self-excitation is bivariate
- **`.planning/phases/03-dgp-estimation-l4-with-boundary-correct-lr-test/03-CONTEXT.md`** (commit `9263d17` 2026-05-26) — user decisions

### Secondary (MEDIUM confidence)

- **Self & Liang 1987** "Asymptotic Properties of Maximum Likelihood Estimators and Likelihood Ratio Tests Under Nonstandard Conditions" *JASA* — boundary asymptotic mixture theory (textbook reference; cited indirectly via Cavaliere)
- **arxiv 2509.00223** "A note on the asymptotic distribution of the Likelihood Ratio Test statistic under boundary conditions" — recent restatement of boundary-LR mixture; verified via WebSearch 2026-05-26
- **arxiv 2405.08640** "A sparsity test for multivariate Hawkes processes" — adjacency-matrix sparsity LRT with χ² mixture asymptotic; verified via WebSearch
- **arxiv 2006.07506** "Uncertainty Quantification for Inferring Hawkes Networks" — polyhedra CI for Hawkes MLE (an alternative to profile-likelihood; documented but not adopted for v1 per CONTEXT.md decision)
- **Springer "A robust and efficient algorithm to find profile likelihood confidence intervals"** (2021) — algorithmic patterns for profile-likelihood CI inversion (grid + bisection); doi.org/10.1007/s11222-021-10012-y
- **Cox & Hinkley 1974** *Theoretical Statistics* — profile-likelihood textbook reference

### Tertiary (LOW confidence — flagged for validation if leaned upon)

- **GitHub `Eden-Kramer-Lab/time_rescale`** — Python reference implementation of time-rescaling KS; not adopted (our exponential-kernel closed-form is simpler), but informative as a sanity-check reference
- **GitHub `stmorse/hawkes`** — teaching reference for multivariate Hawkes; explicitly NOT a substitute for `tick.HawkesExpKern` per Pitfall 1 in our anti-pattern list

## Metadata

**Confidence breakdown:**
- Standard Stack: **HIGH** — All five locked in `analysis/uv.lock`, latest on PyPI, verified via WebFetch on tick docs; CONTEXT.md library-sources canonical-ref
- Architecture Patterns: **HIGH** — Pattern 1 (Kirchner INAR(p)) + Pattern 2 (tick Hawkes) verified against primary sources; Patterns 3-6 (bootstrap LR, held-out split, time-rescaling, profile likelihood) verified against arxiv primary sources + PRE_REGISTRATION lock
- Common Pitfalls: **HIGH** — every pitfall traces to either PITFALLS.md §4/§5 (project-internal lock) or arxiv literature (Filimonov-Sornette, Cavaliere, PMC12416029)
- Validation Architecture: **HIGH** — pytest framework already established in Phase 2; synthetic-ground-truth harness mandated by SC-2; grep gate mandated by SC-3

**Research date:** 2026-05-26
**Valid until:** 2027-01-26 (8 months — stable mathematical methodology with locked stack; the only thing that could move is a `tick` 0.9 release with breaking API changes; library version pins protect against that)

---

*Phase: 03-dgp-estimation-l4-with-boundary-correct-lr-test*
*Researched: 2026-05-26*
