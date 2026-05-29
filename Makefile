# Makefile — abrigo-x402
#
# Phase 0 targets: schema-frozen-check
# Phase 6+ forward-looking targets: leak-check, iteration-2-full (stubs)

.PHONY: schema-frozen-check leak-check verify-reproducibility help \
        fetch-ichi lint-artifacts verify-cache-idempotency schema-probe \
        render-lr-diagnostic render-null-result-pdf render-strip-diagnostic \
        phase-4-acceptance report-ichi

help:
	@echo "Available targets:"
	@echo "  schema-frozen-check     - reject any diff to protocols/_schema.toml after the Phase-0 baseline commit"
	@echo "  leak-check              - reject protocol-name branches, factory-addr literals, magic fee tiers in fetch/src"
	@echo "  schema-probe            - probe whether adding [subgraphs.uniswap_v3] to ichi.toml trips schema-frozen-check"
	@echo "  fetch-ichi              - run ICHI fetch CLI (Phase 1 SC-2 implementation lands in Plan 01-04)"
	@echo "  lint-artifacts          - PANEL-02 metadata header lint (Phase 2 implementation)"
	@echo "  verify-cache-idempotency - rerun fetch twice and assert byte-identical parquet (FETCH-04)"
	@echo "  verify-reproducibility  - (Phase 5 forward-looking) verify reports/MANIFEST.md checksums"
	@echo "  render-lr-diagnostic    - re-render reports/_diagnostics/lr_null_dist.png (Phase 3 SC-3 diagnostic)"

# Phase 0 SC-4(c) — invoked by .pre-commit-config.yaml hook (c)
# Reads the baseline commit hash from notes/PHASE_0_GATE.md and rejects
# any diff against protocols/_schema.toml since that commit.
schema-frozen-check:
	@BASELINE=$$(grep -oE 'Schema baseline commit:\*\* `[a-f0-9]{7,40}`' notes/PHASE_0_GATE.md 2>/dev/null | grep -oE '[a-f0-9]{7,40}' | head -1); \
	if [ -z "$$BASELINE" ] || [ "$$BASELINE" = "SCHEMA_BASELINE_COMMIT" ]; then \
		echo "schema-frozen-check: WARNING — baseline commit not yet recorded in notes/PHASE_0_GATE.md (Plan 07 substitutes the hash)"; \
		echo "schema-frozen-check: deferring to a no-op until Plan 07 records the baseline; allow this commit"; \
		exit 0; \
	fi; \
	if git rev-parse --verify $$BASELINE >/dev/null 2>&1; then \
		DIFF=$$(git diff $$BASELINE -- protocols/_schema.toml 2>/dev/null); \
		if [ -n "$$DIFF" ]; then \
			echo "schema-frozen-check: FAIL — protocols/_schema.toml has diverged from baseline $$BASELINE"; \
			echo "$$DIFF"; \
			echo "schema-frozen-check: AF-12 silent re-scope defense — schema changes require explicit re-planning loop"; \
			exit 1; \
		fi; \
		echo "schema-frozen-check: PASS — protocols/_schema.toml unchanged since baseline $$BASELINE"; \
	else \
		echo "schema-frozen-check: ERROR — baseline commit $$BASELINE not found in git history"; \
		exit 1; \
	fi

