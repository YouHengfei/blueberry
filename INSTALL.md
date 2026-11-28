# Unified installation and lifecycle

Agent-executable procedure for installing, updating and removing blueberry in an
adopting repository across supported coding harnesses. There is no installer script:
deployment uses explicit local copies and human-reviewed merges. See [README.md](README.md)
for copy-paste prompts and [toolkit/README.md](toolkit/README.md) for the generic asset map.

## Core contract

- **Ask first on ambiguity:** if `<blueberry-checkout>`, `<target-repository>` or the
  intended harness (`pi`, `antigravity`, `codex`, `claude-code`, multiple, or another
  harness) is missing or ambiguous, stop and ask. Never install into blueberry itself
  unless explicitly requested.
- **Local copies only:** copy regular files; never create symlinks or follow symlink
  parents/destinations when writing. Installed copies never auto-update on `git pull`.
- **Preserve-first:** inspect existing project instructions, boards, `.coworkers/`,
  `.agents/`, `.pi/`, `.claude/`, running work, reservations and evidence before changing
  anything. Unrelated harness settings, extensions, hooks, MCP configs, skills and prompts
  remain untouched; report collisions instead of removing or overriding them.
- **No side-effect execution:** never change user-global configuration (`~/.pi/`,
  `~/.gemini/`, `~/.codex/`, `~/.claude/`), modify tracked `.gitignore`, start/stop jobs,
  run cleanup, migrate a live board silently, or commit/push during setup, update or
  uninstall. Reading or installing a skill never authorizes invoking it.

## Harness and asset matrix

Pi, Antigravity and Codex share `AGENTS.md` + `.agents/skills/` by default; Claude Code
shares `AGENTS.md` when no `CLAUDE.md` exists (otherwise uses `.claude/rules/blueberry.md`)
and uses `.claude/skills/`. All harnesses share one `COWORKERS.md` + `.coworkers/` root:

| Harness | Adapter | Router (`project.md`) | Zero-tracked-diff fallback | General skills | Optional `/task` | Reload & check |
|---|---|---|---|---|---|---|
| **Pi (`1.6.x`)** | [pi/README.md](toolkit/specific/agent-specific/pi/README.md) | `AGENTS.md` (marked merge; check `AGENTS.override.md`) | `.pi/APPEND_SYSTEM.md` (check `<agent-dir>` first) | `.agents/skills/<name>/` (needs `/trust` / `--approve`) | [prompts/task.md](toolkit/specific/agent-specific/pi/prompts/task.md) → `.pi/prompts/task.md` (`/task`) | `/reload`; inspect diagnostics & `/skill:<name>` |
| **Antigravity (`1.5.x`)** | [antigravity/README.md](toolkit/specific/agent-specific/antigravity/README.md) | `AGENTS.md` (marked merge, no frontmatter) | `.agents/rules/blueberry.md` (`trigger: always_on`) | `.agents/skills/<name>/` (check CLI `~/.gemini/antigravity-cli/skills/`) | [skills/task/](toolkit/specific/agent-specific/antigravity/skills/task/SKILL.md) → `.agents/skills/task/` (`/task`) | `/skills reload` & `/skills` (`agy`) or **Customizations** |
| **Codex CLI** | [codex/README.md](toolkit/specific/agent-specific/codex/README.md) | `AGENTS.md` (marked merge; `AGENTS.override.md` shadows it) | Warn: `AGENTS.override.md` replaces `AGENTS.md`; ask first | `.agents/skills/<name>/` (include `agents/openai.yaml`) | [skills/task/](toolkit/specific/agent-specific/antigravity/skills/task/SKILL.md) → `.agents/skills/task/` (`$task`) | Fresh session; `/status` & `/skills` |
| **Claude Code (`v2.1.277+`)** | [claude-code/README.md](toolkit/specific/agent-specific/claude-code/README.md) | `AGENTS.md` (only if no `CLAUDE.md` / `CLAUDE.local.md`), else `.claude/rules/blueberry.md` | `.claude/rules/blueberry.md` (never `CLAUDE.local.md`) | `.claude/skills/<name>/` (ignores `.agents/`) | [skills/task/SKILL.md](toolkit/specific/agent-specific/antigravity/skills/task/SKILL.md) → `.claude/skills/task/SKILL.md` (`/task`) | Fresh session; `/doctor prompt-audit` |
| **Other** | [agent-specific/](toolkit/specific/agent-specific/README.md) | Verify official docs first | Verified untracked rule path | Verified skill dir | Optional | Per official docs |

