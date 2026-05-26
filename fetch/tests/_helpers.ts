// fetch/tests/_helpers.ts
// Phase 1 test helpers — populated by Wave 1 plans (01-01..01-08).
//
// Conventions:
//   - All fixtures live under fetch/tests/fixtures/ (gitignored data is forbidden;
//     captured-once JSON only). Integration tests that hit real networks live
//     under fetch/tests/integration/ and are excluded by vitest.config.ts.
//   - Helpers re-exported here are shared across the describe.todo stubs below.
//
// This file is intentionally minimal at Plan 01-00; Wave 1 fills it in.

export const FETCH_TESTS_HELPERS_VERSION = '01-00-skeleton' as const;
