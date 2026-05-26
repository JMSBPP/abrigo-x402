// fetch/src/constants.ts
// Phase 1 deterministic constants. The Forno head snapshot is used by --dry-run mode
// to avoid network calls in CI (see Plan 01-06 / orchestrator C3).
//
// To refresh: bump notes/forno_head_snapshot.json manually OR add a Phase-2 `pnpm head:refresh`
// script. Do NOT call Forno on every dry-run.

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));

export interface FornoHeadSnapshot {
  head: number;
  snapshotted_at: string;
  source: string;
  refresh_policy: string;
}

export function loadFornoHeadSnapshot(
  path: string = join(__dirname, '..', '..', 'notes', 'forno_head_snapshot.json'),
): FornoHeadSnapshot {
  const raw = readFileSync(path, 'utf-8');
  return JSON.parse(raw) as FornoHeadSnapshot;
}

// Last-resort fallback if the snapshot file is missing (e.g., partial checkout).
// Refresh periodically; tied to notes/forno_head_snapshot.json on 2026-05-26.
export const DRY_RUN_FALLBACK_HEAD = 67896653;

// Chain IDs (CAIP-2 unprefixed integers; viem chain objects in viem-clients.ts).
export const CELO_CHAIN_ID = 42220 as const;
export const BASE_SEPOLIA_CHAIN_ID = 84532 as const;

// Canonical USDT on Celo (cf. protocols/_schema.toml canonical_celo_usdt).
// Single source-of-truth for the "stables" half of the cKES/USDT anchor pool.
export const CELO_USDT_ADDRESS = '0x48065fbBE25f71C9282ddf5e1cD6D6A887483D5e' as const;

// Base Sepolia USDC — used by the x402-mock round-trip (CONTEXT.md x402 product-test scope).
// Verified live at https://base-sepolia.blockscout.com/token/0x036CbD53842c5426634e7929541eC2318f3dCF7e
export const BASE_SEPOLIA_USDC_ADDRESS = '0x036cbd53842c5426634e7929541ec2318f3dcf7e' as const;