### Marked router block in `AGENTS.md`

Wrap [toolkit/general/system-prompts/project.md](toolkit/general/system-prompts/project.md)
in HTML comment markers (plain Markdown, **no** YAML frontmatter) so updates and
uninstalls can locate blueberry's section without disturbing project rules:

```markdown
<!-- blueberry:router:start -->
<exact contents of toolkit/general/system-prompts/project.md>
<!-- blueberry:router:end -->
```

## Multi-harness coexistence

When a repository uses several harnesses (`pi`, `antigravity`, `codex`, `claude-code`):

1. **One coordination store:** share one `COWORKERS.md` and `.coworkers/` canonical root.
   Roles are harness-agnostic—any harness may act as Planner, Executor or Reviewer.
2. **One router load per harness:** keep the marked router block in `AGENTS.md` once when
   all active harnesses read it. Never install both `AGENTS.md` and a fallback for the
   same harness (`.pi/APPEND_SYSTEM.md`, `.agents/rules/blueberry.md`, or
   `.claude/rules/blueberry.md`). If `CLAUDE.md` exists, add `.claude/rules/blueberry.md`
   for Claude Code without duplicating into `AGENTS.md`.
3. **Shared vs. Claude skills:** install general skills once in `.agents/skills/<name>/`
   (including `agents/openai.yaml`) for Pi + Antigravity + Codex (never duplicate into
   `.pi/skills/`); copy separately to `.claude/skills/<name>/` only when Claude Code is
   installed (since Claude Code ignores `.agents/`).
4. **Non-colliding `/task` helpers:** `.pi/prompts/task.md` (`/task` in Pi),
   `.agents/skills/task/` (`/task` in Antigravity, `$task` in Codex, `/skill:task` in Pi
   with zero startup overhead), and `.claude/skills/task/SKILL.md` (`/task` in Claude Code)
   coexist cleanly.

## Linked worktrees

Git's common `.git/info/exclude` is shared across linked worktrees and `coord.py`
automatically resolves the canonical main repo root via `--git-common-dir`, **but local
git-excluded files in the main checkout do not appear inside a newly created `task/<id>`
worktree**. When launching an agent directly inside a linked worktree:

1. **Never create a second `.coworkers/state/` copy** in the worktree; run
   `<main-repo>/.coworkers/tools/coord.py` (or copy `.coworkers/tools/` locally—its
   auto-root still targets `<main-repo>`).
2. **Copy only the local router/skills needed for that worktree's harness** (regular local
   copies, e.g. `.agents/rules/blueberry.md`, `.pi/APPEND_SYSTEM.md`,
   `.claude/rules/blueberry.md`, and selected skills; already ignored by the shared
   `info/exclude` block).
3. **Optional pointer `COWORKERS.md`:** if agents start in the worktree, place a tiny
   local pointer `COWORKERS.md` naming the canonical `<main-repo>` root and workspace
   record path—never an independent active task index.

## Setup procedure

### 1. Inspect

Resolve real canonical paths for `<blueberry-checkout>` and `<target-repository>` (Git
top-level where available) and show both. Confirm the target harness(es) and read the
matching [adapter notes](toolkit/specific/agent-specific/README.md). Inspect existing
`AGENTS.override.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.agents/`, `.pi/`,
`COWORKERS.md`, `.coworkers/`, Git tracking/ignore status and global skill/rule paths
for collisions.

