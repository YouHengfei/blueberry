---
name: local-tests-cleaner
description: Explicit task-scoped scratch cleanup and bottom-latest board compaction; project-wide only when requested. Preserve active work, shared dependencies, durable task records and accepted evidence.
disable-model-invocation: true
---

# Local tests / task board cleaner

Run only when explicitly invoked. Default to this session's confirmed task; if
ambiguous ask which task, or whether project-wide cleanup is intended. No automatic
cleanup at task completion or retention limits. Missing/legacy layout: stop and
request setup/migration; never deploy this procedure over a live single-board workflow.

## Procedure

1. **Scope and inventory.** Read the project entry point and selected task state,
   relevant registry/record, shared protections and a shallow candidate inventory.
   Do not load every board, raw log/audio, or recursively explore result trees.
   Project-wide work requires explicit scope and the relevant active AND closed-task
   registries; unresolved consumers mean keep. Missing `local_tests/`: board-only
   work, do not create it. Missing summaries: skip, do not reconstruct experiments.
2. **Protect and approve.** Prepare one keep/promote/delete/defer disposition. Prefer
   retiring disposable probes, failed scratch, duplicate outputs and superseded raw
   logs after conclusions (metrics/config/code revision) exist in durable records.
   Preserve active/uncertain ownership, registered artifacts, accepted evidence,
   shared baselines, Markdown summaries/archives and cross-task dependencies.
   Registered retirement needs explicit user approval. Deletions >10 GB or of
   unknown total size need explicit approval; measure only candidate sizes as needed.
   Promotion to maintained project files is a proposal, not authorized by this skill.
3. **Recheck, clean, record.** Acquire the relevant workspace scratch-scope and
   task-record write-scope reservations atomically through the helper before deletion;
   if busy or namespace/ownership is unclear, skip. Producers and dependency registrants
   must use the same scratch scope; record writers use its file scope. Refresh
   shared protections and candidate ownership AFTER acquiring it and after any user
   approval wait. Do not hold an OS lock while waiting or deleting. Delete only the
   approved/confirmed disposable candidates; scope changes require renewed approval.
   Mark intentionally removed artifacts in the durable task record, without rewriting
   conclusions. Snapshot the task board afresh, append one timestamped cleanup handoff
   at the bottom, and remove only oldest excess above **15 handoffs / 20 decisions**
   from the top. At the limit remove nothing. Before evicting a binding decision,
   preserve its constraint/rationale/evidence in the current plan or durable record;
   otherwise keep and report the exception. Use helper revision-checked updates;
   stale writes must be reread/merged. Release only your cleanup claim after work stops.

## Writing and safety

- Bottom is latest. Append new decisions/handoffs/registry entries; update metadata
  in place. Use workspace `YYYY-MM-DD HH:MM`; preserve recorded times/ties and delayed
  event annotations. Never re-sort history or invent timestamps.
- Registries are never FIFO. Aim for ~15 useful rows by safe consolidation or approved
  retirement, not arbitrary deletion. Target concise boards, not hard information loss.
- Delete only inside the selected real `local_tests/` scope; never follow symlinks or
  cross mounts. Legacy non-namespaced paths need explicit ownership/scope confirmation.
- Never delete `.coworkers/tasks/`, another task's records, locks, or live board files.
  Outside scratch, only scoped board compaction and artifact-disposition metadata are
  allowed; no source/environment changes or automatic archival/migration.
- Do not compact other active boards during task cleanup. Project-wide compaction
  requires their owners' agreement. Never transfer tasks/claims or stop others' jobs.
- Report removed/retained counts, freed space only if measured, deferred items and
  unfinished metadata updates. On a conflict after deletion, report the actual deletion
  and reconcile metadata; do not imply that file and board operations were atomic.
