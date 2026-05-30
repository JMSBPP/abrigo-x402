#!/usr/bin/env python3
"""REPRO-03 cost-leg first-step check — Steer STRADDLE adjudication.

Applies the PRE-REGISTERED conservative-fail straddle rule
(notes/PRE_REGISTRATION.md §"Phase 6 — Steer cost-leg STRADDLE decision rule")
to the pre-committed demand band recorded in protocols/steer.toml
[protocol.repro_03_verdict], and writes notes/steer_cost_leg_bound.md with a
YAML frontmatter the HEDGE-05 firing decision tree consumes.

The rule (verbatim): verdict = FAIL unless the primary-source band is STRICTLY
ABOVE the 100k/mo Graph free-tier lower bound, i.e.
    celo_attributable_queries_per_mo_lower_bound > demand_window_lower_bound_queries_per_mo
A STRADDLE (band includes or sits below 100k) -> FAIL -> HEDGE-05 condition (a)
`null_cost`. This script OBSERVES the pre-committed band verbatim — it does NOT
re-estimate, re-enumerate, or narrow demand (AF-03).

The emitted frontmatter MUST satisfy the parser contract in
analysis/src/abrigo_x402/hedge/null_result.py::_parse_cost_leg_bound_verdict:
the file begins with a `---\n...\n---` YAML block whose `verdict` key uppercases
to 'FAIL'. (`re.match(r"---\n(.*?)\n---", text, re.DOTALL)` + yaml.safe_load.)

Stdlib-only (tomllib, argparse, pathlib) by design: this tool lives in scripts/
OUTSIDE the frozen fetch/src + analysis/src trees so the REPRO-02 empty-diff
invariant is preserved. It deliberately does NOT import the frozen analysis
package (no `import` of the production source tree).
"""
from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path


def adjudicate(lower_bound: int, upper_bound: int, demand_window_lower_bound: int) -> str:
    """Return 'PASS' or 'FAIL' under the pre-registered conservative-fail rule.

    FAIL unless the band is STRICTLY ABOVE the demand-window lower bound (100k).
    A straddle (lower_bound <= demand_window_lower_bound) -> FAIL.
    """
    return "PASS" if lower_bound > demand_window_lower_bound else "FAIL"


def _render_doc(verdict: str, band: dict) -> str:
    lower = band["celo_attributable_queries_per_mo_lower_bound"]
    upper = band["celo_attributable_queries_per_mo_upper_bound"]
    ceiling = band["demand_window_lower_bound_queries_per_mo"]
    result = band.get("result", "")
    flag = band.get("flag", "marginal-demand")
    firing = "null_cost" if verdict == "FAIL" else "none"
    # Frontmatter FIRST — _parse_cost_leg_bound_verdict matches `---\n...\n---`
    # at the very start of the file (re.match), so line 1 MUST be `---`.
    fm = (
        "---\n"
        f"verdict: {verdict}\n"
        f"flag: {flag}\n"
        f"firing_condition: {firing}\n"
        f"band_lower: {lower}\n"
        f"band_upper: {upper}\n"
        f"free_tier_ceiling: {ceiling}\n"
        'rule: "not strictly > 100k -> FAIL (pre-registered, AF-03)"\n'
        "---\n"
    )
    body = f"""
# Steer cost-leg lower-bound check (REPRO-03 first step)

**Verdict: {verdict}** — fires HEDGE-05 condition (a) `{firing}`.

This document is the REPRO-03 first-step artifact. It was emitted by
`scripts/cost_leg_check.py` applying the PRE-REGISTERED conservative-fail
straddle rule (see `notes/PRE_REGISTRATION.md` §"Phase 6 — Steer cost-leg
STRADDLE decision rule") to the pre-committed demand band in
`protocols/steer.toml [protocol.repro_03_verdict]`. **No demand was
re-estimated, re-enumerated, or narrowed** — Phase 6 only OBSERVES the verdict
the pre-committed band yields (AF-03).

## Decision

- Pre-committed band: **{lower:,}–{upper:,}** Celo-attributable Graph queries/mo
  (`{result}`).
- Graph free-tier lower bound (DEMAND-01): **{ceiling:,}** queries/mo.
- Rule: verdict = FAIL unless the band is STRICTLY ABOVE {ceiling:,}.
- {lower:,} is **not strictly above** {ceiling:,} → the band straddles / sits
  below the free-tier line → **{verdict}** → `{firing}`.

## STRADDLE provenance (verbatim from protocols/steer.toml)

- channel_a: {band.get("channel_a_source", "")}
- channel_b: {band.get("channel_b_source", "")}
- channel_c: {band.get("channel_c_source", "")}
- synthesis: {band.get("synthesis", "")}

## Disposition

Steer is the intended FEATURES.md D-08 **negative control**: observing the
`{firing}` path fire at least once confirms the falsification machinery works in
practice. Per Iteration-2 resolution policy, the resolution on this null is to
**substitute a replacement candidate (pending — future milestone)**; that
candidate is NOT named or executed here, and any future substitute MUST be
pre-registered before its own data is seen (AF-03).
"""
    return fm + body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="REPRO-03 Steer cost-leg straddle check")
    parser.add_argument(
        "--protocol",
        type=Path,
        default=Path("protocols/steer.toml"),
        help="protocol TOML carrying [protocol.repro_03_verdict]",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("notes/steer_cost_leg_bound.md"),
        help="output markdown path consumed by decide_firing_condition",
    )
    args = parser.parse_args(argv)

    with args.protocol.open("rb") as fh:
        spec = tomllib.load(fh)

    band = spec["protocol"]["repro_03_verdict"]
    verdict = adjudicate(
        lower_bound=band["celo_attributable_queries_per_mo_lower_bound"],
        upper_bound=band["celo_attributable_queries_per_mo_upper_bound"],
        demand_window_lower_bound=band["demand_window_lower_bound_queries_per_mo"],
    )
    doc = _render_doc(verdict, band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(doc)
    firing = "null_cost" if verdict == "FAIL" else "none"
    print(f"cost_leg_check: verdict={verdict} firing_condition={firing} -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
