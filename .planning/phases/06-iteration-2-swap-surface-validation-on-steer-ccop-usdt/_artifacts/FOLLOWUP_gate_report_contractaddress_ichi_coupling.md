# Follow-up — steer gate/fit report metadata carries the ICHI contractAddress

**Status:** tracked, NOT fixed in Phase 6 (does not affect REPRO-02, the null_cost verdict, or the DGP fit).
**Severity:** MINOR (metadata-labeling coupling). 4th coupling alongside the 3 documented Plan-06-03 deviations.

## What
`data/fits/steer/0dc5bee374b6/gate_report.json` (the Iteration-2 Steer cCOP/USDT run) carries:
- `contractAddress: 0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F` — this is the **ICHI cKES/USDT pool**, NOT the Steer cCOP/USDT anchor pool (`0x2AC5baA668A8A58FD0e302B9896717484fd217B0`).

The gate/fit-report writer (in frozen `analysis/src`) defaults/hardcodes the contractAddress to the ICHI pool rather than deriving it from the active protocol spec. Same class as Plan-06-03 deviation 1 (`fetch/scripts/build_panel_real.ts` ichi hardcode).

## Why it does NOT undermine the phase result
- The **data is genuinely Steer's**: `blockRange: [65600000, 68190000]` (the Steer cCOP cold-backfill window, distinct from ICHI's `[67378253, 67896653]`); distinct `dataHash`; `gitCommit 33f3e00`.
- **REPRO-02 is unaffected**: gate_report.json is an OUTPUT under `data/fits/`, not source under `fetch/src`/`analysis/src` — the empty-diff invariant is on source, and it holds.
- **The `null_cost` verdict is unaffected**: it derives from `notes/steer_cost_leg_bound.md` (cost-leg FAIL), not from the gate_report contractAddress.
- The deepened `reports/steer_null_result.pdf` deliberately does NOT surface this mislabeled field (it shows the block range + run_id + the firing-relevant DGP fields instead).

## Why deferred
The fix is in frozen `analysis/src` (the gate/fit-report metadata writer must derive `contractAddress` from the protocol spec's anchor pool) — out of Phase 6's config-swap-only scope. It belongs with the other metadata-coupling fixes (build_panel_real.ts namespace, the iteration-2-full `--reports-pdf` path bug) in a future maintenance/baseline pass, sequenced as a standalone pre-iteration commit like the Phase-6 Wave-1 fixes.

## Acceptance for the follow-up
- A Steer (or any non-ICHI) run's `gate_report.json`/`fit_report.json` `contractAddress` equals the active protocol's anchor pool, derived from the spec — not a hardcoded ICHI default.