If a legacy single-board workflow or active writer would be affected, **stop** and
propose [legacy board migration](#legacy-board-migration) first. Never pair a task-scoped
cleaner or router with an unmigrated live board.

### 2. Select and explain

Using [toolkit/README.md](toolkit/README.md) and the selected adapter(s), list every file
to create, merge or preserve:

- Generic workflow assets: `COWORKERS.md`, `.coworkers/WORKFLOW.md`,
  `.coworkers/state/shared.md` and `.coworkers/tools/{coord.py,README.md}`.
- Router destination: `AGENTS.md` by default. If `AGENTS.md` is already Git-tracked,
  **ask the user explicitly** before modifying it (since `info/exclude` cannot hide edits
  to tracked files), offering either the marked additive merge in `AGENTS.md` or the
  harness's untracked zero-tracked-diff fallback.
- Selected explicit skills (`local-tests-cleaner`) in `.agents/skills/<name>/` and, if
  wanted, the harness's optional `/task` helper.
- Canonical coordination root on a local POSIX filesystem across participating worktrees
  (see [coordination helper limits](toolkit/general/tools/README.md)); never promise
  network/distributed filesystem locking guarantees.

### 3. Create or preserve

- Identical existing assets need no write. Existing boards remain byte-for-byte unchanged
  during ordinary or repeat setup.
- When creating or merging `AGENTS.md`, preserve every existing line in order and insert
  or update only the `<!-- blueberry:router:start -->` ... `<!-- blueberry:router:end -->`
  block (ask before reordering or removing anything). If using `.agents/rules/blueberry.md`
  as an approved Antigravity fallback, prepend required `trigger: always_on` YAML frontmatter.
- Copy absent approved templates (`COWORKERS.md`, `.coworkers/state/shared.md`),
  [WORKFLOW.md](toolkit/general/WORKFLOW.md) and `.coworkers/tools/`. Populate only
  verified root, doc, check and namespace pointers; never invent owners, claims or tasks.
  Record setup provenance in `COWORKERS.md`: source checkout/revision, installed
  harness(es), and exact installed asset paths.
- Create `.coworkers/state/tasks/<task_id>.md` and `.coworkers/tasks/<task_id>/README.md`
  only when the user explicitly authorizes starting a specific task; use `coord.py` for
  subsequent coordination writes.
- Configure local Git exclusions via
  `git -C <target-repository> rev-parse --path-format=absolute --git-path info/exclude`
  (resolving any relative fallback against `<target-repository>`, never against
  `<blueberry-checkout>`; works in both regular checkouts and linked worktrees—verify no
  symlink on the exclude file or parent before creating). Preserve existing lines and
  append missing rules inside a `# blueberry:exclude:start` ... `# blueberry:exclude:end`
  block:
  - Always local-only coordination/scratch: `/COWORKERS.md`, `/.coworkers/state/`,
    `/.coworkers/tools/`, `/.coworkers/WORKFLOW.md`, and `/local_tests/` (when adopted).
  - Local-only harness assets (only for untracked paths installed for local use):
    `/AGENTS.md` (only when newly created for local-only use),
    `/.agents/skills/local-tests-cleaner/`, `/.agents/skills/task/`,
    `/.pi/prompts/task.md`, `/.claude/skills/local-tests-cleaner/`,
    `/.claude/skills/task/`, or an approved fallback router (`/.pi/APPEND_SYSTEM.md`,
    `/.agents/rules/blueberry.md`, `/.claude/rules/blueberry.md`).
  - **Never blanket-ignore `.coworkers/`, `.agents/`, `.pi/` or `.claude/`:**
    `.coworkers/tasks/` must remain versionable for explicit local commits, and harness
    directories may hold tracked team configs. Report broader existing ignore rules or
    tracked coordination files as conflicts; never run `git rm` or modify tracked
    `.gitignore`. Without Git, report that exclusion/versioning is unavailable without
    initializing a repository.

### 4. Verify and report

- Confirm regular files (no symlinks), valid Markdown links, canonical coordination root,
  matching lowercase-hyphen skill names/frontmatter, and absence of duplicate routers or
  duplicate skill names across `.agents/`, `.pi/` and global directories.
- Run `python3 <target-repository>/.coworkers/tools/coord.py --root <canonical-root> snapshot COWORKERS.md`
  and `snapshot .coworkers/state/shared.md` to verify real-directory ancestry and valid
  claims-table formatting.
- Run `git check-ignore -v` to confirm local coordination/scratch paths are ignored while
  `.coworkers/tasks/` and any pre-existing tracked `.agents/` or project files remain
  unignored, and confirm tracked `.gitignore` is unchanged (`git diff -- .gitignore`).
- Review `git status` and diffs: no unrelated edits, global settings changes, job actions,
  artifact deletions or commits. Report created, merged, preserved and skipped items,
  any unresolved conflicts, and exact reload steps (`/reload` in Pi; `/skills reload` and
  `/skills` in `agy` CLI or **Customizations** in Antigravity App/IDE). Do not claim
  interactive harness behavior that was not exercised.

## Update procedure

Installed copies change only through this explicit comparison and merge flow:

1. **Inspect provenance and layout:** resolve `<blueberry-checkout>` and
   `<target-repository>`, read `COWORKERS.md` setup provenance and inspect installed
   generic and harness paths (including legacy Pi `.pi/APPEND_SYSTEM.md` and `.pi/skills/`).
   If no installation exists or a legacy live board requires migration first, stop and ask.
   Never deploy an updated cleaner or router onto an unmigrated single-board layout.
2. **Compare and classify:** diff each installed blueberry asset against source:
   - *Identical:* keep unchanged.
   - *Clean source update (unmodified local copy or marked router block):* propose update.
   - *Local modifications or legacy Pi path migration:* propose an additive merge (or move
     from `.pi/APPEND_SYSTEM.md` + `.pi/skills/` to `AGENTS.md` + `.agents/skills/`,
     removing superseded blueberry copies only after approval so nothing loads twice).
3. **Apply and record:** preserve `COWORKERS.md` index entries, `.coworkers/state/`
   boards/claims, `.coworkers/tasks/` records and unrelated harness files; update
   `Setup provenance` with the new source revision and asset list; refresh selective
   `info/exclude` entries if paths moved.
4. **Verify and report:** run the verification checks from [Step 4](#4-verify-and-report)
   and report applied, skipped and conflicting items with required reload commands.

## Uninstall procedure

Removal reverses only blueberry-installed assets; coordination history and evidence belong
to the project:

1. **Inventory first:** list blueberry-installed files, marked `AGENTS.md` router block
   and `# blueberry:exclude:start` ... `# blueberry:exclude:end` rules from provenance and
   adapter locations (`.agents/skills/{local-tests-cleaner,task}`, `.pi/prompts/task.md`,
   approved fallback router files, `.coworkers/{WORKFLOW.md,tools/}`). Ask before touching
   anything without clear blueberry provenance or with local edits.
2. **Remove only installed pieces:** delete approved blueberry skill/prompt/helper/workflow
   copies; strip only the marked blueberry block from `AGENTS.md` (deleting `AGENTS.md`
   only if it is untracked and becomes empty). In `info/exclude`, remove blueberry-added
   lines for deleted assets while keeping exclude entries for still-present preserved
   untracked paths (`/COWORKERS.md`, `/.coworkers/state/`, `/local_tests/`, or a retained
   local-only `/AGENTS.md`) so preserved state and `.lock` files do not surface as
   untracked noise unless the user asks to expose or delete them. Leave unrelated
   `.agents/` and `.pi/` files untouched.
3. **Preserve project history by default:** keep `COWORKERS.md`, `.coworkers/state/`,
   `.coworkers/tasks/`, `local_tests/` and all evidence unless the user separately and
   explicitly approves deleting specific coordination/scratch paths. Never stop running
   jobs or release active claims silently.
4. **Verify and report:** check `git status` and diffs, confirm tracked `.gitignore` and
   preserved boards/records are intact, and report removed, preserved and leftover items
   plus harness reload steps.

## Legacy board migration

Migrating an older single-board installation into task-scoped `.coworkers/` boards is a
separate, human-approved operation—never a side effect of setup or update:

1. Agree a paused-writer window (confirm no active producer/cleaner uses changing paths);
   if work cannot pause, defer migration and keep existing installed assets untouched.
2. Save a recovery backup outside disposable scratch; split shared protections/claims and
   task state without losing attribution, binding constraints, timestamps or evidence paths.
3. Convert newest-first history into bottom-latest order once (preserving same-time order
   and date-only uncertainty; never fabricate timestamps or move raw artifacts).
4. Publish canonical pointers/namespaces, merge updated prompts and skills together,
   verify links and `info/exclude`, and reload/rebind every session before resuming writers.
