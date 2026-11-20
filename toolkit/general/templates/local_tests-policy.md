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
  and important negative findings. A cleaner skips missing summaries; it does not
  reconstruct an investigation. Removed raw evidence is marked removed, not linked as live.
- **Narrow retained evidence.** Keep the latest accepted full run per backend when
  applicable; a newer failed run does not replace it. Protect anything still needed by
  another task. Registered retirement needs explicit approval, even for completed tasks.
- **Task closure.** Present keep/promote/delete/defer as one batch: keep required proof,
  propose reusable tests/tools for maintained locations, remove disposable probes,
  failed runs, duplicates and superseded raw logs; defer unknown owners/dependencies.
  Completion does not authorize silent bulk cleanup. Record acceptance and exceptions.
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
