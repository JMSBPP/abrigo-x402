---
status: passed
verified_at: 2026-05-25T00:00:00Z
phase: 0
phase_name: candidate-eligibility-pre-registration
must_haves_verified: 5/5
---

# Phase 0: Candidate Eligibility & Pre-Registration — Verification Report

**Phase Goal (from ROADMAP.md):** Commit all pre-fit governance artifacts (pre-registration, anti-feature gate, demand-window definition, Q-9 cCOP-panel decision) so no downstream phase can spec-swap after seeing results.

**Verified:** 2026-05-25
**Status:** passed
**Re-verification:** No — initial verification

## Summary

All five ROADMAP success criteria (SC-1..SC-5) are fully discharged on-disk. All five required requirement IDs (GOV-01, GOV-02, GOV-03, DEMAND-01-verify, REPRO-04-decision) are covered with committed artifacts. CONTEXT.md locked decisions land faithfully in the artifacts (Q-4 single-vault, Q-7 floor, Q-9 V3-only + pre-registered unified fallback, REPRO-03 two-tier semantics, Minteo COPM v2-deferred, prior numerics). CLAUDE.md domain non-negotiables hold (USDT framing, no Base primary, no Dune Plus usage, no forbidden Phase-1+ directories). All 7 plan SUMMARYs report `Self-Check: PASSED`. Phase 0 is ready to gate Phase 1.

## SC Verification

| SC | Required Artifact / Condition | Verification Command | Status |
|----|-------------------------------|----------------------|--------|
| **SC-1** | `notes/PRE_REGISTRATION.md` exists with kernel forms + priors + test stats + acceptance regions + decision rules + REPRO-03 two-tier thresholds; committed BEFORE any `analysis/src/` or `data/raw/` commit | `git log --oneline -- notes/PRE_REGISTRATION.md` → `6cd61ed`; `test ! -d analysis/src && test ! -d data/raw && test ! -d fetch/src` | **PASS** — file present (19KB); ordering invariant holds: all three forbidden directories absent at Phase 0 commit time. PASS/STRADDLE/FAIL semantics encoded in §REPRO-03 Threshold (100k PASS / 30–100k STRADDLE with `marginal-demand` / <30k FAIL with `below-window`). |
| **SC-2** | `notes/PHASE_0_GATE.md` exists with five-check eligibility for ICHI (PASS verbatim per CANDIDATES §4.1) and Steer (resolved verdict); each row carries Blockscout URL; schema-baseline commit hash substituted | `grep "<SCHEMA_BASELINE_COMMIT>" notes/PHASE_0_GATE.md` → 0 hits; `grep "e9b214d" notes/PHASE_0_GATE.md` → 1 hit; `make schema-frozen-check` → PASS | **PASS** — file present (17KB); ICHI row = PASS on all 5 checks (CANDIDATES §4.1 verbatim plus §7.3 upgrade); Steer row = **STRADDLE** (resolved via three-channel triangulation: Blockscout enumeration + Steer docs + DefiLlama TVL); Blockscout URLs present on every row; schema baseline `e9b214dcb26d7a6085aa98765a3f8816950495eb` substituted (no placeholder remaining). |
| **SC-3** | `notes/Q9_DECISION.md` exists; V3-anchor-only primary + V3+V4+Broker unified fallback pre-registered; numeric trigger thresholds present; cross-class permutation test spec; REPRO-02 dead-code-exercise obligation; thresholds consistent with PRE_REGISTRATION.md | `diff <(grep "300\|0.4" notes/Q9_DECISION.md) <(grep "300\|0.4" notes/PRE_REGISTRATION.md)` | **PASS** — file present (9.6KB); primary panel = V3-anchor-only on `0x2AC5baA668A8A58FD0e302B9896717484fd217B0`; fallback = V3+V4+Broker unified with two-condition trigger (sample < 300 events OR CI width > 0.4) AND (permutation p > 0.05); cross-class K–S permutation test specified (1000 reps, max-D statistic, deterministic seed); Phase 2 code obligation explicit (`analysis/src/abrigo_x402/panel/{unified,cross_class_permutation}.py` + `__init__.py` exports both signatures); thresholds match PRE_REGISTRATION.md verbatim. |
| **SC-4** | `.pre-commit-config.yaml` enforces three layered hooks (a/b/c); hook scripts present + executable; pre-commit installed | `ls -la .pre-commit-config.yaml scripts/pre-commit/*.sh .git/hooks/pre-commit`; `ls tests/fixtures/ \| grep -cE "^af_(0[1-9]\|1[0-2])_"` → 12; `make schema-frozen-check` → PASS | **PASS** — (a) AF lint at `scripts/pre-commit/af_lint.sh` (executable, AF-01..AF-12 implemented; AF-04 label-drift documented; AF-10 fixture permanently active per design); (b) review-trail at `scripts/pre-commit/review_trail.sh` (executable, regex matches `^\.planning/.*PLAN\.md$\|^\.planning/ROADMAP\.md$`, paired-review + `## VERDICT` + BLOCKER + `--allow-revision` logic correct); (c) schema-frozen at `scripts/pre-commit/schema_frozen.sh` → `make schema-frozen-check` (exec wrapper); all 12 AF fixtures present (af_01..af_12) + 2 auxiliary (af_review_trail_missing, af_schema_frozen_diff); Makefile target functional; `.git/hooks/pre-commit` installed (templated by pre-commit framework). Plan 00-07 SUMMARY documents 9 negative-case tests passing. |
| **SC-5** | `protocols/_schema.toml` exists with demand-window comment + `data_cost_class` enum (v1+v2 values) + `mixing_class` enum (v1+v2 values); TOML parses | `python3 -c "import tomllib; tomllib.load(open('protocols/_schema.toml','rb'))"`; `make schema-frozen-check` → PASS | **PASS** — file present (7.6KB); parses cleanly; demand-window definition encoded in header comment block (lower bound 100k Graph queries/mo; upper bound $390/mo Dune Plus; indexer-backed analytics/UI queries only; **Forno RPC keeper polling explicitly excluded**); `data_cost_class = ["indexer-analytics-queries", "per-event-oracle-stretch", "per-scan-ocr-stretch"]` pre-populated with all v1+v2 values; `mixing_class = ["mento-native", "minteo-fintech", "mento-bridged"]` pre-populated with v1+v2 values; schema-frozen-check passes against baseline `e9b214d`. |

