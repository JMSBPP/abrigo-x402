/**
 * Mento Broker historical-block FX-rate sidecar generator (Plan 02-06 fills body).
 *
 * Why: Mento SDK 3.2.8 QuoteService.getAmountOut() does NOT accept blockNumber —
 * it always queries head. For per-event FX snap (PANEL-03), must use raw viem
 * readContract({ blockNumber: N }) against the Broker contract directly.
 *
 * Output: data/raw/ichi/fx_rates/<block_range>.parquet
 * Schema: { block: UInt64, source: Categorical, rate: Decimal[38,18], method: Categorical, provenance_url: String }
 *
 * cost-ledger: every batch writes a row with endpoint='forno' (DEMAND-01 uncapped).
 *
 * Resolved cKES↔USDm exchangeId is captured in
 * analysis/tests/fixtures/mento_cKES_USDm_exchange_id.json by Plan 02-00.
 */
import { parseAbi, type Address, type PublicClient } from 'viem';
import { celoClient } from '../viem-clients.js';
// Note: cost-ledger will be wired in Plan 02-06 implementation.
// import { appendLedger } from '../cost-ledger.js';

export const MENTO_ADDRESSES = {
  Broker: '0x777A8255cA72412f0d706dc03C9D1987306B4CaD',
  BiPoolManager: '0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901',
  cKES: '0x456a3D042C0DbD3db53D5489e98dFb038553B0d0',
  USDm: '0x765DE816845861e75A25fCA122bb6898B8B1282a',
} as const satisfies Record<string, Address>;

export const BROKER_ABI = parseAbi([
  'function getAmountOut(address exchangeProvider, bytes32 exchangeId, address tokenIn, address tokenOut, uint256 amountIn) view returns (uint256)',
]);

export const BIPOOL_ABI = parseAbi([
  'function getExchangeIds() view returns (bytes32[])',
  'function getPoolExchange(bytes32 exchangeId) view returns ((address asset0, address asset1, address pricingModule, uint256 bucket0, uint256 bucket1, uint256 lastBucketUpdate, (uint256 spread, uint256 referenceRateFeedID, uint256 referenceRateResetFrequency, uint256 minimumReports, uint256 stablePoolResetSize) config))',
]);

export interface FxSnapRow {
  block: number;
  source: 'mento-broker';
  rate_x1e18: string; // decimal string; cKES per 1 USDm at this block, scaled 1e18
  method: 'exact' | 'unavailable';
  provenance_url: string;
}

export interface FxSnapOptions {
  blocks: number[]; // deduped event blocks needing FX rates
  exchangeId: `0x${string}`; // from analysis/tests/fixtures/mento_cKES_USDm_exchange_id.json
  tokenIn?: Address;
  tokenOut?: Address;
  amountIn?: bigint; // default 1e18 (1 USDm)
  client?: PublicClient;
  outputPath: string; // parquet sidecar path
}

/**
 * Plan 02-06 fills this. Wave 0 ships signature only.
 * Per-block readContract with blockNumber threaded; batched via Multicall3 when possible.
 */
export async function snapFxBlocks(_opts: FxSnapOptions): Promise<FxSnapRow[]> {
  // celoClient kept in the import surface so Plan 02-06 has the default ready.
  void celoClient;
  throw new Error('Plan 02-06: snapFxBlocks not yet implemented');
}
