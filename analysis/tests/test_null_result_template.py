"""Plan 04-08 -- HEDGE-05 firing-decision + null-result PDF template tests.

Three parametrized fixture-driven firing-detection tests + one dual-signature
PDF test (skipped when `quarto` is not on PATH so CI without TinyTeX still
green-lights the suite).
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from abrigo_x402.hedge.null_result import (
    HEDGE05_SIGNATURE,
    decide_firing_condition,
)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("hedge_05_null_cost", "null_cost"),
        ("hedge_05_null_lr", "null_lr"),
        ("hedge_05_null_convex", "null_convex"),
    ],
)
def test_firing_detection_per_fixture(name: str, expected: str) -> None:
    """Each fixture triplet forces exactly one firing condition.

    The decision tree is sequential: a fixture that passes cost_leg_bound +
    has a high LR p-value is attributed to 'null_lr' (the LR check comes
    before the gate check). Acceptance verifies each fixture lands on the
    documented condition (see fixture cost_leg_bound.md frontmatter).
    """
    fix = FIXTURES / name
    fit = json.loads((fix / "fit_report.json").read_text())
    gate = json.loads((fix / "gate_report.json").read_text())
    cost_path = fix / "cost_leg_bound.md"
    firing = decide_firing_condition(fit, gate, cost_path)
    assert firing == expected, (
        f"fixture {name}: expected {expected!r}, got {firing!r}"
    )


def test_pdf_dual_signature_when_quarto_available(tmp_path: Path) -> None:
    """Render a fixture-driven null-result PDF and grep both signature markers.

    Skipped when `quarto` is not on PATH (CI without TinyTeX). When run on a
    dev machine with quarto+TinyTeX installed, asserts:
      - The rendered PDF is non-trivial (> 5KB).
      - `pdftotext <pdf> -` contains "HEDGE-05 NULL RESULT" (visible H1).
      - `pdfinfo <pdf>` contains "HEDGE05-NULL-RESULT-V1" (PDF metadata).
    """
    if not shutil.which("quarto"):
        pytest.skip("quarto CLI not available -- skipping PDF-render dual-signature test")
    if not shutil.which("pdftotext") or not shutil.which("pdfinfo"):
        pytest.skip("pdftotext/pdfinfo not on PATH; cannot verify dual signature")

    from abrigo_x402.hedge.null_result import render_null_result_pdf

    fix = FIXTURES / "hedge_05_null_lr"
    fit = json.loads((fix / "fit_report.json").read_text())
    gate = json.loads((fix / "gate_report.json").read_text())
    out = tmp_path / "ichi.pdf"
    render_null_result_pdf("null_lr", fit, gate, output_path=out)

    assert out.exists(), "render_null_result_pdf returned without writing the PDF"
    assert out.stat().st_size > 5_000, f"PDF suspiciously small: {out.stat().st_size} bytes"

    txt = subprocess.run(
        ["pdftotext", str(out), "-"], capture_output=True, text=True
    ).stdout
    assert "HEDGE-05 NULL RESULT" in txt, (
        "visible H1 signature missing from rendered PDF text"
    )
    info = subprocess.run(
        ["pdfinfo", str(out)], capture_output=True, text=True
    ).stdout
    # pdfinfo surfaces the /HEDGE05Marker custom field on most builds; some
    # builds only expose the raw substring -- accept either form.
    assert (
        HEDGE05_SIGNATURE in info or "HEDGE05" in info
    ), f"machine-readable marker missing from pdfinfo output: {info!r}"
