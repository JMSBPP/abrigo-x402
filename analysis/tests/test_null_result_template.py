"""Plan 04-08 -- HEDGE-05 firing-decision + null-result PDF template tests.

Three parametrized fixture-driven firing-detection tests + one dual-signature
PDF test (skipped when `quarto` is not on PATH so CI without TinyTeX still
green-lights the suite).
"""
from __future__ import annotations

import json
import re
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
    # Some poppler builds only surface the /HEDGE05Marker \pdfinfo custom field
    # under `pdfinfo -custom` (plain `pdfinfo` reports only `Custom Metadata: yes`).
    # Query the custom block (and fall back to plain) so the genuine marker that
    # the template injects is read on every build.
    info = subprocess.run(
        ["pdfinfo", "-custom", str(out)], capture_output=True, text=True
    ).stdout
    if HEDGE05_SIGNATURE not in info and "HEDGE05" not in info:
        info += subprocess.run(
            ["pdfinfo", str(out)], capture_output=True, text=True
        ).stdout
    assert (
        HEDGE05_SIGNATURE in info or "HEDGE05" in info
    ), f"machine-readable marker missing from pdfinfo output: {info!r}"


# ---------------------------------------------------------------------------
# Plan 05-03 — reports/ichi.qmd deliverable (REPORT-01) guards.
#
# THREE tests: one NON-render source-grep AF-03 verdict-not-narrowed companion
# that runs in CI (NO quarto-skip guard), plus two quarto-skip-guarded PDF-text
# tests for the dual signature + the rendered verdict.
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
ICHI_QMD = REPO_ROOT / "reports" / "ichi.qmd"

# AF-03 disposition-memo forbidden relabelings — none may appear in the source.
_FORBIDDEN_NARROWING = (
    "pass with caveat",
    "near-miss positive",
    "directionally positive",
    "exploratory positive",
)


def test_ichi_qmd_source_not_narrowed() -> None:
    """NON-render AF-03 guard — runs in CI WITHOUT quarto (no skip guard).

    Greps the reports/ichi.qmd SOURCE for the verdict-integrity contract:
      required-present : null_strip_unavailable, a LABELED p-value p=0.0474
                         (the statistic is D=0.148 — a bare/statistic-labeled
                         0.0474 must not satisfy this), gate_passes, and the
                         CORRECT include path.
      required-absent  : the 4 forbidden narrowing strings, the wrong
                         ../_templates/ include path, and any USDC literal.
    Plus a non-render path-existence smoke: every JSON path the
    _evidence_branches.qmd partial loads (if any) resolves relative to reports/.
    """
    assert ICHI_QMD.exists(), f"deliverable source missing: {ICHI_QMD}"
    src = ICHI_QMD.read_text()

    # required-present
    assert "null_strip_unavailable" in src, "firing_condition string absent"
    assert "gate_passes" in src, "gate_passes verdict string absent"
    assert re.search(r"p ?(-value)? ?= ?0\.0474", src), (
        "LABELED KS leg-0 p-value 'p=0.0474' absent (a bare 0.0474 or a "
        "statistic-labeled D=0.0474 must not satisfy this — the statistic is D=0.148)"
    )
    assert "include _templates/_evidence_branches.qmd" in src, (
        "CORRECT include path '{{< include _templates/_evidence_branches.qmd >}}' absent"
    )
    # the 3-run methodology comparison must be present
    for rid in ("bdaf5c7ba5a2", "ae9e3ba17900", "0afc6af38e24"):
        assert rid in src, f"3-run comparison run_id {rid} absent"

    # required-absent
    for bad in _FORBIDDEN_NARROWING:
        assert bad not in src.lower(), f"forbidden narrowing string present: {bad!r}"
    assert "../_templates/_evidence_branches" not in src, (
        "WRONG include path '../_templates/...' present (resolves to repo-root /_templates/)"
    )
    assert "usdc" not in src.lower(), "USDC literal present (substrate is USDT — CLAUDE.md)"

    # non-render path-existence smoke: any relative JSON load in the included
    # partial must resolve from reports/. The null_strip_unavailable branch is
    # prose-only (no relative reads), so this is near a no-op, but it catches a
    # future partial edit that introduces a broken relative path.
    partial = REPO_ROOT / "reports" / "_templates" / "_evidence_branches.qmd"
    if partial.exists():
        ptxt = partial.read_text()
        for m in re.finditer(r"""Path\(\s*["']([^"']+\.json)["']""", ptxt):
            rel = m.group(1)
            resolved = (REPO_ROOT / "reports" / rel).resolve()
            assert resolved.exists(), (
                f"_evidence_branches.qmd loads {rel!r} which does not resolve from reports/"
            )


def test_ichi_pdf_dual_signature() -> None:
    """Quarto-skip-guarded — assert the rendered ichi.pdf carries the dual signature.

    Renders via `make report-ichi` when an already-rendered reports/ichi.pdf is
    absent; otherwise asserts on the present PDF. Skipped without quarto so the
    green suite is preserved on this env.
    """
    if not shutil.which("quarto"):
        pytest.skip("quarto CLI not available -- skipping ichi.pdf dual-signature test")
    if not shutil.which("pdftotext") or not shutil.which("pdfinfo"):
        pytest.skip("pdftotext/pdfinfo not on PATH; cannot verify dual signature")

    pdf = REPO_ROOT / "reports" / "ichi.pdf"
    if not pdf.exists():
        subprocess.run(["make", "report-ichi"], cwd=REPO_ROOT, check=True)
    assert pdf.exists(), "make report-ichi did not produce reports/ichi.pdf"

    info = subprocess.run(
        ["pdfinfo", str(pdf)], capture_output=True, text=True
    ).stdout
    assert HEDGE05_SIGNATURE in info or "HEDGE05" in info, (
        f"machine-readable HEDGE05 marker missing from pdfinfo output: {info!r}"
    )


def test_ichi_verdict_not_narrowed() -> None:
    """Quarto-skip-guarded — assert the rendered PDF TEXT states the honest verdict.

    The rendered ichi.pdf MUST contain the required verdict strings and MUST NOT
    contain any forbidden narrowing string. Skipped without quarto.
    """
    if not shutil.which("quarto"):
        pytest.skip("quarto CLI not available -- skipping ichi.pdf verdict test")
    if not shutil.which("pdftotext"):
        pytest.skip("pdftotext not on PATH; cannot extract PDF text")

    pdf = REPO_ROOT / "reports" / "ichi.pdf"
    if not pdf.exists():
        subprocess.run(["make", "report-ichi"], cwd=REPO_ROOT, check=True)
    assert pdf.exists(), "make report-ichi did not produce reports/ichi.pdf"

    txt = subprocess.run(
        ["pdftotext", str(pdf), "-"], capture_output=True, text=True
    ).stdout
    txt_low = txt.lower()

    # required-present in rendered text
    assert "null_strip_unavailable" in txt, "firing_condition absent from PDF text"
    assert re.search(r"p ?(-value)? ?= ?0\.0474", txt), (
        "labeled KS p=0.0474 absent from PDF text"
    )
    assert "false" in txt_low, "FALSE gate indication absent from PDF text"

    # required-absent in rendered text
    for bad in _FORBIDDEN_NARROWING:
        assert bad not in txt_low, f"forbidden narrowing string in PDF text: {bad!r}"
