# Pi adapter (1.6.x)

Follow the [setup procedure](../../../../INSTALL.md#setup-procedure). Generic
destinations are in the [asset map](../../../README.md); read the
[workflow](../../../general/WORKFLOW.md) on demand, not as injected system text.

## Harness-specific resources

| Source | Destination relative to target workspace |
|---|---|
| `toolkit/general/system-prompts/project.md` | `AGENTS.md` (approved marked merge) |
| Selected `toolkit/general/skills/<name>/` | `.agents/skills/<name>/` |
| Optional [prompts/task.md](prompts/task.md) | `.pi/prompts/task.md` (exposed as `/task`) |

Boards, guide and helper use the generic `.coworkers/` layout. `AGENTS.md` and
`.agents/skills/` are shared with other Agent Skills harnesses (such as Antigravity)
so dual-harness repositories need only one router and one skill copy. Installed copies
are independent of this checkout. Do not deploy updated instructions/cleaner to a legacy
live board before its approved migration; source updates do not require a live reload.

## Loading and precedence

- Copy by default. Inspect inherited instructions/resources (`<agent-dir>`, workspace
  `AGENTS.override.md`, `AGENTS.md`, `CLAUDE.md`, `.pi/`) and preserve existing boards.
  Never replace `.pi/SYSTEM.md` or an existing context file with the router. For an
  existing `AGENTS.md`, propose an additive merge inside `<!-- blueberry:router:start -->`
  / `<!-- blueberry:router:end -->` markers that keeps every existing line; ask before
  editing a Git-tracked `AGENTS.md` or reordering/removing anything.
- `AGENTS.md` loads cumulatively across `<agent-dir>`, the working directory and parent
  directories without requiring project trust, avoiding the `.pi/APPEND_SYSTEM.md`
  trap (where a trusted project `.pi/APPEND_SYSTEM.md` shadows `<agent-dir>/APPEND_SYSTEM.md`
  instead of combining). Check for `AGENTS.override.md` in the same directory: Pi lets
  it suppress same-directory `AGENTS.md` and `CLAUDE.md`.
- **Zero-tracked-diff fallback and legacy installs:** use `.pi/APPEND_SYSTEM.md` only
  when `AGENTS.md` is Git-tracked and the user declines modifying it, after inspecting
  `<agent-dir>/APPEND_SYSTEM.md` so nothing is silently hidden—never install in both
  `AGENTS.md` and `.pi/APPEND_SYSTEM.md`. During updates of older Pi installs, migrate
  legacy `.pi/APPEND_SYSTEM.md` and `.pi/skills/` copies to `AGENTS.md` and
  `.agents/skills/` with approval so assets are not loaded twice.
- Do not touch unrelated `.pi/` or `.agents/` resources (settings, extensions, prompts,
  skills, MCP configs, themes); report collisions instead of removing or overriding them.
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
  (`PI_CODING_AGENT_DIR` when set) rather than assuming `~/.pi/agent`.

## Task prompt, skills and trust

The optional `/task <task_id> <role>` (`.pi/prompts/task.md`) is a Markdown prompt
template, not an extension. Pi expands it into a user message. It selects a
conversation-local task, does not enforce a persistent binding, and does not create
worktrees or launch agents. Natural-language selection works without it. Check `/task`
command collisions before deployment.

Pi discovers `SKILL.md` in `.agents/skills/` (from working directory through ancestors up
to the repository root) as well as `.pi/skills/`, `~/.agents/skills/`, `<agent-dir>/skills/`
and configured packages. Check all of them for duplicate names. Keep
`disable-model-invocation: true`: Pi hides explicit-only skills from automatic model
selection and startup prompt descriptions while keeping `/skill:<name>` available. In a
dual Pi + Antigravity workspace, Antigravity's `.agents/skills/task/` maps to
`/skill:task` in Pi (zero startup overhead) and does not collide with `/task` from
`.pi/prompts/task.md`. `/skill:local-tests-cleaner task example_task` scopes a cleanup,
while project-wide cleanup must be requested explicitly. Installing a skill never invokes it.

While `AGENTS.md` loads without trust, `.agents/skills/` and `.pi/` resources load only
after project trust is granted (`/trust` interactively, `--approve` for one-shot automated
runs). Let the user decide trust; never edit `~/.pi/agent/trust.json` or settings silently.
After an approved deployment/migration, run `/reload` in participating sessions (or
restart), check diagnostics and command discovery without invoking cleanup, and reconfirm
task bindings/canonical root. If interactive behavior cannot be checked, report it as
unverified. `enableSkillCommands` can hide command discovery; manually entered
`/skill:<name>` commands still work in the documented Pi version.

## Verification and optional package use

Authoritative Pi documentation topics: `configuration` (precedence/context files),
`security` (project trust), `sessions` (working directories/resume), `how-pi-works`
(request assembly), `skills` and `prompt-templates` (discovery and expansion). Recheck
installed-version docs before changing an adapter. See the
[validation matrix](../../../../tests/README.md) for runtime footprint tests; static
template checks do not prove model judgment.

The optional `package.json` exports only general skills. An explicitly requested
`pi install -l /path/to/blueberry` declares a package in project settings but does not
deploy boards, `AGENTS.md`, guide or helper. Do not mix package and `.agents/skills/`
copies of the same skill. An updated package cleaner still requires the task-scoped
layout; it must stop on a legacy board. Prefer copied resources when controlling rollout.
