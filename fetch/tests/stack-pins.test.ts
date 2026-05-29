// fetch/tests/stack-pins.test.ts
// FETCH-01 SC-1: pinned-versions contract test.
//
// Reads fetch/package.json and asserts every dependency in STACK.md is pinned
// EXACTLY (no caret/tilde prefix). Drift detection — if STACK.md research
// substrate goes out of sync with the actual install, this test fails loudly
// before any downstream code is exercised.

import { describe, test, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { testDirname } from './_helpers';

const __dirname = testDirname(import.meta.url);
const pkg = JSON.parse(
  readFileSync(join(__dirname, '..', 'package.json'), 'utf-8'),
) as {
  dependencies?: Record<string, string>;
  devDependencies?: Record<string, string>;
  version: string;
};

describe('FETCH-01 SC-1: pinned versions contract (STACK.md)', () => {
  const REQUIRED_PINS: Record<string, string> = {
    viem: '2.51.0',
    '@x402/fetch': '2.13.0',
    '@x402/evm': '2.13.0',
    '@x402/core': '2.13.0',
    '@graphprotocol/client-x402': '1.0.0',
    'graphql-request': '7.4.0',
    '@mento-protocol/mento-sdk': '3.2.8',
    zod: '4.4.3',
  };

  for (const [name, expected] of Object.entries(REQUIRED_PINS)) {
    test(`${name} pinned exactly to ${expected}`, () => {
      const actual = pkg.dependencies?.[name];
      expect(actual, `dep ${name} missing from fetch/package.json`).toBeTruthy();
      expect(actual).toBe(expected);
      // Reject caret/tilde prefixes — pin must be exact.
      expect(actual).not.toMatch(/^[\^~]/);
    });
  }

  test('fetch/package.json declares a non-empty semver version', () => {
    expect(pkg.version).toMatch(/^\d+\.\d+\.\d+/);
  });
});
