---
phase: 01-l1-data-fetch-skeleton-free-tier-discipline
plan: 07
subsystem: payments
tags: [x402, base-sepolia, node-http, vitest, eip-712, eip-3009, usdc, viem]

# Dependency graph
requires:
  - phase: 01-l1-data-fetch-skeleton-free-tier-discipline
    provides: "01-00 — x402 exports probe (01-00-x402-exports.txt); BASE_SEPOLIA_CHAIN_ID + BASE_SEPOLIA_USDC_ADDRESS constants"
  - phase: 01-l1-data-fetch-skeleton-free-tier-discipline
    provides: "01-01 — baseSepoliaClient viem singleton; testDirname ESM helper"
  - phase: 01-l1-data-fetch-skeleton-free-tier-discipline
    provides: "01-02 — cost-ledger appendLedger/readLedger + endpoint enum 'x402-mock-sepolia' + chain enum 'base-sepolia'"
provides:
  - "fetch/src/x402-mock/server.ts: startMockServer(port=0) — node:http 402 server with x402 v1 PaymentRequirements, structural X-PAYMENT validation, X-PAYMENT-RESPONSE settlement echo"
  - "fetch/src/x402-mock/server.ts: validateXPaymentHeader(b64) — exported structural validator"
  - "fetch/src/x402-mock/server.ts: PAYMENT_REQUIREMENTS — x402 v1 body with network='base-sepolia' (named, not CAIP-2)"
  - "fetch/src/x402-mock/client-bridge.ts: makeFetchWithPayment(opts) — wraps fetch with @x402/fetch x402Client + @x402/evm/exact/client registerExactEvmScheme"
  - "fetch/src/x402-mock/client-bridge.ts: fetchWithPayment — lazy convenience wrapper respecting vi.stubEnv PRIVATE_KEY"
  - "STACK DRIFT INVENTORY: @x402/evm v2.13 v1-protocol ExactEvmSchemeV1 registers on NAMED networks ('base-sepolia') not CAIP-2 ('eip155:84532'); v2-protocol uses different envelope shape (amount/resource/accepted/PAYMENT-SIGNATURE-header). Documented for Wave-3 plan 01-08 consumers."
affects:
  - "01-08 (Wave 3 — CLI integration may invoke x402-mock for end-to-end product test)"
  - "Phase 5 PDF deliverable (real-mainnet x402 paid-query footnote, if elected)"

# Tech tracking
tech-stack:
  added:
    - "@x402/fetch@2.13.0 (x402Client + wrapFetchWithPayment — already pinned in 01-00; first live use here)"
    - "@x402/evm/exact/client (registerExactEvmScheme subpath — already pinned in 01-00; first live use here)"
    - "node:http (built-in — chosen over express/hono for the ~60-line sketch per RESEARCH §F)"
  patterns:
    - "Live-probe drift adaptation: the plan body's static text (CAIP-2 'eip155:84532') is overridden by the actual @x402/evm v2.13 wire-format ('base-sepolia') discovered via `node -e \"...createPaymentPayload(...)\"` probe. The plan body authorizes this adaptation explicitly."
    - "EIP-712 domain extras: PaymentRequirements.accepts[*].extra = {name: 'USDC', version: '2'} is load-bearing for ExactEvmScheme.createPaymentPayload — without it, signEIP3009Authorization throws."
    - "Header-only mode default: structural X-PAYMENT validation (scheme/network/sig-shape/payer-shape) is the Phase-1 CI mode; X402_MOCK_REAL_SETTLE=1 env-toggle is the manual-only escalation path."
    - "Test artifact isolation: TEST_LEDGER path under fetch/data/raw/ which is .gitignored (01-02 commit 729a17e); test cleanup via rm before re-run."

