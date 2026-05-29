// fetch/tests/budget-dry-run.test.ts — Plan 01-06 (FETCH-02 SC-6).
//
// Validates the pure estimateBudget() function feeding the
// `pnpm fetch ichi --dry-run --estimate-budget` CLI path. Wave 2 plan;
// depends on Plan 01-01 protocol-spec loader + _helpers.testDirname.
//
// Per checker I9 (synthetic spec must round-trip through ProtocolSpecSchema.parse
// BEFORE estimateBudget consumes it): the 50-vault test constructs a raw TOML
// shape, runs it through the parser, and only then passes the result to
// estimateBudget. This catches schema regressions in the test itself.

import { describe, test, expect } from 'vitest';
import { estimateBudget } from '../src/budget.js';
import { loadProtocol, ProtocolSpecSchema } from '../src/protocol-spec.js';
import { testDirname } from './_helpers.js';
import { join } from 'node:path';

const __dirname = testDirname(import.meta.url);

describe('estimateBudget (FETCH-02 SC-6)', () => {
  test('protocols/ichi.toml: single active vault under 30k earmark', async () => {
    const spec = await loadProtocol(join(__dirname, '..', '..', 'protocols', 'ichi.toml'));
    const est = estimateBudget(spec, 67_854_122);
    expect(est.protocol).toBe('ichi');
    expect(est.vault_count).toBeGreaterThanOrEqual(1);
    expect(est.total_queries).toBeLessThan(30_000);
    expect(est.exceeds_earmark).toBe(false);
    expect(est.recommended_reallocation).toBeNull();
  });

  test('synthetic 50-vault spec exceeds 30k earmark (round-trips through ProtocolSpecSchema)', async () => {
    // Per checker I9: build the raw TOML shape, run it through the actual
    // schema parser, then call estimateBudget. This catches schema regressions
    // in the test itself.
    const rawSynth = {
      protocol: {
        name: 'synth-50',
        chain_id: 42220,
        factory_address: '0xdEAD000000000000000000000000000000beef00',
        data_cost_class: 'indexer-analytics-queries',
        panel_construction: 'multi-vault',
        iteration: 99,
        cold_backfill_from_block: 60_000_000,
        anchor_pool: {
          address: '0xdEAD000000000000000000000000000000beef01',
          token0: '0xdEAD000000000000000000000000000000beef02',
          token1: '0xdEAD000000000000000000000000000000beef03',
          fee_tier: 7777,
          mixing_class: 'mento-native',
          swaps_per_30d_observed: 100,
        },
        vaults: Object.fromEntries(
          Array.from({ length: 50 }, (_, i) => [
            `v${i}`,
            {
              address: `0xdEAD${String(i).padStart(36, '0')}`,
              active: true,
              mixing_class: 'mento-native',
              pool_address: '0xdEAD000000000000000000000000000000beef01',
            },
          ]),
        ),
      },
    };
    const synth = ProtocolSpecSchema.parse(rawSynth);
    const est = estimateBudget(synth, 67_854_122, 30_000);
    expect(est.vault_count).toBe(50);
    expect(est.exceeds_earmark).toBe(true);
    expect(est.recommended_reallocation).toContain('reserve');
    expect(est.recommended_reallocation).toContain('force');
  });

  test('returns the required JSON shape keys', async () => {
    const spec = await loadProtocol(join(__dirname, '..', '..', 'protocols', 'ichi.toml'));
    const est = estimateBudget(spec, 67_854_122);
    const keys = Object.keys(est).sort();
    expect(keys).toEqual([
      'blocks_per_vault',
      'earmark',
      'exceeds_earmark',
      'iteration',
      'protocol',
      'queries_per_vault',
      'recommended_reallocation',
      'total_queries',
      'vault_count',
    ]);
  });
});
