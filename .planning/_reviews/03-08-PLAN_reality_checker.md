## VERDICT

PASS

## Scope

Reality check on Wave-3 acceptance closure: SC-5 byte-identical test, once-per-phase production-rep size sanity, `03-VERIFICATION-pre.md` acceptance grid (DGP-01..06 + SC-1..5), revised after iteration-1 NEEDS WORK on SC-5 thread-pinning.

## Findings

- `test_deterministic_fit` scrubs only `fetchTimestamp` before comparison (the sole ROADMAP-allowed wall-clock exception) and content-hashes `residuals.parquet` for byte-identity — SC-5 contract operationalized.
- `test_deterministic_run_id` + `test_different_panel_different_run_id` together prove `run_id` consumes `dataHash`, not just `git_commit + tick_version` — a perturbed-panel collision would surface.
- Production-rep manual sanity (`n_reps=1000` on synthetic α=0 fixture) wired as a one-shot bash heredoc; observed p-value written into the verification grid. Closes the 03-01 50-path / ±15% INFO note — the 1000-rep production sanity lives here.
- Acceptance grid mandates 11+ rows (6 DGP + 5 SC) with regex check `grep -cE "DGP-0[1-6]|SC-[1-5]" ≥ 11`.

## Reality check

Iteration 1 flagged that SC-5 byte-identity was fantasy-deterministic without BLAS / OMP / MKL thread pinning — `statsmodels.tsa.api.VAR.select_order` is sensitive to thread count and could drift AIC bits → different `p_star` → divergent `nhpp_inar_params`. Iteration 2 closes this:

1. `test_byte_identical.py` now sets `OMP_NUM_THREADS=MKL_NUM_THREADS=OPENBLAS_NUM_THREADS=NUMEXPR_NUM_THREADS=1` as the first executable code (above all imports — must precede the transitive numpy import via `run_fit`).
2. `test_deterministic_fit` includes sanity-guard `assert os.environ.get("OMP_NUM_THREADS") == "1"` (and parallel MKL/OpenBLAS/NumExpr asserts) so a regression where the env vars are stripped fails loudly rather than silently.
3. Acceptance criteria grep-verify all four env-var strings + ordering (env-block precedes first `import` after the module docstring).
4. `03-VERIFICATION-pre.md` SC-5 row carries verbatim Notes/Caveats text documenting the failure mode and the fix.

The other reality-check items from iteration 1 (git in-flight commit risk, no path-induced divergence) remain valid observations but are not blockers — process-level `git_commit` identity is the right contract.

## Recommendation

Accept. Iteration-1 BLOCKER closed. SC-5 byte-identity now grep-verifiable as thread-pinned. Plans ready for `/gsd:execute-phase 3`.
