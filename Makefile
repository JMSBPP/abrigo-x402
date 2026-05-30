# Makefile — abrigo-x402
#
# Phase 0 targets: schema-frozen-check
# Phase 6 targets: leak-check (scoped-ichi layer), iteration-2-full (deterministic recipe)

.PHONY: schema-frozen-check leak-check verify-reproducibility help \
        fetch-ichi lint-artifacts verify-cache-idempotency schema-probe \
        render-lr-diagnostic render-null-result-pdf render-strip-diagnostic \
        phase-4-acceptance report-ichi iteration-2-full

# Pattern I — thread-pinned BLAS prefix. Pinned single-threaded BLAS BEFORE any
# numpy/statsmodels/scipy import so the AIC selection (and SC-5 byte-identity) is
# deterministic. Prepended to every Python invocation in iteration-2-full.
BLAS = OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1

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
# (NEVER mutate the real reports/MANIFEST.md).
#
# Two-tier contract:
#  (1) Deterministic inputs/artifacts — sha256 byte-pinned. Per-line rule:
#        absent  -> MISSING -> FAIL (exit 1)
#        present + sha mismatch -> MISMATCH -> FAIL (exit 1)
#        present + sha match    -> OK
#      Final guard: OK_COUNT must equal PIN_COUNT (a silently-skipped pin fails).
#  (2) reports/ichi.pdf — NOT byte-pinned. A rendered PDF embeds the pdfTeX
#      /Producer + /PTEX.Fullbanner (engine version), which SOURCE_DATE_EPOCH
#      cannot neutralize, so the sha differs across TeX toolchains — exactly the
#      cross-build instability the MANIFEST already refuses to byte-pin for the
#      scipy fit. The PDF is instead CONTENT-checked: present+>50KB + the HEDGE05
#      marker + the verbatim 3/4 verdict strings + NO forbidden narrowing string
#      (the AF-03 contract). Absent -> PENDING (not a failure). poppler tools
#      absent -> size-only soft-degrade.
# sha-pin lines are standard sha256sum format (<64-hex><two spaces><path>).
MANIFEST ?= reports/MANIFEST.md
verify-reproducibility:
	@bash -c 'set -euo pipefail; \
	  MANIFEST="$(MANIFEST)"; \
	  if [ ! -f "$$MANIFEST" ]; then echo "verify-reproducibility: SKIP — $$MANIFEST absent (Wave 1 authors it)"; exit 0; fi; \
	  FAIL=0; PINS=0; OKS=0; \
	  while read -r expected path; do \
	    [ -z "$$path" ] && continue; \
	    PINS=$$((PINS+1)); \
	    if [ ! -f "$$path" ]; then echo "MISSING (committed artifact absent): $$path"; FAIL=1; continue; fi; \
	    actual=$$(sha256sum "$$path" | cut -d" " -f1); \
	    if [ "$$actual" != "$$expected" ]; then echo "MISMATCH: $$path ($$actual != $$expected)"; FAIL=1; \
	    else echo "OK: $$path"; OKS=$$((OKS+1)); fi; \
	  done < <(grep -E "^[a-f0-9]{64}  " "$$MANIFEST" | awk "{print \$$1, \$$2}"); \
	  if [ "$$OKS" != "$$PINS" ]; then echo "verify-reproducibility: FAIL — OK_COUNT($$OKS) != PIN_COUNT($$PINS)"; exit 1; fi; \
	  if [ "$$FAIL" != 0 ]; then echo "verify-reproducibility: FAIL (sha pins)"; exit 1; fi; \
	  PDF=reports/ichi.pdf; \
	  if [ ! -f "$$PDF" ]; then echo "PENDING (content-checked): $$PDF not rendered — run make report-ichi"; \
	    echo "verify-reproducibility: PASS ($$OKS/$$PINS sha pins; PDF PENDING)"; exit 0; fi; \
	  SZ=$$(wc -c < "$$PDF"); [ "$$SZ" -gt 51200 ] || { echo "PDF-FAIL: $$PDF $${SZ}B < 50KB"; exit 1; }; \
	  if command -v pdftotext >/dev/null 2>&1; then \
	    T=$$(pdftotext "$$PDF" - 2>/dev/null); \
	    printf "%s" "$$T" | grep -q "null_strip_unavailable" || { echo "PDF-FAIL: firing_condition string absent"; exit 1; }; \
	    printf "%s" "$$T" | grep -Eq "p ?(-value)? ?= ?0\.0474" || { echo "PDF-FAIL: labeled KS p=0.0474 absent"; exit 1; }; \
	    printf "%s" "$$T" | grep -qi "false" || { echo "PDF-FAIL: gate FALSE verdict absent"; exit 1; }; \
	    for bad in "pass with caveat" "near-miss positive" "directionally positive" "exploratory positive" "positive result"; do \
	      printf "%s" "$$T" | grep -qi "$$bad" && { echo "PDF-FAIL: forbidden narrowing string present: $$bad"; exit 1; } || true; done; \
	  else echo "NOTE: pdftotext absent — PDF verdict-text check skipped (size-only)"; fi; \
	  if command -v pdfinfo >/dev/null 2>&1; then \
	    pdfinfo "$$PDF" 2>/dev/null | grep -q "HEDGE05" || { echo "PDF-FAIL: HEDGE05 marker absent from PDF metadata"; exit 1; }; \
	  else echo "NOTE: pdfinfo absent — HEDGE05 marker check skipped"; fi; \
	  echo "OK (content: size+verdict+marker, AF-03): $$PDF"; \
	  SPDF=reports/steer_null_result.pdf; \
	  if [ ! -f "$$SPDF" ]; then \
	    echo "PENDING (content-checked): $$SPDF not rendered — iteration-1-only checkout (NOTE: a Makefile skip does NOT mean Phase 6 passes; 06-VERIFICATION-pre.md gates verification_pass on the steer PDF actually existing)"; \
	    echo "verify-reproducibility: PASS ($$OKS/$$PINS sha pins + ichi PDF content-check; steer PDF PENDING)"; exit 0; fi; \
	  SSZ=$$(wc -c < "$$SPDF"); [ "$$SSZ" -gt 51200 ] || { echo "STEER-PDF-FAIL: $$SPDF $${SSZ}B < 50KB"; exit 1; }; \
	  if command -v pdftotext >/dev/null 2>&1; then \
	    ST=$$(pdftotext "$$SPDF" - 2>/dev/null); \
	    printf "%s" "$$ST" | grep -q "null_cost" || { echo "STEER-PDF-FAIL: firing_condition null_cost string absent"; exit 1; }; \
	    printf "%s" "$$ST" | grep -Eiq "cost.?leg|straddle" || { echo "STEER-PDF-FAIL: cost-leg/STRADDLE evidence string absent"; exit 1; }; \
	    for bad in "pass with caveat" "near-miss positive" "directionally positive" "exploratory positive" "positive result"; do \
	      printf "%s" "$$ST" | grep -qi "$$bad" && { echo "STEER-PDF-FAIL: forbidden narrowing string present: $$bad"; exit 1; } || true; done; \
	  else echo "NOTE: pdftotext absent — steer PDF verdict-text check skipped (size-only)"; fi; \
	  if command -v pdfinfo >/dev/null 2>&1; then \
	    pdfinfo -custom "$$SPDF" 2>/dev/null | grep -q "HEDGE05" || { echo "STEER-PDF-FAIL: HEDGE05 marker absent from PDF metadata (pdfinfo -custom)"; exit 1; }; \
	  else echo "NOTE: pdfinfo absent — steer HEDGE05 marker check skipped"; fi; \
	  echo "OK (content: size+null_cost+HEDGE05+cost-leg, AF-03 no-narrowing): $$SPDF"; \
	  echo "verify-reproducibility: PASS ($$OKS/$$PINS sha pins + ichi + steer PDF content-check)"'

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
#   4. (Plan 06-02 / REPRO-01 scoped layer) genuine functional `ichi` couplings
#      in fetch/src + analysis/src, EXCLUDING comments/docstrings + the
#      CLI-overridable defaults (data/fits/ichi, reports/ichi.pdf) + the
#      protocols/ichi.toml spec-layer reference. The command below is
#      BYTE-IDENTICAL to the string pinned in notes/PRE_REGISTRATION.md
#      §"Phase 6 — REPRO-01 scoped-grep re-scope" (M5). Any genuine coupling
#      that survived the Plan 01 scrub exits 1 with the offending lines.
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
	  ICHI=$$(grep -rnE '\''"ichi"|/ichi/|raw/ichi|fits/ichi'\'' analysis/src fetch/src \
	    | grep -vE '\''data/fits/ichi|reports/ichi\.pdf|protocols/ichi\.toml'\'' \
	    | grep -vE '\'':[0-9]+:[[:space:]]*(#|//|\*|/\*)'\'' || true); \
	  if [ -n "$$ICHI" ]; then echo "LEAK: scoped ichi coupling in analysis/src or fetch/src (REPRO-01)"; echo "$$ICHI"; exit 1; fi; \
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

# Render the null-result PDF for a given firing condition. Plan 06-02 drops the
# papermill per-parameter flag in favour of `-M firing_condition:` (the
# Plan 01 renderer fix: the H1 reads the meta shortcode, the executable evidence
# chunks read the HEDGE05_FIRING_CONDITION env var). Mirrors report-ichi's
# SOURCE_DATE_EPOCH + QUARTO_PYTHON determinism; renders from the template dir
# (the proven cd-into-dir + bare --output pattern, no absolute --output-dir).
render-null-result-pdf:
	@if [ -z "$$FIRING" ]; then \
		echo "Usage: make render-null-result-pdf FIRING={null_cost|null_lr|null_convex|null_strip_unavailable}"; \
		exit 1; \
	fi
	@command -v quarto >/dev/null 2>&1 || { echo "render-null-result-pdf: FAIL — quarto binary required (build prerequisite, not auto-installed)"; exit 1; }
	@quarto install tinytex 2>/dev/null || true
	@mkdir -p reports/_diagnostics
	VENV_PY=$$(cd analysis && uv run python -c 'import sys; print(sys.executable)'); \
		cd reports && SOURCE_DATE_EPOCH=1780012800 FORCE_SOURCE_DATE=1 QUARTO_PYTHON="$$VENV_PY" \
		HEDGE05_FIRING_CONDITION=$$FIRING \
		quarto render _templates/null_result.qmd --no-cache \
		-M firing_condition:$$FIRING --output null_result_$$FIRING.pdf
	@for cand in reports/null_result_$$FIRING.pdf reports/_templates/null_result_$$FIRING.pdf null_result_$$FIRING.pdf; do \
		[ -f "$$cand" ] && mv "$$cand" reports/_diagnostics/null_result_$$FIRING.pdf && break; \
	done
	@test -f reports/_diagnostics/null_result_$$FIRING.pdf && echo "render-null-result-pdf: PASS — reports/_diagnostics/null_result_$$FIRING.pdf ($$(wc -c < reports/_diagnostics/null_result_$$FIRING.pdf)B)" || { echo "render-null-result-pdf: FAIL — no PDF emitted"; exit 1; }

# Phase 5 REPORT-01 — render the Iteration-1 deliverable. quarto is an operator
# build prerequisite (NOT auto-installed); only TinyTeX self-installs. Plan 05-03
# finalizes the spot-check curl-logging body. rm -f the stale PDF first — a stale
# or wrong-source PDF must never satisfy the test -f / size gate (repro-trap
# guard). pdf-engine is pinned to pdflatex in ichi.qmd (the \pdfinfo HEDGE05
# marker is a pdfTeX-only primitive; lualatex/xelatex abort on it).
# Size gate uses portable `wc -c` (not GNU-only stat -c%s) for macOS operators.
report-ichi:
	@command -v quarto >/dev/null 2>&1 || { echo "report-ichi: FAIL — quarto binary required (build prerequisite, not auto-installed)"; exit 1; }
	@quarto install tinytex 2>/dev/null || true
	@test -f reports/ichi.qmd || { echo "report-ichi: FAIL — reports/ichi.qmd absent (Plan 05-03 authors it)"; exit 1; }
	@echo "report-ichi: logging per-row Blockscout spot-check HTTP status (SC-2, network-optional)..."
	@cd analysis && uv run python -c "from abrigo_x402.report.spot_check import seeded_spot_check, verify_url_status; from pathlib import Path; r=seeded_spot_check('bdaf5c7ba5a2', Path('../data/raw/ichi/0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F/67378253_67896653.parquet')); [print(verify_url_status(x['url'])) for x in r['rows']]" || echo "report-ichi: spot-check curl logging unavailable (continuing)"
	@rm -f reports/ichi.pdf
	# SOURCE_DATE_EPOCH pins pdfTeX /CreationDate, /ModDate, and the trailer /ID so the
	# PDF is byte-deterministic across renders (else the MANIFEST sha256 pin breaks on
	# every re-render). 1780012800 = 2026-05-29T00:00:00Z, matching the qmd frontmatter
	# date. QUARTO_PYTHON pins the analysis venv interpreter (has the jupyter stack +
	# abrigo_x402); the system python lacks both. firing_condition comes from the qmd
	# frontmatter params default (no per-parameter papermill flag → no papermill dependency).
	VENV_PY=$$(cd analysis && uv run python -c 'import sys; print(sys.executable)'); \
		cd reports && SOURCE_DATE_EPOCH=1780012800 FORCE_SOURCE_DATE=1 QUARTO_PYTHON="$$VENV_PY" \
		quarto render ichi.qmd --to pdf --output ichi.pdf
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

# -------- Phase 6 (Iteration-2) target --------

# iteration-2-full — the Iteration-2 Steer cCOP/USDT re-run as a DETERMINISTIC
# command sequence (NOT "echo OR invoke"). STEP 1 is ALWAYS the cost-leg check
# (REPRO-03 first step), which runs BEFORE any Steer fetch (AF-03 ordering: the
# pre-registered straddle rule is observed before the demand-band-derived
# verdict drives the pipeline). The block-range / run-id env vars
# (STEER_FROM / STEER_TO / STEER_RANGE / STEER_RUN) are supplied by the operator
# at invocation; Plan 06-03 records the concrete values. The recipe does NOT
# branch on env availability — it is a literal sequence. Every Python line is
# prefixed with the Pattern-I $(BLAS) single-threaded BLAS env.
iteration-2-full:
	@echo "iteration-2-full: STEP 1 — cost-leg check FIRST (REPRO-03 first-step, AF-03 ordering)"
	python scripts/cost_leg_check.py --protocol protocols/steer.toml --out notes/steer_cost_leg_bound.md
	@echo "iteration-2-full: STEP 2 — fetch Steer cCOP/USDT V3 anchor pool"
	pnpm -C fetch fetch steer --pool 0x2AC5baA668A8A58FD0e302B9896717484fd217B0 --from $$STEER_FROM --to $$STEER_TO
	@echo "iteration-2-full: STEP 3 — materialize panel (-> data/raw/steer/)"
	cd analysis && $(BLAS) uv run python -m abrigo_x402.cli materialize --pool 0x2AC5baA668A8A58FD0e302B9896717484fd217B0 --from-block $$STEER_FROM --to-block $$STEER_TO --protocol-toml ../protocols/steer.toml
	@echo "iteration-2-full: STEP 4 — fit (-> data/fits/steer/)"
	cd analysis && $(BLAS) uv run python -m abrigo_x402.cli fit --pool 0x2AC5baA668A8A58FD0e302B9896717484fd217B0 --panel-path ../data/raw/steer/0x2AC5baA668A8A58FD0e302B9896717484fd217B0/$$STEER_RANGE.parquet --out-dir ../data/fits/steer
	@echo "iteration-2-full: STEP 5 — hedge + render null PDF (null_cost from inside the run)"
	cd analysis && $(BLAS) uv run python -m abrigo_x402.cli hedge --run-id $$STEER_RUN --stage all --run-dir-root ../data/fits/steer --cost-leg-bound ../notes/steer_cost_leg_bound.md --reports-pdf ../reports/steer_null_result.pdf
