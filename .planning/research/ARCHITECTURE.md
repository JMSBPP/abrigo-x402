# Architecture Research

**Domain:** Empirical FX-cashflow-modeling pipeline (TypeScript x402 data-fetch + Python DGP estimation + Carr–Madan hedge design) for MiniPay-hosted Celo protocols.
**Researched:** 2026-05-25
**Confidence:** MEDIUM-HIGH (HIGH on layering and language boundary; MEDIUM on free-tier query budget allocation, calibrated against `PROJECT.md` and `SOMNIA_DRAFT.md` only — no live x402 traffic yet measured for this repo).

---

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│   L0 — PROTOCOL SPEC (the only file Iteration 2 swaps)                   │
│   protocols/myriad.toml   protocols/halo.toml   protocols/<next>.toml    │
│   { contract_addresses, subgraph_id, revenue_token, data_cost_class,     │
│     k_estimator_hint, demand_window_override }                           │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │ (read by every layer below)
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│   L1 — DATA-FETCH (TypeScript)                                           │
│   ┌─────────────────┐  ┌──────────────────┐  ┌────────────────────────┐  │
│   │ x402-client.ts  │  │ subgraph-client  │  │ blockscout-fallback.ts │  │
│   │ (Agora pricing  │  │ (@graphprotocol/ │  │ (RPC-direct event      │  │
│   │ instrumentation)│  │ client-cli + -x402)│ logs when subgraph cold)│  │
│   └────────┬────────┘  └────────┬─────────┘  └───────────┬────────────┘  │
│            └────────────────────┴────────────────────────┘               │
│                                 │ writes Parquet + manifest.json         │
└─────────────────────────────────┼────────────────────────────────────────┘
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│   L2 — RAW CACHE (filesystem, content-addressed)                         │
│   data/raw/<protocol>/<subgraph_id>/<block_range>.parquet                │
│   data/raw/<protocol>/manifest.json   (query-cost ledger, repro hash)    │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│   L3 — PANEL CONSTRUCTION (Python)                                       │
│   ┌───────────────────┐  ┌────────────────────┐  ┌────────────────────┐  │
│   │ ingest.py         │  │ revenue_leg.py     │  │ data_leg.py        │  │
│   │ (Parquet → polars)│  │ (Mento transfers,  │  │ (stipulated NHPP   │  │
│   │                   │  │ event-timestamped) │  │ prior from window) │  │
│   └─────────┬─────────┘  └─────────┬──────────┘  └─────────┬──────────┘  │
│             └────────────┬─────────┴───────────────────────┘             │
│                          ▼                                               │
│   ┌──────────────────────────────────────────────────────────────────┐   │
│   │ panel.py — joint (t, dK_D, dK_AI, rho) DataFrame, ISO8601-UTC    │   │
│   └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│   L4 — DGP ESTIMATION (Python)                                           │
│   ┌────────────────────┐  ┌─────────────────────┐  ┌──────────────────┐  │
│   │ nhpp_inar.py       │  │ hawkes_mv.py        │  │ lr_test.py       │  │
│   │ (Kirchner 2015)    │  │ (Daw & Pender 2017) │  │ (Chen et al 2017)│  │
│   └─────────┬──────────┘  └──────────┬──────────┘  └─────────┬────────┘  │
│             └────────────────┬───────┴──────────────────────┘            │
│                              ▼                                           │
│   ┌──────────────────────────────────────────────────────────────────┐   │
│   │ fit_report.json — chosen process + params + LR p-value           │   │
│   └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│   L5 — CROSS-LEG DEPENDENCE (Python; activated only when needed)         │
│   joint_dist.py — empirical copula on (dK_D, dK_AI); vine only if BIC    │
│   prefers it over Gaussian. Output: copula params + tail-dependence λ_L. │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│   L6 — HEDGE DESIGN (Python, symbolic + numeric)                         │
│   carr_madan_strip.py — strike grid + weights ψ(K) on joint C(t)         │
│   falsification.py — gates 1–4 from SOMNIA_DRAFT §FUNCTIONAL FORM        │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│   L7 — REPORTING (Jupyter + Quarto/Pandoc → PDF)                         │
│   notebooks/<protocol>_iteration.ipynb  →  reports/<protocol>.pdf        │
│   (per memory feedback_pdf_deliverable.md — PDF is the deliverable)      │
└──────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Owns | Implementation | Lang |
|-----------|------|----------------|------|
| `protocol_spec` (L0) | All per-protocol parameters | TOML files in `protocols/` | — |
| `x402-client` | Paid GraphQL calls, κ instrumentation, payment header retry | `@graphprotocol/client-x402` over Agora | TS |
| `subgraph-client` | Codegen'd typed query layer, pagination | `@graphprotocol/client-cli` | TS |
| `blockscout-fallback` | Raw event logs when subgraph behind chain head | `viem` + Blockscout v2 REST | TS |
| `raw cache` (L2) | Content-addressed Parquet + cost ledger | filesystem; no DB | — |
| `ingest` | Parquet → polars/pandas, schema validation | `polars` + `pandera` | Py |
| `revenue_leg` | Mento-stablecoin inflows, event-timestamped | pandas + viem-style decoded logs | Py |
| `data_leg` | NHPP prior stipulated in `[free, $390/mo]` window | scipy.stats + protocol_spec | Py |
| `panel` | Joint event-timestamped DataFrame, UTC | polars | Py |
| `nhpp_inar` | INAR(p) bin-count fit | statsmodels + custom (Kirchner 2015) | Py |
| `hawkes_mv` | Multivariate Hawkes MLE, per-leg kernels | `tick` library (Bacry et al.) | Py |
| `lr_test` | Likelihood-ratio test, NHPP nested in Hawkes | scipy.stats.chi2 | Py |
| `joint_dist` | Empirical copula + tail-dependence | `copulae` or `pyvinecopulib` | Py |
| `carr_madan_strip` | Strip-weight grid ψ(K) replicating ϕ(C(t)) | sympy + numpy | Py |
| `falsification` | Apply 4 gates from SOMNIA_DRAFT | pure Python | Py |
| `reporting` | Notebook + PDF render | Jupyter + Quarto or `nbconvert --to pdf` | Py |

