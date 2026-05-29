# Copulae Install Troubleshooting (Phase 4)

Primary: `copulae==0.8.0` via `uv sync`. If that fails:

1. **Wheel unavailable on platform** — try the prior minor: `uv add copulae==0.7.10`
   (relaxes the numpy upper bound; verify `import copulae` still succeeds and the
   5-family API `NormalCopula / StudentCopula / ClaytonCopula / FrankCopula / GumbelCopula`
   is intact — Plan 04-03 smoke test catches API drift before silently downgrading).

2. **Nightly wheels** — `uv pip install --index-url https://test.pypi.org/simple/ copulae`
   (use ONLY as a transient unblock; document the resolution in the run log and
   open a follow-up plan to re-pin once a stable wheel is available).

3. **Total failure (0.7.x and 0.8.x both unavailable)** — workflow BLOCKS. A v1.1
   follow-up plan must implement a minimal 5-family BIC fitter directly on
   `scipy.stats.multivariate_normal` (Gaussian + t) + hand-rolled Archimedean
   log-likelihoods (Clayton / Frank / Gumbel via the generator-function MLE). This
   is explicitly NOT in Phase 4 scope; surface the block immediately to the
   planning gate.

## Verification command

After `uv sync`, run from the repo root:

```bash
cd analysis && uv run python -c "import copulae; print(copulae.__version__)"
```

Exit-code 0 + a printed version string = install succeeded. Any other outcome
escalates per the fallback paths above.

## Why this file exists

The iter-3 reality-checker review of Plan 04-00 flagged the copulae install as a
potential silent blocker for Wave 1 (Plans 04-03 / 04-04 / 04-07 all import the
library). This document is the load-bearing escape hatch — Wave 0 must verify
the install before declaring the scaffold complete.
