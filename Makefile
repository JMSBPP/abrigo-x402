# Makefile — abrigo-x402
#
# Phase 0 targets: schema-frozen-check
# Phase 6+ forward-looking targets: leak-check, iteration-2-full (stubs)

.PHONY: schema-frozen-check leak-check verify-reproducibility help \
        fetch-ichi lint-artifacts verify-cache-idempotency schema-probe

help:
	@echo "Available targets:"
	@echo "  schema-frozen-check     - reject any diff to protocols/_schema.toml after the Phase-0 baseline commit"
	@echo "  leak-check              - reject protocol-name branches, factory-addr literals, magic fee tiers in fetch/src"
	@echo "  schema-probe            - probe whether adding [subgraphs.uniswap_v3] to ichi.toml trips schema-frozen-check"
	@echo "  fetch-ichi              - run ICHI fetch CLI (Phase 1 SC-2 implementation lands in Plan 01-04)"
	@echo "  lint-artifacts          - PANEL-02 metadata header lint (Phase 2 implementation)"
	@echo "  verify-cache-idempotency - rerun fetch twice and assert byte-identical parquet (FETCH-04)"
	@echo "  verify-reproducibility  - (Phase 5 forward-looking) verify reports/MANIFEST.md checksums"

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

# Phase 5 forward-looking stub
verify-reproducibility:
	@echo "verify-reproducibility: STUB — Phase 5 deliverable"
	@exit 0

# -------- Phase 1 targets --------

# Run the fetch CLI for ICHI (Plan 01-04 lands the actual entrypoint).
# ARGS lets callers pass through `--pool ... --from ... --to ...` etc.
fetch-ichi:
	pnpm -C fetch fetch ichi $(ARGS)

# Phase 2 implements PANEL-02 metadata-header lint over generated panel artifacts.
# Pre-panel-build (data/raw/ichi/panels/ absent — true until Plan 02-08): SKIP path,
# exits 0 so the target is a no-op gate. Post-panel-build (directory present): invokes
# scripts/lint_artifacts.py against every *.parquet under data/raw/ichi/panels/ and
# exits non-zero on any artifact missing one of the six PANEL-02 metadata keys.
lint-artifacts:
	@echo "lint-artifacts: scanning data/raw/ichi/panels/ for PANEL-02 headers..."
	@if [ -d data/raw/ichi/panels ]; then \
	  cd analysis && uv run python ../scripts/lint_artifacts.py ../data/raw/ichi/panels/*.parquet; \
	else \
	  echo "lint-artifacts: no panel artifacts yet (data/raw/ichi/panels/ absent) — skipping"; \
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
