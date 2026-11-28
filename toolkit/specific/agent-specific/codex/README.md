# Codex CLI adapter

Follow the [setup procedure](../../../../INSTALL.md#setup-procedure). Generic
destinations are in the [asset map](../../../README.md); read the
[workflow](../../../general/WORKFLOW.md) on demand, not as injected startup text.

## Harness-specific resources

| Source | Destination relative to target workspace |
|---|---|
| `toolkit/general/system-prompts/project.md` | `AGENTS.md` (approved marked merge; plain Markdown, no frontmatter) |
| Selected `toolkit/general/skills/<name>/` | `.agents/skills/<name>/` (includes `agents/openai.yaml`) |
| Optional [task skill](../antigravity/skills/task/) | `.agents/skills/task/` (invoked via `$task` or `/skills`) |

Boards, guide and helper use the generic `.coworkers/` layout. Because Codex natively
reads `AGENTS.md` and `.agents/skills/`, it shares both directly with Pi and Antigravity
with zero duplicate files. Installed copies are independent of this checkout.

## Loading, precedence and override trap

- Copy by default. Inspect `$CODEX_HOME` (defaults to `~/.codex`) and workspace
  `AGENTS.override.md` / `AGENTS.md` from the Git root down to the working directory.
  Never modify global `~/.codex/` or `~/.agents/` files during project setup.
- Codex concatenates instruction files from project root down to the current working
  directory (joined by blank lines; closer files appear later), bounded by
  `project_doc_max_bytes` (default `32 KiB`). Keep `AGENTS.md` concise so it never
  triggers truncation.
- **Same-directory `AGENTS.override.md` shadows `AGENTS.md`:** in any directory, Codex
  checks `AGENTS.override.md` first and skips `AGENTS.md` if an override exists (Pi
  behaves the same way). Unlike Antigravity (`.agents/rules/`) or Claude Code
  (`.claude/rules/`), Codex has no separate additive project-rules folder:
  - Prefer a marked additive merge in `AGENTS.md` (`<!-- blueberry:router:start -->` /
    `<!-- blueberry:router:end -->`).
  - If `AGENTS.md` is Git-tracked and the user declines editing it, warn that creating
    `AGENTS.override.md` would replace tracked `AGENTS.md` (unless the user explicitly
    approves copying tracked `AGENTS.md` + blueberry's router into an excluded
    `AGENTS.override.md` and maintaining parity manually).
- Never blanket-ignore `.agents/` in Git exclude rules; exclude only untracked
  blueberry-installed paths.

## Skills and explicit invocation

- Codex discovers skills in `.agents/skills/<name>/SKILL.md` (and `~/.agents/skills/`).
  Check global `~/.agents/skills/` for duplicate names before deploying.
- **Explicit-only gate (`agents/openai.yaml`):** Codex controls implicit model invocation
  via `<skill>/agents/openai.yaml` (`policy.allow_implicit_invocation: false`), not only
  `SKILL.md` frontmatter. Copy the full skill directory (including `agents/openai.yaml`)
  so `local-tests-cleaner` and `task` stay explicit-only (`$local-tests-cleaner`, `$task`,
  or via `/skills`). Installing or reading a skill never invokes it.
- Verify configuration and loaded skills via `/status` and `/skills` in a fresh Codex
  session without invoking cleanup. Report interactive discovery as unverified if not
  exercised.

## Verification

Authoritative Codex documentation topics: `guides/agents-md` (precedence,
`AGENTS.override.md`, `project_doc_max_bytes`) and Codex Agent Skills (`SKILL.md` and
`agents/openai.yaml` invocation policy). See the
[validation matrix](../../../../tests/README.md): static checks do not prove live Codex
request assembly or model behavior.
