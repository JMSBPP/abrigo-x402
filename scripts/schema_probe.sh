#!/usr/bin/env bash
# scripts/schema_probe.sh
# Probe: would adding [subgraphs.uniswap_v3] block to protocols/ichi.toml
# trigger the schema-frozen-check hook (which compares protocols/_schema.toml
# against baseline e9b214d)?
#
# Output: PROBE_PASS (safe to add to ichi.toml only) or PROBE_FAIL (requires
# Phase-0-style _schema.toml increment).
set -euo pipefail

BASELINE_SHA="e9b214dcb26d7a6085aa98765a3f8816950495eb"
SCHEMA_FILE="protocols/_schema.toml"
PROBE_FILE="protocols/ichi.toml"
TMP_PROBE=$(mktemp)
trap "rm -f $TMP_PROBE" EXIT

# Step 1: confirm baseline _schema.toml is unmodified
if ! git diff "$BASELINE_SHA" -- "$SCHEMA_FILE" > /dev/null 2>&1; then
  echo "PROBE_ERROR: cannot diff $SCHEMA_FILE against baseline $BASELINE_SHA"
  exit 2
fi
SCHEMA_DIFF=$(git diff "$BASELINE_SHA" -- "$SCHEMA_FILE" || true)
if [ -n "$SCHEMA_DIFF" ]; then
  echo "PROBE_FAIL: protocols/_schema.toml already diverges from baseline $BASELINE_SHA"
  echo "$SCHEMA_DIFF"
  exit 1
fi

# Step 2: construct a draft ichi.toml with [subgraphs.uniswap_v3] added
cp "$PROBE_FILE" "$TMP_PROBE"
cat >> "$TMP_PROBE" <<'EOF'

[subgraphs.uniswap_v3]
enabled = false
deployment_id = "<deferred>"
reason = "subgraph hunt at Phase 1 found two stale candidates requiring API key; defer to Phase 1.5 retroactive enrichment"
EOF

# Step 3: would adding this trip schema-frozen-check?
# The hook (scripts/pre-commit/schema_frozen.sh) ONLY checks protocols/_schema.toml.
# Per-protocol TOMLs are NOT in scope of that hook.
# Therefore: appending [subgraphs.uniswap_v3] to ichi.toml is SAFE.
# We verify by simulating: if scripts/pre-commit/schema_frozen.sh exists,
# confirm its grep target is _schema.toml only.
HOOK_FILE="scripts/pre-commit/schema_frozen.sh"
if [ ! -f "$HOOK_FILE" ]; then
  echo "PROBE_ERROR: $HOOK_FILE missing — Phase 0 hook not installed?"
  exit 2
fi
HOOK_CONTENT=$(cat "$HOOK_FILE")
if echo "$HOOK_CONTENT" | grep -qE "protocols/ichi\.toml|protocols/steer\.toml|protocols/\*\.toml"; then
  echo "PROBE_FAIL: schema-frozen hook ALSO scans per-protocol TOMLs"
  echo "Adding [subgraphs.uniswap_v3] to ichi.toml WILL trip the hook"
  echo "Required: Phase-0-style increment to _schema.toml with re-baseline"
  exit 1
fi

echo "PROBE_PASS: schema-frozen-check only scans $SCHEMA_FILE"
echo "Safe to add [subgraphs.uniswap_v3] block to protocols/ichi.toml at Phase 1.5"
echo "Recommendation: Phase 1 does NOT add the block (subgraph downgrade default)"
exit 0
