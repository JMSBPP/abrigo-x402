---
phase: 00-candidate-eligibility-pre-registration
plan: 05
subsystem: infra
tags: [toml, protocol-spec, ichi, steer, mento, celo, schema-conformance]

# Dependency graph
requires:
  - phase: 00-candidate-eligibility-pre-registration
    provides: "Plan 00-02 PHASE_0_GATE.md (Steer REPRO-03 = STRADDLE verdict + marginal-demand flag at commit a669d37); Plan 00-03 Q9_DECISION.md (v3-anchor-only primary + numeric fallback triggers at commit 5782527); Plan 00-04 protocols/_schema.toml frozen baseline at commit e9b214d (per-vault address_resolution_status + active boolean + mixing_class enum)"
provides:
  - "protocols/ichi.toml — Iter-1 swap surface (cKES/USDT anchor active; 27-vault Celo footprint enumerated for AF-12 defense)"
  - "protocols/steer.toml — Iter-2 stub (cCOP/USDT anchor; STRADDLE verdict + marginal-demand flag propagated from PHASE_0_GATE.md; Q-9 v3-anchor-only primary + unified fallback metadata with numeric thresholds verbatim from Q9_DECISION.md)"
  - "L0 protocol-spec layer operationalized: GOV-03 (schema-frozen invariant at L0) + REPRO-04 (Q-9 decision encoded in swap-surface config) discharged"
affects:
  - "Plan 00-06: .pre-commit-config.yaml schema-frozen-check hook validates both TOMLs against _schema.toml enum structure"
  - "Plan 00-07: PHASE_0_GATE.md SCHEMA_BASELINE_COMMIT placeholder substitution unaffected (operates on PHASE_0_GATE.md only)"
  - "Phase 1 fetch infrastructure: 17 pending-status vault placeholders in ichi.toml require Phase-1 full ICHIVaultCreated factory-log pagination to resolve; Phase 2+ code MUST assert verified-before-fetch (M12)"
  - "Phase 2 analysis/src: must export build_v3_anchor_panel + build_unified_panel + cross_class_permutation_test signatures (REPRO-02 invariant); v3-anchor-only is the panel_construction flag the panel module reads"
  - "Iter-2 entire pipeline: hedge_05_fires=true at Phase 0 means Iter-2 never runs Phase 1-5 cycle; reports/steer_null_result.pdf emission at Phase 6 documents marginal-demand"

# Tech tracking
tech-stack:
  added: []  # No new libraries; TOML files only
  patterns:
    - "L0 protocol-spec config layer: per-protocol TOML files (ichi.toml, steer.toml) conform to frozen _schema.toml; substrate expansion = active-boolean toggle, never row addition (AF-12 defense)"
    - "REPRO-03 verdict propagation: PHASE_0_GATE.md → steer.toml [protocol.repro_03_verdict] structured block; Phase 6 reads this for confirmation, never to decide"
    - "Q-9 fallback pre-registration: numeric trigger thresholds embedded in steer.toml [protocol.q9_fallback] verbatim from Q9_DECISION.md; AF-03 spec-swap defense at the config layer"
    - "M12 address resolution: every vault row carries address_resolution_status ∈ {verified, pending}; pending paired with zero-address placeholder; Phase 2+ code asserts verified before fetch"

key-files:
  created:
    - "protocols/ichi.toml (299 lines, 27 vaults — 10 verified + 17 pending)"
    - "protocols/steer.toml (166 lines, 6 vaults — all verified)"
  modified: []

key-decisions:
  - "Task 1 enumeration deferred to documented fallback: CANDIDATES.md §3 + §4.1 + §5.5 primary-source LP-holder reads serve as the verified-address baseline. Full ICHIVaultCreated factory-log paginated retrieval requires Phase-1 fetch infrastructure (TypeScript x402-aware Blockscout client with cursor support)."
  - "Pending vaults uniformly use the canonical zero-address (0x0000...0000) per M12 strict acceptance criterion. Partial-prefix addresses from CANDIDATES.md §4.1 (e.g. '0x93e2...224B') are documented in the reason field for Phase-1 disambiguation, NOT inserted as pseudo-addresses (rejected the initial draft that tried to encode partial-prefixes as fake-zero-padded addresses)."
  - "steer.toml STRADDLE verdict embedded as a structured [protocol.repro_03_verdict] block (not just a string field) carrying result, flag, resolved_at_commit, channel A/B/C sources, and TVL-proportional vs vault-count-proportional bound synthesis. Phase 6 confirmatory check reads this block."
  - "hedge_05_fires = true encoded on steer.toml [protocol] block as a top-level boolean; documents at the L0 layer that Iter-2 fires HEDGE-05 memo-only null at Phase 0 (no Phase 1-5 cycle)."

