# AF-10 violating fixture (ACTIVE): Dune Plus API key reference

Triggers `scripts/pre-commit/af_lint.sh` AF-10 check. **Detected in-place** —
the AF-10 grep excludes only `tests/unit` and `node_modules`, NOT all of `tests/`
(per C2 resolution), so this `.env.violating` file under `tests/fixtures/` IS
seen by the hook.

## How to activate
1. The fixture is already detected by the hook when this file is present:
   `bash scripts/pre-commit/af_lint.sh` → expect exit 1 with "AF-10: DUNE_PLUS_API_KEY reference detected"
2. To return to PASS state, delete `.env.violating` (this fixture file).

Note: in Plan 00-07 Test 2, the validation copies this fixture in-place is not needed
— the fixture's mere existence triggers the hook. The Plan 00-07 test removes the
fixture temporarily, asserts PASS, then restores it.
