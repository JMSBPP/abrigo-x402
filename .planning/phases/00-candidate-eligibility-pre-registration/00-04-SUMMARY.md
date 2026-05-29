---
phase: 00-candidate-eligibility-pre-registration
plan: 04
subsystem: infra
tags: [toml, schema, governance, demand-window, schema-frozen, af-12, gov-03, demand-01]

# Dependency graph
requires:
  - phase: 00-candidate-eligibility-pre-registration
    provides: "L0 protocol-spec TOML layer pattern from research/ARCHITECTURE.md"
provides:
  - "protocols/_schema.toml — frozen schema baseline for all protocol-spec TOML files"
  - "data_cost_class enum pre-populated for v1+v2 (indexer-analytics-queries / per-event-oracle-stretch / per-scan-ocr-stretch)"
  - "mixing_class enum pre-populated for v1+v2 (mento-native / minteo-fintech / mento-bridged)"
  - "Demand-window scope locked at schema layer (indexer-backed analytics/UI queries ONLY; Forno RPC EXPLICITLY EXCLUDED)"
  - "Per-vault schema with active boolean + reason string + address_resolution_status enum (AF-12 silent-re-scope defense)"
  - "SCHEMA_BASELINE_COMMIT hash for Plan 00-06 (make schema-frozen-check) and Plan 00-07 (PHASE_0_GATE.md substitution)"
affects:
  - "00-05-PLAN (protocols/ichi.toml — Iter-1 swap surface, consumes vault enumeration schema)"
  - "00-06-PLAN (.pre-commit-config.yaml + make schema-frozen-check — references this commit hash)"
  - "00-07-PLAN (notes/PHASE_0_GATE.md — substitutes <SCHEMA_BASELINE_COMMIT> placeholder with this commit hash)"
  - "Phase 2+ (fetch/ + analysis/ load protocols/*.toml against this schema via zod/pydantic mirrors)"

# Tech tracking
tech-stack:
  added:
    - "TOML schema layer (Python tomllib stdlib parser)"
  patterns:
    - "L0 protocol-spec TOML as single-source-of-truth (ARCHITECTURE.md Pattern 1)"
    - "Schema-frozen invariant via commit-hash baseline (AF-12 silent re-scope defense at schema layer)"
    - "Enum pre-population at v1+v2 horizon (no schema diff required when adding protocols)"
    - "Per-vault active-flag toggle instead of row addition (substrate moves are git-diff-visible)"

key-files:
  created:
    - "protocols/_schema.toml"
  modified: []

key-decisions:
  - "data_cost_class enum frozen at three v1+v2 values: indexer-analytics-queries (v1 ICHI + Steer), per-event-oracle-stretch (v2 prediction markets / Reality.eth), per-scan-ocr-stretch (v2 Halo-class OCR — historical class kept for v2 reactivation)"
  - "mixing_class enum frozen at three v1+v2 values: mento-native (v1 active — cKES/cCOP/cNGN/cGHS/cZAR/cXOF/BRLm), minteo-fintech (v1 deferred / v2 candidate — Minteo COPM 0xC92E8Fc...), mento-bridged (v2 anticipated — cross-chain BRLm if ever issued)"
  - "Demand-window scope DEMAND-01 encoded as comment block: indexer-backed analytics/UI queries ONLY. Forno RPC eth_call keeper polling EXPLICITLY EXCLUDED — free at any volume on Forno SLA, therefore below the demand window's lower bound at any scale, therefore wrong demand class. x402 settlement gas modeled-not-paid in v1 per CLAUDE.md non-negotiable (no Celo facilitator in x402-foundation monorepo as of 2026-05-25)"
  - "AF-12 silent-re-scope defense baked into vault schema: substrate moves expressed ONLY as active=true|false toggles on existing rows. Row additions to a frozen iteration require a new schema commit (which fails make schema-frozen-check), forcing an explicit re-planning loop"
  - "address_resolution_status enum (verified|pending) added to per-vault schema — Phase 2+ code asserts active=true vaults have status=verified before any fetch (M12 placeholder-vault defense)"
  - "[schema_documentation] block carries canonical-truths: chain_id=42220, canonical Celo USDT 0x48065fbBE25f71C9282ddf5e1cD6D6A887483D5e, celo_block_time_seconds=1.0 (post-2024-hardfork — anchors PITFALLS §1 sample-thinness retraction), demand-window bounds 100k Graph queries/mo lower + 390 USD/mo Dune Plus upper"

