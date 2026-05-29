// fetch/src/protocol-spec.ts
// L0 protocol-spec loader. Reads protocols/<name>.toml via @iarna/toml and
// validates against a zod schema mirror of protocols/_schema.toml. Returns a
// typed ProtocolSpec consumable by all downstream fetch/ modules.
//
// Per CLAUDE.md domain non-negotiables and CONTEXT.md Pattern 3
// (protocol-agnosticism): NO module under fetch/src/ may hard-code protocol
// names, factory addresses, fee tiers, or mixing-class enum values outside
// the values it loads from this module. The protocol-agnosticism test in
// Plan 01-05 enforces this with a grep over fetch/src/.
//
// Owned by Plan 01-01. Consumed by Plans 01-04 (Blockscout client),
// 01-05 (protocol-agnosticism test), 01-06 (dry-run / estimate-budget),
// 01-08 (CLI integration).

import { readFile } from 'node:fs/promises';
import TOML from '@iarna/toml';
import { z } from 'zod';

// ----------------------------------------------------------------------
// Primitive schemas
// ----------------------------------------------------------------------

const HexAddr = z
  .string()
  .regex(/^0x[0-9a-fA-F]{40}$/, 'must be a 0x-prefixed 20-byte hex address');

// Mirrors protocols/_schema.toml [enums].mixing_class.
const MixingClass = z.enum(['mento-native', 'minteo-fintech', 'mento-bridged']);

// Mirrors protocols/_schema.toml [enums].data_cost_class.
const DataCostClass = z.enum([
  'indexer-analytics-queries',
  'per-event-oracle-stretch',
  'per-scan-ocr-stretch',
]);

const AddressResolutionStatus = z.enum(['verified', 'pending']);

// ----------------------------------------------------------------------
// Composite schemas
// ----------------------------------------------------------------------

export const AnchorPoolSchema = z.object({
  address: HexAddr,
  token0: HexAddr,
  token1: HexAddr,
  fee_tier: z.number().int(),
  mixing_class: MixingClass,
  blockscout_url: z.string().url().optional(),
  swaps_per_30d_observed: z.number().int().nonnegative().optional(),
  above_hawkes_floor: z.boolean().optional(),
});

// pool_address is optional because Minteo-fintech vaults (e.g. COPM_minteo_vault_*
// in protocols/ichi.toml) wrap an `underlying_token` directly and do NOT deposit
// into a Uniswap V3 pool. M12 verified-before-fetch invariant for `active = true`
// vaults is the runtime guarantee that `pool_address` will be present when needed;
// the schema can't statically distinguish active from inactive rows without
// making the field a discriminated-union, which is overkill for v1.
export const VaultSchema = z.object({
  address: HexAddr,
  address_resolution_status: AddressResolutionStatus.optional(),
  active: z.boolean(),
  mixing_class: MixingClass,
  pool_address: HexAddr.optional(),
  underlying_token: HexAddr.optional(),
  reason: z.string().optional(),
  blockscout_url: z.string().url().optional(),
});

// The TOML file shape (matches the [protocol] table). We lift this out below
// so callers see a flat ProtocolSpec without the redundant [protocol] wrapper.
const ProtocolTableSchema = z.object({
  name: z.string(),
  chain_id: z.number().int(),
  factory_address: HexAddr,
  factory_blockscout_url: z.string().url().optional(),
  data_cost_class: DataCostClass,
  cost_leg_lower_bound_verified: z.boolean().optional(),
  panel_construction: z.string(),
  iteration: z.number().int(),
  cold_backfill_from_block: z.number().int().nonnegative().optional(),
  anchor_pool: AnchorPoolSchema,
  vaults: z.record(z.string(), VaultSchema).default({}),
});

export const ProtocolSpecSchema = z
  .object({
    protocol: ProtocolTableSchema,
  })
  .transform((raw) => ({
    // Lift the [protocol] table out so callers get a flat ProtocolSpec.
    ...raw.protocol,
  }));

export type ProtocolSpec = z.infer<typeof ProtocolSpecSchema>;
export type AnchorPool = z.infer<typeof AnchorPoolSchema>;
export type Vault = z.infer<typeof VaultSchema>;

// ----------------------------------------------------------------------
// Loader
// ----------------------------------------------------------------------

/**
 * Load and validate a protocol-spec TOML file.
 *
 * Throws if:
 *   - The file cannot be read
 *   - The TOML cannot be parsed (@iarna/toml error)
 *   - The shape does not conform to the schema (zod ZodError)
 *
 * The loader is intentionally protocol-agnostic: it does NOT inspect
 * `name` to dispatch behavior. Per CONTEXT.md Pattern 3, all downstream
 * code reads the returned ProtocolSpec uniformly.
 */
export async function loadProtocol(path: string): Promise<ProtocolSpec> {
  const text = await readFile(path, 'utf-8');
  const parsed = TOML.parse(text);
  return ProtocolSpecSchema.parse(parsed);
}
