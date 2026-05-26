// fetch/tests/cache.test.ts — Plan 01-04 lands the real assertions.
import { describe } from 'vitest';

describe.todo('Cache key idempotency (FETCH-04 / Plan 01-04)', () => {
  // Will assert: sha256(canonical(chainId, contractAddress, blockRange)) is
  // stable across reruns; fetchTimestamp is NOT part of the key; two-run
  // byte-identical parquet under data/raw/<protocol>/<hash>.parquet.
});
