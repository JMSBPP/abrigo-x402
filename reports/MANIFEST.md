# Reproducibility Manifest — abrigo-x402 Iteration 1 (ICHI cKES/USDT)

**Requirement:** REPORT-04
**Canonical run:** run_id `bdaf5c7ba5a2` (Phase 04.1.1) · gitCommit `12cf99f` · dataHash `a72a4ee…`
**Verdict reported:** gate_passes=FALSE (3/4), firing_condition=`null_strip_unavailable`, η≈0.600 (LR rejects NHPP p=0.0; held-out Hawkes +114 nats; held-out KS leg-0 p=0.0474 — knife-edge miss at α=0.05).

## Reproducibility model (Option C-hybrid)

The headline numbers are produced by a **scipy maximum-likelihood fit** that is
NOT byte-reproducible across BLAS builds/threads, so `make verify-reproducibility`
does NOT re-run the fit. Instead it **checksums the committed input + the committed
derived artifacts** of the canonical run and matches them against the pins below.
A fresh clone HAS every pinned path because:

- The 832-row panel parquet is **committed** (Plan 05-00 scoped a root-`.gitignore`
  negation re-including this one parquet; its JSONL source cache stays ignored).
  It is therefore **not regenerated via `cli.py materialize`** — the JSONL source
  cache is not git-tracked, so an offline materialize is impossible; committing the
  128 KB panel is the chosen reproducibility path.
- The `bdaf5c7ba5a2/` run-dir artifacts (incl. `CORRECTIONS.md` + `sensitivity_sweep.json`)
  are committed via Plan 05-00's nested-`.gitignore` allowlist + Plan 05-01's commit.

To reproduce the headline numbers from scratch a reader re-runs `cli.py fit` under
thread-pinned BLAS (`OMP=MKL=OpenBLAS=NumExpr=1`) on the pinned panel; the AIC-min
β selection is deterministic single-threaded, but the floating-point fit is not
byte-stable, hence the checksum-the-committed-artifacts gate rather than a re-fit
equality assertion (Pitfall 2 — never re-fit inside the verify gate).

## Pins

Each line below is standard `sha256sum` format: `<64-hex><two spaces><relative-path>`.
`make verify-reproducibility` greps `^[a-f0-9]{64}  <path>`, recomputes the sha256,
and matches. 3-state rule: a present+matching pin is OK; a present+mismatching pin
FAILs (exit non-zero); an absent pin FAILs UNLESS it is `reports/ichi.pdf` (the ONLY
allow-listed PENDING path — rendered in Plan 05-03, its sha finalized at render time
in Plan 05-04).

### Inputs

a72a4eeaf2805aaf6b89b993e25d6b9012b8a97d507ca7e40a2dac68ee9f412a  data/raw/ichi/0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F/67378253_67896653.parquet
213132afb1455a36d8cbee58e3ee1e0c99af74d9d136bb7e8cd28aa7e78496e5  analysis/uv.lock
2e92c498634b8929ed33edfe8d897b2b2abb6004ca303d866f6c42ed17dfde81  pnpm-lock.yaml

### Derived artifacts (run_id bdaf5c7ba5a2)

697ad360c7320330cb7196348dd8c6bcd6edb99d79a2bad1d4b2966fd32e6190  data/fits/ichi/bdaf5c7ba5a2/fit_report.json
f578b56624e9bc08f4cb6a1828ed5707fd9450f2fb46cd062e066a89700d0851  data/fits/ichi/bdaf5c7ba5a2/gate_report.json
886f18e74fe29a7d60b369bfbc92304bc59dd8dc8a854fbfd8691ab98f8ffea2  data/fits/ichi/bdaf5c7ba5a2/firing_condition.json
48fd53c0ac89a78464f86414c3533fb309ca76353e75620dcf1008258f6e51c6  data/fits/ichi/bdaf5c7ba5a2/joint_dist.json
5cccc58adaed0a79b8888ece6dc7540bd464a9e1fdb9de7cf95deefe4a6a63c4  data/fits/ichi/bdaf5c7ba5a2/strip_degenerate.json
21ea3e4998bc1a38a2208dd771677f69c6733eae1bc74e39163e161fb0d601e3  data/fits/ichi/bdaf5c7ba5a2/stress_report.json
7879545dff4911451c6f9cd34d6bb8f3f26eebf1e9981b11cef90a4bf3f7583a  data/fits/ichi/bdaf5c7ba5a2/sensitivity_sweep.json
51b22b3c0767f169c395489ecb1b0ec537ea2aaaa0d7dd7d9458c16f78a4ae42  data/fits/ichi/bdaf5c7ba5a2/residuals.parquet
825b830404f5ad99cd0ed514d0cb2fa25319cb500ba617bd5908fb3e41a6af37  data/fits/ichi/bdaf5c7ba5a2/CORRECTIONS.md
ebff6d9b2d4c7b0d533ba89640387613b1d007fef7c007b434cbf568d88d7d5d  data/fits/ichi/bdaf5c7ba5a2/run_log.txt

### Deliverable (PENDING until rendered)

The Iteration-1 PDF is pinned but is the ONLY allow-listed PENDING path: until
Plan 05-03 renders it, `verify-reproducibility` logs `PENDING: reports/ichi.pdf`
and does NOT fail. Plan 05-04 replaces the all-zero placeholder sha with the real
render sha. (The placeholder below is intentionally non-matching; the path is
absent on a clone so the 3-state rule treats it as PENDING, never MISMATCH.)

0000000000000000000000000000000000000000000000000000000000000000  reports/ichi.pdf

## Provenance (non-checksummed)

- **Subgraph block-pins:** blockRange = [67378253, 67896653], chainId = 42220 (Celo) — from `fit_report.json`.
- **Spot-check seed (REPORT-02):** `int(sha256("bdaf5c7ba5a2")[:8], 16)` = `0xe33ecd48` = `3812543816` (decimal). The 5 spot-check rows are a seeded `numpy.random.default_rng(3812543816).choice(832, 5, replace=False)` draw from the committed panel parquet; a fresh clone re-derives the identical 5 rows. Blockscout URLs of the form `https://celo.blockscout.com/tx/0x...`.
- **Panel population (PANEL-04):** the panel parquet has **832 raw rows** (retaining `txHash`); after the PANEL-04 phantom-transfer filter these reduce to **778 arrival events** used in the DGP fit. The spot-check draws from the 832-row parquet because it carries `txHash`.
- **Lockfiles:** the tracked lockfiles are `analysis/uv.lock` and `pnpm-lock.yaml` (the pnpm lockfile, not an npm one — no npm lockfile exists). A repo-root `uv.lock` likewise does not exist. Only the two tracked lockfiles are pinned (CONTEXT decision 6).
