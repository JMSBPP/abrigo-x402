#!/usr/bin/env tsx
// fetch/scripts/build_panel_real.ts
// Plan 02-10 — Real-data bulk-pull driver for the ICHI cKES/USDT anchor pool.
//
// Orchestrates the four Phase-1/Phase-2 bulk-pull primitives:
//   1. Pool events (Swap/Mint/Burn) — Blockscout v1 getLogs, chunked
//   2. Transfer companions per unique tx — Blockscout v2 /transactions/{hash}/logs
//   3. Vault state per unique block — Forno multicall (snapVaultState)
//   4. Mento FX snap per unique block — Forno readContract (snapFxBlocks)
//
// Writes four JSONL sidecars to data/raw/ichi/<pool>/ which the Python
// `panel.build_panel` then materializes into the Parquet panel.
//
// CLI:
//   pnpm -C fetch exec tsx scripts/build_panel_real.ts \
//     --pool 0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F \
//     --vault 0xe304b980535c29869983BC58d129F984Fec4176F \
//     --from 67378253 --to 67896653 \
//     [--chunk 100000] [--limit-tx 0]
//
// Cost-ledger: every Blockscout/Forno call appends one row. Forno is uncapped.

import {
  existsSync,
  mkdirSync,
  writeFileSync,
  appendFileSync,
  readFileSync,
} from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash, randomUUID } from 'node:crypto';
import type { Address } from 'viem';

import { getLogsV1, type BlockscoutLog } from '../src/blockscout/v1-getlogs.js';
import { snapVaultState } from '../src/vault/state-snap.js';
import { snapFxBlocks } from '../src/mento/historical-rate.js';
import { appendLedger } from '../src/cost-ledger.js';

// -----------------------------------------------------------------------------
// Constants
// -----------------------------------------------------------------------------

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..', '..');

// Verified canonical hash literals.
const SWAP_TOPIC0 =
  '0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67';
const MINT_TOPIC0 =
  '0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde';
const BURN_TOPIC0 =
  '0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c';
const TRANSFER_TOPIC0 =
  '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef';

const BLOCKSCOUT_BASE = 'https://celo.blockscout.com';

// Mento cKES↔USDm exchangeId captured by Plan 02-00.
const MENTO_EXCHANGE_FIXTURE = join(
  REPO_ROOT,
  'analysis',
  'tests',
  'fixtures',
  'mento_cKES_USDm_exchange_id.json',
);

// Inter-call delay to be polite to free-tier endpoints.
// Blockscout free tier on celo.blockscout.com tolerates ~5 req/s sustained;
// we pace at ~5/s (200ms delay) and use a generous backoff schedule on 429s.
const RATE_DELAY_MS = 250;
const MAX_RETRY = 6;

// -----------------------------------------------------------------------------
// Tiny CLI parser
// -----------------------------------------------------------------------------

function parseArgs(argv: string[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a !== undefined && a.startsWith('--')) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next !== undefined && !next.startsWith('--')) {
        out[key] = next;
        i++;
      } else {
        out[key] = 'true';
      }
    }
  }
  return out;
}

// -----------------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------------

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

async function withRetry<T>(label: string, fn: () => Promise<T>): Promise<T> {
  let lastErr: unknown;
  for (let attempt = 1; attempt <= MAX_RETRY; attempt++) {
    try {
      return await fn();
    } catch (e) {
      lastErr = e;
      const msg = e instanceof Error ? e.message : String(e);
      const is429 = /429|rate.?limit/i.test(msg);
      // Exponential backoff with a 30s ceiling. 429s start at 2s and reach
      // 30s by attempt 5; transient 5xxs back off at 0.5s base.
      const baseMs = is429 ? 2000 : 500;
      const delay = Math.min(30_000, baseMs * 2 ** (attempt - 1));
      console.warn(
        `  [retry ${attempt}/${MAX_RETRY}] ${label} failed (${msg.slice(0, 80)}); sleeping ${delay}ms`,
      );
      await sleep(delay);
    }
  }
  throw lastErr;
}

