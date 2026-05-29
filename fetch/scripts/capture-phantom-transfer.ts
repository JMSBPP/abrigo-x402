// fetch/scripts/capture-phantom-transfer.ts
// One-shot Blockscout v1 probe: capture a real Celo fee-abstraction
// phantom-transfer transaction involving the USDT adapter.
// Output: analysis/tests/fixtures/phantom_transfer_usdt_real.json.
//
// Owned by Plan 02-00 (Wave 0 capture). Used by Plan 02-03 phantom_filter
// unit tests to verify adapter-to/from Transfers are excluded.
//
// Run: `pnpm -C fetch exec tsx scripts/capture-phantom-transfer.ts`
import { writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { getLogsV1 } from '../src/blockscout/v1-getlogs.js';
import { loadFornoHeadSnapshot } from '../src/constants.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..', '..');

const USDT_ADAPTER = '0x0e2a3e05bc9a16f5292a6170456a710cb89c6f72';
const TRANSFER_TOPIC0 =
  '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef';
const BLOCKSCOUT_BASE = 'https://celo.blockscout.com';

const fixturePath = join(
  REPO_ROOT,
  'analysis/tests/fixtures/phantom_transfer_usdt_real.json',
);

const head = loadFornoHeadSnapshot().head;
console.error(`Forno head snapshot: ${head}`);

// Scan a recent window for adapter Transfer activity.
// The USDT adapter sees fee-abstraction traffic only when users pay gas in USDT.
// Try progressively wider windows if smaller ones return empty.
const WINDOWS = [10_000, 50_000, 200_000, 1_000_000];

let target: Awaited<ReturnType<typeof getLogsV1>>[number] | undefined;
let usedWindow = 0;
for (const w of WINDOWS) {
  const fromBlock = head - w;
  console.error(`Probing blocks ${fromBlock} → ${head} (window=${w})...`);
  let logs: Awaited<ReturnType<typeof getLogsV1>> = [];
  try {
    logs = await getLogsV1({
      baseUrl: BLOCKSCOUT_BASE,
      address: USDT_ADAPTER,
      topic0: TRANSFER_TOPIC0,
      fromBlock,
      toBlock: head,
    });
  } catch (err) {
    // v1 client throws on "No logs found" (its regex is /No records/i which
    // misses the live "No logs found" message). Treat as empty-success.
    const msg = (err as Error).message ?? '';
    if (/No (logs|records) found/i.test(msg)) {
      logs = [];
    } else {
      throw err;
    }
  }
  console.error(`  found ${logs.length} adapter Transfer logs`);
  if (logs.length > 0) {
    target = logs[logs.length - 1];
    usedWindow = w;
    break;
  }
}

if (!target) {
  const fallback = {
    _meta: {
      source: 'blockscout-v1-getlogs',
      url: `${BLOCKSCOUT_BASE}/api?module=logs&action=getLogs`,
      captured_at: new Date().toISOString(),
      head_block_at_capture: head,
      adapter: USDT_ADAPTER,
      windows_probed: WINDOWS,
      status: 'no-adapter-traffic-found',
    },
    txHash: null,
    blockNumber: null,
    logs: [],
    note:
      'USDT-adapter saw zero Transfer activity in the probed windows. ' +
      'phantom_transfer_synthetic.json is the load-bearing fixture for ' +
      'Plan 02-03 unit tests until adapter traffic surfaces.',
  };
  writeFileSync(fixturePath, JSON.stringify(fallback, null, 2));
  console.log('No adapter traffic — wrote fallback fixture');
  process.exit(0);
}

// Fetch full tx logs to capture the paired structural context (Swap + adapter Transfer + counterparty Transfer in same tx).
const txHash = target.transactionHash;
const receiptUrl = `${BLOCKSCOUT_BASE}/api/v2/transactions/${txHash}/logs`;
console.error(`Fetching full tx logs from ${receiptUrl}`);

interface TxLogsResponse {
  items: unknown[];
}
const res = (await (await fetch(receiptUrl)).json()) as TxLogsResponse;

const blockNumberDecimal = parseInt(target.blockNumber, 16);

const out = {
  _meta: {
    source: 'blockscout-v1-getlogs + blockscout-v2-tx-logs',
    head_block_at_capture: head,
    adapter: USDT_ADAPTER,
    captured_at: new Date().toISOString(),
    window_used: usedWindow,
    status: 'resolved',
    receipt_url: receiptUrl,
  },
  txHash,
  blockNumber: blockNumberDecimal,
  blockNumberHex: target.blockNumber,
  adapterLogTopics: target.topics,
  logs: res.items,
};

writeFileSync(fixturePath, JSON.stringify(out, null, 2));
console.log(
  `Captured: txHash=${txHash}, block=${blockNumberDecimal}, logs=${res.items.length}`,
);
process.exit(0);
