# Phase 6: Iteration-2 Swap-Surface Validation on Steer (cCOP/USDT) — Research

**Researched:** 2026-05-29
**Domain:** Reproducibility-invariant re-run of a frozen 7-layer pipeline via config-swap; pre-registered cost-leg adjudication; generic null-result PDF rendering; leak-gate enforcement (no CI).
**Confidence:** HIGH on the codebase facts (all verified by direct read/grep on HEAD); MEDIUM on the renderer-fix sequencing (depends on a design choice flagged in Open Questions).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

1. **Cost-leg straddle adjudication (REPRO-03 — binding first-step gate).** `steer.toml` records `celo_attributable_queries_per_mo_lower_bound = 30000` against `demand_window_lower_bound_queries_per_mo = 100000` (Graph free-tier ceiling, canonical DEMAND-01). The 30k–100k band includes the 100k line but is not strictly above it. **Decision rule: a straddle (not strictly ABOVE the 100k lower bound) → cost-leg FAILS → fire HEDGE-05 condition (a) `null_cost`.** Steer is the honest D-08 negative control; the null firing is the intended validation, not a disappointment. **The straddle decision rule is PRE-REGISTERED now (before any Steer fetch) and applied to the existing pre-committed 30k–100k band as-is.** No re-estimation, no fresh enumeration to narrow the band. Phase 6 only OBSERVES the verdict — it never re-estimates demand to chase pass/fail (AF-03). The rule must be written to `notes/PRE_REGISTRATION.md` and `notes/steer_cost_leg_bound.md` BEFORE the check executes; commit ordering must show the rule predates the verdict.

2. **Resolution on cost-leg failure (REPRO-03).** Iteration 2's resolution policy on the Steer null is **SUBSTITUTE a replacement candidate** (not defer-and-close). **The substitute candidate is NOT named or executed in this milestone** — it is a future-milestone decision. Phase 6 ships the Steer null-result deliverable and records the disposition as "substitute pending (future milestone)." **AF-03 guardrail (MANDATORY for the future milestone, recorded here so it is not lost):** any future substitute candidate MUST be pre-registered BEFORE its own data is seen. Choosing a substitute *after* observing Steer's null without pre-registration would be candidate-shopping — forbidden. Phase 6 does NOT pre-register a specific substitute (per user decision), so the future milestone owns that pre-registration.

3. **Pipeline execution on the (expected) null.** **The full Phase 2–5 pipeline RUNS on Steer cCOP/USDT regardless of the cost-leg fail** — it is not short-circuited. This mirrors how ICHI emitted `null_strip_unavailable` from *inside* its completed run. Rationale: the full re-run is what demonstrates the **REPRO-02 zero-edit swap-surface invariant** — `git diff fetch/src analysis/src` between the Iteration-1-complete baseline and Iteration-2-complete MUST be empty. `null_cost` is then fired from inside the gate report, as one possible OUTPUT of the run. This resolves the apparent ROADMAP SC-2 ("exits cleanly on cost-leg fail") vs SC-4 ("`make iteration-2-full` runs Phase 2–5 and produces steer.pdf OR steer_null_result.pdf") tension in favor of the full re-run: the cost-leg verdict is a field in the gate report, not a pre-fetch short-circuit. Free-tier fetch budget for the cCOP/USDT V3 anchor pull is accepted.

4. **Null-result deliverable (REPORT-01 re-fires for Iteration 2).** **Renderer: fix + use the generic HEDGE-05 `render_null_result_pdf`** (`analysis/src/abrigo_x402/hedge/null_result.py`) — its originally-intended purpose. This folds the tracked follow-up bug (relative template path + papermill `-P` dependency) INTO Phase 6 and gives the null-result template its first production use. **CRITICAL SEQUENCING (REPRO-02 preservation):** fixing `render_null_result_pdf` is an edit to `analysis/src`, which would otherwise violate the REPRO-02 "empty `git diff` on `fetch/src` + `analysis/src`" invariant. Therefore the generic-renderer fix MUST land as a **standalone pre-Iteration-2 baseline maintenance commit**, and the Iteration-1-complete→Iteration-2-complete empty-diff window is measured AFTER that fix. The fix is GENERIC (no `ichi`/`steer` identifiers — must pass `grep -r "ichi" fetch/src analysis/src` = 0). The protocol-agnosticism lint (SC-5) must still pass. **Depth: cost-leg headline + DGP/gate results as supporting material** + explicit REPRO-02 zero-edit attestation. Honest and complete, not a stub.

### Claude's Discretion

