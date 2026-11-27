# Antigravity adapter (1.5.x)

Follow the [setup procedure](../../../../INSTALL.md#setup-procedure). Generic
destinations are in the [asset map](../../../README.md); read the
[workflow](../../../general/WORKFLOW.md) on demand, not as always-on rule text.
Applies across Antigravity CLI (`agy`), Antigravity App and Antigravity IDE/extensions.

## Harness-specific resources

| Source | Destination relative to target workspace |
|---|---|
| `toolkit/general/system-prompts/project.md` | `AGENTS.md` (approved marked merge; plain Markdown, no frontmatter) |
| Selected `toolkit/general/skills/<name>/` | `.agents/skills/<name>/` |
| Optional [skills/task/SKILL.md](skills/task/SKILL.md) | `.agents/skills/task/SKILL.md` (exposed as `/task`) |

Boards, guide and helper use the generic `.coworkers/` layout. Installed copies are
independent of this checkout. Do not deploy updated instructions/cleaner to a legacy
live board before its approved migration; source updates do not require a live reload.

## Loading, precedence and budgets

- Copy by default. Inspect existing workspace and global rules before writing, and
  preserve existing boards and unrelated `.agents/` customizations (rules, skills,
  custom agents, plugins, `hooks.json`, `mcp_config.json` and discovery manifests).
- Antigravity rules are **cumulative** (deduplicated by resolved file path, never
  replacement-based). It loads `AGENTS.md`, `GEMINI.md`, `.agents/AGENTS.md`,
  `.agents/GEMINI.md` and `.agents/rules/*.md` (plus legacy `.agent/`, `_agents/`,
  `_agent/`) from the workspace folder and each parent up to the `.git` root, plus
  global rules under `~/.gemini/`. Subfolders below the workspace folder are not scanned.
- Reuse `AGENTS.md` (or an existing `GEMINI.md` if the project already keeps board
  discovery there) with `<!-- blueberry:router:start -->` / `<!-- blueberry:router:end -->`
  markers so Pi and Antigravity share one router without double-loading. Standalone
  `AGENTS.md` and `GEMINI.md` **do not use YAML frontmatter**.
- **Zero-tracked-diff fallback:** only when `AGENTS.md` is already Git-tracked and the
  user declines modifying it, install the router at `.agents/rules/blueberry.md` instead
  (never in both places). Every `.md` file inside `.agents/rules/` is scanned one level
  deep and **must** start with YAML frontmatter declaring snake_case `trigger: always_on`
  (missing or camelCase triggers such as `alwaysOn` are silently discarded):

  ```markdown
  ---
  trigger: always_on
  description: Task-local collaboration router pointing to COWORKERS.md and the selected task.
  ---
  ```

- Antigravity caps each rule file at 24,000 bytes (after expanding `@[label](<path>)`
  includes) and pools global + `always_on` rules under a 20,000-token budget (demoting
  over-budget rules to path pointers). Never use `@[label](<path>)` in rules to inline
  `COWORKERS.md`, `.coworkers/WORKFLOW.md`, task boards or stage plans.
- Never blanket-ignore `.agents/` in Git exclude rules: projects often track shared
  rules, skills or MCP configs there. Exclude only untracked blueberry-installed paths.
- Do not modify `~/.gemini/` global files or `~/.gemini/antigravity-cli/settings.json`
  (`trustedWorkspaces`, permissions, sandbox settings).

## Task command, skills and sessions

Antigravity deprecates legacy `.agents/workflows/*.md` in favor of Agent Skills under
`.agents/skills/<name>/SKILL.md` (scanned one level deep unless listed in
`.agents/skills.json`) and automatically exposes each skill as `/<name>` in CLI and App.

- **Optional `/task` skill:** installing `skills/task/SKILL.md` to
  `.agents/skills/task/SKILL.md` provides `/task <task_id> <role>` (distinct from
  Antigravity's built-in `/tasks` background-process panel). Check for an existing
  workspace or global `task` skill before copying; natural-language selection works
  without it. In dual Pi + Antigravity workspaces, `.agents/skills/task/` coexists
  safely with `.pi/prompts/task.md` because Pi namespaces skills as `/skill:task`.
- **Precedence and collisions:** skill priority is repository personal dir
  (`.gemini/config.json`) > workspace `.agents/skills/` > `~/.gemini/config/skills/` >
  built-in—**except in `agy` CLI**, where `~/.gemini/antigravity-cli/skills/` and
  `~/.gemini/skills/` override workspace skills and ignore manifest `exclude`. Inspect
  all of those locations for duplicate names before deployment.
- **Explicit-invocation boundary:** keep `disable-model-invocation: true` in `SKILL.md`
  for cross-harness parity with Pi, but note that official Antigravity `skills.md` only
  documents `name` and `description` frontmatter. Until interactively verified, treat
  `local-tests-cleaner` and `task` explicit-only gates as instruction-level safeguards,
  not harness-enforced locks. Installing or reading a skill never invokes it.
- **Sessions, subagents and `/learn`:** Antigravity rereads rules and skills before each
  turn; in `agy` CLI run `/skills reload` (or start a new conversation) to refresh
  `/skills` and slash-command completions, and inspect `/skills` or App/IDE
  **Customizations** without running cleanup. Prefer fresh sessions (`/clear` / `/new`)
  for unrelated tasks; `/fork` (`/branch`) inherits history, and `/compact` summaries may
  drop task identity—reconfirm and reread state when uncertain. Built-in subagents
  (`invoke_subagent`, `.agents/agents/`), `/swarm` and `/teamwork` do not automatically
  acquire or transfer `coord.py` claims; verify subagent context inheritance before
  relying on isolation. Built-in `/learn` proposals still require explicit human approval
  and merge—never silent rule rewrites.

## Verification and optional plugins

Authoritative Antigravity documentation topics: `rules`, `skills`,
`customization-discovery`, `slash-commands`, `subagents` and `cli/reference`. Recheck
installed-version docs before changing this adapter. See the
[validation matrix](../../../../tests/README.md): static contract checks do not prove
live `agy` request assembly, autonomous skill suppression or subagent payload isolation.

Antigravity plugins (`.agents/plugins/<name>/plugin.json`, `agy plugin install`) bundle
rules/skills/hooks/MCP and namespace skills as `<plugin>:<skill>`. Blueberry defaults to
explicit local copies rather than a plugin bundle so updates around active work stay
reviewable and gated on board migration. Do not mix plugin and copied versions of the
same skill or router.
