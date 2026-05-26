// fetch/tests/protocol-agnostic.test.ts — Plan 01-05 lands the real assertions.
import { describe } from 'vitest';

describe.todo('Protocol-agnosticism leak gate (REPRO-01 / Plan 01-05)', () => {
  // Will assert (authoritative gate; Makefile `make leak-check` is the cheap complement):
  //   1. No `if (config.name === "ichi" | "steer")` branches in fetch/src
  //   2. No protocol factory address literals in fetch/src
  //   3. No Uniswap V3 magic fee-tier ints in fetch/src
  // Greps fetch/src recursively; fails the suite on any hit.
});