key-files:
  created:
    - "fetch/src/x402-mock/server.ts (~160 lines — node:http 402 mock + structural validator + paymentResponseHeader encoder)"
    - "fetch/src/x402-mock/client-bridge.ts (~55 lines — makeFetchWithPayment factory + lazy fetchWithPayment)"
  modified:
    - "fetch/tests/x402_mock.test.ts (was describe.todo stub; now 3 passing tests: bare 402 / round-trip / bad-network rejection + ledger row write)"

key-decisions:
  - "Adopted x402 v1 protocol (x402Version=1, header=X-PAYMENT, network='base-sepolia') over v2 (x402Version=2, header=PAYMENT-SIGNATURE, network='eip155:84532', schema-renamed envelope) — v1 envelope matches the plan's structural validator verbatim."
  - "Added PaymentRequirements.accepts[0].extra={name:'USDC', version:'2'} for EIP-712 domain (required by @x402/evm v2.13)."
  - "Mock validator rejects malformed X-PAYMENT via 402 + X-PAYMENT-RESPONSE.errorReason instead of HTTP 400 — matches RESEARCH §F sketch and gives the wrapFetchWithPayment client a uniform error surface."
  - "TEST_DEFAULT_PK = 0x{31 zero bytes}01 (well-known no-funds test key, address 0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf) — deterministic for CI; .env PRIVATE_KEY override for faucet-funded manual validation."

patterns-established:
  - "x402 v2.13 v1-protocol wire format: network is a NAMED string ('base-sepolia', 'ethereum', 'base', ...). v2-protocol uses CAIP-2 ('eip155:*') but a renamed schema (amount/accepted/PAYMENT-SIGNATURE)."
  - "Module-level lazy client construction: x402Client is built at first call in fetchWithPayment to respect vi.stubEnv-set env vars in tests."
  - "Cost-ledger row written for every mock round-trip with endpoint='x402-mock-sepolia', paid_real=false, chain='base-sepolia' — audit-trail bookkeeping without consuming the 90k/mo Graph cap."

requirements-completed: [FETCH-02]

# Metrics
duration: 6min
completed: 2026-05-26
---

# Phase 01 Plan 07: x402 Mock Server + Client Bridge Summary

**Self-hosted node:http 402 mock + @x402/fetch wrapFetchWithPayment round-trip on Base Sepolia (header-only mode default), with cost-ledger row write for the mock-mock-sepolia endpoint.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-05-26T14:10:44Z
- **Completed:** 2026-05-26T14:17:00Z
- **Tasks:** 2
- **Files modified:** 3 (2 created in src/x402-mock/, 1 rewritten in tests/)

## Accomplishments

- node:http 402 mock with structural X-PAYMENT validation + X-PAYMENT-RESPONSE settlement echo
- @x402/fetch x402Client + @x402/evm/exact/client registerExactEvmScheme bridge wired with viem privateKeyToAccount signer
- 3-test integration suite green (bare 402 / round-trip / bad-network rejection) including ledger-row write with endpoint='x402-mock-sepolia'
- STACK drift discovered + adapted: @x402/evm v2.13 v1-protocol uses named networks ('base-sepolia'), not the CAIP-2 form the plan body proposed

## Task Commits

Each task was committed atomically:

1. **Task 1: node:http 402 mock server** — `4718946` (feat)
2. **Task 1 (drift adaptation): adapt to v1-protocol named-network shape** — `27176ce` (fix)
3. **Task 2: client bridge + integration test + ledger row** — `e62b694` (feat)

_Note: Task 1 has two commits because the live x402 probe revealed wire-format drift from the plan-body's static proposal — the adaptation is a Rule-3 fix (blocking issue: the original CAIP-2 network throws "No network/scheme registered for x402 version: 1" inside createPaymentPayload)._

**Plan metadata commit** (this file + STATE.md + ROADMAP.md): committed last via final docs(01-07) commit.

## Files Created/Modified

