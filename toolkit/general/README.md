# General assets

Project-neutral sources for the [setup procedure](../../README.md#agent-setup-procedure).
The [asset map](../README.md) lists exact destinations.

- [system-prompts/project.md](system-prompts/project.md): short task router; no profiles.
- [WORKFLOW.md](WORKFLOW.md): on-demand user guide, roles, Git, closure and migration.
- [templates/COWORKERS.template.md](templates/COWORKERS.template.md): small project index.
- [templates/SHARED.template.md](templates/SHARED.template.md): shared claims/protections.
- [templates/TASK.template.md](templates/TASK.template.md): task-local mutable state.
- [templates/TASK_README.template.md](templates/TASK_README.template.md): durable task record.
- [templates/STAGE.template.md](templates/STAGE.template.md): optional executable stage plan.
- [tools/](tools/README.md): stdlib revision checks, atomic claims and recovery guidance.
- [templates/local_tests-policy.md](templates/local_tests-policy.md): scratch lifecycle.
- [templates/SKILL.template.md](templates/SKILL.template.md): authoring skeleton.
- [skills/local-tests-cleaner/SKILL.md](skills/local-tests-cleaner/SKILL.md): task-scoped
  cleanup with bottom-latest retention; explicit invocation, migrated layout only.

Copy assets deliberately. Reading/installing a skill never authorizes execution.
Use lowercase-hyphen skill names matching their directories. Updates are approved
merges, not silent replacements; project-specific adaptations stay in their projects.
