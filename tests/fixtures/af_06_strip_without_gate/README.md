# AF-06 violating fixture (ACTIVE): Carr-Madan strip without gate_report.json

## How to activate
1. `mkdir -p analysis/src/dummy data/fits/test_run`
2. `touch analysis/src/dummy/carr_madan_strip.py data/fits/test_run/strip.json`
3. Do NOT create `data/fits/test_run/gate_report.json`
4. Run `bash scripts/pre-commit/af_lint.sh` → expect exit 1 with "AF-06: Carr-Madan strip artifact exists without preceding gate_report.json"
5. Cleanup: `rm -rf analysis data` → re-run → expect exit 0
