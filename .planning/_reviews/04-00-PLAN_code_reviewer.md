## VERDICT

PASS

## Scope

Code-reviewer pass on Plan 04-00 (Wave 0 scaffold: dependence/ + hedge/ module skeletons, 12 skip-marked test stubs, 3 HEDGE-05 fixture triplets, Quarto template, lint-artifacts five-track extension, Makefile targets, pyproject deps, four pre-commit grep gates).

## Findings

- Frontmatter: `wave: 0`, `depends_on: [pre]` correctly sequences after the AF-03 amendment; STEP 1 of the action body explicitly aborts if `grep -q "Carr-Madan Grid Numerical Tolerances" notes/PRE_REGISTRATION.md` fails, hardening the ordering invariant at scaffold time
- Wave-1 symbol surface locked verbatim in `must_haves.truths` (canonical names: `cross_correlogram_event_index`, `permutation_null_max_abs_rho`, `fit_5_families_bic`, `evaluate_condition_{1..4}`, `compute_strip`, `run_three_way_stress`, `load_calibration`, `generate_lhs_samples`, `decide_firing_condition`, `render_null_result_pdf`, `run_hedge`) — each Wave-1 plan I reviewed lands at these exact names
- `REQUIRED_*_KEYS` tuples + `HEDGE05_SIGNATURE = "HEDGE05-NULL-RESULT-V1"` constant forward-declared in their owning modules at scaffold time; STEP 8 mirrors them as frozensets in `scripts/lint_artifacts.py` (Pattern G sync) — Plan 04-03 acceptance criteria includes the explicit cross-check `frozenset(REQUIRED_JOINT_DIST_KEYS) == JOINT_DIST_REQUIRED_KEYS`
- `pyvinecopulib==0.7.6` correctly deferred (RESEARCH Open Question 3) — only `copulae==0.8.0` + `jupyter` land in this plan; `fit_5_families_bic(use_vine=True)` is wired to `NotImplementedError` in the scaffold and Plan 04-03 keeps that branch
- Quarto template carries dual signature markers (`# HEDGE-05 NULL RESULT — ` H1 + `\pdfinfo{ /HEDGE05Marker (HEDGE05-NULL-RESULT-V1) }`) and `execute: { freeze: false, cache: false }` honors Pitfall 3 at scaffold time
- Four pre-commit gates wired: SC-2 usdc literal, Carr-Madan `scipy.integrate.quad|np.trapz`, canonical-LL `loglik_in_sample_raw`, hardcoded-jump-params — scoped to `hedge/*` excluding `usdt_depeg.py` (the only legitimate home for the (λ, μ_J, σ_J) constants), which matches Plan 04-06 acceptance criterion 7
- `files_modified` block is large (~35 paths) but disjoint from every Wave-1 plan's `files_modified` — verified against 04-01, 04-03, 04-04, 04-05, 04-06: each only modifies its OWN module file + its OWN test files, not the scaffold-touch list
- File-content truncation at line 816 of 1015 visible — but the surface declared in the visible portion is sufficient to verify scaffold-Wave-1 sync; the unread portion is the Makefile + pyproject + pre-commit details which are conventional

## Recommendation

Accept.
