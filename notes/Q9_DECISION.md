# Q-9 Decision: cCOP Panel Construction (Iteration 2 / Steer on cCOP/USDT)

**Committed:** 2026-05-25

**Status:** Locked — V3-anchor-only primary panel + V3+V4+Broker unified fallback. Both paths pre-registered. Spec swap after seeing data is forbidden (AF-03).

**Cross-reference:** This decision is also recorded in `notes/PRE_REGISTRATION.md` `## Q-9 Fallback Pre-Registration` — both files MUST agree on numeric trigger threshold values.

## Background

The question (per CANDIDATES.md §7 Hidden-Volume Audit + REQUIREMENTS.md REPRO-04):

> "cCOP panel construction — V3-anchor-only (~580–625 swaps/30d) OR V3+V4+Broker unified (~900 events/30d adding Mento V2 Broker ~185/30d + Uniswap V4 PoolManager cCOP routing ~90/30d)."

Stakes: AF-03 spec-swap-after-seeing-results vs. AF-12 silent-re-scope. The fallback choice MUST be pre-registered to avoid an ad-hoc Phase-6 spec swap after seeing V3-only fit results. The unified-panel path cannot be a backup plan invented in Phase 6 once the V3-only fit shows wide CIs; if it is allowed to materialize then, every analysis-stage observation about V3-only inadequacy becomes a post-hoc justification for re-scoping. The pre-registration commits the fallback path BEFORE any data is fetched, so Phase 6 only OBSERVES whether the trigger conditions hold; it never DECIDES whether to switch.

## Primary Decision: V3-Anchor-Only

**Headline panel: cCOP/USDT Uniswap V3 Swap stream on pool `0x2AC5baA668A8A58FD0e302B9896717484fd217B0`.**

- Event class: Uniswap V3 `Swap` events (topic `0xc42079f9...`).
- Volume: ~580–625 swaps/30d per CANDIDATES.md §7.3 (corrected count post-thinness-retraction).
- Why primary: No pooling assumption to defend at the headline. Single-event-class panel construction is the cleanest reproducibility surface for the per-iteration swap-surface (REPRO-01 / REPRO-02). Single-class arrivals admit direct NHPP-vs-Hawkes LR specification with no need to defend an exchangeability claim across heterogeneous venues.
- Cost of choice: Ignores ~38% of cCOP cashflow signal (~275 swap-equivalents/30d from Broker + V4 channels per CANDIDATES §7.3). Acceptable v1 tradeoff: simpler model, fewer assumptions, lower spec-risk. The omitted channels are documented under "ignored signal scope" in the headline narrative; their absence is a known truncation, not a silent omission.

## Pre-Registered Fallback: V3+V4+Broker Unified

**Switch trigger (BOTH conditions MUST hold):**

1. **Sample-size or precision floor failure** — the V3-only sample fails one of:
   - V3-only sample size < 300 events over the fitted window (Hawkes branching-ratio identifiability floor per PITFALLS §4), OR
   - Hawkes branching-ratio profile-likelihood CI width > 0.4 (conventional precision floor — wider CI means η is not usefully bounded for the four-criterion gate).
2. **Cross-class permutation test passes (fails to reject pooling assumption)** — cross-class permutation test (1000 reps; null hypothesis = three event classes V3 Swap + V4 PoolManager + Mento V2 Broker share common arrival-process structure; alternative = at least one class differs) returns p > 0.05.

**If both hold:** Switch to V3+V4+Broker unified panel.

- V3 Swap events on `0x2AC5baA668A8A58FD0e302B9896717484fd217B0` (~580–625 events/30d).
- V4 PoolManager events on `0x288dc841A52FCA2707c6947B3A777c5E56cd87BC` filtered to cCOP-counterparty (~90 V4 swap-equivalents/30d).
- Mento V2 Broker mint/burn events on `0x777A8255cA72412f0d706dc03C9D1987306B4CaD` filtered to cCOP-counterparty (~185 swap-equivalents/30d).
- Total: ~900 events/30d per CANDIDATES §7.3.

**If V3-only sample passes precision floor OR permutation test rejects pooling:** Stay on V3-anchor-only. The fit is interpreted with the V3-only signal scope explicitly stated. The unified-panel code remains dead-code-exercised; its dormancy is part of the audit trail, not a defect.

**Why this is pre-registration, not Phase-6 ad-hoc decision:** AF-03 (spec-swap-after-seeing-results) forbids changing the headline specification after the data fit. The fallback path is committed HERE with explicit numeric trigger conditions; Phase 6 only OBSERVES whether the conditions hold, never DECIDES whether to switch. Any deviation from the numeric trigger logic in Phase 6 must surface as a `## VERDICT: BLOCKER` in the 2-way review trail before the commit lands.

## Cross-Class Permutation Test Specification

The pooling assumption (V3 + V4 + Broker share a common arrival-process structure) is the load-bearing claim if the fallback fires. The permutation test specification:

