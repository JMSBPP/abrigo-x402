// fetch/src/cost-ledger.ts
// Plan 01-02 — append-only JSONL cost-ledger + 90k/mo Graph budget gate.
//
// FETCH-02 load-bearing free-tier discipline gate:
//   - Every paid fetch in Phase 2+ MUST call checkBudget() before issuing,
//     and call appendLedger() after the response lands.
//   - The 90k/mo soft cap counts only endpoint='graph-mainnet' rows in the
//     current UTC month. Blockscout / Forno / x402-mock-sepolia / graph-sepolia
//     rows are logged but UNCAPPED (CONTEXT.md cost-ledger schema §FETCH-02).
//   - --force override (passed through checkBudget opts) returns
//     would_exceed=true without throwing, so the CLI can decide what to do
//     when budget is intentionally being burned.
//
// JSONL pivot per orchestrator finding #5 (RESEARCH.md §J fallback): one
// JSON object per line, written via fs.appendFile. POSIX guarantees writes
// shorter than PIPE_BUF (typically 4096B) are atomic, so concurrent writers
// don't interleave. Phase 2 / Phase 5 may batch-convert to Parquet via polars
// if the ledger grows past JSONL's comfortable scale (~10M rows).

import { appendFile, readFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname } from 'node:path';
import { z } from 'zod';

// ---------------------------------------------------------------------------
// Schema
// ---------------------------------------------------------------------------

export const EndpointEnum = z.enum([
  'graph-mainnet',
  'graph-sepolia',
  'blockscout',
  'forno',
  'x402-mock-sepolia',
]);
export type Endpoint = z.infer<typeof EndpointEnum>;

export const ChainEnum = z.enum(['celo', 'base-sepolia']);
export type Chain = z.infer<typeof ChainEnum>;

export const CostLedgerRowSchema = z.object({
  // ISO-8601 UTC. The regex anchors on the date prefix; full RFC-3339 validation
  // happens implicitly because Date(timestamp).toISOString() is the only producer.
  timestamp: z.string().regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/),
  endpoint: EndpointEnum,
  query_id: z.string(),
  // Decimal string. Stored as string (not number) to preserve precision across
  // language boundaries (Python polars / Node) and to avoid float-rounding in
  // downstream demand-window analytics.
  cost_usdc: z.string().regex(/^\d+(\.\d+)?$/),
  paid_real: z.boolean(),
  tx_hash: z.string().nullable(),
  chain: ChainEnum.nullable(),
  response_bytes: z.number().int().nonnegative(),
  // 64-char lowercase hex (sha256 of the raw response body).
  response_sha256: z.string().regex(/^[0-9a-f]{64}$/),
  fetch_id: z.string(),
});
export type CostLedgerRow = z.infer<typeof CostLedgerRowSchema>;

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DEFAULT_LEDGER = 'data/raw/_cost_ledger.jsonl';
const DEFAULT_GRAPH_CAP = 90_000;

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

export class GraphBudgetExceededError extends Error {
  constructor(
    public details: {
      current: number;
      projected: number;
      cap: number;
      force: boolean;
    },
  ) {
    super(
      `Graph budget cap exceeded: current=${details.current} + projected=${details.projected} > cap=${details.cap}. Pass --force to bypass.`,
    );
    this.name = 'GraphBudgetExceededError';
  }
}

// ---------------------------------------------------------------------------
// Append / Read
// ---------------------------------------------------------------------------

export async function appendLedger(
  row: CostLedgerRow,
  path: string = DEFAULT_LEDGER,
): Promise<void> {
  // Zod throws on invalid; the throw is part of the contract (test 3 in 01-02).
  CostLedgerRowSchema.parse(row);

  const parent = dirname(path);
  if (!existsSync(parent)) {
    await mkdir(parent, { recursive: true });
  }

  // fs.appendFile is atomic per POSIX when the payload is shorter than PIPE_BUF.
  // A single ledger row JSON-encoded is well under 4KB (response_sha256 + tx_hash
  // dominate, both <= ~140 chars total), so concurrent writers do not interleave.
  await appendFile(path, JSON.stringify(row) + '\n', 'utf-8');
}

export async function readLedger(
  path: string = DEFAULT_LEDGER,
): Promise<CostLedgerRow[]> {
  if (!existsSync(path)) return [];
  const text = await readFile(path, 'utf-8');
  return text
    .split('\n')
    .filter((line) => line.trim().length > 0)
    .map((line) => CostLedgerRowSchema.parse(JSON.parse(line)));
}

// ---------------------------------------------------------------------------
// Budget gate (Task 2 in 01-02; lands in this same file via the second commit)
// ---------------------------------------------------------------------------

export interface CheckBudgetOpts {
  projected_graph_queries: number;
  force?: boolean;
  ledger_path?: string;
  cap?: number;
}

export interface CheckBudgetResult {
  current: number;
  projected: number;
  cap: number;
  would_exceed: boolean;
}

export async function checkBudget(
  opts: CheckBudgetOpts,
): Promise<CheckBudgetResult> {
  const {
    projected_graph_queries,
    force = false,
    ledger_path = DEFAULT_LEDGER,
    cap = DEFAULT_GRAPH_CAP,
  } = opts;

  // Start of the current UTC month — explicit Date.UTC construction per
  // checker M12. Using `new Date().setUTCMonth(-1)` on January 15th would
  // yield "December 15 same year" unless adjusted; Date.UTC(y, m-1, 1)
  // lets JS normalize month underflow correctly.
  const now = new Date();
  const monthStart = new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1),
  ).toISOString();

  const rows = await readLedger(ledger_path);
  const current = rows.filter(
    (r) => r.endpoint === 'graph-mainnet' && r.timestamp >= monthStart,
  ).length;

  const would_exceed = current + projected_graph_queries > cap;
  if (would_exceed && !force) {
    throw new GraphBudgetExceededError({
      current,
      projected: projected_graph_queries,
      cap,
      force,
    });
  }

  return {
    current,
    projected: projected_graph_queries,
    cap,
    would_exceed,
  };
}