---

## Recommended Project Structure

```
abrigo-x402/
├── protocols/                       # L0 — SWAP SURFACE for Iteration 2+
│   ├── myriad.toml                  # Iteration 1
│   ├── halo.toml                    # Iteration 2 (stub now, fill later)
│   └── _schema.toml                 # shared schema, validated by pydantic/zod
│
├── fetch/                           # L1 — TypeScript
│   ├── package.json
│   ├── tsconfig.json
│   ├── .graphclientrc.yml           # @graphprotocol/client-cli config
│   ├── src/
│   │   ├── x402-client.ts           # paid-call wrapper, retries on 402
│   │   ├── subgraph-client.ts       # codegen'd queries
│   │   ├── blockscout.ts            # RPC + Blockscout fallback
│   │   ├── kappa-meter.ts           # Agora-decomposition instrumentation
│   │   ├── cost-ledger.ts           # writes manifest.json per query
│   │   └── cli.ts                   # `pnpm fetch <protocol>` entrypoint
│   └── tests/
│
├── data/                            # L2 — git-ignored cache
│   └── raw/<protocol>/<subgraph_id>/<block_range>.parquet
│
├── analysis/                        # L3–L6 — Python (uv-managed venv)
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── src/abrigo_x402/
│   │   ├── ingest.py                # L3
│   │   ├── panel.py                 # L3
│   │   ├── revenue_leg.py           # L3
│   │   ├── data_leg.py              # L3
│   │   ├── dgp/
│   │   │   ├── nhpp_inar.py         # L4
│   │   │   ├── hawkes_mv.py         # L4
│   │   │   └── lr_test.py           # L4
│   │   ├── dependence/
│   │   │   └── joint_dist.py        # L5
│   │   ├── hedge/
│   │   │   ├── carr_madan_strip.py  # L6
│   │   │   └── falsification.py     # L6
│   │   └── protocol_spec.py         # loads protocols/*.toml
│   └── tests/
│
├── notebooks/                       # L7
│   ├── myriad_iteration.ipynb
│   └── halo_iteration.ipynb         # later
│
├── reports/                         # rendered PDFs (git-tracked)
│   └── myriad.pdf
│
├── .planning/                       # GSD planning artifacts
└── notes/
```

