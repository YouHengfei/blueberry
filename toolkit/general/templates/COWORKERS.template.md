# COWORKERS — project entry point

An index, not a global current task.
- Coordination root: (verified real absolute path; shared across worktrees)
- Workflow: `.coworkers/WORKFLOW.md` (read on demand for create/close/claim/publish)
- Helper: `.coworkers/tools/coord.py` (usage: `.coworkers/tools/README.md`)
- Shared claims/protections: `.coworkers/state/shared.md`

## Project context

- Authoritative docs: (verified paths; project rules stay in their owning docs)
- Checks: (verified commands/runbook; listing a check does not mean it passed)
- Resource namespaces: (pointers to `shared.md` and runbooks)
- Local constraints: (exceptions or pointers; no secrets)

## Roles

- **Planner** — scope, design, core code when appropriate, executable plan, acceptance checks before handoff; reviews and accepts or replans.
- **Executor** — delegated bounded slices, test/benchmark runs and verification in scope; owns its jobs and scratch.
- **Reviewer (optional)** — independent audit of risky diffs, core code or disputed evidence.

Roles are harness-agnostic and attach to tasks; one session may fill several. Task state
lives at `.coworkers/state/tasks/<task_id>.md`; durable records live at `.coworkers/tasks/<task_id>/`.

## Active task index

| Added | Task ID | Purpose | State board |
|---|---|---|---|

Append on creation; remove closed tasks only after durable records are linked and closure
is agreed. Live status and participants belong only in the task board.

## Setup provenance

- Source checkout/revision, installed harness(es), installed asset paths: (record at setup)
- Existing installations: preserve first; migration requires a paused-writer window.
