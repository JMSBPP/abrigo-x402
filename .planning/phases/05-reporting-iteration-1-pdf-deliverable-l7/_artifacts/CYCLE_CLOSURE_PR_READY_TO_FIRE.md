# Cycle-closure PR — READY-TO-FIRE (HARD-BLOCKED on PDF render)

**Status:** NOT YET FIRED. The cycle-closure PR is HARD-GATED on a rendered
>50KB `reports/ichi.pdf` + a RESOLVED (non-PENDING) MANIFEST PDF pin + the AF-03
PDF-text grep GREEN + clean-checkout `verify-reproducibility` green +
`05-VERIFICATION-pre.md :: verification_pass: pass`. `quarto` is ABSENT in the
execution env, so the PDF is unrendered → those conditions are NOT met → **no
PDF-less PR is opened, no push to origin is made** (critical invariants 2-3;
plan Task-2 HARD GATE; reviewer MAJOR-B / MAJOR-1).

This file pre-stages the exact branch name, commit pathspec, push target, and PR
body so the operator can fire the cycle closure in one pass after rendering.

---

## Step 0 — render the PDF + resolve the gate (operator, quarto machine)

```
make report-ichi                                   # SOLE producer of reports/ichi.pdf (auto-installs TinyTeX)
test $(stat -c%s reports/ichi.pdf) -gt 51200       # >50KB gate
sha256sum reports/ichi.pdf                          # copy the sha
# edit reports/MANIFEST.md: replace the all-zero placeholder line
#   0000…0000  reports/ichi.pdf
# with the real:  <sha256>  reports/ichi.pdf
make verify-reproducibility                         # now exit 0 with the PDF line STRICT (14/14 pins)
git worktree add --detach /tmp/wt HEAD && (cd /tmp/wt && make verify-reproducibility) && git worktree remove --force /tmp/wt
pdftotext reports/ichi.pdf - | grep -E 'null_strip_unavailable' \
  && pdftotext reports/ichi.pdf - | grep -E 'p ?= ?0\.0474' \
  && pdfinfo reports/ichi.pdf | grep HEDGE05Marker   # AF-03 PDF-text guard GREEN
cd analysis && uv run pytest tests/test_null_result_template.py -x   # 3 render tests now PASS, not skip
# then edit 05-VERIFICATION-pre.md: verification_pass: pending-render -> pass ; pdf_rendered: true ; manifest_pdf_pin_resolved: true
```

## Step 1 — PRE-FLIGHT (assert before push/PR)

```
git remote get-url origin | grep -q 'JMSBPP/abrigo-x402'   # origin is the personal fork
gh auth status                                              # gh authenticated
```

## Step 2 — branch + commit (EXACT Phase-5 pathspec; NEVER `git add -A`)

PINNED branch name: **`phase-05-iteration-1-pdf`** (so the checkpoint verify query
matches).

