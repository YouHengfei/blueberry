# Toolkit map

Start with the [setup procedure](../INSTALL.md#setup-procedure).
Sources are project-neutral; live state, project rules and evidence stay in their
owning projects. Default deployment is explicit local copies, not an installer.

| Source | Destination in an adopting project | Purpose |
|---|---|---|
| [general/system-prompts/project.md](general/system-prompts/project.md) | `AGENTS.md` (marked merge; see adapter fallbacks) | Small selective task router |
| [general/WORKFLOW.md](general/WORKFLOW.md) | `.coworkers/WORKFLOW.md` | On-demand workflow and user guide |
| [general/templates/COWORKERS.template.md](general/templates/COWORKERS.template.md) | `COWORKERS.md` | Small project index; copy once |
| [general/templates/SHARED.template.md](general/templates/SHARED.template.md) | `.coworkers/state/shared.md` | Canonical claims/protections; copy once |
| [general/templates/TASK.template.md](general/templates/TASK.template.md) | `.coworkers/state/tasks/<task_id>.md` | Selected task's mutable state |
| [general/templates/TASK_README.template.md](general/templates/TASK_README.template.md) | `.coworkers/tasks/<task_id>/README.md` | Durable record, progressively completed |
| [general/templates/STAGE.template.md](general/templates/STAGE.template.md) | `.coworkers/tasks/<task_id>/stages/NN_short_description.md` | Optional detailed plan/findings |
| [general/tools/](general/tools/) | `.coworkers/tools/` | Cooperative state/claim helper and usage |
| [general/templates/local_tests-policy.md](general/templates/local_tests-policy.md) | Adopt in project policy only if useful | Scratch lifecycle |
| [general/templates/SKILL.template.md](general/templates/SKILL.template.md) | Authoring only | Explicit skill skeleton |
| [general/skills/](general/skills/) | `.agents/skills/<name>/` (shared across harnesses) | Selected explicit procedures |
| [specific/agent-specific/](specific/agent-specific/) | Read relevant adapter, do not inject | Verified loading notes and optional `/task` helpers |

Existing boards and instructions are preserved first. Do not migrate active writers
or upgrade only the cleaner on a legacy layout. No vendor profiles, machine paths,
credentials, live boards or experiment outputs belong in this toolkit.