- `fetch/src/x402-mock/server.ts` (created, 162 lines) — node:http 402 mock; exports `startMockServer`, `validateXPaymentHeader`, `PAYMENT_REQUIREMENTS`
- `fetch/src/x402-mock/client-bridge.ts` (created, 56 lines) — exports `makeFetchWithPayment(opts)` + lazy `fetchWithPayment`
- `fetch/tests/x402_mock.test.ts` (rewritten from describe.todo stub, 110 lines) — 3 passing tests + cost-ledger row write
- `fetch/src/x402-mock/.gitkeep` (deleted — replaced by real files)

## Decisions Made

- **x402 v1 protocol over v2** — v1 envelope `{scheme, network, payload: {authorization: {from, ...}, signature}}` matches the plan's structural validator. v2 would have required reshaping the validator (no top-level scheme/network; `accepted` envelope; PAYMENT-SIGNATURE header).
- **`base-sepolia` named network, not `eip155:84532`** — forced by @x402/evm v2.13's NetworkSchemaV1 (live-probed). The functional contract (402 → sign → retry → 200) is invariant; the wire-format shift is library plumbing the plan body explicitly authorizes adapting.
- **EIP-712 `extra: {name: 'USDC', version: '2'}` added to PaymentRequirements** — load-bearing for ExactEvmScheme.createPaymentPayload. Without it, signEIP3009Authorization throws before producing a signature.
- **Header-only mode is the Phase-1 default** — `X402_MOCK_REAL_SETTLE=1` env-toggle is documented but not implemented in this plan (deferred until a faucet-funded developer-machine workflow is exercised manually).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Adapted mock + tests from CAIP-2 `'eip155:84532'` to named `'base-sepolia'`**
- **Found during:** Task 1 → Task 2 transition (writing the client bridge probe)
- **Issue:** The plan body's PAYMENT_REQUIREMENTS proposed `accepts[0].network = 'eip155:84532'`, but live probe of `client.createPaymentPayload(requirements)` with `x402Version: 1` threw "No network/scheme registered for x402 version: 1" because @x402/evm v2.13's ExactEvmSchemeV1 registers on NAMED networks only (`base-sepolia`, `base`, `ethereum`, …). v2-protocol does register on `eip155:*` but uses a completely different envelope (renamed fields, PAYMENT-SIGNATURE header) that would have required reshaping the validator.
- **Fix:**
  - Changed `PAYMENT_REQUIREMENTS.accepts[0].network` from `'eip155:84532'` → `'base-sepolia'`
  - Changed `validateXPaymentHeader`'s network check from `'eip155:84532'` → `'base-sepolia'`
  - Changed `paymentResponseHeader`'s emitted network field similarly
  - Updated test assertions and the malformed-network case (`'eip155:1'` → `'ethereum'`)
- **Files modified:** `fetch/src/x402-mock/server.ts`, `fetch/tests/x402_mock.test.ts`
- **Verification:** `pnpm -C fetch test tests/x402_mock.test.ts --run` → 3/3 passing; full Phase-1 suite 80/80 passing; `pnpm -C fetch exec tsc --noEmit` clean
- **Committed in:** `27176ce` (server.ts) + `e62b694` (test + client-bridge)

