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
import { describe, test, expect, beforeEach } from 'vitest';
import { readFileSync, existsSync } from 'node:fs';
import { rm } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { cacheKeyHash, canonicalize } from '../src/cache/key.js';
import {
  appendManifestIfNew,
  readManifest,
  findByCacheKey,
  type ManifestEntry,
} from '../src/cache/manifest.js';
import { writeCachePayload } from '../src/cache/parquet-writer.js';

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

// ───────────────────────────────────────────────────────────────────────────
// Task 2 — manifest writer + deterministic payload writer (FETCH-04 byte-identity)
// ───────────────────────────────────────────────────────────────────────────

const TEST_MANIFEST = 'data/raw/manifest.test.json';

const validEntry: ManifestEntry = {
  cache_key_hash: 'a'.repeat(64),
  chainId: 42220,
  contractAddress: '0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F',
  blockRange: [67_800_000, 67_800_100],
  fetchTimestamp: '2026-05-25T12:00:00.000Z',
  dataHash: 'b'.repeat(64),
  gitCommit: 'deadbeef',
  endpoint: 'blockscout',
  query_count: 1,
  usdc_cost: '0.000',
  paid_real: false,
  protocol: 'ichi',
  fetcher_version: '0.1.0',
};

describe('manifest writer (FETCH-04)', () => {
  beforeEach(async () => {
    if (existsSync(TEST_MANIFEST)) await rm(TEST_MANIFEST);
  });

  test('readManifest on missing file returns empty array (no throw)', async () => {
    const r = await readManifest('data/raw/_definitely_missing_manifest.json');
    expect(r).toEqual([]);
  });

  test('appendManifestIfNew appends a fresh entry', async () => {
    const r = await appendManifestIfNew(validEntry, TEST_MANIFEST);
    expect(r.appended).toBe(true);
    const all = await readManifest(TEST_MANIFEST);
    expect(all.length).toBe(1);
    expect(all[0].cache_key_hash).toBe(validEntry.cache_key_hash);
  });

  test('appendManifestIfNew is idempotent on duplicate cache_key_hash', async () => {
    await appendManifestIfNew(validEntry, TEST_MANIFEST);
    const r2 = await appendManifestIfNew(validEntry, TEST_MANIFEST);
    expect(r2.appended).toBe(false);
    expect(r2.existing?.cache_key_hash).toBe(validEntry.cache_key_hash);
    const all = await readManifest(TEST_MANIFEST);
    expect(all.length).toBe(1);
  });

  test('findByCacheKey returns null for missing hash', async () => {
    const r = await findByCacheKey('c'.repeat(64), TEST_MANIFEST);
    expect(r).toBeNull();
  });

  test('findByCacheKey returns the entry after append', async () => {
    await appendManifestIfNew(validEntry, TEST_MANIFEST);
    const r = await findByCacheKey(validEntry.cache_key_hash, TEST_MANIFEST);
    expect(r).not.toBeNull();
    expect(r?.endpoint).toBe('blockscout');
  });

  test('zod rejects invalid endpoint', async () => {
    await expect(
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      appendManifestIfNew({ ...validEntry, endpoint: 'unknown' as any }, TEST_MANIFEST),
    ).rejects.toThrow();
  });

  test('manifest entry shape: fetchTimestamp is metadata-only (NOT in cache key)', () => {
    // Sanity: the canonical key bytes derived from manifest fields exclude fetchTimestamp.
    // This is the load-bearing FETCH-04 paid-step-is-idempotent invariant at the
    // schema level — a manifest entry's cache_key_hash MUST be reproducible from
    // (chainId, contractAddress, blockRange) ALONE.
    const reproducible = cacheKeyHash({
      chainId: validEntry.chainId,
      contractAddress: validEntry.contractAddress,
      blockRange: validEntry.blockRange,
    });
    // The validEntry uses a synthetic 'a'.repeat(64) for the hash field, so we
    // assert structural exclusion: the canonical form contains exactly the 3 keys.
    const canon = canonicalize({
      chainId: validEntry.chainId,
      contractAddress: validEntry.contractAddress,
      blockRange: validEntry.blockRange,
    });
    expect(reproducible).toMatch(/^[0-9a-f]{64}$/);
    expect(canon).not.toContain('fetchTimestamp');
    expect(canon).not.toContain('dataHash');
    expect(canon).not.toContain('gitCommit');
  });
});

describe('writeCachePayload (FETCH-04 byte-identity)', () => {
  const cleanup = async () => {
    if (existsSync('data/raw/test-byte-id')) await rm('data/raw/test-byte-id', { recursive: true });
  };
  beforeEach(cleanup);

  test('two identical writes produce byte-identical files (FETCH-04 SC-4 unit-level)', async () => {
    const rows = [
      { blockNumber: 67_800_005, txHash: '0xabc', amount0: '1000' },
      { blockNumber: 67_800_006, txHash: '0xdef', amount0: '2000' },
    ];
    const opts = { cache_key_hash: 'a'.repeat(64), protocol: 'test-byte-id' };
    const r1 = await writeCachePayload(rows, opts);
    const sha1 = createHash('sha256').update(readFileSync(r1.path)).digest('hex');
    const r2 = await writeCachePayload(rows, opts);
    const sha2 = createHash('sha256').update(readFileSync(r2.path)).digest('hex');
    expect(sha1).toBe(sha2);
    expect(r1.dataHash).toBe(r2.dataHash);
    expect(r1.path).toBe(r2.path);
  });

  test('dataHash returned matches file content sha256', async () => {
    const rows = [{ x: 1 }];
    const r = await writeCachePayload(rows, { cache_key_hash: 'b'.repeat(64), protocol: 'test-byte-id' });
    const fileHash = createHash('sha256').update(readFileSync(r.path)).digest('hex');
    expect(r.dataHash).toBe(fileHash);
  });

  test('empty rows array writes an empty file (no trailing newline)', async () => {
    const r = await writeCachePayload([], { cache_key_hash: 'd'.repeat(64), protocol: 'test-byte-id' });
    const content = readFileSync(r.path, 'utf-8');
    expect(content).toBe('');
    const expectedHash = createHash('sha256').update('').digest('hex');
    expect(r.dataHash).toBe(expectedHash);
  });

  test('payload path follows data/raw/<protocol>/<prefix>/<hash>.jsonl layout', async () => {
    const hash = 'ef' + 'a'.repeat(62);
    const r = await writeCachePayload([{ x: 1 }], { cache_key_hash: hash, protocol: 'test-byte-id' });
    expect(r.path).toBe(`data/raw/test-byte-id/ef/${hash}.jsonl`);
  });
});
