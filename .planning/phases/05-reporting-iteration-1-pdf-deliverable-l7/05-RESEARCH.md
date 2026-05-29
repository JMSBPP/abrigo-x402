# Phase 5: Reporting + Iteration-1 PDF Deliverable (L7) - Research

**Researched:** 2026-05-29
**Domain:** Reproducible scientific reporting — Quarto/TinyTeX PDF render, deterministic spot-check + reproducibility manifest, cost-prior sensitivity sweep, near-miss null-result framing
**Confidence:** HIGH (the verdict artifacts, render scaffolding, Makefile, and test patterns were read directly from disk; the one genuinely-open design — gitignored-artifacts reproducibility — is resolved below with a recommended option and rationale)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Near-miss narrative framing (load-bearing):**
- Headline = methodology-validation + honest near-miss. Lead: the free-tier pipeline works end-to-end and CORRECTED a false null; real self-excitation found (η≈0.6, LR rejects NHPP), but the held-out KS gate was missed by a knife-edge. Frame v1.0 as a validated method + an honest 3/4.
- Dedicated methodology section + 3-run comparison table: synthetic-mislabel (`0afc6af38e24`, true η=0.05 via tick normalized-kernel) → real-LS-null (`ae9e3ba17900`, null_lr artifact) → real-MLE-3/4 (`bdaf5c7ba5a2`, η=0.600). Name the three root-cause bugs: mislabeled fixture, projection-trick CI, kernel-blind β=0.1. This IS the v1.0 scientific contribution.
- KS knife-edge stated explicitly + anti-fishing provenance. Print p=0.0474 plainly, show both legs (0.0474 / 0.0564), name the locked min-leg aggregator, reference the disposition memo's rejected post-hoc changes. Refusal-to-narrow is a credibility asset.
- Concrete "what unlocks certification" (v2 path) section: power-law kernel (fixes KS via long-memory, BUT extrapolates the tail at n≈700) vs more data (cleaner, but slow on free-tier). Honest staging toward Phase 6 / Iteration 2.
- Convexity-justified / calibration-caveated distinction throughout: the convex hedge SHAPE is robust (all 4 convex-dominance conditions pass → η≈0.6 fat tails dominate linear); the precise Carr-Madan strip is uncalibratable on the degenerate joint_dist (held-out n=79 < 101 floor) → that is the `null_strip_unavailable` firing, not "no hedge."

**Render pipeline:**
- Quarto from `.qmd`, reusing the Phase-4 templates. Author `reports/ichi.qmd` composing `reports/_templates/null_result.qmd` + `_evidence_branches.qmd`; `make report-ichi` runs `quarto render`. SC-1's literal `.ipynb` is satisfied-in-spirit by the `.qmd` source — documented deviation (deliverable contract is "PDF via Quarto", which `.qmd` satisfies).
- Build auto-installs TinyTeX: `make report-ichi` runs `quarto install tinytex` if the LaTeX engine is missing, then renders. The `quarto` binary itself remains a build prerequisite (auto-install covers the LaTeX engine, not quarto). Tension with offline discipline accepted for the build target only.
- Tests stay skip-guarded on missing quarto (`quarto_skipped` sentinel) so the 207-green suite is preserved. The build target is the hard-require path; the test suite is not.
- No silent markdown fallback — markdown-only output is rejected; the PDF is the mandated deliverable (SC-1).

**Sensitivity sweep presentation (REPORT-03):**
- Primary metric tracked across the 3×3 grid = convex-dominance Δ (cost-of-convexity vs linear hedge) under `{rate_per_event × 0.5, 1.0, 1.5}` × `{USD_per_query × 0.5, 1.0, 1.5}`. Shows the instrument-choice call (convex beats linear) survives ±50% cost-prior perturbation.
- `sensitivity_sweep.json` lives at `data/fits/ichi/bdaf5c7ba5a2/sensitivity_sweep.json` with downstream estimates RE-RUN per cell (not approximated/interpolated), per SC-3.
- Caveat: cost leg is MODELED not paid (x402-on-Celo settlement non-existent), so the dominance margin is partly stipulative — state honestly.

