// fetch/src/viem-clients.ts
// Cached viem PublicClient instances for the two Phase-1 chains:
//   - Celo mainnet (chain id 42220, RPC defaults to https://forno.celo.org)
//   - Base Sepolia testnet (chain id 84532, RPC defaults to https://sepolia.base.org)
//
// Both clients are module-level singletons — every import returns the SAME
// instance. This is deliberate: viem PublicClient construction is cheap but
// non-trivial, and Phase-1 callers (freshness wrappers, Blockscout client,
// x402 mock bridge) re-import these per-module. The singleton pattern keeps
// the active socket/keepalive pool unified.
//
// RPC URLs are read at module-load time from process.env with public-RPC
// defaults. Tests that need to override the RPC should do so via vi.stubEnv
// BEFORE the first import (vitest reloads modules per test file by default).
//
// Throttle note: Forno rate-limits aggressively (PITFALLS §6 — burst eth_call
// or eth_blockNumber trips an IP block for ~15min). Phase-1 callers cap Forno
// calls at <= 3 req/sec; the freshness wrapper (Plan 01-03) caches forno_head
// for 5 seconds across multiple freshness checks within a fetch session.

import { createPublicClient, http } from 'viem';
import { celo, baseSepolia } from 'viem/chains';

const CELO_RPC = process.env.CELO_RPC_URL ?? 'https://forno.celo.org';
const BASE_SEPOLIA_RPC = process.env.BASE_SEPOLIA_RPC_URL ?? 'https://sepolia.base.org';

// Type annotations intentionally omitted — viem narrows the PublicClient
// return type to the chain-specific shape (CeloPublicClient, BaseSepoliaPublicClient).
// Annotating as the base `PublicClient` triggers TS2719 because the chain-narrowed
// type is structurally a subtype but TypeScript treats it as nominally different
// (viem's `transactions` union widens per chain). Let inference handle it.
export const celoClient = createPublicClient({
  chain: celo,
  transport: http(CELO_RPC),
});

export const baseSepoliaClient = createPublicClient({
  chain: baseSepolia,
  transport: http(BASE_SEPOLIA_RPC),
});

/**
 * Factory function form — returns the same cached celoClient. Some Wave-1
 * call sites prefer a factory (for ergonomics with the freshness wrapper
 * constructor pattern); this is just an alias.
 */
export function createCeloClient() {
  return celoClient;
}

/**
 * Factory form for Base Sepolia, mirroring createCeloClient.
 */
export function createBaseSepoliaClient() {
  return baseSepoliaClient;
}
