// fetch/tests/cli-integration.test.ts — Plan 01-08 lands the real assertions.
import { describe } from 'vitest';

describe.todo('End-to-end CLI integration (Plan 01-08)', () => {
  // Will assert: `pnpm fetch ichi` invokes the full pipeline against captured
  // fixtures (Blockscout v1 getLogs + viem decode + cache write + cost-ledger
  // append + freshness gate), producing a manifest.json entry with non-empty
  // dataHash. Marked with vitest tag 'integration' to allow CI exclusion.
});
