import { describe, it, expect, vi, beforeEach } from 'vitest';
import { readFileSync, existsSync, rmSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import {
  MENTO_ADDRESSES,
  BROKER_ABI,
  BIPOOL_ABI,
  snapFxBlocks,
} from '../src/mento/historical-rate.js';

const EXCHANGE_ID =
  '0x89de88b8eb790de26f4649f543cb6893d93635c728ac857f0926e842fb0d298b' as const;

function makeMockClient(quotedRate: bigint, revertOn: number[] = []): any {
  return {
    readContract: vi.fn(async (args: any) => {
      const block = Number(args.blockNumber);
      if (revertOn.includes(block)) throw new Error('execution reverted');
      return quotedRate;
    }),
  };
}

function tmpFile(): string {
  const dir = mkdtempSync(join(tmpdir(), 'fx_snap_test_'));
  return join(dir, 'fx.jsonl');
}

describe('snapFxBlocks', () => {
  let TMP: string;
  beforeEach(() => {
    TMP = tmpFile();
    if (existsSync(TMP)) rmSync(TMP);
  });

  it('returns one row per block with method=exact', async () => {
    const client = makeMockClient(1_000_000_000_000_000_000n);
    const rows = await snapFxBlocks({
      blocks: [100, 200],
      exchangeId: EXCHANGE_ID,
      outputPath: TMP,
      client,
    });
    expect(rows.length).toBe(2);
    expect(rows[0].method).toBe('exact');
    expect(rows[0].rate_x1e18).toBe('1000000000000000000');
    expect(rows[0].source).toBe('mento-broker');
  });

  it('threads blockNumber per readContract call (Pitfall 1)', async () => {
    const client = makeMockClient(1n);
    await snapFxBlocks({
      blocks: [100, 200],
      exchangeId: EXCHANGE_ID,
      outputPath: TMP,
      client,
    });
    expect(client.readContract.mock.calls[0][0].blockNumber).toBe(100n);
    expect(client.readContract.mock.calls[1][0].blockNumber).toBe(200n);
    expect(client.readContract.mock.calls[0][0].address.toLowerCase()).toBe(
      MENTO_ADDRESSES.Broker.toLowerCase(),
    );
    expect(client.readContract.mock.calls[0][0].functionName).toBe(
      'getAmountOut',
    );
  });

  it('marks revert blocks as method=unavailable with rate=0', async () => {
    const client = makeMockClient(1_000_000_000_000_000_000n, [150]);
    const rows = await snapFxBlocks({
      blocks: [100, 150, 200],
      exchangeId: EXCHANGE_ID,
      outputPath: TMP,
      client,
    });
    expect(rows[1].method).toBe('unavailable');
    expect(rows[1].rate_x1e18).toBe('0');
    expect(rows[0].method).toBe('exact');
    expect(rows[2].method).toBe('exact');
  });

  it('deduplicates blocks', async () => {
    const client = makeMockClient(1n);
    await snapFxBlocks({
      blocks: [100, 100, 200, 200, 200],
      exchangeId: EXCHANGE_ID,
      outputPath: TMP,
      client,
    });
    expect(client.readContract.mock.calls.length).toBe(2);
  });

  it('writes JSONL sidecar parseable with blockscout provenance URL', async () => {
    const client = makeMockClient(1_500_000_000_000_000_000n);
    await snapFxBlocks({
      blocks: [100],
      exchangeId: EXCHANGE_ID,
      outputPath: TMP,
      client,
    });
    const line = readFileSync(TMP, 'utf-8').trim();
    const row = JSON.parse(line);
    expect(row.block).toBe(100);
    expect(row.source).toBe('mento-broker');
    expect(row.rate_x1e18).toBe('1500000000000000000');
    expect(row.method).toBe('exact');
    expect(row.provenance_url).toContain('blockscout.com/block/100');
  });

  it('passes correct args to broker getAmountOut (BiPoolManager + exchangeId + cKES + USDm + 1e18)', async () => {
    const client = makeMockClient(1n);
    await snapFxBlocks({
      blocks: [100],
      exchangeId: EXCHANGE_ID,
      outputPath: TMP,
      client,
    });
    const args = client.readContract.mock.calls[0][0].args;
    expect(args[0].toLowerCase()).toBe(
      MENTO_ADDRESSES.BiPoolManager.toLowerCase(),
    );
    expect(args[1]).toBe(EXCHANGE_ID);
    expect(args[2].toLowerCase()).toBe(MENTO_ADDRESSES.cKES.toLowerCase());
    expect(args[3].toLowerCase()).toBe(MENTO_ADDRESSES.USDm.toLowerCase());
    expect(args[4]).toBe(10n ** 18n);
  });
});

describe('Mento address book', () => {
  it('exports verified Broker + BiPoolManager + cKES + USDm addresses', () => {
    expect(MENTO_ADDRESSES.Broker.toLowerCase()).toBe(
      '0x777a8255ca72412f0d706dc03c9d1987306b4cad',
    );
    expect(MENTO_ADDRESSES.BiPoolManager.toLowerCase()).toBe(
      '0x22d9db95e6ae61c104a7b6f6c78d7993b94ec901',
    );
    expect(MENTO_ADDRESSES.cKES.toLowerCase()).toBe(
      '0x456a3d042c0dbd3db53d5489e98dfb038553b0d0',
    );
    expect(MENTO_ADDRESSES.USDm.toLowerCase()).toBe(
      '0x765de816845861e75a25fca122bb6898b8b1282a',
    );
  });

  it('BROKER_ABI + BIPOOL_ABI parse correctly', () => {
    expect(BROKER_ABI.length).toBeGreaterThan(0);
    expect(BIPOOL_ABI.length).toBeGreaterThan(0);
  });
});
