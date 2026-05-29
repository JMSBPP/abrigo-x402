#!/usr/bin/env bash
# scripts/pre-commit/af_lint.sh — AF-01..AF-12 anti-feature lint gate (GOV-03)
#
# Each anti-feature listed below. Active checks return non-zero on violation;
# Phase-3+ deferred checks are passthroughs documented as such, with matching
# tests/fixtures/af_NN_phase_deferred/ README placeholders explaining why.
#
# Canonical AF labels per FEATURES.md (authoritative source of truth):
#   AF-01 mock-data validation
#   AF-02 hand-tuned p-values
#   AF-03 spec swap after seeing results
#   AF-04 Hand-tuned bin width for INAR(p)  [FEATURES.md canonical]
#         REQUIREMENTS.md GOV-03 also uses "AF-04" for retrospective category
#         invention / mixing_class enum violations. The label-drift resolution:
#         this script's AF-04 ACTIVE check enforces mixing_class enum validity
#         (REQUIREMENTS.md GOV-03 wording). FEATURES.md AF-04 (bin-width
#         tuning) is Phase-3+ deferred since INAR(p) fitting code does not
#         yet exist. Both interpretations documented in tests/fixtures/README.md.
#   AF-05 binning that destroys arrival signal
#   AF-06 strip-without-gate
#   AF-07 forced-Hawkes claim
#   AF-08 dashboard scope-creep
#   AF-09 single-fit no-comparison
#   AF-10 Dune-Plus-to-validate
#   AF-11 untimestamped fits
#   AF-12 silent re-scope

set -euo pipefail
EXIT_CODE=0
FAILURES=()

# AF-01: mock / synthetic-data validation in production paths.
# Two-pronged check: (a) text-content references in production code,
# (b) filenames matching mock/synthetic/fake patterns under production paths.
# Filename check catches binary fixtures (e.g. fake_panel.parquet) that the
# content-grep cannot see because parquet is a non-text format.
if grep -rEl "mock[_-]data|synthetic[_-]events|fake[_-]panel" fetch/src analysis/src 2>/dev/null | grep -v "/tests/" >/dev/null 2>&1; then
  FAILURES+=("AF-01: mock/synthetic data text reference detected in production paths (fetch/src or analysis/src outside tests/)")
  EXIT_CODE=1
fi
AF01_DIRS=""
[ -d fetch/src ] && AF01_DIRS="$AF01_DIRS fetch/src"
[ -d analysis/src ] && AF01_DIRS="$AF01_DIRS analysis/src"
if [ -n "$AF01_DIRS" ]; then
  if find $AF01_DIRS -type f \( -name "*mock_data*" -o -name "*mock-data*" -o -name "*synthetic_events*" -o -name "*synthetic-events*" -o -name "*fake_panel*" -o -name "*fake-panel*" \) ! -path "*/tests/*" 2>/dev/null | grep -q .; then
    FAILURES+=("AF-01: mock/synthetic data file detected in production paths (fetch/src or analysis/src outside tests/)")
    EXIT_CODE=1
  fi
fi

# AF-02: hand-tuned p-values — Phase-3+ DEFERRED (no analysis/src yet)
# When analysis/src exists, will flag alpha-level != 0.01.
if [ -d analysis/src ]; then
  if grep -rE "alpha\s*=\s*0\.0[2-9]|alpha\s*=\s*0\.1" analysis/src 2>/dev/null >/dev/null; then
    FAILURES+=("AF-02: non-pre-registered alpha-level found (expected α=0.01 per notes/PRE_REGISTRATION.md)")
    EXIT_CODE=1
  fi
fi

