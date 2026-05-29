// fetch/tests/freshness.test.ts
// Plan 01-03 — FETCH-03 SC-3 unit tests for BOTH freshness wrappers.
//
// Per checker C4 (single-file invariant): this file will contain BOTH the
// subgraphFreshness and blockscoutFreshness describe blocks (blockscout half
// appended by Task 2). `fornoMock` is IMPORTED from ./_helpers (Plan 01-01) —
// NEVER redeclared locally.
//
// Per RESEARCH.md §H + orchestrator finding #1: Blockscout v2 log shape lacks
// the per-log consensus field hypothesized by the CONTEXT.md draft. The
// blockscout wrapper (Task 2) checks lag-vs-Forno only.

import { describe, test, expect } from 'vitest';
import { subgraphFreshness, SubgraphLagError } from '../src/subgraph/freshness';
import { blockscoutFreshness, BlockscoutFreshnessError } from '../src/blockscout/freshness';
import { fornoMock } from './_helpers';

describe('subgraphFreshness (FETCH-03 SC-3 subgraph path)', () => {
  test('passes at lag = 99', async () => {
    const r = await subgraphFreshness({
      response: { _meta: { block: { number: 67_854_023 } }, foo: 1 },
      forno: fornoMock(67_854_122n) as any,
    });
    expect(r.foo).toBe(1);
  });

  test('throws SubgraphLagError at lag = 101', async () => {
    await expect(
      subgraphFreshness({
        response: { _meta: { block: { number: 67_854_021 } }, foo: 1 },
        forno: fornoMock(67_854_122n) as any,
      })
    ).rejects.toBeInstanceOf(SubgraphLagError);
  });

  test('throws when _meta is missing', async () => {
    await expect(
      subgraphFreshness({ response: { foo: 1 } as any, forno: fornoMock(67_854_122n) as any })
    ).rejects.toBeInstanceOf(SubgraphLagError);
  });

  test('throws when _meta.block.number is missing', async () => {
    await expect(
      subgraphFreshness({
        response: { _meta: { block: {} } } as any,
        forno: fornoMock(67_854_122n) as any,
      })
    ).rejects.toBeInstanceOf(SubgraphLagError);
  });

  test('custom threshold = 50 rejects lag = 75', async () => {
    await expect(
      subgraphFreshness(
        {
          response: { _meta: { block: { number: 67_854_047 } }, foo: 1 },
          forno: fornoMock(67_854_122n) as any,
        },
        50
      )
    ).rejects.toBeInstanceOf(SubgraphLagError);
  });

  test('forno.getBlockNumber called exactly once', async () => {
    const forno = fornoMock(67_854_122n);
    await subgraphFreshness({
      response: { _meta: { block: { number: 67_854_023 } } },
      forno: forno as any,
    });
    expect(forno.getBlockNumber).toHaveBeenCalledTimes(1);
  });
});

describe('blockscoutFreshness (FETCH-03 SC-3 blockscout path)', () => {
  test('passes at lag = 99', async () => {
    const r = await blockscoutFreshness({
      most_recent_log_block: 67_854_023,
      forno: fornoMock(67_854_122n) as any,
      endpoint: 'celo.blockscout.com',
    });
    expect(r.fresh).toBe(true);
    expect(r.lag).toBe(99);
  });

  test('throws BlockscoutFreshnessError at lag = 101', async () => {
    try {
      await blockscoutFreshness({
        most_recent_log_block: 67_854_021,
        forno: fornoMock(67_854_122n) as any,
        endpoint: 'celo.blockscout.com',
      });
      throw new Error('should have thrown');
    } catch (e) {
      expect(e).toBeInstanceOf(BlockscoutFreshnessError);
      expect((e as BlockscoutFreshnessError).details.lag).toBe(101);
      expect((e as BlockscoutFreshnessError).details.endpoint).toBe('celo.blockscout.com');
    }
  });

  test('custom threshold = 50 rejects lag = 75', async () => {
    await expect(
      blockscoutFreshness({
        most_recent_log_block: 67_854_047,
        forno: fornoMock(67_854_122n) as any,
        endpoint: 'celo.blockscout.com',
        threshold: 50,
      })
    ).rejects.toBeInstanceOf(BlockscoutFreshnessError);
  });
});
