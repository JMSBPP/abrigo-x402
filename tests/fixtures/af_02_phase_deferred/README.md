# AF-02 fixture (PHASE-DEFERRED): hand-tuned p-values

Active check deferred to Phase 3+ — no fixture trigger needed at Phase 0; the AF
is documented but the hook is a passthrough until Phase 3+ analysis/src/ exists
with model-fitting code that reports p-values.

When Phase 3+ adds analysis/src/, add a violating fixture here: a synthetic Python
file in fetch/src or analysis/src setting `alpha = 0.05` (non-pre-registered).
