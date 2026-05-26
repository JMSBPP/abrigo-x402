import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { readFileSync, existsSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import {
  snapVaultState,
  VAULT_ADDRESSES,
  MULTICALL3_CELO,
  VAULT_ABI,
} from '../src/vault/state-snap.js';

const VAULT = VAULT_ADDRESSES.cKES_USDT_anchor;

function makeMockClient(callTracker: any[]) {
  return {
    multicall: vi.fn(async (args: any) => {
      callTracker.push(args);
      return [
        // getTotalAmounts -> (uint256, uint256)
        {
          status: 'success',
          result: [1_000_000_000_000_000_000n, 2_000_000_000_000_000_000n],
        },
        // totalSupply -> uint256
        { status: 'success', result: 5_000_000_000_000_000_000n },
        // currentTick -> int24
        { status: 'success', result: 12345 },
        // baseLower -> int24
        { status: 'success', result: 10000 },
        // baseUpper -> int24
        { status: 'success', result: 20000 },
      ];
    }),
  } as any;
}

const TMP = join(tmpdir(), `vault_state_test_${process.pid}.jsonl`);

beforeEach(() => {
  if (existsSync(TMP)) rmSync(TMP);
});
afterEach(() => {
  if (existsSync(TMP)) rmSync(TMP);
});

describe('snapVaultState', () => {
  it('returns one row per requested block', async () => {
    const calls: any[] = [];
    const rows = await snapVaultState({
      vaultAddress: VAULT,
      blocks: [100, 200],
      outputPath: TMP,
      client: makeMockClient(calls),
    });
    expect(rows.length).toBe(2);
    expect(rows[0].blockNumber).toBe(100);
    expect(rows[1].blockNumber).toBe(200);
  });

  it('threads blockNumber per multicall batch (Pitfall 3)', async () => {
    const calls: any[] = [];
    await snapVaultState({
      vaultAddress: VAULT,
      blocks: [100, 200],
      outputPath: TMP,
      client: makeMockClient(calls),
    });
    expect(calls.length).toBe(2);
    expect(calls[0].blockNumber).toBe(100n);
    expect(calls[1].blockNumber).toBe(200n);
    expect(String(calls[0].multicallAddress).toLowerCase()).toBe(
      MULTICALL3_CELO.toLowerCase(),
    );
    expect(calls[0].allowFailure).toBe(true);
  });

  it('deduplicates blocks (per-block memoization)', async () => {
    const calls: any[] = [];
    await snapVaultState({
      vaultAddress: VAULT,
      blocks: [100, 100, 200, 200, 200],
      outputPath: TMP,
      client: makeMockClient(calls),
    });
    expect(calls.length).toBe(2);
  });

  it('writes JSONL sidecar with one line per block', async () => {
    const calls: any[] = [];
    await snapVaultState({
      vaultAddress: VAULT,
      blocks: [100, 200],
      outputPath: TMP,
      client: makeMockClient(calls),
    });
    const lines = readFileSync(TMP, 'utf-8').trim().split('\n');
    expect(lines.length).toBe(2);
    const row = JSON.parse(lines[0]);
    expect(row.blockNumber).toBe(100);
    expect(row.totalAmounts_0).toBe('1000000000000000000');
    expect(row.totalAmounts_1).toBe('2000000000000000000');
    expect(row.totalSupply).toBe('5000000000000000000');
    expect(row.currentTick).toBe(12345);
    expect(row.lowerTick).toBe(10000);
    expect(row.upperTick).toBe(20000);
  });

  it('handles per-call failure with null fields (allowFailure semantics)', async () => {
    const client = {
      multicall: vi.fn(async () => [
        { status: 'success', result: [1n, 2n] },
        { status: 'failure', error: new Error('reverted') },
        { status: 'success', result: 100 },
        { status: 'success', result: 0 },
        { status: 'success', result: 0 },
      ]),
    } as any;
    const rows = await snapVaultState({
      vaultAddress: VAULT,
      blocks: [100],
      outputPath: TMP,
      client,
    });
    expect(rows[0].totalSupply).toBeNull();
    expect(rows[0].currentTick).toBe(100);
    expect(rows[0].totalAmounts_0).toBe('1');
  });

  it('uses VAULT_ABI canonical function names in multicall contracts', async () => {
    const calls: any[] = [];
    await snapVaultState({
      vaultAddress: VAULT,
      blocks: [100],
      outputPath: TMP,
      client: makeMockClient(calls),
    });
    const fnNames = calls[0].contracts.map((c: any) => c.functionName);
    expect(fnNames).toEqual([
      'getTotalAmounts',
      'totalSupply',
      'currentTick',
      'baseLower',
      'baseUpper',
    ]);
  });
});

describe('Vault + Multicall address book', () => {
  it('exports cKES_USDT_anchor + Multicall3 addresses verbatim', () => {
    expect(VAULT_ADDRESSES.cKES_USDT_anchor.toLowerCase()).toBe(
      '0xe304b980535c29869983bc58d129f984fec4176f',
    );
    expect(MULTICALL3_CELO.toLowerCase()).toBe(
      '0xca11bde05977b3631167028862be2a173976ca11',
    );
  });

  it('VAULT_ABI pins canonical ICHIVault function names (Plan 02-00 ABI fixture)', () => {
    expect(VAULT_ABI.length).toBeGreaterThanOrEqual(5);
  });
});
