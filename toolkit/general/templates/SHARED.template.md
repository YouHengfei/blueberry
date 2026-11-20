# Shared coordination

One authoritative copy under the canonical coordination root, not per worktree.
Refresh before claiming resources or deleting candidate artifacts. This file is
coordination, not proof of live availability; verify actual occupancy separately.

## Resource namespaces

| Stable namespace | Real host / workspace / scope | Verification runbook |
|---|---|---|

Agree on namespace mappings before claims. IDs are slash-separated and case-sensitive;
use the same spelling for the same resource. Parent/child scopes conflict.
Examples: `host/worker_a/device/0`, `host/worker_a/device/0/core/1`,
`host/worker_a/port/tcp/8000`, `workspace/main/files/src`,
`workspace/main/scratch/example_task`. Different aliases are NOT detected as equal.
All v1 claims are exclusive; multi-resource claims are all-or-nothing.

## Claims — helper managed

Use claim/annotate/release; generic board updates cannot change the rows.
Do not steal stale-looking claims, delete lock files, or edit rows directly.

<!-- blueberry:claims:start -->
| Claim | Task | Session | Resources | Since | Job |
|---|---|---|---|---|---|
<!-- blueberry:claims:end -->

## Protected assets and cross-task dependencies

| Added | Path / workspace | Retention reason | Consumers / owner | Release condition |
|---|---|---|---|---|

Register cross-task consumers before using an artifact, even read-only. Acquire its
workspace scratch-scope claim while adding/removing a dependency so cleanup cannot
race registration. Keep shared baselines and latest accepted full runs here when
applicable; a new failed run does not supersede accepted evidence. Uncertain paths
remain protected. No automatic expiry or FIFO retirement.

## Cross-task decisions

Append timestamped decisions at the bottom; keep details in referenced task records.
Promote still-binding constraints before explicit oldest-excess cleanup (20 decisions).
