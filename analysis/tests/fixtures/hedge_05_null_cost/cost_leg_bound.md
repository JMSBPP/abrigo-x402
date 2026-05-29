---
verdict: FAIL
protocol: ichi-fixture
threshold_queries_per_month: 100000
measured_queries_per_month: 5000
---

# Cost-Leg Bound Memo (FIXTURE — synthetic for HEDGE-05 firing test)

This fixture forces HEDGE-05 firing condition (a) `null_cost`. The DGP and convex
gate both pass (LR rejects NHPP, all four conditions pass); the cost-leg bound is
the sole firing trigger.

Synthetic content — not a real cost-leg analysis.
