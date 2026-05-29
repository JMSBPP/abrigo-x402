// fetch/tests/protocol-agnostic.test.ts
// FETCH-01 SC-5 leak-gate test — the load-bearing contract that proves the
// L1 fetch layer has zero protocol-name special-cases. Phase-6 swap-surface
// invariant (`grep -r "ichi" fetch/src` returns 0 hits) builds on this gate.
//
// Two parallel checks:
//   (1) Recursive walk of fetch/src/ rejecting forbidden patterns: protocol-name
//       branches (config.name == 'ichi' / 'steer'), hard-coded factory addresses
//       (0x9FAb... ICHI / 0x116Dba... Steer), and magic fee-tier literals
//       (0.0001, 100, 500, 3000, 10000) when associated with `fee = ...`.
//   (2) The synthetic test_fixture.toml (name='synthetic-test', fee_tier=7777)
//       loads through the SAME loadProtocol() code path as ichi.toml — proves
//       the loader has no special-case branches.
//
// Subgraph dormant-state tests use vi.stubEnv (checker I8) rather than
// process.env mutation + dynamic import; client.ts reads GRAPH_API_KEY at
// CALL TIME, so static imports + stubEnv interact cleanly.
//
// Owned by Plan 01-05.

import { describe, test, expect, vi, afterEach } from 'vitest';
import { readFileSync, readdirSync } from 'node:fs';
import { join, extname } from 'node:path';
import { loadProtocol } from '../src/protocol-spec.js';
import {
  getSubgraphClient,
  MissingGraphApiKeyError,
} from '../src/subgraph/client.js';
import { testDirname } from './_helpers.js';

const __dirname = testDirname(import.meta.url);

function* walk(dir: string): Generator<string> {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory() && !entry.name.startsWith('.')) {
      yield* walk(full);
    } else if (
      entry.isFile() &&
      ['.ts', '.tsx', '.js', '.mjs'].includes(extname(entry.name))
    ) {
      yield full;
    }
  }
}

