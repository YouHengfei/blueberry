# <NN_stage_name>

Task: `<task_id>` · State: planned / running / blocked / reviewed
Planner/acceptance owner: (session) · Executors: (session + work item)

## Execution plan

Write for an Executor with no hidden access to the Planner's conversation.
Scale detail to risk; include enough to execute and recognize a wrong result.

1. Goal, non-goals, dependencies and starting code revision.
2. Verified prerequisites, environment and required resource scopes.
3. Ordered steps with concrete commands/procedures and safe stopping points.
4. Allowed code/config changes; prohibited changes and cost/resource limits.
5. Checks, expected observations and acceptance thresholds.
6. Evidence paths, required metrics and reproduction metadata.
7. Stop/replan conditions, failure reporting and cleanup expectations.

## Execution notes

Append significant timestamped observations at the bottom. Link raw logs instead of
pasting them. Record actual outcomes, including failures and deviations.

## Findings and review

- Code/config/environment actually tested:
- Results, uncertainty and acceptance verdict:
- Remaining work and responsible role/session:
- Reusable tools / retained evidence / disposable output disposition:

Reconcile the plan at meaningful request boundaries. The Executor proposes scope or
acceptance changes; the Planner/user approves them. Do not rewrite historical results
to match a later explanation; append a correction with its evidence.