### Structure Rationale

- **`protocols/` at repo root, not nested:** maximally visible — this is THE swap surface. Anything Iteration-2-specific that lives outside this folder is a leak.
- **`fetch/` and `analysis/` as sibling top-level packages, not one root project:** they have distinct package managers (pnpm vs uv), distinct runtimes (Node vs Python), and distinct lifecycles (fetch runs episodically against the 100k/mo budget; analysis runs locally over the cache as often as wanted). Coupling them in one project breaks both dependency graphs.
- **`data/raw/` content-addressed by `(protocol, subgraph_id, block_range)`:** lets Iteration 2 share zero data with Iteration 1 cleanly, and lets re-runs hit cache for free. Git-ignored — `manifest.json` is the only authoritative record.
- **`reports/` git-tracked:** PDFs are deliverables per memory `feedback_pdf_deliverable.md`. Notebooks are reproducible inputs; PDFs are evidence of having shipped.

---

## TypeScript ↔ Python Boundary

**Decision: File handoff via Parquet + a JSON manifest. No HTTP, no process spawn.**

| Option | Verdict | Rationale |
|--------|---------|-----------|
| **Parquet files + JSON manifest (CHOSEN)** | ✓ | Schema-typed, columnar, polars/pandas/duckdb-native. Decouples the 100k/mo paid-call lifecycle from the unlimited-rerun analysis lifecycle. Cache is inspectable. |
| HTTP service (TS server, Python client) | ✗ | Adds a long-running process for what is fundamentally a batch ETL. No upside; complicates reruns. |
| `child_process.spawn` (Python invokes TS) | ✗ | Couples reruns to repaying x402 fees. Burns the 100k budget on every notebook re-execution. |
| Shared in-process (Pyodide / nodejs in Python) | ✗ | Toolchain overhead enormous; no benefit for batch ETL. |

**Why this is the right boundary:** the 100k Graph queries/mo cap is a hard physical constraint, and the entire point of the pipeline is that *estimation* and *hedge design* must be cheap to iterate on after data is paid for once. The file boundary makes the paid step idempotent and the rest free.

**Schema discipline:** `protocols/_schema.toml` is mirrored by a pydantic model (`analysis/src/abrigo_x402/protocol_spec.py`) and a zod schema (`fetch/src/protocol-spec.ts`). Both validate the same TOML on load — if they drift, CI fails.

---

## Iteration-1 vs Iteration-2 Swap Surface

**Iteration 2 (Halo) must touch only these files:**

| File | Iteration-1 value (Myriad) | Iteration-2 value (Halo) |
|------|----------------------------|--------------------------|
| `protocols/myriad.toml` → `protocols/halo.toml` | prediction-market settlement contracts on Celo | Halo receipt-OCR settlement contracts |
| `protocols/<name>.toml :: data_cost_class` | `"per-event-oracle"` | `"per-scan-ocr"` |
| `protocols/<name>.toml :: subgraph_id` | Myriad subgraph (verify `_meta.block.number`) | Halo subgraph |
| `protocols/<name>.toml :: revenue_token` | `cCOP` (or whichever Mento) | per-Halo deployment |
| `protocols/<name>.toml :: demand_window_override` | unset (use default `[free, $390/mo]`) | possibly adjusted for OCR cost class |
| `notebooks/<name>_iteration.ipynb` | new notebook, same template | new notebook, same template |

**Everything in `fetch/src/` and `analysis/src/` must remain untouched.** If a Halo-specific code path appears, it goes behind a `data_cost_class` dispatch inside the relevant module (e.g., `data_leg.py` reads `cost_class` and picks the right prior).

**Leak detection:** before declaring Iteration 1 done, `grep -r "myriad" fetch/src analysis/src` must return zero hits. Any match indicates a leak that will block Iteration 2.

---

## Free-Tier Resource Budget

**Total monthly budget: 100,000 Graph queries (Decentralized Network free tier).**