- Where the cost-leg first-step check physically lives such that it runs first WITHOUT editing `fetch/src`/`analysis/src` (likely a `scripts/` tool or a `make iteration-2-full` Makefile step that reads `steer.toml`'s pre-committed band + applies the pre-registered straddle rule + writes `notes/steer_cost_leg_bound.md`). Researcher to confirm existing cost-leg machinery vs. new scripts/-level glue.
- Exact `make iteration-2-full` target wiring and the leak-check (`make leak-check`) enforcement mechanism (pre-commit hook vs. CI — note: no CI currently exists in the repo).
- Null-result PDF reproducibility treatment (mirror the ichi content-check / SOURCE_DATE_EPOCH determinism approach where applicable).

### Deferred Ideas (OUT OF SCOPE)

- **Substitute candidate execution** (e.g. cNGN/USDT) — named candidate + run is a FUTURE MILESTONE, pre-registered before its data is seen (AF-03).
- **CI wiring for `make leak-check` + `verify-reproducibility`** — no CI exists in the repo today (flagged by the Phase-5 DevOps review); making these required CI checks is a project-wide infra follow-up, not Phase 6.
- **Cost-side convexity modeling** (the free→paid subscription step as a convex exposure) — Phase 7 / v2 synthesis theme.
- **Unified-panel path execution** — only materializes if BOTH Q9 switch-trigger conditions hold during the Steer fit; pre-registered, not pre-built.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REPRO-01 | Protocol-spec layer (`protocols/*.toml`) is the only file class that changes; `grep -r "ichi" fetch/src analysis/src` returns zero hits before Iteration 2 starts. | **Currently FAILING** — see Pitfall 1. ~40 `ichi` hits exist across `fetch/src` + `analysis/src` (comments/docstrings + a few load-bearing). The literal-grep gate is distinct from (and stricter than) the SC-5 protocol-agnosticism lint, which only forbids protocol-name *branches*. Phase 6 must reconcile this: either (a) scrub `ichi` to generic language, or (b) re-scope REPRO-01's grep to match what SC-5 actually enforces. Flagged as a BLOCKER-grade decision for the planner. |
| REPRO-02 | Same Phase 2–5 pipeline runs end-to-end on Steer with no edits to `fetch/src`/`analysis/src`; empty `git diff` between iter-1-complete and iter-2-complete. | The fetch layer IS protocol-agnostic (`cli.ts` derives `protocols/<cmd>.toml`, `parquet-writer.ts` namespaces by `data/raw/<protocol>/`). BUT `analysis/src/abrigo_x402/cli.py :: materialize` HARDCODES `data/raw/ichi/<pool>` (line 67) and the fit/hedge `--out-dir`/`--run-dir-root` defaults are `data/fits/ichi` — these are CLI-arg-overridable but the materialize path is NOT. Plus the Q9 unified-panel + cross-class-permutation modules that REPRO-02's own dead-code obligation required DO NOT EXIST. See Pitfall 2 + Open Question 1. |
| REPRO-03 (first-step) | Cost-leg lower-bound check runs FIRST; on fail, null-result ships, no pipeline edits. | The verdict is ALREADY pre-resolved at Phase 0 (STRADDLE, `a669d37`); the threshold + straddle rule are in `notes/PRE_REGISTRATION.md §REPRO-03 Threshold`. Phase 6 only OBSERVES + writes `notes/steer_cost_leg_bound.md` with `verdict: FAIL` so `decide_firing_condition` → `null_cost`. The check lives OUTSIDE the frozen source dirs (scripts/ + Makefile glue). See Standard Stack + Architecture Pattern 1. |
| REPRO-04 (enforcement) | cCOP panel construction follows the Phase-0-locked Q-9 decision (V3-anchor-only primary). | `protocols/steer.toml :: panel_construction = "v3-anchor-only"` is set. V3-only is the path. The unified fallback materializes only if BOTH triggers fire during the Steer fit AND the (non-existent) cross-class permutation passes — see Open Question 1 (collision). |
| HEDGE-05 (firing condition a) | Null-result template fires on cost-leg gate failure; deliverable PDF documents the null with disqualifying evidence. | `decide_firing_condition()` already routes condition (a) `null_cost` from a `cost_leg_bound_path` parsing to `verdict: FAIL`. `render_null_result_pdf()` exists but is BROKEN (template path + papermill `-P`). Fix per Decision 4. See Standard Stack + Code Examples. |
</phase_requirements>

## Summary

Phase 6 is a **reproducibility-invariant re-run**, not new capability development. The entire scientific content (cost-leg STRADDLE → `null_cost`) is already pre-determined at Phase 0; Phase 6's job is to *demonstrate* that the frozen pipeline runs on a config-swap (`protocols/steer.toml`) and emits the pre-registered null-result PDF, while proving `git diff fetch/src analysis/src == ∅` across the iteration boundary. The deliverable is `reports/steer_null_result.pdf` headlining the cost-leg evidence with the full DGP/gate output as support.

Three load-bearing realities emerged from reading the code, and they reshape the planning surface:

1. **REPRO-01's `grep -ri "ichi"` gate is currently FAILING (~40 hits).** Most are comments/docstrings; a few are load-bearing (`cli.py` materialize path, decoder ABI fixture name, `cli.ts` command validation). The SC-5 protocol-agnosticism lint (the *authoritative* algorithmic-leak gate) PASSES because it only forbids protocol-name *branches* + factory-address literals + magic fee tiers — NOT the bare string `ichi`. The planner must reconcile REPRO-01's literal-grep wording against SC-5's actual scope.
2. **`analysis/src/abrigo_x402/cli.py :: materialize` hardcodes `data/raw/ichi/<pool>`** (line 67), independent of the `--protocol-toml` arg. A clean Steer config-swap cannot write `data/raw/steer/<pool>` without editing this — a REPRO-02 collision.
3. **The Q9 unified-panel + cross-class-permutation modules were never built.** Phase 0 SC-3 + `Q9_DECISION.md §"Phase 2 Code Obligation"` mandated `analysis/src/abrigo_x402/panel/{unified.py, cross_class_permutation.py}` exist from Phase 2 (dead-code-exercised) precisely so REPRO-02's empty-diff holds if the fallback fires in Phase 6. They do not exist (`panel.py` is a single module, no `panel/` package). If both Q9 triggers fire during the Steer fit, the fallback CANNOT execute without authoring new `analysis/src` code — which COLLIDES with REPRO-02. (See Open Question 1 for why this is unlikely to bite, but it MUST be planned around.)

**Primary recommendation:** Sequence Phase 6 as: (Wave 0) standalone generic-renderer fix as a pre-iteration-2 baseline commit + `make iteration-2-full`/`make leak-check` scaffolding + REPRO-01 reconciliation; (Wave 1) write the pre-registered straddle rule + `notes/steer_cost_leg_bound.md` (FAIL verdict) BEFORE any fetch; (Wave 2) run the frozen pipeline on `steer.toml` via `make iteration-2-full`, emitting `reports/steer_null_result.pdf` via the fixed renderer; (Wave 3) attest empty `git diff fetch/src analysis/src` and acceptance-gate. The materialize-path hardcoding and the absent Q9 modules are the two items the planner must explicitly resolve before claiming REPRO-02.

## Standard Stack

This phase adds **no new libraries**. It reuses the frozen pipeline + already-installed tooling. Versions below are the in-repo pins (verified present on HEAD).

### Core (already in repo, reused unchanged)
| Component | Location | Purpose | Why Standard |
|-----------|----------|---------|--------------|
| `quarto` 1.9.38 | system binary (verified installed) | Renders null-result PDF | Already used by `make report-ichi`; the renderer template `null_result.qmd` targets quarto pdf |
| `abrigo_x402` CLI | `analysis/src/abrigo_x402/cli.py` | `materialize` / `fit` / `hedge` subcommands drive the pipeline | The whole Phase 2–5 pipeline; consumed via config-swap |
| `protocol_spec.load_protocol` | `analysis/src/abrigo_x402/protocol_spec.py` | Python TOML loader (pydantic) | Already protocol-agnostic; drops extra fields; validates anchor_pool/vaults |
| `protocol-spec.ts :: loadProtocol` | `fetch/src/protocol-spec.ts` | TS-side TOML loader (zod) | `cli.ts` derives `protocols/<cmd>.toml` from positional arg — Steer already supported |
| `decide_firing_condition` | `analysis/src/abrigo_x402/hedge/null_result.py` | Routes `null_cost` (condition a) from a `cost_leg_bound_path` → `verdict: FAIL` | Built Phase 4; condition (a) is exactly Steer's path |
| `render_null_result_pdf` | `analysis/src/abrigo_x402/hedge/null_result.py` | Generic HEDGE-05 PDF renderer | **BROKEN — fix in scope (Decision 4)** |
| `make report-ichi` machinery | `Makefile` | SOURCE_DATE_EPOCH determinism + size gate + spot-check curl logging | The reproducibility pattern to mirror for steer null PDF |
| `make verify-reproducibility` | `Makefile` | sha256 pins + PDF content-check (size + verdict strings + HEDGE05 marker + AF-03 forbidden-narrowing strings) | Pattern to extend for steer PDF |

### Supporting (already present)
| Component | Location | When to Use |
|-----------|----------|-------------|
| `assert_no_graph_mainnet_in_ledger` | `analysis/src/abrigo_x402/panel.py:143` | DEMAND-01 enforce: raises on any `endpoint='graph-mainnet'` cost-ledger row. This is the ONLY existing generic cost-leg machinery — it enforces the *fetch-side* demand-window constraint (no paid Graph mainnet), NOT the REPRO-03 lower-bound adjudication. The straddle check is NEW scripts/-level glue, not this. |
| `scripts/lint_artifacts.py` | `scripts/` | PANEL-02 metadata + SC-1 fit_report lint; `ICHI_PANEL_REQUIRED_COLUMNS` frozenset (note: `ICHI_`-prefixed — a REPRO-01 grep hit candidate) |
| `cost-ledger.ts` + 90k cap | `fetch/src/cost-ledger.ts` | FETCH-02 budget gate; protects the cCOP/USDT V3 anchor pull from exceeding free-tier |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Fix `render_null_result_pdf` to use `-M`/meta substitution (no papermill) | Add `papermill` as a tracked dev-dep + keep `-P` | The template ALREADY supports `{{< meta params.firing_condition >}}` (verified in `null_result.qmd` line 29). Switching the renderer to `-M firing_condition:X` (pandoc metadata) needs NO new dependency and is the lower-risk fix. **Recommend `-M` / metadata, not papermill.** See Code Examples. |
| New `scripts/cost_leg_check.py` for the straddle adjudication | Inline bash in the `make iteration-2-full` target | A small Python script is more testable (Nyquist) and keeps the Makefile readable; bash-inline is harder to unit-test. **Recommend a `scripts/`-level tool** invoked by the Makefile. Either keeps the check OUTSIDE the frozen `analysis/src`. |

**Installation:** None. `quarto` is present; no Python/TS deps added (the `-M` renderer fix avoids papermill entirely).

**Version verification:** No registry packages added this phase. `quarto --version` → `1.9.38` (verified). The renderer fix introduces zero new dependencies if the `-M`/metadata path is chosen.

## Architecture Patterns

### Recommended File Layout (additions only — all OUTSIDE the frozen source dirs)
```
scripts/
└── cost_leg_check.py          # NEW: reads steer.toml band + applies pre-registered straddle rule
                               #      → writes notes/steer_cost_leg_bound.md (verdict: FAIL)
                               #      OUTSIDE analysis/src — preserves REPRO-02 empty-diff
notes/
├── PRE_REGISTRATION.md        # APPEND straddle decision rule BEFORE the check runs (already has §REPRO-03 Threshold)
└── steer_cost_leg_bound.md    # NEW: YAML-frontmatter verdict:FAIL doc consumed by decide_firing_condition
reports/
└── steer_null_result.pdf      # NEW deliverable (reports/ is outside frozen dirs)
Makefile                       # ADD iteration-2-full + leak-check (leak-check stub exists, needs ichi-grep layer)
.planning/phases/06-.../
└── 06-VERIFICATION-pre.md     # acceptance grid + REPRO-02 empty-diff attestation
```
The renderer fix touches `analysis/src/abrigo_x402/hedge/null_result.py` (+ possibly `reports/_templates/null_result.qmd`) — this is the ONE allowed `analysis/src` edit, landed as a **standalone pre-iteration-2 baseline commit** (Decision 4) so the empty-diff window opens AFTER it.

### Pattern 1: Cost-leg first-step check lives in scripts/ + Makefile (NOT analysis/src)
**What:** A `scripts/cost_leg_check.py` reads `protocols/steer.toml [protocol.repro_03_verdict]` (already records the 30k–100k band + `result = "STRADDLE"`), applies the pre-registered straddle rule (`not strictly > 100k → FAIL`), and writes `notes/steer_cost_leg_bound.md` with YAML frontmatter `verdict: FAIL`. The `make iteration-2-full` target invokes this FIRST, then runs the pipeline.
**When to use:** This is the REPRO-03 first-step. It must run + commit BEFORE any Steer fetch (AF-03 ordering — the rule predates the verdict).
**Why outside analysis/src:** Keeps `git diff fetch/src analysis/src == ∅` (REPRO-02). The frontmatter format must match `_parse_cost_leg_bound_verdict` (regex `^---\n(.*?)\n---` + `verdict:` key, uppercased → compared to `"FAIL"`).

```python
# Source: contract derived from analysis/src/abrigo_x402/hedge/null_result.py:42-62
# scripts/cost_leg_check.py writes notes/steer_cost_leg_bound.md as:
# ---
# verdict: FAIL
# flag: marginal-demand
# band_lower: 30000
# band_upper: 100000
# free_tier_ceiling: 100000
# rule: "not strictly > 100k → FAIL (pre-registered, AF-03)"
# ---
# (body documents the STRADDLE provenance from steer.toml [protocol.repro_03_verdict])
```

### Pattern 2: HEDGE-05 fires from INSIDE the completed run (not a pre-fetch short-circuit)
**What:** The pipeline runs fully; `cli.py hedge --run-id <steer-run> --cost-leg-bound notes/steer_cost_leg_bound.md --run-dir-root data/fits/steer --reports-pdf reports/steer_null_result.pdf` passes the FAIL-verdict doc, and `decide_firing_condition` returns `null_cost` (condition (a) is evaluated FIRST in the sequential tree). This mirrors ICHI's `null_strip_unavailable` firing from inside its completed Phase-4 run.
**When to use:** Always for Steer — Decision 3 resolves the SC-2-vs-SC-4 tension toward the full re-run.
**Evidence the wiring exists:** `cli.py:257` already exposes `--cost-leg-bound`; `null_result.py:111-115` evaluates condition (a) first; `run_hedge` accepts `run_dir_root`/`reports_pdf` (orchestrator.py:287-289).

### Pattern 3: Config-swap drives the pipeline (with one materialize-path caveat)
**What:** `pnpm -C fetch fetch steer [...]` already works (`cli.ts:99` accepts `steer`; namespaces to `data/raw/steer/`). The Python `cli.py fit`/`hedge` accept `--out-dir`/`--run-dir-root` so they CAN target `data/fits/steer`.
**Caveat (Pitfall 2):** `cli.py materialize` line 67 hardcodes `data/raw/ichi/<pool>` — it does NOT derive the namespace from `--protocol-toml`. A Steer materialize would either write into `data/raw/ichi/` (wrong namespace, REPRO-02-questionable) or require editing `cli.py` (REPRO-02 violation). **The planner MUST resolve this** — see Open Question 1.

### Anti-Patterns to Avoid
- **Re-estimating the demand band to chase pass/fail.** AF-03 violation. The 30k–100k band is pre-committed in `steer.toml`; Phase 6 only OBSERVES.
- **Editing `analysis/src` to make the Steer run work (materialize path, Q9 modules) and counting it inside the empty-diff window.** Any such edit must land as a standalone pre-iteration-2 baseline commit BEFORE the diff window opens (same discipline as the renderer fix), OR be re-scoped out. Silently editing inside the window is a REPRO-02 failure dressed as a pass (AF-03-adjacent).
- **Naming/pre-registering a substitute candidate in Phase 6.** Decision 2 forbids it; that is future-milestone scope.
- **Relabeling the null as a near-miss / partial positive.** The `verify-reproducibility` PDF content-check already greps for forbidden narrowing strings (`"near-miss positive"`, `"directionally positive"`, etc.). The steer PDF check must carry the same AF-03 guard.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Firing-condition decision | A new Steer-specific null router | `decide_firing_condition(... cost_leg_bound_path=...)` (already routes `null_cost` first) | Built + tested in Phase 4; condition (a) is Steer's exact path |
| Null-result PDF render | A bespoke steer.qmd | Fixed generic `render_null_result_pdf` + `null_result.qmd` template | Decision 4 mandates the generic renderer's first production use |
| Demand-window fetch enforcement | A new cost-leg fetch guard | `assert_no_graph_mainnet_in_ledger` (panel.py) + `cost-ledger.ts` 90k cap | Already enforce DEMAND-01 on the fetch side |
| Reproducible PDF determinism | A custom checksum scheme | `SOURCE_DATE_EPOCH` + content-check pattern from `report-ichi`/`verify-reproducibility` | Proven in Phase 5; PDFs aren't byte-pinned (engine /Producer varies) — content-checked instead |
| Cost-leg straddle adjudication | Inline it in `analysis/src` | A `scripts/`-level tool invoked by the Makefile | Keeping it outside frozen dirs is THE mechanism that preserves REPRO-02 |

**Key insight:** Nearly everything Phase 6 needs already exists and is parameterized. The work is *wiring + sequencing + attestation*, plus fixing the one broken generic renderer. The danger is not missing capability — it is accidentally editing a frozen source file (materialize path, Q9 modules) inside the empty-diff window.

## Common Pitfalls

### Pitfall 1: REPRO-01 `grep -ri "ichi"` gate is already failing — and conflicts with SC-5
**What goes wrong:** REPRO-01 (REQUIREMENTS.md line 65) literally says `grep -r "ichi" fetch/src analysis/src` must return zero hits before Iteration 2. Running it on HEAD returns **~40 hits** across both trees: docstrings (`decoders.py` "ICHI vault Deposit/Withdraw"), the materialize path (`cli.py:67`), the fit ABI fixture name (`ichi_vault_abi.json`), `cli.ts:99` (`cmd !== 'ichi'`), `__init__.py` module docstrings, `data/fits/ichi` defaults, `reports/ichi.pdf` defaults, etc.
**Why it happens:** The SC-5 protocol-agnosticism lint (the *authoritative* gate, `fetch/tests/protocol-agnostic.test.ts`) only forbids protocol-name *branches* (`if config.name == 'ichi'`), factory-address literals, and magic fee-tier literals — it deliberately allows the bare string `ichi` in comments and in non-branching code. REPRO-01's literal-grep wording was always stricter than what the codebase was built to satisfy.
**How to avoid:** The planner must make an explicit reconciliation decision (a 2-way-review-grade call):
  - **Option A (scrub):** Replace `ichi` with generic terms in `analysis/src`/`fetch/src` (e.g. "the LP-aggregator vault" not "ICHI vault"; derive ABI fixture name from protocol slug; make materialize namespace protocol-derived). This is itself an `analysis/src` edit → must be a standalone pre-iteration-2 baseline commit (same discipline as the renderer fix).
  - **Option B (re-scope REPRO-01):** Document that REPRO-01's intent is satisfied by the SC-5 algorithmic-leak gate (the load-bearing one) + a NARROWER literal grep (e.g. exclude comments, or grep only for `ichi`-as-branch-condition). This requires an AF-12 / pre-registration note since it changes a requirement's acceptance.
**Warning signs:** A plan that asserts "REPRO-01 leak gate passes" without showing the actual `grep -ri "ichi"` output is hand-waving — the raw command fails today.

### Pitfall 2: `cli.py materialize` hardcodes `data/raw/ichi/` — config-swap can't drive a clean Steer panel
**What goes wrong:** `materialize` (cli.py:67) sets `pool_dir = repo_root / "data" / "raw" / "ichi" / pool` — the `ichi` literal is fixed regardless of `--protocol-toml`. A Steer materialize writes into the `ichi/` namespace (semantically wrong + a REPRO-01 path hit) or needs a code edit (REPRO-02 violation).
**Why it happens:** Phase 2 (Plan 02-10) was built for the ICHI anchor only; the namespace was never generalized to read `spec.protocol.name`.
**How to avoid:** Land a standalone pre-iteration-2 baseline commit that derives the namespace from the loaded protocol (`spec.protocol.name`) — making materialize genuinely protocol-driven. This is the SAME class of fix as the renderer fix and should sit in the SAME Wave-0 baseline-fix commit cluster (BEFORE the empty-diff window). Note `fit`/`hedge` already accept `--out-dir`/`--run-dir-root` overrides, so only `materialize` needs this.
**Warning signs:** A Steer run that produces `data/raw/ichi/0x2AC5.../...parquet` (Steer pool under the ichi namespace) is the tell.

### Pitfall 3: Q9 unified-panel + cross-class-permutation modules don't exist — REPRO-02 collision if the fallback fires
**What goes wrong:** `Q9_DECISION.md §"Phase 2 Code Obligation (REPRO-02 Invariant)"` + ROADMAP Phase-0 SC-3 mandated `analysis/src/abrigo_x402/panel/{unified.py, cross_class_permutation.py, __init__.py}` exist from Phase 2 (dead-code-exercised by `test_unified_panel_synthetic.py` + `test_cross_class_permutation.py`) precisely so that IF the Q9 fallback fires in Phase 6, no new `analysis/src` code is authored (preserving the empty diff). **None of this exists.** There is only `panel.py` (a single module, no `panel/` package). `test_permutation_null.py` is the DEPEND-01 cost×revenue cross-correlogram permutation — NOT the Q9 cross-class (V3/V4/Broker) permutation. ROADMAP SC-5 even says: "if unified, the cross-class permutation test result is committed at `data/fits/steer/<run_id>/q9_pooling_test.json`" — but the test code to produce it doesn't exist.
**Why it happens:** Phase 2 shipped V3-anchor-only for ICHI; the dead-code obligation for the unified path was never executed (the Phase-0 SC-3 obligation was documentary, and Phase 2's actual plans built only the anchor path).
**How to avoid:** The planner must confront this directly. Two sub-cases:
  - **If the V3-only Steer fit does NOT trip both Q9 triggers** (sample ≥ 300 OR CI ≤ 0.4, OR permutation would reject): the fallback never fires, V3-only stands, and the missing modules are moot for *execution* — but REPRO-02's empty-diff is still clean because no new code was needed. `steer.toml` says `swaps_per_30d_observed = 600` and `above_hawkes_floor = true` (600/300 = 2.0×), so sample-size trigger likely does NOT fire → fallback likely does NOT materialize. **This is the expected path.**
  - **If the fit DOES trip both triggers:** executing the fallback requires authoring `panel/unified.py` + `cross_class_permutation.py` — an `analysis/src` edit that COLLIDES with REPRO-02. There is no clean resolution inside Phase 6 without either (a) a pre-iteration-2 baseline commit building these modules (large, risky, and arguably AF-03-adjacent since it's reactive), or (b) documenting that the V3-only fit is interpreted with stated signal scope and the fallback is deferred.
**Recommendation:** Plan for the expected path (V3-only, no fallback) and pre-register — in the PRE_REGISTRATION straddle-rule commit — that IF both triggers fire, the disposition is "fallback deferred; V3-only reported with signal-scope caveat" rather than authoring reactive modules. This keeps REPRO-02 intact and honest. **Flag this as a prominent MAJOR for the 2-way review.** Note: since the cost-leg STRADDLE already fires `null_cost` as the HEADLINE regardless of the DGP fit, the Q9 fallback question is largely academic for the deliverable — but the fit still RUNS (Decision 3), so the trigger evaluation still happens and must be handled.

### Pitfall 4: The renderer's papermill `-P` dependency + relative template path
**What goes wrong:** `render_null_result_pdf` (null_result.py:191) passes `-P firing_condition:<X>` which requires `papermill` (NOT installed — verified absent). Also the default `template=Path("reports/_templates/null_result.qmd")` is resolved against the subprocess CWD (pytest runs from `analysis/`, so it doesn't resolve → "No valid input files passed to render"). The sibling `Makefile :: render-null-result-pdf` (line 196-203) has the same `--execute-param` papermill dependency.
**Why it happens:** The renderer was scaffolded in Phase 4 (Plan 04-08) and skip-guarded on `shutil.which("quarto")`; installing quarto in Phase 5 un-skipped the test and exposed it (documented in `FOLLOWUP_generic_null_result_renderer_bug.md`).
**How to avoid:**
  - Switch the renderer to `-M firing_condition:<X>` (pandoc metadata, no papermill) — the template ALREADY reads `{{< meta params.firing_condition >}}` (line 29) AND `r params$firing_condition` (line 18). Verify the metadata path works end-to-end with quarto 1.9.38.
  - Anchor the template + output paths to the repo root (compute from `Path(__file__)` or pass `cwd=REPO_ROOT` to `subprocess.run`).
  - Update the Makefile `render-null-result-pdf` target to drop `--execute-param`.
  - Mirror `report-ichi`'s `SOURCE_DATE_EPOCH` determinism for the steer PDF.
**Warning signs:** `test_pdf_dual_signature_when_quarto_available` still skipping (quarto IS present now, so it should RUN and PASS post-fix). The acceptance per the FOLLOWUP doc: `make render-null-result-pdf FIRING=null_cost` renders a >5KB PDF carrying the visible H1 + HEDGE05 marker, from repo root, with no untracked dep.

### Pitfall 5: No CI exists — leak-check + verify-reproducibility are manual/pre-commit only
**What goes wrong:** ROADMAP SC-3 says "CI enforces via `make leak-check`" and SC-4 references CI. The Phase-5 DevOps review flagged that **no CI exists in the repo**. Treating `make leak-check` as CI-enforced is fantasy.
**Why it happens:** The repo never wired GitHub Actions; leak-check is a Makefile target + the SC-5 test runs under `vitest`/`pytest` locally + pre-commit.
**How to avoid:** Phase 6 should (a) extend the existing `make leak-check` target to ADD the `grep -ri "ichi"` layer (it currently only greps protocol-name branches + addresses + fee tiers — verified Makefile lines 161-173), (b) document that enforcement is pre-commit/manual (CI wiring is explicitly Deferred), and (c) NOT claim CI enforcement in the VERIFICATION doc. The `make iteration-2-full` target is a NEW target (only a help-text stub references it today — it does not exist in the Makefile).

## Code Examples

### The renderer fix: switch `-P` → `-M` (no papermill) + repo-root anchoring
```python
# Source: current broken code at analysis/src/abrigo_x402/hedge/null_result.py:187-194
# CURRENT (broken — papermill + cwd-relative template):
cmd = [
    "quarto", "render", str(template),
    "--no-cache", "--to", "pdf",
    "-P", f"firing_condition:{firing_condition}",   # <-- papermill (absent)
    "--output", output_path.name,
    "--output-dir", str(output_path.parent),
]
subprocess.run(cmd, check=True, capture_output=True, text=True)  # cwd-relative

# RECOMMENDED FIX (metadata substitution, repo-root anchored, no new dep):
REPO_ROOT = Path(__file__).resolve().parents[4]   # null_result.py -> hedge -> abrigo_x402 -> src -> analysis -> repo? VERIFY depth
template_abs = (REPO_ROOT / template).resolve()
cmd = [
    "quarto", "render", str(template_abs),
    "--no-cache", "--to", "pdf",
    "-M", f"firing_condition:{firing_condition}",   # pandoc metadata; template reads {{< meta params.firing_condition >}}
    "--output", output_path.name,
    "--output-dir", str((REPO_ROOT / output_path.parent).resolve()),
]
subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=REPO_ROOT)
# NOTE: verify parents[N] depth against actual layout: analysis/src/abrigo_x402/hedge/null_result.py
#       -> repo root is parents[4] (hedge=0? no): file.parents -> [hedge, abrigo_x402, src, analysis, REPO]. parents[4]=REPO. CONFIRM at impl time.
```

### Driving the Steer pipeline (config-swap), per the existing CLI surface
```bash
# Source: verified against analysis/src/abrigo_x402/cli.py + Makefile + fetch/src/cli.ts
# (1) cost-leg first-step check (NEW scripts/ tool) — writes notes/steer_cost_leg_bound.md (verdict: FAIL)
python scripts/cost_leg_check.py --protocol protocols/steer.toml --out notes/steer_cost_leg_bound.md
# (2) fetch (already protocol-agnostic; namespaces to data/raw/steer/)
pnpm -C fetch fetch steer --pool 0x2AC5baA668A8A58FD0e302B9896717484fd217B0 --from <N> --to <M>
# (3) materialize — CAVEAT: cli.py:67 hardcodes data/raw/ichi/ (Pitfall 2 — needs baseline fix)
uv run python -m abrigo_x402.cli materialize --pool 0x2AC5... --from-block <N> --to-block <M> --protocol-toml protocols/steer.toml
# (4) fit (overridable out-dir)
uv run python -m abrigo_x402.cli fit --pool 0x2AC5... --panel-path data/raw/steer/0x2AC5.../<range>.parquet --out-dir data/fits/steer
# (5) hedge — passes the FAIL-verdict cost-leg doc → decide_firing_condition returns null_cost
uv run python -m abrigo_x402.cli hedge --run-id <steer-run> --stage all \
    --run-dir-root data/fits/steer \
    --cost-leg-bound notes/steer_cost_leg_bound.md \
    --reports-pdf reports/steer_null_result.pdf
```

### The cost-leg-bound frontmatter contract (what the parser expects)
```python
# Source: analysis/src/abrigo_x402/hedge/null_result.py:42-62 (_parse_cost_leg_bound_verdict)
# Regex: re.match(r"---\n(.*?)\n---", text, re.DOTALL); yaml.safe_load; fm.get("verdict").upper() == "FAIL"
# So notes/steer_cost_leg_bound.md MUST begin with:
# ---
# verdict: FAIL
# ---
# Anything else (no frontmatter, no verdict key) → None → condition (a) does NOT fire.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Phase 0 stub said Steer "does NOT run a full Phase 1-5 cycle" (steer.toml header comment, memo-only null at Phase 0) | Decision 3: full Phase 2–5 RUNS regardless of the STRADDLE, to prove REPRO-02 | 2026-05-29 (Phase 6 CONTEXT) | The `steer.toml` header comment ("Iter-2 does NOT run a full Phase 1-5 cycle") is now SUPERSEDED by CONTEXT Decision 3 — the planner should note the comment is stale, not authoritative. |
| Renderer uses `-P`/papermill | Renderer uses `-M`/pandoc metadata | This phase | No new dependency; first production use of the generic null-result renderer |

**Deprecated/outdated:**
- `protocols/steer.toml` header comment lines 8-12 ("this file is a stub … Iter-2 does NOT run a full Phase 1-5 cycle") — CONTRADICTED by CONTEXT Decision 3. The file's *data* (band, addresses, panel_construction) is authoritative; the *prose comment* about not running a cycle is stale.
- `hedge_05_fires = true # memo-only null at Phase 0` (steer.toml:34) — the memo-only framing is superseded; the null now fires from inside the completed run as a full `reports/steer_null_result.pdf`.

## Open Questions

1. **Materialize-path hardcoding + missing Q9 modules vs. REPRO-02 — the central tension.**
   - What we know: `cli.py materialize` hardcodes `data/raw/ichi/`; the Q9 unified-panel + cross-class-permutation modules don't exist; both would require `analysis/src` edits to support a fully-clean Steer run / fallback.
   - What's unclear: whether the planner scrubs+generalizes these as pre-iteration-2 baseline commits (clean but more work), or re-scopes (document the materialize-namespace fix as a baseline commit, and pre-register that the Q9 fallback is deferred-not-built if both triggers fire).
   - Recommendation: (a) materialize-namespace generalization → standalone baseline commit (small, clean, removes a REPRO-01 hit); (b) Q9 fallback → pre-register "deferred with signal-scope caveat" since V3-only sample (600/30d) is 2× above the 300 floor so the sample trigger likely won't fire, AND the cost-leg STRADDLE headlines the null regardless. Both decisions need 2-way-review sign-off.

2. **REPRO-01 grep reconciliation: scrub vs. re-scope.**
   - What we know: `grep -ri "ichi" fetch/src analysis/src` returns ~40 hits today; SC-5 (the authoritative gate) passes.
   - What's unclear: which option (scrub to generic / re-scope the requirement) the project wants.
   - Recommendation: scrub the load-bearing hits (materialize path, ABI fixture name, `cli.ts` validation can stay as a generic command-allowlist) AND re-word REPRO-01's acceptance to match SC-5's algorithmic-leak intent, with a PRE_REGISTRATION note (AF-12 discipline). Comments/docstrings mentioning "ICHI" as the iter-1 example are arguably fine; the requirement should say so explicitly.

3. **Renderer template: does `{{< meta params.firing_condition >}}` + `r params$firing_condition` both resolve under `-M` (no params block execution)?**
   - What we know: the template has BOTH a `params:` block (papermill/quarto-params style) and `{{< meta >}}` shortcodes; `-M` sets pandoc metadata, not quarto `params`.
   - What's unclear: whether `r params$firing_condition` (line 18 H1) resolves without the params being injected by papermill.
   - Recommendation: at implementation time, render once with `-M firing_condition:null_cost` and `pdftotext` the output to confirm the H1 shows `null_cost`; if the `params$` reference fails, convert it to a `{{< meta firing_condition >}}` shortcode in the H1 too (template edit lives in `reports/` if the template moves, or is part of the baseline analysis/src-adjacent fix — confirm template location is `reports/_templates/` which is OUTSIDE frozen dirs → free to edit).

## Validation Architecture

> `.planning/config.json` was not found / nyquist_validation not explicitly false → section included.

### Test Framework
| Property | Value |
|----------|-------|
| Framework (Python) | `pytest` 9.0.3 (analysis/), thread-pinned BLAS (Pattern I — `os.environ.setdefault` OMP/MKL/OpenBLAS/NumExpr=1 before numpy import) |
| Framework (TS) | `vitest` (fetch/) — hosts the authoritative SC-5 leak gate |
| Config file | `analysis/pyproject.toml` (pytest), `fetch/vitest.config.ts` |
| Quick run command | `cd analysis && uv run pytest tests/test_null_result_template.py -x` |
| Full suite command | `cd analysis && uv run pytest` + `cd fetch && pnpm test` + `make verify-reproducibility` + `make leak-check` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REPRO-01 | `grep -ri "ichi"` clean (post-scrub) + SC-5 lint passes | leak-gate | `make leak-check` (extend with ichi-grep layer) + `cd fetch && pnpm test protocol-agnostic` | ⚠️ leak-check exists but lacks ichi layer; SC-5 test exists |
| REPRO-02 | Empty `git diff` on frozen dirs across iter boundary | smoke | `git diff <iter1-complete-sha> HEAD -- fetch/src analysis/src` (expect empty) | ❌ Wave 0 — author the attestation check (a script or VERIFICATION step) |
| REPRO-03 | Straddle rule → `notes/steer_cost_leg_bound.md` verdict:FAIL, written BEFORE fetch | unit + ordering | `python scripts/cost_leg_check.py ...` + `pytest scripts/test_cost_leg_check.py` + `git log` ordering proof | ❌ Wave 0 — author `scripts/cost_leg_check.py` + its test |
| REPRO-04 | `panel_construction == "v3-anchor-only"` honored; Q9 trigger evaluated | unit | assert `load_protocol("protocols/steer.toml").protocol` panel field; trigger-eval logged in fit_report | ✅ steer.toml set; ⚠️ Q9 fallback modules absent (Pitfall 3) |
| HEDGE-05 (a) | `decide_firing_condition` returns `null_cost` on FAIL doc; PDF renders | unit + render | `pytest tests/test_null_result_template.py::test_pdf_dual_signature_when_quarto_available` + `make render-null-result-pdf FIRING=null_cost` | ✅ decision test exists (fixture `hedge_05_null_cost`); ⚠️ render test currently exposes the papermill bug |

### Sampling Rate
- **Per task commit:** `cd analysis && uv run pytest tests/test_null_result_template.py -x` (the renderer-fix RED→GREEN) + `pytest scripts/test_cost_leg_check.py` for the straddle tool.
- **Per wave merge:** `make leak-check` + `cd fetch && pnpm test protocol-agnostic` + targeted analysis suite.
- **Phase gate:** Full analysis suite (thread-pinned) + `cd fetch && pnpm test` + `make verify-reproducibility` (extended for steer PDF) + the REPRO-02 empty-diff attestation, all green before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `scripts/cost_leg_check.py` — reads `steer.toml [protocol.repro_03_verdict]`, applies pre-registered straddle rule, writes `notes/steer_cost_leg_bound.md` (verdict:FAIL). Covers REPRO-03.
- [ ] `scripts/test_cost_leg_check.py` (or `analysis/tests/`) — asserts the FAIL verdict + frontmatter shape matching `_parse_cost_leg_bound_verdict`.
- [ ] Generic-renderer fix in `analysis/src/abrigo_x402/hedge/null_result.py` (`-M` substitution + repo-root anchoring) — **standalone pre-iteration-2 baseline commit** (Decision 4). Un-skips + greens `test_pdf_dual_signature_when_quarto_available`.
- [ ] `make iteration-2-full` target (NEW — does not exist; only a help-text stub) + extend `make leak-check` with the `grep -ri "ichi"` layer + extend `make render-null-result-pdf` to drop `--execute-param`.
- [ ] Materialize-namespace generalization in `cli.py` (Pitfall 2) — baseline commit if Option A chosen.
- [ ] REPRO-02 empty-diff attestation mechanism (a VERIFICATION step or small script) pinning the iter-1-complete baseline sha (last frozen-dir commit ≈ `b68352e`, or the PR#1 merge `87991ac` as the iteration-1-complete marker).
- [ ] `reports/MANIFEST.md` extension or a steer-specific content-check in `verify-reproducibility` for `reports/steer_null_result.pdf` (mirror the ichi PDF content-check: size>50KB + `null_cost` string + HEDGE05 marker + AF-03 forbidden-narrowing guard).

## Sources

### Primary (HIGH confidence) — direct reads on HEAD (2026-05-29)
- `analysis/src/abrigo_x402/cli.py` — materialize/fit/hedge subcommands; `data/raw/ichi/` hardcode (line 67); `--out-dir`/`--run-dir-root`/`--cost-leg-bound`/`--reports-pdf` args
- `analysis/src/abrigo_x402/hedge/null_result.py` — `decide_firing_condition` (condition (a) first), `render_null_result_pdf` (papermill `-P` bug), `_parse_cost_leg_bound_verdict` frontmatter contract
- `analysis/src/abrigo_x402/hedge/orchestrator.py` — `run_hedge(run_dir_root, cost_leg_bound_path, reports_pdf)` signature
- `analysis/src/abrigo_x402/protocol_spec.py` + `panel.py` (`assert_no_graph_mainnet_in_ledger`)
- `fetch/src/cli.ts` (`cmd !== 'ichi' && cmd !== 'steer'`, `protocols/<cmd>.toml`), `fetch/src/cache/parquet-writer.ts` (`data/raw/<protocol>/` namespace), `fetch/tests/protocol-agnostic.test.ts` (SC-5 forbidden-pattern set)
- `reports/_templates/null_result.qmd` (params block + `{{< meta >}}` shortcode), `Makefile` (`report-ichi`, `verify-reproducibility`, `leak-check`, `render-null-result-pdf`)
- `protocols/steer.toml` (STRADDLE band, addresses, `panel_construction`, stale "no full cycle" comment), `protocols/ichi.toml`, `protocols/_schema.toml`
- `notes/PRE_REGISTRATION.md` (§REPRO-03 Threshold PASS/STRADDLE/FAIL, §Q-9 Fallback Pre-Registration), `notes/Q9_DECISION.md` (V3-anchor-only + Phase-2 Code Obligation for unified/permutation modules)
- `grep -ri "ichi" fetch/src analysis/src` → ~40 hits (REPRO-01 currently failing); `ls analysis/src/abrigo_x402/panel/` → no package (only `panel.py`)
- `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md §Phase 6`, `.planning/STATE.md`
- `.../05-.../_artifacts/FOLLOWUP_generic_null_result_renderer_bug.md` (the documented renderer bug + acceptance)
- `quarto --version` → 1.9.38; `papermill` absent from analysis env

### Secondary (MEDIUM confidence)
- CONTEXT.md decisions (locked by the user; relayed verbatim in User Constraints)

### Tertiary (LOW confidence)
- (none — all claims verified against the working tree)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all reused components read directly; no new packages.
- Architecture: HIGH on existing wiring (CLI args, firing tree, fetch namespace); MEDIUM on the renderer-fix `parents[N]` depth (must confirm at impl time).
- Pitfalls: HIGH — REPRO-01 grep failure, materialize hardcode, and missing Q9 modules all reproduced via direct grep/ls on HEAD.

**Research date:** 2026-05-29
**Valid until:** ~2026-06-28 (stable — pinned codebase; re-verify the `grep -ri "ichi"` count and the iter-1-complete baseline sha if commits land before planning).
