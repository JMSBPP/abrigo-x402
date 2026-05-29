## VERDICT

PASS

## Scope

Reality check on DGP-01 (Kirchner INAR(p) NHPP fit via statsmodels VAR with AIC bin-width selection on the locked `{60, 300, 900, 3600}`s grid + non-negativity projection).

## Findings

- Bivariate count matrix (`np.column_stack([counts_0, counts_1])`) — NOT a summed univariate shortcut — so PITFALLS §5 (cross-leg covariance leakage) is structurally avoided.
- Kirchner non-negativity step implemented as `np.maximum(raw_coefs, 0.0)` + `np.maximum(fit.intercept, 0.0)` and a `raw_coefs_had_negatives` audit flag — matches arxiv:1509.02017 §6.
- AIC table over the locked grid is recorded in `bin_width_aic_table` and the acceptance criteria assert the selected bin is `in {60.0, 300.0, 900.0, 3600.0}` — off-grid selection would fail collection.
- Synthetic recovery test reduced from the SC-2 spec (1000 paths / ±10%) to 50 paths / ±15% for CI runtime; the gap is explicitly called out in the test docstring and rolled forward to 03-08 as a once-per-phase manual sanity. This is the gsd-plan-checker INFO observation and is handled.

## Reality check

The most plausible failure at execution is `statsmodels.tsa.api.VAR.select_order` silently returning `aic=0` (degenerate) when `n_bins // 3 < 1` at the 3600s bin width on a thin panel (30 days / 3600s = 720 bins — fine, but a shorter window or sparser leg would underflow). The plan clamps with `max(int(sel.aic), 1)` and wraps in `try/except → p_star=1`, which prevents a crash but masks the degeneracy — a fit at `p=1` on degenerate data can still recover a baseline within ±15% tolerance and "pass" without anyone noticing the order selection broke.

## Recommendation

Accept. Plan implements DGP-01 correctly; the degeneracy-masking is acceptable for the scaffold and will surface in 03-08's manual production-rep run if it matters.
