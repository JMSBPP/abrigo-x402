// fetch/tests/cost-ledger.test.ts
// Plan 01-02 — append-only JSONL cost-ledger + 90k/mo Graph budget gate (FETCH-02).
//
// JSONL pivot per orchestrator finding #5 (see 01-RESEARCH.md §J fallback):
// fs.appendFile of one line at a time is atomic per POSIX (PIPE_BUF guarantees
// <4096-byte writes are not interleaved); hyparquet-writer's small-write profile
// adds binary-format risk without empirical benefit at Phase-1 volumes.

import { describe, test, expect, beforeEach } from 'vitest';
import { rm, mkdir, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import {
  appendLedger,
  readLedger,
  checkBudget,
  GraphBudgetExceededError,
  type CostLedgerRow,
} from '../src/cost-ledger';

const TEST_LEDGER = 'data/raw/_cost_ledger.test.jsonl';

const validRow: CostLedgerRow = {
  timestamp: '2026-05-25T12:00:00.000Z',
  endpoint: 'blockscout',
  query_id: 'q1',
  cost_usdc: '0.000',
  paid_real: false,
  tx_hash: null,
  chain: 'celo',
  response_bytes: 12345,
  response_sha256: 'a'.repeat(64),
  fetch_id: 'fid1',
};

describe('cost-ledger append/read', () => {
  beforeEach(async () => {
    if (existsSync(TEST_LEDGER)) await rm(TEST_LEDGER);
  });

  test('appends one row and reads it back', async () => {
    await appendLedger(validRow, TEST_LEDGER);
    const rows = await readLedger(TEST_LEDGER);
    expect(rows.length).toBe(1);
    expect(rows[0]?.endpoint).toBe('blockscout');
    expect(rows[0]?.query_id).toBe('q1');
    expect(rows[0]?.response_bytes).toBe(12345);
  });

  test('appends three rows preserving append order', async () => {
    for (const i of [1, 2, 3]) {
      await appendLedger({ ...validRow, query_id: `q${i}` }, TEST_LEDGER);
    }
    const rows = await readLedger(TEST_LEDGER);
    expect(rows.map((r) => r.query_id)).toEqual(['q1', 'q2', 'q3']);
  });

  test('rejects invalid endpoint via zod', async () => {
    await expect(
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      appendLedger({ ...validRow, endpoint: 'unknown' as any }, TEST_LEDGER),
    ).rejects.toThrow();
  });

  test('readLedger on missing file returns empty array', async () => {
    const rows = await readLedger('data/raw/_cost_ledger.nonexistent.jsonl');
    expect(rows).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// Task 2 — 90k Graph-mainnet budget gate
// ---------------------------------------------------------------------------

const TEST_LEDGER_BUDGET = 'data/raw/_cost_ledger.budget-test.jsonl';

/**
 * Synthesize a graph-mainnet row at the given monthOffset relative to now.
 * Explicit Date.UTC construction handles January rollover correctly (M12):
 * setUTCMonth(getUTCMonth() - 1) on January 15th would yield "December 15
 * same year" unless year is adjusted manually; Date.UTC(y, m + offset, d)
 * lets JS normalize month underflow / overflow automatically.
 */
const graphRow = (i: number, monthOffset = 0): CostLedgerRow => {
  const now = new Date();
  const d = new Date(
    Date.UTC(
      now.getUTCFullYear(),
      now.getUTCMonth() + monthOffset,
      // Clamp to day 15 to avoid month-boundary edge cases (e.g., May 31
      // + monthOffset=-1 becoming "April 31" → normalizes to May 1, which
      // would land BACK in the current month and break the "last month"
      // semantic the test is asserting).
      15,
      now.getUTCHours(),
      now.getUTCMinutes(),
      now.getUTCSeconds(),
      now.getUTCMilliseconds(),
    ),
  );
  return {
    timestamp: d.toISOString(),
    endpoint: 'graph-mainnet',
    query_id: `gq${i}`,
    cost_usdc: '0.0001',
    paid_real: false,
    tx_hash: null,
    chain: null,
    response_bytes: 512,
    response_sha256: 'b'.repeat(64),
    fetch_id: 'fid-graph',
  };
};

describe('cost-ledger: 90k Graph-mainnet budget gate', () => {
  beforeEach(async () => {
    if (existsSync(TEST_LEDGER_BUDGET)) await rm(TEST_LEDGER_BUDGET);
  });

  test('empty ledger: projection of 5000 passes (current=0)', async () => {
    const r = await checkBudget({
      projected_graph_queries: 5000,
      ledger_path: TEST_LEDGER_BUDGET,
    });
    expect(r.current).toBe(0);
    expect(r.projected).toBe(5000);
    expect(r.cap).toBe(90_000);
    expect(r.would_exceed).toBe(false);
  });

  test('current=85k graph-mainnet + projected=6k throws GraphBudgetExceededError', async () => {
    // Seed 85k synthetic graph-mainnet rows directly (faster than 85k
    // appendLedger calls; the test asserts the read+filter+sum path, not
    // append path correctness — that is covered by the append/read suite).
    await mkdir('data/raw', { recursive: true });
    const rows =
      Array.from({ length: 85_000 }, (_, i) => JSON.stringify(graphRow(i))).join(
        '\n',
      ) + '\n';
    await writeFile(TEST_LEDGER_BUDGET, rows);

    await expect(
      checkBudget({
        projected_graph_queries: 6000,
        ledger_path: TEST_LEDGER_BUDGET,
      }),
    ).rejects.toBeInstanceOf(GraphBudgetExceededError);
  });

  test('force=true bypasses the gate and returns would_exceed=true', async () => {
    await mkdir('data/raw', { recursive: true });
    const rows =
      Array.from({ length: 85_000 }, (_, i) => JSON.stringify(graphRow(i))).join(
        '\n',
      ) + '\n';
    await writeFile(TEST_LEDGER_BUDGET, rows);

    const r = await checkBudget({
      projected_graph_queries: 6000,
      force: true,
      ledger_path: TEST_LEDGER_BUDGET,
    });
    expect(r.would_exceed).toBe(true);
    expect(r.current).toBe(85_000);
    expect(r.projected).toBe(6000);
  });

  test('blockscout rows do NOT count against the cap (endpoint-specific)', async () => {
    await mkdir('data/raw', { recursive: true });
    // 85k blockscout rows — would exceed if the cap counted all endpoints.
    const bs = (i: number): CostLedgerRow => ({
      ...graphRow(i),
      endpoint: 'blockscout',
    });
    const rows =
      Array.from({ length: 85_000 }, (_, i) => JSON.stringify(bs(i))).join(
        '\n',
      ) + '\n';
    await writeFile(TEST_LEDGER_BUDGET, rows);

    const r = await checkBudget({
      projected_graph_queries: 50_000,
      ledger_path: TEST_LEDGER_BUDGET,
    });
    expect(r.current).toBe(0); // 0 graph-mainnet rows in scope
    expect(r.would_exceed).toBe(false);
  });

  test('last-month graph-mainnet rows do NOT count toward this month', async () => {
    // 50k graph-mainnet rows dated 1 month ago. Current month projection of
    // 50k should pass (current=0 since last-month rows are out of scope).
    await mkdir('data/raw', { recursive: true });
    const rows =
      Array.from({ length: 50_000 }, (_, i) =>
        JSON.stringify(graphRow(i, -1)),
      ).join('\n') + '\n';
    await writeFile(TEST_LEDGER_BUDGET, rows);

    const r = await checkBudget({
      projected_graph_queries: 50_000,
      ledger_path: TEST_LEDGER_BUDGET,
    });
    expect(r.current).toBe(0);
    expect(r.would_exceed).toBe(false);
  });
});
