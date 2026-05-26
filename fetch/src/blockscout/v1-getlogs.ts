// fetch/src/blockscout/v1-getlogs.ts
// Blockscout v1 etherscan-compat getLogs client. Phase-1 primary bulk-pull
// substrate for the cKES/USDT Uniswap V3 anchor pool Swap-event panel.
//
// CRITICAL ENDPOINT CHOICE (orchestrator finding #1, verified RESEARCH §C):
//   Blockscout v2  /api/v2/addresses/<addr>/logs   REJECTS topic0 with HTTP 422.
//   Blockscout v1  /api?module=logs&action=getLogs ACCEPTS topic0 + fromBlock + toBlock.
// We use v1. Do not refactor to v2 — the unit tests pin the URL shape.
//
// Pagination: 1000-log page cap (Blockscout v1 hard limit per RESEARCH §C).
// Keyset cursor: when result.length === 1000 we re-request with
// fromBlock = parseInt(lastLog.blockNumber, 16) + 1. This is the "next-page"
// pattern for the v1 etherscan-compat module (which does not expose a `page`
// pointer); it relies on Blockscout returning logs in ascending block order
// (verified RESEARCH §C). Pages may overlap within a single block (logIndex
// jitter), but the block-cursor approach guarantees forward progress.
//
// Owned by Plan 01-05. Consumed by Plan 01-06 (CLI ICHI fetch path).

import { z } from 'zod';

const LogSchema = z.object({
  address: z.string(),
  blockNumber: z.string(),
  timeStamp: z.string(),
  logIndex: z.string(),
  transactionHash: z.string(),
  topics: z.array(z.string().nullable()),
  data: z.string(),
});

const ResponseSchema = z.object({
  status: z.string(),
  message: z.string(),
  // v1 etherscan-compat sometimes returns `result: "Error! ..."` (string) for
  // certain errors. We accept either an array OR a string and let the caller
  // raise on status !== '1'.
  result: z.union([z.array(LogSchema), z.string()]),
});

export type BlockscoutLog = z.infer<typeof LogSchema>;

export interface GetLogsV1Opts {
  baseUrl: string;
  address: string;
  fromBlock: number;
  toBlock: number;
  topic0: string;
  apiKey?: string;
  /**
   * Fetch implementation override. Defaults to global fetch. Tests pass
   * an in-memory mock to avoid live HTTP.
   */
  fetcher?: typeof fetch;
}

/**
 * Page through Blockscout v1 getLogs for a single topic-filtered query.
 *
 * Resolves to the concatenated list of logs across all pages. Auto-paginates
 * when a page returns the maximum 1000 logs (block-cursor keyset; see header).
 *
 * Throws on:
 *   - HTTP non-2xx from the upstream
 *   - status !== '1' with a non-empty result (real upstream error)
 *
 * Treats status === '0' with message containing 'No records' as an empty
 * success (the v1 endpoint's idiom for "no logs in this range").
 */
export async function getLogsV1(opts: GetLogsV1Opts): Promise<BlockscoutLog[]> {
  const { baseUrl, address, fromBlock, toBlock, topic0, apiKey } = opts;
  const fetcher = opts.fetcher ?? fetch;
  const all: BlockscoutLog[] = [];
  let cursor = fromBlock;
  while (cursor <= toBlock) {
    const url = new URL(`${baseUrl}/api`);
    url.searchParams.set('module', 'logs');
    url.searchParams.set('action', 'getLogs');
    url.searchParams.set('address', address);
    url.searchParams.set('fromBlock', String(cursor));
    url.searchParams.set('toBlock', String(toBlock));
    url.searchParams.set('topic0', topic0);
    if (apiKey !== undefined && apiKey !== '') {
      url.searchParams.set('apikey', apiKey);
    }

    const res = await fetcher(url.toString());
    if (!res.ok) {
      throw new Error(`Blockscout v1 getLogs HTTP ${res.status}`);
    }
    const parsed = ResponseSchema.parse(await res.json());
    const result = Array.isArray(parsed.result) ? parsed.result : [];

    if (parsed.status !== '1') {
      // v1 idiom: status='0' + 'No records found' + empty result == success-empty.
      if (result.length === 0 && /No records/i.test(parsed.message ?? '')) {
        break;
      }
      throw new Error(
        `Blockscout v1 status=${parsed.status}: ${parsed.message}`,
      );
    }

    all.push(...result);

    // Termination: last page (under the 1000-row cap) OR no rows at all.
    if (result.length < 1000) {
      break;
    }

    // Advance cursor past the last block we observed. blockNumber is hex.
    const lastEntry = result[result.length - 1];
    if (lastEntry === undefined) {
      break;
    }
    const lastBlock = parseInt(lastEntry.blockNumber, 16);
    if (!Number.isFinite(lastBlock)) {
      throw new Error(
        `Blockscout v1 returned malformed blockNumber=${lastEntry.blockNumber}`,
      );
    }
    cursor = lastBlock + 1;
  }
  return all;
}
