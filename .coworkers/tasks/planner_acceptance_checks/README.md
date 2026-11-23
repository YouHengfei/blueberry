# Planner-owned acceptance checks

Outcome: implemented the user-approved handoff rule in canonical workflow assets.
Planner/Executor self-check; no independent review or deployment to installed copies.

## Scope and decision

Before a coding task becomes ready, the Planner supplies an existing executable
acceptance command or new tests for critical behavior and negative cases. Record
prerequisites, expected results, and broken-baseline evidence where practical.
Exploration instead uses a bounded experiment with required evidence. Executors add
regressions but cannot weaken acceptance checks without Planner approval. Planner
reviews test validity, implementation diff and results; green tests alone do not accept.

## Evidence and handoff

- Changed WORKFLOW.md, TASK/STAGE/COWORKERS templates, and tests/test_assets.py.
- Added test first: targeted test failed because the readiness rule was absent.
- After implementation: 49 unittest tests passed; git diff --check passed.
- Base: 5fd3497 plus existing Tier-B working changes, left untouched by this task.
- Reproduce: PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -q
- Template tests check wording/contracts, not model compliance.
- No device jobs, card reservations, scratch outputs, commits or pushes.
- User-requested refinement: shortened workflow rule from 16 to 9 lines and reduced
  template repetition; kept readiness, negative cases, baseline, exploration and review gates.
  Revalidation: 49 tests pass; git diff --check clean.
- Next: user reviews focused diff; installed copies remain unchanged.
