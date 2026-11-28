# Task-local workflow

Read on demand for task create/close, shared claims, publishing or rule changes—not every
turn. Paths are workspace-relative unless `COWORKERS.md` names another canonical root.

## 1. Tasks and sessions

- **Select:** Explicit task wins; else keep this session's task. If unclear, offer
  matching tasks, a `snake_case` ID (≤64 chars), or discussion-only. Never infer from
  latest activity or a global current-task file.
- **Create:** After approval only, via `coord.py init-task` (or board + README + index).
- **Sessions:** Bind task + role + session ID/alias. Use fresh sessions for unrelated
  work; reconfirm after ambiguous resume or compaction.

## 2. Roles, plans and acceptance

- **States:** `ready`, `running`, `blocked`, `review`, `done`, `cancelled`. Single `Next`
  owner; add `Blocked by / Unblock` only when blocked. Roles are harness-agnostic and
  task-scoped (one session may fill several; label self-checks; one acceptance owner).
- **Planner:** Owns scope, design, core/complex implementation when appropriate, and an
  executable plan (revision, prerequisites, steps, scope/resources, checks, evidence,
  stop/cleanup rules) with no hidden context. Small tasks need no stage file.
- **Acceptance gate:** Before marking a coding task `ready`, Planner supplies an
  existing test command or new tests for critical behavior and negative cases
  (prerequisites + expected results) and confirms they fail for the intended reason on
  the broken baseline where practical (else notes the limit). Exploration uses a
  bounded experiment and required evidence.
- **Executor / Reviewer:** Executor owns delegated bounded slices, test/benchmark runs,
  regressions and its jobs/scratch; must not weaken acceptance checks without Planner
  approval. Stop/replan on invalidating findings. Planner reviews diff, tests and
  evidence—Passing tests alone do not establish acceptance. Reviewer is optional (ideal
  when Planner wrote core code).

## 3. Writing and records

- **Layout:** `COWORKERS.md` (index), `.coworkers/state/{shared.md,tasks/<id>.md}`
  (mutable, excluded), `.coworkers/tasks/<id>/{README.md,stages/NN_*.md}` (durable),
  `local_tests/<id>/<run_id>/` (disposable). Never rename IDs or copy stage plans into
  boards; link raw logs.
- **History:** Bottom is latest (`YYYY-MM-DD HH:MM`). Append decisions/handoffs/index/
  registries; update snapshots in place. Never re-sort, invent times, or rewrite verdicts
  (append corrections). Reconcile changed state at boundaries—no no-op handoffs.

## 4. Parallel work and claims

- **Stay in the current checkout by default** for single-goal work. Create a linked
  worktree only when another active task/dirty tree occupies the checkout or the user
  asks (confirm path; worktrees do not isolate editable `.venv` installs; remove at
  closure). Share one canonical root across worktrees; keep durable records in its
  worktree.
- Scope is not ownership: map namespaces in `shared.md`, verify live occupancy, claim via
  `coord.py`, annotate PIDs/ports/logs, release when jobs stop. Hold scratch claims while
  producing, registering dependencies, or cleaning. Never kill others' jobs or steal
  claims (stale recovery needs owner/user approval + evidence). Coordinate record/stage
  edits via single writer or file-scope claim.

## 5. Git, closure and gates

- **Local-first Git:** Checkpoint locally; commit before evidence runs or save dirty
  patch + env. Never commit secrets, mutable state, or scratch. Before publication:
  freeze writers, keep backup refs, prepare reviewed commits (strip unapproved local
  records from history), validate, ask before push.
- **Closure & cleanup:** Before `done`/`cancelled`, record acceptance, `README.md`,
  released claims/jobs, and keep/promote/delete/defer disposition (mark removed items).
  Cleanup is explicit (`local-tests-cleaner`; project-wide needs separate request);
  compact above 15 handoffs / 20 decisions from top (keep binding constraints);
  registries are never FIFO.
- **Human gates:** Ask on ambiguity, scope/acceptance/ownership conflicts, destructive
  retirement, acceptance, publication. Rule changes: proposal → approval → merge → check.
