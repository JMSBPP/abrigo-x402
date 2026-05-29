# Follow-up — `render_null_result_pdf` latent bug (exposed by installing quarto)

**Status:** tracked, NOT fixed in the Phase-5 closure (out of ichi-deliverable scope).
**Severity:** MINOR (both reviewers). Does NOT affect `reports/ichi.pdf` (the Phase-5 deliverable) or any of REPORT-01..04.

## What
`analysis/tests/test_null_result_template.py::test_pdf_dual_signature_when_quarto_available`
was skip-guarded on `shutil.which("quarto")`. quarto was absent in the canonical
operator env, so it always skipped and the suite read green. Installing quarto
1.9.38 (to render the ichi deliverable) un-skipped it and exposed two latent bugs
in `analysis/src/abrigo_x402/hedge/null_result.py::render_null_result_pdf` (the
GENERIC HEDGE-05 null-result template renderer — a prior-phase module, NOT the
ichi.qmd deliverable):

1. **Relative template path.** Default `template=Path("reports/_templates/null_result.qmd")`
   is resolved against the subprocess CWD. Run from `analysis/` (pytest CWD) it
   does not resolve → `quarto render` aborts with "No valid input files passed to
   render". Fix: anchor the template + output to the repo root (compute from the
   module location, or `cwd=REPO_ROOT` in the `subprocess.run`).
2. **papermill dependency.** It passes `-P firing_condition:<X>` (line ~191),
   which requires the (untracked) `papermill` package. The generic template's
   purpose IS multi-firing-condition rendering, so the param is functional and
   cannot simply be dropped (unlike ichi.qmd, which has a frontmatter default).
   Fix options: (a) declare papermill as a tracked dev-dependency; or (b) switch
   the generic template to read `{{< meta firing_condition >}}` and pass
   `-M firing_condition:<X>` (pandoc metadata, no papermill).

The sibling `Makefile` target `render-null-result-pdf` (~line 196) has the same
`--execute-param` papermill dependency and would fail identically if exercised.

## Why deferred
- It is a separate module from a prior phase; the Phase-5 deliverable
  (`reports/ichi.qmd` → `reports/ichi.pdf`) renders via `make report-ichi` and
  does NOT use `render_null_result_pdf`.
- A correct fix needs the template + module + (if chosen) reproducible-render
  determinism, and warrants its own two-step review.

## Acceptance for the follow-up
- `test_pdf_dual_signature_when_quarto_available` PASSES with quarto present.
- `make render-null-result-pdf FIRING=null_lr` renders a >5KB PDF carrying the
  visible H1 + the HEDGE05 marker, from a clean repo root, with no untracked dep.
