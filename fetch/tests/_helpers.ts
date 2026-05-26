// fetch/tests/_helpers.ts
// Phase 1 shared test helpers. fetch/package.json declares "type": "module" so
// the CJS global __dirname is undefined at runtime. Every test file that needs
// the directory of the test source MUST import testDirname from here.
//
// Owned by Plan 01-01. Consumed by Plans 01-03 (freshness tests) and 01-05
// (blockscout-client + protocol-agnostic tests) in Wave 1b.
//
// Conventions:
//   - All fixtures live under fetch/tests/fixtures/ (gitignored data is forbidden;
//     captured-once JSON only). Integration tests that hit real networks live
//     under fetch/tests/integration/ and are excluded by vitest.config.ts.
//   - Helpers re-exported here are shared across all Wave 1 test files.

import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { vi } from 'vitest';

export const FETCH_TESTS_HELPERS_VERSION = '01-01' as const;

/**
 * ESM equivalent of the CJS `__dirname` global. Pass `import.meta.url` from
 * the calling file:
 *
 *     const __dirname = testDirname(import.meta.url);
 *
 * Required because fetch/package.json declares `"type": "module"` — raw
 * `__dirname` throws `ReferenceError: __dirname is not defined`.
 */
export function testDirname(metaUrl: string): string {
  return dirname(fileURLToPath(metaUrl));
}

/**
 * Shared Forno PublicClient mock. Used by freshness, cache, and blockscout-client
 * tests to avoid live RPC calls. Returns an object exposing the minimum surface
 * needed (getBlockNumber); cast as `any` at call sites to satisfy viem's
 * `PublicClient` type.
 *
 * Example:
 *
 *     const client = fornoMock(67896653n);
 *     await client.getBlockNumber(); // resolves to 67896653n
 */
export const fornoMock = (head: bigint) =>
  ({ getBlockNumber: vi.fn().mockResolvedValue(head) }) as unknown as {
    getBlockNumber: () => Promise<bigint>;
  };
