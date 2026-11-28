---
name: task
description: Explicit slash-command (/task) to select a conversation-local task and role from COWORKERS.md without loading other task boards. Invoke only when explicitly requested by the user.
disable-model-invocation: true
---

# Select task and role

Run only when explicitly invoked (for example `/task <task_id> <role>` or `$task`). Use
any task ID and role supplied with the command; if either is omitted or ambiguous, do not
guess.

Run `python3 .coworkers/tools/coord.py status --format text` (using the canonical root in
`COWORKERS.md` if running from a linked worktree without local tools) to inspect active
tasks, `Next` owners and active claims without reading all task boards. Read `COWORKERS.md`
if project context or canonical root pointers are needed. Bind only this conversation to
the requested task and a verified role/session identity. Read only the selected task state
and active plan. Do not create a global current-task file, claim another owner's role, or
start a workload merely to select it. If the task/role is ambiguous, offer relevant
existing tasks, a proposed snake_case new task, or discussion-only; ask before ambiguous
creation/joining. Missing or legacy layout requires approved setup/migration, not a silent
reset. Report the selected task, role, `Next` action, relevant active claims and
unresolved ownership; do not read all task boards.
