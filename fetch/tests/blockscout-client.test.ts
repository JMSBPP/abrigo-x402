// fetch/tests/blockscout-client.test.ts
// Plan 01-05 Task 1: Blockscout v1 etherscan-compat getLogs client + Swap decoder
// unit tests. Uses a captured fixture (tests/fixtures/blockscout-v1-getlogs-cKES-USDT.json)
// instead of live HTTP — CI must not depend on network.
//
// Endpoint correctness: per RESEARCH §C, Blockscout v2 /api/v2/addresses/<addr>/logs
// REJECTS topic0 with HTTP 422. Only v1 etherscan-compat
// /api?module=logs&action=getLogs accepts topic0 + fromBlock/toBlock together. Test 1
// pins the v1 URL shape so future refactors cannot silently regress to v2.

import { describe, test, expect, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { getLogsV1 } from '../src/blockscout/v1-getlogs.js';
import {
  UniswapV3SwapTopic0,
  decodeSwap,
} from '../src/decoders/uniswap-v3-swap.js';
import { testDirname } from './_helpers.js';

const __dirname = testDirname(import.meta.url);
const fixturePath = join(
  __dirname,
  'fixtures',
  'blockscout-v1-getlogs-cKES-USDT.json',
);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const fixture: any = JSON.parse(readFileSync(fixturePath, 'utf-8'));

// Build a fetch mock that returns a sequence of JSON responses (one per call).
// Casts to `unknown as typeof fetch` because we only stub the surface getLogsV1
// uses (ok + json()).
function makeMockFetch(responses: unknown[]): typeof fetch {
  let i = 0;
  const fn = vi.fn(async () => {
    const body = responses[Math.min(i, responses.length - 1)];
    i++;
    return {
      ok: true,
      status: 200,
      json: async () => body,
    };
  });
  return fn as unknown as typeof fetch;
}

describe('getLogsV1 — Blockscout v1 etherscan-compat client', () => {
  test('builds correct etherscan-compat URL (module=logs&action=getLogs, NOT v2)', async () => {
    const mock = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => fixture,
    }));
    await getLogsV1({
      baseUrl: 'https://celo.blockscout.com',
      address: '0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F',
      fromBlock: 67_500_000,
      toBlock: 67_830_000,
      topic0: UniswapV3SwapTopic0,
      fetcher: mock as unknown as typeof fetch,
    });
    expect(mock).toHaveBeenCalledTimes(1);
    const calledUrl = mock.mock.calls[0]?.[0] as string;
    expect(calledUrl).toContain('/api?');
    expect(calledUrl).toContain('module=logs');
    expect(calledUrl).toContain('action=getLogs');
    expect(calledUrl).toContain(
      'address=0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F',
    );
    expect(calledUrl).toContain('fromBlock=67500000');
    expect(calledUrl).toContain('toBlock=67830000');
    expect(calledUrl).toContain(
      'topic0=0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67',
    );
    // v2 path must NOT appear — that endpoint rejects topic0 (RESEARCH §C).
    expect(calledUrl).not.toContain('/api/v2/');
  });

  test('parses fixture response into typed log array', async () => {
    const mock = makeMockFetch([fixture]);
    const logs = await getLogsV1({
      baseUrl: 'https://celo.blockscout.com',
      address: fixture.result[0].address,
      fromBlock: 67_500_000,
      toBlock: 67_830_000,
      topic0: UniswapV3SwapTopic0,
      fetcher: mock,
    });
    expect(logs.length).toBe(fixture.result.length);
    expect(logs[0]?.blockNumber).toMatch(/^0x[0-9a-f]+$/);
    expect(logs[0]?.topics[0]).toBe(UniswapV3SwapTopic0);
  });

  test('appends apikey query param when provided', async () => {
    const mock = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => fixture,
    }));
    await getLogsV1({
      baseUrl: 'https://celo.blockscout.com',
      address: fixture.result[0].address,
      fromBlock: 0,
      toBlock: 1_000,
      topic0: UniswapV3SwapTopic0,
      apiKey: 'free-tier-key-abc',
      fetcher: mock as unknown as typeof fetch,
    });
    const calledUrl = mock.mock.calls[0]?.[0] as string;
    expect(calledUrl).toContain('apikey=free-tier-key-abc');
  });

  test('auto-paginates: 1000-log page triggers a second request with fromBlock = lastBlock + 1', async () => {
    // Build a synthetic page-1 with exactly 1000 logs at blockNumber 0x4061986.
    const oneLog = fixture.result[0];
    const page1 = {
      status: '1',
      message: 'OK',
      result: Array.from({ length: 1000 }, (_, idx) => ({
        ...oneLog,
        logIndex: `0x${idx.toString(16)}`,
      })),
    };
    // Page-2 must show .length < 1000 to terminate the loop.
    const page2 = { status: '1', message: 'OK', result: [oneLog] };
    const mock = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => null,
    }));
    let call = 0;
    mock.mockImplementation(async () => {
      const body = call === 0 ? page1 : page2;
      call++;
      return { ok: true, status: 200, json: async () => body };
    });

    const logs = await getLogsV1({
      baseUrl: 'https://celo.blockscout.com',
      address: oneLog.address,
      fromBlock: 67_000_000,
      toBlock: 67_830_000,
      topic0: UniswapV3SwapTopic0,
      fetcher: mock as unknown as typeof fetch,
    });
    expect(mock).toHaveBeenCalledTimes(2);
    expect(logs.length).toBe(1001);
    const secondCallUrl = mock.mock.calls[1]?.[0] as string;
    // lastBlock = 0x4061986 = 67_502_982; cursor should become 67_502_983.
    expect(secondCallUrl).toContain('fromBlock=67502983');
  });

  test('throws on status != 1 with non-empty result (real error)', async () => {
    const bad = {
      status: '0',
      message: 'Daily limit exceeded',
      result: [{ ...fixture.result[0] }],
    };
    const mock = makeMockFetch([bad]);
    await expect(
      getLogsV1({
        baseUrl: 'https://celo.blockscout.com',
        address: '0x0000000000000000000000000000000000000000',
        fromBlock: 0,
        toBlock: 0,
        topic0: UniswapV3SwapTopic0,
        fetcher: mock,
      }),
    ).rejects.toThrow(/Blockscout v1 status/);
  });

  test('treats "No records found" with empty result as empty success (returns [])', async () => {
    const empty = { status: '0', message: 'No records found', result: [] };
    const mock = makeMockFetch([empty]);
    const logs = await getLogsV1({
      baseUrl: 'https://celo.blockscout.com',
      address: '0x0000000000000000000000000000000000000000',
      fromBlock: 0,
      toBlock: 0,
      topic0: UniswapV3SwapTopic0,
      fetcher: mock,
    });
    expect(logs).toEqual([]);
  });

  test('throws when HTTP response is not ok', async () => {
    const mock = vi.fn(async () => ({
      ok: false,
      status: 500,
      json: async () => ({}),
    }));
    await expect(
      getLogsV1({
        baseUrl: 'https://celo.blockscout.com',
        address: '0x0000000000000000000000000000000000000000',
        fromBlock: 0,
        toBlock: 0,
        topic0: UniswapV3SwapTopic0,
        fetcher: mock as unknown as typeof fetch,
      }),
    ).rejects.toThrow(/HTTP 500/);
  });
});

