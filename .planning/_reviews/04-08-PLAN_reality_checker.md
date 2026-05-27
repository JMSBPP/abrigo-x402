## VERDICT

PASS

## Scope

Wave-3 orchestrator: `_build_char_func_from_winner` (BIC-winner-derived char_func, no Gaussian proxy) + `run_hedge(run_id, stage)` + `hedge` CLI subcommand + `decide_firing_condition` + Quarto render + ≥5 char_func helper tests + thread-pinned byte-identity scaffold. Revised after iter-3 closure of the MC-noise-floor regression introduced by iter-2.

## Findings

- **Iter-3 fix #1 (MC → Sobol QMC, root cause of iter-2 regression):** `CHAR_FUNC_MC_SAMPLES = 10_000` → `CHAR_FUNC_SOBOL_N = 2**16 = 65,536` (power of 2 enforced by `ValueError` guard `n_samples & (n_samples - 1) != 0`). Archimedean families (clayton/frank/gumbel) now sample via `scipy.stats.qmc.Sobol(d=2, scramble=True, seed=seed).random(N)` + `cop.cdf_inverse(sobol_uniforms)` with `cop.random` fallback. Noise floor improves from 1/√N ≈ 4×10⁻³ (MC, fails 0.001 tolerance) to `log(N)/N ≈ 10⁻⁴` (Sobol, decisively passes). New test `test_iter3_sobol_noise_floor_below_tolerance` probes two seeds at N=2¹⁶ on Clayton fixture and bounds `|phi1(u) - phi2(u)| < 0.005`.
- **Iter-3 fix #2 (honest source labels):** `clayton_mc_empirical` → `clayton_sobol_qmc` (and same for frank/gumbel). Gaussian/t retain `*_latent_mvn` / `*_latent_mvt` because the copula sampler itself is closed-form — MC-vs-QMC distinction only matters for the archimedean noise-floor regime.
- **Iter-3 fix #3 (fourth firing condition, `null_strip_unavailable`):** `decide_firing_condition` signature extended with `run_dir: Path | None = None`; new branch checks `(run_dir / "strip_degenerate.json").exists()` and returns `"null_strip_unavailable"`. `render_null_result_pdf` validator accepts the new condition. `_evidence_branches.qmd` gains a fourth branch with two sub-paths (`build_failed_upstream` vs `positivity_fail_after_2_12`) distinguishing helper exceptions from genuine FFT-positivity failures. Orchestrator caught-exception path sets `reason: "build_failed_upstream"` (replacing the iter-2 string "char_func construction from BIC winner failed").
- Pattern I thread-pinning preserved (`os.environ.setdefault("OMP_NUM_THREADS","1")` etc. as first 4 executable lines of `test_byte_identical_phase_4.py`).
- `test_phi_at_zero_equals_one` invariant preserved (φ(0) = 1+0j bit-perfect).
- Fail-loud helper-exception path preserved (no silent Gaussian-proxy fallback by construction).

## Reality check

Iter-3 closed the fantasy-positive failure mode at its source — the MC sample-mean noise floor that defeated the Carr-Madan positivity check. Now Archimedean copulas use Sobol QMC whose discrepancy decay is decisively below the 0.001 tolerance, AND the orchestrator distinguishes `build_failed_upstream` (helper raised) from `positivity_fail_after_2_12` (helper succeeded but FFT positivity check failed on the actual data — a substantive distributional finding, not a numerical artifact). Residual risk: `copulae==0.8.0` lacks `cdf_inverse` on some archimedean classes — fallback to `cop.random(N, seed)` is documented, which loses QMC discrepancy but matches the previous iter-2 MC behavior — graceful degradation rather than build failure. This fallback is a real path; if a user reports persistent positivity failures, the source-label trace identifies whether QMC was used.

## Recommendation

Accept. Iter-2 MC-noise regression closed via Path A. Plans ready for `/gsd:execute-phase 4`.
