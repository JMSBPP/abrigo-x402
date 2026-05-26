# Phase 3: DGP Estimation (L4) with Boundary-Correct LR Test - Context

**Gathered:** 2026-05-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Fit NHPP (Kirchner INAR(p)) and bivariate Hawkes (tick exponential kernel, full off-diagonal) on the Phase-2 panel; run boundary-correct bootstrap LR test, time-rescaling KS test, held-out temporal evaluation, and profile-likelihood branching-ratio CIs; emit `data/fits/ichi/<run_id>/fit_report.json` plus a `residuals.parquet` sidecar consumed by Phase 4.

In scope: the four-criterion gate is evaluated and reported, but Phase 3 does not decide PASS/STRADDLE/FAIL at the publication level — that decision lives in Phase 5's reporting layer.

Out of scope (deferred to v2 milestone per `notes/PRE_REGISTRATION.md`): power-law kernel sweep, kernel-class robustness test, bootstrap CIs on all DGP parameters, structural-break test. These fire ONLY if Hawkes wins the four-criterion gate in v1 — handle in Iteration 3+.

</domain>

<decisions>
## Implementation Decisions

### Bivariate leg definition

- **Two streams: direction-bivariate.** `leg_0` = token0-inflow Swaps (zeroForOne, 382 events on the 30-day ICHI cKES/USDT panel); `leg_1` = token1-inflow Swaps (oneForZero, 396 events). Both legs comfortably exceed the 300-event Q-9 Hawkes-identifiability floor.
- **Labels: `leg_0` / `leg_1`** (Uniswap token-index convention). NOT `R`/`C` — both legs are revenue (1bp fee on input regardless of direction); the PRE_REGISTRATION "revenue × cost" prose is a model-of-cost abstraction, not a token-direction asymmetry.
- **Economic interpretation of cross-leg coefficients:**
  - `α_{0,0}` = self-excitation within token0-inflow stream (cKES-buying clusters?)
  - `α_{1,1}` = self-excitation within token1-inflow stream (USDT-buying clusters?)
  - `α_{0,1}` = does a token1-inflow Swap excite a subsequent token0-inflow Swap? (round-trip arbitrage signature)
  - `α_{1,0}` = symmetric
- **NHPP fit form: bivariate INAR(p) via `statsmodels.tsa.api.VAR`** with non-negativity projection (Kirchner 2015). Same dimensionality as the Hawkes alternative → LR test compares equivalently-sized models. NO summed univariate INAR(p) shortcut (would leak cross-leg covariance into spurious Hawkes self-excitation per PITFALLS §5).
- **Same-block co-fire handling: shared continuous timestamp.** 13 same-block Swap pairs in the panel. Both events at `t = block_timestamp` (seconds). `tick.HawkesExpKern` handles simultaneous events natively. NO logIndex tie-breaking — logIndex is a client-implementation artifact, not a real time signal.
- **Residual emission:** `fit_report.json` includes `residuals_hash` (sha256 of residuals file bytes); the actual rescaled-time sequences land at `data/fits/ichi/<run_id>/residuals.parquet`. Phase 4 copula loads `residuals.parquet` directly without re-running the Hawkes fit. SC-5 byte-identical contract extends to `residuals.parquet`.

### Claude's Discretion

The following areas were left as Claude's Discretion during discussion. Recommended defaults documented here; planner may revisit only if research surfaces a blocker.

