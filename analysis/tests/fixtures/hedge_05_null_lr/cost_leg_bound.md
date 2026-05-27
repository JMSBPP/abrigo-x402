---
verdict: PASS
protocol: ichi-fixture
threshold_queries_per_month: 100000
measured_queries_per_month: 150000
---

# Cost-Leg Bound Memo (FIXTURE — synthetic for HEDGE-05 firing test)

This fixture forces HEDGE-05 firing condition (b) `null_lr`. The cost-leg passes
(verdict=PASS) and the convex gate has `any_condition_passed=true`, but the LR test
fails to reject NHPP at α=0.05 (p_value=0.5). The LR firing condition dominates
because the decision tree evaluates cost -> lr -> convex in order.

Synthetic content — not a real cost-leg analysis.
