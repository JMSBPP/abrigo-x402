# AF-03 violating fixture (ACTIVE): spec swap after seeing results

Triggers `scripts/pre-commit/af_lint.sh` AF-03 check.

## How to activate
1. Synthetic scenario: an analysis/src/ commit exists with timestamp T1; PRE_REGISTRATION.md is then modified at timestamp T2 > T1.
2. The AF-03 check compares git log timestamps. To simulate: create analysis/src/, commit, then commit a change to PRE_REGISTRATION.md.
3. Run `bash scripts/pre-commit/af_lint.sh` → expect exit 1 with "AF-03: notes/PRE_REGISTRATION.md commit-timestamp is LATER than first analysis/src/ commit"
