# Pi adapter (1.5.x)

Follow the [agent setup procedure](../../../../README.md#agent-setup-procedure).
Generic destinations are in the [asset map](../../../README.md); read the
[workflow](../../../general/WORKFLOW.md) on demand, not as injected system text.

## Harness-specific resources

| Source | Destination relative to target workspace |
|---|---|
| `toolkit/general/system-prompts/project.md` | `.pi/APPEND_SYSTEM.md` (approved merge) |
| Selected `toolkit/general/skills/<name>/` | `.pi/skills/<name>/` |
| Optional [prompts/task.md](prompts/task.md) | `.pi/prompts/task.md` |

Boards, guide and helper use the generic `.coworkers/` layout. Installed copies are
independent of this checkout. Do not deploy updated instructions/cleaner to a legacy
live board before its approved migration; source updates do not require a live reload.

## Loading and precedence

- Copy by default. Inspect inherited instructions/resources and preserve existing
  boards. Never replace `.pi/SYSTEM.md` or an existing context file with the router.
  For a differing entry point, propose an additive, clearly marked merge that keeps
  every existing line; ask before reordering or removing anything.
- Do not touch unrelated `.pi/` resources: settings, extensions, prompts, skills and
  context files are preserved; report collisions and precedence risks instead of
  removing or overriding them.
- A trusted project's `.pi/APPEND_SYSTEM.md` takes precedence over agent-dir
  `APPEND_SYSTEM.md`; they are not combined. Inspect inherited content before creating
  one and ask how to preserve instructions it would hide. The same precedence applies
  to `SYSTEM.md`, which replaces the default prompt.
- `AGENTS.md`/`CLAUDE.md` context files load separately. Reuse an existing entry point
  if it already provides board discovery; do not introduce a competing one.
- Pi does not automatically discover `COWORKERS.md` or arbitrary `.coworkers/` records.
  The loaded router supplies selective-read instructions. Do not name task/stage
  records as auto-discovered context files to force them into every request.
- Tool-read content remains in active history until context management removes it;
  “read once” is not zero ongoing context cost. Compaction summaries may omit task
  identity: refresh/reconfirm when uncertain, never infer from latest board activity.
- Sessions have their own working directory. Resume uses that directory; fresh sessions
  are preferable for unrelated work, while fork/clone inherit history. `/name` can
  label a session, `/session` can verify its identity. Names are not resource claims.
- Do not change user-level settings/resources. Inspect the active agent directory
  rather than assuming the default `~/.pi/agent`.

## Task prompt and skills

The optional `/task <task_id> <role>` is a Markdown prompt template, not an extension.
Pi expands it into a user message. It selects a conversation-local task, does not enforce
a persistent binding, and does not create worktrees or launch agents. Natural language
selection works without it. Check `/task` command collisions before deployment.

Pi recursively discovers `SKILL.md` in `.pi/skills/` and configured resources/packages;
Agent Skills `.agents/skills/` locations can also contribute. Check inherited paths for
duplicate names. Keep `disable-model-invocation: true`; full procedures are explicit,
not advertised for automatic selection. Skill arguments are a user request, not a
shell parser: `/skill:local-tests-cleaner task example_task` scopes a cleanup, while
project-wide cleanup must be requested explicitly. Installing a skill never invokes it.

Project resources load after trust; let the user decide it. Do not silently modify
trust settings. After an approved deployment/migration, run `/reload` in participating
sessions (or restart), check diagnostics and command discovery without invoking cleanup,
and reconfirm task bindings/canonical root. If interactive behavior cannot be checked,
report it as unverified. `enableSkillCommands` can hide command discovery; manually
entered commands still work in the documented Pi version.

## Verification and optional package use

Authoritative Pi documentation topics: configuration (instruction precedence), sessions
(working directories/resume), how-pi-works (request assembly), skills and prompt-templates
(discovery and expansion). Recheck installed-version docs before changing an adapter.
See the [validation matrix](../../../../tests/README.md) for runtime footprint tests;
static template checks do not prove multi-agent behavior or actual request token counts.

The optional `package.json` exports only general skills. An explicitly requested
`pi install --local /path/to/blueberry` declares a package but does not deploy boards,
prompts, guide or helper. Do not mix package and copied versions of the same skill.
An updated package cleaner still requires the task-scoped layout; it must stop on a
legacy board. Prefer copied resources when controlling rollout around active work.