function writeJsonl<T>(path: string, rows: T[]): void {
  mkdirSync(dirname(path), { recursive: true });
  const lines = rows.map((r) => JSON.stringify(r)).join('\n');
  writeFileSync(path, rows.length === 0 ? '' : lines + '\n');
}

function appendJsonl<T>(path: string, rows: T[]): void {
  if (rows.length === 0) return;
  mkdirSync(dirname(path), { recursive: true });
  const lines = rows.map((r) => JSON.stringify(r)).join('\n') + '\n';
  appendFileSync(path, lines);
}

async function logBlockscoutLedger(
  endpoint: 'blockscout',
  queryId: string,
  responseBytes: number,
  responseSha: string,
): Promise<void> {
  try {
    await appendLedger({
      timestamp: new Date().toISOString(),
      endpoint,
      query_id: queryId,
      cost_usdc: '0',
      paid_real: false,
      tx_hash: null,
      chain: 'celo',
      response_bytes: responseBytes,
      response_sha256: responseSha,
      fetch_id: randomUUID(),
    });
  } catch (e) {
    console.warn(`  ledger-append failed (best-effort): ${(e as Error).message}`);
  }
}

// -----------------------------------------------------------------------------
// Task 1 — Pool-event pull via Blockscout v1 getLogs
// -----------------------------------------------------------------------------

interface PoolEventsResult {
  events: BlockscoutLog[];
  txHashes: Set<string>;
  blocks: Set<number>;
}

async function pullPoolEvents(
  pool: Address,
  fromBlock: number,
  toBlock: number,
  chunkSize: number,
  outputPath: string,
): Promise<PoolEventsResult> {
  // Wipe output (idempotent re-runs)
  mkdirSync(dirname(outputPath), { recursive: true });
  writeFileSync(outputPath, '');

  const allEvents: BlockscoutLog[] = [];
  const txHashes = new Set<string>();
  const blocks = new Set<number>();

  const totalChunks = Math.ceil((toBlock - fromBlock + 1) / chunkSize);
  let chunkIdx = 0;

  for (
    let cursor = fromBlock;
    cursor <= toBlock;
    cursor += chunkSize, chunkIdx++
  ) {
    const chunkTo = Math.min(cursor + chunkSize - 1, toBlock);

    for (const topic of [SWAP_TOPIC0, MINT_TOPIC0, BURN_TOPIC0]) {
      const label = `pool-events chunk ${chunkIdx + 1}/${totalChunks} blocks ${cursor}-${chunkTo} topic ${topic.slice(0, 10)}`;
      const logs = await withRetry(label, () =>
        getLogsV1({
          baseUrl: BLOCKSCOUT_BASE,
          address: pool,
          fromBlock: cursor,
          toBlock: chunkTo,
          topic0: topic,
        }),
      );

      const queryId = `bs-v1-${pool.toLowerCase()}-${cursor}-${chunkTo}-${topic.slice(2, 10)}`;
      const respText = JSON.stringify(logs);
      const sha = createHash('sha256').update(respText).digest('hex');
      await logBlockscoutLedger('blockscout', queryId, respText.length, sha);

      allEvents.push(...logs);
      appendJsonl(outputPath, logs);
      for (const log of logs) {
        txHashes.add(log.transactionHash);
        blocks.add(parseInt(log.blockNumber, 16));
      }

      console.log(`[${chunkIdx + 1}/${totalChunks}] ${label}: ${logs.length} logs`);
      await sleep(RATE_DELAY_MS);
    }
  }

  console.log(
    `pool-events: ${allEvents.length} total events, ${txHashes.size} unique txs, ${blocks.size} unique blocks`,
  );
  return { events: allEvents, txHashes, blocks };
}

// -----------------------------------------------------------------------------
// Task 2 — Transfer companion pull via Blockscout v2 /transactions/{hash}/logs
// -----------------------------------------------------------------------------

// Blockscout v2 returns a fundamentally different log shape from v1; we
// normalise to the v1-compat schema expected downstream (load_jsonl).
interface BsV2Log {
  address: { hash: string } | string;
  block_number: number | string;
  block_hash?: string;
  data: string;
  index: number | string;
  topics: (string | null)[];
  transaction_hash?: string;
}