describe('Uniswap V3 Swap decoder', () => {
  test('UniswapV3SwapTopic0 constant exactly equals the verified keccak256(Swap signature)', () => {
    expect(UniswapV3SwapTopic0).toBe(
      '0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67',
    );
  });

  test('decodeSwap returns typed Swap args (sender, recipient, amount0, amount1, tick)', () => {
    // Synthetic but ABI-valid payload: viem decodeEventLog accepts the indexed
    // address topics + 5*32-byte data field. Values:
    //   amount0      = 100        (int256)
    //   amount1      = -100       (int256, two's complement)
    //   sqrtPriceX96 = 1_000_000  (uint160)
    //   liquidity    = 50_000     (uint128)
    //   tick         = 4000       (int24)
    const topics = [
      UniswapV3SwapTopic0,
      // sender   indexed address — left-padded to 32 bytes
      '0x000000000000000000000000aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
      // recipient indexed address
      '0x000000000000000000000000bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
    ] as readonly `0x${string}`[];
    const data =
      // amount0 = 100
      '0x' +
      '0000000000000000000000000000000000000000000000000000000000000064' +
      // amount1 = -100 (two's complement of 100)
      'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff9c' +
      // sqrtPriceX96 = 1_000_000 (0x0f4240)
      '00000000000000000000000000000000000000000000000000000000000f4240' +
      // liquidity = 50_000 (0xc350)
      '000000000000000000000000000000000000000000000000000000000000c350' +
      // tick = 4000 (0xfa0)
      '0000000000000000000000000000000000000000000000000000000000000fa0';

    const decoded = decodeSwap(topics, data as `0x${string}`);
    expect(decoded.eventName).toBe('Swap');
    // sender / recipient are 0x-prefixed 20-byte addresses (viem returns checksummed).
    expect(decoded.args.sender.toLowerCase()).toBe(
      '0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    );
    expect(decoded.args.recipient.toLowerCase()).toBe(
      '0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
    );
    expect(decoded.args.amount0).toBe(100n);
    expect(decoded.args.amount1).toBe(-100n);
    expect(decoded.args.sqrtPriceX96).toBe(1_000_000n);
    expect(decoded.args.liquidity).toBe(50_000n);
    expect(decoded.args.tick).toBe(4000);
  });
});
