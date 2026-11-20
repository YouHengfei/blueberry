# Task: <task_id>

## Current state

- Goal: (one sentence)
- State: ready / running / blocked / review / done / cancelled (choose one)
- Stage: (current stage ID, or single_stage)
- Planner: (acceptance-owner session identity; do not invent an owner)
- Executors: (session identity + distinct work item for each)
- Reviewer: (optional; independent review is not mandatory)
- Next: (role/session — one actionable next step)
- Workspace: (real path; branch; tested revision when available)
- Records: (actual task-workspace path to `.coworkers/tasks/<task_id>/README.md`)
- Plan: (current stage document/section; do not duplicate its plan here)
- Blocked by / Unblock: (include only when blocked; cause + responsible party)

## Scope and acceptance

- Non-goals and allowed write scope: (intended scope is not an active claim)
- Acceptance: (observable checks, thresholds, approved exceptions)
- Dependencies: (other task/asset pointers; register cross-task uses in shared.md)

## Open questions

- (question, raised by, date, who can decide; remove when resolved)

## Decisions

Append at bottom: `YYYY-MM-DD HH:MM role/session — decision; rationale; evidence`.
Newer records belong below older ones; do not silently rewrite historical verdicts.

## Handoffs

Append at bottom: `YYYY-MM-DD HH:MM role/session — outcome; metric; next; evidence`.
No entry is needed when a request changes no durable task state.

## Retained artifacts

| Added | Path | Purpose / reproduction | Consumers / protection | Last used |
|---|---|---|---|---|

Register only justified reusable tools or retained evidence. Append new rows;
update metadata in place. Cross-task consumers also register in shared.md before use.

## Closure

- Acceptance: (Planner/user verdict; failures and exceptions explicit)
- Task README: (problem, solution, results, revisions, reproduction, evidence)
- Cleanup: (keep/promote/delete/defer disposition + user approval or exceptions)
- Reservations: (owned jobs stopped and claims released; never others' jobs)
- Publication: local only; push requires separate authorization.

Explicit cleanup only: retain newest 15 handoffs / 20 decisions, removing oldest
excess from the top. Preserve binding constraints in the current plan/record first,
otherwise retain and report an exception. Registries are never FIFO-pruned.
