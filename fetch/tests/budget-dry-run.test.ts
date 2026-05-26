// fetch/tests/budget-dry-run.test.ts — Plan 01-06 lands the real assertions.
import { describe } from 'vitest';

describe.todo('Budget dry-run estimator (FETCH-02 SC-6 / Plan 01-06)', () => {
  // Will assert: `pnpm fetch ichi --dry-run --estimate-budget` reads
  // notes/forno_head_snapshot.json (via fetch/src/constants.ts loadFornoHeadSnapshot)
  // and prints a cost estimate WITHOUT calling Forno or any paid endpoint.
});