# AF-03: spec swap after seeing results — pre-reg commit MUST predate any analysis/src commit.
# EXCEPTION: explicit AF-03 amendment commits (subject prefix "docs(pre-reg):") are the documented
# audit-trail mechanism (see notes/PRE_REGISTRATION.md §"Pre-Registration Discipline (AF-03 Audit Trail)"
# bullet 1: "Revising any of them requires a new pre-registration entry with a git commit predating
# the next downstream phase"). The amendment IS the spec-swap defense, not a violation of it.
# The fine-grained ordering invariant (amendment predates analysis/src/abrigo_x402/hedge/ +
# analysis/src/abrigo_x402/dependence/ — the directories the amendment governs) is enforced
# per-phase by plan-level acceptance gates (e.g., Plan 04-09's acceptance grid), not here.
if [ -f notes/PRE_REGISTRATION.md ] && [ -d analysis/src ]; then
  PRE_REG_SUBJECT=$(git log -1 --format=%s -- notes/PRE_REGISTRATION.md 2>/dev/null || echo "")
  # Accept both the bare AF-03 amendment subject `docs(pre-reg):` AND the
  # phase-suffixed variant `docs(pre-reg:<phase>):` introduced by Plan
  # 04.1.1-00. Phase-suffixed amendments are required when multiple in-flight
  # phases each add their own AF-03 amendment section — the suffix
  # disambiguates the audit trail (e.g. `docs(pre-reg:04.1.1):` for the LL-fit
  # acceptance & fallback chain amendment vs `docs(pre-reg):` for the original
  # Carr-Madan grid amendment).
  if ! echo "$PRE_REG_SUBJECT" | grep -qE "^docs\(pre-reg(:[^)]+)?\):"; then
    PRE_REG_TS=$(git log -1 --format=%ct -- notes/PRE_REGISTRATION.md 2>/dev/null || echo 0)
    ANALYSIS_FIRST_TS=$(git log --reverse --format=%ct -- analysis/src 2>/dev/null | head -1 || echo 0)
    # Default empty results to 0 so the numeric comparison never receives an empty operand
    PRE_REG_TS=${PRE_REG_TS:-0}
    ANALYSIS_FIRST_TS=${ANALYSIS_FIRST_TS:-0}
    if [ "$PRE_REG_TS" != "0" ] && [ "$ANALYSIS_FIRST_TS" != "0" ] && [ "$PRE_REG_TS" -gt "$ANALYSIS_FIRST_TS" ]; then
      FAILURES+=("AF-03: notes/PRE_REGISTRATION.md commit-timestamp is LATER than first analysis/src/ commit — spec-swap violation (and last pre-reg commit is NOT an explicit 'docs(pre-reg):' amendment commit)")
      EXIT_CODE=1
    fi
  fi
fi

