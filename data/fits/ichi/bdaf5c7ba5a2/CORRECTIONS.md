# CORRECTIONS

- HALT triggered 2026-05-29: KS held-out p > threshold (leg-0 p=0.0474 vs pre-registered α=0.05; min-leg aggregator → ks_held_out_passes=FALSE → gate_passes=FALSE, 3/4).
- This run (`bdaf5c7ba5a2`) is FROZEN at the realized result. gate_passes=FALSE is the pre-registered outcome; the descriptive findings (η≈0.600, LR rejects NHPP at p=0.0, held-out Hawkes beats NHPP by 114 nats) are reportable AS DESCRIPTIVE EVIDENCE only. Do NOT cite gate_passes as confirmatory / do NOT label the verdict a "pass" or "positive".
- Disposition memo: `.planning/phases/04.1.1-.../_artifacts/DISPOSITION_MEMO_04_1_1_ks_halt.md`.
- Awaiting user-enumerated pivot IF a verdict-flip attempt is desired — no alternative spec, threshold, KS aggregator, held-out split, or residual test has been authored.
- No post-hoc changes (KS α, aggregator, held-out fraction, leg weighting, test geometry, re-seed) have been applied between lock and HALT.
- Shipping the realized gate_passes=FALSE result faithfully via the pre-registered null/near-miss handling (firing_condition + verification + Phase 5 PDF) requires NO pivot — that path is already locked.
