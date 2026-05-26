// fetch/tests/freshness.test.ts — Plan 01-03 lands the real assertions.
import { describe } from 'vitest';

describe.todo('blockscoutFreshness + subgraphFreshness lag gate (FETCH-03 / Plan 01-03)', () => {
  // Will assert: lag <= 100 blocks vs Forno head = pass; lag > 100 = throw
  // BlockscoutFreshnessError / SubgraphFreshnessError with structured details.
});
