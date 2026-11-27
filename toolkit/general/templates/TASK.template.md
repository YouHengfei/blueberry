# Task: <task_id>

## Current state

- Goal: (one sentence)
- State: ready / running / blocked / review / done / cancelled
- Stage: (stage ID, or single_stage)
- Planner: (acceptance-owner session ID)
- Executors: (session ID + distinct work item)
- Reviewer: (optional)
- Next: (role/session — one actionable step)
- Workspace: (real path; branch; tested revision)
- Records: (task-workspace path to `.coworkers/tasks/<task_id>/README.md`)
- Plan: (stage doc/section link; do not copy plan here)
- Blocked by / Unblock: (only when blocked)

## Scope and acceptance

- Write scope & non-goals: (intended scope is not an active claim)
- Acceptance: (observable checks, thresholds, exceptions)
- Planner-owned acceptance check (before `ready`): (plan/command, expected result, negative cases; WORKFLOW.md §2)
- Dependencies: (register cross-task uses in `shared.md`)

## Open questions

- (question; raised by; date; owner — remove when resolved)

## Decisions

Append at bottom: `YYYY-MM-DD HH:MM role/session — decision; rationale; evidence`.

## Handoffs

Append at bottom: `YYYY-MM-DD HH:MM role/session — outcome; metric; next; evidence` (skip no-op).

## Retained artifacts

| Added | Path | Purpose / reproduction | Consumers / protection | Last used |
|---|---|---|---|---|

## Closure

- Acceptance / exceptions:
- Task README & cleanup disposition:
- Owned jobs stopped & claims released:
- Publication: local only unless authorized.

Explicit cleanup keeps newest 15 handoffs / 20 decisions, removing oldest excess from the top
after preserving binding constraints. Registries are never FIFO.
