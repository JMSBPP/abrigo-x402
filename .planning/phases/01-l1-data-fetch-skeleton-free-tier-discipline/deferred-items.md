# Phase 01 — Deferred Items

Cross-plan discoveries that fall outside the scope of the plan that discovered them.

## Logged by Plan 01-03 (freshness wrappers, 2026-05-26)

### Pre-existing failure in `fetch/tests/blockscout-client.test.ts`

- **Owner:** Plan 01-05 (Blockscout client — Wave 1b parallel sibling)
- **Symptom:** Single test failure at line 150 — cursor pagination expects `fromBlock=67502983` but receives `fromBlock=67508615`. Other 8 tests in that file pass.
- **Scope ruling:** This file is owned by 01-05, not 01-03. Plan 01-03 only touches `fetch/src/{subgraph,blockscout}/freshness.ts` and `fetch/tests/freshness.test.ts`. The blockscout client cursor-advance logic is out of scope.
- **Action:** Surface to Plan 01-05 executor (likely already aware — they own the file). No fix attempted from 01-03.
- **Verified non-regression:** Full suite shows 1 file failed / 6 passed / 4 skipped; the failing file is `tests/blockscout-client.test.ts`, which was already failing before 01-03 touched the tree (01-03 only added `tests/freshness.test.ts` + `src/subgraph/freshness.ts` + `src/blockscout/freshness.ts`).