| Layer | Allocated/mo | Use | Notes |
|-------|--------------|-----|-------|
| L1 cold backfill (first run per protocol) | 30,000 | One-shot historical pull, paginated `first: 1000, skip: …` | Cached forever in `data/raw/`. Should be one-time per `subgraph_id`. |
| L1 incremental updates | 15,000 | Daily top-up pulls during dev (`block_gte: latest_cached_block`) | ~500/day × 30. |
| L1 κ-instrumentation experiments | 10,000 | Vary `first`, `skip`, fields to map Agora cost surface | Throwaway; pure science budget. |
| L1 Iteration-2 (Halo) cold backfill | 25,000 | Same as Myriad, second protocol | Iteration 2 must fit inside the same monthly cap. |
| Reserve / contingency | 20,000 | Buffer for re-pulls, subgraph reindex churn, ad-hoc | Hard floor; do not pre-allocate. |

**Celo RPC (`forno.celo.org`)** is unmetered for our load profile but rate-limited. Pagination: `eth_getLogs` with `fromBlock`/`toBlock` windows ≤ 10k blocks (Celo ~5s block time → ~13.9 hours/window). Used as a fallback only when the subgraph's `_meta.block.number` lags head by > 1 hour (per PROJECT.md note on Celo subgraph lag).

**Blockscout v2 REST** is unmetered without an API key; used for ABI fetch and verification, not bulk event pulls.

**Hard gate:** `fetch/src/cost-ledger.ts` writes a running `queries_consumed_this_month.json`; CLI refuses to fetch if projected spend would exceed 90,000/mo. Forces an explicit `--force` flag.

---

## Architectural Patterns

### Pattern 1: Protocol Spec as Single Source of Truth

**What:** All per-protocol parameters live in `protocols/<name>.toml`. Both TS and Py load this file via mirrored schemas (zod + pydantic).
**When to use:** Always; this is the project's main reuse mechanism.
**Trade-offs:** Adds a schema-sync chore (CI must check the two schemas match); pays for itself the first time Iteration 2 ships without code edits.

**Example:**
```toml
# protocols/myriad.toml
name = "myriad"
chain_id = 42220                              # Celo mainnet
data_cost_class = "per-event-oracle"
demand_window_lower_usd_per_month = 0         # Graph free tier
demand_window_upper_usd_per_month = 390       # Dune Plus

[contracts]
settlement = "0x..."                          # to fill in P1
market_factory = "0x..."

[subgraph]
id = "..."                                    # to fill in P1
min_block_number = 0
preferred_endpoint = "decentralized"

[revenue]
token_symbol = "cCOP"
token_address = "0x..."

[data_leg_prior]
kappa_estimator = "agora-additive"
rate_per_day_mean = 1.0                       # stipulated NHPP prior
rate_per_day_sd = 0.5
```

### Pattern 2: Paid Step is Idempotent, Cached, Inspectable

**What:** `pnpm fetch myriad` is the only command that spends from the 100k budget. It writes Parquet + appends to `manifest.json` (which query, which block range, how much it cost). Re-running it consults the manifest and skips already-cached ranges.
**When to use:** Mandatory for any paid data source on a budget.
**Trade-offs:** Slight complexity vs naive fetch; eliminates the entire class of "I burned my month's queries re-running a notebook" failures.

### Pattern 3: Estimation is a Pure Function of the Cache

**What:** L3–L6 modules only read from `data/raw/` and `protocols/`, never from the network. Notebooks can be re-run unboundedly during DGP iteration.
**When to use:** Always — this is the discipline that lets you actually iterate on Kirchner-INAR vs Hawkes specifications without going over budget.
**Trade-offs:** None; this is just clean separation of concerns.

### Pattern 4: Falsification Gates as Explicit Code

**What:** `analysis/src/abrigo_x402/hedge/falsification.py` encodes the four gates from `SOMNIA_DRAFT.md §FUNCTIONAL FORM` (vol-of-vol > 0; positive skew/fat tails; Hawkes self-excitation; USDC depeg jump) plus the demand-window gate from `PROJECT.md`. Each gate returns `(passed: bool, evidence: dict)`. The hedge-design step is gated on at least one passing.
**When to use:** This is non-negotiable for this project — its premise is that null results are publishable.
**Trade-offs:** Forces you to write the failure case before the success case, which is the point.

