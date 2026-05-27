## VERDICT

PASS

## Scope

Reality check on Wave-0 scaffold plan (stubs, conftest fixtures, two locked synthetic Parquet fixtures, lint_artifacts.py extension) — gates whether Wave 1 can land in parallel.

## Findings

- Both synthetic fixtures (`synthetic_hawkes_eta_05.parquet`, `synthetic_nhpp_baseline_only.parquet`) are captured by `scripts/capture_synthetic_fixtures.py` with locked uint32 seeds (`HAWKES_SEED = 20260526`, `NHPP_SEED = 20260526 + 1`) visible in source — meets the "locked seeds visible" bar.
- Pitfall 9 (`force_simulation=True`) explicitly forbidden in both the capture script and the conftest helper, with a banner comment in each.
- Stubs raise `NotImplementedError` with Wave-1-plan-ID references, giving downstream blame trails when imports succeed but bodies are empty.
- `scripts/lint_artifacts.py` hook for `fit_report.json` is wired but dormant — the loop fires only when Wave 2 lands the artifact, so no false-positive lint failures during Wave 1.
- 21 test stubs land skip-marked with reasons; `pytest --collect-only` will pass and Wave 1 plans simply remove their skip decorators.

## Reality check

The most realistic failure mode here is the synthetic Hawkes fixture having a wrong number of events: `baseline=0.00013` events/sec over 30 days yields ≈337 expected baseline events per leg, but with η=0.5 self-excitation the realized count roughly doubles (Hawkes mean-rate inflation = baseline / (1 − η)). The plan's sanity check accepts 100–800 events/leg — which catches a pathological seed but not a slightly off branching-ratio that produces, say, ≈700 events and silently makes Wave-1 power tests too easy. The fixture is captured ONCE and shasummed, so this is a one-shot decision the executor must eyeball.

## Recommendation

Accept. Plan correctly establishes the scaffold contract Wave 1 needs.