patterns-established:
  - "AF-12 silent re-scope defense at L0: every known vault enumerated even if inactive in v1; substrate expansion in future iterations is `active = true/false` toggle on existing row, never new row addition. Schema-frozen-check (Plan 00-06) enforces _schema.toml immutability; planning-level 2-way review catches any new [protocol.vaults.NEW] additions outside an explicit re-planning loop."
  - "Verdict-propagation at config layer: Phase 0 governance markdown (PHASE_0_GATE.md, Q9_DECISION.md) → Phase 0 protocol-spec TOML structured blocks. Downstream phases READ the TOML, never the markdown directly, for verdict-conditioned branching logic. Commit hashes embedded in TOML for audit chain (a669d37 for STRADDLE; 5782527 for Q-9 thresholds)."
  - "M12 verified-before-fetch invariant: every vault row carries address_resolution_status. Phase 2+ fetch code asserts status='verified' before any RPC call. Pending placeholders are governance-only (Phase 0 enumeration), not operational targets."

requirements-completed:
  - GOV-03
  - REPRO-04

# Metrics
duration: 5min
completed: 2026-05-25
---

# Phase 0 Plan 05: Protocol-Spec TOMLs (ICHI Iter-1 + Steer Iter-2) Summary

**L0 protocol-spec layer operationalized: ichi.toml enumerates 27-vault Celo footprint (1 active anchor, 24 v2-deferred, 2 COPM minteo-fintech-deferred) for AF-12 defense; steer.toml embeds STRADDLE+marginal-demand verdict, v3-anchor-only panel construction, and Q-9 numeric fallback triggers verbatim from upstream governance.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-05-25T20:28:49Z
- **Completed:** 2026-05-25T20:34:35Z
- **Tasks:** 3 (Task 1 enumeration consumed by Task 2; Tasks 2+3 emitted committed artifacts)
- **Files modified:** 2 (both created)

## Accomplishments

- **(a) Total vault count enumerated in ichi.toml:** 27 rows (vs the ~40-vault factory-log total per CANDIDATES.md §4.1). Enumeration was PARTIAL — full ICHIVaultCreated factory-log paginated retrieval deferred to Phase-1 fetch infrastructure. 10 vault rows carry verified primary-source addresses from CANDIDATES.md §3 (per-pool LP-holder reads) + §5.5 (COPM Minteo vaults). 17 rows are pending placeholders with zero-address per M12 (includes 4 partial-prefix references from §4.1 documented in reason fields, plus 13 generic pending placeholders for known-but-unenumerated factory log positions).
- **(b) Steer REPRO-03 verdict propagated from PHASE_0_GATE.md:** STRADDLE (Celo-attributable Graph queries/mo in 30k-100k band). Verdict + flag = `marginal-demand` embedded as structured [protocol.repro_03_verdict] block including channel A/B/C source citations and TVL-proportional (8k-40k) vs vault-count-proportional (48k-240k) bound synthesis. resolved_at_commit = a669d37.
- **(c) cost_leg_lower_bound_verified flag:** `false` in both files. ichi.toml: false because v1 cost leg is modeled, not paid (no Celo facilitator in x402-foundation monorepo per CLAUDE.md). steer.toml: false because STRADDLE band includes the 100k/mo line — bound is not above it.
- **(d) address_resolution_status counts:** ichi.toml = 10 verified + 17 pending = 27 total. steer.toml = 6 verified + 0 pending = 6 total. Combined: 16 verified + 17 pending = 33 vault rows across both TOMLs. All pending rows use the canonical zero-address.
- **(e) Git commit hashes:** ichi.toml at `aa2fcc8` (feat scope); steer.toml at `24d054b` (feat scope).

## Task Commits

1. **Task 1: Enumerate ICHI Celo vault footprint** — no separate commit (output consumed by Task 2 per plan)
2. **Task 2: protocols/ichi.toml** — `aa2fcc8` (feat)
3. **Task 3: protocols/steer.toml** — `24d054b` (feat)

**Plan metadata:** to be committed after STATE.md + ROADMAP updates

## Files Created/Modified

- `protocols/ichi.toml` (299 lines) — Iter-1 swap surface; cKES/USDT anchor vault `0xe304b9...4176F` active; 24 vault rows v2-deferred; 2 COPM Minteo vaults v2-deferred with minteo-fintech mixing class; factory `0x9FAb4b...7418F`; data_cost_class=indexer-analytics-queries; panel_construction=single-vault (Q-4 microcosm)
- `protocols/steer.toml` (166 lines) — Iter-2 stub; cCOP/USDT anchor pool `0x2AC5ba...17B0`; factory `0x116Dba...014C`; panel_construction=v3-anchor-only; phase_0_repro_03_verdict=STRADDLE; phase_0_repro_03_flag=marginal-demand; hedge_05_fires=true; Q-9 fallback metadata with V4 PoolManager `0x288dc8...87BC`, Mento V2 Broker `0x777A82...4CaD`, sample_floor=300, ci_width_floor=0.4, permutation_reps=1000, p_threshold=0.05

## Decisions Made

1. **Task 1 documented-fallback path taken.** Plan Task 1's action block explicitly permits: "If enumeration is INCOMPLETE due to Blockscout pagination limits, document the gap with the count obtained and rely on CANDIDATES.md §3+§4.1 for the known set as the minimum required listing." The CANDIDATES.md primary-source LP-holder enumeration already covered the 10 most-relevant ICHI vault addresses (cKES/USDT anchor + 2 COPM + 7 other class representatives). Full factory-log pagination would consume Phase-1 budget and requires the TypeScript x402-aware Blockscout client with cursor-based pagination support. Documented in [enumeration_status] block with `enumeration_complete = false` and explicit `enumeration_gap_reason`. Acceptance criterion "At minimum 10 ICHI vault addresses identified" — PASS.