```
git checkout -b phase-05-iteration-1-pdf            # if on master
git status --short                                  # REVIEW: confirm no 04.1.1 file is swept in
git add \
  reports/ichi.qmd \
  reports/ichi.pdf \
  reports/MANIFEST.md \
  analysis/src/abrigo_x402/report/ \
  analysis/tests/test_spot_check.py \
  analysis/tests/test_sensitivity_sweep.py \
  analysis/tests/test_manifest.py \
  analysis/tests/test_null_result_template.py \
  Makefile \
  .gitignore \
  data/fits/.gitignore \
  data/fits/ichi/bdaf5c7ba5a2/sensitivity_sweep.json \
  data/fits/ichi/bdaf5c7ba5a2/CORRECTIONS.md \
  data/raw/ichi/0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F/67378253_67896653.parquet \
  .planning/phases/05-reporting-iteration-1-pdf-deliverable-l7/
git commit -m "feat(05): Iteration 1 ICHI cKES/USDT PDF deliverable + reproducibility

- reports/ichi.qmd -> reports/ichi.pdf (research-paper near-miss report)
- 5-row Blockscout spot-check + 9-cell cost-prior sensitivity sweep
- MANIFEST + make verify-reproducibility (resolved PDF pin, clean-checkout green)
- honest 3/4 verdict (gate_passes=FALSE, null_strip_unavailable)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

NOTE: most data/fits/ichi/bdaf5c7ba5a2/ artifacts + the panel parquet are already
committed (Plan 05-00/05-01). The `git status --short` review confirms which paths
are genuinely new vs already tracked; only the genuinely-changed Phase-5 paths
need re-adding (e.g. reports/ichi.pdf, MANIFEST.md, ichi.qmd, the VERIFICATION
file). Do NOT stage any `04.1.1-*` working-tree file.

## Step 3 — push to origin ONLY (never upstream)

```
git push origin phase-05-iteration-1-pdf
```

## Step 4 — open the PR to upstream (honest 3/4 body)

```
gh pr create --repo wvs-finance/abrigo-x402 \
  --base master --head JMSBPP:phase-05-iteration-1-pdf \
  --title "Iteration 1: ICHI cKES/USDT DGP estimation — validated method, honest 3/4 (null_strip_unavailable)" \
  --body-file <(cat <<'BODY'
## Iteration 1 — ICHI cKES/USDT DGP estimation (honest 3/4)

**Verdict: `gate_passes = FALSE` (3 of 4).** This is a near-miss / null result,
reported honestly. It is NOT a pass and is NOT narrowed.

**What the pipeline found (canonical run `bdaf5c7ba5a2`, real Celo data):**
- The free-tier pipeline works end-to-end and **corrected a false null**: an
  earlier least-squares fit reported no self-excitation; the canonical
  maximum-likelihood estimator finds strong self-excitation.
- η ≈ 0.600 (reported as a **lower bound** — ~13% finite-sample downward bias at
  n ≈ 700).
- LR rejects the NHPP null: observed_stat = 561.29, p = 0.0 (1000-rep parametric
  bootstrap, common t0, α = 0.01).
- Held-out Hawkes log-likelihood beats the NHPP baseline by ≈ 114 nats.

**The lone failure — the held-out time-rescaling KS:**
- leg-0 **p = 0.0474** (statistic D = 0.148, n = 83); leg-1 p = 0.0564 (n = 79).
- Under the locked **min-leg aggregator**, p = 0.0474 < 0.05 →
  `ks_held_out_passes = FALSE`. A knife-edge miss (0.0026 below α = 0.05). We
  print the p-value labeled as a p-value; the statistic is D = 0.148, separately.
- The disposition memo enumerates 9 post-hoc changes considered and rejected
  (incl. switching the aggregator, which would "pass"). None applied. The refusal
  to narrow is a credibility asset.

**Convexity-justified, calibration-caveated:**
- All **4 convex-dominance conditions pass** (vol-of-vol = 1.180, skew = 1.849 /
  excess-kurt = 3.602, η = 0.600 ≥ 0.2, USDT-depeg basis jump) → the hedge SHAPE
  is convex; fat tails + self-excitation dominate the linear hedge.
- The PRICED Carr–Madan strip is NOT calibratable: the empirical joint
  distribution is degenerate at the held-out overlap (n_min = 79 < 101, the
  DEPEND-01 lag-radius floor), so the joint characteristic function is
  unestimable → derived `firing_condition = null_strip_unavailable`, NOT "no hedge".

**Methodology (the v1.0 contribution).** 3-run comparison naming the three
root-cause bugs fixed: (1) mislabeled fixture (tick normalized-kernel: true η was
0.05, not 0.5), (2) projection-trick CI, (3) kernel-blind β = 0.1.

**What unlocks certification (v2, named not executed):** power-law kernel (fixes
KS via long memory, but extrapolates the tail at n ≈ 700) vs more data (cleaner,
slow on free-tier). Deferred to Iteration 2 / DGP-V2-01.

Reproducibility: `make verify-reproducibility` green on a clean checkout
(committed panel + run-dir artifacts + the rendered PDF, sha256-pinned).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
BODY
)
```

## Step 5 — MERGE is the user's gated action

The executor does NOT merge. Review the PR; if the honest 3/4 framing is correct,
merge upstream yourself (or request changes). AF-03 carries into the merge: never
merge a verdict dressed as a pass.

## Verify the PR opened correctly

```
gh pr list --repo wvs-finance/abrigo-x402 --head phase-05-iteration-1-pdf \
  --json url,baseRefName,headRefName \
  --jq '.[0] | select(.baseRefName=="master" and .headRefName=="phase-05-iteration-1-pdf") | .url'
```
