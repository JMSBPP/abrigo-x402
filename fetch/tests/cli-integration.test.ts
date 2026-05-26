// fetch/tests/cli-integration.test.ts — Plan 01-06 CLI smoke tests.
//
// Spawns the CLI via tsx and asserts JSON shape + exit codes. Plan 01-08
// adds the heavier end-to-end Blockscout v1 getLogs + cache-write path on
// top of this scaffold.
//
// Operational invariants (checker C3): dry-run NEVER calls Forno. Head is
// derived from FETCH_HEAD_OVERRIDE > notes/forno_head_snapshot.json >
// fetch/src/constants.ts DRY_RUN_FALLBACK_HEAD. The JSON output includes
// `head_source: 'env_override'|'snapshot'|'fallback'|'live'` so consumers
// can audit; dry-run output MUST never report head_source === 'live'.

import { describe, test, expect } from 'vitest';
import { execSync } from 'node:child_process';

function runCli(
  args: string,
  envOverrides: Record<string, string | undefined> = {},
): { stdout: string; stderr: string; code: number } {
  // Default: pin head via env override so the test is deterministic + offline.
  const env: Record<string, string> = {
    ...(process.env as Record<string, string>),
    FETCH_HEAD_OVERRIDE: '67854122',
  };
  for (const [k, v] of Object.entries(envOverrides)) {
    if (v === undefined || v === '') {
      delete env[k];
    } else {
      env[k] = v;
    }
  }
  try {
    const stdout = execSync(`pnpm -s exec tsx src/cli.ts ${args}`, {
      cwd: process.cwd(),
      encoding: 'utf-8',
      env,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return { stdout, stderr: '', code: 0 };
  } catch (e: unknown) {
    const err = e as { stdout?: Buffer | string; stderr?: Buffer | string; status?: number };
    return {
      stdout: err.stdout?.toString() ?? '',
      stderr: err.stderr?.toString() ?? '',
      code: err.status ?? 1,
    };
  }
}

describe('CLI integration (Plan 01-06)', () => {
  test('--version exits 0 with semver', () => {
    const r = runCli('--version');
    expect(r.code).toBe(0);
    expect(r.stdout.trim()).toMatch(/^[0-9]+\.[0-9]+\.[0-9]+/);
  });

  test('ichi --dry-run --estimate-budget emits valid JSON with required keys', () => {
    const r = runCli('ichi --dry-run --estimate-budget');
    expect(r.code).toBe(0);
    const parsed = JSON.parse(r.stdout);
    expect(parsed.protocol).toBe('ichi');
    expect(parsed).toHaveProperty('total_queries');
    expect(parsed).toHaveProperty('exceeds_earmark');
    expect(parsed).toHaveProperty('earmark');
    expect(parsed).toHaveProperty('cache_hit');
    expect(parsed).toHaveProperty('dry_run');
    expect(parsed.dry_run).toBe(true);
    // Checker C3 — dry-run reports head provenance (no implicit live Forno call).
    expect(parsed).toHaveProperty('head_source');
    expect(['env_override', 'snapshot', 'fallback']).toContain(parsed.head_source);
    // Specifically must NOT be 'live' on dry-run.
    expect(parsed.head_source).not.toBe('live');
  });

  test('ichi --dry-run with no FETCH_HEAD_OVERRIDE makes ZERO Forno calls (checker C3)', () => {
    // Strip the env override; rely solely on snapshot/fallback. Must never escalate to live.
    const r = runCli('ichi --dry-run --estimate-budget', { FETCH_HEAD_OVERRIDE: undefined });
    expect(r.code).toBe(0);
    const parsed = JSON.parse(r.stdout);
    expect(parsed).toHaveProperty('head_source');
    expect(['snapshot', 'fallback']).toContain(parsed.head_source);
    expect(parsed.head_source).not.toBe('live');
  });

  test('ichi --dry-run --pool/--from/--to surfaces cache_hit flag', () => {
    const r = runCli(
      'ichi --dry-run --estimate-budget --pool 0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F --from 67800000 --to 67800100',
    );
    expect(r.code).toBe(0);
    const parsed = JSON.parse(r.stdout);
    expect(typeof parsed.cache_hit).toBe('boolean');
  });

  test('exits 1 for unknown subcommand', () => {
    const r = runCli('unknown-cmd');
    expect(r.code).toBe(1);
  });
});