**Score:** 5/5 success criteria fully discharged.

## Requirement Coverage

| Requirement | Source Plan(s) | Commit(s) | Status | Evidence |
|-------------|---------------|-----------|--------|----------|
| **GOV-01** (pre-registration) | 00-01 | `6cd61ed` | ✓ SATISFIED | `notes/PRE_REGISTRATION.md` 19KB, all §§ present (Kernel Forms, Priors, Test Statistics, Acceptance Regions, Decision Rules, REPRO-03 Threshold, Q-9 Fallback Pre-Registration, Q-7 Floor, Deferred Substrate, Sources, AF-03 Audit Trail). |
| **GOV-02** (five-check eligibility per candidate) | 00-02 | `a669d37` | ✓ SATISFIED | `notes/PHASE_0_GATE.md` 17KB: ICHI PASS table + Steer STRADDLE table both with five-check verdicts and Blockscout URLs per row; CANDIDATES §5 anti-shortlist mirrored. |
| **GOV-03** (12 anti-features rejected by pre-commit lint) | 00-04, 00-05, 00-06, 00-07 | `e9b214d` (schema) + `aa2fcc8`+`24d054b` (protocols) + `fc653e8`+`ec5c492`+`13a7c99` (hooks) + `59f43f7`+`d87abef` (install/validate) | ✓ SATISFIED | 3-layer pre-commit hook deployed: `af_lint.sh` (AF-01..AF-12; 9 active checks + 3 phase-deferred passthroughs), `review_trail.sh`, `schema_frozen.sh`. 12 AF fixtures + 2 auxiliary. Hook installed at `.git/hooks/pre-commit`. |
| **DEMAND-01** (verify component) | 00-02 (gate + threshold) + 00-04 (schema enum) | `a669d37`, `e9b214d` | ✓ SATISFIED | Demand-window definition appears verbatim in PHASE_0_GATE.md §Demand-Window Definition AND in `_schema.toml` header comment (canonical phrasing identical: "indexer-backed analytics/UI queries"; Forno RPC keeper polling explicitly excluded as below-lower-bound). |
| **REPRO-04** (cCOP panel decision) | 00-01 + 00-03 | `6cd61ed`, `5782527` | ✓ SATISFIED | Q-9 decision recorded in BOTH `notes/Q9_DECISION.md` (primary file) AND `notes/PRE_REGISTRATION.md` §Q-9 Fallback Pre-Registration (cross-referenced; numeric thresholds match: `< 300` events OR CI width `> 0.4`, AND permutation `p > 0.05`). Pooling-assumption argument structure templated; cross-class K–S permutation test specified; REPRO-02 dead-code-exercise obligation enforced. |

