# Task-local workflow

Read on demand for task create/close, shared claims, publishing or rule changes—not every
turn. Paths are workspace-relative unless `COWORKERS.md` names another canonical root.

## 1. Tasks and sessions

- **Select:** Explicit task wins; else keep this session's task. If unclear, offer
  matching tasks, a `snake_case` ID (≤64 chars, letter-start), or discussion-only. Never
  infer from latest board activity or a global current-task file.
- **Create:** After approval only. Create `.coworkers/state/tasks/<task_id>.md` via
  `coord.py update --expected missing`, create `.coworkers/tasks/<task_id>/README.md`,
  then append one index row in `COWORKERS.md` (reconcile if interrupted).
- **Sessions:** Bind task + role + real session ID/alias. Prefer fresh sessions for
  unrelated work; reconfirm and reread state after ambiguous resume or compaction.

## 2. Roles, plans and acceptance

- **States:** `ready`, `running`, `blocked`, `review`, `done`, `cancelled`. Use one
  `Next` owner field; add `Blocked by / Unblock` only when blocked. Roles attach to tasks
  (one session may fill several; label self-checks; one acceptance owner per task).
- **Planner:** Writes an executable plan (starting revision, prerequisites, steps,
  allowed scope/resources, checks, evidence, stop/cleanup conditions) with no hidden
  context. Small tasks need no stage file.
- **Acceptance gate:** Before marking a coding task `ready`, Planner supplies an
  existing test command or new tests for critical behavior and negative cases
  (prerequisites + expected results) and confirms they fail for the intended reason on
  the broken baseline where practical (else notes the limit). Exploration uses a
  bounded experiment and required evidence.
- **Executor / Reviewer:** Executor verifies prerequisites, implements in scope, adds
  regressions, reports deviations, and must not weaken acceptance checks without Planner
  approval. Stop/replan on invalidating findings. Planner reviews diff, tests and
  evidence—Passing tests alone do not establish acceptance. Reviewer is optional.

## 3. Writing and records

- **Layout:** `COWORKERS.md` (index), `.coworkers/state/{shared.md,tasks/<id>.md}`
  (mutable, excluded), `.coworkers/tasks/<id>/{README.md,stages/NN_*.md}` (durable),
  `local_tests/<id>/<run_id>/` (disposable). Never rename IDs or copy stage plans into
  boards; link raw logs.
- **History:** Bottom is latest (`YYYY-MM-DD HH:MM`). Append decisions/handoffs/index/
  registries; update snapshots in place. Never re-sort, invent times, or rewrite verdicts
  (append corrections). Reconcile only changed state at boundaries—no no-op handoffs.

## 4. Parallel work and claims

- Share one canonical coordination root across worktrees; durable records stay in the
  task's worktree (path in board). Use `task/<id>` worktrees for substantial parallel work.
- Intended scope is not ownership: map canonical namespaces in `shared.md`, check live
  occupancy, claim scopes atomically via `coord.py`, annotate PIDs/ports/logs, and
  release after jobs stop. Hold scratch-scope claims while producing, registering
  cross-task dependencies, or cleaning. Never kill others' jobs or steal claims; stale
  recovery needs owner/user approval + evidence. Coordinate edits to versioned files
  (records/stages) via single writer or file-scope claim.

## 5. Git, closure and gates

- **Local-first Git:** Checkpoint stages locally (`task/<id>`); commit before evidence
  runs or capture dirty patch + env. Never commit secrets, mutable state, or scratch.
  Before publication: freeze writers, keep backup refs, build reviewed commits (strip
  unapproved local records from full history), validate, ask before push.
- **Closure & cleanup:** Before `done`/`cancelled`, record acceptance, task `README.md`,
  released claims/jobs, and keep/promote/delete/defer disposition (mark removed items).
  Cleanup is explicit (`local-tests-cleaner`; project-wide needs separate request);
  compact above 15 handoffs / 20 decisions from top after keeping binding constraints;
  registries are never FIFO.
- **Human gates:** Ask on ambiguity, scope/acceptance/ownership conflicts, destructive
  retirement, acceptance, publication. Rule changes: proposal → approval → merge → check.
