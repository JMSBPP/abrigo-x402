## VERDICT

PASS

## Scope

Code-reviewer pass on Plan 03-03 (DGP-03: boundary-correct parametric bootstrap LR test, SC-3 grep gate).

## Findings

- Frontmatter clean: wave 1, depends_on=["03-00","03-01","03-02"] (correctly captures dependence on both fit functions for refit-per-rep), non-overlapping files, requirement DGP-03
- Pitfall 2 (simulate-from-null) correctly enforced via `adjacency=np.zeros((2, 2))` in `_simulate_nhpp_under_null` — grep-gated in acceptance criteria
- SC-3 anti-patterns (`likelihood_ratio_test`, `chi2(1).sf`) actually enforced both at scaffold time AND with a runtime `test_grep_gate_forbidden_calls_absent` pytest test that shells out to grep — defensive double-coverage
- Pitfall 9 (`force_simulation=True` never set) grep-gated
- Deterministic seed derivation: `digest()[:4]` (bytes) is semantically correct as 4 bytes → uint32; the frontmatter docstring mentions `[:8]` (hex chars) which gsd-plan-checker flagged as a notational discrepancy — semantically equivalent (8 hex chars = 4 bytes), but worth a docstring tidy
- PRE_REGISTRATION lock visible: `PRODUCTION_N_REPS: int = 1000` grep-checked
- Headless matplotlib (`matplotlib.use('Agg')`) set before `pyplot` import — correct ordering
- Bare `except Exception` in the bootstrap rep loop and in `_simulate_nhpp_under_null` callsite is broad; acceptable here because rep failures must not crash the test, are counted in `n_failed`, and surface in fit_report.json
- Diagnostic plot path is hardcoded as `reports/_diagnostics/lr_null_dist.png` in the orchestrator callsite (Plan 03-07) — fine for the headline run; tests use `tmp_path`

## Recommendation

Accept. Optional: harmonise the `[:4] bytes` vs `[:8] hex` notation in the frontmatter docstring.
