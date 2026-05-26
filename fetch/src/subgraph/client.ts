// fetch/src/subgraph/client.ts
// Dormant-by-default Graph subgraph client (orchestrator finding #2,
// RESEARCH §A subgraph hunt verdict — DOWNGRADE to Blockscout-only as
// Phase-1 default).
//
// The client EXISTS so Plan 01-06 + Phase 1.5 enrichment can wire it without
// reshaping the import graph; it THROWS MissingGraphApiKeyError on every call
// path that lacks process.env.GRAPH_API_KEY. Phase 1 Plan 01-06 does NOT call
// this module; Phase 1.5 wiring will set GRAPH_API_KEY and uncap it.
//
// CRITICAL (checker I8): process.env.GRAPH_API_KEY is read INSIDE the function
// body, NOT captured at module-load time. This lets vi.stubEnv tests work
// with the natural static-import pattern (no dynamic import dance needed).
// If you refactor to top-level capture, the test suite WILL silently fail
// to flip the env between cases.
//
// Owned by Plan 01-05. Consumer: Phase 1.5 enrichment + Plan 01-06 (will
// guard call sites with the env check; in Phase 1 the call sites are absent).

import { GraphQLClient } from 'graphql-request';

export class MissingGraphApiKeyError extends Error {
  constructor(msg?: string) {
    super(
      msg ??
        'GRAPH_API_KEY env var is unset — subgraph leg disabled. Phase 1 default is Blockscout-only per RESEARCH §A.',
    );
    this.name = 'MissingGraphApiKeyError';
  }
}

/**
 * Return a GraphQLClient pointed at The Graph's decentralized-network
 * gateway for the given deployment id. The deployment id is the long
 * Qm... hash that the Subgraph Studio publishes; Plan 01-06 will source
 * it from `protocols/ichi.toml [subgraphs.uniswap_v3] deployment_id`
 * once Phase 1.5 wires that block in (the block is intentionally absent
 * from ichi.toml at Phase 1 — RESEARCH §A downgrade verdict).
 *
 * Throws MissingGraphApiKeyError if process.env.GRAPH_API_KEY is unset
 * or empty. Reads the env at CALL TIME (NOT module-load time) — see
 * file header for the rationale.
 */
export function getSubgraphClient(deploymentId: string): GraphQLClient {
  const apiKey = process.env.GRAPH_API_KEY;
  if (apiKey === undefined || apiKey === '') {
    throw new MissingGraphApiKeyError();
  }
  const url = `https://gateway.thegraph.com/api/${apiKey}/subgraphs/id/${deploymentId}`;
  return new GraphQLClient(url);
}
