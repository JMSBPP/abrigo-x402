"""HEDGE-05 firing decision + Quarto null-result PDF rendering.

Dual signature markers (per CONTEXT.md decisions §"HEDGE-05 firing wiring + PDF toolchain"):
  - Visible H1 in rendered PDF: "# HEDGE-05 NULL RESULT -- <firing-condition>"
  - Machine-readable PDF metadata marker: HEDGE05-NULL-RESULT-V1 (injected via
    \\pdfinfo in the Quarto template's include-in-header block).

Firing-condition decision tree (sequential, per CONTEXT.md):
  1. cost                  -- cost_leg_bound verdict = FAIL
  2. lr                    -- DGP-03 LR p-value >= 0.05 (Hawkes indistinguishable from NHPP)
  3. convex                -- gate_report.any_condition_passed = False
  4. null_strip_unavailable -- (iter-3 addition) gate passed but Carr-Madan strip
                              not emittable on the BIC-winner-derived char_func;
                              detected by existence of strip_degenerate.json in run_dir.

Per RESEARCH §"Pitfall 3 -- Quarto chunk caching + freeze gives false-determinism":
ALWAYS render with --no-cache. The template's execute YAML block already pins
freeze: false / cache: false; --no-cache is the additional CLI guard.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml

HEDGE05_SIGNATURE: str = "HEDGE05-NULL-RESULT-V1"

# CONTEXT.md firing-condition (b) threshold -- α=0.05 for LR-indistinguishable.
DGP_INDISTINGUISHABLE_ALPHA: float = 0.05

# iter-3: extended set of accepted firing conditions for render_null_result_pdf
# (the fourth value `null_strip_unavailable` covers the gate-passed-but-strip-
# not-emittable hybrid state -- catches both upstream char_func builder
# exceptions and downstream FFT positivity-fail-after-2_12).
_VALID_FIRING_CONDITIONS: frozenset[str] = frozenset(
    {"null_cost", "null_lr", "null_convex", "null_strip_unavailable"}
)


def _parse_cost_leg_bound_verdict(path: Path) -> str | None:
    """Return uppercased verdict string (e.g. 'PASS', 'FAIL') or None.

    Returns None when the file is missing, lacks a YAML frontmatter block,
    has malformed YAML, or carries no `verdict:` field. Callers downstream
    treat None as "no verdict signal" rather than as a firing trigger.
    """
    if not path.exists():
        return None
    text = path.read_text()
    m = re.match(r"---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return None
    try:
        fm = yaml.safe_load(m.group(1))
    except Exception:
        return None
    if not isinstance(fm, dict):
        return None
    v = fm.get("verdict")
    return str(v).upper() if v is not None else None


def decide_firing_condition(
    fit_report: dict,
    gate_report: dict,
    cost_leg_bound_path: Path | None = None,
    run_dir: Path | None = None,
) -> str | None:
    """HEDGE-05 firing decision tree (sequential evaluation, per CONTEXT.md).

    Order is load-bearing -- a triplet that satisfies multiple conditions is
    attributed to the FIRST condition in the sequence (the test fixture
    `hedge_05_null_lr` explicitly relies on this: cost passes + LR fails to
    reject + gate passes -> null_lr, not "no firing").

    1. If cost_leg_bound_path is supplied AND parses to verdict='FAIL'
       -> return 'null_cost'
    2. Elif fit_report['lr_test']['p_value'] >= DGP_INDISTINGUISHABLE_ALPHA
       -> return 'null_lr'
    3. Elif gate_report['any_condition_passed'] is False
       -> return 'null_convex'
    4. (iter-3) Elif run_dir is supplied AND (run_dir / 'strip_degenerate.json')
       exists -> return 'null_strip_unavailable'.
       Covers both upstream reasons (build_failed_upstream from
       _build_char_func_from_winner exception) and downstream reasons
       (positivity_fail_after_2_12 from compute_strip).
    5. Else -> return None (no firing -- positive-result path).

    Parameters
    ----------
    fit_report : dict
        Phase 3 fit_report.json contents (must contain `lr_test.p_value` for
        condition 2 to fire).
    gate_report : dict
        Phase 4 gate_report.json contents (must contain `any_condition_passed`
        for condition 3 to fire).
    cost_leg_bound_path : Path | None
        Path to notes/<protocol>_cost_leg_bound.md (or a fixture analogue).
        None disables condition 1.
    run_dir : Path | None
        Phase 4 run_dir (data/fits/ichi/<run_id>/). None disables condition 4.

    Returns
    -------
    str | None
        One of {'null_cost', 'null_lr', 'null_convex', 'null_strip_unavailable'}
        or None when no condition fires.
    """
    # Condition (a) -- cost-leg bound
    if cost_leg_bound_path is not None:
        verdict = _parse_cost_leg_bound_verdict(Path(cost_leg_bound_path))
        if verdict == "FAIL":
            return "null_cost"

    # Condition (b) -- LR indistinguishability
    lr_test = fit_report.get("lr_test", {}) or {}
    p_value = lr_test.get("p_value")
    if p_value is not None and float(p_value) >= DGP_INDISTINGUISHABLE_ALPHA:
        return "null_lr"

    # Condition (c) -- zero convex-dominance conditions
    if not bool(gate_report.get("any_condition_passed", False)):
        return "null_convex"

    # Condition (d) -- iter-3 fourth firing condition: gate passed but strip not emittable.
    if run_dir is not None and (Path(run_dir) / "strip_degenerate.json").exists():
        return "null_strip_unavailable"

    return None


def render_null_result_pdf(
    firing_condition: str,
    fit_report: dict,
    gate_report: dict,
    output_path: Path = Path("reports/ichi.pdf"),
    template: Path = Path("reports/_templates/null_result.qmd"),
) -> Path:
    """Invoke `quarto render <template> --no-cache --to pdf -P firing_condition:<X>`.

    Per RESEARCH Pitfall 3, `--no-cache` is non-negotiable: Quarto's chunk
    caching + freeze defaults can produce a stale-but-byte-identical PDF
    across two different `firing_condition` inputs, which would silently
    defeat SC-5 byte-identity reasoning at the audit-gate.

    The visible H1 + `\\pdfinfo HEDGE05-NULL-RESULT-V1` injection both live
    in the template; this function does not touch the PDF post-render.

    Parameters
    ----------
    firing_condition : str
        One of {'null_cost', 'null_lr', 'null_convex', 'null_strip_unavailable'}.
        ValueError otherwise.
    fit_report, gate_report : dict
        Forwarded to the template via the parametrized Quarto chunks (the
        template reads them off disk for evidence rendering -- this function
        only forwards the firing-condition param).
    output_path : Path
        Destination for the rendered PDF. Parent directory is created if
        missing.
    template : Path
        Path to the .qmd source. Defaults to reports/_templates/null_result.qmd.

    Returns
    -------
    Path
        The output_path argument (returned for caller chaining).

    Raises
    ------
    ValueError
        If firing_condition is not in the accepted set.
    RuntimeError
        If the `quarto` binary is not on PATH, or if `quarto render` exits
        non-zero (the captured stderr is included in the message).
    """
    if firing_condition not in _VALID_FIRING_CONDITIONS:
        raise ValueError(
            "firing_condition must be one of "
            "{'null_cost','null_lr','null_convex','null_strip_unavailable'}; "
            f"got {firing_condition!r}"
        )
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "quarto", "render", str(template),
        "--no-cache",
        "--to", "pdf",
        "-P", f"firing_condition:{firing_condition}",
        "--output", output_path.name,
        "--output-dir", str(output_path.parent),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError as e:
        raise RuntimeError(
            "quarto CLI not found on PATH. Install via `quarto install tinytex` "
            "or via system package manager (apt/pacman/dnf). See "
            "analysis/README.md System Dependencies section."
        ) from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"quarto render failed (exit {e.returncode}): {e.stderr}"
        ) from e
    return output_path
