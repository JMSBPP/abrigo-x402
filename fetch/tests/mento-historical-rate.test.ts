import { describe, it, expect } from 'vitest';
import {
  MENTO_ADDRESSES,
  BROKER_ABI,
  BIPOOL_ABI,
  snapFxBlocks,
} from '../src/mento/historical-rate.js';

describe('mento historical-rate sidecar', () => {
  it.todo(
    'Plan 02-06: snapFxBlocks returns one row per requested block with method=exact when Broker quotes',
  );
  it.todo(
    'Plan 02-06: snapFxBlocks returns method=unavailable when Broker reverts at block N',
  );
  it.todo(
    'Plan 02-06: snapFxBlocks threads blockNumber:N to viem.readContract (mock asserts arg)',
  );
  it.todo(
    'Plan 02-06: snapFxBlocks writes endpoint=forno cost-ledger row',
  );
  it.todo(
    'Plan 02-06: snapFxBlocks output parquet has FxSnapRow schema {block, source, rate_x1e18, method, provenance_url}',
  );

  it('exports the snapFxBlocks signature (Wave 0 scaffold throws)', () => {
    // Import-surface smoke test — Plan 02-06 replaces the throwing body.
    expect(typeof snapFxBlocks).toBe('function');
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
