// fetch/src/cache/manifest.ts — FETCH-04 cache-manifest writer.
//
// Per CONTEXT.md (locked): `data/raw/manifest.json` is the append-only registry
// of per-fetch entries. The `cache_key_hash` field is the content-addressed
// primary key — duplicates are idempotent (no-op append + return existing entry).
//
// `fetchTimestamp` is stored as METADATA only, NOT in the canonical cache key
// (cache key is sha256(canonicalize({chainId, contractAddress, blockRange}))).
// Re-running an identical fetch is therefore a manifest cache hit with zero new
// rows AND zero new cost-ledger rows — the FETCH-04 paid-step-is-idempotent
// invariant Plan 01-08 verifies end-to-end.
//
// Atomic-write strategy: write to `<path>.tmp` then `rename()` — a partial write
// during a power-loss / kill-9 leaves the prior manifest intact rather than a
// half-written file. This matches the cost-ledger's append discipline.

import { readFile, writeFile, mkdir, rename } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname } from 'node:path';
import { z } from 'zod';

/**
 * Enum of endpoints whose costs flow into the cost-ledger.
 *
 * The 90k/mo Graph soft-cap counts ONLY `graph-mainnet` rows. `blockscout`,
 * `forno`, `graph-sepolia`, and `x402-mock-sepolia` rows are logged for audit
 * but uncapped (CONTEXT.md FETCH-02 decisions).
 */
export const EndpointEnum = z.enum([
  'graph-mainnet',
  'graph-sepolia',
  'blockscout',
  'forno',
  'x402-mock-sepolia',
]);
export type Endpoint = z.infer<typeof EndpointEnum>;

export const ManifestEntrySchema = z.object({
  /** sha256(canonical(chainId, contractAddress, blockRange)) — 64-char lowercase hex. */
  cache_key_hash: z.string().regex(/^[0-9a-f]{64}$/),
  chainId: z.number().int(),
  contractAddress: z.string(),
  /** [fromBlock, toBlock] inclusive. */
  blockRange: z.tuple([z.number(), z.number()]),
  /** ISO-8601 UTC; metadata only — NOT part of cache key (FETCH-04 invariant). */
  fetchTimestamp: z.string(),
  /** sha256 of the cached payload file content — verified by Plan 01-08 sha256sum cmp. */
  dataHash: z.string().regex(/^[0-9a-f]{64}$/),
  /** Short git rev; provenance for downstream Phase-2 panel reproducibility. */
  gitCommit: z.string(),
  endpoint: EndpointEnum,
  query_count: z.number().int().nonnegative(),
  /** Decimal-string for arbitrary-precision USDC accounting; never JS-number. */
  usdc_cost: z.string(),
  /** True iff a real USDC tx (mainnet OR testnet) was broadcast; false for cache hits / mocks-without-onchain-settle. */
  paid_real: z.boolean(),
  /** Protocol slug from protocols/<slug>.toml (e.g. "ichi"). */
  protocol: z.string(),
  /** fetch/ workspace package.json version at fetch time. */
  fetcher_version: z.string(),
});
export type ManifestEntry = z.infer<typeof ManifestEntrySchema>;

const DEFAULT_MANIFEST = 'data/raw/manifest.json';

/**
 * Read & parse the manifest array. Returns [] if the file is missing or empty.
 * Throws if the file exists with non-empty content that fails zod parse — a
 * corrupted manifest is a hard error, NOT silently ignored.
 */
export async function readManifest(
  path: string = DEFAULT_MANIFEST,
): Promise<ManifestEntry[]> {
  if (!existsSync(path)) return [];
  const text = await readFile(path, 'utf-8');
  if (text.trim().length === 0) return [];
  const arr = JSON.parse(text);
  return z.array(ManifestEntrySchema).parse(arr);
}

/**
 * Idempotent append. If `entry.cache_key_hash` already exists in the manifest,
 * returns `{ appended: false, existing }` without touching disk. Otherwise
 * atomically rewrites the manifest with the new entry appended.
 */
export async function appendManifestIfNew(
  entry: ManifestEntry,
  path: string = DEFAULT_MANIFEST,
): Promise<{ appended: boolean; existing?: ManifestEntry }> {
  // Validate-first: refuse to even read the manifest if the entry is malformed.
  ManifestEntrySchema.parse(entry);
  const existing = await readManifest(path);
  const dup = existing.find((e) => e.cache_key_hash === entry.cache_key_hash);
  if (dup) return { appended: false, existing: dup };
  const next = [...existing, entry];
  if (!existsSync(dirname(path))) await mkdir(dirname(path), { recursive: true });
  const tmp = `${path}.tmp`;
  await writeFile(tmp, JSON.stringify(next, null, 2));
  await rename(tmp, path);
  return { appended: true };
}

/**
 * Look up a manifest entry by cache_key_hash. Returns null if not found.
 * The CLI cache short-circuit path (Plan 01-06) calls this BEFORE any network call.
 */
export async function findByCacheKey(
  cache_key_hash: string,
  path: string = DEFAULT_MANIFEST,
): Promise<ManifestEntry | null> {
  const all = await readManifest(path);
  return all.find((e) => e.cache_key_hash === cache_key_hash) ?? null;
}