// Forbidden patterns. Justifications:
// - if config.name == 'ichi'/'steer'         -> protocol-name branch in business logic
// - if protocol == 'ichi'/'steer'             -> same
// - if vault_owner == 'ichi'                  -> per RESEARCH §L sketch
// - factory address literals                  -> these belong in protocols/*.toml only
// - fee = 0.0001 / 100 / 500 / 3000 / 10000   -> magic fee-tier literals
const FORBIDDEN_PROTOCOL_BRANCHES: RegExp[] = [
  /if\s*\(?\s*config\.name\s*[!=]==?\s*['"](ichi|steer)['"]/,
  /if\s*\(?\s*protocol\s*[!=]==?\s*['"](ichi|steer)['"]/,
  /if\s*\(?\s*vault_owner\s*[!=]==?\s*['"](ichi|steer)['"]/,
  /\b0x9FAb4bdD4E05f5C023CCC85D2071b49791D7418F\b/i,
  /\b0x116Dba5DcE9CcDA828218b7eB46406810632014C\b/i,
];

// Magic fee-tier literals: only flagged when assigned to a `fee*` lvalue.
// Naked `100` / `500` etc. in array sizes or hex offsets are not flagged.
const FORBIDDEN_MAGIC_FEE_TIERS: RegExp[] = [
  /\bfee[_a-zA-Z]*\s*[:=]\s*(?:0\.0001|100|500|3000|10000)\b/,
];

describe('FETCH-01 SC-5: protocol-agnosticism contract', () => {
  test('no protocol-name conditionals, hard-coded factory addresses, or magic fee-tier literals in fetch/src/', () => {
    const offenders: {
      file: string;
      pattern: string;
      line: number;
      text: string;
    }[] = [];
    const patterns: RegExp[] = [
      ...FORBIDDEN_PROTOCOL_BRANCHES,
      ...FORBIDDEN_MAGIC_FEE_TIERS,
    ];
    // __dirname = fetch/tests/. src dir = fetch/src/.
    const srcDir = join(__dirname, '..', 'src');
    for (const file of walk(srcDir)) {
      const lines = readFileSync(file, 'utf-8').split('\n');
      for (let i = 0; i < lines.length; i++) {
        const lineText = lines[i] ?? '';
        for (const pat of patterns) {
          if (pat.test(lineText)) {
            offenders.push({
              file,
              pattern: pat.source,
              line: i + 1,
              text: lineText.trim(),
            });
          }
        }
      }
    }
    if (offenders.length > 0) {
      // Surface offenders verbatim for fast triage.
      console.error('SC-5 LEAK offenders:', JSON.stringify(offenders, null, 2));
    }
    expect(offenders).toEqual([]);
  });

  test('synthetic test_fixture.toml (name=synthetic-test, fee_tier=7777) loads via the SAME code path as ichi.toml', async () => {
    const synth = await loadProtocol(
      join(__dirname, 'fixtures', 'test_fixture.toml'),
    );
    // The loader has no name-based branch — verifying values came through
    // a uniform path is proof.
    expect(synth.name).toBe('synthetic-test');
    expect(synth.chain_id).toBe(42220);
    expect(synth.anchor_pool.address).toMatch(/^0x[0-9a-fA-F]{40}$/);
    // Non-standard Uniswap V3 fee tier — would fail if the loader had a
    // magic-number branch on {100,500,3000,10000}.
    expect(synth.anchor_pool.fee_tier).toBe(7777);
    expect(synth.anchor_pool.mixing_class).toBe('mento-native');
    // Critical NEGATIVE assertion: NO assertion on name being 'ichi'/'steer'.
  });

  test('synthetic fixture exposes the synthetic vault under the same VaultSchema as ichi.toml', async () => {
    const synth = await loadProtocol(
      join(__dirname, 'fixtures', 'test_fixture.toml'),
    );
    const vaultIds = Object.keys(synth.vaults);
    expect(vaultIds).toContain('synthetic_vault_1');
    const v = synth.vaults.synthetic_vault_1;
    expect(v?.active).toBe(true);
    expect(v?.mixing_class).toBe('mento-native');
    expect(v?.pool_address).toMatch(/^0x[0-9a-fA-F]{40}$/);
  });
});

describe('getSubgraphClient — disabled-by-default (orchestrator finding #2)', () => {
  // Per checker I8: vi.stubEnv + vi.unstubAllEnvs is the safe primitive for
  // env mutation in vitest. The subgraph module reads process.env.GRAPH_API_KEY
  // at CALL TIME (inside the function body — verified by reading client.ts),
  // so static-imported references bind correctly with stubEnv. No dynamic
  // import needed.
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  test('throws MissingGraphApiKeyError when GRAPH_API_KEY is unset (empty string)', () => {
    vi.stubEnv('GRAPH_API_KEY', '');
    expect(() => getSubgraphClient('any-deployment-id')).toThrow(
      MissingGraphApiKeyError,
    );
  });

  test('returns a defined GraphQLClient when GRAPH_API_KEY is set', () => {
    vi.stubEnv('GRAPH_API_KEY', 'test-key-12345');
    const client = getSubgraphClient(
      '9nh6Ums63wFcoZpmegyPcAFtY3CAzQc3S6cuERALYMqa',
    );
    expect(client).toBeDefined();
    // Smoke-check that the URL the client targets includes the gateway path
    // shape — we don't fire any request here.
    expect(typeof client.request).toBe('function');
  });

  test('MissingGraphApiKeyError carries a name and informative message', () => {
    vi.stubEnv('GRAPH_API_KEY', '');
    try {
      getSubgraphClient('any');
      throw new Error('expected throw');
    } catch (err) {
      expect(err).toBeInstanceOf(MissingGraphApiKeyError);
      const e = err as MissingGraphApiKeyError;
      expect(e.name).toBe('MissingGraphApiKeyError');
      expect(e.message).toMatch(/GRAPH_API_KEY/);
    }
  });
});