**2. [Rule 3 - Blocking] Added `extra: {name: 'USDC', version: '2'}` to PaymentRequirements**
- **Found during:** Task 2 (first attempt at round-trip)
- **Issue:** `ExactEvmScheme.createPaymentPayload` throws `"EIP-712 domain parameters (name, version) are required in payment requirements for asset 0x036cbd…cf7e"` when `extra.name` or `extra.version` is missing. Required for the TransferWithAuthorization EIP-712 typed-data signature.
- **Fix:** Added `extra: { name: 'USDC', version: '2' }` to the single `accepts[]` entry. Matches the canonical Circle USDC EIP-712 domain (verified against Circle's deployed contract).
- **Files modified:** `fetch/src/x402-mock/server.ts`
- **Verification:** Round-trip test produces a valid 132-char EIP-712 signature; mock's structural validator accepts.
- **Committed in:** `27176ce`

---

**Total deviations:** 2 auto-fixed (both Rule-3 blocking — library wire-format mismatches the plan body's static proposal)
**Impact on plan:** Both adaptations were explicitly authorized by the plan's own caveat ("If `@x402/fetch` 2.13's exact API surface differs from RESEARCH §E… adapt imports to the actual surface, document the discrepancy in 01-07-SUMMARY.md"). Functional contract (402 → sign → retry → 200) is invariant; wire-format is library plumbing. No scope creep.

## Issues Encountered

- The plan's `must_haves.truths` listed `accepts[0].network='eip155:84532'` THREE times — but the plan body's NOTE in Task 2 explicitly contemplated wire-format drift and authorized adaptation. The CAIP-2 form is the x402 v2-protocol convention, which DOES register on `eip155:*` but requires a renamed envelope schema (amount/resource/accepted/PAYMENT-SIGNATURE) that would have invalidated the plan's structural validator. The v1-protocol named-network form was the smaller-blast-radius choice.

## Self-Check

Verifying claimed artifacts and commits:

- `fetch/src/x402-mock/server.ts` — FOUND
- `fetch/src/x402-mock/client-bridge.ts` — FOUND
- `fetch/tests/x402_mock.test.ts` — FOUND (real assertions, not describe.todo)
- Commit `4718946` — FOUND (feat 01-07 mock server initial)
- Commit `27176ce` — FOUND (fix 01-07 v1-protocol adaptation)
- Commit `e62b694` — FOUND (feat 01-07 client bridge + integration test)
- `pnpm -C fetch test tests/x402_mock.test.ts --run` → 3/3 pass
- `pnpm -C fetch test --run` → 11 files / 80 tests pass
- `pnpm -C fetch exec tsc --noEmit` → exit 0
- `grep -q "base-sepolia" fetch/src/x402-mock/server.ts` → match
- `grep -q "0x036cbd53842c5426634e7929541ec2318f3dcf7e" fetch/src/x402-mock/server.ts` → match
- `grep -q "x402-mock-sepolia" fetch/tests/x402_mock.test.ts` → match

## Self-Check: PASSED

## User Setup Required

None for CI / Phase-1 default. For manual `X402_MOCK_REAL_SETTLE=1` validation (NOT exercised in this plan):

1. Faucet-fund a Base Sepolia test wallet via Circle Faucet (`faucet.circle.com`) for test USDC + Coinbase CDP / Alchemy / QuickNode for test ETH
2. Set `PRIVATE_KEY=0x…` in `.env` (test wallet only — never mainnet keys)
3. Run with env-toggle: `X402_MOCK_REAL_SETTLE=1 pnpm -C fetch test tests/x402_mock.test.ts --run`
4. Verify on-chain tx via `baseSepoliaClient.getTransactionReceipt(hash)` — implementation deferred to a Phase-1.5 enrichment plan if/when needed

## Next Phase Readiness

- **Wave 3 (Plan 01-08)** can now invoke the x402 mock end-to-end if CLI-level integration is desired. The mock binds to an ephemeral port (`server.listen(0)`) so multiple parallel test files do not collide.
- **Phase 5 PDF deliverable** has a working code-path for the real-mainnet x402 footnote (deferred decision per CONTEXT.md); only the network field flips from `'base-sepolia'` → `'base'` and the signer's wallet must hold real USDC.
- **STACK drift documented in this SUMMARY** is load-bearing for any future plan that wires real x402 paid queries against The Graph mainnet gateway — the v1 vs v2 protocol choice determines header name (X-PAYMENT vs PAYMENT-SIGNATURE) and envelope shape.

---
*Phase: 01-l1-data-fetch-skeleton-free-tier-discipline*
*Completed: 2026-05-26*
