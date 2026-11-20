# Parallel task workflow — implementation record

Task ID: `parallel_task_workflow` · Outcome: implemented; user review and live rollout pending.
Validated: 2026-11-20. Planner/Executor self-check, not independent review.
This is a durable implementation record, not an initialized live coordination installation.

## At a glance

A single global current-task board mixed unrelated plans, handoffs and resource ownership.
The new sources separate a small project entry point, task-local mutable state, durable
records and shared reservations. A short router requests relevant context instead of all
boards. A cooperative helper protects board updates and resource claims from participating
writers. No adopting project's live configuration, jobs, board or test artifacts were changed.

## Changes and rationale

- Project/task/shared templates plus task README and optional numbered stage templates.
- `.coworkers/state/` for ignored coordination; `.coworkers/tasks/` for versionable local
  records; `local_tests/<task_id>/<run_id>/` for disposable execution output.
- Session-local task selection, explicit ambiguity choices, actionable role/state/next fields.
- Bottom-latest append history; explicit oldest-excess retention (15 handoffs / 20 decisions),
  protected binding constraints and non-FIFO registries.
- Standard-library helper: revision-checked atomic updates, exclusive all-or-nothing claims,
  owner-checked annotate/release, bounded locks and fail-closed malformed state handling.
- Task-scoped cleaner with shared-dependency checks, coordinated scratch/record write scopes,
  stronger closure disposition and no automatic cleanup or legacy-board migration.
- Local branch/worktree/checkpoint/publication guidance; philosophy, Mermaid diagram and user guide.
- Optional Pi task-selection prompt; documented loading boundaries and deferred context experiments.

Rejected: one huge shared board, independent copies of reservations, a global current-task
selector, durable records in disposable scratch, and automatic expiry/stealing of old claims.
No daemon, installer, model API dependency or process-control mechanism was introduced.

## Source identity

Base checkout: `d1ff94b` (`origin/main`) plus the clean task-workflow sources.
This is not a claim that the base commit alone reproduces the tested sources.

- Tested source fingerprint: `ee19eb6beb8a70aa027f755c2322244587e4451aa9e75443e961306a116a1aed`.
- Helper SHA-256: `af38e894033d4b408d3f79ae54637c7e65a6fce2eae59e9dfc34fe6a333ba998`.
- Fingerprint recipe: sort the 24 `.md`/`.py`/`.json` files in root `README.md`,
  `package.json`, `toolkit/` and `tests/`; hash each relative POSIX path + NUL + file
  bytes + NUL in order with SHA-256. This record is excluded to avoid self-reference.

## Validation and reproduction

From the source checkout:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
```

| Check | Result | Limits |
|---|---|---|
| Isolated unittest suite | 41 passed, 0 failures, 0 skips | Local POSIX host, Python 3.13.13 |
| Competing processes | One winner for conflicting claims / stale board revisions | Cooperative writers only |
| Crash and I/O behavior | Lock releases; reservations persist; post-replace errors require reread | Not distributed durability testing |
| Git fixtures | Ordinary and linked worktrees, selective exclusions and canonical claims pass | Temporary repos only |
| Copied assets / links / metadata | Pass | Not interactive harness discovery or an automated agent setup test |
| Router footprint | 203 whitespace-delimited words / 1,506 bytes | Not provider tokens or live request measurements |
| Syntax / whitespace | Python 3.10 grammar and diff checks pass | Python 3.10 runtime not exercised |

An intermediate fixture failure assumed `git init --template=` creates `info/exclude`;
the fixture now explicitly seeds local rules, and setup documents creating an absent
exclude file/parent. This was a test-fixture correction, not a live Git change.

## Evidence and cleanup

Reusable evidence is the source test suite and the fingerprints above. Temporary
repositories, synthetic boards and test subprocesses are removed/stopped by their fixtures;
no raw result directories or one-off scripts are retained. No real test artifacts were deleted.
Pre-existing working-tree changes and tracked ignore files were preserved.

## Limitations and next action

- Review the sources before publication or deployment. Publication and live rollout require authorization.
- Helper locks are advisory, local-POSIX only; identities/namespaces require cooperation.
  They do not authenticate owners, detect aliases, validate physical availability or protect
  arbitrary direct edits. Code and durable-record writers need their own scope coordination.
- No live board migration, installed skill update, workload restart or harness reload occurred.
  Agree a paused-writer migration window before rolling out the new layout and cleaner together.
- Execute the synthetic context-footprint matrix in `tests/README.md` for Pi and then other
  verified harnesses/models. Actual LLM task routing, subagent inheritance, compaction behavior
  and request token deltas remain unmeasured. Do not infer them from static size checks.
