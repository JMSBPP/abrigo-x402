// fetch/tests/x402_mock.test.ts — Plan 01-07 Task 2.
// Self-hosted x402 mock round-trip on Base Sepolia (HEADER-ONLY mode default).
//
// Test contract per Plan 01-07:
//   (1) bare 402 emits PaymentRequirements
//   (2) wrapFetchWithPayment round-trip succeeds with 32-byte tx hash
//   (3) bad network rejected with errorReason
// + cost-ledger row written with endpoint='x402-mock-sepolia',
//   paid_real=false, chain='base-sepolia'.
//
// STACK DRIFT (cf. server.ts comment block): network is `base-sepolia`
// (named) not `eip155:84532` (CAIP-2) because @x402/evm v2.13 v1-protocol
// schemes register on named networks.

import { describe, test, expect, beforeAll, afterAll } from 'vitest';
import type { Server } from 'node:http';
import { rm } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { startMockServer } from '../src/x402-mock/server';
import { makeFetchWithPayment } from '../src/x402-mock/client-bridge';
import {
  appendLedger,
  readLedger,
  type CostLedgerRow,
} from '../src/cost-ledger';

const TEST_LEDGER = 'data/raw/_cost_ledger.x402-test.jsonl';

let server: Server;
let port: number;

beforeAll(async () => {
  ({ server, port } = await startMockServer(0));
  if (existsSync(TEST_LEDGER)) await rm(TEST_LEDGER);
});

afterAll(
  () => new Promise<void>((resolve) => server.close(() => resolve())),
);

describe('x402 mock round-trip (FETCH-02 x402 plumbing)', () => {
  test('GET /mock/weather without X-PAYMENT returns 402 with PaymentRequirements', async () => {
    const res = await fetch(`http://localhost:${port}/mock/weather`);
    expect(res.status).toBe(402);
    const body = await res.json();
    expect(body.x402Version).toBe(1);
    // STACK DRIFT: named 'base-sepolia' replaces CAIP-2 'eip155:84532'.
    expect(body.accepts[0].network).toBe('base-sepolia');
    expect(body.accepts[0].asset).toBe(
      '0x036cbd53842c5426634e7929541ec2318f3dcf7e',
    );
    // EIP-712 domain — load-bearing for ExactEvmScheme.createPaymentPayload.
    expect(body.accepts[0].extra).toEqual({ name: 'USDC', version: '2' });
  });

  test('round-trip: 402 -> sign -> retry -> 200 + X-PAYMENT-RESPONSE carries tx hash', async () => {
    const wrapped = makeFetchWithPayment();
    const res = await wrapped(`http://localhost:${port}/mock/weather`);
    expect(res.status).toBe(200);

    const settleHeader = res.headers.get('x-payment-response');
    expect(settleHeader).toBeTruthy();
    const settle = JSON.parse(
      Buffer.from(settleHeader!, 'base64').toString(),
    );
    expect(settle.success).toBe(true);
    expect(settle.transaction).toMatch(/^0x[0-9a-f]{64}$/);
    expect(settle.network).toBe('base-sepolia');
    expect(settle.payer).toMatch(/^0x[0-9a-fA-F]{40}$/);

    // Append a ledger row exercising the x402-mock-sepolia endpoint
    const responseBody = await res.text();
    const responseHash = createHash('sha256')
      .update(responseBody)
      .digest('hex');
    const row: CostLedgerRow = {
      timestamp: '2026-05-25T12:00:00.000Z',
      endpoint: 'x402-mock-sepolia',
      query_id: 'mock-' + settle.transaction.slice(0, 12),
      cost_usdc: '0.001',
      paid_real: false,
      tx_hash: settle.transaction,
      chain: 'base-sepolia',
      response_bytes: responseBody.length,
      response_sha256: responseHash,
      fetch_id: 'mock-test',
    };
    await appendLedger(row, TEST_LEDGER);
    const rows = await readLedger(TEST_LEDGER);
    expect(rows.length).toBe(1);
    expect(rows[0].endpoint).toBe('x402-mock-sepolia');
    expect(rows[0].chain).toBe('base-sepolia');
    expect(rows[0].paid_real).toBe(false);
  });

  test('malformed X-PAYMENT (wrong network) returns 402 with errorReason', async () => {
    // Submit a structurally-valid envelope but on the wrong named network.
    // 'ethereum' is a registered v1 named network so the mock parses
    // structurally — and rejects on network mismatch (not parse failure).
    const badPayload = Buffer.from(
      JSON.stringify({
        scheme: 'exact',
        network: 'ethereum',
        payload: {
          signature: '0x' + 'a'.repeat(130),
          authorization: { from: '0x' + 'b'.repeat(40) },
        },
      }),
    ).toString('base64');
    const res = await fetch(`http://localhost:${port}/mock/weather`, {
      headers: { 'X-PAYMENT': badPayload },
    });
    expect(res.status).toBe(402);
    const settleHeader = res.headers.get('x-payment-response');
    expect(settleHeader).toBeTruthy();
    const settle = JSON.parse(
      Buffer.from(settleHeader!, 'base64').toString(),
    );
    expect(settle.success).toBe(false);
    expect(settle.errorReason).toContain('network');
  });
});