- **Held-out split mechanic:** wall-clock last 20% of the panel window (≈ 6 days at the end of the 30-day window). Wall-clock split (not event-count split) is more defensible per PITFALLS §4 "fit must be stable under ±10% window shift" — using event-count splits couples the test set to the realized event density. Stationarity diagnostic (`train_rate` vs `held_out_rate` within ±25%) gates whether the baseline-stationarity branch fires per SC-4.
- **`<run_id>` path scheme:** `run_id = sha256(panel_dataHash + fit_code_gitCommit + tick_lib_version)[:12]`. Deterministic → SC-5 byte-identical extends to the path itself. Same input + same code → same run_id. Different code or panel → different run_id. Implementation reference: `data/raw/manifest.json` Phase 2 pattern.
- **Fit-artifact provenance:** the `fit_report.json` + `residuals.parquet` pair gets a `data/fits/manifest.json` entry mirroring the Phase 2 panel manifest schema (`cache_key_hash`, `dataHash`, `gitCommit`, `fetchTimestamp`, etc.). Allowlist via `.gitignore` negation pattern same as `data/raw/manifest.json`.
- **Sparse-leg handling:** no pre-emptive fallback to univariate — both legs are over the 300-event Q-9 floor. The four-criterion gate (LR rejection + η ≥ 0.2 + KS held-out + within-bootstrap CI not blowing past width 0.4) is the canonical safety net per PRE_REGISTRATION. If a future panel falls under the floor, the Q-9 trigger (`<300 events OR CI width >0.4 → null-fire`) is locked in PRE_REGISTRATION and is non-negotiable.
- **Bootstrap reps:** default 1000 (locked in PRE_REGISTRATION). NO CLI flag to override at production-fit time — AF-04 hand-tuning hazard. A dev-only `--bootstrap-reps=<N>` flag may be exposed for unit-test smoke runs, but the production fit always uses 1000.
- **Random seed:** PRNG seed = `sha256(panel_dataHash + "phase-3-bootstrap")[:8]` interpreted as uint32. Deterministic, panel-dependent. Different panel → different bootstrap sample. Same panel → byte-identical bootstrap → byte-identical `fit_report.json`.
- **Diagnostic plot:** `reports/_diagnostics/lr_null_dist.png` (locked by SC-3). Matplotlib output; rendered headless. SC-3 requires the χ²(0):χ²(1) mixture be visually verifiable.
- **NHPP validation harness:** `analysis/tests/test_nhpp_inar.py` simulates 1000 paths from `tick.hawkes.SimuHawkesExpKernels` with known params (locked), refits via the Kirchner estimator, asserts recovered params within ±10%. CI gate per SC-2.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Pre-registration (locked parameters — NEVER post-hoc revise)
- `notes/PRE_REGISTRATION.md` §Kernel Forms — NHPP / Hawkes / power-law (deferred) specs
- `notes/PRE_REGISTRATION.md` §Prior Parameters — bin-width grid `{1m, 5m, 15m, 1h}`, AIC-min rule, exponential-kernel default
- `notes/PRE_REGISTRATION.md` §Test Statistics — bootstrap LR (1000 reps, 50:50 χ²(0):χ²(1) mixture, α = 0.01), time-rescaling KS (Brown 2002, p > 0.05), profile-likelihood η-CI
- `notes/PRE_REGISTRATION.md` §Acceptance Regions — four-criterion gate (LR + η ≥ 0.2 + KS held-out + non-stationarity rule-out)
- `notes/PRE_REGISTRATION.md` §Null-Fire Conditions — when to emit null-result PDF per HEDGE-05
- `notes/PRE_REGISTRATION.md` §Sample-Size Floors — Q-7 ($10k volume OR 30 events/30d), Q-9 (<300 events OR CI width >0.4 → null)

### Pitfalls to mitigate (architectural risks)
- `.planning/research/PITFALLS.md` §4 — NHPP-vs-Hawkes misidentification, LR-test boundary correction, EM/profile-likelihood requirement, four-criterion gate origin
- `.planning/research/PITFALLS.md` §3 — Mock data and in-sample optimism (mandates held-out evaluation + synthetic-ground-truth validation harness)
- `.planning/research/PITFALLS.md` §5 — Cross-leg dependence assumed independent when self-excitation is bivariate (mandates full off-diagonal matrix; no diagonal-only shortcut)

### Phase 0 governance / anti-features
- `notes/PHASE_0_GATE.md` — pre-fit gates that already passed
- `notes/Q9_DECISION.md` — V3-only vs unified panel-construction decision (REPRO-04)
- ROADMAP.md §Phase 3 — SC-1..SC-5 verbatim
- `.planning/REQUIREMENTS.md` §DGP-01..DGP-06 — requirement traceability

