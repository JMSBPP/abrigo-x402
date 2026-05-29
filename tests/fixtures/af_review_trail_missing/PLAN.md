# Synthetic PLAN.md fixture for review-trail enforcement test

Staging this as `.planning/test-phase/test-PLAN.md` MUST trigger
`review-trail: FAIL — missing .planning/_reviews/test-PLAN_reality_checker.md`.

The hook is triggered by file path matching `^\.planning/(.*/)?PLAN\.md$`.
