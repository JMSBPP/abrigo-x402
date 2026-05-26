// fetch/tests/cost-ledger.test.ts — Plan 01-02 lands the real assertions.
import { describe } from 'vitest';

describe.todo('Cost-ledger 90k Graph budget gate (FETCH-02 / Plan 01-02)', () => {
  // Will assert: cumulative graph-mainnet rows >= 90_000 aborts unless --force;
  // blockscout/forno/x402-mock-sepolia rows uncapped; ledger entries content-addressed.
});
