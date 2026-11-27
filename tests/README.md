# Validation: mechanics now, agent behavior separately

Run from the blueberry checkout with Python 3.10+ (POSIX for locking):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

The context-footprint measurement harness lives in
[experiments/context-footprint](../experiments/context-footprint/README.md): Tier A
(scripted mock model, zero cost, against the real Pi binary using workspace `AGENTS.md`
and `.agents/skills/`) is runnable and passing;
Tier B (real models) requires explicit spending authorization. The matrix below is the
full scenario set; Tier A mechanically covers the assembly rows, not model judgment.

No third-party test dependency, model API, device, container, real workload, live
project board or retained artifact is needed. Writes are confined to automatically
removed temporary directories. Git integration tests create commits/worktrees only
inside those disposable fixtures; they do not commit this checkout or change global
Git configuration. Test subprocesses are the only processes these tests terminate.

## Automated scope

- Revision-checked create/update/no-op, stale-write rejection and independent boards.
- Real competing subprocesses: one winner for a shared revision or conflicting claim.
- All-or-nothing claims, namespace ancestry/boundaries, owner checks and job annotations.
- Bounded lock waits, process-crash lock release with persistent reservation records.
- Malformed state fails closed; generic updates cannot edit claims.
- Path restrictions, symlink/hardlink guards, bounded input and pre/post-replace I/O
  failures (post-replace errors need a fresh snapshot, not an assumption of rollback).
- Generic template links/frontmatter, unified [INSTALL.md](../INSTALL.md) and Pi /
  Antigravity adapter contracts, static word budgets across the router (<=110 words),
  `WORKFLOW.md` (<=550 words), templates, helper guide and cleaner skill, and a copied
  helper/template round trip in a disposable project (not automated agent setup).
- Disposable ordinary/linked Git worktrees: resolved info/exclude, selective ignores
  (preserving `.coworkers/tasks/` and unrelated `.agents/` files), versionable task
  records and one canonical shared reservation root.
- Synthetic task-state reads stay scoped to the requested file. This tests helper
  I/O isolation, NOT an LLM's decision about which file to request.

POSIX tests are skipped on unsupported platforms. A cross-device guard unit test does
not validate network filesystem locking. Observe the actual reported pass/skip count;
never describe skipped or unexecuted coverage as a pass.

## Context-footprint experiment matrix

This is an explicit experiment protocol, not completed compatibility evidence. Use
synthetic tasks with unique detail markers and no private project content. Compare
baseline and blueberry under the same harness version, model/config and session history.
Record source revision/dirty patch identity, adapter version, model and scenario inputs.
Tier A (assembly) is measured; rows marked *behavioral* still need Tier B with a real model.

| Scenario | Expected reading / behavior |
|---|---|
| General explanation *(A)* | No new task or unrelated board loading |
| Ambiguous task | Index titles allowed; offer matching tasks/new ID/discussion-only |
| Explicit task A | A state and relevant plan; no B detail marker |
| Stage transition | Current stage; previous evidence only when relevant, not all stages |
| Planner → Executor | Plan usable without Planner's private conversation; next owner correct |
| Optional review | Selected evidence only; independent review labeled honestly |
| Resume/compaction | Retain or reconfirm task; no switch to last-updated task |
| Explicit task switch | New binding; inherited history distinguished from newly read files |
| Parallel A/B | Separate states/write scopes, shared conflicts handled without stealing |
| Task cleanup | Candidate registry + shared protections; no unrelated deletion |
| Project cleanup | Explicit broader scope; includes closed-task retained evidence |
| Missing/legacy setup | Report and request setup/migration; no silent reset |
| Nested/subagent operation | Check inherited context/task scope using documented harness behavior |

Capture observable assembled requests via a mock transport or official diagnostics
where supported, with secrets redacted. Otherwise report visibility limits and use
read traces/usage data; do not invent hidden prompt sizes. Measure separately:

1. Always-loaded instruction/skill-metadata delta from the baseline.
2. Task/stage/tool-result context acquired on demand and carried into later requests.
3. Unrelated detail-marker leakage (task titles in the index are allowed).
4. Task/role selection errors, unnecessary clarification and unsafe action attempts.
5. Resume/compaction and handoff correctness, plus human readability of the snapshot.

The <=110 whitespace-word router check (and per-asset word caps) are static size budgets,
not token claims.
Do not confuse prompt caching discounts with removing unrelated context. Include
both first-request and continuing-session measurements; tool reads can persist.

## Harness/model matrix and rollout

Start with Pi's and Antigravity's documented versions using disposable fixture projects.
No live reload or migration is required to develop sources. Interactive discovery,
Antigravity request-assembly capture and actual model behavior must be checked separately
before claiming them verified.

Choose other harnesses according to actual use. Before adding an adapter, read its
official instruction discovery/precedence, skills, prompt templates, session, subagent
and reload documentation. Shared Markdown syntax is not proof of equal loading behavior.
Run the same scenarios across selected models/agent configurations and repeat stochastic
cases, recording failures rather than requiring one lucky run. Do not automatically
spend API credits, grant project trust, run cleanup or publish session traces.

Store the experiment's readable report in its own `.coworkers/tasks/<task_id>/README.md`
and transient captures under its namespaced scratch. Record unmeasured cells explicitly.
Only migrate a live installation after validation and an agreed paused-writer window.