interface BsV2Response {
  items: BsV2Log[];
}

function normalizeV2ToV1(log: BsV2Log, txHash: string): BlockscoutLog {
  const addr =
    typeof log.address === 'string'
      ? log.address
      : (log.address.hash ?? '');
  const blockNum =
    typeof log.block_number === 'number'
      ? `0x${log.block_number.toString(16)}`
      : String(log.block_number);
  const logIdx =
    typeof log.index === 'number'
      ? `0x${log.index.toString(16)}`
      : String(log.index);
  return {
    address: addr.toLowerCase(),
    blockNumber: blockNum,
    timeStamp: '0x0', // v2 endpoint omits timeStamp; downstream uses blockNumber primarily
    logIndex: logIdx,
    transactionHash: log.transaction_hash ?? txHash,
    topics: log.topics,
    data: log.data,
  };
}

async function pullTxLogs(
  txHashes: string[],
  outputPath: string,
): Promise<{ transferLogs: BlockscoutLog[]; called: number }> {
  mkdirSync(dirname(outputPath), { recursive: true });
  writeFileSync(outputPath, '');

  const transferLogs: BlockscoutLog[] = [];
  const total = txHashes.length;
  let called = 0;

  for (let i = 0; i < total; i++) {
    const txHash = txHashes[i];
    if (txHash === undefined) continue;
    const url = `${BLOCKSCOUT_BASE}/api/v2/transactions/${txHash}/logs`;
    const label = `tx-logs ${i + 1}/${total} ${txHash.slice(0, 10)}`;

    const items = await withRetry(label, async (): Promise<BsV2Log[]> => {
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error(`Blockscout v2 tx-logs HTTP ${res.status}`);
      }
      const json = (await res.json()) as BsV2Response;
      return json.items ?? [];
    });
    called++;

    const queryId = `bs-v2-tx-${txHash.toLowerCase()}`;
    const respText = JSON.stringify(items);
    const sha = createHash('sha256').update(respText).digest('hex');
    await logBlockscoutLedger('blockscout', queryId, respText.length, sha);

    const filtered = items
      .filter((l) => {
        const t0 = (l.topics ?? [])[0];
        return (
          t0 !== null && t0 !== undefined && t0.toLowerCase() === TRANSFER_TOPIC0
        );
      })
      .map((l) => normalizeV2ToV1(l, txHash));

    transferLogs.push(...filtered);
    appendJsonl(outputPath, filtered);

    if ((i + 1) % 50 === 0 || i + 1 === total) {
      console.log(
        `[${i + 1}/${total}] tx-logs done; transfer companions so far: ${transferLogs.length}`,
      );
    }
    await sleep(RATE_DELAY_MS);
  }

  console.log(
    `tx-logs: ${called} Blockscout v2 calls, ${transferLogs.length} Transfer companions captured`,
  );
  return { transferLogs, called };
}

// -----------------------------------------------------------------------------
// Task 3 — Vault state pull via Forno multicall
// -----------------------------------------------------------------------------

async function pullVaultState(
  vault: Address,
  blocks: number[],
  outputPath: string,
): Promise<void> {
  console.log(
    `vault-state: snapping ${new Set(blocks).size} unique blocks via Forno multicall...`,
  );
  await withRetry('snapVaultState', () =>
    snapVaultState({
      vaultAddress: vault,
      blocks,
      outputPath,
    }),
  );
  console.log(`vault-state: written → ${outputPath}`);
}

// -----------------------------------------------------------------------------
// Task 4 — FX snap pull via Forno readContract
// -----------------------------------------------------------------------------

