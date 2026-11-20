# COWORKERS — project entry point

Layout: task-scoped v2. This is an index, not a global current task.
Coordination root: (verified real absolute path; all participating worktrees use it).
Workflow: `.coworkers/WORKFLOW.md` (read when joining a task, not every request).
Helper: `.coworkers/tools/coord.py`; usage: `.coworkers/tools/README.md`.
Shared claims/protections: `.coworkers/state/shared.md` under the coordination root.

## Project context

- Authoritative docs: (verified paths; project rules remain in their owning docs)
- Checks: (verified commands/runbook; listing a check does not mean it passed)
- Environment and resource namespaces: (runbook + shared-board pointers)
- Local constraints: (exceptions or pointers; no secrets)

## Select, do not load everything

- Explicit task wins; otherwise keep the session's clearly matching task.
- If ambiguous, offer relevant existing tasks, a proposed snake_case task ID,
  or discussion-only. Confirm before creating/joining ambiguous work.
- Read only the selected task state, current plan, and relevant evidence.
  No task is needed for a general question. Never select by most-recent update.
- Task boards live at `.coworkers/state/tasks/<task_id>.md`. Records live in
  the task workspace at `.coworkers/tasks/<task_id>/`; the board gives its path.
- Confirm role/session identity and existing owners. Refresh claims before
  shared-resource work; use one canonical namespace and live availability checks.

## Writing and safety

- Use helper revision checks for board writes; claims use claim/annotate/release.
  On conflicts, reread and merge. Never overwrite another session's work.
- Append new history/index/registry entries at the bottom. Update snapshots in
  place; do not re-sort history or invent timestamps. Never transfer ownership.
- At meaningful request boundaries reconcile state, next action, evidence,
  plan validity and reservations; write only changes. No mandatory no-op logs.
- Cleanup and publication need explicit authorization. Task-scoped cleanup is
  the default; do not clean another task or migrate a live board during a job.

## Active task index

| Added | Task ID | Purpose | State board |
|---|---|---|---|

Append on creation; remove a closed task only after its durable record is linked
and closure is agreed. Live status and participants belong only in the task board.

## Setup provenance

- Source checkout/revision, selected assets, verified harness: (record at setup)
- Existing installations: preserve first; migration requires a paused-writer window.
