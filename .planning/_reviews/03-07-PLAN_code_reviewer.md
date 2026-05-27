## VERDICT

PASS

## Scope

Code-reviewer pass on Plan 03-07 (Wave 2: run_fit orchestrator + cli.py fit subcommand + fit_report.json schema + lint_artifacts extension).

## Findings

- Frontmatter clean: wave 2, depends_on lists all six Wave-1 plans (03-01..03-06), files_modified are non-overlapping with concurrent plans (no Wave 2 sibling); requirements list is the full DGP-01..06 set
- `REQUIRED_FIT_REPORT_KEYS` schema matches ROADMAP SC-1 verbatim: chainId, contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit, run_id, tick_lib_version, nhpp_inar_params, hawkes_mv_params, lr_test, ks_rescaled_time, held_out_loglik, branching_ratio_ci, baseline_stationarity_check (DGP-04 derived), input_diagnostics, gate_passes, gate_criteria — all 18 keys accounted for
- Nested-key spot-checks present in `test_fit_report_has_all_sc1_keys` for lr_test, branching_ratio_ci, baseline_stationarity_check, held_out_loglik, ks_rescaled_time — catches schema drift in any Wave-1 subreport
- CONTEXT.md gate-failure invariant ("NEVER write a fit_report.json with missing keys") enforced by `missing = [k for k in REQUIRED_FIT_REPORT_KEYS if k not in fit_report]; raise KeyError if missing` AND verified by `test_gate_failure_still_writes_complete_artifact`
- run_id derivation matches CONTEXT: `sha256(panel_dataHash + git_commit + tick_version)[:12]`; tested by both `test_residuals_hash_matches` (residuals provenance) and the byte-identical tests in 03-08
- Function names used by orchestrator (`wall_clock_split`, `compute_held_out_loglik_hawkes/nhpp`, `time_rescaling_ks_test_leg`, `profile_likelihood_eta_ci`) match the Wave-1 implementations — internally consistent; only 03-00's scaffold is inconsistent
- `_extract_legs_from_panel` assumes a `event_name == "Swap"` filter with `amount0/amount1` as Int128-castable strings; consistent with Phase 2 panel.py contract
- `chain_id = 42220` and `contract_address = 0x61Ef…829F` hardcoded inside `_panel_provenance` — should arguably be parsed from the panel's PANEL-02 header rather than re-hardcoded; works for the ICHI cKES/USDT case but couples the orchestrator to one pool; flag for Phase 6 (Steer iteration) — not blocking for Phase 3
- `subprocess.check_output(["git", "rev-parse", "HEAD"])` for gitCommit — `cwd` not pinned; assumes invocation from repo root. Defensive but works when invoked via the documented CLI
- CLI subcommand wiring, lint_artifacts extension, Makefile target, and data/fits/.gitignore allowlist all consistent with Phase 2 PANEL-02 precedent
- The two-step verify command for lint_artifacts (bad dummy must fail, clean must pass) is a solid test of the lint gate itself

## Recommendation

Accept. Follow-up: surface the hardcoded `chain_id`/`contract_address` to the panel's own metadata header in a later phase so Steer (Phase 6) doesn't need to fork the orchestrator.
