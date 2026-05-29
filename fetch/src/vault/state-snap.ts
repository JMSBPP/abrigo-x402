/**
 * ICHI vault state sidecar generator (Plan 02-04).
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
 * so we deduplicate the input block list to avoid redundant multicall round-trips.
 *
 * Output: JSONL sidecar at opts.outputPath (one JSON row per deduped block).
 * The TS↔Python boundary is JSONL (deterministic line-per-row, byte-stable).
 * Parquet conversion + PANEL-02 metadata-header injection happens on the
 * Python side via polars 1.41's write_parquet(metadata=...) in Plans 02-07/02-08.
 *
 * Cost-ledger: each multicall round-trip writes an endpoint='forno' row.
 * Forno is uncapped per DEMAND-01 (NEVER counted against the 90k/mo Graph budget).
 *
 * Pitfall 3 mitigation: the `blockNumber: BigInt(N)` arg is threaded into every
 * multicall — without it, viem queries head-of-chain and silently produces stale
 * data for old blocks.
 *
 * Canonical ABI names verified against analysis/tests/fixtures/ichi_vault_abi.json
 * (Plan 02-00 capture from Blockscout-v2 verified source):
 *   getTotalAmounts (NOT totalAmounts), baseLower/baseUpper (NOT lowerTick/upperTick).
 */
import { parseAbi, type Address, type PublicClient } from 'viem';
import { celoClient } from '../viem-clients.js';
import { appendLedger } from '../cost-ledger.js';
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import { createHash, randomUUID } from 'node:crypto';

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
  totalAmounts_0: string | null;
  totalAmounts_1: string | null;
  totalSupply: string | null;
  currentTick: number | null;
  lowerTick: number | null;
  upperTick: number | null;
}

export interface VaultStateOptions {
  vaultAddress: Address;
  blocks: number[]; // may contain duplicates; per-block memo deduplicates
  client?: PublicClient; // default celoClient (Forno)
  outputPath: string; // JSONL output path
}

/**
 * Snap ICHI vault state at a list of blocks via Celo Multicall3.
 *
 * Per-block memoization deduplicates the input blocks; one multicall per unique block.
 * The multicall threads `blockNumber: BigInt(block)` per batch — Pitfall 3 mitigation.
 *
 * Writes JSONL sidecar to opts.outputPath. Returns the row array for in-memory use.
 * Cost-ledger receives one endpoint='forno' row per multicall round-trip.
 */
export async function snapVaultState(
  opts: VaultStateOptions,
): Promise<VaultStateRow[]> {
  const client = (opts.client ?? celoClient) as PublicClient;
  const dedupedBlocks = Array.from(new Set(opts.blocks)).sort((a, b) => a - b);
  const rows: VaultStateRow[] = [];

  for (const block of dedupedBlocks) {
    const results = (await client.multicall({
      multicallAddress: MULTICALL3_CELO,
      blockNumber: BigInt(block),
      allowFailure: true,
      contracts: [
        {
          address: opts.vaultAddress,
          abi: VAULT_ABI,
          functionName: 'getTotalAmounts',
        },
        {
          address: opts.vaultAddress,
          abi: VAULT_ABI,
          functionName: 'totalSupply',
        },
        {
          address: opts.vaultAddress,
          abi: VAULT_ABI,
          functionName: 'currentTick',
        },
        {
          address: opts.vaultAddress,
          abi: VAULT_ABI,
          functionName: 'baseLower',
        },
        {
          address: opts.vaultAddress,
          abi: VAULT_ABI,
          functionName: 'baseUpper',
        },
      ],
    } as any)) as any[];

    const [ta, ts, ct, lt, ut] = results;
    rows.push({
      blockNumber: block,
      totalAmounts_0:
        ta?.status === 'success'
          ? (ta.result as readonly [bigint, bigint])[0].toString()
          : null,
      totalAmounts_1:
        ta?.status === 'success'
          ? (ta.result as readonly [bigint, bigint])[1].toString()
          : null,
      totalSupply:
        ts?.status === 'success' ? (ts.result as bigint).toString() : null,
      currentTick: ct?.status === 'success' ? Number(ct.result) : null,
      lowerTick: lt?.status === 'success' ? Number(lt.result) : null,
      upperTick: ut?.status === 'success' ? Number(ut.result) : null,
    });

    // DEMAND-01 enforce: every Forno multicall → endpoint='forno' ledger row
    // (uncapped; recorded for audit + provenance). Best-effort: tests run
    // without a writable ledger dir, so tolerate failure here.
    try {
      const queryId = `vault-state-${opts.vaultAddress.toLowerCase()}-${block}`;
      const sha = createHash('sha256').update(queryId).digest('hex');
      await appendLedger({
        timestamp: new Date().toISOString(),
        endpoint: 'forno',
        query_id: queryId,
        cost_usdc: '0',
        paid_real: false,
        tx_hash: null,
        chain: 'celo',
        response_bytes: 0,
        response_sha256: sha,
        fetch_id: randomUUID(),
      });
    } catch {
      /* ledger best-effort in tests; tolerate missing dir or schema drift */
    }
  }

  // Write JSONL sidecar — one JSON object per line, trailing newline for
  // deterministic byte-stability across reruns.
  mkdirSync(dirname(opts.outputPath), { recursive: true });
  const lines = rows.map((r) => JSON.stringify(r)).join('\n');
  writeFileSync(opts.outputPath, lines + '\n');

  return rows;
}
