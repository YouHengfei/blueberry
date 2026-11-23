# Task-local workflow and user guide

Read this when joining or changing a workflow, not on every request. Paths below
are relative to the project workspace unless the entry point names a different
canonical coordination root. This is guidance, not a second live board.

## 1. Select a task

Say `Work on task <task_id> as Planner/Executor` or describe the intended work.
The agent retains a clearly matching session-local binding. An explicit task wins.
When ambiguous, it offers relevant existing tasks, a proposed new snake_case task,
or discussion-only. Confirm before ambiguous creation/joining. General questions
need no task. Never select by the newest board entry or a shared current-task file.

For a new approved task, choose an unused, stable ID (<=64 characters, lowercase
snake_case starting with a letter). Inspect existing owners, create its state board
from the task template and its record README from the record template, then add
one index row. Creation is deliberate, not a side effect of reading missing state.
Use helper `update --expected missing` for new coordination files; task records are
ordinary project files. A task-file creation and index update are separate state
writes, not a multi-file transaction: if interrupted, reconcile the index from
verified boards with owners. The index is a discovery aid, not reservation authority.

Bind the conversation to task + role + real session ID or a declared unique alias.
On ambiguous resume/compaction, reconfirm and reread current state. A fresh session
is preferable for unrelated work: forks/clones inherit old conversation context.
No need to repeat the task ID on every clearly continuing request.

## 2. State and responsibilities

Each task has one current snapshot: goal, state, stage, Planner/acceptance owner,
Executors with distinct work items, next action, workspace/branch, records and plan
pointers. Add blocker + unblock owner only when blocked. States are `ready`,
`running`, `blocked`, `review`, `done`, `cancelled`. The `Next` field identifies
who acts next; do not introduce redundant waiting/blocked booleans.

Planner defines scope and observable acceptance, writes an executable plan, and
accepts or replans from evidence. Plans include starting revision, prerequisites,
ordered steps, allowed changes/resources, checks and thresholds, evidence, stop
conditions and cleanup expectations. Write for an Executor without hidden context;
be specific, not unnecessarily verbose. A small task needs no separate stage file.

Before marking a coding task `ready`, Planner supplies an existing test command or
new tests for critical behavior and negative cases, with prerequisites and expected
results. Where practical, confirm they fail for the intended reason on the broken
baseline; otherwise note the limitation. For exploration, specify a bounded experiment
and required evidence instead.

Executor runs the checks, adds regressions and reports deviations; it must not weaken
acceptance checks without Planner approval. Planner reviews the diff, test validity
and evidence. Passing tests alone does not establish acceptance.

Executor confirms prerequisites, implements/tests within scope, records actual
code/config/environment and results, and manages its jobs and scratch. Unexpected
conditions that invalidate the plan require a stop/replan, not silent scope expansion.
Reviewer provides optional independent scrutiny for risk or disputed evidence.
Roles are responsibilities, not project-global positions or mandatory separate agents.
Label self-checks honestly; several Planners still need one acceptance owner per task.

At meaningful request boundaries, reconcile state, next action, plan validity,
evidence and reservations. Write only changes; no no-op handoffs. Executors propose
scope/acceptance changes; Planner/user approves them. Unchanged failures are not
passing checks, and incomparable evidence is inconclusive.

## 3. Read selectively

Load the small project entry point, selected task state, current plan and only
relevant evidence. Shared claims/protections are refreshed before a shared action.
Do not read all task boards or all stages at startup. Cross-task review and project
cleanup are explicit exceptions with a bounded relevant set.

Detailed files are ordinary Markdown, not additional auto-discovered instruction
files. Once read, tool output can remain in conversation context; reading a huge
board once does not eliminate its cost on subsequent model requests. Existing
project engineering rules stay in their owning instruction/doc entry points.

## 4. Parallel work and shared resources

Use one canonical coordination root across participating worktrees. Their local
`COWORKERS.md` files can be small pointers to it, not independent indexes or claims.
Mutable task state lives there; versioned records live in the task's actual worktree.
Record that path in the task board. Separate clones/hosts do not share ignored files
magically. Do not claim concurrency safety without a genuinely shared, supported store.

Read-only work can share a checkout. Small disjoint edits may share one with explicit
scopes. Substantial independent implementation should use separate task branches and
worktrees. Intended write scope is not ownership: claim active scopes in shared state.
Namespace file/scratch claims by real workspace identity, infrastructure by real host
and resource identity. Use one agreed mapping; aliases can evade textual conflict checks.

The helper serializes short board/claim transactions, not the job itself. All writers
must cooperate. Refresh live occupancy, claim all required scopes atomically, then
check/start the job. If startup fails, verify no owned process remains before release.
Annotate jobs with PIDs/start identity, ports and log paths when available. Never kill
another session's job, transfer ownership, or infer abandonment from age alone.

Hold the relevant scratch-scope reservation while producing or cleaning output.
Cross-task consumers acquire that scope briefly to register dependencies in shared.md
before use; keep their protection entry until finished. Cleanup acquires the same scope,
then refreshes protections. Long jobs do not hold OS file locks, only recorded claims.
The helper cannot validate hardware availability or prevent uncooperative external jobs.

For a stale-looking reservation, ask the owner/user and verify processes. Human-approved
recovery may release using the recorded identity only after documenting that approval
and evidence in the task record. There is no automatic expiry, force-steal or kill command.

## 5. Local-first Git

