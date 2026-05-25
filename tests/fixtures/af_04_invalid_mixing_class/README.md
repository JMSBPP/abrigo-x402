# AF-04 violating fixture (ACTIVE — REQUIREMENTS.md GOV-03 interpretation): invalid mixing_class

Triggers `scripts/pre-commit/af_lint.sh` AF-04 check.

## How to activate
1. `cp tests/fixtures/af_04_invalid_mixing_class/protocols_fixture.toml protocols/test_fixture.toml`
2. Run `bash scripts/pre-commit/af_lint.sh` → expect exit 1 with "AF-04: invalid mixing_class value"
3. Cleanup: `rm protocols/test_fixture.toml` → re-run → expect exit 0

Note: the canonical FEATURES.md AF-04 ("Hand-tuned bin width for INAR(p)") is
Phase-3+ deferred (see `af_02_phase_deferred/` for the same Phase-3+ scope rationale);
this active check enforces the REQUIREMENTS.md GOV-03 interpretation per
`tests/fixtures/README.md` label-drift resolution.
