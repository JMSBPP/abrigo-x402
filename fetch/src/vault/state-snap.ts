/**
 * ICHI vault state sidecar generator (Plan 02-04 fills body).
 *
 * Reads vault state per Swap-event block via viem multicall against
 * Celo Multicall3 (0xcA11bde05977b3631167028862bE2a173976CA11):
 *   - getTotalAmounts() -> (uint256 total0, uint256 total1)
 *   - totalSupply()     -> uint256
 *   - currentTick()     -> int24
 *   - baseLower()       -> int24
 *   - baseUpper()       -> int24
 *
 * Per-block memoization: vault state only changes on Mint/Burn/Deposit/Withdraw,
 * so memoize per block to avoid redundant multicall.
 *
 * Output: data/raw/ichi/vault_state/<vault_hash>/<block_range>.parquet
 * cost-ledger: each multicall round-trip writes endpoint='forno' row.
 *
 * The canonical ABI fragment lives in
 * analysis/tests/fixtures/ichi_vault_abi.json (captured by Plan 02-00 from
 * Blockscout-v2 verified source). Function names verified:
 *   getTotalAmounts (NOT totalAmounts), baseLower/baseUpper (NOT lowerTick/upperTick).
 */
import { parseAbi, type Address, type PublicClient } from 'viem';
import { celoClient } from '../viem-clients.js';

export const VAULT_ADDRESSES = {
  cKES_USDT_anchor: '0xe304b980535c29869983BC58d129F984Fec4176F',
  cKES_USDT_pool: '0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F',
} as const satisfies Record<string, Address>;

export const MULTICALL3_CELO: Address =
  '0xcA11bde05977b3631167028862bE2a173976CA11';

// ABI verified against analysis/tests/fixtures/ichi_vault_abi.json (Plan 02-00).
// Function names canonical for the ICHIVault contract on Celo.
export const VAULT_ABI = parseAbi([
  'function getTotalAmounts() view returns (uint256 total0, uint256 total1)',
  'function totalSupply() view returns (uint256)',
  'function currentTick() view returns (int24)',
  'function baseLower() view returns (int24)',
  'function baseUpper() view returns (int24)',
]);

export interface VaultStateRow {
  blockNumber: number;
  totalAmounts_0: string; // decimal string (uint256 → string)
  totalAmounts_1: string;
  totalSupply: string;
  currentTick: number;
  lowerTick: number;
  upperTick: number;
}

export interface VaultStateOptions {
  vaultAddress: Address;
  blocks: number[]; // deduped Swap-event blocks (per-block memo)
  client?: PublicClient;
  outputPath: string;
}

/** Plan 02-04 fills this. Wave 0 ships signature only. */
export async function snapVaultState(
  _opts: VaultStateOptions,
): Promise<VaultStateRow[]> {
  void celoClient;
  throw new Error('Plan 02-04: snapVaultState not yet implemented');
}
