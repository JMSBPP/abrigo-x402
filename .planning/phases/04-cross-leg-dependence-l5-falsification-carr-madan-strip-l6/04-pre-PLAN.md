---
phase: 04-cross-leg-dependence-l5-falsification-carr-madan-strip-l6
plan: pre
type: execute
wave: 0
depends_on: []
files_modified:
  - notes/PRE_REGISTRATION.md
autonomous: true
requirements: [HEDGE-02]

must_haves:
  truths:
    - "notes/PRE_REGISTRATION.md contains a §Carr-Madan Grid Numerical Tolerances sub-section locking the 0.1% positivity tolerance"
    - "The amendment commit is a SOLO commit (touches ONLY notes/PRE_REGISTRATION.md, no other files) with message prefix 'docs(pre-reg):'"
    - "The amendment commit hash predates every commit under analysis/src/abrigo_x402/hedge/ and analysis/src/abrigo_x402/dependence/ (git ordering invariant honors AF-03)"
    - "The amendment text uses the verbatim string 'positivity tolerance: negative implied-density mass < 0.1% of total integrated |q(k)|' and the verbatim escalation policy '2^11 -> 2^12, then abort to strip_degenerate.json'"
  artifacts:
    - path: "notes/PRE_REGISTRATION.md"
      provides: "AF-03 amendment locking 0.1% Carr-Madan positivity tolerance + 2^11->2^12 escalation policy + abort-to-strip_degenerate.json fallback"
      contains: "Carr-Madan Grid Numerical Tolerances"
  key_links:
    - from: "notes/PRE_REGISTRATION.md §Carr-Madan Grid Numerical Tolerances"
      to: "Plan 04-05 (analysis/src/abrigo_x402/hedge/carr_madan_strip.py)"
      via: "0.1% tolerance constant + 2^11->2^12 escalation + strip_degenerate.json fallback"
      pattern: "0\\.001|positivity_tolerance"
---

<objective>
Discharge the AF-03 pre-registration amendment obligation locked by `04-CONTEXT.md <deferred>` and `04-VALIDATION.md` Wave-0 row: add a `§Carr-Madan Grid Numerical Tolerances` sub-section to `notes/PRE_REGISTRATION.md` locking the 0.1% positivity tolerance, the 2^11 -> 2^12 grid-escalation policy, and the abort-to-`strip_degenerate.json` fallback.

Purpose: per AF-03 (no spec-swap after seeing results), every numerical tolerance load-bearing for the HEDGE-02 acceptance decision MUST be pre-registered. The 0.1% tolerance is new — it does NOT appear in the original 2026-05-25 PRE_REGISTRATION.md commit. Phase 4 cannot land any `analysis/src/abrigo_x402/hedge/*` code until this amendment is committed FIRST, as a SOLO commit, with the ordering verifiable via `git log`.

Output: a single git commit modifying ONLY `notes/PRE_REGISTRATION.md`. Hash predates all Phase-4 implementation commits.
</objective>

