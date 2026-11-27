# <NN_stage_name>

Task: `<task_id>` · State: planned / running / blocked / reviewed
Planner: (session) · Executors: (session + work item)

## Execution plan

Write with no hidden Planner context; scale detail to risk:

1. Goal, non-goals, dependencies and starting revision.
2. Verified prerequisites, environment and resource claims needed.
3. Ordered steps with commands and safe stopping points.
4. Allowed/prohibited changes and resource/cost limits.
5. Planner-owned acceptance check (before `ready`): command, prerequisites, expected
   results, negative cases, baseline evidence/limit (or bounded experiment + evidence).
6. Evidence paths, metrics, stop/replan conditions and cleanup expectations.

## Execution notes

Append timestamped observations at bottom (link raw logs; record failures/deviations).

## Findings and review

- Tested code/config/environment:
- Results, uncertainty and acceptance verdict:
- Remaining work and next owner:
- Keep / promote / delete / defer disposition:

Reconcile changes at boundaries; Executor proposes scope/acceptance changes for Planner
approval. Append corrections rather than rewriting history.