Prefer one branch `task/<task_id>` and worktree per substantial task. Within it,
checkpoint coherent stages (reproduce, instrument, fix, validate), not every message.
Use project commit conventions and explicit paths; do not stage another task's work.
Do not switch branches, stash/reset, or rewrite history in another active checkout.
Local commits require the user's task/workflow authorization; setup never commits.

Before evidence-producing runs prefer a committed checkpoint. Otherwise capture the
additional dirty patch safely; a base hash alone does not identify the tested code.
Record config/environment as well. Task records can be committed locally; mutable
coordination and raw logs are not. Local Git is not a place for credentials either.

Before publication: freeze writers; retain backup refs and evidence checkpoints;
prepare coherent commits on a publication branch; inspect both history and final diff;
validate the publication candidate; record its exact tested revision; ask before push.
Simply deleting local-only records from the final tree does not remove them from earlier
commits. Keep only approved material in published history; preserve local investigation
refs needed for reproducibility. Worktrees do not isolate editable environments,
containers, devices, ports, services or external output paths.

## 6. Records and naming

- Root `COWORKERS.md`: index, project pointers, routing, setup provenance.
- `.coworkers/state/tasks/<task_id>.md`: live snapshot, decisions and handoffs.
- `.coworkers/state/shared.md`: authoritative claims, namespaces, shared protections.
- `.coworkers/tasks/<task_id>/README.md`: durable task narrative and final summary.
- `.coworkers/tasks/<task_id>/stages/NN_short_description.md`: optional detailed plans/results.
- `local_tests/<task_id>/<run_id>/`: disposable execution output; use unique sortable run IDs.

Use stable snake_case IDs and numbered stage names; never rename a task on status change.
Keep one source per topic. The board links to the stage plan, not a copied plan. Versioned
record/stage files are not protected by board revision checks: assign one writer or claim
their workspace file scope before editing, including when Planner and Executor share a
task. Handoff proposed changes rather than concurrently rewriting the same plan. Summaries
link to raw evidence instead of embedding logs. Do not move existing evidence merely to
match the new layout. Official project docs stay where that project already keeps them.
Promote supported knowledge there only after approval, not whole investigation transcripts.

Append new handoffs, decisions, index and registry entries at the bottom. Current snapshots
and metadata update in place. Use workspace `YYYY-MM-DD HH:MM` timestamps; append order is
the history order. Delayed reports may record event and reporting times. Preserve original
timestamps, ties and uncertainty; no continual sorting or invented times. Corrections append
and identify the superseded claim instead of rewriting historical evidence.

Explicit cleanup retains newest 15 handoffs / 20 decisions, removing only oldest excess
from the top. Preserve binding constraints/rationale/evidence in current plans or durable
records before eviction; otherwise retain and report exceptions. Registries are never FIFO;
aim for ~15 useful rows through approved retirement/consolidation, not arbitrary deletion.

## 7. Finish and clean

Coding complete is not task complete. Before `done`, record acceptance, a readable task
README, owned job/claim release, and a keep/promote/delete/defer disposition. Exceptions
are explicit. Cancelled tasks also need a short outcome and artifact disposition, not an
invented successful result. Routine questions need neither a board nor a completion essay.

The task README starts with problem/change/outcome/proof, then cause/solution, alternatives,
revisions, validation table, reproduction, evidence manifest, limitations and cleanup.
Failed/unchanged checks and absent tests remain visible. Mark removed raw artifacts as
removed, explaining remaining verification limits; do not imply dangling paths still exist.

Task-scoped cleanup is the default, explicitly requested. Within the selected task's
scratch scope it auto-deletes and reports the low-risk classes: unregistered one-off
probes, this task's unregistered unsummarized failed/empty run dirs, empty directories,
and superseded raw outputs whose conclusions are already captured. Approval gates
remain for registered retirement, accepted evidence and shared baselines, cross-task
consumers, >10 GB/unknown-size deletions and anything outside the task scope. Missing
summaries of other tasks are skipped, not reconstructed. Retention limits never
trigger deletion.

Project-wide cleanup requires a separate explicit request and review of relevant task
registries (including closed tasks with retained evidence) and shared protections. Do not
compact another active board without agreement. No cleaner deletes durable task records,
follows symlinks/crosses mounts, or releases someone else's reservations. Use the explicit
cleaner skill or the scratch policy for the bounded procedure and size-approval limits.

## 8. Human gates and evolution

Ask at ambiguity, scope/acceptance changes, conflicting ownership, destructive retirement,
final acceptance and publication. Ordinary authorized work does not need repeated approval.
User/task-driven workflow evolution is proposal → human approval → explicit merge → validation.
Never silently rewrite persistent instructions from inferred preferences or task outcomes.

## 9. Migrate an existing board

This is a separate approved operation, never a side effect of installing updated assets.
Agree a paused-writer window; confirm no active producer/cleaner will use changing paths.
Inventory task content, shared protections, timestamps and current jobs; retain a recovery
copy outside disposable scratch. Split without losing attribution, binding constraints or
paths. Review old newest-first history once into bottom-latest order, preserving same-time
relative order and date-only uncertainty. Do not fabricate times or move raw artifacts.
Publish canonical pointers and namespace mappings; merge prompt/skill changes together;
verify links and ignore rules; reload/rebind every participating session before writers resume.
If any participant cannot pause, defer migration. Existing installed copies remain unchanged
until their approved migration; never pair a new cleaner with an unmigrated live board.
