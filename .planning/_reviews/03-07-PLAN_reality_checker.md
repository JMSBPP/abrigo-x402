## VERDICT

PASS

## Scope

Reality check on Wave-2 orchestrator (`run_fit`), CLI `fit` subcommand, `scripts/lint_artifacts.py` extension, `data/fits/.gitignore`, and the `fit_report.json` SC-1 metadata-key enumeration.

## Findings

- `REQUIRED_FIT_REPORT_KEYS` tuple lists every key the ROADMAP SC-1 schema requires verbatim: 6 PANEL-02 provenance keys (`chainId`, `contractAddress`, `blockRange`, `fetchTimestamp`, `dataHash`, `gitCommit`), plus `run_id`, `tick_lib_version`, plus the 7 statistical blocks (`nhpp_inar_params`, `hawkes_mv_params`, `lr_test`, `ks_rescaled_time`, `held_out_loglik`, `branching_ratio_ci`, `baseline_stationarity_check`), plus `input_diagnostics`, `gate_passes`, `gate_criteria` = 18 top-level keys. Both the orchestrator and the linter share this tuple.
- Gate-failure-still-writes-complete-artifact invariant is enforced TWICE: orchestrator raises `KeyError` if any required key is missing AT WRITE TIME, AND the linter rejects at consumption time. `test_gate_failure_still_writes_complete_artifact` exercises the synthetic α=0 path where the gate should fail — the test asserts all 18 keys still present.
- `run_id = sha256(panel_dataHash + git_commit + tick.__version__)[:12]` is deterministic and panel-dependent per CONTEXT.md.
- Linter has a self-test built into the verify command: `mkdir test_lint_bad; echo bad-json > fit_report.json; ! make lint-artifacts; rm; make lint-artifacts` — proves the linter actually fails on missing keys, not just claims to.
- `ks_combined_pvalue = float(min(ks_pvals))` — using the minimum p-value across legs is conservative (Bonferroni-ish) for the gate; the per-leg p-values are still preserved in `per_leg`. Acceptable.

## Reality check

The most realistic failure is `_extract_legs_from_panel` mis-classifying Swap direction. The Phase-2 panel stores `amount0`/`amount1` as `String`-encoded decimal ints (PANEL convention from CLAUDE.md). The orchestrator casts via `swaps.get_column("amount0").cast(pl.Int128)` then `.gt(0).to_numpy()` — but Polars cast of a String column containing negative values (e.g., `"-100"`) to `Int128` works only if Polars 1.41 supports signed string parsing on that column type. If parsing fails silently to null, both leg masks become all-False and the `if leg_0.size == 0 and leg_1.size == 0` guard raises — visible failure. But if parsing succeeds and the sign convention is wrong (token0 inflow corresponds to `amount0 < 0` from the pool's perspective, not `> 0`), legs are swapped and every downstream cross-leg α coefficient is mis-labeled with no test catching it. The test fixture in 03-07 hardcodes the convention (`amount0: "100", amount1: "-100"` for leg_0) so the test would pass regardless of which sign convention is "correct" for the real ICHI pool.

## Recommendation

Accept with a note: the Swap direction convention (`amount0 > 0` means token0 inflow) should be cross-checked against an actual ICHI pool Swap event in Phase-2's fixtures during execution. Not a 03-07 blocker — caught at Phase 4 latest if economic interpretation looks wrong.
