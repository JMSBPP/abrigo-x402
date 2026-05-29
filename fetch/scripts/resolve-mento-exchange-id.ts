// fetch/scripts/resolve-mento-exchange-id.ts
// One-shot Forno probe: resolve the Mento BiPoolManager exchangeId for the
// cKES↔USDm pair. Output: analysis/tests/fixtures/mento_cKES_USDm_exchange_id.json.
//
// Owned by Plan 02-00 (Wave 0 capture). The resolved exchangeId is the
// load-bearing input for the Mento historical-rate sidecar (Plan 02-06).
// Forno is uncapped per DEMAND-01.
//
// Run: `pnpm -C fetch exec tsx scripts/resolve-mento-exchange-id.ts`
import { writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseAbi, type Address } from 'viem';
import { celoClient } from '../src/viem-clients.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..', '..');

const BIPOOL: Address = '0x22d9db95E6Ae61c104A7B6F6C78D7993B94ec901';
const BROKER: Address = '0x777A8255cA72412f0d706dc03C9D1987306B4CaD';
const CKES = '0x456a3D042C0DbD3db53D5489e98dFb038553B0d0'.toLowerCase();
const USDM = '0x765DE816845861e75A25fCA122bb6898B8B1282a'.toLowerCase();

const ABI = parseAbi([
  'function getExchangeIds() view returns (bytes32[])',
  'function getPoolExchange(bytes32) view returns ((address asset0, address asset1, address pricingModule, uint256 bucket0, uint256 bucket1, uint256 lastBucketUpdate, (uint256 spread, uint256 referenceRateFeedID, uint256 referenceRateResetFrequency, uint256 minimumReports, uint256 stablePoolResetSize) config))',
]);

const ids = (await celoClient.readContract({
  address: BIPOOL,
  abi: ABI,
  functionName: 'getExchangeIds',
})) as `0x${string}`[];

console.error(`Probing ${ids.length} BiPoolManager exchanges...`);

let resolved: {
  exchangeId: string;
  asset0: string;
  asset1: string;
  pricingModule: string;
} | null = null;

for (const id of ids) {
  try {
    const pe = (await celoClient.readContract({
      address: BIPOOL,
      abi: ABI,
      functionName: 'getPoolExchange',
      args: [id],
    })) as {
      asset0: string;
      asset1: string;
      pricingModule: string;
    };
    const a = pe.asset0.toLowerCase();
    const b = pe.asset1.toLowerCase();
    if ((a === CKES && b === USDM) || (a === USDM && b === CKES)) {
      resolved = {
        exchangeId: id,
        asset0: a,
        asset1: b,
        pricingModule: pe.pricingModule,
      };
      break;
    }
  } catch (err) {
    console.error(`  getPoolExchange(${id}) reverted; skipping`);
  }
}

const fixturePath = join(REPO_ROOT, 'analysis/tests/fixtures/mento_cKES_USDm_exchange_id.json');
const out = {
  _meta: {
    source: 'forno-live-call',
    url: 'https://forno.celo.org',
    biPoolManager: BIPOOL,
    broker: BROKER,
    captured_at: new Date().toISOString(),
    pair_lower: { cKES: CKES, USDm: USDM },
    status: resolved ? 'resolved' : 'unresolved',
  },
  exchangeId: resolved?.exchangeId ?? null,
  asset0: resolved?.asset0 ?? null,
  asset1: resolved?.asset1 ?? null,
  pricingModule: resolved?.pricingModule ?? null,
  totalExchangesProbed: ids.length,
};

writeFileSync(fixturePath, JSON.stringify(out, null, 2));
if (resolved) {
  console.log(`Resolved cKES↔USDm exchangeId: ${resolved.exchangeId}`);
  process.exit(0);
} else {
  console.error(`cKES↔USDm exchange not found among ${ids.length} exchanges`);
  process.exit(1);
}