patterns-established:
  - "L0 protocol-spec TOML schema-first: every protocols/<name>.toml file is constrained by _schema.toml comment-documented schema; zod + pydantic mirrors load against the same enum constants"
  - "Schema-frozen commit-hash baseline: the commit hash of the Phase-0 _schema.toml commit is the immutable reference point for pre-commit hook (c); any later diff is rejected"
  - "Enum-pre-population pattern: every enum field on a frozen-schema file MUST be populated with all v1+v2+v∞ anticipated values at the freeze-commit moment; adding a value later is a schema-frozen-check violation, not an iteration-routine task"

requirements-completed:
  - DEMAND-01
  - GOV-03

# Metrics
duration: 4min
completed: 2026-05-25
---

# Phase 0 Plan 04: protocols/_schema.toml Frozen Baseline Summary

**Frozen-schema L0 protocol-spec TOML committed at `e9b214d` with data_cost_class + mixing_class enums pre-populated for v1+v2, demand-window scope (indexer-backed analytics/UI queries only; Forno RPC excluded) locked in comment block, and per-vault active-toggle schema defending AF-12 silent re-scope.**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-05-25T20:20:09Z
- **Completed:** 2026-05-25T20:25:00Z (approx)
- **Tasks:** 1
- **Files modified:** 1 (created)

## Accomplishments

- `protocols/_schema.toml` authored (125 lines, > 60-line floor; parses cleanly via Python tomllib 3.11+ stdlib)
- `data_cost_class` enum pre-populated with all three v1+v2 anticipated values: `["indexer-analytics-queries", "per-event-oracle-stretch", "per-scan-ocr-stretch"]`
- `mixing_class` enum pre-populated with all three v1+v2 anticipated values: `["mento-native", "minteo-fintech", "mento-bridged"]`
- Demand-window definition locked in top-of-file comment block (DEMAND-01): scope = indexer-backed analytics/UI queries ONLY; lower bound = 100k Graph queries/mo; upper bound = $390/mo Dune Plus; Forno RPC eth_call keeper polling EXPLICITLY EXCLUDED
- Per-vault schema documented with `active` boolean + `mixing_class` enum + `reason` string + `address_resolution_status` enum (verified|pending) — AF-12 silent-re-scope defense at schema layer, M12 placeholder-vault defense at fetch layer
- `[schema_documentation]` block records version 1.0.0, locked_at_phase, canonical Celo chain_id 42220, canonical Celo USDT address, celo_block_time_seconds = 1.0 (post-2024-hardfork)
- Atomic commit at `e9b214d` (full SHA `e9b214dcb26d7a6085aa98765a3f8816950495eb`) — this is the **SCHEMA_BASELINE_COMMIT** that Plan 00-07 substitutes into `notes/PHASE_0_GATE.md` `<SCHEMA_BASELINE_COMMIT>` placeholder, and Plan 00-06 references in `make schema-frozen-check`

## Task Commits

1. **Task 1: Author protocols/_schema.toml with pre-populated enums and demand-window comment block** — `e9b214d` (feat)

**SCHEMA_BASELINE_COMMIT (full SHA):** `e9b214dcb26d7a6085aa98765a3f8816950495eb`
**SCHEMA_BASELINE_COMMIT (short):** `e9b214d`

_This is the value Plan 00-07 substitutes into `notes/PHASE_0_GATE.md` `<SCHEMA_BASELINE_COMMIT>` placeholder._

## Files Created/Modified

