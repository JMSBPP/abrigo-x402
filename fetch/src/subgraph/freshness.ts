// fetch/src/subgraph/freshness.ts
// FETCH-03 — Subgraph silent-stale-data gate (PITFALLS §2).
//
// Every Graph query must include `_meta { block { number hash timestamp } }`.
// This wrapper compares the subgraph's anchor block against the Forno head
// (Celo mainnet eth_blockNumber) and throws `SubgraphLagError` when the lag
// exceeds the threshold (default 100 blocks ≈ 100s at Celo's 1s/block).
//
// Source: RESEARCH.md §G (Plan 01-03). The wrapper is endpoint-agnostic — it
// accepts a generic `response` shape and only inspects `_meta.block.number`,
// so the same code works for Uniswap-V3-on-Celo (Messari fork), Mento Broker,
// and any future subgraph deployment.
//
// Threshold rationale: 100 blocks = 100 seconds on Celo. Subgraph indexers
// typically reorg-buffer 10–30 blocks; 100 blocks gives an ~70-block safety
// margin while still failing fast on stalled indexers (REPRO-02-compatible
// per FETCH-03 SC-3).

import type { PublicClient } from 'viem';

export interface SubgraphMeta {
  block: { number: number; hash?: string; timestamp?: number };
}

export interface SubgraphFreshnessInput<T> {
  response: T & { _meta?: SubgraphMeta };
  forno: PublicClient;
}

export class SubgraphLagError extends Error {
  constructor(
    public details: {
      subgraph_block: number;
      forno_head: number;
      lag: number;
      threshold: number;
      deployment_id?: string;
    }
  ) {
    super(
      `Subgraph stale: lag=${details.lag} blocks > threshold=${details.threshold} ` +
        `(subgraph=${details.subgraph_block}, forno=${details.forno_head})`
    );
    this.name = 'SubgraphLagError';
  }
}

export async function subgraphFreshness<T>(
  { response, forno }: SubgraphFreshnessInput<T>,
  threshold = 100
): Promise<T> {
  const meta = response._meta;
  if (!meta?.block?.number) {
    throw new SubgraphLagError({
      subgraph_block: -1,
      forno_head: -1,
      lag: -1,
      threshold,
    });
  }
  const head = Number(await forno.getBlockNumber());
  const lag = head - meta.block.number;
  if (lag > threshold) {
    throw new SubgraphLagError({
      subgraph_block: meta.block.number,
      forno_head: head,
      lag,
      threshold,
    });
  }
  return response;
}
