---
name: local-tests-cleaner
description: Explicit task-scoped scratch cleanup with aggressive auto-delete of low-risk disposable classes and bottom-latest board compaction; approval gates for registered, shared, cross-task and large deletions. Preserve durable task records and accepted evidence.
disable-model-invocation: true
---

# Local tests / task board cleaner

Run only when explicitly invoked. Default to this session's confirmed task; if ambiguous,
ask which task or whether project-wide cleanup is intended. Retention limits never trigger deletion.
Missing or legacy layout: stop and request setup/migration; never run over an unmigrated
single-board workflow.

## Procedure

1. **Scope & inventory:** Read `COWORKERS.md`, selected task state, task registry/record,
   shared protections, and a shallow candidate listing (no deep tree walks or raw logs).
   Project-wide cleanup requires explicit scope plus active and closed-task registries
   (unresolved consumers = keep). Missing `local_tests/`: compact board only, do not create
   it. Skip missing summaries of other tasks—never reconstruct experiments.
2. **Classify & gate:** Within the selected task's scratch scope, auto-delete and report:
   unregistered one-off scripts/probes; this task's unregistered unsummarized failed/empty
   run dirs; empty dirs; duplicate/superseded raw outputs whose conclusions (metrics,
   config, revision) exist in summaries/records. Require explicit approval for: registered
   retirement, accepted evidence/shared baselines, cross-task consumers, anything outside
   task scope, and deletions >10 GB or of unknown size (measure candidates only as needed).
   Preserve active/uncertain ownership, Markdown summaries, and durable records. Code
   promotion is a proposal only.
3. **Claim, clean, record:** Acquire workspace scratch-scope and task-record write-scope
   claims atomically via `coord.py` (skip if busy/unclear). Refresh shared protections and
   ownership AFTER acquiring claims and after any approval wait; never hold OS locks while
   waiting/deleting. Delete only confirmed/approved items (scope changes need renewed
   approval). Mark intentionally removed artifacts in the durable task record. Snapshot the
   task board afresh, append one timestamped cleanup handoff at bottom, and compact oldest
   excess above **15 handoffs / 20 decisions** from the top (preserve binding constraints
   in plan/record first, else keep and report). Use revision-checked updates; release only
   your cleanup claim after work stops.

## Safety rails

- Bottom is latest (`YYYY-MM-DD HH:MM`); never re-sort or invent times.
  Registries are never FIFO (~15 useful rows via consolidation/approved retirement).
- Delete only inside the selected real `local_tests/` scope; no symlinks or mount
  crossings. Legacy non-namespaced paths need explicit confirmation.
- Never delete `.coworkers/tasks/`, other tasks' boards/records, lock files, or stop
  others' jobs/steal claims. Project-wide board compaction needs owners' agreement.
- Report removed/retained counts, freed space only if measured, deferred items, and any
  post-deletion metadata conflicts (file deletion and board updates are not atomic).