<execution_context>
@/home/jmsbpp/.claude/get-shit-done/workflows/execute-plan.md
@/home/jmsbpp/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/04-cross-leg-dependence-l5-falsification-carr-madan-strip-l6/04-CONTEXT.md
@.planning/phases/04-cross-leg-dependence-l5-falsification-carr-madan-strip-l6/04-RESEARCH.md
@.planning/phases/04-cross-leg-dependence-l5-falsification-carr-madan-strip-l6/04-VALIDATION.md
@notes/PRE_REGISTRATION.md
@.planning/research/PITFALLS.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Amend notes/PRE_REGISTRATION.md with §Carr-Madan Grid Numerical Tolerances (SOLO COMMIT, AF-03 ordering invariant)</name>
  <files>notes/PRE_REGISTRATION.md</files>
  <read_first>
    - notes/PRE_REGISTRATION.md (the entire file — append-only structure; new sub-section goes inside the existing §Test Statistics section or as a new top-level §Carr-Madan Grid Numerical Tolerances section after §Test Statistics)
    - .planning/phases/04-cross-leg-dependence-l5-falsification-carr-madan-strip-l6/04-CONTEXT.md <decisions> §"Carr-Madan grid + three-way stress test" sub-section (verbatim locked decisions)
    - .planning/phases/04-cross-leg-dependence-l5-falsification-carr-madan-strip-l6/04-RESEARCH.md §"Pitfall 7: AF-03 amendment ordering invariant is non-obvious"
    - .planning/research/PITFALLS.md (broader AF-03 discipline context)
  </read_first>
  <action>
    Append a new sub-section to `notes/PRE_REGISTRATION.md`. Insert location: after the existing `§Test Statistics` section, as a new H2 `## Carr-Madan Grid Numerical Tolerances` (or H3 inside §Test Statistics — pick whichever the existing file structure prefers; if existing file uses H2-only structure, use H2).

    The sub-section text MUST contain the following verbatim load-bearing strings (do not paraphrase — these are grep-able from downstream tests and the Phase 4 acceptance gate):

    1. Section heading: `## Carr-Madan Grid Numerical Tolerances` (or `### Carr-Madan Grid Numerical Tolerances` if nested under §Test Statistics)

    2. Date-stamp paragraph: "Amendment date: 2026-05-27. This sub-section is added as an AF-03 amendment to lock numerical tolerances for the HEDGE-02 Carr-Madan replicating-strip implementation in Phase 4."

    3. Positivity tolerance constant paragraph (VERBATIM):
       "Positivity tolerance: negative implied-density mass < 0.1% of total integrated |q(k)|. Implementation: compute total ∫ |q(k)| dk on the FFT grid; if (sum of negative q(k)) / (sum of |q(k)|) < 0.001, treat as numerical FFT-truncation noise and proceed; otherwise escalate per the grid-escalation policy below. Rationale: under fat-tailed joint distributions (Hawkes self-excitation + USDT depeg jump), the characteristic function decays slowly and 2^11/2^12 FFT grids exhibit small FFT-truncation artifacts at extreme strikes; the 0.1% threshold is calibrated to absorb these artifacts without masking genuine fat-tail blowups. This tolerance is load-bearing for the HEDGE-02 acceptance decision and is therefore pre-registered here per AF-03 discipline."

    4. Grid-escalation policy paragraph (VERBATIM):
       "Grid-escalation policy: start at 2^11 = 2048 points. If positivity tolerance fails at 2^11, escalate to 2^12 = 4096 points. If 2^12 still fails the positivity tolerance, abort to strip_degenerate.json (do NOT silently switch to COS or PROJ methods). The strip_degenerate.json payload must include {max_negative_value, total_negative_mass, characteristic_function_decay_rate, recommended_method: 'COS' or 'PROJ' or 'none'} so the Phase 5 report can document the failure publicly."

    5. Consumer cross-reference paragraph (VERBATIM):
       "Consumers: analysis/src/abrigo_x402/hedge/carr_madan_strip.py (Phase 4 implementation); reports/_templates/null_result.qmd (Phase 4 null-result branch); reports/ichi.pdf (Phase 5 deliverable). Any code path that bypasses the 0.001 tolerance constant, the 2^11->2^12 single-escalation policy, or the abort-to-strip_degenerate.json fallback is an AF-03 violation."

    6. Ordering invariant paragraph (VERBATIM):
       "Ordering invariant: this amendment commit MUST predate every commit under analysis/src/abrigo_x402/hedge/ and analysis/src/abrigo_x402/dependence/ (verifiable via `git log --pretty=format:'%H %s' -- notes/PRE_REGISTRATION.md analysis/src/abrigo_x402/hedge/ analysis/src/abrigo_x402/dependence/`). Honored by Plan 04-pre."

    Then ALSO update the existing `## Cross-Plan Consumer Map` section at the bottom of the file to add a new bullet under the "Phase 4 (Carr-Madan + falsification)" entry:
       "- consumes the §Carr-Madan Grid Numerical Tolerances amendment above (positivity tolerance, grid-escalation policy, abort-fallback) for the HEDGE-02 Carr-Madan strip implementation."

    Commit as a SOLO commit (this file ONLY — no analysis/src changes, no other files):
    ```
    git add notes/PRE_REGISTRATION.md
    git commit -m "docs(pre-reg): AF-03 amendment — Carr-Madan grid 0.1% positivity tolerance + 2^11->2^12 escalation + abort-to-strip_degenerate.json fallback (Phase 4 prerequisite)"
    ```

    DO NOT touch analysis/src/abrigo_x402/hedge/ or analysis/src/abrigo_x402/dependence/ in this commit (those directories should not yet exist; if they do, do not add or modify any file inside them).

    The commit message prefix `docs(pre-reg):` is load-bearing — Plan 04-09's acceptance gate greps for it.
  </action>
  <verify>
    <automated>test -f notes/PRE_REGISTRATION.md &amp;&amp; grep -q "Carr-Madan Grid Numerical Tolerances" notes/PRE_REGISTRATION.md &amp;&amp; grep -q "0.1% of total integrated" notes/PRE_REGISTRATION.md &amp;&amp; grep -q "2\^11" notes/PRE_REGISTRATION.md &amp;&amp; grep -q "strip_degenerate.json" notes/PRE_REGISTRATION.md &amp;&amp; git log -1 --pretty=format:'%s' -- notes/PRE_REGISTRATION.md | grep -q "AF-03 amendment" &amp;&amp; test $(git show --stat --name-only HEAD | grep -cE "^(analysis|fetch|protocols|reports|scripts)/" || true) -eq 0</automated>
  </verify>
  <acceptance_criteria>
    - File `notes/PRE_REGISTRATION.md` contains the literal string `Carr-Madan Grid Numerical Tolerances` (case-sensitive)
    - File contains the literal string `0.1% of total integrated |q(k)|`
    - File contains the literal string `2^11` and `2^12`
    - File contains the literal string `strip_degenerate.json`
    - File contains the literal string `Amendment date: 2026-05-27`
    - File contains the literal string `Ordering invariant`
    - `git log -1 --pretty=format:'%s' -- notes/PRE_REGISTRATION.md` returns a message starting with `docs(pre-reg): AF-03 amendment`
    - `git show --stat --name-only HEAD | grep -v '^notes/PRE_REGISTRATION.md$' | grep -cE '^(analysis|fetch|protocols|reports|scripts)/' || true` returns 0 (the SOLO-commit invariant: this commit touches ONLY notes/PRE_REGISTRATION.md, no analysis/fetch/scripts/reports files)
    - `git log --pretty=format:'%H %s' -- analysis/src/abrigo_x402/hedge/ analysis/src/abrigo_x402/dependence/ 2>/dev/null | wc -l` returns 0 (no hedge/ or dependence/ commits exist yet at this point in the sequence — the amendment IS the first Phase 4 commit)
  </acceptance_criteria>
  <done>
    `notes/PRE_REGISTRATION.md` carries the new §Carr-Madan Grid Numerical Tolerances sub-section with all six verbatim paragraphs, committed as a SOLO commit with `docs(pre-reg): AF-03 amendment` prefix, and `git log` confirms zero commits under `analysis/src/abrigo_x402/hedge/` or `analysis/src/abrigo_x402/dependence/` predate this commit. Plan 04-00 may now proceed.
  </done>