# Phase 5 REPORT-04 — recompute-and-match reproducibility verification.
# MANIFEST path is parameterized so tests can run against a tmp copy
# (NEVER mutate the real reports/MANIFEST.md). 3-state per-line rule:
#   absent + is reports/ichi.pdf  -> PENDING (skip, not a failure)
#   absent + any other pinned path -> MISSING -> FAIL (exit 1)
#   present + sha mismatch         -> MISMATCH -> FAIL (exit 1)
#   present + sha match            -> OK
# Final guard: OK_COUNT must equal PIN_COUNT (a silently-skipped pin fails).
# Pin lines are standard sha256sum format (<64-hex><two spaces><path>); the awk
# parse splits on whitespace runs so no leading space leaks into $$path.
MANIFEST ?= reports/MANIFEST.md
verify-reproducibility:
	@bash -c 'set -euo pipefail; \
	  MANIFEST="$(MANIFEST)"; \
	  if [ ! -f "$$MANIFEST" ]; then echo "verify-reproducibility: SKIP — $$MANIFEST absent (Wave 1 authors it)"; exit 0; fi; \
	  FAIL=0; PINS=0; OKS=0; \
	  while read -r expected path; do \
	    [ -z "$$path" ] && continue; \
	    PINS=$$((PINS+1)); \
	    if [ ! -f "$$path" ]; then \
	      if [ "$$path" = "reports/ichi.pdf" ]; then echo "PENDING: $$path (not yet rendered)"; PINS=$$((PINS-1)); continue; \
	      else echo "MISSING (committed artifact absent): $$path"; FAIL=1; continue; fi; \
	    fi; \
	    actual=$$(sha256sum "$$path" | cut -d" " -f1); \
	    if [ "$$actual" != "$$expected" ]; then echo "MISMATCH: $$path ($$actual != $$expected)"; FAIL=1; \
	    else echo "OK: $$path"; OKS=$$((OKS+1)); fi; \
	  done < <(grep -E "^[a-f0-9]{64}  " "$$MANIFEST" | awk "{print \$$1, \$$2}"); \
	  if [ "$$OKS" != "$$PINS" ]; then echo "verify-reproducibility: FAIL — OK_COUNT($$OKS) != PIN_COUNT($$PINS)"; exit 1; fi; \
	  [ "$$FAIL" = 0 ] && echo "verify-reproducibility: PASS ($$OKS/$$PINS pins matched)" || { echo "verify-reproducibility: FAIL"; exit 1; }'

# -------- Phase 1 targets --------

# Run the fetch CLI for ICHI (Plan 01-04 lands the actual entrypoint).
# ARGS lets callers pass through `--pool ... --from ... --to ...` etc.
fetch-ichi:
	pnpm -C fetch fetch ichi $(ARGS)

# Phase 2 implements PANEL-02 metadata-header lint over generated panel artifacts.
# Pre-panel-build (no panel parquets — true until Plan 02-08): SKIP path,
# exits 0 so the target is a no-op gate. Post-panel-build: invokes
# scripts/lint_artifacts.py against every *.parquet under data/raw/ichi/ and
# exits non-zero on any artifact missing one of the six PANEL-02 metadata keys.
#
# Plan 02-10: the real-data driver writes panels at
# data/raw/ichi/<pool>/<from>_<to>.parquet (NOT under panels/), so the scan
# walks data/raw/ichi/ recursively rather than restricting to a single
# subdirectory.
lint-artifacts:
	@echo "lint-artifacts: scanning data/raw/ichi/ for PANEL-02 + data/fits/ for SC-1..."
	@PARQUETS=""; \
	if [ -d data/raw/ichi ]; then \
	  PARQUETS=$$(find data/raw/ichi -name "*.parquet" 2>/dev/null); \
	fi; \
	FIT_REPORTS=""; \
	if [ -d data/fits ]; then \
	  FIT_REPORTS=$$(find data/fits -name "fit_report.json" 2>/dev/null); \
	fi; \
	if [ -z "$$PARQUETS" ] && [ -z "$$FIT_REPORTS" ]; then \
	  echo "lint-artifacts: no panel artifacts or fit_report.json yet — skipping"; \
	else \
	  ARGS=""; \
	  [ -n "$$PARQUETS" ] && ARGS="$$ARGS $$(echo $$PARQUETS | sed 's| | ../|g; s|^|../|')"; \
	  cd analysis && uv run python ../scripts/lint_artifacts.py $$ARGS; \
	fi

# FETCH-04 cache-byte-identity invariant. Two consecutive runs of the same
# (pool, fromBlock, toBlock) tuple must produce sha256-equivalent parquet
# files in data/raw/ichi/ — zero new cost-ledger rows on the second run.
verify-cache-idempotency:
	@bash -c 'set -euo pipefail; \
	  rm -rf data/raw/ichi/; \
	  pnpm -C fetch fetch ichi --pool 0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F --from 67800000 --to 67800100; \
	  H1=$$(find data/raw/ichi -name "*.parquet" -o -name "*.jsonl" | sort | xargs sha256sum | sha256sum | cut -d" " -f1); \
	  pnpm -C fetch fetch ichi --pool 0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F --from 67800000 --to 67800100; \
	  H2=$$(find data/raw/ichi -name "*.parquet" -o -name "*.jsonl" | sort | xargs sha256sum | sha256sum | cut -d" " -f1); \
	  [ "$$H1" = "$$H2" ] || { echo "FAIL: cache idempotency broken ($$H1 != $$H2)"; exit 1; }; \
	  echo "PASS: cache byte-identical across reruns"'

