# AF Fixtures Taxonomy

This directory holds synthetic violating fixtures for the AF-01..AF-12 anti-feature
lint gate (`scripts/pre-commit/af_lint.sh`). Per GOV-03 SC-4(a), every AF the hook
ACTIVELY checks must have a fixture that triggers exit-nonzero. Deferred AFs (those
whose production code does not yet exist) carry placeholder README files explaining
the deferral.

## Fixture Categories

### Active AF fixtures (trigger exit-nonzero on hook)

| AF | Fixture directory | Trigger mechanism |
|----|-------------------|-------------------|
| AF-01 | af_01_mock_data/ | Copy `fake_panel.parquet` into `fetch/src/` or `analysis/src/` |
| AF-03 | af_03_spec_swap/ | Synthetic git-log scenario where PRE_REGISTRATION.md commit postdates analysis/src/ |
| AF-04 | af_04_invalid_mixing_class/ | Copy `protocols_fixture.toml` into `protocols/` — has invalid mixing_class value |
| AF-06 | af_06_strip_without_gate/ | Create `analysis/src/dummy/carr_madan_strip.py` + `data/fits/test_run/strip.json` without `gate_report.json` |
| AF-08 | af_08_dashboard_dir/ | Move the `dashboard/` subdir from `tests/fixtures/af_08_dashboard_dir/` to repo root |
| AF-10 | af_10_dune_plus/ | The hook detects `.env.violating` in-place (no copy needed) because af_lint.sh AF-10 excludes only `tests/unit`, not all of `tests/` |
| AF-12 | af_12_silent_rescope/ | After protocols/ichi.toml is in HEAD, stage a diff adding a NEW [protocol.vaults.X] block |

### Phase-deferred AF fixtures (placeholder README only)

| AF | Fixture directory | Reason for deferral |
|----|-------------------|---------------------|
| AF-02 | af_02_phase_deferred/ | Hand-tuned p-values can only be violated by code that fits a model and reports a p-value. No analysis/src/ exists yet (Phase 3+). |
| AF-05 | af_05_phase_deferred/ | Daily/hourly aggregation can only be violated inside analysis/src/. Phase 3+. |
| AF-07 | af_07_phase_deferred/ | Forced-Hawkes claim requires a fit_report.json artifact + held-out KS test. Phase 3+. |
| AF-09 | af_09_phase_deferred/ | Single-fit-no-comparison requires multiple fits to compare against. Phase 3+. |
| AF-11 | af_11_phase_deferred/ | Untimestamped fits requires fit_report.json artifacts. Phase 3+. |

## AF-04 Label-Drift Resolution (C1 from Phase 0 checker review)

**FEATURES.md AF-04** = "Hand-tuned bin width for INAR(p)" (canonical label).
**REQUIREMENTS.md GOV-03 AF-04** = retrospective category invention / mixing_class
enum violation (per the "12 anti-features" enumeration in GOV-03 wording).

**Resolution:** FEATURES.md is treated as the authoritative source of truth for AF
label semantics. However, the *active* `af_lint.sh` AF-04 hook check enforces the
REQUIREMENTS.md GOV-03 interpretation (mixing_class enum validity), because:
  - The FEATURES.md AF-04 (bin-width tuning) check requires INAR(p) fitting code
    inside `analysis/src/`, which does not yet exist at Phase 0. That check is
    Phase-3+ deferred — documented in `af_02_phase_deferred/` and `af_05_phase_deferred/`
    fixtures (both Phase-3+ Hawkes/NHPP-code-dependent checks).
  - The REQUIREMENTS.md GOV-03 AF-04 (mixing_class enum) check is enforceable at
    Phase 0 against the `protocols/*.toml` artifacts that DO exist now.

Both readings of "AF-04" are accepted in pre-commit hook output messages: the active
check identifies itself as "AF-04 (REQUIREMENTS.md GOV-03 interpretation: mixing_class
enum validity)" and the bin-width interpretation is referenced in comments inside
`af_lint.sh` near the AF-04 block.

This file's `tests/fixtures/af_04_invalid_mixing_class/` fixture exercises the active
check. When Phase 3+ INAR(p) code exists, a future plan will add a second active AF-04
fixture (`af_04_invalid_bin_width/`) for the FEATURES.md interpretation.

## Plan 00-07 Negative-Case Validation

`Plan 00-07 Task 3` runs each active fixture through the hook and asserts exit-nonzero,
then cleans up. The fixture activation steps + cleanup steps are documented in each
active fixture's README.md.

## How to Verify All 12 AFs Have a Fixture

```sh
ls tests/fixtures/ | grep -cE "^af_(0[1-9]|1[0-2])_"
```

Returns 12 if all twelve AF directories exist (af_01 through af_12 plus af_review_trail_missing and af_schema_frozen_diff which are not numbered AFs).
