// fetch/src/blockscout/freshness.ts
// FETCH-03 — Blockscout silent-stale-data gate (PITFALLS §2).
//
// CORRECTED per RESEARCH.md §H (orchestrator finding #1): the per-log
// consensus field hypothesized by the Phase-0 CONTEXT.md draft is absent
// from both `/api/v2/addresses/{addr}/logs` and the v1
// `/api?module=logs&action=getLogs` shape (verified via live probe in
// RESEARCH §C). This wrapper relies exclusively on the lag of the
// most-recently-indexed log block versus the Forno head (Celo eth_blockNumber).
//
// Threshold semantics mirror subgraphFreshness: default 100 blocks ≈ 100s at
// Celo's 1s/block, fails fast on stalled indexers.
//
// Returns `{ lag, fresh: true }` on success so callers can log the observed
// lag for the cost-ledger / monitoring without re-querying Forno.

import type { PublicClient } from 'viem';

export class BlockscoutFreshnessError extends Error {
  constructor(
    public details: {
      most_recent_log_block: number;
      forno_head: number;
      lag: number;
      threshold: number;
      endpoint: string;
    }
  ) {
    super(
      `Blockscout response stale: lag=${details.lag} blocks > threshold=${details.threshold} ` +
        `from ${details.endpoint}`
    );
    this.name = 'BlockscoutFreshnessError';
  }
}

export async function blockscoutFreshness({
  most_recent_log_block,
  forno,
  threshold = 100,
  endpoint,
}: {
  most_recent_log_block: number;
  forno: PublicClient;
  threshold?: number;
  endpoint: string;
}): Promise<{ lag: number; fresh: true }> {
  const head = Number(await forno.getBlockNumber());
  const lag = head - most_recent_log_block;
  if (lag > threshold) {
    throw new BlockscoutFreshnessError({
      most_recent_log_block,
      forno_head: head,
      lag,
      threshold,
      endpoint,
    });
  }
  return { lag, fresh: true };
}