# Schema-frozen-check probe — load-bearing per Plan 01-00 orchestrator finding #3.
# Reports whether appending [subgraphs.uniswap_v3] to protocols/ichi.toml would
# trip the schema-frozen pre-commit hook (which scans protocols/_schema.toml only).
schema-probe:
	bash scripts/schema_probe.sh

# Phase-1 protocol-agnostic leak gate (REPRO-01 invariant). This Makefile
# target is the cheap pre-commit complement to fetch/tests/protocol-agnostic.test.ts
# which is the authoritative leak-gate. Keep patterns in sync; see Plan 01-05.
#
# Three classes of leak detected:
#   1. Protocol-name branches    (`if config.name === "ichi"`, etc.)
#   2. Protocol factory addresses inlined in source
#   3. Uniswap V3 magic fee tiers inlined as literals
leak-check:
	@bash -c 'set -euo pipefail; \
	  if [ ! -d fetch/src ]; then \
	    echo "leak-check: SKIP — fetch/src not present"; \
	    exit 0; \
	  fi; \
	  HITS=$$(grep -rEn "if\s*\(?\s*(config\.name|protocol|vault_owner)\s*[!=]==?\s*[\"'\''](ichi|steer)[\"'\'']" fetch/src 2>/dev/null || true); \
	  if [ -n "$$HITS" ]; then echo "LEAK: protocol-name branch in fetch/src"; echo "$$HITS"; exit 1; fi; \
	  ADDRS=$$(grep -rEni "0x(9FAb4bdD4E05f5C023CCC85D2071b49791D7418F|116Dba5DcE9CcDA828218b7eB46406810632014C)" fetch/src 2>/dev/null || true); \
	  if [ -n "$$ADDRS" ]; then echo "LEAK: protocol factory addr in fetch/src"; echo "$$ADDRS"; exit 1; fi; \
	  FEES=$$(grep -rEn "\bfee\s*[:=]\s*(0\.0001|100|500|3000|10000)\b" fetch/src 2>/dev/null || true); \
	  if [ -n "$$FEES" ]; then echo "LEAK: magic fee-tier literal in fetch/src"; echo "$$FEES"; exit 1; fi; \
	  echo "PASS: leak-check clean"'

# Phase 3 Plan 03-03 — DGP-03 bootstrap LR null-distribution diagnostic.
# Re-renders reports/_diagnostics/lr_null_dist.png from the locked synthetic-NHPP
# fixture (n_reps=200 against tests/fixtures/synthetic_nhpp_baseline_only.parquet,
# deterministic seed sha256("03-03-diagnostic-render"+"phase-3-bootstrap")[:4]).
# Output is committed to the repo so PRs can see the SC-3 diagnostic visually.
render-lr-diagnostic:
	@mkdir -p reports/_diagnostics
	@cd analysis && uv run python -c "\
import numpy as np; import polars as pl;\
from abrigo_x402.dgp.lr_test import parametric_bootstrap_lr;\
df = pl.read_parquet('tests/fixtures/synthetic_nhpp_baseline_only.parquet');\
leg_0 = df.filter(pl.col('leg')==0).select('event_time').to_numpy().ravel().astype(np.float64);\
leg_1 = df.filter(pl.col('leg')==1).select('event_time').to_numpy().ravel().astype(np.float64);\
r = parametric_bootstrap_lr(leg_0, leg_1, panel_data_hash='03-03-diagnostic-render', window_start=0.0, window_end=2_592_000.0, n_reps=200, diagnostic_plot_path='../reports/_diagnostics/lr_null_dist.png');\
print(f'render-lr-diagnostic: PASS ({r[\"n_successful_bootstrap\"]}/{r[\"n_reps\"]} successful reps, seed={r[\"seed\"]})')"

