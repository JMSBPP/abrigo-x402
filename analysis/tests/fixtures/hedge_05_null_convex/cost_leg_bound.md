---
verdict: PASS
protocol: ichi-fixture
threshold_queries_per_month: 100000
measured_queries_per_month: 150000
---

# Cost-Leg Bound Memo (FIXTURE — synthetic for HEDGE-05 firing test)

This fixture forces HEDGE-05 firing condition (c) `null_convex`. The cost-leg
passes (verdict=PASS), the LR test rejects NHPP (p_value=0.001), but the convex
gate has all four conditions failing (`any_condition_passed=false`).

Synthetic content — not a real cost-leg analysis.
