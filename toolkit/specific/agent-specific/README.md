# Agent harness notes

Read these alongside the [setup procedure](../../../INSTALL.md#setup-procedure).
They map generic assets to a harness; they do not install anything or define
another workflow.

- [pi/](pi/README.md): Pi 1.6.x `AGENTS.md` and `.agents/skills/` discovery,
  trust/precedence rules, optional `/task` prompt, and reload/verification steps.
- [antigravity/](antigravity/README.md): Antigravity 1.5.x (`agy` CLI, App, IDE)
  cumulative rules, `.agents/skills/` slash commands, precedence caveats, and reload steps.

For another harness, inspect its official documentation before deployment.
Document supported paths, instruction precedence, explicit skill invocation,
conflict handling, and reload behavior. Shared `SKILL.md` syntax does not imply
identical discovery paths or support for every frontmatter field.
