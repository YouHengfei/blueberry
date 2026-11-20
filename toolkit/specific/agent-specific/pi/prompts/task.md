---
description: Select a task and role for this conversation without loading other task plans
argument-hint: "[task_id] [role]"
---

Requested task: ${1:-unspecified}
Requested role: ${2:-unspecified}

Read the project entry point COWORKERS.md and follow its canonical coordination-root
pointer. Bind only this conversation to the requested task and a verified role/session
identity. Read only the selected state and relevant plan. Do not create a global
current-task file, claim another owner's role, or start a workload merely to select it.
If the task/role is ambiguous, offer relevant existing tasks, a proposed snake_case
new task, or discussion-only; ask before ambiguous creation/joining. Missing or legacy
layout requires approved setup/migration, not a silent reset. Report the selected task,
role, next action and unresolved ownership; do not read all task boards.
