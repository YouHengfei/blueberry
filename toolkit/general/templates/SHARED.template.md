# Shared coordination

One authoritative copy under the canonical coordination root. Refresh before claiming
resources or cleaning; verify live occupancy separately.

## Resource namespaces

| Stable namespace | Real host / workspace / scope | Verification runbook |
|---|---|---|

Slash-separated, case-sensitive IDs; parent/child scopes conflict (aliases are not
matched). Examples: `host/worker_a/device/0`, `host/worker_a/port/tcp/8000`,
`workspace/main/files/src`, `workspace/main/scratch/example_task`. Claims are exclusive
and all-or-nothing.

## Claims — helper managed

Use `coord.py` `claim`/`annotate`/`release` only; never edit rows or unlink lock files.

<!-- blueberry:claims:start -->
| Claim | Task | Session | Resources | Since | Job |
|---|---|---|---|---|---|
<!-- blueberry:claims:end -->

## Protected assets and cross-task dependencies

| Added | Path / workspace | Retention reason | Consumers / owner | Release condition |
|---|---|---|---|---|

Hold the workspace scratch-scope claim while adding/removing cross-task dependencies.
Protect shared baselines, accepted evidence and uncertain paths. No auto-expiry or FIFO.

## Cross-task decisions

Append timestamped entries at bottom; preserve binding constraints before explicit
oldest-excess cleanup (20 decisions).
