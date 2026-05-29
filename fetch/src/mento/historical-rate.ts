/**
 * Mento Broker historical-block FX-rate sidecar generator (PANEL-03).
 *
 * Why: Mento SDK 3.2.8 QuoteService.getAmountOut() does NOT accept blockNumber —
 * it always queries head (RESEARCH §B + Pitfall 1). For per-event FX snap we MUST
 * use raw viem readContract({ blockNumber: N }) against the Broker contract directly.
 *
 * Output: JSONL sidecar at outputPath (one row per requested block).
 * Schema: { block, source, rate_x1e18, method, provenance_url }
 *
 * cost-ledger: every readContract call writes a row with endpoint='forno'
 * (DEMAND-01 uncapped).
 *
 * Resolved cKES↔USDm exchangeId is captured in
 * analysis/tests/fixtures/mento_cKES_USDm_exchange_id.json by Plan 02-00.
 */
import { createHash } from 'node:crypto';
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import { parseAbi, type Address, type PublicClient } from 'viem';
import { celoClient } from '../viem-clients.js';
import { appendLedger } from '../cost-ledger.js';

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
  blocks: number[]; // event blocks needing FX rates (deduped + sorted internally)
  exchangeId: `0x${string}`; // from analysis/tests/fixtures/mento_cKES_USDm_exchange_id.json
  tokenIn?: Address; // default cKES
  tokenOut?: Address; // default USDm
  amountIn?: bigint; // default 1e18 (1 unit)
  client?: PublicClient; // default celoClient (cached singleton)
  outputPath: string; // JSONL sidecar path
}

/**
 * Snap Mento Broker mid-rates at requested historical blocks.
 *
 * For each unique block: calls Broker.getAmountOut(BiPoolManager, exchangeId,
 * cKES, USDm, 1e18) via raw viem.readContract with `blockNumber: BigInt(block)`
 * threaded (load-bearing per Pitfall 1 — SDK silently queries head).
 *
 * On revert: row records method='unavailable' with rate_x1e18='0' and the
 * downstream Python fx_snap forward-fills from the most recent prior 'exact' row.
 *
 * Writes JSONL sidecar (one JSON object per line) at outputPath.
 * Appends a cost-ledger row per readContract call (endpoint='forno', uncapped).
 */
export async function snapFxBlocks(
  opts: FxSnapOptions,
): Promise<FxSnapRow[]> {
  const client = (opts.client ?? celoClient) as PublicClient;
  const tokenIn = opts.tokenIn ?? (MENTO_ADDRESSES.cKES as Address);
  const tokenOut = opts.tokenOut ?? (MENTO_ADDRESSES.USDm as Address);
  const amountIn = opts.amountIn ?? 10n ** 18n;

  // Dedup + sort blocks (per-block dedup invariant; downstream readers expect
  // monotonic block ordering for the asof join).
  const dedupedBlocks = Array.from(new Set(opts.blocks)).sort((a, b) => a - b);

  const rows: FxSnapRow[] = [];
  for (const block of dedupedBlocks) {
    let row: FxSnapRow;
    try {
      const out = await client.readContract({
        address: MENTO_ADDRESSES.Broker as Address,
        abi: BROKER_ABI,
        functionName: 'getAmountOut',
        args: [
          MENTO_ADDRESSES.BiPoolManager as Address,
          opts.exchangeId,
          tokenIn,
          tokenOut,
          amountIn,
        ],
        blockNumber: BigInt(block), // LOAD-BEARING — RESEARCH §B + Pitfall 1
      });
      row = {
        block,
        source: 'mento-broker',
        rate_x1e18: (out as bigint).toString(),
        method: 'exact',
        provenance_url: `https://celo.blockscout.com/block/${block}`,
      };
    } catch {
      // Broker revert at this block (paused exchange, pre-deployment, zero
      // liquidity, precision underflow). Mark unavailable; downstream Python
      // forward-fills from the most recent prior 'exact' rate.
      row = {
        block,
        source: 'mento-broker',
        rate_x1e18: '0',
        method: 'unavailable',
        provenance_url: `https://celo.blockscout.com/block/${block}`,
      };
    }
    rows.push(row);

    // Best-effort cost-ledger append; tests use ephemeral cwd where
    // `data/raw/` may not exist; appendLedger creates the dir, but if the
    // write fails for any reason we don't want to fail the snap.
    try {
      const queryId = `mento-fx-${block}-${opts.exchangeId.slice(0, 10)}`;
      const responseSha = createHash('sha256')
        .update(row.rate_x1e18)
        .digest('hex');
      await appendLedger({
        timestamp: new Date().toISOString(),
        endpoint: 'forno',
        query_id: queryId,
        cost_usdc: '0',
        paid_real: false,
        tx_hash: null,
        chain: 'celo',
        response_bytes: row.rate_x1e18.length,
        response_sha256: responseSha,
        fetch_id: queryId,
      });
    } catch {
      /* best-effort in tests with ephemeral cwd */
    }
  }

  mkdirSync(dirname(opts.outputPath), { recursive: true });
  const lines = rows.map((r) => JSON.stringify(r)).join('\n');
  writeFileSync(opts.outputPath, lines + '\n');

  return rows;
}
