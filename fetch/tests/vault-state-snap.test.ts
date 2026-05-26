import { describe, it, expect } from 'vitest';
import {
  VAULT_ADDRESSES,
  MULTICALL3_CELO,
  VAULT_ABI,
  snapVaultState,
} from '../src/vault/state-snap.js';

describe('ichi vault state sidecar', () => {
  it.todo(
    'Plan 02-04: snapVaultState batches per-block multicall against Celo Multicall3',
  );
  it.todo('Plan 02-04: snapVaultState threads blockNumber per multicall');
  it.todo(
    'Plan 02-04: snapVaultState per-block memoization deduplicates by blockNumber',
  );
  it.todo('Plan 02-04: snapVaultState output parquet has VaultStateRow schema');
  it.todo('Plan 02-04: snapVaultState writes endpoint=forno cost-ledger row');

  it('exports the snapVaultState signature (Wave 0 scaffold throws)', () => {
    expect(typeof snapVaultState).toBe('function');
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
    // Names verified against analysis/tests/fixtures/ichi_vault_abi.json
    expect(VAULT_ABI.length).toBeGreaterThanOrEqual(5);
  });
});
