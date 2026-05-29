---
phase: 05-reporting-iteration-1-pdf-deliverable-l7
plan: 04
artifact: VERIFICATION-pre
verification_pass: pass
quarto_skipped: false
requirements_covered: [REPORT-01, REPORT-02, REPORT-03, REPORT-04]
canonical_run_id: "bdaf5c7ba5a2"
verdict_reported: "gate_passes=false (3/4); firing_condition=null_strip_unavailable; eta~0.600 (lower bound); LR rejects NHPP (observed_stat=561.29, p=0.0); held-out Hawkes +114 nats; KS held-out leg-0 p=0.0474 (statistic D=0.148) -> ks_held_out_passes=false"
numbers_match_consult: pass
numbers_match_method: "qmd-source + on-disk artifact cross-check, CONFIRMED post-render via pdftotext/pdfinfo greps"
pdf_rendered: true
manifest_pdf_pin_resolved: content-checked  # PDF demoted from sha-byte-pin to content-check (B1 fix); not byte-pinnable across TeX toolchains
verify_reproducibility_exit: 0
verify_reproducibility_clean_checkout_exit: 0
created: 2026-05-29
---

## RESOLUTION (render completed 2026-05-29)

`pending-render` is RESOLVED. quarto 1.9.38 was installed (to `~/.local`, outside
the repo); `reports/ichi.pdf` rendered (517 KB) via `make report-ichi`. Render
required 5 build-mechanics fixes (pdf-engine=pdflatex; drop `::: {#refs}`;
keywords-surfaced HEDGE05 marker; QUARTO_PYTHON venv pin + drop `--execute-param`;
SOURCE_DATE_EPOCH). A two-step review (Reality Checker + DevOps Automator) on the
render diff returned NEEDS-WORK→resolved: AF-03 verdict integrity CLEARED; the PDF
byte-pin was demoted to a CONTENT check (BLOCKER B1 — PDFs embed the pdfTeX engine
banner, not byte-stable across toolchains); three literal `[@key]` citations
converted to author-year prose. Post-fix gates: `make report-ichi` exit 0;
`make verify-reproducibility` PASS (13/13 sha pins + PDF content-check), absent→PENDING
and tamper→FAIL branches proven; AF-03 PDF greps GREEN (null_strip_unavailable,
p=0.0474, gate FALSE present; forbidden narrowing strings absent; HEDGE05 marker in
Keywords). One tracked follow-up: the GENERIC `render_null_result_pdf` (a prior-phase
module, not this deliverable) has a latent path/papermill bug exposed by quarto —
see `_artifacts/FOLLOWUP_generic_null_result_renderer_bug.md`. Review trail:
`.planning/_reviews/05-render-fixes_{reality_checker,devops}.md`.

# Phase 5 Plan 04 — Iteration-1 Acceptance Gate Verification (pre-render)

Mirrors the Phase-3/Phase-4 Pattern-K acceptance template
(`.planning/phases/04-.../04-VERIFICATION-pre.md`). Every Phase-5 requirement
(REPORT-01..04), plus the AF-03 verdict-not-narrowed guard, is mapped to
{command, expected, observed, verdict}. The `verification_pass` is **TRI-STATE**:
`pass` ONLY after a rendered >50KB `reports/ichi.pdf` exists AND the AF-03
PDF-text grep ran GREEN (not skipped); otherwise `pending-render`. This env lacks
the `quarto` binary, so REPORT-01's PDF render and the AF-03 PDF-text grep are
NOT yet runnable — the top-level state is therefore **`pending-render`**, NOT
`pass`. REPORT-02/03/04 are MET; the lone PENDING item is REPORT-01's PDF render
(and the AF-03 PDF-text companion that depends on it). The numbers-match consult
(below) ran GREEN against the `.qmd` source + the on-disk `bdaf5c7ba5a2/`
artifacts.

**Headline scientific finding being reported (canonical run `bdaf5c7ba5a2`):**
the free-tier pipeline corrected a false null and found strong self-excitation
(η ≈ 0.600, LR rejects NHPP at p = 0.0, held-out Hawkes beats NHPP by ≈ 114
nats), but the held-out time-rescaling KS gate misses α = 0.05 by a knife-edge
(leg-0 p = 0.0474, statistic D = 0.148, under the locked min-leg aggregator) →
**`gate_passes = FALSE` (3/4)**, derived **`firing_condition =
null_strip_unavailable`**. All four convex-dominance conditions pass (the hedge
SHAPE is convexity-justified; the priced Carr–Madan strip is calibration-caveated
on the degenerate joint distribution at n_min = 79 < 101). This is reported
honestly as a near-miss / null result — the verdict is NOT a pass and is NOT
narrowed.

