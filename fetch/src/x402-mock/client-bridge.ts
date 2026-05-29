// fetch/src/x402-mock/client-bridge.ts
// Plan 01-07 Task 2 — wrapFetchWithPayment + registerExactEvmScheme bridge.
//
// Resolved against .planning/phases/01-l1-…/01-00-x402-exports.txt (checker I10)
// + live probe of node_modules at @x402/fetch@2.13.0:
//   - x402Client + wrapFetchWithPayment LIVE in @x402/fetch (NOT @x402/core —
//     core only exports x402Version, which is the literal `2`)
//   - registerExactEvmScheme LIVES at the @x402/evm/exact/client SUBPATH
//     (the bare @x402/evm package also re-exports ExactEvmScheme but not
//     registerExactEvmScheme — confirmed by Object.keys() probe)
//
// Default test PRIVATE_KEY: 0x{31 zero bytes}01 (deterministic Ethereum key
// whose address is 0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf; never holds
// real funds on any chain — widely-known test value). CI / vitest uses this;
// developer machines override via .env (real faucet-funded test wallet) when
// running with X402_MOCK_REAL_SETTLE=1.

import { x402Client, wrapFetchWithPayment } from '@x402/fetch';
import { registerExactEvmScheme } from '@x402/evm/exact/client';
import { privateKeyToAccount } from 'viem/accounts';
import type { Hex } from 'viem';

const TEST_DEFAULT_PK =
  '0x0000000000000000000000000000000000000000000000000000000000000001' as Hex;

export interface MakeFetchOpts {
  privateKey?: Hex;
  rpcUrl?: string;
}

export function makeFetchWithPayment(opts: MakeFetchOpts = {}): typeof fetch {
  const pk =
    opts.privateKey ??
    (process.env.PRIVATE_KEY as Hex | undefined) ??
    TEST_DEFAULT_PK;
  if (!pk.startsWith('0x')) {
    throw new Error('PRIVATE_KEY must be 0x-prefixed hex');
  }
  const signer = privateKeyToAccount(pk);
  const client = new x402Client();
  registerExactEvmScheme(client, { signer });
  return wrapFetchWithPayment(fetch, client) as typeof fetch;
}

// Convenience pre-wrapped fetch using env or default test key. Constructed
// lazily so test files that stub PRIVATE_KEY via vi.stubEnv get the override.
let _cached: typeof fetch | undefined;
export const fetchWithPayment: typeof fetch = ((
  input: Parameters<typeof fetch>[0],
  init?: Parameters<typeof fetch>[1],
) => {
  if (!_cached) _cached = makeFetchWithPayment();
  return _cached(input, init);
}) as typeof fetch;
