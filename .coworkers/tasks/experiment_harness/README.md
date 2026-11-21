# Experiment harness and aggressive cleanup — implementation record

Task ID: `experiment_harness` · Outcome: Tier A context-footprint harness runnable and
stable (5/5 pass, repeated); aggressive-cleanup decision applied; Tier B pending authorization.
Follows `parallel_task_workflow` (same day, 2026-11-20); supersedes its fingerprint.
Planner/Executor self-check, not independent review.

## User decisions applied

1. **Aggressive cleanup ADOPTED.** Cleaner skill, scratch policy, workflow §7 and the task
   template now auto-delete and report the low-risk classes inside the selected task's
   scratch scope: unregistered one-off probes, this task's unregistered unsummarized
   failed/empty run dirs, empty directories, and superseded raw outputs whose conclusions
   are already captured. Approval gates unchanged for registered retirement, accepted
   evidence/shared baselines, cross-task consumers, >10 GB/unknown size and out-of-scope
   paths. Retention limits never trigger deletion.
2. Reconcile-at-boundaries (not literal every-request rewrites): confirmed unchanged.
3. Single `State` + `Next` fields (no waiting/blocked booleans): confirmed unchanged.

## Built: context-footprint experiment harness

`experiments/context-footprint/` — fixtures.py, mock_provider.py, scenarios.py, grade.py,
run_tier_a.py, README.md. Tier A runs the real `pi` binary against a scripted
OpenAI-compatible mock provider on loopback (`NO_PROXY` exemption for ambient proxies),
with disposable `PI_CODING_AGENT_DIR` agent dirs and fixture workspaces; user-level
configuration is untouched; no API spend. The grader inspects captured request bodies for
expected/forbidden `FX_*_M1` markers, so assembly claims cannot be faked.

## Validation and reproduction

```bash
cd experiments/context-footprint && python run_tier_a.py --keep
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v   # 43 pass
```

| Check | Result | Notes |
|---|---|---|
| router_overhead | PASS | Always-loaded system-prompt delta **150 words** vs baseline (budget ≤260; words, not provider tokens) |
| general_no_task | PASS | No board/log/workflow/shared content enters on a general question |
| task_isolation_alpha | PASS | Sibling task, other stages, record and all logs stay out of every payload |
| evidence_scoping | PASS | Only the selected run's log enters; sibling logs/stages/records stay out |
| shared_and_record | PASS | Shared protections + durable record enter; all task boards and logs stay out |
| Stability | PASS ×3 full runs | Identical results; each scenario 1–3 requests, system 439 words |

Intermediate failures fixed while stabilizing: proxy tunneling to loopback (503),
stale-port reuse across scenarios, agent-directory collision, and one wrong expectation
(`general_no_task` originally expected an unread file's marker). All fixture workspaces,
agent dirs and mock servers are removed by the runner unless `--keep`.

## Source identity

- Sources (24-file recipe from `parallel_task_workflow`, now including tests/README changes):
  `8e02b24a336a21d0cd8700db1a4cabf76172e316b7dd38935401ac13c709c88f`
- Experiments directory (6 py/md files, bytecode excluded): `459dc2df20fa2444225ff9c70b083b5b34a40d602a8b8cf839194e4e2331afe7`
- Base: uncommitted work on top of user commit `3a0e713` plus this session's review fixes.

## Limits and next steps

- Tier A verifies **assembly only**; it cannot show that a real model chooses the right
  file or asks instead of guessing. Tier B (real provider, response capture, behavioral
  graders, repeats) is designed in `experiments/context-footprint/README.md` and requires
  explicit user authorization to spend API credit. Do not run it as a side effect.
- Other harness adapters need verified injection/provider paths before results compare.
- Tecoomni live migration remains deferred behind a paused-writer window; the running
  benchmark was not touched.