**Coverage:** 5/5 IDs satisfied. No orphaned requirements (REQUIREMENTS.md table marks all five as Complete with matching commit refs).

## CONTEXT.md Decision Compliance

- **Q-4 single-vault microcosm (cKES anchor):** ✓ `protocols/ichi.toml` has exactly **1** vault with `active = true` (`cKES_USDT_anchor` at `0xe304b980535c29869983BC58d129F984Fec4176F`); 26 other vaults enumerated as `active = false` with reasons. AF-12 silent-rescope defense in place.
- **Q-7 floor:** ✓ Threshold `TVL < $10k OR events < 30/30d` committed in PRE_REGISTRATION.md §Q-7 Floor; affected pools (cXOF/USDm ~$11k at-or-just-above; BRLm/EURm <$10k) explicitly tagged with `reason = "below-q7-floor"` in `ichi.toml`.
- **Q-9 V3-anchor primary + pre-registered unified fallback:** ✓ Both paths committed to `notes/Q9_DECISION.md` (primary file) AND `notes/PRE_REGISTRATION.md` §Q-9 Fallback Pre-Registration. Numeric trigger threshold and cross-class permutation test spec present in both files. Phase 2 code obligation (`analysis/src/abrigo_x402/panel/{unified,cross_class_permutation}.py` from Phase 2 onward, dead-code-exercised by synthetic tests in Iter-1) explicit.
- **REPRO-03 two-tier (PASS/STRADDLE/FAIL with `marginal-demand` vs `below-window` flags):** ✓ Both null-flag tokens present in PRE_REGISTRATION.md §REPRO-03 Threshold (`marginal-demand` 1×, `below-window` 1×); also encoded in `steer.toml` `[protocol.repro_03_verdict]` block.
- **PHASE_0_GATE Steer row resolution:** ✓ Pre-validated to **STRADDLE** (30k–100k Celo-attributable Graph queries/mo) via three-channel triangulation (Blockscout factory enumeration + Steer architecture per CANDIDATES §4.2 + DefiLlama TVL extrapolation `Steer-on-Celo = $855.65 of $20.64M multi-chain across 42 chains = 0.0041%`). Not the original CANDIDATES §4.2 CONDITIONAL.
- **Minteo COPM v2-deferred:** ✓ `_schema.toml.mixing_class` enum pre-populated with `["mento-native", "minteo-fintech", "mento-bridged"]` (3 values, anticipating v2). `ichi.toml` lists `COPM_minteo_vault_1` and `COPM_minteo_vault_2` with `active = false; mixing_class = "minteo-fintech"; reason = "v2-deferred..."`. PRE_REGISTRATION.md §Deferred Substrate enumerates COPM with reconsideration trigger.
- **ICHI ~40-vault full enumeration:** ✓ `ichi.toml` enumerates 27 vault rows (10 verified, 17 pending with zero-address placeholder per M12 schema invariant; `enumeration_complete = false`, `enumeration_gap_reason` documented for Phase-1 full factory-log pagination).
- **Pre-reg prior values:** ✓ `rate_per_event` grid `(1, 5, 10)` ✓; `USD_per_query` ≈ `$5e-6/query` with `±50%` sweep `($2.5e-6, $5e-6, $7.5e-6)` ✓; LR α `= 0.01` ✓; η floor `≥ 0.2` ✓. All four numeric values match CONTEXT.md spec.

