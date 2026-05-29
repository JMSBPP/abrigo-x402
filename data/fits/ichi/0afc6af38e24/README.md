# Archived: synthetic-substrate Phase 4 production rep (run_id 0afc6af38e24)

**Status:** Methodology-validation substrate. **Superseded by `ae9e3ba17900` for v1.0 publication.**

## Why this run exists

Plan 04-09 (Phase 4 acceptance gate) needed a production-rep substrate. The real Phase-2 ICHI panel at `data/raw/ichi/0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F/67378253_67896653.parquet` lacked the `block_timestamp` column required by Phase 3's `_extract_legs_from_panel` (Phase 2→Phase 3 column-wire gap — out of Plan 04-09 scope at the time). The fallback substrate was a 3x time-shifted stack of the Phase 3 synthetic Hawkes fixture (`analysis/tests/fixtures/synthetic_hawkes_eta_05.parquet`), written to `data/raw/ichi/.../synthetic_p4_09_stacked_67000000_67002058.parquet`.

The synthetic substrate validated the Plan 04-08 Path A architecture end-to-end (Sobol-QMC characteristic function builder, four-condition gate, three-way stress, null-result-PDF firing decision) on data with known properties (Hawkes η=0.5 self-excitation).

## Why this run is now superseded

Phase 04.1 (gap closure) backported `block_timestamp` into the Phase 2 ingest path (Plan 04.1-00: `analysis/src/abrigo_x402/ingest.py` + sanity tests + lint extension) and regenerated the real ICHI panel (Plan 04.1-01: same JSONL sidecars, augmented parquet schema). Plan 04.1-02 reran the Phase 3 fit producing run_id `ae9e3ba17900` with deterministically derived dataHash. Plan 04.1-03 reran the Phase 4 hedge orchestrator on that real-data run_id.

The new real-data run is the canonical v1.0 publication substrate. Phase 5 PDF deliverable (`reports/ichi.pdf`) reads from `data/fits/ichi/ae9e3ba17900/` for headline findings.

## Preserved as audit history

This directory is NOT deleted. It preserves audit history of the synthetic-substrate methodology-validation path. The synthetic-vs-real comparison table in `.planning/phases/04-cross-leg-dependence-l5-falsification-carr-madan-strip-l6/04-VERIFICATION-pre.md` (appended "04.1 Real-Data Rerun" section) IS the load-bearing methodology-validation evidence for Phase 5: the architecture works on data with known properties (synthetic) AND on data with unknown properties (real).

## Pointers

- **Canonical Phase 5 input:** `data/fits/ichi/ae9e3ba17900/` (load-bearing v1.0 substrate)
- **Methodology-validation evidence:** this directory (kept for audit; cited in Phase 5 narrative methodology section only)
- **Append-section in Phase 4 verification gate:** `.planning/phases/04-cross-leg-dependence-l5-falsification-carr-madan-strip-l6/04-VERIFICATION-pre.md` → "04.1 Real-Data Rerun" section
- **Frontmatter signal Phase 5 reads at parse time:** `real_data_rerun_run_id: ae9e3ba17900` + `substrate_substitution_resolved: true`

---

*Archived: 2026-05-27 (Phase 04.1 close-the-loop)*
