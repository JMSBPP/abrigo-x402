// fetch/tests/protocol-spec.test.ts — Plan 01-05 lands the real assertions.
import { describe } from 'vitest';

describe.todo('protocols/*.toml zod schema parse (Plan 01-05)', () => {
  // Will assert: protocols/ichi.toml + protocols/steer.toml load via zod
  // mirror of protocols/_schema.toml; data_cost_class + mixing_class enums
  // enforced at parse time; M12 verified-before-fetch invariant for active vaults.
});