### Pattern 5: Notebook as Thin Orchestrator, Library as Substance

**What:** `notebooks/<protocol>_iteration.ipynb` contains almost no logic — just `from abrigo_x402 import …`, parameter overrides, and rendered tables/plots. All math is in the library, unit-tested.
**When to use:** Always for a reproducibility-focused pipeline; notebooks are bad VCS citizens but excellent PDF generators.
**Trade-offs:** Slight friction in early exploration (you'll be tempted to leave logic in the notebook); pays off the first time you need to re-run with one parameter changed.

---

## Data Flow

### End-to-End Forward Path (one-way; no backflow)

```
protocols/myriad.toml
        │
        ▼
fetch/cli.ts ──reads spec──> x402-client + subgraph-client
        │                          │
        │                          ▼
        │                   Celo subgraph (paid)  ──fallback──> Blockscout/RPC
        │                          │
        │                          ▼
        └────────────> data/raw/myriad/*.parquet + manifest.json
                                   │
                                   ▼  (file handoff — language boundary)
                          analysis/ingest.py
                                   │
                                   ▼
                          panel.py (joint DataFrame)
                                   │
                       ┌───────────┴───────────┐
                       ▼                       ▼
              dgp/nhpp_inar.py        dgp/hawkes_mv.py
                       │                       │
                       └───────────┬───────────┘
                                   ▼
                            dgp/lr_test.py  ──> fit_report.json
                                   │
                                   ▼
                       dependence/joint_dist.py (if needed)
                                   │
                                   ▼
                       hedge/falsification.py  ──gates──> abort or continue
                                   │
                                   ▼
                       hedge/carr_madan_strip.py
                                   │
                                   ▼
                       notebooks/myriad_iteration.ipynb
                                   │
                                   ▼
                            reports/myriad.pdf
```

No bidirectional arrows. The only feedback path is human: read the report, edit code or the spec, re-run.

### State Locations

| Layer | State persistence | Lifetime |
|-------|-------------------|----------|
| L0 spec | Git-tracked TOML | Permanent |
| L1 cost ledger | `data/raw/<protocol>/manifest.json` | Permanent (budget audit trail) |
| L2 cache | `data/raw/**.parquet` | Git-ignored; rebuildable from L1 |
| L3 panel | Recomputed each notebook run; optionally cached `data/panel/` | Cheap to regenerate |
| L4 fit results | `data/fits/<protocol>/fit_report.json` | Git-trackable for diffing across reruns |
| L7 PDFs | `reports/*.pdf` | Git-tracked — these are the deliverables |

---

## Build Order (Phase-Ready)

Strict dependency order; each block gates the next:

1. **L0 + L1 skeleton + smoke test** — `protocols/myriad.toml` populated with verified addresses (PROJECT.md Active item 1) + `fetch/` initialized with `@graphprotocol/client-cli` codegen, one trivial paid call working end-to-end with budget tracking. *Ships:* a working `pnpm fetch myriad --dry-run` and one Parquet file.
2. **L1 full backfill + L2 cache hygiene** — paginated historical pull of Myriad settlement events; manifest.json with cost accounting; Blockscout fallback wired. *Ships:* `data/raw/myriad/` populated for the trailing observable window.
3. **L3 panel** — `ingest.py` + `revenue_leg.py` + `data_leg.py` + `panel.py`. Schema validated. Event timestamps in UTC, idempotent. *Ships:* a notebook cell that prints the joint panel head.
4. **L4 DGP estimation** — NHPP first (it's the null + cheapest), then Hawkes, then LR test. Each in its own module, each unit-tested on synthetic data with known parameters. *Ships:* `fit_report.json` for Myriad.
5. **L5 dependence** *(conditional — skip if LR test rejects Hawkes and legs look independent on plot)* — copula fit. *Ships:* a `joint_dist.json` or a documented "not needed" note.
6. **L6 hedge design + falsification** — falsification gates first (might short-circuit the whole step with a null-result PDF, which is a legitimate deliverable per PROJECT.md). Then Carr–Madan strip if any gate passes. *Ships:* hedge sketch + PDF.
7. **L7 report rendering** — Quarto/nbconvert pipeline, PDF committed. *Ships:* `reports/myriad.pdf`.
8. **Iteration 2 (Halo)** — only after L7 ships for Myriad. Touches only `protocols/halo.toml` and `notebooks/halo_iteration.ipynb`. If it requires touching any file under `fetch/src/` or `analysis/src/`, Iteration 1's swap-surface design failed and must be fixed before Iteration 2 continues.

**Blocking relationships:**

```
L1 ─┬─> L2 ──> L3 ──> L4 ──> L6 ──> L7 ──> Iteration 2
    │                  │       ▲
    └──> κ data ───────┘       │
                  L5 (optional)┘
```

L4 cannot start before L3 (panel must exist). L6 cannot start before L4 (gates need fit params). L5 is optional and parallel to early L6 work. Iteration 2 is gated on L7 to ensure swap surface is real.

---

## Scaling Considerations

This is a research pipeline, not a service; "scale" means "number of protocols evaluated", not "users".

| Scale | Architecture adjustments |
|-------|--------------------------|
| 1 protocol (Iteration 1) | Single-machine, local Parquet, single-folder cache. Current design. |
| 2–5 protocols (Iteration 2 + minor MiniPay candidates) | Same as above. The 100k/mo cap becomes the binding constraint, not compute. |
| 5–20 protocols | Consider duckdb over the Parquet cache for cross-protocol queries; move `fit_report.json` to a tiny SQLite. Still single-machine. |
| 20+ protocols | At this point the project has succeeded enough that it deserves a real pipeline orchestrator (Prefect / Dagster) and a paid Graph tier. Out of scope for this iteration. |

### Scaling Priorities

1. **First bottleneck: the 100k/mo Graph query cap.** Mitigations already in design: cache + manifest + 90k soft cap + Blockscout fallback for bulk events.
2. **Second bottleneck: subgraph lag on Celo** (per PROJECT.md). Mitigation: Blockscout/RPC fallback path in L1, with `_meta.block.number` checked before each session.
3. **Third bottleneck (much later): Hawkes MLE compute time** scales O(N²) in event count with `tick`'s default kernel. Mitigations: exponential-kernel parameterization, sub-sampling. Only relevant if Myriad has >100k events in the observable window, which is unlikely.

---

## Anti-Patterns

### Anti-Pattern 1: Network calls inside notebooks
**What people do:** `await fetch(graphqlEndpoint, …)` from inside the iteration notebook.
**Why it's wrong:** Every notebook re-run burns budget. Couples estimation iteration speed to x402 spend. Inverts the project's economics.
**Do this instead:** Network calls live only in `fetch/`. Notebooks read Parquet.

### Anti-Pattern 2: Protocol-specific branching in core modules
**What people do:** `if protocol == "myriad": …` inside `nhpp_inar.py` or `panel.py`.
**Why it's wrong:** Defeats the swap surface; Iteration 2 will require core edits.
**Do this instead:** All branching keys off `protocol_spec` fields (`data_cost_class`, `revenue_token`, etc.). Add a new spec field if needed.

### Anti-Pattern 3: Treating subgraph data as ground truth
**What people do:** Build the panel directly from subgraph responses; assume completeness.
**Why it's wrong:** Celo subgraphs lag; `_meta.block.number` matters; some events may be missing or reindexed retroactively.
**Do this instead:** Stamp every fetch with `subgraph_meta_block` in the manifest. Validate event counts against a Blockscout cross-check for at least one block range per session.

### Anti-Pattern 4: Skipping the falsification gates
**What people do:** Carr–Madan strip whether or not gates 1–4 pass, because "the math is interesting".
**Why it's wrong:** The whole project's thesis depends on the gates being non-trivial. A pretty strip on a regime where a linear hedge dominates is misleading.
**Do this instead:** `falsification.py` runs first, prints all gates, requires at least one pass before `carr_madan_strip.py` will execute. Null result PDF is a valid deliverable per PROJECT.md.

### Anti-Pattern 5: Re-pulling cached ranges
**What people do:** Naive script that just refetches a year of data on every run.
**Why it's wrong:** Burns the monthly query budget on idempotent work.
**Do this instead:** `cost-ledger.ts` consults `manifest.json` and refuses to re-pay for a `(subgraph_id, block_range)` already present.

### Anti-Pattern 6: Stipulating the data-leg prior inside a Python module
**What people do:** Hardcode the NHPP rate prior in `data_leg.py`.
**Why it's wrong:** Iteration 2 (per-scan OCR cost class) needs a different prior; you'll edit code instead of spec.
**Do this instead:** Prior parameters live in `protocols/<name>.toml :: [data_leg_prior]`. `data_leg.py` reads them.

---

## Integration Points

### External Services

| Service | Integration pattern | Notes |
|---------|---------------------|-------|
| The Graph Decentralized Network | `@graphprotocol/client-cli` codegen + `@graphprotocol/client-x402` paid wrapper | 100k/mo cap. Verify `_meta.block.number` per session. Per PROJECT.md, Celo subgraph availability lags other chains. |
| Celo RPC (`forno.celo.org`) | `viem` PublicClient | Free, rate-limited. Use for fallback `eth_getLogs` in ≤10k-block windows. Chain ID 42220. |
| Blockscout (Celo) | v2 REST, no API key | Used for ABI verification + bulk event fallback. Pagination via `next_page_params`. |
| Mento stablecoin contracts (cCOP, cKES, …) | `viem` ABI decode of `Transfer` events | On-chain ground truth for revenue leg. |
| Off-chain FX cross-rate (USDC/USD, local-stable/USD) | CoinGecko/Messari REST, daily, cached | Per `SOMNIA_DRAFT.md` no-native-oracle constraint. Stamped into panel with provenance. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `fetch/` ↔ `analysis/` | Parquet files + `manifest.json` over filesystem | No HTTP, no spawn. See "TypeScript ↔ Python Boundary" above. |
| `protocols/` ↔ `fetch/` | TOML loaded via zod schema | Schema lives in `fetch/src/protocol-spec.ts`. |
| `protocols/` ↔ `analysis/` | TOML loaded via pydantic schema | Schema lives in `analysis/src/abrigo_x402/protocol_spec.py`. Must mirror zod schema; CI check. |
| L4 ↔ L6 | `fit_report.json` on disk | Decouples DGP fitting from hedge design; gate inspection is just JSON read. |
| Notebook ↔ library | `from abrigo_x402 import …` | Notebooks contain orchestration + presentation only. |

---

## Sources

- `/home/jmsbpp/apps/d2p/abrigo/abrigo-x402/.planning/PROJECT.md` (constraints, free-tier budget, Iteration 1/2 swap requirement, falsification gate) — HIGH
- `/home/jmsbpp/apps/d2p/abrigo/abrigo-x402/CLAUDE.md` (domain non-negotiables, Carr–Madan + Panoptic stance, x402-on-Celo not -on-Base) — HIGH
- `/home/jmsbpp/apps/d2p/abrigo/abrigo-analytics/notes/SOMNIA_DRAFT.md` (formal cost model: primal/dual, cashflow process `dC_t`, arrival process NHPP-vs-Hawkes via Kirchner / Daw & Pender / Chen, four falsification gates) — HIGH
- `/home/jmsbpp/apps/d2p/abrigo/abrigo-x402/notes/DRAFT.md` (user-story origin: cCOP / Dune $369 incident; foreign-currency cashflow framing) — HIGH
- Memory `feedback_pdf_deliverable.md` (PDF output discipline) — HIGH
- Memory `feedback_python_venv.md` (uv-managed venv) — HIGH
- Memory `feedback_phased_buy_discipline.md` (evidence-before-spend; free-tier-only justified) — HIGH
- `@graphprotocol/client-x402` and `@graphprotocol/client-cli` (Iteration-1 stack mandated by PROJECT.md) — MEDIUM, unverified against current docs in this pass; flagged for L1 implementation phase to double-check version-specific Agora pricing introspection hooks
- `tick` (Bacry et al., Hawkes process MLE in Python) — MEDIUM, well-known library; specific kernel choices to validate at L4 phase

---

*Architecture research for: empirical FX-cashflow modeling pipeline (Iteration 1 = Myriad, Iteration 2 = Halo)*
*Researched: 2026-05-25*
