# Context-footprint experiment

Measures what blueberry actually puts into model context, in two tiers:

| Tier | Question | Model | Cost | Status |
|---|---|---|---|---|
| **A (mechanical)** | What does the harness *assemble* into each request? | Scripted mock provider | Zero | **Runnable now, all scenarios pass** |
| **B (behavioral)** | Does a real model *choose* the right file / ask / use `coord.py`? | Real provider (`--confirm-spend`) or `pi-mock` dry run | Explicit opt-in | **Runnable now (`run_tier_b.py`); `pi-mock` E2E verified** |

Tier A passing means the harness assembles minimal, correctly scoped payloads and the
always-loaded overhead stays in budget. It says nothing about model judgment.

## Tier A usage

```bash
cd experiments/context-footprint
python3 run_tier_a.py --keep          # runs against `pi` found on PATH
python3 run_tier_a.py --pi /path/to/pi --scenario task_isolation_alpha --out /tmp/out
```

Each run creates disposable fixture workspaces (installing `AGENTS.md` and
`.agents/skills/local-tests-cleaner` for the blueberry configuration, bounded by `.git`
and trusted for that invocation only via `--approve`) and disposable agent directories
(`PI_CODING_AGENT_DIR`); user-level configuration (`~/.pi/agent`) is never touched. The
mock provider is loopback-only and the runner sets `NO_PROXY=127.0.0.1,localhost` so an
ambient HTTP proxy cannot tunnel it. A full run finishes in well under a minute.

Outputs (default: a printed temp directory): `report.md`, `results.json`, one
`<scenario>.requests.jsonl` per scenario (the exact assembled request bodies), plus
scripted-turn files.

## What the scenarios check

| Scenario | Assertion focus |
|---|---|
| `router_overhead` | Always-loaded system-prompt delta vs baseline ≤ 180 words (router itself ≤ 110). |
| `general_no_task` | A general question pulls in no task-board, log, workflow or shared content. |
| `task_isolation_alpha` | Reading Task A state + current stage leaves sibling-task, other-stage, record and log markers out of every payload. |
| `evidence_scoping` | One selected evidence log enters; sibling logs, stages and records stay out. |
| `shared_and_record` | Shared protections + durable record enter; all task boards and logs stay out. |

Markers are fixed strings defined in `fixtures.py` (`FX_*_M1`), embedded once per file,
with benign filler for realistic payload sizes. The grader searches the captured request
bodies for expected/forbidden markers — this is why Tier A cannot lie about assembly.

## Tier B (behavioral, explicit spend opt-in)

`run_tier_b.py` evaluates real model behavior across 6 deterministic scenarios (`general_no_task`,
`ambiguous_asks_first`, `task_isolation_alpha`, `coord_cli_not_raw_edit`, `casual_cleanup_trap`,
and `no_weaken_acceptance`) by parsing headless JSONL event streams (`pi --mode json`,
`agy --output-format stream-json`, `claude --output-format stream-json`, `codex exec --json`)
and grading both normalized tool traces and post-run filesystem state in disposable `/tmp` Git repos.

```bash
# Zero-cost end-to-end verification of the Tier B runner and graders against local `pi`:
python3 experiments/context-footprint/run_tier_b.py --harness pi-mock

# Live behavioral run (requires explicit --confirm-spend; supports --repeat N):
python3 experiments/context-footprint/run_tier_b.py \
  --harness agy --scenario casual_cleanup_trap --repeat 3 --confirm-spend
```

Live runs refuse to execute without `--confirm-spend`. For headless shell actions inside
disposable `/tmp` repos under `agy`, pass `--auto-approve-tools` only when appropriate.
Record the model, harness version, blueberry revision, date, and per-scenario pass rates.

## Other harnesses

The fixture, markers, scenarios and grader are harness-neutral. Only the runner is
Pi-specific (agent-dir injection, CLI flags). A new harness adapter must document its
verified instruction-injection path and provider plumbing before results are comparable;
never assume an equivalent flag exists. Words are not provider tokens: budget checks are
static sizes, while token deltas require provider usage data or request capture.
