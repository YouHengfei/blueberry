# Generic project prompt

[project.md](project.md) is a small, harness-neutral instruction fragment. It
points to the project-local `COWORKERS.md` and selected task. It contains no project
profile, resource inventory, detailed role manual or task content. The current
static budget is <=250 whitespace-delimited words; this is not a token measurement.

The [agent setup procedure](../../../README.md#agent-setup-procedure) copies or
merges it into the harness's supported instruction entry point after checking
existing instructions and precedence. Read the relevant
[harness notes](../../specific/agent-specific/README.md) first.

Keep detailed project rules in their existing docs, mutable coordination in
`.coworkers/state/`, and durable task records in `.coworkers/tasks/`. Read the
workflow/stage details on demand. Do not grow this fragment into a second board,
replace a harness's base prompt, or load every task at session startup.