# -------- Phase 4 targets --------

# Render the null-result PDF for a given firing condition. Wave 2 wires the full
# substrate-injection path; Wave 0 scaffolds the target so the command surface is
# present for plan-04-08 to land against.
render-null-result-pdf:
	@if [ -z "$$FIRING" ]; then \
		echo "Usage: make render-null-result-pdf FIRING={null_cost|null_lr|null_convex|null_strip_unavailable}"; \
		exit 1; \
	fi
	cd reports && quarto render _templates/null_result.qmd --no-cache \
		--execute-param firing_condition:$$FIRING --output ichi.pdf

# Phase 5 REPORT-01 — render the Iteration-1 deliverable. quarto is an operator
# build prerequisite (NOT auto-installed); only TinyTeX self-installs. Plan 05-03
# finalizes the spot-check curl-logging body. The legacy render-null-result-pdf
# target ALSO writes reports/ichi.pdf, so rm -f the stale PDF first — a stale or
# wrong-source PDF must never satisfy the test -f / size gate (repro-trap guard).
# Size gate uses portable `wc -c` (not GNU-only stat -c%s) for macOS operators.
report-ichi:
	@command -v quarto >/dev/null 2>&1 || { echo "report-ichi: FAIL — quarto binary required (build prerequisite, not auto-installed)"; exit 1; }
	@quarto install tinytex 2>/dev/null || true
	@test -f reports/ichi.qmd || { echo "report-ichi: FAIL — reports/ichi.qmd absent (Plan 05-03 authors it)"; exit 1; }
	@rm -f reports/ichi.pdf
	cd reports && quarto render ichi.qmd --to pdf --output ichi.pdf
	@test -f reports/ichi.pdf || { echo "report-ichi: FAIL — no PDF emitted (markdown fallback rejected)"; exit 1; }
	@SIZE=$$(wc -c < reports/ichi.pdf); [ "$$SIZE" -gt 51200 ] || { echo "report-ichi: FAIL — PDF $${SIZE}B < 50KB (SC-1)"; exit 1; }
	@SIZE=$$(wc -c < reports/ichi.pdf); echo "report-ichi: PASS — reports/ichi.pdf ($${SIZE}B)"

# Re-render the Carr-Madan strip diagnostic for a given run_id. Wave 2 wires the
# CLI hedge --stage strip subcommand; Wave 0 scaffolds the target.
render-strip-diagnostic:
	@if [ -z "$$RUN_ID" ]; then echo "Usage: make render-strip-diagnostic RUN_ID=<id>"; exit 1; fi
	cd analysis && uv run python -m abrigo_x402.cli hedge --stage strip --run-id $$RUN_ID

# Phase 4 acceptance gate. Wave 3 (Plan 04-09) closes against this. At Wave 0 the
# tests are skip-marked so this exits 0 trivially; once Wave 1 lands, the targets
# become load-bearing.
phase-4-acceptance:
	@echo "=== Phase 4 acceptance gate ==="
	cd analysis && uv run pytest \
		tests/test_cross_correlogram.py \
		tests/test_permutation_null.py \
		tests/test_copula_bic.py \
		tests/test_falsification.py \
		tests/test_carr_madan_strip.py \
		tests/test_stress_test.py \
		tests/test_usdt_depeg_lhs.py \
		tests/test_null_result_template.py \
		tests/test_joint_dist_provenance.py \
		tests/test_gate_report_provenance.py \
		tests/test_stress_report_provenance.py \
		tests/test_byte_identical_phase_4.py \
		tests/test_required_keys_sync.py \
		-x
	@! grep -i "^[^#]*usdc" analysis/src/abrigo_x402/hedge/falsification.py
	@! grep -E "scipy\.integrate\.quad|np\.trapz" analysis/src/abrigo_x402/hedge/carr_madan_strip.py
	@! grep -rE "loglik_in_sample_raw" analysis/src/abrigo_x402/hedge/
	@! grep -E "port from Hernandez Cruz" notes/usdt_depeg_calibration.md 2>/dev/null || true
	$(MAKE) lint-artifacts
	@echo "=== Phase 4 acceptance: PASS ==="
