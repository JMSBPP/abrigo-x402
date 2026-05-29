// fetch/tests/viem-clients.test.ts
// Plan 01-01 Task 3: cached viem PublicClient instances for Celo + Base Sepolia.
//
// No network calls — every assertion reads the configured chain object from the
// PublicClient. Singleton behavior is checked by importing the module twice and
// asserting referential identity.

import { describe, test, expect } from 'vitest';
import {
  celoClient,
  baseSepoliaClient,
  createCeloClient,
  createBaseSepoliaClient,
} from '../src/viem-clients.js';
import { CELO_CHAIN_ID, BASE_SEPOLIA_CHAIN_ID } from '../src/constants.js';

describe('viem cached clients (Plan 01-01 Task 3)', () => {
  test('celoClient is configured for chain 42220 (Celo)', () => {
    expect(celoClient.chain?.id).toBe(CELO_CHAIN_ID);
    expect(celoClient.chain?.id).toBe(42220);
  });

  test('baseSepoliaClient is configured for chain 84532 (Base Sepolia)', () => {
    expect(baseSepoliaClient.chain?.id).toBe(BASE_SEPOLIA_CHAIN_ID);
    expect(baseSepoliaClient.chain?.id).toBe(84532);
  });

  test('clients are cached (singleton across imports)', async () => {
    const mod1 = await import('../src/viem-clients.js');
    const mod2 = await import('../src/viem-clients.js');
    expect(mod1.celoClient).toBe(mod2.celoClient);
    expect(mod1.baseSepoliaClient).toBe(mod2.baseSepoliaClient);
  });

  test('createCeloClient factory returns the same singleton', () => {
    expect(createCeloClient()).toBe(celoClient);
  });

  test('createBaseSepoliaClient factory returns the same singleton', () => {
    expect(createBaseSepoliaClient()).toBe(baseSepoliaClient);
  });
});