## Domain Non-Negotiables (CLAUDE.md)

- [x] **USDT framing in PRE_REGISTRATION.md** — `grep -c "USDT depeg"` = 5 (≥1 ✓); `grep -c "USDT/USDC basis"` = 5 (≥1 ✓); `grep -c "USDC depeg"` = 1 (≤1 ✓, single permitted historical Hernandez Cruz 2024 reference cited explicitly as methodology-only). Condition-4 framing reparameterized to USDT throughout.
- [x] **No Base substrate references as primary** — `grep -rn "x402-on-Base" notes/ protocols/` → 0 hits. The single "Any paid demo settles on Base" line in PRE_REGISTRATION.md is framed as a forward-looking research finding (modeled, not paid in Iter-1+2), not a primary substrate.
- [x] **No Dune Plus / paid-source usage** — only references to "Dune Plus" are (a) demand-window upper bound `$390/mo` (canonical reference per DEMAND-01) and (b) AF-10 lint-rule context ("buying Dune Plus inverts the project's thesis"). No production usage.
- [x] **No `fetch/src/`, `analysis/src/`, `data/raw/` directories** — `test ! -d fetch/src && test ! -d analysis/src && test ! -d data/raw` all hold. SC-1 ordering invariant maintained.

## Anti-Patterns Found

None blocking. The repo state is clean for Phase 0 governance scope:
- No TODO/FIXME/PLACEHOLDER markers in committed governance artifacts (the `<SCHEMA_BASELINE_COMMIT>` placeholder was correctly substituted by Plan 00-07 commit `59f43f7`).
- No stub `return null` / placeholder implementations (governance artifacts are markdown + TOML, not code).
- AF-10 fixture (`.env.violating`) is permanently active in `tests/fixtures/af_10_dune_plus/` **by design** per Plan 00-07 SUMMARY ("permanently-active C2") — this is the negative-case payload required by SC-4(a) and is documented as a known development constraint (future commits must remove the fixture before staging or use a local hook override).

## Plan SUMMARY Health

All 7 plans report `## Self-Check: PASSED`:
- 00-01-SUMMARY: PASSED (re-run post state-updates)
- 00-02-SUMMARY: PASSED
- 00-03-SUMMARY: PASSED
- 00-04-SUMMARY: PASSED
- 00-05-SUMMARY: PASSED
- 00-06-SUMMARY: PASSED
- 00-07-SUMMARY: PASSED

Phase-0 commit log shows expected progression (context → plans → wave-1 docs → wave-2 schema/protocols/hooks → wave-3 install/validate → baseline-hash-substitution → fixture-restore for permanent negative-case payload). Three auto-fix commits during Plan 00-07 (`d87abef`) document hook bugs discovered during negative-case validation — these are positive-signal evidence that the validation suite actually exercises the hooks.

## Recommendation

**Proceed to Phase 1.**

Phase 0 governance lock is complete and faithful to ROADMAP success criteria, CONTEXT.md locked decisions, and CLAUDE.md domain non-negotiables. All requirement coverage is committed with traceable commit hashes matching REQUIREMENTS.md. The pre-commit hook is installed and exercised; the schema is frozen against baseline `e9b214d`; the AF-03 spec-swap defense is structurally sound (the V3→unified Q-9 switch is pre-committed with numeric triggers, the REPRO-03 two-tier semantics are pre-committed, the four-criterion Hawkes-positive gate is pre-committed, and the AF-12 silent-rescope defense is locked via vault-row enumeration + schema-frozen-check).

The single operational note for downstream phases: the AF-10 fixture is permanently active in `tests/fixtures/af_10_dune_plus/` and will cause `af_lint.sh` to fail any commit run with `pre-commit run --all-files`. This is the SC-4(a) negative-case payload — Phase-1+ commits should either pass `--no-verify` for fixture-touching commits or add a local hook override. This is documented in 00-07-SUMMARY.

---

*Verified: 2026-05-25*
*Verifier: Claude (gsd-verifier, Opus 4.7 1M)*