- `protocols/_schema.toml` — L0 protocol-spec TOML schema layer (125 lines). Defines enums (data_cost_class, mixing_class), per-protocol schema (in comments — TOML doesn't natively support schema-of-schemas, so the schema is human-readable + grep-auditable), and [schema_documentation] metadata block. Frozen after this commit.

## Decisions Made

### Final enum value lists (locked at Phase 0)

**`[enums.data_cost_class]`:**
- `"indexer-analytics-queries"` — v1: Graph subgraph reads for analytics/UI (ICHI cost leg Iter-1, Steer cost leg Iter-2)
- `"per-event-oracle-stretch"` — v2 anticipated: per-event on-chain oracle reads (prediction markets, Reality.eth-class)
- `"per-scan-ocr-stretch"` — v2 anticipated: per-document OCR backend calls (Halo-class receipt OCR — historical class kept for v2 reactivation)

**`[enums.mixing_class]`:**
- `"mento-native"` — v1 active: Mento Reserve-backed local stables (cKES, cCOP, cNGN, cGHS, cZAR, cXOF, BRLm)
- `"minteo-fintech"` — v1 deferred / v2 candidate: Minteo COPM and similar fintech-issued local-stable clones (Celo address `0xC92E8Fc...`)
- `"mento-bridged"` — v2 anticipated: bridged variants of Mento stables (e.g. cross-chain BRLm if ever issued)

### Additional schema fields added beyond the planned minimum

The plan minimum required: `active`, `mixing_class`, `address`, `reason`, `address_resolution_status`. The committed schema additionally documents:

- **`[protocol]` block:** `name`, `chain_id`, `factory_address`, `data_cost_class`, `cost_leg_lower_bound_verified` (REPRO-03 Phase-0 pre-validation flag for Steer), `panel_construction` (Q-9 V3-only vs unified vs single-vault — matches `notes/Q9_DECISION.md` taxonomy)
- **`[protocol.anchor_pool]` block:** `address`, `token0`, `token1`, `fee_tier`, `mixing_class` (the headline LP venue per protocol — supports Uniswap V3 anchor pool reasoning across ICHI Iter-1 and Steer Iter-2)
- **`[protocol.vaults.<vault_id>]` block:** `address`, `address_resolution_status`, `active`, `mixing_class`, `pool_address`, `reason` (per-vault granularity for ICHI ~40-vault enumeration + Steer-vault enumeration)
- **`[schema_documentation]` block:** `version` (1.0.0), `locked_at_phase`, `last_modified` (2026-05-25), `contract_addresses_verified_via` (Blockscout v2 REST endpoint), `demand_window_lower_bound`, `demand_window_upper_bound`, `canonical_celo_chain_id` (42220), `canonical_celo_usdt` (0x48065fbBE25f71C9282ddf5e1cD6D6A887483D5e), `celo_block_time_seconds` (1.0), `celo_block_time_source` (Forno primary-source verification 2026-05-25; anchors PITFALLS §1 sample-thinness retraction)

All additions are forward-compatible with v2 substrate broadening and required for Phase-2+ fetch/analysis code to load protocol-spec TOMLs without ambiguity.

### Verification of acceptance criteria

All 20 acceptance criteria from the plan pass:
- `test -f protocols/_schema.toml` → exit 0
- `python3 -c "import tomllib; tomllib.load(open('protocols/_schema.toml', 'rb'))"` → exit 0 (TOML valid; top-level keys = `['enums', 'schema_documentation']`)
- All 3 `data_cost_class` enum values present (asserted via tomllib)
- All 3 `mixing_class` enum values present (asserted via tomllib)
- `grep -c "indexer-backed analytics/UI queries" protocols/_schema.toml` → 1 (DEMAND-01 scope language)
- `grep -c "Forno RPC" protocols/_schema.toml` → 1 (explicit exclusion)
- `grep -c "EXPLICITLY EXCLUDED" protocols/_schema.toml` → 1
- `grep -c "100,000" protocols/_schema.toml` → 1; `grep -c "100000" protocols/_schema.toml` → 1 (free-tier lower bound)
- `grep -c "390" protocols/_schema.toml` → 3 (Dune Plus upper bound)
- `grep -c "AF-12" protocols/_schema.toml` → 3 (silent re-scope defense documented)
- `grep -c "DEMAND-01" protocols/_schema.toml` → 1
- `grep -c "GOV-03" protocols/_schema.toml` → 1
- `grep -c "active" protocols/_schema.toml` → 6
- `grep -c "mixing_class" protocols/_schema.toml` → 4 (enum def + per-pool + per-vault occurrences)
- `grep -c "0x48065fbBE25f71C9282ddf5e1cD6D6A887483D5e" protocols/_schema.toml` → 1 (canonical Celo USDT)
- `grep -c "celo_block_time_seconds" protocols/_schema.toml` → 1
- `grep -c "address_resolution_status" protocols/_schema.toml` → 2 (M12)
- `wc -l protocols/_schema.toml` → 125 (≥ 60 floor)
- `git log --oneline -- protocols/_schema.toml` → 1 commit (`e9b214d`)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added lowercase "indexer-backed analytics/UI queries" phrasing to demand-window comment**
- **Found during:** Task 1 (acceptance-criteria verification)
- **Issue:** The plan's comment-block template used only UPPERCASE phrasing `INDEXER-BACKED ANALYTICS/UI QUERIES ONLY`, but acceptance criterion required `grep -c "indexer-backed analytics/UI queries" protocols/_schema.toml >= 1` (case-sensitive lowercase). The plan's `key_links` frontmatter pattern `"indexer.backed|indexer-backed"` confirmed lowercase grep is the canonical audit form.
- **Fix:** Added an inline canonical-phrasing line under the uppercase header: `# Canonical phrasing (lowercase, for downstream grep audits):\n#   scope = indexer-backed analytics/UI queries`
- **Files modified:** `protocols/_schema.toml`
- **Verification:** `grep -c "indexer-backed analytics/UI queries" protocols/_schema.toml` → 1; TOML still parses cleanly via tomllib
- **Committed in:** `e9b214d` (Task 1 commit — applied before commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minimal — restored grep-auditability of the demand-window scope phrasing without altering schema structure or semantics. No scope creep.

## Issues Encountered

None — schema authored in one pass; only the case-sensitivity grep mismatch surfaced during verification and was resolved before commit.

## User Setup Required

None — no external service configuration required for this plan. The schema file is pure governance/configuration artifact.

## Next Phase Readiness

- **Plan 00-05 (protocols/ichi.toml):** Ready. The schema is now stable; ichi.toml can populate `[protocol]` + `[protocol.anchor_pool]` + `[protocol.vaults.<id>]` rows against the documented schema without needing to edit `_schema.toml`.
- **Plan 00-06 (.pre-commit-config.yaml + make schema-frozen-check):** Ready. The `make schema-frozen-check` target should diff `protocols/_schema.toml` against the SCHEMA_BASELINE_COMMIT `e9b214dcb26d7a6085aa98765a3f8816950495eb` and reject any non-empty diff.
- **Plan 00-07 (notes/PHASE_0_GATE.md):** Ready. Substitute the `<SCHEMA_BASELINE_COMMIT>` placeholder with `e9b214dcb26d7a6085aa98765a3f8816950495eb` (full SHA) or `e9b214d` (short SHA) — preference for full SHA in the locked governance artifact.
- **No blockers for downstream wave-1 parallel plans (00-01, 00-02, 00-03) or wave-2 dependents (00-05, 00-06).**

## Self-Check: PASSED

- `[x] protocols/_schema.toml` exists (verified `test -f`)
- `[x]` TOML parses cleanly via Python tomllib (verified `python3 -c "import tomllib; tomllib.load(...)"`)
- `[x]` All 3 `data_cost_class` enum values present (verified via tomllib assertion)
- `[x]` All 3 `mixing_class` enum values present (verified via tomllib assertion)
- `[x]` Demand-window comment block present (verified via grep `indexer-backed analytics/UI queries` → 1, `EXPLICITLY EXCLUDED` → 1, `Forno RPC` → 1)
- `[x]` Per-vault schema fields present (verified via grep `active` → 6, `mixing_class` → 4, `address_resolution_status` → 2)
- `[x]` `[schema_documentation]` block fields present (verified via grep `celo_block_time_seconds` → 1, canonical USDT address → 1)
- `[x]` ≥ 60 lines (verified `wc -l` → 125)
- `[x]` Commit exists (verified `git log --oneline -- protocols/_schema.toml` → `e9b214d`)
- `[x]` SCHEMA_BASELINE_COMMIT recorded in this SUMMARY for Plan 00-07 substitution: `e9b214dcb26d7a6085aa98765a3f8816950495eb`

---

*Phase: 00-candidate-eligibility-pre-registration*
*Plan: 04*
*Completed: 2026-05-25*
