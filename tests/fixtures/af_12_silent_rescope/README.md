# AF-12 violating fixture (ACTIVE): row addition after initial commit

Triggers `scripts/pre-commit/af_lint.sh` AF-12 check (C3: initial-commit edge
case handled — initial commit logs baseline; subsequent additions are rejected).

## How to activate (per Plan 00-07 Test 3 sub-step)
1. Stage protocols_baseline.toml as a real protocol file: `cp tests/fixtures/af_12_silent_rescope/protocols_baseline.toml protocols/test_fixture.toml && git add protocols/test_fixture.toml && git commit -m "test: af-12 baseline" --no-verify`
2. Now stage a row addition: append `[protocol.vaults.SYNTHETIC_NEW]\nactive = false\nreason = "af12-test"\n` to `protocols/test_fixture.toml` and `git add protocols/test_fixture.toml`
3. Run `bash scripts/pre-commit/af_lint.sh` → expect exit 1 with "AF-12 violation: vault rows increased"
4. Cleanup: `git restore --staged protocols/test_fixture.toml && git checkout protocols/test_fixture.toml && git rm protocols/test_fixture.toml && git commit -m "test: cleanup af-12 fixture" --no-verify`