### Phase 2 upstream contract (what Phase 3 consumes)
- `.planning/phases/02-panel-build-l3-for-the-ichi-ckes-usdt-anchor/02-CONTEXT.md` — panel construction decisions
- `data/raw/ichi/0x61Ef…829F/67378253_67896653.parquet` — the real-data panel (gitignored; manifest at `data/raw/manifest.json`)
- `data/raw/manifest.json` — Phase 2 panel provenance (model for Phase 3's `data/fits/manifest.json`)
- `analysis/src/abrigo_x402/panel.py` — `build_panel` signature; the Parquet's column schema
- `analysis/src/abrigo_x402/provenance.py` — `with_header` / `assert_has_header` API (same metadata pattern for `fit_report.json` provenance keys)

### Library sources
- `tick==0.8.0.2` — `tick.hawkes.HawkesExpKern` (multivariate exponential Hawkes), `tick.hawkes.SimuHawkesExpKernels` (synthetic ground truth for SC-2)
- `statsmodels==0.14.6` — `statsmodels.tsa.api.VAR` (Kirchner INAR(p) base)
- Kirchner 2015 arxiv.org/abs/1509.02017 — INAR(p) NHPP estimator
- Daw & Pender 2017 arxiv.org/pdf/1707.05143v3 — bivariate Hawkes specification reference
- Filimonov & Sornette 2014 arxiv.org/pdf/1403.5227 — boundary-LR correction
- arxiv.org/pdf/2410.05008 — LR over-rejection under naive plug-in
- Brown et al. 2002 — time-rescaling KS theorem (cited in PITFALLS §4)
- Wheatley ETH thesis — robust Hawkes estimation, profile-likelihood η-CI rationale

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- **`analysis/src/abrigo_x402/ingest.py`** (`load_jsonl`, `apply_finality_cutoff`) — reuse for loading the Phase 2 Parquet input. New Phase 3 fitting module reads via `polars.read_parquet`, then filters to `event_name == "Swap"` and projects `(blockNumber, txHash, logIndex, tick, amount0, amount1)` to derive leg_0 / leg_1 streams.
- **`analysis/src/abrigo_x402/provenance.py`** (`with_header`, `assert_has_header`) — pattern model for `fit_report.json` metadata header. `fit_report.json` is JSON not Parquet so the API doesn't carry over directly, but the metadata KEY set is the same: `chainId`, `contractAddress`, `blockRange`, `fetchTimestamp`, `dataHash`, `gitCommit` (SC-1 requirement).
- **`analysis/src/abrigo_x402/panel.py`** (`build_panel`, `write_panel`, `assert_no_graph_mainnet_in_ledger`) — model for the Phase 3 orchestrator's shape: pure-function pipeline + dedicated write step + cost-ledger enforcement.
- **`analysis/src/abrigo_x402/cli.py`** (`materialize` subcommand) — argparse pattern for the new `fit` subcommand. New CLI invocation: `python -m abrigo_x402.cli fit --pool 0x61Ef…829F --panel-path data/raw/ichi/.../<range>.parquet --out-dir data/fits/ichi/`.
- **`fetch/data/raw/_cost_ledger.jsonl`** — Phase 3 has no chain calls (fits are pure-compute on the Parquet); no new ledger rows needed, but the `assert_no_graph_mainnet_in_ledger` invariant must still pass.
- **`scripts/lint_artifacts.py`** (PANEL-02 metadata-header linter) — extend or sibling `lint_fit_artifacts.py` to enforce the SC-1 metadata header on `fit_report.json` + the `residuals.parquet` provenance.

### Established Patterns

- **String-as-decimal-int column convention** (Pitfall 6) — Phase 2 stores amount0/amount1/sqrtPriceX96 as `String` and casts to `pl.Int128`/`pl.Decimal(38,0)` at use-time. Phase 3 fit consumes these and casts to NumPy int64 for the leg-bin timestamps; conversion is at the ingest boundary, not in the JSONL.
- **Synthetic-fixture-first TDD** — Phase 2 fitted synthetic 100-row panels before live data. SC-2 mandates the same for Phase 3: `test_nhpp_inar.py` simulates from `SimuHawkesExpKernels` with known params, refits, asserts ±10% recovery.
- **Polars 1.41 native `write_parquet(metadata=...)`** — used for the Parquet panel in Phase 2; reuse for `residuals.parquet`. JSON metadata via vanilla `json.dump` for `fit_report.json`.
- **Deterministic provenance hashing** — Phase 2 `data_hash_for_panel` (analysis/src/abrigo_x402/cli.py L45-55) is sha256 over concatenated sidecar bytes. Phase 3 `data_hash_for_fit` is sha256 over `(panel_dataHash, fit_code_gitCommit, tick_lib_version, residuals_bytes)` — extends the same pattern.
- **`.gitignore` allowlist via negation** — `data/raw/manifest.json` pattern (line 44). Mirror for `data/fits/manifest.json` and any pinned reference fits, but NOT the per-run `fit_report.json` (those re-materialize from the panel deterministically).

### Integration Points

- **Phase 2 panel Parquet** is the sole upstream input. Path resolved via `data/raw/ichi/<pool>/<from_block>_<to_block>.parquet`. Phase 3 reads it; no writes back.
- **Phase 4 copula** is the sole downstream consumer. Phase 4 will load `data/fits/ichi/<run_id>/residuals.parquet` + the cross-leg α matrix from `fit_report.json`.
- **CLI surface** extends `analysis/src/abrigo_x402/cli.py` with a `fit` subcommand mirroring `materialize`. No new top-level CLI binary.
- **NOT involved:** `fetch/` workspace, Forno, Blockscout, Mento. Phase 3 is pure-compute on the materialized Parquet. The cost-ledger writes zero new rows.

</code_context>

<specifics>
## Specific Ideas

- "The PRE_REGISTRATION 'revenue × cost' framing is the model-of-cost abstraction, not a token-direction asymmetry on the V3 pool. Use token-index labels (`leg_0`/`leg_1`) in code; let the prose-level framing live in Phase 5's PDF."
- The Phase 2 panel surfaced a real economic finding (vault TVL $57k, annualized yield 0.0024%, total 30-day pool revenue $1.22) — the Hawkes/NHPP fit will likely produce a **STRADDLE** or **null-fire** outcome on the four-criterion gate, not a clean Hawkes-positive claim. This is *expected* and *valid* per HEDGE-05 — Phase 3 must not lower the bar to produce a Hawkes-positive number from this thin panel.
- Phase 3 must produce a fit_report.json that survives metadata audit even when the gate fails — i.e., NEVER write a fit_report.json with missing keys; report `gate_passes: false` with the failing criteria detailed.

</specifics>

<deferred>
## Deferred Ideas

- **v2.0 streaming-tokenization extension** — per `notes/ROADMAP-EXTENSIONS.md`; Phase 3 keeps NHPP/Hawkes math polymorphic enough that the v2.0 streaming-PV decomposition can re-use the same fit code on Superfluid flow-rate-change events.
- **Power-law Hawkes kernel** — DGP-V2-01; fires only if exponential Hawkes wins the v1 four-criterion gate (PRE_REGISTRATION §Kernel Forms locks this deferral).
- **Bootstrap CIs on all DGP parameters** — DGP-V2-02; fires only on v1 Hawkes-positive.
- **Structural-break test** — DGP-V2-03; fires unconditionally in Phase 7 if v1 ships.
- **Held-out segment piecewise-constant baseline fallback** — SC-4 mentions "baseline_stationarity_check" decision: `stationary` or `piecewise_required`. If `piecewise_required` fires for the 30-day ICHI panel, the piecewise NHPP/Hawkes baseline extension is a Plan 03-NN within this phase (not deferred). Decision logged at fit time per SC-4.

</deferred>

---

*Phase: 03-dgp-estimation-l4-with-boundary-correct-lr-test*
*Context gathered: 2026-05-26*
