# Claude Code adapter (v2.1.277+)

Follow the [setup procedure](../../../../INSTALL.md#setup-procedure). Generic
destinations are in the [asset map](../../../README.md); read the
[workflow](../../../general/WORKFLOW.md) on demand, not as always-loaded memory.

## Harness-specific resources

| Source | Destination relative to target workspace |
|---|---|
| `toolkit/general/system-prompts/project.md` | `AGENTS.md` (if no `CLAUDE.md` exists) **or** `.claude/rules/blueberry.md` (cumulative, zero-tracked-diff) |
| Selected `toolkit/general/skills/<name>/` | `.claude/skills/<name>/` |
| Optional [task skill](../antigravity/skills/task/SKILL.md) | `.claude/skills/task/SKILL.md` (exposed as `/task`) |

Boards, guide and helper use the generic `.coworkers/` layout. Installed copies are
independent of this checkout; never deploy updated instructions/cleaner onto a legacy
live single-board workflow before its approved migration.

## Loading, precedence and `AGENTS.md` rules

Verified against official Claude Code memory and skills documentation:

- **`AGENTS.md` conditional default (`claude-md-or-agents-md`):** Starting in v2.1.277,
  Claude Code reads `AGENTS.md` automatically **only when no `CLAUDE.md`,
  `.claude/CLAUDE.md`, or `CLAUDE.local.md` exists** in the working directory or any
  ancestor directory. If any of those files exist, Claude Code **skips `AGENTS.md`**
  unless `CLAUDE.md` explicitly imports `@AGENTS.md` or the user sets `/config` →
  **Project instructions** to `claude-md-and-agents-md`.
- **Do NOT use `CLAUDE.local.md` as a fallback in `AGENTS.md` repos:** creating
  `CLAUDE.local.md` triggers the `CLAUDE.md` presence check and silently stops Claude Code
  from reading `AGENTS.md`.
- **Preferred cumulative / zero-tracked-diff fallback — `.claude/rules/blueberry.md`:**
  Files in `.claude/rules/*.md` do **not** suppress `AGENTS.md` and load cumulatively
  alongside both `AGENTS.md` and `CLAUDE.md` (plain Markdown; no `trigger:` frontmatter
  needed). Use `.claude/rules/blueberry.md` whenever:
  1. The repository already has `CLAUDE.md` (so `AGENTS.md` would be ignored by Claude Code), or
  2. `AGENTS.md` is Git-tracked and the user wants zero tracked-file diffs.
  Never load the router from both `AGENTS.md` (when active) and `.claude/rules/blueberry.md`.
- **Claude Code ignores `.agents/`:** Official docs confirm Claude Code does not read
  `AGENTS.override.md`, `AGENTS.local.md`, or anything under `.agents/`. Project skills
  must be copied into `.claude/skills/<name>/SKILL.md` even when `.agents/skills/` is
  installed for Pi/Antigravity/Codex.
- Never blanket-ignore `.claude/` in Git exclude rules (teams often track `.claude/skills/`,
  `.claude/rules/`, `.claude/settings.json`, or store `.claude/worktrees/`). Exclude only
  untracked blueberry-installed paths (`/.claude/rules/blueberry.md`,
  `/.claude/skills/local-tests-cleaner/`, `/.claude/skills/task/`).
- Never modify `~/.claude/` global files or settings during project setup.

## Skills, `/task` and subagents

- Skills under `.claude/skills/<name>/SKILL.md` are exposed directly as `/<name>` (e.g.,
  `/task` and `/local-tests-cleaner`). Check `~/.claude/skills/` and managed skills for
  collisions; avoid the reserved name `synced`.
- **`disable-model-invocation: true` is enforced:** Claude Code hides marked skills from
  automatic model invocation, prevents preloading them into subagents, and keeps them
  manual-only via `/<name>`. Installing or reading a skill never invokes it.
- **Subagents & worktrees:** Built-in `Explore` and `Plan` subagents start without
  `CLAUDE.md`/`AGENTS.md`; custom subagents inherit context per their startup config and
  do not automatically hold `coord.py` claims. Across linked git worktrees, local
  git-excluded `.claude/rules/blueberry.md` and `.claude/skills/` exist only in the
  worktree where copied.
- Verify loaded instructions and skills with `/doctor prompt-audit` (or start a fresh
  session) without invoking cleanup. Report interactive discovery as unverified if not
  exercised.

## Verification

Authoritative Claude Code documentation topics: `memory` (`CLAUDE.md`, `AGENTS.md`,
`CLAUDE.local.md`, `.claude/rules/`) and `skills` (`.claude/skills/`,
`disable-model-invocation`, subagent preloading). See the
[validation matrix](../../../../tests/README.md): static checks do not prove live Claude
Code prompt assembly or model behavior.
