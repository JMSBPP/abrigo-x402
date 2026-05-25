# AF-08 violating fixture (ACTIVE): dashboard directory at repo root

Triggers `scripts/pre-commit/af_lint.sh` AF-08 check. The fixture lives under
`tests/fixtures/af_08_dashboard_dir/dashboard/` — the hook's `find` excludes
`./tests/*` (M13) so the fixture does NOT trigger on the clean repo state.

## How to activate
1. `cp -r tests/fixtures/af_08_dashboard_dir/dashboard ./dashboard`
2. Run `bash scripts/pre-commit/af_lint.sh` → expect exit 1 with "AF-08: dashboard/webapp directory detected"
3. Cleanup: `rm -rf ./dashboard` → re-run → expect exit 0