</task>

</tasks>

<verification>
After commit:

```bash
# Verify amendment content
grep -c "Carr-Madan Grid Numerical Tolerances\|0.1% of total integrated\|2\^11\|strip_degenerate.json\|Amendment date: 2026-05-27\|Ordering invariant" notes/PRE_REGISTRATION.md
# Expect: >= 6 hits

# Verify SOLO commit discipline
git show --stat --name-only HEAD | tail -10
# Expect: only notes/PRE_REGISTRATION.md changed

# Verify AF-03 ordering invariant baseline
git log --pretty=format:'%H %s' -- analysis/src/abrigo_x402/hedge/ analysis/src/abrigo_x402/dependence/ 2>/dev/null | wc -l
# Expect: 0 (no Phase 4 implementation commits exist yet)

# Verify commit message prefix
git log -1 --pretty=format:'%s' -- notes/PRE_REGISTRATION.md
# Expect: starts with "docs(pre-reg): AF-03 amendment"
```
</verification>

<success_criteria>
- `notes/PRE_REGISTRATION.md` amended with `§Carr-Madan Grid Numerical Tolerances` sub-section containing the six verbatim paragraphs (positivity tolerance, escalation policy, abort fallback, consumer cross-reference, ordering invariant, date stamp)
- Amendment committed as a SOLO commit (ONLY `notes/PRE_REGISTRATION.md`) with message prefix `docs(pre-reg): AF-03 amendment`
- Zero commits exist under `analysis/src/abrigo_x402/hedge/` or `analysis/src/abrigo_x402/dependence/` (these directories may or may not exist yet; if they exist, no commits touch them)
- AF-03 ordering invariant established for Plans 04-00 through 04-09: every subsequent hedge/* or dependence/* commit has a strictly later git timestamp than this amendment commit
</success_criteria>

<output>
After completion, create `.planning/phases/04-cross-leg-dependence-l5-falsification-carr-madan-strip-l6/04-pre-SUMMARY.md` recording:
- The commit hash of the amendment
- The six verbatim paragraph titles added
- Confirmation of SOLO-commit discipline (output of `git show --stat HEAD`)
- Baseline confirmation that no hedge/* or dependence/* commits predate this one
- Forward reference: "Plan 04-00 may now scaffold hedge/* and dependence/* modules; all subsequent commits in those directories will honor the AF-03 ordering invariant established here."
</output>
