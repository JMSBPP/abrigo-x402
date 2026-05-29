# abrigo-x402

First iteration of the x402-protocol substrate for Abrigo. Builds on the `SOMNIA_DRAFT.md` cost model in `../abrigo-analytics/notes/SOMNIA_DRAFT.md` (primal/dual cost spaces, x402 unit-cost, Somnia agent unit-cost, Panoptic convex-hedge replication).

Sibling repos:
- `../abrigo-analytics` — empirical validation + structural econometrics
- `../abrigo-marketing` — narrative & positioning

## Git workflow — fork/upstream model

Two remotes, identical pattern to `abrigo-analytics`:

| Remote | URL | Role |
|---|---|---|
| `origin` | `https://github.com/JMSBPP/abrigo-x402.git` | personal fork — all `git push` targets this |
| `upstream` | `https://github.com/wvs-finance/abrigo-x402.git` | canonical repo — receives PRs from `origin` |

Rules:
1. **All pushes go to `origin`** (`JMSBPP/abrigo-x402`). Never push directly to `upstream`.
2. **PRs target `upstream`**: branches on `origin` are opened as PRs into `wvs-finance/abrigo-x402:master`.
3. **Sync from upstream** before starting new work:
   ```bash
   git fetch upstream
   git rebase upstream/master   # or: git merge upstream/master
   git push origin master
   ```
4. **Opening a PR** (from a feature branch on `origin`):
   ```bash
   gh pr create --repo wvs-finance/abrigo-x402 \
     --base master --head JMSBPP:<branch-name> \
     --title "..." --body "..."
   ```

### Cycle-closure integration (end of a development cycle)

A **development cycle closes when its terminal deliverable lands** — e.g. the Iteration-1 PDF (`reports/ichi.pdf`, Phase 5), the Iteration-2 PDF (Phase 6), or any milestone whose verification has passed. At that point, closure is NOT optional housekeeping — it is the final step of the cycle:

1. **Push the completed cycle to `origin`** (`JMSBPP/abrigo-x402`) — never to `upstream`.
2. **Open a PR into `upstream`** (`wvs-finance/abrigo-x402:master`) for the cycle's branch, with a body summarizing the cycle's deliverable + verification outcome (honest verdict, including null/near-miss results).
3. **Merge on `upstream`** only after the cycle is complete and verified (PDF rendered, `make verify-reproducibility` green, phase VERIFICATION passed).

Sequence: **complete + verify the deliverable → push origin → PR to upstream → merge upstream.** This applies to every iteration/cycle going forward, not just Iteration 1. Do not merge a cycle to upstream with an unverified deliverable or a verdict that was narrowed/relabeled to look like a pass (AF-03 discipline carries into the merge decision).

## Domain non-negotiables (from SOMNIA_DRAFT)

- Unit of account: `X = USD`; data-payment unit `Y_D = 1 USDC`; agent-payment unit `Y_AI = 1 SOMI`.
- x402 v2 `PaymentRequirements` carries no first-class complexity index κ — any closed-form `f(κ)` is a provider-specific overlay (Agora pricing for The Graph).
- Somnia gas pricing on `docs.somnia.network/agents/invoking-agents/gas-fees` is labelled "stop-gap" with no effective-date metadata; treat as volatile.
- No native SOMI/USD on-chain oracle as of 2026-05-23 — cross-rate ρ_{Y_AI/Y_D} must be sourced off-chain until a native feed ships.
- Convex perpetual (Panoptic) strictly dominates linear hedge whenever any of: vol-of-vol > 0, positive skew/fat tails, Hawkes self-excitation, or USDC depeg jump.
- x402-on-Base substrate is **NON-RETIREMENT-PENDING-MATURITY** until 2026-11-12 + ≥50 Colombian-attributable payer wallets observable (see `abrigo-analytics/memory/project_e10_x402_substrate_pending_maturity_2026_11.md`).

## What this repo holds

To be defined as the iteration matures. Likely surface area:
- Solidity contracts implementing the x402 payment leg and the Panoptic-replicated convex hedge.
- Off-chain SOMI/USD oracle adapter until a native feed exists.
- Agora-pricing decomposition module (κ inference from top-level GraphQL fields).
- Settlement reconciliation against the IAgentRequester escrow-refund channel.