## Acceptance Grid

| Row | Requirement / Guard | Command | Expected | Observed | Verdict |
|-----|---------------------|---------|----------|----------|---------|
| 1 | REPORT-01 — PDF renders + >50KB | `make report-ichi && test $(stat -c%s reports/ichi.pdf) -gt 51200` | exit 0 + size > 50KB | quarto binary ABSENT in this env (`command -v quarto` fails); `reports/ichi.pdf` does not exist. The SOLE producer (`make report-ichi`) hard-requires quarto. SC-1's literal `.ipynb` is treated as satisfied-in-spirit by the `.qmd` source (`reports/ichi.qmd`, 535 lines) per the documented CONTEXT deviation — the deliverable contract is "PDF via Quarto". | **PENDING-RENDER** |
| 1b | REPORT-01b — PDF dual-signature greppable | `pdfinfo reports/ichi.pdf \| grep HEDGE05Marker` AND `pdftotext reports/ichi.pdf - \| grep "## Verdict"` | both grep exit 0 | Dual-signature contract present statically in the `.qmd` source: `\pdfinfo{ /HEDGE05Marker (HEDGE05-NULL-RESULT-V1) }` (line 36-38) + visible `## Verdict` callout banner (§Results). The PDF-text confirmation is quarto-skip-guarded (`tests/test_null_result_template.py::test_ichi_pdf_dual_signature` SKIPPED — no quarto). | **PENDING-RENDER** |
| 2 | REPORT-02 — seeded 5-row Blockscout spot-check | `cd analysis && uv run pytest tests/test_spot_check.py -x` | exit 0 | PASS (subsumed in the 17-passed targeted run). Seed `int(sha256("bdaf5c7ba5a2")[:8],16) = 3812543816` re-derived live and matches MANIFEST.md line 70. URLs of the form `https://celo.blockscout.com/tx/0x...`; build-time curl is network-optional (logs "unverified (no network)" rather than failing). | PASS |
| 3 | REPORT-03 — cost-prior sensitivity sweep | `cd analysis && uv run pytest tests/test_sensitivity_sweep.py -x` | exit 0 + 9-cell pre-reg grid + no-cost-model | PASS. `sensitivity_sweep.json` has 9 cells; grid = rate_per_event {1,5,10} × USD_per_query {2.5e-6, 5e-6, 7.5e-6} (pre-reg lock, NOT symmetric ±50% on both axes); each cell carries `evaluated_once=true / broadcast_to_grid=true / depends_on_cost_priors=false` (no `recomputed` literal); `all_cells_any_condition_passed=true`, `conditions_cost_prior_invariant=true`. `! grep -rE 'rate_per_event\|USD_per_query\|kappa' analysis/src/` no-new-cost-model guard holds. | PASS |
| 4 | REPORT-04 — reproducibility manifest + verify | `cd analysis && uv run pytest tests/test_manifest.py -x` AND `make verify-reproducibility` (incl. clean-checkout) | exit 0 + exit 0 | PASS. `make verify-reproducibility` → `PASS (13/13 pins matched)` exit 0 (working tree). CLEAN-CHECKOUT worktree run (`git worktree add --detach HEAD`) → identical `PASS (13/13 pins matched)` exit 0. Lockfiles correct: `analysis/uv.lock` + `pnpm-lock.yaml` pinned; `package-lock.json` ABSENT; root `uv.lock` ABSENT. Option C-hybrid committed artifacts (panel parquet + the bdaf5c7ba5a2 run-dir incl. CORRECTIONS.md + sensitivity_sweep.json) all tracked + matched. 3-state rule honoured: 13 present+matching pins OK; `reports/ichi.pdf` PENDING (the ONLY allow-listed pending path) — logged `PENDING`, does NOT fail. | PASS (PDF pin PENDING) |
| 5 | AF-03 verdict-not-narrowed (source-grep companion, runs here) | `cd analysis && uv run pytest tests/test_null_result_template.py::test_ichi_qmd_source_not_narrowed -x` | exit 0 | PASS (subsumed in the 17-passed run). The `.qmd` source contains the required strings {`null_strip_unavailable` ×7, `gate_passes` ×5, labeled `p = 0.0474`} and NONE of the 4 forbidden narrowing strings (the softened-pass / leaning-positive relabelings enumerated in the disposition memo's forbidden-relabeling list); the correct include `_templates/_evidence_branches.qmd` is present; no `USDC` literal. | PASS |
| 5b | AF-03 verdict-not-narrowed (PDF-text guard, quarto-machine) | `pdftotext reports/ichi.pdf - \| grep` required-present + forbidden-absent | required strings present, forbidden absent | `tests/test_null_result_template.py::test_ichi_verdict_not_narrowed` SKIPPED — quarto CLI not available. Runs GREEN on the operator's quarto machine after render; gates the cycle-closure PR. | **PENDING-RENDER** |
| 6 | Regression — targeted Phase-5 suite green incl. quarto-skips | `cd analysis && uv run pytest tests/test_spot_check.py tests/test_sensitivity_sweep.py tests/test_manifest.py tests/test_null_result_template.py -q` | exit 0; render rows SKIP | **17 passed, 3 skipped** (the 3 quarto PDF-text render tests skip-guarded; the source-grep AF-03 companion PASSES). Thread-pinned BLAS (OMP=MKL=OpenBLAS=NumExpr=1). Full slow suite deliberately NOT run (per the executor critical invariant); fit NOT recomputed; no κ; no new cost model. | PASS |

*Verdict legend: PASS · PENDING-RENDER (blocked only by the absent quarto binary in this env) · FAIL.*

## Numbers-Match Consult (Analytics Reporter)

Every headline figure presented in `reports/ichi.qmd` was cross-checked against
the on-disk canonical run `bdaf5c7ba5a2/` artifacts. The `.qmd` loads numbers via
read-only code cells (Pattern 1 — `json.loads((RUN_DIR / ...).read_text())`), so
those values match the artifacts by construction; the table below additionally
verifies the prose/footnote literals on the SINGLE canonical roundings and
confirms the label discipline (the `0.0474` is the leg-0 **p-value**, never the
statistic `D = 0.148`). **Result: MATCH on all rows — no `.qmd` correction was
required.**

| Figure (as in ichi.qmd) | qmd value | Artifact source | Artifact value | Match |
|-------------------------|-----------|-----------------|----------------|-------|
| Branching ratio η (lower bound) | ~0.600 | `fit_report.json :: hawkes_mv_params.branching_ratio` | 0.5999724484494755 | ✓ |
| η-floor met (η ≥ 0.2) | PASS | `gate_criteria.eta_floor_met` / `eta_floor_threshold` | true / 0.2 | ✓ |
| AIC-min decay β | 0.001 (1/β=1000s) | `hawkes_mv_params.decays` + `decay_aic_table["0.001"]` | 0.001 / AIC 9800.78 | ✓ |
| LR observed statistic Λ | 561.29 | `lr_test.observed_stat` | 561.2948088026606 | ✓ |
| LR p-value (rejects NHPP) | p = 0.0 (α=0.01) | `lr_test.p_value` / `alpha` / `rejects_at_alpha` | 0.0 / 0.01 / true | ✓ |
| LR bootstrap replicates | 1000 | `lr_test.n_reps` / `n_failed` | 1000 / 0 | ✓ |
| Held-out ℓ Hawkes | -1206.23 | `held_out_loglik.hawkes` | -1206.2319733635582 | ✓ |
| Held-out ℓ NHPP | -1320.63 | `held_out_loglik.nhpp` | -1320.6281331371827 | ✓ |
| Held-out advantage | ≈ 114 nats (Hawkes wins) | `nhpp - hawkes` | 114.40 nats | ✓ |
| KS held-out leg-0 **p-value** | p = 0.0474 | `ks_rescaled_time.per_leg[0].p_value` | 0.047350333810196134 | ✓ |
| KS held-out leg-0 statistic D | D = 0.148 (n=83) | `ks_rescaled_time.per_leg[0].ks_statistic` / `n_events` | 0.14799982742727918 / 83 | ✓ |
| KS held-out leg-1 **p-value** | p = 0.0564 (n=79) | `ks_rescaled_time.per_leg[1].p_value` / `n_events` | 0.05643942824856608 / 79 | ✓ |
| KS aggregator (min-leg) p | 0.0474 < 0.05 → FALSE | `ks_rescaled_time.p_value` (min-leg) / `ks_alpha` | 0.047350333810196134 / 0.05 | ✓ |
| Full unrounded leg-0 p (footnote) | 0.047350333810196134 | `ks_rescaled_time.per_leg[0].p_value` | 0.047350333810196134 | ✓ |
| ks_held_out_passes | FALSE | `gate_criteria.ks_held_out_passes` | false | ✓ |
| **gate_passes** | **FALSE (3/4)** | `fit_report.gate_passes` | false | ✓ |
| Branching CI lower (excludes 0) | lower = 0.001 | `branching_ratio_ci.lower` / `method` | 0.001 / constrained_mle_profile | ✓ |
| **firing_condition** | **null_strip_unavailable** | `firing_condition.json :: firing_condition` | null_strip_unavailable | ✓ |
| vol-of-vol leg-0 | 1.180 | `gate_report :: vol_of_vol_gt_zero…leg_0.vol_of_vol` | 1.180302236815738 | ✓ |
| skew / excess-kurt leg-0 | 1.849 / 3.602 | `gate_report :: positive_skew_fat_tails…leg_0` | 1.8485569198 / 3.6020455357 | ✓ |
| convex Hawkes-self-excitation η | 0.600 (≥ 0.2) | `gate_report :: hawkes_self_excitation…branching_ratio` | 0.5999724484494755 | ✓ |
| USDT-depeg LHS | N = 64, 0 flips | `gate_report :: usdt_depeg_basis_jump…sensitivity_summary` | n_samples 64 / n_flips 0 | ✓ |
| any_condition_passed (all 4) | true | `gate_report :: any_condition_passed` | true | ✓ |
| 3-run comparison row η (`bdaf5c7ba5a2`) | 0.600 | `fit_report.hawkes_mv_params.branching_ratio` | 0.5999724484494755 | ✓ |
| Sweep cells / grid | 9 cells, {1,5,10}×{2.5e-6,5e-6,7.5e-6} | `sensitivity_sweep.json :: grid` | 9 cells, exact grid | ✓ |
| Sweep cells passing | 9/9 any_condition_passed | `sensitivity_sweep.json` | 9/9, cost_prior_invariant=true | ✓ |
| Panel population | 832 raw → 778 events (382+396) | `fit_report.input_diagnostics.total_events_per_leg` + MANIFEST | 382 + 396 = 778; 832 raw | ✓ |
| Held-out / train split | held-out 83+79; train 299+317 | `held_out_loglik.split_metadata` | held 83+79; train 299+317 | ✓ |
| Spot-check seed | 3812543816 | `sha256("bdaf5c7ba5a2")[:8]` → MANIFEST | 3812543816 | ✓ |

**Consult verdict:** the `.qmd` source reports the canonical artifact values
verbatim on the single agreed roundings; the KS `0.0474` is labeled as a p-value
everywhere (statistic stated separately as `D = 0.148`); the verdict is
`gate_passes = FALSE` (3/4) with `firing_condition = null_strip_unavailable`,
unnarrowed. The render-time `pdftotext` confirmation (that the rendered PDF text
carries these same values + the dual signature + none of the forbidden strings)
is `pending-render` — it runs on the operator's quarto machine and gates the
cycle-closure PR.

## Pending-render closure path (operator, quarto machine)

This env lacks the `quarto` binary, so REPORT-01's PDF render and the AF-03
PDF-text grep are NOT runnable here. The `verification_pass` is therefore
`pending-render`. To flip it to `pass` AND unblock the cycle-closure PR
(Task 2, HARD-gated), an operator on a quarto-equipped machine runs:

```
make report-ichi                                  # renders reports/ichi.pdf (auto-installs TinyTeX); SOLE producer
test $(stat -c%s reports/ichi.pdf) -gt 51200      # confirm >50KB
sha256sum reports/ichi.pdf                         # then replace the all-zero placeholder pin in reports/MANIFEST.md
make verify-reproducibility                        # now exit 0 with the PDF line STRICT (no longer PENDING)
# clean-checkout: git worktree add --detach /tmp/wt HEAD && (cd /tmp/wt && make verify-reproducibility)
pdftotext reports/ichi.pdf - | grep -E 'null_strip_unavailable' \
  && pdftotext reports/ichi.pdf - | grep -E 'p ?= ?0\.0474' \
  && pdfinfo reports/ichi.pdf | grep HEDGE05Marker      # AF-03 PDF-text guard GREEN
cd analysis && uv run pytest tests/test_null_result_template.py -x  # the 3 render tests now PASS, not skip
```

Only after the rendered >50KB PDF exists, the MANIFEST PDF pin is RESOLVED
(non-PENDING), `make verify-reproducibility` exits 0 with the PDF line strict
(incl. the clean-checkout run), the AF-03 PDF-text grep is GREEN, and this file's
`verification_pass` is set to `pass`, does the Task-2 cycle-closure PR open.
A PDF-less PR is HARD-BLOCKED. AF-03 carries into the PR body: the honest 3/4
verdict (gate_passes=FALSE, null_strip_unavailable, labeled p=0.0474) is reported
plainly — never dressed as a pass.

## Quarto Availability Note

`command -v quarto` fails in this execution environment (the binary is an
operator prerequisite, not installed here). Per the Phase-5 design and the
`quarto_skipped` sentinel pattern, all render-touching tests stay skip-guarded so
the targeted suite is green (17 passed / 3 skipped); the frontmatter carries
`quarto_skipped: true` DISTINCT from `verification_pass: pending-render`. This is
the DESIGNED path — not a blocker. The PDF render is genuinely pending on a
quarto machine.
