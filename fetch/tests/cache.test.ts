// fetch/tests/cache.test.ts — Plan 01-04 FETCH-04 SC-4 unit tests.
//
// Two test groups land in this plan:
//   1) cacheKeyHash / canonicalize (Task 1) — content-addressed cache key with
//      mechanical byte-stability via explicit template literal (checker C2 fix).
//   2) manifest writer + deterministic payload writer (Task 2) — zod-validated
//      manifest with cache_key_hash idempotency, plus byte-identical JSONL writes.
//
// The "literal byte content" test in Task 1 is the load-bearing FETCH-04 SC-4
// guarantee: any deviation in key order, whitespace, or address-case breaks the
// hand-written reference string — NOT relying on V8 insertion-order preservation.
import { describe, test, expect } from 'vitest';
import { cacheKeyHash, canonicalize } from '../src/cache/key.js';

const POOL = '0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F';   // cKES/USDT
const POOL_LC = POOL.toLowerCase();

describe('cacheKeyHash (FETCH-04 SC-4)', () => {
  test('returns 64-char hex string', () => {
    const h = cacheKeyHash({ chainId: 42220, contractAddress: POOL, blockRange: [67_800_000, 67_800_100] });
    expect(h).toMatch(/^[0-9a-f]{64}$/);
  });

  test('case-invariant on contractAddress (EIP-55 mixed-case === lowercase)', () => {
    const h1 = cacheKeyHash({ chainId: 42220, contractAddress: POOL, blockRange: [67_800_000, 67_800_100] });
    const h2 = cacheKeyHash({ chainId: 42220, contractAddress: POOL_LC, blockRange: [67_800_000, 67_800_100] });
    expect(h1).toBe(h2);
  });

  test('differs by chainId', () => {
    const h1 = cacheKeyHash({ chainId: 42220, contractAddress: POOL, blockRange: [67_800_000, 67_800_100] });
    const h2 = cacheKeyHash({ chainId: 84532, contractAddress: POOL, blockRange: [67_800_000, 67_800_100] });
    expect(h1).not.toBe(h2);
  });

  test('differs by blockRange', () => {
    const h1 = cacheKeyHash({ chainId: 42220, contractAddress: POOL, blockRange: [67_800_000, 67_800_100] });
    const h2 = cacheKeyHash({ chainId: 42220, contractAddress: POOL, blockRange: [67_800_001, 67_800_100] });
    expect(h1).not.toBe(h2);
  });

  test('canonicalize contains lowercase address and no extra fields', () => {
    const c = canonicalize({ chainId: 42220, contractAddress: POOL, blockRange: [67_800_000, 67_800_100] });
    const parsed = JSON.parse(c);
    expect(parsed.contractAddress).toBe(POOL_LC);
    expect(Object.keys(parsed).sort()).toEqual(['blockRange', 'chainId', 'contractAddress']);
    expect(parsed).not.toHaveProperty('fetchTimestamp');
  });

  test('property-order invariant (input key order does not affect output)', () => {
    const a = canonicalize({ chainId: 42220, contractAddress: POOL, blockRange: [67_800_000, 67_800_100] });
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const b = canonicalize({ blockRange: [67_800_000, 67_800_100], chainId: 42220, contractAddress: POOL } as any);
    expect(a).toBe(b);
  });

  test('canonicalize: literal byte content (checker C2 — mechanical byte-stability)', () => {
    // Hand-written reference string. Any deviation in key order, whitespace, or
    // address-case breaks this test. This is the load-bearing FETCH-04 SC-4
    // byte-identity invariant — explicit template-literal output, NOT JSON.stringify
    // with a property-filter array (which does not enforce key order in spec).
    const out = canonicalize({
      chainId: 42220,
      contractAddress: '0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F',
      blockRange: [67000000, 67100000],
    });
    expect(out).toBe(
      '{"blockRange":[67000000,67100000],"chainId":42220,"contractAddress":"0x61ef8708fc240dc7f9f2c0d81c3124df2fd8829f"}',
    );
  });
});
