#!/usr/bin/env bash
# scripts/pre-commit/review_trail.sh — 2-way review-trail enforcement (ROADMAP review-trail contract)
#
# Rejects commits modifying .planning/**/PLAN.md or .planning/ROADMAP.md
# unless paired .planning/_reviews/<basename>_reality_checker.md +
# _code_reviewer.md exist with `## VERDICT` first H2 and no unresolved
# BLOCKER. Override flag --allow-revision honors NEEDS REVISION but not
# BLOCKER.

set -euo pipefail
EXIT_CODE=0
ALLOW_REVISION=0
[ "${1:-}" = "--allow-revision" ] && ALLOW_REVISION=1

STAGED=$(git diff --cached --name-only 2>/dev/null || true)
# Match any markdown file under .planning/ whose basename ends in PLAN.md
# (covers GSD convention 00-07-PLAN.md AND bare PLAN.md), plus ROADMAP.md
NEED_REVIEW=$(echo "$STAGED" | grep -E "^\.planning/.*PLAN\.md$|^\.planning/ROADMAP\.md$" || true)

if [ -z "$NEED_REVIEW" ]; then
  echo "review-trail: PASS (no PLAN.md or ROADMAP.md changes staged)"
  exit 0
fi

for f in $NEED_REVIEW; do
  BASENAME=$(basename "$f" .md)
  RC=".planning/_reviews/${BASENAME}_reality_checker.md"
  CR=".planning/_reviews/${BASENAME}_code_reviewer.md"

  if [ ! -f "$RC" ]; then
    echo "review-trail: FAIL — missing $RC for $f"
    EXIT_CODE=1
    continue
  fi
  if [ ! -f "$CR" ]; then
    echo "review-trail: FAIL — missing $CR for $f"
    EXIT_CODE=1
    continue
  fi

  RC_VERDICT_LINE=$(grep -nE "^## " "$RC" | head -1 || echo "")
  CR_VERDICT_LINE=$(grep -nE "^## " "$CR" | head -1 || echo "")

  if ! echo "$RC_VERDICT_LINE" | grep -qE "## VERDICT$"; then
    echo "review-trail: FAIL — $RC first H2 is not '## VERDICT' (got: $RC_VERDICT_LINE)"
    EXIT_CODE=1
    continue
  fi
  if ! echo "$CR_VERDICT_LINE" | grep -qE "## VERDICT$"; then
    echo "review-trail: FAIL — $CR first H2 is not '## VERDICT' (got: $CR_VERDICT_LINE)"
    EXIT_CODE=1
    continue
  fi

  RC_VERDICT=$(awk '/^## VERDICT$/{getline; while(/^\s*$/){getline}; print; exit}' "$RC")
  CR_VERDICT=$(awk '/^## VERDICT$/{getline; while(/^\s*$/){getline}; print; exit}' "$CR")

  for V in "$RC_VERDICT" "$CR_VERDICT"; do
    if echo "$V" | grep -qiE "(BLOCKED|BLOCKER)"; then
      echo "review-trail: FAIL — BLOCKER verdict in review for $f: '$V'"
      EXIT_CODE=1
    fi
    if echo "$V" | grep -qiE "NEEDS REVISION"; then
      if [ "$ALLOW_REVISION" -ne 1 ]; then
        echo "review-trail: FAIL — NEEDS REVISION verdict for $f without --allow-revision override"
        EXIT_CODE=1
      else
        echo "review-trail: WARN — NEEDS REVISION accepted via --allow-revision for $f"
      fi
    fi
  done
done

if [ "$EXIT_CODE" -ne 0 ]; then
  exit 1
fi
echo "review-trail: PASS"
exit 0
