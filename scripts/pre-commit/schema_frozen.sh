#!/usr/bin/env bash
# scripts/pre-commit/schema_frozen.sh — wrapper invoking `make schema-frozen-check`
set -euo pipefail
exec make schema-frozen-check