async function pullFxSnap(
  blocks: number[],
  outputPath: string,
): Promise<void> {
  if (!existsSync(MENTO_EXCHANGE_FIXTURE)) {
    throw new Error(
      `Missing Mento exchangeId fixture at ${MENTO_EXCHANGE_FIXTURE}`,
    );
  }
  const fixture = JSON.parse(readFileSync(MENTO_EXCHANGE_FIXTURE, 'utf-8')) as {
    exchangeId: `0x${string}`;
  };

  console.log(
    `fx-snap: snapping ${new Set(blocks).size} unique blocks via Mento Broker (exchangeId=${fixture.exchangeId.slice(0, 12)}...)...`,
  );
  await withRetry('snapFxBlocks', () =>
    snapFxBlocks({
      blocks,
      exchangeId: fixture.exchangeId,
      outputPath,
    }),
  );
  console.log(`fx-snap: written → ${outputPath}`);
}

// -----------------------------------------------------------------------------
// Main
// -----------------------------------------------------------------------------

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));

  const pool = (args.pool ?? '').trim() as Address;
  const vault = (args.vault ?? '').trim() as Address;
  const fromBlock = Number(args.from);
  const toBlock = Number(args.to);
  const chunkSize = Number(args.chunk ?? '100000');
  const limitTx = Number(args['limit-tx'] ?? '0'); // 0 = no limit

  if (!pool || !vault || !Number.isFinite(fromBlock) || !Number.isFinite(toBlock)) {
    console.error(
      'usage: build_panel_real.ts --pool 0x... --vault 0x... --from N --to N [--chunk 100000] [--limit-tx 0]',
    );
    process.exit(2);
  }

  console.log('=== build_panel_real ===');
  console.log(`pool       ${pool}`);
  console.log(`vault      ${vault}`);
  console.log(`range      [${fromBlock}, ${toBlock}]  (${toBlock - fromBlock + 1} blocks)`);
  console.log(`chunkSize  ${chunkSize}`);
  console.log(`limit-tx   ${limitTx === 0 ? 'none' : limitTx}`);

  const outDir = join(REPO_ROOT, 'data', 'raw', 'ichi', pool);
  const eventsPath = join(outDir, 'pool_events.jsonl');
  const txLogsPath = join(outDir, 'tx_logs.jsonl');
  const vaultStatePath = join(outDir, 'vault_state.jsonl');
  const fxSnapPath = join(outDir, 'fx_snap.jsonl');

  const startMs = Date.now();

  // ---- 1. Pool events ----
  const { events, txHashes, blocks } = await pullPoolEvents(
    pool,
    fromBlock,
    toBlock,
    chunkSize,
    eventsPath,
  );

  // ---- 2. Transfer companions ----
  let txHashList = Array.from(txHashes);
  if (limitTx > 0 && txHashList.length > limitTx) {
    console.warn(
      `  applying --limit-tx ${limitTx} (would otherwise call Blockscout v2 ${txHashList.length} times)`,
    );
    txHashList = txHashList.slice(0, limitTx);
  }
  await pullTxLogs(txHashList, txLogsPath);

  // ---- 3. Vault state ----
  // Only Swap-event blocks need vault state (per panel pipeline contract).
  const swapBlocks = Array.from(
    new Set(
      events
        .filter((e) => (e.topics?.[0] ?? '').toLowerCase() === SWAP_TOPIC0)
        .map((e) => parseInt(e.blockNumber, 16)),
    ),
  ).sort((a, b) => a - b);
  await pullVaultState(vault, swapBlocks, vaultStatePath);

  // ---- 4. FX snap ----
  // Asof-join consumes all event blocks (not just swaps) so coverage holds.
  const allBlocks = Array.from(blocks).sort((a, b) => a - b);
  await pullFxSnap(allBlocks, fxSnapPath);

  const durationMs = Date.now() - startMs;
  console.log(`\n=== complete in ${(durationMs / 1000).toFixed(1)}s ===`);
  console.log(`outputs in ${outDir}:`);
  console.log(`  pool_events.jsonl  (${events.length} rows)`);
  console.log(`  tx_logs.jsonl      (Transfer companions)`);
  console.log(`  vault_state.jsonl  (${swapBlocks.length} blocks)`);
  console.log(`  fx_snap.jsonl      (${allBlocks.length} blocks)`);
}

main().catch((e) => {
  console.error('FATAL:', e);
  process.exit(1);
});
