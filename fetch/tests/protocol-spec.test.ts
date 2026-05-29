// fetch/tests/protocol-spec.test.ts
// Plan 01-01 Task 2: loadProtocol() parses protocols/ichi.toml + the synthetic
// test_fixture.toml via @iarna/toml + zod; rejects malformed enum values.
//
// Path resolution: __dirname is computed via testDirname(import.meta.url) per
// the Plan 01-01 ESM convention. fetch/tests/ is the test root; protocols/ is
// two levels up (fetch/tests/ → fetch/ → repo root → protocols/).

import { describe, test, expect } from 'vitest';
import { join } from 'node:path';
import { loadProtocol } from '../src/protocol-spec.js';
import { testDirname } from './_helpers.js';

const __dirname = testDirname(import.meta.url);
const REPO_PROTOCOLS = join(__dirname, '..', '..', 'protocols');
const FIXTURES = join(__dirname, 'fixtures');

describe('protocol-spec loader (Plan 01-01 Task 2)', () => {
  test('loads protocols/ichi.toml as a typed ProtocolSpec', async () => {
    const spec = await loadProtocol(join(REPO_PROTOCOLS, 'ichi.toml'));
    expect(spec.name).toBe('ichi');
    expect(spec.chain_id).toBe(42220);
    expect(spec.anchor_pool.address).toMatch(/^0x[0-9a-fA-F]{40}$/);
    expect(spec.data_cost_class).toBe('indexer-analytics-queries');
    expect(spec.panel_construction).toBe('single-vault');
    expect(spec.anchor_pool.mixing_class).toBe('mento-native');
    // I5 gate: cold_backfill_from_block was added at Plan 01-01 to unblock
    // Plans 01-04 + 01-06. Assertion locks the field's presence.
    expect(spec.cold_backfill_from_block).toBeGreaterThan(0);
    // Vault enumeration carried forward from Phase-0 Plan 00-05.
    expect(Object.keys(spec.vaults).length).toBeGreaterThan(0);
  });

  test('loads synthetic test_fixture.toml with non-standard fee_tier', async () => {
    const spec = await loadProtocol(join(FIXTURES, 'test_fixture.toml'));
    expect(spec.name).toBe('synthetic-test');
    expect(spec.chain_id).toBe(42220);
    // fee_tier = 7777 — proves the loader has no Uniswap-V3-fee-tier branch.
    expect(spec.anchor_pool.fee_tier).toBe(7777);
    expect(spec.iteration).toBe(99);
  });

  test('rejects a TOML with invalid mixing_class via zod enum check', async () => {
    await expect(
      loadProtocol(join(FIXTURES, 'test_fixture_bad.toml')),
    ).rejects.toThrow();
  });

  test('rejects a non-existent file', async () => {
    await expect(
      loadProtocol(join(FIXTURES, 'does_not_exist.toml')),
    ).rejects.toThrow();
  });
});
