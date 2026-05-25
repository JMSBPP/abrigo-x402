# schema-frozen-diff violating fixture

Synthetic modified copy of `protocols/_schema.toml` with an extra enum value (`"v3-test-class"`) added to `data_cost_class`. Plan 00-07 copies this over `protocols/_schema.toml`, runs `bash scripts/pre-commit/schema_frozen.sh`, asserts exit 1 (schema-frozen-check FAIL), then restores the baseline.
