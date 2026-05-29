# Roadmap Extensions (post-v1.0)

Decisions taken about scope/milestones that follow the current v1.0 milestone
(Iter-1 ICHI + Iter-2 Steer + Phase-7 cross-iteration synthesis). Anything
recorded here is **not in scope for v1.0** but should inform:

1. How we structure v1.0 code (keep math/data polymorphic where the extension
   would re-use it; do not bake v1.0-only assumptions into v1.0 internals).
2. The "Future Work" section of the Phase 5 PDF deliverable.
3. The Phase 7 methodological-refinements note.

---

## v2.0 — Streaming Tokenization (Superfluid + x402 + SOMI claim-tokens)

**Decision date:** 2026-05-26
**Decision:** Option A (sibling-milestone extension after Phase 7) per user direction.
**Status:** Parked. Will become its own milestone (v2.0) once v1.0 closes.

### Primitive sketch

A transferable token representing a *claim on N units of x402-paid queries
and/or M seconds of SOMI-paid Somnia agent work*, funded by a Superfluid
stream (USDC on Base; possibly wrapped-SOMI for the AI leg). The token is the
capital primitive — mark-to-market continuously, transferable, composable
collateral. Hedge target shifts from spot cost to **PV of the stream**, which
natively matches Panoptic perpetual premium-stream shape.

### Where it composes cleanly with v1.0

- Same numéraire (`X = USD`), same payment units (`Y_D = 1 USDC`,
  `Y_AI = 1 SOMI`) — no domain-non-negotiable changes.
- Carr-Madan replicating strip generalizes from price-grid to (time × price)
  grid; the integration scheme grows, the formula doesn't.
- Hawkes self-excitation makes flow-rate volatility the natural hedge target
  — clustering enables a hedge market by making vol-of-vol tradable.

### Five frictions to remember (do not over-commit v1.0 code)

1. **x402 v2 spec is per-request, not subscription.** No first-class
   subscription/session field. v2.0 needs either a provider-specific overlay
   (Agora-on-The-Graph pattern: cf. `SOMNIA_DRAFT`'s f(κ) overlay) or an
   x402 v3 extension proposal.
2. **Somnia ↔ Base cross-chain mechanics.** SOMI lives on Somnia; Superfluid
   lives on EVM L2s. Options: (a) wrapped SOMI on Base (adds wrapper trust),
   (b) USDC stream + MM swap to SOMI at agent dispatch (loads
   ρ_{Y_AI/Y_D} slippage onto the hedge layer), (c) native Somnia streaming
   primitive — unverified, probe before committing.
3. **Streaming-specific empirical leg is separate.** v1.0's Hawkes fits a
   *discrete* arrival process. Streaming claims also need empirical
   validation of flow-rate adjustment processes (Hawkes-clustered? volatility
   correlated?). v2.0 must repeat Phases 2-5 against Superfluid mainnet data.
4. **Fungibility vs. complexity-index κ.** Token fungibility (ERC-20)
   requires standardizing κ across providers — Agora pricing showed κ is a
   provider-specific overlay. NFT-per-claim avoids that but makes per-unit
   hedging heavy. Choice has hedge-cost implications.
5. **NON-RETIREMENT-PENDING-MATURITY adds a gate.** v1.0 already gated on
   x402-on-Base maturity (≥50 Colombian payer wallets observable by
   2026-11-12). v2.0 additionally requires Superfluid+x402 integration to be
   live and observable — pushes the maturity bar higher.

### Hooks into v1.0 that we MUST keep polymorphic

- **`analysis/src/abrigo_x402/decoders.py`** — keep event-decoding generic;
  don't hard-code "Swap" as the only arrival type. (Already the case.)
- **`analysis/src/abrigo_x402/revenue_leg.py`** — Q96 LP-fee formula is
  Uniswap-V3-specific. v2.0 will need a sibling module for streaming-PV
  decomposition; keep the cross-leg copula interface in Phase 4 abstract
  enough to take either flow type.
- **`analysis/src/abrigo_x402/vault_state.py`** — TickMath + LiquidityAmounts
  ports are pure V3 math; reusable for any V3 position (Panoptic options ARE
  V3 positions). No changes needed; just don't tie them to ICHI semantics.
- **Phase 4 Carr-Madan replicating-strip module** (not yet written) — design
  the API for an arbitrary payoff `f(S_T)`, not just LP-fee revenue. v2.0
  will pass a stream-PV payoff into the same strip generator.

### Hooks into v1.0 that v2.0 will NOT re-use

- **Blockscout v1 getLogs pipeline** — Superfluid mainnet data comes from
  the Superfluid Subgraph (GraphQL) or directly from contract events. The
  cost-ledger / freshness layer reuses cleanly; the data-source plumbing
  does not.
- **Mento broker historical FX snap** — irrelevant for the streaming case
  unless v2.0 specifically prices a cKES-denominated stream.
- **CIP-64 phantom-Transfer filter** — Celo-specific.

### When to revisit

After Phase 7 (`/gsd:audit-milestone v1.0` produces an audit verdict).
Promote this note to a new top-level `.planning/ROADMAP.md` v2.0 milestone
at that point. Do NOT preemptively scaffold v2.0 work while v1.0 is in
flight — risks AF-03 spec-swap on v1.0.

---

*End of v2.0 note.*
