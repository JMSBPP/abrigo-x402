// fetch/src/decoders/uniswap-v3-swap.ts
// Uniswap V3 Swap event ABI + decoder. The topic0 constant is the verified
// keccak256("Swap(address,address,int256,int256,uint160,uint128,int24)")
// per RESEARCH §D — pinned verbatim so downstream consumers can grep for it
// and any drift triggers a unit-test failure (see fetch/tests/blockscout-client.test.ts).
//
// Owned by Plan 01-05. Consumed by Plan 01-06 (CLI Swap-log decode + cache write).

import { decodeEventLog } from 'viem';
import type { Abi } from 'viem';

export const UniswapV3SwapEventAbi = [
  {
    type: 'event',
    name: 'Swap',
    inputs: [
      { indexed: true, name: 'sender', type: 'address' },
      { indexed: true, name: 'recipient', type: 'address' },
      { indexed: false, name: 'amount0', type: 'int256' },
      { indexed: false, name: 'amount1', type: 'int256' },
      { indexed: false, name: 'sqrtPriceX96', type: 'uint160' },
      { indexed: false, name: 'liquidity', type: 'uint128' },
      { indexed: false, name: 'tick', type: 'int24' },
    ],
  },
] as const satisfies Abi;

/**
 * topic0 = keccak256("Swap(address,address,int256,int256,uint160,uint128,int24)")
 * Verified live via cast keccak (RESEARCH §D). Do not modify.
 */
export const UniswapV3SwapTopic0 =
  '0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67' as const;

/**
 * Decode a raw Uniswap V3 Swap event log via viem.
 *
 * Caller responsibility: pass exactly the `topics` array and `data` field
 * from Blockscout's getLogs response (cast to `0x${string}`). viem returns
 * typed args: sender + recipient as checksummed addresses; amount0/amount1/
 * sqrtPriceX96/liquidity as bigint; tick as number (int24 fits a JS number).
 *
 * Throws if topics[0] !== UniswapV3SwapTopic0 (viem internal check).
 */
export function decodeSwap(
  topics: readonly `0x${string}`[],
  data: `0x${string}`,
) {
  return decodeEventLog({
    abi: UniswapV3SwapEventAbi,
    eventName: 'Swap',
    topics: topics as unknown as [signature: `0x${string}`, ...args: `0x${string}`[]],
    data,
  });
}