**Spot-check + reproducibility (REPORT-02 / REPORT-04):**
- 5 rows selected by seeded uniform random, seed derived from run_id `bdaf5c7ba5a2`, drawn from the 778-event panel. Deterministic + re-derivable; seed recorded in MANIFEST.md.
- Blockscout URLs of the form `https://celo.blockscout.com/tx/0x...`.
- HTTP-200 verification = build-time `curl` with logged results, network-optional. `make report-ichi` curls each of the 5 URLs and logs HTTP status per row; if no network, logs "unverified (no network)" rather than failing the build (satisfies SC-2's "or the build script logs the verification per row").
- MANIFEST.md pins checksums of inputs + derived artifacts; `make verify-reproducibility` recomputes-and-matches, exits 0 only on full match. Pins: panel parquet sha256 (`a72a4ee…`), lockfile SHAs, subgraph block-pins, run_id artifact checksums (fit_report / gate_report / firing_condition / sensitivity_sweep).

**Cycle-closure (terminal step of Iteration 1):**
- PDF completion TRIGGERS cycle closure: push origin → PR to upstream (`wvs-finance/abrigo-x402:master`) → merge upstream, only after the PDF renders + `make verify-reproducibility` green + phase VERIFICATION passes. AF-03 carries into the merge: never merge a verdict dressed as a pass.

**Per-task specialized-agent assignment (MANDATORY):**
- Every implementation task in the Phase 5 plan MUST name the closest-fit AI-agency specialist as its executor — not a generic executor. Planner records the chosen specialist + one-line why, per task.
- The report-document writeup is the headline case: prose CONCISE, carries the mathematical equations (Hawkes kernel, branching ratio, LR statistic, Carr-Madan strip, KS time-rescaling), reads like a research paper. Assign the research-paper-capable writing specialist (ROADMAP names Technical Writer; use it or the closest catalog specialist for academic/mathematical writeups).
- The writing task MUST invoke project SKILLS: `latex-econ-model`, `notation-clean`, `latex-doc`, `read-paper`. Skills are the mechanism; the specialist agent is the driver.
- DISTINCT from (and composes with) the global two-step REVIEWER process (Reality Checker + one specialist reviewer on the plan).
- Other tasks get fit-for-purpose specialists (render-pipeline/Makefile + reproducibility-manifest → DevOps-Automator-class; sensitivity-sweep numerical → analytics/quant-class; numbers-match verification → Analytics Reporter consult).

### Claude's Discretion
- Exact PDF section ordering / typography / figure styling (within methodology-validation + near-miss frame).
- Whether the 3-run comparison is one table or table+figure.
- Exact `make report-ichi` / `make verify-reproducibility` target wiring.
- Sweep visualization form (heatmap vs annotated table) for the 3×3 convex-dominance grid.

### Deferred Ideas (OUT OF SCOPE)
- Power-law kernel sweep (DGP-V2-01) + more-data certification — the v2 path; NAMED in the PDF's "what unlocks certification" section but NOT executed in Phase 5.
- Iteration-2 / Steer cCOP/USDT (Phase 6) — the PDF's cycle-closure PR sets up Phase 6, but Steer work is its own phase.
- Deployed Solidity hedge contracts — Iteration 3+.
- Re-fit / re-hedge of the DGP — Phase 04.1.1 is closed; Phase 5 reports, does not recompute the fit.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| REPORT-01 | Render Iteration-1 deliverable as `reports/ichi.pdf` via Quarto; markdown-only not acceptable | §Quarto Composition & PDF Render; the `make report-ichi` → `quarto render reports/ichi.qmd` target wiring + TinyTeX auto-install + the SC-1 size+`.pdf`-exists check. Reuses `null_result.qmd` + `_evidence_branches.qmd` (read on disk). |
| REPORT-02 | Spot-check: 5 random panel rows with Blockscout URLs, manually verifiable | §Spot-Check Determinism. Panel has `txHash` column (full 0x hashes, 832 rows). Seed = derived from run_id `bdaf5c7ba5a2`; `numpy.random.default_rng(seed)` + `choice(n, 5, replace=False)`. URLs `https://celo.blockscout.com/tx/0x...`. Build-time `curl -I` with network-optional logging. |
| REPORT-03 | Cost-leg prior sensitivity sweep: ±50% perturbation of `(rate_per_event, USD_per_query)`, all downstream estimates re-run | §Sensitivity Sweep — INCLUDES THE LARGEST GAP: `rate_per_event`/`USD_per_query` do not exist anywhere in `analysis/src/` today, and there is no computed "convex-dominance Δ" margin. The planner must define the cost-leg → dominance-margin map. Locked grid values in PRE_REGISTRATION §Prior Parameters. |
| REPORT-04 | Reproducibility manifest: block-pins, lockfiles, output checksums; sufficient for fresh clone to reproduce headline numbers | §Reproducibility Manifest + §The Gitignored-Artifacts Decision (recommended Option C-hybrid). Fills the `verify-reproducibility` Makefile STUB (lines 47-49). |
</phase_requirements>

## Summary

Phase 5 is a **reporting / packaging** phase, not an estimation phase. Every headline number already exists on disk under `data/fits/ichi/bdaf5c7ba5a2/` (read and verified during this research). The dominant risk is not technical difficulty — it is **AF-12 scope creep**: the temptation to recompute the fit, narrow the knife-edge verdict, or silently fall back to markdown. The verdict is FIXED: `gate_passes=FALSE` (3/4), `firing_condition=null_strip_unavailable`, η=0.600, LR rejects NHPP (observed_stat=561.29, p=0.0), held-out KS leg-0 p=0.0474 (knife-edge miss, min-leg aggregator). The report READS these artifacts; it does NOT recompute.

Two findings change the planning calculus materially. **(1)** `quarto` is NOT on PATH in this environment, `analysis/uv.lock` exists but there is NO root `uv.lock` and NO `package-lock.json` (the JS workspace uses `pnpm-lock.yaml` at repo root). REPORT-04's manifest must pin the lockfiles that *actually exist*: `analysis/uv.lock` + `pnpm-lock.yaml`. **(2)** The REPORT-03 sweep's "convex-dominance Δ" metric and its `rate_per_event`/`USD_per_query` inputs **do not exist in the codebase** — `grep -rn "rate_per_event\|USD_per_query" analysis/src/` returns zero hits, and the four-condition gate (`falsification.py`) computes pass/fail booleans, not a cost-of-convexity margin. The planner must specify (a) a small cost-leg model that consumes the two priors and (b) a dominance-margin definition, then re-run it per cell. This is the single largest planning unknown and is flagged HIGH-priority below.

The gitignored-artifacts reproducibility question (the CONTEXT-flagged open item) resolves cleanly: **Option C-hybrid** — un-ignore and commit the small JSON/parquet artifacts of the single `bdaf5c7ba5a2` run dir as repro evidence (they are tiny: fit_report 32 KB, the rest < 5 KB each, residuals.parquet 4 KB), pin their checksums in MANIFEST.md, and have `verify-reproducibility` recompute-and-match those committed files plus the committed panel inputs. This sidesteps scipy multi-start non-determinism entirely (no re-fit on a fresh clone) while still catching drift.

**Primary recommendation:** Author `reports/ichi.qmd` as a near-miss specialization of the existing null-result template; wire `make report-ichi` (quarto render → PDF, with `quarto install tinytex` self-heal) and `make verify-reproducibility` (sha256 recompute-and-match); commit the `bdaf5c7ba5a2` run-dir artifacts as repro evidence under a `.gitignore` exception; define the cost-leg→dominance-Δ map explicitly before running the 3×3 sweep; and gate cycle-closure (push origin → PR upstream → merge) on a green render + green verify + passing VERIFICATION, never on a narrowed verdict.

## Standard Stack

The toolchain is already in the repo. This phase adds no new estimation libraries; it adds a render path and a small cost-leg model. Verify versions against what is pinned, not training data.

### Core
| Tool | Version | Purpose | Why Standard (this repo) |
|------|---------|---------|--------------------------|
| Quarto CLI | (binary, build prerequisite — NOT auto-installed) | `.qmd` → PDF render with embedded Python code cells | Already the chosen toolchain (Phase-4 `null_result.qmd`, Makefile `render-lr-diagnostic`/`render-null-result-pdf`). One toolchain, reuses scaffolding. |
| TinyTeX | auto-install via `quarto install tinytex` | LaTeX engine that compiles the Quarto-generated `.tex` to PDF + renders math | Lightweight TeX distribution; `quarto install tinytex` is the canonical install path. Per Quarto docs, the built-in engine auto-installs missing LaTeX packages and runs LaTeX multiple times to resolve refs/bib. (HIGH — confirmed via quarto.org/docs/output-formats/pdf-engine.html) |
| Python (uv) | per `analysis/uv.lock` | Quarto Python code cells + the seeded spot-check draw + the sweep driver | `analysis/` is `uv`-managed (`analysis/pyproject.toml` + `analysis/uv.lock`). Quarto runs `.qmd` Python cells via the active interpreter. |
| polars | per `analysis/uv.lock` | Read the 832-row panel parquet for the spot-check draw | Already the panel I/O library project-wide. |
| numpy | per `analysis/uv.lock` | Deterministic seeded RNG for the 5-row draw + per-cell sweep numerics | `numpy.random.default_rng(seed)` is the deterministic generator; thread-pinning (Pattern I) already established. |

### Supporting
| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| `pdftotext` / `pdfinfo` | system (`/usr/bin`, confirmed present) | Verify rendered PDF dual-signature + size in tests | The existing `test_null_result_template.py` greps `pdftotext`/`pdfinfo`; reuse for SC-1 PDF assertions. |
| `curl` | system | Build-time HTTP-200 check on the 5 Blockscout URLs | REPORT-02 SC-2 "or build script logs the verification per row" — `curl -I -s -o /dev/null -w "%{http_code}"` with network-optional fallback. |
| `sha256sum` | system (coreutils) | MANIFEST checksum recompute in `make verify-reproducibility` | Mirrors the existing `verify-cache-idempotency` target's `sha256sum` pattern. |

### Project Skills (mechanism for the writeup task — NOT new dependencies)
| Skill | Path | Role in Phase 5 |
|-------|------|-----------------|
| `latex-econ-model` | `~/.claude/skills/latex-econ-model/` | Typeset the stochastic model (Hawkes kernel φ(t)=Σα·e^(−βt), branching ratio η=ρ(α/β), Carr-Madan strip, LR statistic) with Econometrica-standard notation. Workflow stage = theory; structures Environment → Technology → Equilibrium → Solution. |
| `notation-clean` | `~/.claude/skills/notation-clean/` | Audit the math notation to publication standard: inline one-shot symbols, no Greek-for-non-parameters, no collisions with reserved symbols (β, r, t, T, k, κ). Read `references/notation-rules.md` first. Invoke in `--mode both` on `reports/ichi.qmd` math. |
| `latex-doc` | `~/.claude/skills/latex-doc/` | LaTeX/Quarto math correctness: equation environments, `figure`/`\caption`/`\label`, fix compile errors. Routing: `check` for review, `add` for new sections. Standard academic ordering (Abstract → Intro → Model → Data → Results → Discussion → Conclusion). |
| `read-paper` | `~/.claude/skills/read-paper/` | When citing the locked sources (Filimonov & Sornette 2014, Brown et al. 2002, Daw & Pender 2017, Kirchner 2015, Bacry power-law for the v2 section). Citekey/author-year lookup against `references.bib`. Note this skill's bib path is `/home/jmsbpp/projects/references.bib` (global), not repo-local. |

**Installation / availability:**
```bash
# quarto must be installed by the operator (build prerequisite, NOT auto-installed):
#   per CONTEXT — the build target self-installs only TinyTeX, not the quarto binary.
quarto --version          # currently: "command not found" in this env → operator installs
quarto install tinytex    # the report-ichi target runs this if the LaTeX engine is missing
# Python toolchain already present:
cd analysis && uv sync    # restores from analysis/uv.lock
```

**Version verification:** `analysis/uv.lock` is the authoritative Python pin (257 KB, present). There is NO root `uv.lock` and NO `package-lock.json`; the JS workspace pin is `pnpm-lock.yaml` at repo root. The MANIFEST (REPORT-04) MUST cite these two files, not the FEATURES.md-era names. (HIGH — confirmed by `ls` + `find`.)

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Quarto `.qmd` | nbconvert from `.ipynb` | REPORT-01 allows either, but CONTEXT locks Quarto (reuses the Phase-4 templates + activates the 3 skipped quarto tests). `.ipynb` would orphan the existing scaffolding. SC-1's literal `.ipynb` is treated as satisfied-in-spirit by `.qmd` — documented deviation. |
| TinyTeX | full TeX Live / `tectonic` | TinyTeX is the Quarto-native lightweight default; full TeX Live is heavy and unnecessary; `tectonic` would diverge from the auto-install path CONTEXT locks. |
| Re-fit on fresh clone for repro | Commit the run-dir artifacts (Option C-hybrid) | scipy multi-start MLE is NOT byte-reproducible across machines even thread-pinned (the byte-identity tests pin the *fit input → run_id* path, not cross-machine MLE convergence). Committing the artifacts is the only way to make a fresh clone reproduce the *headline numbers* without a 213-second fit run + non-determinism risk. See §The Gitignored-Artifacts Decision. |

## Architecture Patterns

### Recommended Layout
```
reports/
├── ichi.qmd                  # NEW — the Iteration-1 deliverable source (near-miss specialization)
├── ichi.pdf                  # NEW — rendered deliverable (REPORT-01; committed or pinned per Option C)
├── MANIFEST.md               # NEW — reproducibility manifest (REPORT-04)
├── _templates/
│   ├── null_result.qmd       # REUSE — dual-signature shell + params$firing_condition
│   └── _evidence_branches.qmd# REUSE — the null_strip_unavailable branch already written
└── _diagnostics/             # existing — lr_null_dist.png etc.
data/fits/ichi/bdaf5c7ba5a2/
├── fit_report.json           # READ — η, LR, KS, held-out, gate_criteria, gate_passes
├── gate_report.json          # READ — 4/4 convex-dominance conditions
├── firing_condition.json     # READ — null_strip_unavailable
├── strip_degenerate.json     # READ — char_func_build_error, recommended_method=none
├── joint_dist.json           # READ — degenerate_reason (n_min=79 ≤ 101)
├── stress_report.json        # READ — divergence NaN (degenerate path)
├── residuals.parquet         # READ — KS residuals
└── sensitivity_sweep.json    # NEW — the 3×3 convex-dominance Δ grid (REPORT-03)
```

### Pattern 1: Read-only artifact consumption (NON-NEGOTIABLE)
**What:** Every number in the PDF is loaded from the on-disk JSON; the report never re-invokes the fit/hedge orchestrators.
**When to use:** All of Phase 5 except the sensitivity sweep (which re-runs only the *cost-leg/dominance* layer per cell, never the DGP fit).
**Example:**
```python
# Source: pattern of reports/_templates/null_result.qmd load-substrate cell (read on disk)
import json
from pathlib import Path
RUN = Path("../data/fits/ichi/bdaf5c7ba5a2")
fit  = json.loads((RUN / "fit_report.json").read_text())
gate = json.loads((RUN / "gate_report.json").read_text())
fire = json.loads((RUN / "firing_condition.json").read_text())
eta        = fit["hawkes_mv_params"]["branching_ratio"]          # 0.5999724…
lr_p       = fit["lr_test"]["p_value"]                           # 0.0
lr_stat    = fit["lr_test"]["observed_stat"]                     # 561.2948…
ks_leg0_p  = fit["ks_rescaled_time"]["per_leg"][0]["p_value"]    # 0.04735…
ks_leg1_p  = fit["ks_rescaled_time"]["per_leg"][1]["p_value"]    # 0.05644…
gate_pass  = fit["gate_passes"]                                  # False
firing     = fire["firing_condition"]                            # "null_strip_unavailable"
```

### Pattern 2: Deterministic seeded spot-check (REPORT-02)
**What:** Derive an integer seed from the run_id string, seed `numpy.random.default_rng`, draw 5 distinct row indices from the 832-row panel, emit Blockscout URLs.
**When to use:** The spot-check section + its test.
**Example:**
```python
# Source: composition of panel schema (txHash present) + numpy default_rng determinism
import numpy as np, polars as pl, hashlib
run_id = "bdaf5c7ba5a2"
seed = int(hashlib.sha256(run_id.encode()).hexdigest()[:8], 16)  # deterministic, record in MANIFEST
df = pl.read_parquet(".../67378253_67896653.parquet")            # 832 rows, txHash col present
idx = np.random.default_rng(seed).choice(df.height, size=5, replace=False)
rows = df[sorted(idx.tolist())]
urls = [f"https://celo.blockscout.com/tx/{h}" for h in rows["txHash"].to_list()]
```
NOTE the panel parquet is 832 rows, while the *fit* used n=778 events (382+396 per leg after the PANEL-04 phantom-transfer filter). The CONTEXT says "778-event panel"; the planner must decide whether the spot-check draws from the 832-row raw panel or the 778 filtered events — recommend drawing from the **832-row parquet** (it carries `txHash`; the filtered leg events do not retain a clean tx mapping) and stating the count explicitly. Record the exact file + row count + seed in MANIFEST so the draw is re-derivable.

### Pattern 3: Network-optional build-time verification (REPORT-02 / SC-2)
**What:** `curl -I` each URL, capture HTTP status, log per row; on network failure log `unverified (no network)` instead of failing the build.
**Example:**
```bash
# Source: SC-2 "or the build script logs the verification per row" clause
for url in "${URLS[@]}"; do
  code=$(curl -s -I -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "000")
  if [ "$code" = "000" ]; then echo "$url -> unverified (no network)"; else echo "$url -> HTTP $code"; fi
done
```

### Pattern 4: Recompute-and-match reproducibility gate (REPORT-04)
**What:** `make verify-reproducibility` reads MANIFEST.md, recomputes sha256 of each pinned file, compares; exit 0 only on full match, exit 1 on any mismatch.
**Example:** mirror the existing `verify-cache-idempotency` target (`sha256sum | cut -d" " -f1`, compare, exit 1 on mismatch). Pin: panel parquet (`a72a4eeaf2805…`), `analysis/uv.lock`, `pnpm-lock.yaml`, the committed run-dir artifacts, `reports/ichi.pdf`. Subgraph block-pins come from the fit_report's `blockRange` `[67378253, 67896653]` + `chainId` 42220.

### Anti-Patterns to Avoid
- **Recomputing the fit in the report** — the PDF must READ `bdaf5c7ba5a2`'s artifacts. Re-running `cli.py fit` is an AF-12 silent-rescope and a determinism hazard.
- **Markdown fallback** — if quarto/TinyTeX is missing, the build target must FAIL, not emit `.md`. (Tests may skip; the build target may not.)
- **Verdict narrowing in prose** — never write "near-miss positive", "directionally positive", "pass with caveat". The disposition memo enumerates 9+ rejected post-hoc changes; cite them. `gate_passes=FALSE` stays FALSE.
- **Interpolating the sweep** — SC-3 requires per-cell re-run, not a fitted surface over the 3×3 grid.
- **Pinning non-existent lockfiles** — `package-lock.json` and root `uv.lock` do NOT exist. Pin `analysis/uv.lock` + `pnpm-lock.yaml`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF generation from `.qmd` | A bespoke pandoc/LaTeX wrapper | `quarto render` (already in Makefile precedent) | Quarto handles multi-pass LaTeX, auto package install, math, code-cell execution. |
| LaTeX engine bootstrap | Manual TeX Live install scripts | `quarto install tinytex` | Canonical, lightweight, doesn't touch system PATH (per Quarto docs). |
| Deterministic RNG | `random.seed` + `random.sample` | `numpy.random.default_rng(seed)` | Reproducible across versions; `default_rng` is the recommended modern generator (Pattern I thread-pinning already in repo). |
| Checksum compare | A Python diff harness | `sha256sum` + shell compare (mirror `verify-cache-idempotency`) | One Makefile idiom, no new code surface. |
| Math notation discipline | Ad-hoc symbol choices | `notation-clean` + `latex-econ-model` skills | Econometrica-standard, avoids one-shot Greek + reserved-symbol collisions. |

**Key insight:** The hard parts (fit, gate, strip, copula) are DONE and frozen. The only genuinely new *code* is (a) the spot-check draw, (b) the cost-leg→dominance-Δ sweep, (c) two Makefile targets. Keep each minimal.

## Common Pitfalls

### Pitfall 1: The cost-leg sweep has no existing entry point
**What goes wrong:** REPORT-03 says "all downstream estimates re-run" across the `(rate_per_event, USD_per_query)` grid, but neither symbol exists in `analysis/src/`, and the four-condition gate produces booleans, not a cost-of-convexity Δ.
**Why it happens:** The cost leg is MODELED-not-paid (PRE_REGISTRATION); the priors were locked in the pre-reg doc but never wired into a cost model — Phases 0–4 never needed a dollar figure, only the convex-dominance booleans.
**How to avoid:** The planner MUST specify, BEFORE the sweep task: (1) a minimal cost-leg cost function `C(rate_per_event, USD_per_query) = events × rate_per_event × USD_per_query` (the natural reading of the pre-reg interpretation: queries/event × $/query × event count), and (2) the dominance-Δ definition — e.g., the margin by which the convex (Panoptic-replicated) hedge's modeled payoff under the η≈0.6 fat-tailed joint beats the linear hedge, net of the modeled cost leg, per cell. The four conditions in `gate_report.json` (vol_of_vol=1.18, skew=1.85, η=0.60, depeg) already establish *that* convex dominates; the sweep shows *by how much* and that the sign of Δ survives ±50%. State the stipulative nature plainly (no x402-on-Celo settlement exists). Whether Δ even depends on the cost priors must be made explicit — if the dominance margin is computed on the joint distribution and the cost priors only scale a common additive term, the sweep may show Δ is *robust by construction*; that is itself a reportable, honest finding. **Do not invent a κ-complexity index** (CLAUDE.md non-negotiable: x402 v2 carries no first-class κ).
**Warning signs:** A plan task that says "re-run the sweep" without first defining what quantity is re-run.

### Pitfall 2: scipy MLE is not byte-reproducible across machines
**What goes wrong:** A fresh clone running `make verify-reproducibility` that *re-fits* would get a slightly different η (multi-start L-BFGS-B basins differ across BLAS builds), failing the checksum match — or worse, silently producing a different headline.
**Why it happens:** The Phase-3 SC-5 byte-identity tests pin the *panel → run_id derivation* and require thread-pinned BLAS; they do NOT guarantee cross-machine MLE convergence to identical floats.
**How to avoid:** Option C-hybrid — commit the run-dir artifacts; `verify-reproducibility` matches the committed files, never re-fits. The MANIFEST documents the fit-run as a one-time provenance prerequisite (commit `12cf99f`, run_id `bdaf5c7ba5a2`), not a step a verifier re-executes.
**Warning signs:** A `verify-reproducibility` target that calls `cli.py fit`.

### Pitfall 3: quarto absent in CI/dev breaks the green suite
**What goes wrong:** Activating the 3 skipped quarto tests as hard-requires would turn the 207-green suite red on any env without quarto (this env has none).
**Why it happens:** quarto is a heavyweight binary not installed by `uv sync`.
**How to avoid:** Keep the `quarto_skipped` sentinel pattern (`if not shutil.which("quarto"): pytest.skip(...)`) — already in `test_null_result_template.py`. The PDF dual-signature test stays skip-guarded; only the `make report-ichi` build target hard-requires quarto.
**Warning signs:** Removing the `shutil.which("quarto")` guard.

### Pitfall 4: The `null_result.qmd` template hardcodes a different title/signature
**What goes wrong:** `null_result.qmd` is the *generic HEDGE-05* template titled "HEDGE-05 Null Result" with the `HEDGE05-NULL-RESULT-V1` marker. `reports/ichi.pdf` is the *Iteration-1 deliverable* — a fuller research-paper-style document, not just the null-result shell.
**Why it happens:** CONTEXT says "compose from" the partials, but the deliverable is a superset (methodology section, 3-run table, sweep, spot-check, v2 path), not a clone.
**How to avoid:** `reports/ichi.qmd` is a NEW document that `{{< include >}}`s `_evidence_branches.qmd` for the `null_strip_unavailable` evidence block, and reuses the dual-signature pattern, but has its own title, abstract, model section, and the four new sections. The planner should treat the partials as reusable *blocks*, not the whole document.
**Warning signs:** `reports/ichi.qmd` that is just `null_result.qmd` with a renamed title.

### Pitfall 5: Off-by-population in the spot-check (832 vs 778)
**What goes wrong:** CONTEXT says "778-event panel"; the parquet is 832 rows. Drawing 5 from the wrong population makes the seed non-re-derivable.
**How to avoid:** Pin the exact file path, row count, and seed in MANIFEST; recommend drawing from the 832-row parquet (it carries `txHash`). State the relationship (832 raw rows → 778 arrival events post PANEL-04 filter) in the spot-check prose.

## Code Examples

### `make report-ichi` target (DevOps-Automator-class task)
```makefile
# Source: composition of Makefile render-null-result-pdf precedent (line 148-154) + Quarto tinytex docs
report-ichi:
	@command -v quarto >/dev/null 2>&1 || { echo "report-ichi: FAIL — quarto binary required (build prerequisite, not auto-installed)"; exit 1; }
	@quarto list tools 2>/dev/null | grep -qi tinytex || quarto install tinytex
	cd reports && quarto render ichi.qmd --to pdf --output ichi.pdf
	@test -f reports/ichi.pdf || { echo "report-ichi: FAIL — no PDF emitted (markdown fallback rejected)"; exit 1; }
	@SIZE=$$(stat -c%s reports/ichi.pdf); [ "$$SIZE" -gt 51200 ] || { echo "report-ichi: FAIL — PDF $${SIZE}B < 50KB (SC-1)"; exit 1; }
	@echo "report-ichi: PASS — reports/ichi.pdf ($${SIZE}B)"
```

### `make verify-reproducibility` target (fills the STUB at lines 47-49)
```makefile
# Source: mirror of verify-cache-idempotency sha256 idiom (Makefile line 89-97)
verify-reproducibility:
	@bash -c 'set -euo pipefail; \
	  FAIL=0; \
	  while IFS=" " read -r expected path; do \
	    [ -z "$$path" ] && continue; \
	    actual=$$(sha256sum "$$path" 2>/dev/null | cut -d" " -f1); \
	    if [ "$$actual" != "$$expected" ]; then echo "MISMATCH: $$path ($$actual != $$expected)"; FAIL=1; \
	    else echo "OK: $$path"; fi; \
	  done < <(grep -E "^[a-f0-9]{64}  " reports/MANIFEST.md | sed "s/  / /"); \
	  [ "$$FAIL" = 0 ] && echo "verify-reproducibility: PASS" || { echo "verify-reproducibility: FAIL"; exit 1; }'
```
(Exact MANIFEST line format is Claude's Discretion; the recompute-and-match + exit 0/1 contract is the load-bearing part.)

### `.gitignore` exception for the repro-evidence run dir (Option C-hybrid)
```gitignore
# Source: existing .gitignore data/raw exception pattern (lines 42-46)
# Phase 5 REPORT-04: commit the single canonical run dir as reproducibility evidence.
data/fits/*
!data/fits/ichi/
!data/fits/ichi/bdaf5c7ba5a2/
!data/fits/ichi/bdaf5c7ba5a2/*.json
!data/fits/ichi/bdaf5c7ba5a2/*.parquet
!data/fits/ichi/bdaf5c7ba5a2/*.md
```
(Confirm the current `.gitignore` `data/fits` rule — the read showed `data/raw/*` rules at lines 42-46; the planner must locate the `data/fits` ignore line and add the negation exceptions beneath it.)

## The Gitignored-Artifacts Decision (THE flagged open question — RESOLVED)

CONTEXT flagged three options. Evidence-based recommendation:

| Option | Mechanism | Verdict |
|--------|-----------|---------|
| (a) un-ignore + commit the `bdaf5c7ba5a2` run dir | Negation rules in `.gitignore`; checksum the committed files | **RECOMMENDED (as C-hybrid).** Artifacts are tiny (fit_report 32 KB; gate/firing/strip/joint/stress JSON < 5 KB each; residuals.parquet 4 KB; total < 50 KB). A fresh clone HAS the exact headline numbers; no re-fit, no non-determinism. |
| (b) `verify-reproducibility` re-derives the fit from committed panel + lockfiles | Re-run `cli.py fit` on a fresh clone | **REJECTED.** scipy multi-start MLE is not byte-reproducible across BLAS builds (Pitfall 2); the 213-second fit is slow; and re-deriving risks an AF-12 recompute-in-report. The SC-5 byte-identity guarantees the *run_id derivation*, not cross-machine float-identical convergence. |
| (c) MANIFEST pins committed inputs + PDF, documents the fit as a prerequisite | Inputs + outputs pinned, fit-run is a documented manual step | **ADOPTED as the framing layer ON TOP of (a).** The MANIFEST documents the fit provenance (commit `12cf99f`, run_id, dataHash `a72a4ee…`) as a one-time step a reproducer can re-run if they wish, but `verify-reproducibility` validates the committed artifacts, not a re-fit. |

**Recommended: Option C-hybrid = (a) committed artifacts + (c) MANIFEST framing.** Un-ignore the single `bdaf5c7ba5a2` run dir (JSON + parquet + CORRECTIONS.md), pin every file's sha256 in MANIFEST.md alongside the panel parquet + lockfiles + the PDF, and have `verify-reproducibility` recompute-and-match the committed set. This satisfies REPORT-04's "sufficient for a fresh clone to reproduce the headline numbers" literally (the numbers are in the committed JSON) while catching drift in inputs OR outputs. Note: the panel parquet itself (`data/raw/ichi/.../67378253_67896653.parquet`) is gitignored under `data/raw/*` and is NOT trivially committable (it is larger and the `data/raw` exceptions only whitelist the cost-ledger). The planner must decide whether to (i) also un-ignore the panel parquet for full repro, or (ii) pin the panel by sha256 in MANIFEST and document its regeneration from the committed `pool_events.jsonl`/`vault_state.jsonl` cache via `cli.py materialize` (the Plan 04.1-01 pure-rerun path, cost-ledger burn = 0). Recommend (ii): pin the panel sha256 + document the deterministic `materialize` regeneration, since the raw JSONL cache is the true content-addressed source.

## Sensitivity Sweep Mechanics (REPORT-03 — HIGH-priority gap)

**Locked grid (PRE_REGISTRATION §Prior Parameters):**
- `rate_per_event`: 3-point grid; central 5, sweep `{2.5, 5, 7.5}` (the ±50% of central) — NOTE pre-reg also states a `(1,5,10)` grid as the "sensitivity sweep" wording; the CONTEXT locks the ±50% framing `{×0.5, ×1.0, ×1.5}` = `{2.5, 5, 7.5}`. **The planner must reconcile (1,5,10) vs (2.5,5,7.5)** — the CONTEXT's "±50%" + the 3×3 framing points to `{2.5,5,7.5}`; the pre-reg `(1,5,10)` is the older verbatim. Recommend `{2.5, 5, 7.5}` to match the locked ±50% CONTEXT decision and the `USD_per_query` ±50% which is unambiguously `{2.5e-6, 5e-6, 7.5e-6}`. Surface this reconciliation explicitly in the plan.
- `USD_per_query`: `{2.5e-6, 5e-6, 7.5e-6}` (±50% of $5e-6 headline).

**Where the priors enter:** NOWHERE today. There is no cost model. The planner defines a minimal cost-leg model (Pitfall 1). The four-condition gate (`falsification.py :: evaluate_four_conditions`) is the convex-dominance evidence, but it is parameter-free w.r.t. the cost priors — its condition-4 `gate_decision_func` defaults to permissive and uses jump-diffusion triples `{λ_J, μ_J, σ_J}`, not query-cost priors.

**Recommended sweep design (analytics/quant-class task):**
1. Define `cost_leg_usd(cell) = n_events × rate_per_event × USD_per_query` (events = 778, or the fitted leg counts).
2. Define `dominance_Δ(cell)` = convex-hedge modeled value − linear-hedge modeled value, under the η≈0.6 fat-tailed joint, net of `cost_leg_usd`. The convex/linear comparison can reuse the stress-test / strip machinery's *modeled* payoff under the fitted joint — but since the strip is degenerate (`null_strip_unavailable`), the planner likely uses the gate's convex-dominance *conditions* + a stipulated payoff differential rather than the (unavailable) calibrated strip price. State this stipulation honestly.
3. Loop the 3×3 grid, RE-RUN the dominance computation per cell (no interpolation), write `data/fits/ichi/bdaf5c7ba5a2/sensitivity_sweep.json` with a documented schema: `{run_id, grid: [{rate_per_event, USD_per_query, cost_leg_usd, dominance_delta, convex_dominates: bool}], all_cells_convex_dominant: bool, caveat: "cost leg modeled-not-paid; partly stipulative"}`.
4. The PDF presents the 3×3 as a heatmap or annotated table (Claude's Discretion) with the honest caveat.

**Honest-finding caveat to surface:** if Δ's *sign* (convex dominates) is invariant across all 9 cells, the sweep demonstrates robustness; if Δ is additively shifted by a common cost term that doesn't flip the sign, say so — the dominance is convexity-driven (fat tails), not cost-prior-driven. This is the convexity-justified vs calibration-caveated distinction the CONTEXT mandates.

## Specialist-Agent + Skills Integration

Per CONTEXT's MANDATORY per-task-specialist directive, suggested assignments (planner finalizes + records one-line why):

| Task | Specialist (AI-agency catalog) | Why | Skills invoked |
|------|-------------------------------|-----|----------------|
| Report writeup (`reports/ichi.qmd` prose + math) | **Technical Writer** (ROADMAP Phase-5 primary) — or closest academic-writing specialist | Research-paper-style, concise, equation-carrying narrative | `latex-econ-model`, `notation-clean`, `latex-doc`, `read-paper` (citations) |
| Render pipeline + Makefile + MANIFEST + verify-reproducibility | **DevOps Automator** | Build targets, TinyTeX bootstrap, checksum gate, `.gitignore` exception | — |
| Sensitivity sweep (cost-leg model + 3×3 Δ) | **Analytics/quant specialist** (e.g. an analytics engineer) | Numerical per-cell re-run, sweep JSON schema | `polars`, `statsmodels` if needed |
| Numbers-match verification (PDF == artifacts) | **Analytics Reporter** consult (per ROADMAP) | Confirms every PDF figure equals the on-disk artifact value | — |
| Spot-check + curl | DevOps Automator or the analytics specialist | Deterministic draw + network-optional curl | `polars`, `numpy` |

**Skills compose with Quarto thus:** the writeup specialist authors `reports/ichi.qmd`; the math lives in `$$…$$` LaTeX blocks inside the `.qmd`; `latex-econ-model` shapes the model section's notation (Hawkes φ(t), η=ρ(α/β), LR Λ, Carr-Madan strip, KS time-rescaling Λ(t)); `notation-clean` audits in `--mode both` against `notation-rules.md`; `latex-doc check` validates compile correctness of the generated `.tex`; `read-paper` resolves the locked citations (Filimonov & Sornette 2014, Brown et al. 2002, Daw & Pender 2017, Kirchner 2015, Bacry power-law). These are skills run by the agent on the `.qmd`, then `quarto render` compiles the math through TinyTeX.

## State of the Art

| Old Approach | Current Approach | When | Impact |
|--------------|------------------|------|--------|
| `random.seed` + `random.sample` | `numpy.random.default_rng(seed)` | NumPy 1.17+ | Reproducible, recommended generator API |
| Manual TeX Live install | `quarto install tinytex` | Quarto 1.x | One-command lightweight LaTeX, auto package install, PATH-safe |
| `.ipynb` + nbconvert | Quarto `.qmd` | Quarto 1.x | Code-cell execution + native PDF + reusable partials/includes |

**Deprecated/outdated for this repo:**
- `package-lock.json` / root `uv.lock` references in FEATURES.md TS-14 — neither exists; the real pins are `analysis/uv.lock` + `pnpm-lock.yaml`.
- The pre-reg `(1,5,10)` rate_per_event grid wording vs the CONTEXT-locked ±50% `{2.5,5,7.5}` — reconcile (see Sensitivity Sweep).

## Open Questions

1. **Cost-leg → dominance-Δ definition (HIGH).**
   - What we know: priors are locked `(rate_per_event, USD_per_query)`; the four convex-dominance *conditions* pass; cost leg is modeled-not-paid.
   - What's unclear: there is no cost model and no Δ metric in code; what exact quantity does each cell re-compute?
   - Recommendation: planner specifies `cost_leg_usd = events × rate × $/query` + a stipulated convex-vs-linear payoff differential under the fitted joint; document the stipulation; surface whether Δ's sign is cost-prior-invariant (convexity-driven) as the honest finding.

2. **rate_per_event grid: `(1,5,10)` vs `(2.5,5,7.5)` (MEDIUM).**
   - What we know: pre-reg says both `(1,5,10)` and "±50%"; CONTEXT locks "±50% / ×0.5,1.0,1.5".
   - Recommendation: use `{2.5,5,7.5}` to honor the CONTEXT ±50% lock; note the pre-reg `(1,5,10)` verbatim in a footnote.

3. **Spot-check population: 832 raw rows vs 778 filtered events (LOW).**
   - Recommendation: draw from the 832-row parquet (carries `txHash`); state the 832→778 PANEL-04 filter relationship; pin file+count+seed in MANIFEST.

4. **Panel parquet committability for full repro (MEDIUM).**
   - What we know: `data/raw/*` is gitignored; only the cost-ledger is whitelisted; the parquet is content-addressed from the JSONL cache.
   - Recommendation: pin the panel sha256 in MANIFEST + document deterministic `cli.py materialize` regeneration (cost-ledger burn 0) rather than committing the parquet.

## Validation Architecture

> nyquist_validation is `true` in `.planning/config.json` — this section is REQUIRED.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (per `analysis/` suite; 207-green baseline, thread-pinned BLAS Pattern I) |
| Config file | `analysis/pyproject.toml` |
| Quick run command | `cd analysis && uv run pytest tests/test_null_result_template.py -x` |
| Full suite command | `cd analysis && uv run pytest -x` (under OMP=MKL=OpenBLAS=NumExpr=1) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REPORT-01 | `make report-ichi` exits 0 and PDF > 50 KB exists | smoke (build) | `make report-ichi && test $$(stat -c%s reports/ichi.pdf) -gt 51200` | ❌ Wave 0 (new Makefile target) |
| REPORT-01 | PDF dual-signature greppable (`pdftotext`/`pdfinfo`) | integration (quarto-skip-guarded) | `cd analysis && uv run pytest tests/test_null_result_template.py::test_pdf_dual_signature_when_quarto_available` | ✅ exists, skip-guarded — extend for ichi.qmd |
| REPORT-02 | Seeded 5-row draw is deterministic from run_id | unit | `cd analysis && uv run pytest tests/test_spot_check.py::test_seeded_draw_deterministic -x` | ❌ Wave 0 |
| REPORT-02 | Blockscout URLs well-formed (`https://celo.blockscout.com/tx/0x...`) | unit | same file, `::test_blockscout_urls_wellformed` | ❌ Wave 0 |
| REPORT-03 | `sensitivity_sweep.json` schema valid + 9 cells + no interpolation flag | unit | `cd analysis && uv run pytest tests/test_sensitivity_sweep.py -x` | ❌ Wave 0 |
| REPORT-03 | Each cell's dominance-Δ re-computed (not interpolated) | unit | same file, `::test_per_cell_recompute` | ❌ Wave 0 |
| REPORT-04 | `make verify-reproducibility` exits 0 on match, 1 on mismatch | smoke (build) | `make verify-reproducibility; echo $$?` (expect 0); tamper-then-expect-1 in a test | ❌ Wave 0 (fills STUB lines 47-49) |
| REPORT-04 | MANIFEST pins exist + sha256 of committed artifacts match | unit | `cd analysis && uv run pytest tests/test_manifest.py -x` | ❌ Wave 0 |
| AF-03/AF-12 | Verdict not narrowed: PDF text contains `gate_passes` FALSE + `0.0474` + `null_strip_unavailable`; no "pass with caveat" | integration (quarto-skip-guarded) | grep `pdftotext reports/ichi.pdf -` for required strings + assert-absent forbidden strings | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd analysis && uv run pytest tests/test_<new_file>.py -x` (thread-pinned)
- **Per wave merge:** `cd analysis && uv run pytest -x` (full suite, single-threaded BLAS — confirm still green incl. the 3 quarto-skips)
- **Phase gate:** full suite green + `make report-ichi` green + `make verify-reproducibility` green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `analysis/tests/test_spot_check.py` — covers REPORT-02 (seeded determinism + URL format)
- [ ] `analysis/tests/test_sensitivity_sweep.py` — covers REPORT-03 (schema + per-cell recompute)
- [ ] `analysis/tests/test_manifest.py` — covers REPORT-04 (pins present + sha256 match + mismatch→exit-1)
- [ ] Extend `analysis/tests/test_null_result_template.py` — add an ichi.qmd dual-signature + verdict-not-narrowed test (keep `quarto_skipped` guard)
- [ ] `Makefile` targets: `report-ichi` (new), `verify-reproducibility` (fill STUB at lines 47-49) — add to `.PHONY`
- [ ] `.gitignore` exception for `data/fits/ichi/bdaf5c7ba5a2/` (Option C-hybrid)
- [ ] No framework install needed — pytest + quarto-skip pattern already present; quarto binary is an operator prerequisite (this env lacks it → tests must stay skip-guarded)

## Sources

### Primary (HIGH confidence — read directly from disk this session)
- `data/fits/ichi/bdaf5c7ba5a2/{fit_report,gate_report,firing_condition,strip_degenerate,joint_dist,stress_report}.json` — all headline numbers verified (η=0.5999724, LR observed_stat=561.2948 p=0.0, KS leg-0 p=0.04735 leg-1 p=0.05644, gate_passes=false, firing=null_strip_unavailable, 4/4 conditions pass)
- `reports/_templates/null_result.qmd` + `_evidence_branches.qmd` — dual-signature shell + the `null_strip_unavailable` branch (already written)
- `Makefile` — `verify-reproducibility` STUB (lines 47-49), `render-null-result-pdf` quarto precedent (148-154), `verify-cache-idempotency` sha256 idiom (89-97), `lint-artifacts` (68-84)
- `analysis/tests/test_null_result_template.py` — `quarto_skipped` skip-guard + pdftotext/pdfinfo dual-signature pattern
- `analysis/src/abrigo_x402/hedge/falsification.py` — four-condition gate (no cost-prior input; condition-4 jump-triple)
- `notes/PRE_REGISTRATION.md` — §Prior Parameters (rate/USD grids), cost-leg-modeled-not-paid, locked verdict gate
- `.planning/phases/04.1.1-*/_artifacts/DISPOSITION_MEMO_04_1_1_ks_halt.md` — the rejected post-hoc changes (anti-fishing provenance)
- ICHI panel parquet schema via polars — 832 rows × 33 cols, `txHash` present (full 0x)
- `.gitignore` (data/raw rules), `.planning/config.json` (nyquist_validation=true), `git remote -v`, `ls` (quarto absent, analysis/uv.lock + pnpm-lock.yaml present, no package-lock.json)
- `~/.claude/skills/{latex-econ-model,notation-clean,latex-doc,read-paper}/SKILL.md` — skill indexes
- `CLAUDE.md` §Cycle-closure integration (push origin → PR upstream → merge upstream)

### Secondary (MEDIUM-HIGH confidence)
- quarto.org/docs/output-formats/pdf-engine.html — `quarto install tinytex` (PATH-safe; `--update-path` to expose), built-in engine auto-installs LaTeX packages + multi-pass; Pandoc supports pdflatex/xelatex/lualatex/tectonic/latexmk

### Tertiary (LOW confidence — flag for validation)
- None. All load-bearing claims verified against on-disk artifacts or official Quarto docs.

## Metadata

**Confidence breakdown:**
- Verdict numbers / artifacts to report: HIGH — read directly from `bdaf5c7ba5a2/`
- Render pipeline (Quarto/TinyTeX): HIGH — Quarto docs + existing Makefile precedent + read templates
- Spot-check determinism: HIGH — panel schema confirmed (txHash present), numpy default_rng standard
- Reproducibility design: HIGH — Option C-hybrid resolved with evidence (artifact sizes, scipy non-determinism, real lockfile names)
- Sensitivity sweep: MEDIUM — the mechanism is clear but the cost-leg→Δ map DOES NOT EXIST YET and must be designed by the planner (flagged HIGH-priority gap, not a confidence issue about facts)
- Specialist + skills integration: HIGH — skills read; CONTEXT directive explicit

**Research date:** 2026-05-29
**Valid until:** 2026-06-28 (stable — the verdict is frozen; only Quarto/TinyTeX version drift is a fast-moving risk, low impact)
