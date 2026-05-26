// fetch/tests/cost-ledger.test.ts
// Plan 01-02 — append-only JSONL cost-ledger + 90k/mo Graph budget gate (FETCH-02).
//
// JSONL pivot per orchestrator finding #5 (see 01-RESEARCH.md §J fallback):
// fs.appendFile of one line at a time is atomic per POSIX (PIPE_BUF guarantees
// <4096-byte writes are not interleaved); hyparquet-writer's small-write profile
// adds binary-format risk without empirical benefit at Phase-1 volumes.

import { describe, test, expect, beforeEach } from 'vitest';
import { rm } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import {
  appendLedger,
  readLedger,
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
