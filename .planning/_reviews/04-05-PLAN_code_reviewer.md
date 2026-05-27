## VERDICT

PASS

## Scope

Code-reviewer pass on Plan 04-05 (Wave 1: `compute_strip` FFT-based Carr-Madan static-replication on 2^11→2^12 escalation grid + abort-to-`strip_degenerate.json` + 0.1% PRE_REG positivity tolerance + polymorphic payoff (RESEARCH Pattern 5); 5 tests).

## Findings

- Frontmatter: `wave: 1`, `depends_on: [pre, "00"]`, `files_modified` is `hedge/carr_madan_strip.py` + its test file — disjoint from Wave-1 siblings
- Anti-pattern grep gate is the load-bearing safety net: `! grep -E "scipy\.integrate\.(quad|fixed_quad|romberg)|np\.trapz" carr_madan_strip.py` + Test 5 — addresses RESEARCH §Anti-Patterns directly. The grep is run in both the `<verify>` automated block AND as an acceptance criterion
- `POSITIVITY_TOLERANCE = 0.001` constant + acceptance grep `grep -q "POSITIVITY_TOLERANCE.*=.*0\.001"` ties the implementation to the PRE_REGISTRATION amendment (committed by Plan 04-pre) — the `key_links` table makes this explicit
- 2^11 → 2^12 single-escalation operationalized via `max_escalations: int = 1` parameter + `for attempt in range(max_escalations + 1)` loop body — clean, no silent multi-escalation
- Abort-to-`strip_degenerate.json` path: degenerate dict carries `{max_negative_value, total_negative_mass, characteristic_function_decay_rate, recommended_method}` — recommended_method ∈ {"COS", "PROJ", "none"} per CONTEXT.md, but the implementation does NOT actually compute COS/PROJ — only records the recommendation (Test 3 verifies this)
- Polymorphic payoff `payoff: Callable[[np.ndarray], np.ndarray]` signature acceptance: `grep -q "payoff: Callable"` — RESEARCH Pattern 5 / v2.0 streaming-tokenization API future-compatibility
- FFT implementation uses `np.fft.fftshift(np.fft.ifft(np.fft.ifftshift(phi_values))) * n_grid * du / (2π)` — the `fftshift`/`ifftshift` pair is the correct numerical pattern for symmetric u-grids; `np.real()` discards numerical-noise imaginary parts. No silent dependency on `scipy.fft` either (both work; CONTEXT.md picks `numpy.fft`)
- Test design for escalation/degenerate paths uses `slow_decay_char_func(alpha)` surrogate (`np.exp(-|u|^alpha)`) with alpha=1.5 (borderline) and alpha=0.3 (pathological) — captures the FFT-truncation phenomenology without requiring real fat-tail joint distributions
- Test 2 (escalation triggers) accepts EITHER 2^11/2^12 success OR degenerate result — pragmatic given that the exact escalation point depends on numpy/scipy version and FFT precision; the locked-behavior assertion is "if 2^11 fails AND 2^12 succeeds → escalated_to_2_12 == True", which IS deterministic on a given platform
- u_max truncation = 200.0 (planner's discretion); recorded in SUMMARY output

## Recommendation

Accept.
