# AF-01 violating fixture (ACTIVE): mock data in production paths

Triggers `scripts/pre-commit/af_lint.sh` AF-01 check.

## How to activate (negative-case test)
1. `mkdir -p fetch/src && cp tests/fixtures/af_01_mock_data/fake_panel.parquet fetch/src/`
2. Run `bash scripts/pre-commit/af_lint.sh` → expect exit 1 with "AF-01: mock/synthetic data detected"
3. Cleanup: `rm -rf fetch/` (Phase 0 ordering invariant: fetch/ must not exist)
4. Re-run hook → expect exit 0
