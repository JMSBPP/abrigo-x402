#!/usr/bin/env tsx
// fetch/src/cli.ts — Plan 01-06 (Wave 2). Composes Wave-1 modules into the
// `pnpm -C fetch fetch <ichi|steer> [...]` CLI.
//
// Flag matrix:
//   --version | -v         : prints fetch/package.json version, exits 0
//   --dry-run              : NO network calls; head from env/snapshot/fallback
//   --estimate-budget      : emit BudgetEstimate JSON to stdout
//   --force                : bypass GraphBudgetExceededError gate (non-dry-run only)
//   --pool 0x...           : optional pool address for cache-key short-circuit
//   --from N --to N        : optional block range for cache-key short-circuit
//
// Checker C3 head-derivation precedence (NEVER touches network on dry-run):
//   1. FETCH_HEAD_OVERRIDE env var
//   2. notes/forno_head_snapshot.json (loadFornoHeadSnapshot)
//   3. fetch/src/constants.ts DRY_RUN_FALLBACK_HEAD
//   4. (non-dry-run only) celoClient.getBlockNumber() — head_source = 'live'
//
// The CLI emits `head_source` in the JSON so consumers can audit head
// provenance; dry-run output MUST never report head_source === 'live'.

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { loadProtocol } from './protocol-spec.js';
import { celoClient } from './viem-clients.js';
import { estimateBudget } from './budget.js';
import { checkBudget, GraphBudgetExceededError } from './cost-ledger.js';
import { cacheKeyHash } from './cache/key.js';
import { findByCacheKey } from './cache/manifest.js';
import { loadFornoHeadSnapshot, DRY_RUN_FALLBACK_HEAD } from './constants.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const pkg = JSON.parse(
  readFileSync(join(__dirname, '..', 'package.json'), 'utf-8'),
) as { version: string };

type ParsedFlags = Record<string, string | boolean>;

function parseArgs(argv: string[]): { flags: ParsedFlags; positional: string[] } {
  const flags: ParsedFlags = {};
  const positional: string[] = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const name = a.slice(2);
      const next = argv[i + 1];
      if (next !== undefined && !next.startsWith('--')) {
        flags[name] = next;
        i++;
      } else {
        flags[name] = true;
      }
    } else {
      positional.push(a);
    }
  }
  return { flags, positional };
}

type HeadSource = 'env_override' | 'snapshot' | 'fallback' | 'live';

interface ResolvedHead {
  head: number;
  head_source: HeadSource;
}

async function resolveHead(opts: { dryRun: boolean }): Promise<ResolvedHead> {
  const envOverride = process.env.FETCH_HEAD_OVERRIDE;
  if (envOverride && envOverride.trim().length > 0) {
    const n = Number(envOverride);
    if (Number.isFinite(n) && n > 0) {
      return { head: n, head_source: 'env_override' };
    }
  }
  if (opts.dryRun) {
    // Dry-run must be deterministic + network-free (checker C3).
    try {
      const snap = loadFornoHeadSnapshot();
      return { head: snap.head, head_source: 'snapshot' };
    } catch {
      return { head: DRY_RUN_FALLBACK_HEAD, head_source: 'fallback' };
    }
  }
  // Non-dry-run: live Forno call (rate-limit caveat from viem-clients.ts applies).
  const head = Number(await celoClient.getBlockNumber());
  return { head, head_source: 'live' };
}

async function main(): Promise<number> {
  const argv = process.argv.slice(2);
  if (argv.includes('--version') || argv.includes('-v')) {
    console.log(pkg.version);
    return 0;
  }

  const { flags, positional } = parseArgs(argv);
  const cmd = positional[0];
  if (cmd !== 'ichi' && cmd !== 'steer') {
    console.error(
      'Usage: pnpm -C fetch fetch <ichi|steer> [--dry-run] [--estimate-budget] [--force] [--pool 0x...] [--from N] [--to N]',
    );
    return 1;
  }

  // Protocol spec path — relative to fetch/ (process.cwd() when invoked via
  // `pnpm -C fetch fetch ...`). The integration test spawns from fetch/ as
  // well, so `../protocols/<cmd>.toml` resolves identically.
  const specPath = join('..', 'protocols', `${cmd}.toml`);
  const spec = await loadProtocol(specPath);

  const dryRun = Boolean(flags['dry-run']);
  const { head, head_source } = await resolveHead({ dryRun });

  const est = estimateBudget(spec, head);

  // Cache short-circuit: if --pool/--from/--to all provided, look up the
  // manifest by cache_key_hash and surface cache_hit boolean. The full
  // skip-network behaviour lands in Plan 01-08; here we just expose the flag.
  let cache_hit = false;
  if (flags.pool && flags.from !== undefined && flags.to !== undefined) {
    const key = cacheKeyHash({
      chainId: spec.chain_id,
      contractAddress: String(flags.pool),
      blockRange: [Number(flags.from), Number(flags.to)],
    });
    const existing = await findByCacheKey(key);
    cache_hit = existing !== null;
  }

  // Budget gate fires ONLY on non-dry-run paths (dry-run is informational).
  if (!dryRun) {
    try {
      await checkBudget({
        projected_graph_queries:
          est.vault_count * Math.ceil(est.blocks_per_vault / 10_000),
        force: Boolean(flags.force),
      });
    } catch (e) {
      if (e instanceof GraphBudgetExceededError) {
        console.error(e.message);
        return 2;
      }
      throw e;
    }
  }

  const output = {
    ...est,
    cache_hit,
    dry_run: dryRun,
    head_block: head,
    head_source,
  };

  if (flags['estimate-budget'] || dryRun) {
    console.log(JSON.stringify(output, null, 2));
  }
  return 0;
}

main()
  .then((code) => process.exit(code))
  .catch((err: unknown) => {
    const msg = err instanceof Error ? err.message : String(err);
    console.error('FATAL:', msg);
    process.exit(99);
  });
