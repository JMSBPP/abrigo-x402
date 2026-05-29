# Phase 6 — Deferred / Out-of-Scope Discoveries

Items found during execution that are NOT caused by the current plan's changes
and are therefore logged, not fixed.

## D1 — Synthetic Phase-4 parquets lack the PANEL-02 metadata footer (pre-existing)

**Found during:** Plan 06-01 Task 2 (generalized the lint column-guard).

**Observation:** The two synthetic Phase-4 fixtures on disk —
`data/raw/ichi/0x61Ef.../synthetic_p4_09_67000000_67000686.parquet` and
`synthetic_p4_09_stacked_67000000_67002058.parquet` — fail
`scripts/lint_artifacts.py` on the six PANEL-02 metadata-header keys (chainId,
contractAddress, blockRange, fetchTimestamp, dataHash, gitCommit). They were
written by the Plan 04-09 synthetic-stacking path, which never embedded a
PANEL-02 footer.

**Not caused by this plan:** The failure is on the REQUIRED_KEYS metadata check
(line ~338), which is unchanged. Both synthetic parquets DO carry
`block_timestamp`, so the generalized `data/raw/<protocol>/` column-guard added
in this plan passes on them; the metadata-footer failure is orthogonal and
pre-existing. The real panel
(`data/raw/ichi/0x61Ef.../67378253_67896653.parquet`) passes both checks.

**Why not fixed:** `data/raw/` is gitignored; these synthetic fixtures are not
passed to the linter by `make leak-check`, `make lint-artifacts`, or the test
suite (which lint only explicitly-named paths / the real panel). No CI or gate
regresses. Re-materializing the synthetic fixtures with a PANEL-02 footer (or
deleting them) is housekeeping outside Phase-6 scope.
