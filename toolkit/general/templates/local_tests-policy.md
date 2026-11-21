# Scratch-artifact lifecycle

`local_tests/<task_id>/<run_id>/` holds disposable execution output, not permanent
knowledge. Keep durable summaries in the task workspace's
`.coworkers/tasks/<task_id>/README.md` and optional numbered stage documents.
Do not move existing evidence just to adopt this layout.

- **Register or delete.** Retain a tool/result only with a clear future purpose,
  reproduction information and task-registry entry. Cross-task consumers and shared
  baselines also register in canonical `shared.md` before use. Otherwise remove your
  confirmed one-off scratch within the authorized task scope after use.
- **Conclusions before deletion.** Capture metrics, code revision, config/environment
  and important negative findings before removing anything summarized. Removed raw
  evidence is marked removed, not linked as live.
- **Narrow retained evidence.** Keep the latest accepted full run per backend when
  applicable; a newer failed run does not replace it. Protect anything still needed by
  another task. Registered retirement needs explicit approval, even for completed tasks.
- **Aggressive closure cleanup.** At task closure (and explicit task cleanup),
  auto-delete and report the low-risk classes: unregistered one-off probes, this
  task's unregistered unsummarized failed/empty run dirs, empty directories, and
  superseded raw outputs whose conclusions are already captured. One approval batch
  still gates registered retirement, accepted evidence/shared baselines, cross-task
  consumers, >10 GB/unknown-size deletions and anything outside the task scope.
  Retention limits never trigger cleanup. Record acceptance and exceptions.
- **Concurrency.** Producers, cleaners and dependency registrants use the same canonical
  workspace scratch namespace. Cleanup holds that reservation and refreshes protection
  records after acquisition and approval waits. Never kill jobs to make cleanup possible.
- **Safety.** Explicit task cleanup by default, project-wide only on request. No symlink
  traversal or mount crossing; uncertain ownership means keep. >10 GB or unknown-size
  deletions need explicit approval. Never delete durable task records or lock files.
- **Git.** Exclude scratch locally through `git rev-parse --git-path info/exclude`,
  preserving existing effective rules and tracked `.gitignore`. Do not commit raw logs,
  credentials or large outputs. Ignore rules do not untrack existing files.

Invoke the explicit cleaner skill for bounded inventory, safe disposition and board
compaction. Limits alone never trigger deletion. Registry order is append-at-bottom,
metadata updates in place; it is never a FIFO deletion queue.
