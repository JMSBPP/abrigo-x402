// fetch/src/cache/key.ts — FETCH-04 content-addressed cache key.
//
// Per CONTEXT.md (locked): cache key = sha256(canonical(chainId, contractAddress, blockRange)).
// `fetchTimestamp` is NEVER in the key — it is metadata only (manifest.json field).
// This honours FETCH-04's paid-step-is-idempotent invariant: re-running the same
// fetch produces byte-identical Parquet/JSONL output AND zero new cost-ledger rows.
//
// CRITICAL (checker C2 mechanical byte-stability):
// `canonicalize()` MUST use an explicit string template literal — NOT `JSON.stringify`
// with an array second-arg. The array form is a PROPERTY FILTER per spec, NOT a key-order
// specifier; it is byte-stable today only by accident of V8's insertion-order preservation.
// The explicit template literal makes byte-identity a contract of THIS file, mechanically
// independent of any JS engine's stringify implementation.
//
// Tests in fetch/tests/cache.test.ts pin the exact byte-content against a hand-written
// reference string — any drift in key order, whitespace, or address-case breaks them.

import { createHash } from 'node:crypto';

export interface CacheKeyInput {
  chainId: number;
  /** EIP-55 mixed-case OR all-lowercase; canonicalized to lowercase internally. */
  contractAddress: string;
  /** [fromBlock, toBlock] inclusive. */
  blockRange: [number, number];
}

/**
 * Canonical serialization of a cache key input.
 *
 * Alphabetical key order (blockRange, chainId, contractAddress), no whitespace,
 * lowercase contractAddress. Numbers serialize via JS default (no trailing `.0` for
 * integers; `Number.MAX_SAFE_INTEGER` covers any plausible Celo block range).
 *
 * Byte-identity contract: this function returns a string mechanically identical
 * to the hand-written reference string asserted in the test suite.
 */
export function canonicalize({ chainId, contractAddress, blockRange }: CacheKeyInput): string {
  const addr = contractAddress.toLowerCase();
  const lo = blockRange[0];
  const hi = blockRange[1];
  return `{"blockRange":[${lo},${hi}],"chainId":${chainId},"contractAddress":"${addr}"}`;
}

/**
 * sha256 hex digest of the canonical serialization. 64-character lowercase hex string.
 * Stable across runs, machines, and Node versions (RFC 6234 sha256 is deterministic).
 */
export function cacheKeyHash(input: CacheKeyInput): string {
  return createHash('sha256').update(canonicalize(input)).digest('hex');
}
