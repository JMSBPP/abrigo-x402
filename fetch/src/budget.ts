// fetch/src/budget.ts — Plan 01-06 / FETCH-02 SC-6 dry-run budget estimator.
//
// Pure function: spec + Forno head -> BudgetEstimate JSON. NO network calls,
// NO disk I/O. The CLI (`fetch/src/cli.ts`) is the sole consumer; tests
// exercise this module directly with fixtures + the synthetic 50-vault spec.
//
// Per RESEARCH §M cold-backfill budget dry-run algorithm:
//   blocks_per_vault       = max(0, fornoHead - cold_backfill_from_block)
//   subgraph_queries/vault = ceil(blocks_per_vault / 10_000)
//   blockscout_queries/vault = ceil(observed_swaps_30d / 1_000)
//   total_queries          = vault_count * (subgraph + blockscout) / vault
//
// The 30k earmark is the cold-backfill envelope (CONTEXT.md cold-backfill
// envelope 30k+15k+45k). exceeds_earmark counts ONLY the subgraph (graph)
// queries against the cap (per FETCH-02 the 90k/mo cap is graph-mainnet
// rows only; the 30k earmark is the cold-backfill subset of that 90k).
// Blockscout queries are uncapped (per cost-ledger schema).
//
// recommended_reallocation MUST mention both "reserve" (the 45k reserve
// referenced in CONTEXT.md) and "force" (the CLI --force flag) so the
// human operator knows the two operational levers when the gate fires.

import type { ProtocolSpec } from './protocol-spec.js';

export interface BudgetEstimate {
  protocol: string;
  iteration: number;
  vault_count: number;
  blocks_per_vault: number;
  queries_per_vault: number;
  total_queries: number;
  exceeds_earmark: boolean;
  earmark: number;
  recommended_reallocation: string | null;
}

/**
 * Estimate the cold-backfill query budget for a protocol spec at a given
 * Forno head. Pure function (no I/O). The dry-run path NEVER calls Forno
 * directly — the head is resolved by the CLI layer (env override > snapshot
 * > fallback constant > live).
 *
 * @param spec     ProtocolSpec loaded via loadProtocol() — schema-validated.
 * @param fornoHead Celo head block number (integer).
 * @param earmark  Cold-backfill earmark cap. Defaults to 30_000 per CONTEXT.md.
 * @returns BudgetEstimate — JSON-serializable, key order alphabetic-stable.
 */
export function estimateBudget(
  spec: ProtocolSpec,
  fornoHead: number,
  earmark = 30_000,
): BudgetEstimate {
  const activeVaults = Object.entries(spec.vaults).filter(([, v]) => v.active);
  const vault_count = activeVaults.length;

  // cold_backfill_from_block is required per FETCH-02 / per-protocol field.
  // Plan 01-01 added this field to protocols/ichi.toml. The schema marks it
  // optional only because [protocol.vaults] enumeration may precede setting
  // the floor; the CLI dry-run path requires it.
  const fromBlock = spec.cold_backfill_from_block ?? 65_000_000;
  const blocks_per_vault = Math.max(0, fornoHead - fromBlock);

  const subgraph_queries_per_vault = Math.ceil(blocks_per_vault / 10_000);
  const observed_swaps_30d = spec.anchor_pool.swaps_per_30d_observed ?? 4_400;
  const blockscout_queries_per_vault = Math.ceil(observed_swaps_30d / 1_000);
  const queries_per_vault =
    subgraph_queries_per_vault + blockscout_queries_per_vault;

  const total_queries = vault_count * queries_per_vault;

  // exceeds_earmark gates the GRAPH leg only (per FETCH-02: blockscout uncapped).
  const graph_total = vault_count * subgraph_queries_per_vault;
  const exceeds_earmark = graph_total > earmark;

  return {
    protocol: spec.name,
    iteration: spec.iteration,
    vault_count,
    blocks_per_vault,
    queries_per_vault,
    total_queries,
    exceeds_earmark,
    earmark,
    recommended_reallocation: exceeds_earmark
      ? `Projected graph queries (${graph_total}) exceeds ${earmark} earmark. Options: (a) re-scope vault set, (b) reallocate from the 45k reserve, (c) pass --force to bypass at the budget gate.`
      : null,
  };
}