- **Null hypothesis (H₀):** The inter-event-time distributions of V3 Swap events, V4 PoolManager cCOP-touching events, and Mento V2 Broker cCOP mint/burn events are draws from the same arrival process (common λ(t) or common Hawkes self-excitation structure).
- **Alternative hypothesis (H₁):** At least one of the three event classes is drawn from a structurally different arrival process.
- **Test statistic:** Cross-class Kolmogorov-Smirnov D statistic between the three pairwise distributions of inter-event times — D = max(D_{V3,V4}, D_{V3,Broker}, D_{V4,Broker}).
- **Permutation procedure:** 1000 permutations randomly relabeling event-class labels across the pooled event stream while preserving timestamps; recompute D under each permutation; build empirical null distribution.
- **Decision rule:** Reject the pooling assumption if observed D > 95th percentile of permuted D distribution (p < 0.05). FAIL to reject (p > 0.05) → pooling assumption is statistically permissible, fallback may proceed if condition 1 also holds.
- **Implementation:** `analysis/src/abrigo_x402/panel/cross_class_permutation.py` with deterministic seed for reproducibility. Test in `analysis/tests/test_cross_class_permutation.py` validates against synthetic data with known null + alternative distributions.
- **Multiple-testing note:** No correction is applied across the three pairwise comparisons because the max-D statistic already controls the family-wise error rate by construction; the permutation distribution is built on the same max statistic, so the 95th-percentile cutoff is family-wise valid.

## Phase 2 Code Obligation (REPRO-02 Invariant)

Per REQUIREMENTS.md REPRO-02 ("Iteration 2 must run the same Phase 2–5 pipeline end-to-end on Steer-on-cCOP/USDT with no edits to fetch/src or analysis/src"):

**Both the unified-panel pooling code AND the cross-class permutation test code MUST live in `analysis/src/` from Phase 2 onwards, dead-code-exercised by synthetic unit tests in Iteration 1.**

Specifically:

- `analysis/src/abrigo_x402/panel/unified.py` — builds the V3+V4+Broker unified panel from three event-class inputs. Exists in Phase 2 (Iteration 1), dead-code-exercised by `analysis/tests/test_unified_panel_synthetic.py` against synthetic three-class fixtures.
- `analysis/src/abrigo_x402/panel/cross_class_permutation.py` — performs the permutation test specified above. Exists in Phase 2, dead-code-exercised by `analysis/tests/test_cross_class_permutation.py`.
- `analysis/src/abrigo_x402/panel/__init__.py` — exports `build_v3_anchor_panel()` AND `build_unified_panel()` AND `cross_class_permutation_test()`. All three signatures present in Phase 2.

This obligation is enforced by the Phase 1 SC-5 protocol-agnosticism contract test + the REPRO-01 leak-gate `grep -ri "ichi" fetch/src analysis/src` (must return 0 before Phase 6 starts). The Iter-1-complete → Iter-2-complete diff on `analysis/src/` must be empty; any module that needs to exist in Iter-2 must already exist (and be exercised) in Iter-1.

## Pooling-Assumption Argument Structure

If the fallback fires, the report (Iteration 2 `reports/steer.pdf` or `reports/steer_null_result.pdf`) MUST include the following argument structure:

1. State the pooling assumption: "We pool V3 Swap + V4 PoolManager + Mento V2 Broker events as a unified arrival process for cCOP."
2. Justify empirically: "The cross-class permutation test (1000 reps) returned p = [X] > 0.05, failing to reject the common-arrival-structure null."
3. State the consequence: "Headline DGP parameters (μ, α, β, η) are estimated on the unified panel."
4. Quantify the alternative: "Under V3-only panel, the same fit produces parameters (μ', α', β', η') with branching-ratio profile-likelihood CI width [W'] > 0.4 (precision floor failure trigger)."
5. State the sensitivity: "The convex-dominance / hedge-strip conclusions are reported separately under V3-only and unified panels in the cost-leg sensitivity sweep (REPORT-03 / D-09)."

This argument structure must be templated into the Phase 5 / Phase 6 report build so it cannot be silently omitted. Omission of any of the five steps is a 2-way-review BLOCKER, not a NEEDS REVISION.

## Sources

- CANDIDATES.md §7 Hidden-Volume Audit (channels: V3 + V4 + Broker)
- CANDIDATES.md §7.3 (corrected event counts: V3 ~580–625, V4 ~90, Broker ~185)
- CANDIDATES.md §7.5 Q9 (open question #9: include all three event classes / V3 only / V3 + covariates)
- PITFALLS.md §4 (Hawkes branching-ratio identifiability + profile-likelihood CIs + boundary-correct LR test)
- PITFALLS.md §5 (cross-leg dependence; multivariate Hawkes specification)
- FEATURES.md AF-03 (spec-swap discipline); AF-12 (silent re-scope); D-03 (pre-registration)
- REQUIREMENTS.md REPRO-02 (parameter-driven re-runnability invariant)
- REQUIREMENTS.md REPRO-04 (cCOP panel construction decision)
- notes/PRE_REGISTRATION.md `## Q-9 Fallback Pre-Registration` (must match this document verbatim on numeric thresholds)

---

*Q-9 Decision Locked: 2026-05-25*
