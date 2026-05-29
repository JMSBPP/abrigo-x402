# Phase 5: Reporting + Iteration-1 PDF Deliverable (L7) - Context

**Gathered:** 2026-05-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Ship the Iteration-1 PDF deliverable `reports/ichi.pdf` (Quarto) with: (REPORT-01) the rendered PDF, (REPORT-02) a 5-row Blockscout spot-check, (REPORT-03) the cost-leg prior sensitivity sweep, (REPORT-04) a reproducibility manifest + `make verify-reproducibility`. Completes Iteration 1 and CLOSES the development cycle (push origin → PR to upstream → merge upstream).

**The verdict being reported is fixed (from Phase 04.1.1, run_id `bdaf5c7ba5a2`):** gate_passes=FALSE (3/4), firing_condition=null_strip_unavailable. η≈0.600 (LR rejects NHPP p=0.0; held-out Hawkes +114 nats), but the held-out KS missed α=0.05 on a knife-edge (leg-0 p=0.0474). This is a NULL/NEAR-MISS report — NOT a positive-strip report. The verdict must NOT be flipped, narrowed, or relabeled (AF-03; HALT disposition memo on record).

**Out of scope (own phases):** Iteration-2 / Steer (Phase 6); the power-law kernel sweep + more-data certification (v2 / DGP-V2-01); any re-fit or re-hedge of the DGP (Phase 04.1.1 is closed); deployed Solidity hedge contracts (Iteration 3+).
</domain>

<decisions>
## Implementation Decisions

### Near-miss narrative framing (the load-bearing decision)
- **Headline = methodology-validation + honest near-miss.** Lead: the free-tier pipeline works end-to-end and CORRECTED a false null; real self-excitation found (η≈0.6, LR rejects NHPP), but the held-out KS gate was missed by a knife-edge. Frame v1.0 as a validated method + an honest 3/4.
- **Dedicated methodology section + 3-run comparison table.** Show synthetic-mislabel (`0afc6af38e24`, true η=0.05 via tick normalized-kernel) → real-LS-null (`ae9e3ba17900`, null_lr artifact) → real-MLE-3/4 (`bdaf5c7ba5a2`, η=0.600). Name the three root-cause bugs: mislabeled fixture, projection-trick CI, kernel-blind β=0.1. This IS the v1.0 scientific contribution.
- **KS knife-edge stated explicitly + anti-fishing provenance.** Print p=0.0474 plainly, show both legs (0.0474 / 0.0564), name the locked min-leg aggregator, reference the disposition memo's 9 rejected post-hoc changes. The refusal-to-narrow is a credibility asset, not a weakness to hide.
- **Concrete "what unlocks certification" (v2 path) section.** Name both routes with the tradeoff: power-law kernel (fixes KS via long-memory, BUT extrapolates the tail at n≈700) vs more data (cleaner, but slow on free-tier). Honest staging toward Phase 6 / Iteration 2.
- **Convexity-justified / calibration-caveated distinction** runs throughout: the convex hedge SHAPE is robust (all 4 convex-dominance conditions pass → η≈0.6 fat tails dominate linear); the precise Carr-Madan strip is uncalibratable on the degenerate joint_dist (held-out n=79 < 101 floor) → that's the `null_strip_unavailable` firing, not "no hedge."

### Render pipeline
- **Quarto from `.qmd`, reusing the Phase-4 templates.** Author `reports/ichi.qmd` composing the existing `reports/_templates/null_result.qmd` + `_evidence_branches.qmd` partials; `make report-ichi` runs `quarto render`. One toolchain, reuses scaffolding, activates the 3 currently-skipped quarto tests. SC-1's literal `.ipynb` is treated as satisfied-in-spirit by the `.qmd` source — planner notes this as an explicit, documented deviation (the deliverable contract is "PDF via Quarto", which `.qmd` satisfies).
- **Build auto-installs TinyTeX.** `make report-ichi` runs `quarto install tinytex` if the LaTeX engine is missing, then renders. NOTE: the `quarto` binary itself remains a build prerequisite (auto-install covers the LaTeX engine, not quarto). Tension with offline discipline is accepted for the build target only.
- **Tests stay skip-guarded** on missing quarto (the existing `quarto_skipped` sentinel pattern) so the 207-green suite is preserved on envs without quarto. The build target (`make report-ichi`) is the hard-require path; the test suite is not.
- **No silent markdown fallback** — markdown-only output is rejected; the PDF is the mandated deliverable (SC-1).

