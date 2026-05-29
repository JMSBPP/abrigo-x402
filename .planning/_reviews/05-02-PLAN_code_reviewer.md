# Reviewer 2 (DevOps Automator) — Plan 05-02 (spot-check + MANIFEST + verify-reproducibility) — RE-REVIEW

## VERDICT
PASS

Scoped re-review of the heart of the reproducibility plumbing. My two prior BLOCKERs (fresh-clone verify failing on un-tracked pins; the PENDING-skip being too broad) are CLOSED, and the MAJOR (tamper test mutating the real MANIFEST) is CLOSED via the parameterized `MANIFEST ?=` var + a tmp-copy contract. The fresh-clone path is now genuinely exercised by a `git worktree add HEAD` clean-checkout run, not just the working tree. I re-derived the underlying gitignore allowlist empirically (see 05-00 verdict) so the pins resolve on a clone. No new BLOCKERs.

---

## Prior findings — confirm-closed

### BLOCKER 1 — MANIFEST pins ignored/untracked files → fresh-clone verify exits 1 → **CLOSED (empirically)**
- Root cause fixed upstream: the 05-00 nested allowlist re-includes `ichi/bdaf5c7ba5a2/{*.json,*.md,*.parquet,*.txt}` and 05-00 plain-adds CORRECTIONS.md + the panel; 05-01 plain-adds sensitivity_sweep.json. I confirmed in the sandbox that all of these are NOT-IGNORED and plain-addable.
- New defensive gate added: **Test 5 `test_every_pinned_fits_path_tracked`** (L152) — for every pinned `data/fits/...` and the panel `data/raw/...` path, `git ls-files <path>` must be non-empty. A missing-on-clone pin can no longer ship.
- New clean-checkout verification (L167-173, acceptance L184): `git worktree add /tmp/repro-check HEAD && (cd … && make verify-reproducibility); RC=$?; git worktree remove --force …; [ "$RC" = 0 ]`. This exercises the actual fresh-clone path (only HEAD-tracked files present), not the working tree where untracked files happen to exist on disk. This is the single most important fix — it converts "green on the author's box" into "green on the clone the PR reviewer pulls."

### BLOCKER 2 — blanket PENDING-skip hides a missing committed artifact → **CLOSED**
The 3-state rule is now explicit and scoped (L86-92, and baked into the 05-00 Makefile body L191-194):
- absent AND path == `reports/ichi.pdf` → PENDING, skip, PIN_COUNT decremented (the ONLY allow-listed PENDING path);
- absent AND any OTHER path → `MISSING (committed artifact absent)` → FAIL (exit 1);
- present + mismatch → FAIL; present + match → OK;
- final `OK_COUNT == PIN_COUNT` guard.
Test 4 `test_missing_committed_artifact_fails` (L151) locks this contract: a non-ichi.pdf absent pin → exit 1; an absent ichi.pdf → PENDING exit 0. PENDING is correctly narrowed to ichi.pdf only.

### MAJOR 3 — tamper test must not mutate the real MANIFEST → **CLOSED**
The Makefile target is parameterized `MANIFEST ?= reports/MANIFEST.md` (locked in 05-00 L182). Test 2 (L149) runs `make verify-reproducibility MANIFEST=<tmp_copy>` against a COPY in `tmp_path`, tampers the COPY, and asserts the real `reports/MANIFEST.md` is byte-unchanged after the run (acceptance L189). Never mutates the real file.

### MINOR 4 — 832-vs-778 draw population pinned → **CLOSED**
Test 1 (L110) now asserts `panel_rows == 832`; the panel is sha256-pinned (`a72a4ee…`) so a population change trips the test. The 832→778 PANEL-04 relationship is recorded in the MANIFEST provenance subsection (L164).

### MINOR 5 — curl needs `--connect-timeout` → **CLOSED**
The interface (L80) and Task 1 (L121) now use `curl … --connect-timeout 5 --max-time {timeout}`. A misconfigured proxy can no longer stall up to max-time × 5.

---

## New findings from the edits
None at BLOCKER/MAJOR.

- **MINOR (new) — clean-checkout worktree uses a fixed path `/tmp/repro-check`.** If a prior aborted run left that worktree registered, `git worktree add` will fail with "already exists." The plan does `git worktree remove --force` at the end, but not a pre-clean. Recommend prefixing with `git worktree remove --force /tmp/repro-check 2>/dev/null || true` before the add, or use a `mktemp -d` path. Non-blocking — a failed add surfaces loudly and does not produce a false PASS.

- **MINOR (new) — the clean-checkout run executes `make` inside the worktree, which has no built venv.** `verify-reproducibility` itself only calls `sha256sum`/`grep`/`awk` (no `uv run`), so it does not need the venv — confirmed by reading the 05-00 Makefile body (pure shell). Good. Flagged only so the executor does not add a `uv`-dependent step to the gate later, which would break the worktree run.

---

## Clean checks (re-confirmed live)
- Lockfile pins CORRECT: `analysis/uv.lock` + `pnpm-lock.yaml` exist + tracked; `package-lock.json` + root `uv.lock` do NOT. `! grep -q 'package-lock.json'` acceptance (L187) is right. ✓
- Panel sha256 `a72a4ee…` == disk == `fit_report.dataHash`; panel now committed via the 05-00 root negation (re-derived NOT-IGNORED). ✓
- verify-reproducibility does NOT re-fit — checksums committed artifacts only (Pitfall 2); no `cli.py fit`; explicit "DO NOT wire a materialize regeneration step" (L176) since the JSONL cache is untracked. ✓
- Canonical awk parse inherited verbatim from 05-00 (no divergent re-author). ✓
- Seed derivation recorded (`int(sha256("bdaf5c7ba5a2")[:8],16)`) + numpy `default_rng` (cross-version deterministic). ✓
- `depends_on: [05-00, 05-01]` — correct ordering so the sensitivity_sweep.json pin references an existing file. ✓
- `grep -cE '^[a-f0-9]{64}  data/fits/ichi/bdaf5c7ba5a2/' … ≥ 10` (L188) now correctly counts CORRECTIONS.md + sensitivity_sweep.json among the pins. ✓
