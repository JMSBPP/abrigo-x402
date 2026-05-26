#!/usr/bin/env tsx
// fetch/src/cli.ts
// Phase 1 stub entrypoint. Plan 01-06 expands this with --dry-run /
// --estimate-budget / --force; Plan 01-08 wires the full ichi subcommand
// against Blockscout v1 getLogs + the cost-ledger.
//
// At Plan 01-01 the CLI handles only:
//   - --version / -v   : prints the package version from fetch/package.json
//   - ichi | steer     : prints "not yet implemented" to stderr and exits 2
//   - anything else    : prints usage and exits 1

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const pkg = JSON.parse(
  readFileSync(join(__dirname, '..', 'package.json'), 'utf-8'),
) as { version: string };

const argv = process.argv.slice(2);

if (argv.includes('--version') || argv.includes('-v')) {
  console.log(pkg.version);
  process.exit(0);
}

const cmd = argv[0];
if (cmd === 'ichi' || cmd === 'steer') {
  // Wave 2 plan 01-06 implements the full ichi pipeline; 01-08 wires CLI integration.
  console.error(
    `[fetch] '${cmd}' subcommand not yet implemented — Phase 1 Plan 01-06/01-08 wires this.`,
  );
  process.exit(2);
}

console.error(
  'Usage: pnpm -C fetch fetch <ichi|steer> [--dry-run] [--estimate-budget] [--force] [--pool 0x...] [--from N] [--to N]',
);
process.exit(1);
