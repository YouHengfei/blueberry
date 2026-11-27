# Scratch-artifact lifecycle

`local_tests/<task_id>/<run_id>/` holds disposable outputs; durable summaries live in
`.coworkers/tasks/<task_id>/README.md`. Do not move existing evidence solely for layout.

- **Register or delete:** Keep a scratch item only with a task-registry entry and clear
  future use (register shared baselines and cross-task uses in `shared.md` while holding
  the workspace scratch-scope claim). Capture metrics, revision and config before removing
  summarized raw logs; mark removed items as removed.
- **Aggressive closure cleanup:** Within the selected task's scratch scope, explicit
  cleanup auto-deletes and reports: unregistered one-off probes, this task's unregistered
  unsummarized failed/empty run dirs, empty dirs, and superseded raw outputs whose
  conclusions are already captured. Approval gates remain for registered retirement,
  accepted evidence/shared baselines, cross-task consumers, >10 GB/unknown-size deletions
  and anything outside task scope. Retention limits never trigger deletion.
- **Safety & Git:** Task-scoped by default; project-wide only on separate explicit request.
  Never follow symlinks, cross mounts, kill jobs, or delete durable task records/locks.
  Exclude `/local_tests/` locally via `git rev-parse --path-format=absolute --git-path info/exclude`;
  never commit raw logs or secrets. Use `local-tests-cleaner` for bounded cleanup; registries
  append at bottom and are never FIFO.