2. **Strict zero-address for pending placeholders.** First draft attempted to encode CANDIDATES.md §4.1 partial-prefix addresses (e.g. "0x93e2...224B") as pseudo-addresses by zero-padding the prefix. Plan acceptance criterion `pending vaults use zero-address` is strict — the assertion `vaults[k]['address'] == '0x0000000000000000000000000000000000000000'` failed on these pseudo-addresses. Auto-fix (deviation Rule 1 below): replaced all 7 pseudo-addresses with the canonical zero-address and moved the partial-prefix string into the reason field for Phase-1 disambiguation. This is the M12-compliant representation.

3. **Structured verdict block over flat field.** Plan Task 3 action block suggested a single string field `phase_0_repro_03_verdict = "..."`. Chose to additionally embed a structured `[protocol.repro_03_verdict]` block recording result, flag, channel-A/B/C source citations, demand-window bounds, TVL-proportional vs vault-count-proportional synthesis, and the resolved_at_commit hash. This makes Phase 6 (if launched) read the full verdict context atomically rather than re-deriving from PHASE_0_GATE.md.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Pending vault addresses violated M12 zero-address strict criterion**
- **Found during:** Task 2 (protocols/ichi.toml validation)
- **Issue:** First draft of ichi.toml encoded CANDIDATES.md §4.1 partial-prefix addresses (e.g. `"0x93e2...224B"`) as pseudo-addresses by left-padding/right-padding the partial hex (e.g. `0x93e224b00000000000000000000000000093e224`). The plan acceptance criterion is strict: `assert all(vaults[k]['address'] == '0x0000000000000000000000000000000000000000' for k in pending)`. Validation reported 7 pending vault rows with non-zero addresses.
- **Fix:** Replaced all 7 pseudo-addresses with the canonical zero-address `0x0000000000000000000000000000000000000000`. Moved the CANDIDATES.md §4.1 partial-prefix string into the `reason` field comment for Phase-1 disambiguation (e.g. `"address-pending-Phase-1-full-enumeration (CANDIDATES §4.1 lists partial-prefix '0x93e2...224B' only)"`). Updated [enumeration_status] verified_count from 11 to 10 and pending_count from 14 to 17 to match the corrected reality.
- **Files modified:** `protocols/ichi.toml`
- **Verification:** Re-ran the M12 strict assertion via tomllib — PASS. All 17 pending rows now equal the canonical zero-address.
- **Committed in:** `aa2fcc8` (Task 2 commit; fix folded into the same atomic commit before push)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** No scope creep. The fix restored strict M12 compliance and corrected the [enumeration_status] verified/pending tallies to match the corrected file state. All other plan acceptance criteria passed on first validation.

## Issues Encountered

None during planned work. Note: plan 00-06 commits were already present on the branch at execution start (parallel wave-2 sibling) — verified independent file scope (this plan touches only `protocols/ichi.toml` + `protocols/steer.toml`; plan 00-06 touches `.pre-commit-config.yaml` + `Makefile` + `scripts/pre-commit/`), no merge conflict.

## User Setup Required

None — no external service configuration. All artifacts are committed config files. The pre-commit hook that consumes _schema.toml + ichi.toml + steer.toml (`make schema-frozen-check`) is delivered by parallel Plan 00-06.

## Next Phase Readiness

**Ready for Wave-2 sibling completion + Wave-3 plan 00-07:**
- protocols/ichi.toml + protocols/steer.toml committed and schema-conformant
- 16 verified vault addresses across both TOMLs ready for Phase-1 fetch wiring
- 17 pending placeholders documented for Phase-1 ICHIVaultCreated factory-log full enumeration
- STRADDLE verdict + marginal-demand flag locked in steer.toml; Iter-2 confirmed memo-only-null at Phase 0; no Phase 1-5 cycle for Steer
- Q-9 numeric thresholds (300 / 0.4 / 1000 / 0.05) embedded verbatim from Q9_DECISION.md; AF-03 spec-swap defense active at L0
- AF-12 silent re-scope defense active: substrate expansion = boolean toggle on existing row, never row addition; reviewable by git-diff

**No blockers.** Plan 00-06 (parallel) delivers the schema-frozen-check hook that will validate both TOMLs against _schema.toml on future commits. Plan 00-07 substitutes the schema baseline commit hash into PHASE_0_GATE.md — independent of these TOMLs.

---
*Phase: 00-candidate-eligibility-pre-registration*
*Completed: 2026-05-25*

## Self-Check: PASSED

- protocols/ichi.toml: FOUND
- protocols/steer.toml: FOUND
- 00-05-SUMMARY.md: FOUND
- Commit aa2fcc8: FOUND (Task 2 ichi.toml)
- Commit 24d054b: FOUND (Task 3 steer.toml)
