// fetch/src/cache/parquet-writer.ts — FETCH-04 deterministic payload writer.
//
// Phase 1 ships **deterministic JSONL** for the cached payload (consistent with
// the cost-ledger choice — JSONL is byte-stable across Node versions; Parquet
// from TS adds compression-dependency risk at zero empirical benefit for
// Phase-1 volumes ~ 4k events/30d). Phase 2 polars batch-converts JSONL → Parquet
// when the analysis layer ingests.
//
// Byte-identity contract (FETCH-04 SC-4 unit-level proof):
//   - Rows are written verbatim in CALLER's order (no internal sort).
//   - No `Date.now()`, no timestamp injection, no nondeterministic embedding.
//   - `JSON.stringify` per row with no indent and no whitespace, newline-delimited.
//   - Two invocations with identical inputs produce identical files AND identical
//     `dataHash` values. The full CLI-level sha256sum proof lives in Plan 01-08.
//
// File layout: `data/raw/<protocol>/<prefix>/<cache_key_hash>.jsonl`
//   where `prefix = cache_key_hash.slice(0, 2)` — 256-way fanout keeps any single
//   directory under ~10k entries even at multi-iteration scale.

import { writeFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join } from 'node:path';

export interface WriteCachePayloadOpts {
  /** sha256 hex from cacheKeyHash() — used for both the file name and the directory prefix. */
  cache_key_hash: string;
  /** Protocol slug (e.g. "ichi"). Drives the data/raw/<protocol>/ namespace. */
  protocol: string;
  /** Defaults to "data/raw" (CONTEXT.md FETCH-04 layout); overridable for tests. */
  root?: string;
}

export interface WriteCachePayloadResult {
  /** Absolute-ish path to the written JSONL file. */
  path: string;
  /** sha256 of the file content — used as the manifest's `dataHash` field. */
  dataHash: string;
}

/**
 * Write `rows` to a deterministic JSONL file at
 * `<root>/<protocol>/<cache_key_hash[0:2]>/<cache_key_hash>.jsonl`.
 *
 * Returns the path and the sha256 of the file content. Two invocations with
 * identical inputs produce byte-identical files and identical hashes.
 */
export async function writeCachePayload(
  rows: Record<string, unknown>[],
  opts: WriteCachePayloadOpts,
): Promise<WriteCachePayloadResult> {
  const { cache_key_hash, protocol, root = 'data/raw' } = opts;
  const prefix = cache_key_hash.slice(0, 2);
  const dir = join(root, protocol, prefix);
  if (!existsSync(dir)) await mkdir(dir, { recursive: true });
  const path = join(dir, `${cache_key_hash}.jsonl`);
  // Stable serialization: JSON.stringify per row in input order, no whitespace,
  // newline-delimited. Empty rows array → empty file (sha256 of "").
  const content = rows.length === 0
    ? ''
    : rows.map((r) => JSON.stringify(r)).join('\n') + '\n';
  await writeFile(path, content);
  const dataHash = createHash('sha256').update(content).digest('hex');
  return { path, dataHash };
}