# AF-04 (ACTIVE — REQUIREMENTS.md GOV-03 interpretation): mixing_class enum validity
# AF-04 (FEATURES.md interpretation: bin-width tuning) is Phase-3+ deferred (INAR(p) code doesn't exist)
if [ -f protocols/_schema.toml ]; then
  ENUM_VALUES=$(python3 -c "import tomllib; d = tomllib.load(open('protocols/_schema.toml', 'rb')); print('|'.join(d['enums']['mixing_class']))" 2>/dev/null || echo "")
  if [ -n "$ENUM_VALUES" ]; then
    for f in protocols/*.toml; do
      [ "$f" = "protocols/_schema.toml" ] && continue
      [ -f "$f" ] || continue
      INVALID=$(python3 -c "
import tomllib
d = tomllib.load(open('$f', 'rb'))
enum = set('$ENUM_VALUES'.split('|'))
bad = []
def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == 'mixing_class' and isinstance(v, str) and v not in enum:
                bad.append(v)
            walk(v)
walk(d)
print(','.join(bad))
" 2>/dev/null || echo "")
      if [ -n "$INVALID" ]; then
        FAILURES+=("AF-04: invalid mixing_class value(s) in $f: $INVALID (not in schema enum; REQUIREMENTS.md GOV-03 interpretation)")
        EXIT_CODE=1
      fi
    done
  fi
fi

# AF-05: binning that destroys arrival signal — Phase-3+ DEFERRED (no analysis/src yet)
if [ -d analysis/src ]; then
  if grep -rE "resample\(['\"](D|1D|1d|H|1H|1h)['\"]\)" analysis/src 2>/dev/null >/dev/null; then
    FAILURES+=("AF-05: daily/hourly resample detected in analysis/src — destroys sub-minute arrival signal")
    EXIT_CODE=1
  fi
fi

# AF-06: strip-without-gate — reject any carr_madan_strip artifact without gate_report.json predating it
if compgen -G "analysis/src/**/carr_madan_strip*.py" >/dev/null 2>&1; then
  if [ ! -f data/fits/*/gate_report.json ] 2>/dev/null; then
    if compgen -G "data/fits/*/strip*.json" >/dev/null 2>&1; then
      FAILURES+=("AF-06: Carr-Madan strip artifact exists without preceding gate_report.json (HEDGE-01 four-condition gate must pass first)")
      EXIT_CODE=1
    fi
  fi
fi

# AF-07: forced-Hawkes claim — Phase-3+ DEFERRED (no fit reports yet)
:

# AF-08 (M13): dashboard scope-creep — reject web UI files in scope
# Exclude tests/ so the af_08_dashboard_dir fixture under tests/fixtures/ does NOT trigger on clean state
if find . -type d \( -name "dashboard" -o -name "dashboards" -o -name "webapp" -o -name "streamlit*" -o -name "next" \) ! -path "./node_modules/*" ! -path "./.git/*" ! -path "./tests/*" 2>/dev/null | grep -q .; then
  FAILURES+=("AF-08: dashboard/webapp directory detected — research artifact only, no UI per FEATURES.md AF-08")
  EXIT_CODE=1
fi

# AF-09: single-fit no-comparison — Phase-3+ DEFERRED (no fits to compare yet)
:

# AF-10 (C2): Dune-Plus-to-validate — forbid DUNE_PLUS_API_KEY env var references
# Exclude tests/unit and node_modules but NOT tests/fixtures/ so the AF-10 fixture
# at tests/fixtures/af_10_dune_plus/.env.violating IS detected when fixture is active.
if grep -rE "DUNE_PLUS_API_KEY|dune_plus_api_key" . --include="*.py" --include="*.ts" --include="*.js" --include=".env*" --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=tests/unit 2>/dev/null >/dev/null; then
  FAILURES+=("AF-10: DUNE_PLUS_API_KEY reference detected — buying Dune Plus inverts the project's thesis per FEATURES.md AF-10")
  EXIT_CODE=1
fi

# AF-11: untimestamped fits — Phase-3+ DEFERRED (no fit_report.json artifacts yet)
:

# AF-12 (C3): silent re-scope — vault rows ADDED on top of existing rows.
# Handles initial-commit edge case explicitly: file must already exist in HEAD
# (otherwise this is a new file establishing the baseline — log and allow).
for f in $(git diff --cached --name-only --diff-filter=AM 2>/dev/null | grep -E "^protocols/.*\.toml$" | grep -v "_schema.toml" || true); do
  if git cat-file -e "HEAD:$f" 2>/dev/null; then
    # File exists in HEAD — compare row counts between HEAD and staged version
    EXISTING_ROWS=$(git show "HEAD:$f" 2>/dev/null | grep -cE "^\[(protocol\.)?vaults\." || echo 0)
    NEW_ROWS=$(git show ":$f" 2>/dev/null | grep -cE "^\[(protocol\.)?vaults\." || echo 0)
    if [ "$NEW_ROWS" -gt "$EXISTING_ROWS" ]; then
      FAILURES+=("AF-12 violation in $f: vault rows increased from $EXISTING_ROWS to $NEW_ROWS — toggle active flag on existing rows instead of adding new ones per CONTEXT.md AF-12 defense")
      EXIT_CODE=1
    fi
  else
    # Initial commit of file — establish baseline, allow
    echo "AF-12 note: $f is being committed for the first time; vault enumeration baseline established. Subsequent commits will be gated against this baseline."
  fi
done

# Report
if [ "$EXIT_CODE" -ne 0 ]; then
  echo "AF-lint: FAIL"
  printf '  %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "AF-lint: PASS (all AF-01..AF-12 active checks clean; deferred checks are passthroughs)"
exit 0