### Sensitivity sweep presentation (REPORT-03)
- **Primary metric tracked across the 3×3 grid = convex-dominance Δ** (cost-of-convexity vs linear hedge) under `{rate_per_event × 0.5, 1.0, 1.5}` × `{USD_per_query × 0.5, 1.0, 1.5}`. Shows how the instrument-choice call (convex beats linear) survives ±50% cost-prior perturbation.
- Underlying `sensitivity_sweep.json` lives at `data/fits/ichi/bdaf5c7ba5a2/sensitivity_sweep.json` with downstream estimates RE-RUN per cell (not approximated/interpolated), per SC-3.
- Caveat to surface: the cost leg is MODELED not paid (x402-on-Celo settlement non-existent per PRE_REGISTRATION), so the dominance margin is partly stipulative — state this honestly.

### Spot-check + reproducibility (REPORT-02 / REPORT-04)
- **5 rows selected by seeded uniform random**, seed derived from run_id `bdaf5c7ba5a2`, drawn from the 778-event panel. Deterministic + re-derivable; the seed is recorded in MANIFEST.md so a fresh clone draws the same 5 rows. No cherry-picking.
- Blockscout URLs of the form `https://celo.blockscout.com/tx/0x...`.
- **HTTP-200 verification = build-time curl with logged results, network-optional.** `make report-ichi` curls each of the 5 URLs and logs HTTP status per row into the build log / PDF; if no network, logs "unverified (no network)" rather than failing the build (satisfies SC-2's "or the build script logs the verification per row" clause). Honest about offline runs.
- **MANIFEST.md pins checksums of inputs + derived artifacts; `make verify-reproducibility` recomputes-and-matches, exits 0 only on full match.** Pins: panel parquet sha256 (`a72a4ee…`), `uv.lock` SHA, `package-lock.json` SHA, subgraph block-pins, and the run_id artifact checksums (fit_report.json / gate_report.json / firing_condition.json / sensitivity_sweep.json). Catches drift in inputs OR outputs.

### Cycle-closure (terminal step of Iteration 1)
- The PDF is this cycle's terminal deliverable → its completion TRIGGERS cycle closure: **push origin → PR to upstream (wvs-finance/abrigo-x402:master) → merge upstream**, only after the PDF renders + `make verify-reproducibility` is green + phase VERIFICATION passes. Per project CLAUDE.md §"Git workflow — Cycle-closure integration" and memory `project_cycle_closure_push_pr_merge.md`. AF-03 carries into the merge: never merge a verdict dressed as a pass.

### Per-task specialized-agent assignment (spec/plan directive — MANDATORY)
- **Every implementation task in the Phase 5 plan MUST name the closest-fit specialized agent from the AI-agency catalog as its executor — not a generic executor.** The planner records the chosen specialist + a one-line why, per task.
- **The report-document writeup is the headline case:** the prose must be CONCISE, carry the mathematical equations (Hawkes kernel, branching ratio, LR statistic, Carr-Madan strip, KS time-rescaling), and read like a research paper. Assign the research-paper-capable writing specialist (ROADMAP names **Technical Writer** as Phase-5 primary — use it, or the closest catalog specialist for academic/mathematical writeups) rather than a generic writer. State the pick + why in the plan.
- The writing task MUST invoke the relevant project SKILLS for quality: `latex-econ-model` (typeset the economic/stochastic model with proper notation), `notation-clean` (Econometrica-standard notation discipline — no one-shot Greek, no collisions), `latex-doc` (LaTeX/Quarto-math correctness), and `read-paper` where citing sources. These skills are the mechanism; the specialist agent is the driver.
- This is DISTINCT from (and composes with) the global two-step REVIEWER process (Reality Checker + one specialist reviewer on the plan): that governs review; THIS governs implementation-agent assignment.
- Other Phase-5 tasks similarly get fit-for-purpose specialists (e.g. the render-pipeline / Makefile + reproducibility-manifest task → DevOps-Automator-class; the sensitivity-sweep numerical task → an analytics/quant-class specialist; numbers-match verification → Analytics Reporter consult per ROADMAP). Planner assigns explicitly.

### Claude's Discretion
- Exact PDF section ordering / typography / figure styling (within the methodology-validation + near-miss frame).
- Whether the 3-run comparison is one table or table+figure.
- Exact `make report-ichi` / `make verify-reproducibility` target wiring.
- Sweep visualization form (heatmap vs annotated table) for the 3×3 convex-dominance grid.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### The verdict being reported (Phase 04.1.1 outputs — canonical v1.0)
- `data/fits/ichi/bdaf5c7ba5a2/fit_report.json` — the canonical fit: scipy_canonical_ll, AIC-min β=0.001, η=0.600, observed_stat=561.29, gate_criteria (lr_rejects=true, eta_floor_met=true, branching_ci_excludes_zero=true, ks_held_out_passes=FALSE), gate_passes=false
- `data/fits/ichi/bdaf5c7ba5a2/firing_condition.json` — firing_condition=null_strip_unavailable
- `data/fits/ichi/bdaf5c7ba5a2/gate_report.json` — all 4 convex-dominance conditions pass (any_condition_passed=true)
- `data/fits/ichi/bdaf5c7ba5a2/strip_degenerate.json` + `stress_report.json` + `joint_dist.json` + `run_log.txt`
- `data/fits/ichi/bdaf5c7ba5a2/CORRECTIONS.md` — the frozen-result corrections header
- `.planning/phases/04.1.1-.../_artifacts/DISPOSITION_MEMO_04_1_1_ks_halt.md` — the HALT memo: the 9 rejected post-hoc changes (anti-fishing provenance the PDF cites)
- `.planning/phases/04.1.1-.../04.1.1-DIAGNOSTIC.md` — the three root-cause bugs + the kernel-normalization mislabel proof (methodology-section source)
- `data/fits/ichi/ae9e3ba17900/README.md` + `fit_report.json` — the superseded LS-null run (3-run comparison row)

### Requirements + pre-registration
- `.planning/REQUIREMENTS.md` — REPORT-01, REPORT-02, REPORT-03, REPORT-04 (the 4 phase requirements)
- `notes/PRE_REGISTRATION.md` — §Prior Parameters (rate_per_event grid (1,5,10); USD_per_query $5e-6 ±50%; the REPORT-03 sweep values are locked here), §Phase 04.1.1 (v1/v2/02b/02c — the verdict gate + estimator), the cost-leg-modeled-not-paid framing
- `.planning/ROADMAP.md §Phase 5` — the 4 success criteria (note: the "Plans" list under Phase 5 is a copy-paste artifact of Phase 2; the SC-1..4 are authoritative)

### Render scaffolding (reuse)
- `reports/_templates/null_result.qmd` — Phase-4 null-result Quarto template (the base for ichi.qmd's near-miss framing)
- `reports/_templates/_evidence_branches.qmd` — Phase-4 evidence-branch partial
- `Makefile` — `verify-reproducibility` (currently STUB at line 47-48, this phase implements it), `lint-artifacts`, `render-lr-diagnostic` (quarto-render precedent at line 153)
- `analysis/tests/test_null_result_template.py` — the quarto-skipped dual-signature test (currently skipped; this phase may activate it)

### Project + git workflow
- `./CLAUDE.md` — §"Git workflow — fork/upstream model" + §"Cycle-closure integration" (push origin → PR upstream → merge upstream); USDT (not USDC) framing; domain non-negotiables
- `.planning/PROJECT.md` — v1.0 thesis (free-tier dominance); null results are valid deliverables (treating a null as failure is itself an AF-03 violation)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `reports/_templates/null_result.qmd` + `_evidence_branches.qmd` — Phase-4 Quarto partials; `reports/ichi.qmd` composes these (near-miss is a specialization of the null-result template).
- `Makefile :: verify-reproducibility` — STUB (lines 47-48) explicitly labeled "Phase 5 deliverable"; this phase fills it.
- `Makefile` quarto-render precedent (line 153: `cd reports && quarto render _templates/null_result.qmd`) — the `make report-ichi` target mirrors this.
- `analysis/src/abrigo_x402/hedge/null_result.py :: decide_firing_condition` — already produced firing_condition=null_strip_unavailable; the PDF reads the artifact, does not recompute.
- `data/fits/ichi/bdaf5c7ba5a2/*.json` — all numbers the PDF cites already exist on disk; the report READS them (Analytics-Reporter consult verifies PDF numbers == artifact numbers).

### Established Patterns
- `quarto_skipped` sentinel — tests skip-guard on missing quarto CLI (preserves the 207-green suite); the build target hard-requires.
- PANEL-02 provenance header `{chainId, contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit}` — the MANIFEST.md pins build on this.
- Content-addressed run_id (Pattern H) — the seeded spot-check draw + MANIFEST checksums anchor to run_id bdaf5c7ba5a2.

### Integration Points
- `make report-ichi` → `quarto render reports/ichi.qmd` → `reports/ichi.pdf` (the deliverable).
- `make verify-reproducibility` → recompute checksums vs `reports/MANIFEST.md` → exit 0/1.
- Cycle closure → `git push origin` → `gh pr create --repo wvs-finance/abrigo-x402` → merge upstream (after verify green).

### ⚠ Flagged for research/planning
- **`data/fits/` is gitignored.** A fresh clone will NOT have `bdaf5c7ba5a2/`'s artifacts to checksum. The planner MUST resolve how `make verify-reproducibility` obtains the artifacts on a fresh clone: either (a) commit the specific bdaf5c7ba5a2 artifacts as repro evidence (un-ignore that one run dir), or (b) verify-reproducibility re-derives them from the committed panel + lockfiles, or (c) MANIFEST pins the committed inputs + the PDF and documents the fit-run as a prerequisite step. Researcher to investigate the cleanest option.

</code_context>

<specifics>
## Specific Ideas

- The PDF's story arc, in the user's framing: "the pipeline works and corrected a false null; there IS a convex hedge worth building (the data demands convexity); we just can't certify the priced strip at n≈700 — and here's exactly what unlocks it (power-law / more data)."
- The KS knife-edge + the 9-rejected-post-hoc-changes list is a FEATURE of the report — it demonstrates the anti-fishing discipline that makes the 3/4 credible, not a flaw to bury.
- Power-law-vs-more-data tradeoff (from the user discussion): power-law is better science but extrapolates the tail at n≈700; more data is cleaner but slow on free-tier. The v2-path section frames this honestly.
- Cost leg is modeled not paid → the convex-dominance Δ sweep is partly stipulative; say so.

</specifics>

<deferred>
## Deferred Ideas

- Power-law kernel sweep (DGP-V2-01) + more-data certification — the v2 path; NAMED in the PDF's "what unlocks certification" section but NOT executed in Phase 5.
- Iteration-2 / Steer cCOP/USDT (Phase 6) — the PDF's cycle-closure PR sets up Phase 6, but Steer work is its own phase.
- Deployed Solidity hedge contracts — Iteration 3+.
- Re-fit / re-hedge of the DGP — Phase 04.1.1 is closed; Phase 5 reports, does not recompute the fit.

</deferred>

---

*Phase: 05-reporting-iteration-1-pdf-deliverable-l7*
*Context gathered: 2026-05-29*
