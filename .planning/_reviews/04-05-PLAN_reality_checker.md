## VERDICT

PASS

## Scope

`compute_strip` Carr-Madan FFT inversion + 0.1% positivity tolerance + 2¹¹→2¹² single-escalation + abort-to-`strip_degenerate.json`; polymorphic payoff signature; 5 tests. Revised after iter-3 closure of the MC-noise-floor regression introduced by iter-2.

## Findings

- **Iter-3 fix (MC noise floor + hybrid state):** the root cause of the iter-2 NEEDS WORK was an MC char_func at N=10,000 with 1/√N ≈ 1% noise floor systematically defeating the 0.1% positivity tolerance. Iter-3 closed this via two paired changes:
  1. **04-08 switched MC → Sobol QMC at N=2¹⁶=65,536.** Convergence is O(log N / N) ≈ 10⁻⁴, decisively below 0.001 tolerance. Source labels honestly relabeled `*_sobol_qmc` (clayton/frank/gumbel) so the audit trail names the sampler.
  2. **04-05 + 04-08 formalize the "gate-passed but strip-not-emittable" fourth firing condition** `null_strip_unavailable` with explicit `reason ∈ {build_failed_upstream, positivity_fail_after_2_12}` sub-paths in `strip_degenerate.json`. CONTEXT.md decision section, Quarto template, `null_result.py`'s `decide_firing_condition`, and 04-09 acceptance grid row 13c all wire through. No more ambiguous "gate passes, strip silently disappears" state.
- Anti-pattern gate (`scipy.integrate.quad|fixed_quad|romberg|np.trapz`) triple-enforced.
- `POSITIVITY_TOLERANCE = 0.001` grep-locked against PRE_REG amendment via key_links (Plan 04-pre commit predates per AF-03 ordering).
- `STRIP_DEGENERATE_KEYS` extended with `reason` field for forensic post-mortem; module docstring documents the new firing-condition (d) routing path.
- Polymorphic payoff signature preserved for v2.0 streaming-tokenization.
- The price-recovery `strip_prices` field naming was a documented divergence from the canonical Carr-Madan static-replication-portfolio decomposition (OTM puts + OTM calls weighted by f''(K)); the contract `REQUIRED_STRIP_KEYS = (strip_prices, strikes, ...)` is honored. Phase 5 reporting layer is the canonical Carr-Madan rendering boundary; 04-05 produces the FFT-inverted density expectation that the static-replication strip is built from.

## Reality check

Iter-3 closed the fantasy-positive failure mode (gate passes → MC undersampling causes strip abort → ambiguous hybrid state). Now: (i) Sobol QMC noise floor 10⁻⁴ < tolerance, so the abort path fires only on genuine distributional degeneracy; (ii) when the abort path does fire, condition (d) emits a documented HEDGE-05 null PDF rather than dropping into an intermediate state. Residual risk: a heavy-tailed clayton fit with high `λ` could still produce a characteristic function whose true (not MC-noisy) tail is heavy enough to defeat 2¹² FFT grid — but that's now a genuine "data is too heavy-tailed for our chosen FFT method" finding, which is exactly what condition (d) is designed to signal.

## Recommendation

Accept. Iter-2 MC-noise regression closed via Path A. Plans ready for `/gsd:execute-phase 4`.
