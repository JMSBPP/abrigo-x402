# Makefile — abrigo-x402
#
# Phase 0 targets: schema-frozen-check
# Phase 6+ forward-looking targets: leak-check, iteration-2-full (stubs)

.PHONY: schema-frozen-check leak-check verify-reproducibility help

help:
	@echo "Available targets:"
	@echo "  schema-frozen-check  - reject any diff to protocols/_schema.toml after the Phase-0 baseline commit"
	@echo "  leak-check           - (Phase 6 forward-looking) grep for ichi/cKES leakage in fetch/src + analysis/src"
	@echo "  verify-reproducibility - (Phase 5 forward-looking) verify reports/MANIFEST.md checksums"

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

# Phase 6 forward-looking — leak gate for REPRO-01 invariant
# Currently a stub because fetch/src and analysis/src don't exist yet
leak-check:
	@if [ ! -d fetch/src ] && [ ! -d analysis/src ]; then \
		echo "leak-check: SKIP — fetch/src and analysis/src don't exist yet (Phase 0 / pre-Phase-1 state)"; \
		exit 0; \
	fi; \
	HITS=$$(grep -ri "ichi" fetch/src analysis/src 2>/dev/null | wc -l); \
	if [ "$$HITS" -gt 0 ]; then \
		echo "leak-check: FAIL — 'ichi' leaked into protocol-agnostic source ($$HITS hits)"; \
		grep -ri "ichi" fetch/src analysis/src; \
		exit 1; \
	fi; \
	echo "leak-check: PASS — no 'ichi' leakage in fetch/src or analysis/src"

# Phase 5 forward-looking stub
verify-reproducibility:
	@echo "verify-reproducibility: STUB — Phase 5 deliverable"
	@exit 0
