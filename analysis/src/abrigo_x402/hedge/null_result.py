"""HEDGE-05 firing decision + Quarto null-result PDF rendering.

Dual signature markers: visible H1 + \\pdfinfo HEDGE05-NULL-RESULT-V1 (PDF metadata).

Firing-condition decision tree (sequential, per CONTEXT.md):
  1. cost  — cost_leg_bound verdict = FAIL
  2. lr    — DGP-03 LR p-value >= 0.05 (Hawkes indistinguishable from NHPP)
  3. convex — gate_report.any_condition_passed = False
  4. null_strip_unavailable — Carr-Madan strip produced strip_degenerate.json
"""
from pathlib import Path

HEDGE05_SIGNATURE: str = "HEDGE05-NULL-RESULT-V1"


def decide_firing_condition(
    fit_report: dict,
    gate_report: dict,
    cost_leg_bound_path: Path | None = None,
    strip_degenerate_path: Path | None = None,
) -> str | None:
    """Sequential decision tree (per CONTEXT.md):

    1. If cost_leg_bound_path exists AND parses to verdict='FAIL' -> return 'null_cost'
    2. Elif fit_report['lr_test']['p_value'] >= 0.05 -> return 'null_lr'
    3. Elif gate_report['any_condition_passed'] is False -> return 'null_convex'
    4. Elif strip_degenerate_path exists -> return 'null_strip_unavailable'
    5. Else -> return None (no firing; positive result path)
    """
    raise NotImplementedError("Plan 04-08 implements HEDGE-05 firing decision")


def render_null_result_pdf(
    firing_condition: str,
    fit_report: dict,
    gate_report: dict,
    output_path: Path = Path("reports/ichi.pdf"),
    template: Path = Path("reports/_templates/null_result.qmd"),
) -> Path:
    """Invoke `quarto render <template> --param firing_condition:<firing_condition> --no-cache --output <output_path>`.

    Injects HEDGE05_SIGNATURE into PDF metadata via \\pdfinfo block in template.
    Per Pitfall 3: always pass --no-cache for determinism.
    """
    raise NotImplementedError("Plan 04-08 implements HEDGE-05 PDF render")
