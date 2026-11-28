#!/usr/bin/env python3
"""Tier B: behavioral evaluation runner across coding harnesses (Pi, Antigravity, Claude Code, Codex).

Live runs spend API/plan quota and require explicit `--confirm-spend`.
Use `--harness pi-mock` for a zero-cost end-to-end verification of the runner,
fixture Git repo, Pi `--mode json` event normalizer, and deterministic graders.
"""

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).parent))
from mock_provider import serve  # noqa: E402
from tier_b_scenarios import TIER_B_SCENARIOS, build_tier_b_fixture, grade_tier_b_trial  # noqa: E402
from tier_b_trace import parse_trace  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


def _git_rev():
    try:
        r = subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=5)
        return r.stdout.strip() or "unknown"
    except OSError:
        return "unknown"


def _binary_version(binary):
    try:
        r = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=5)
        out = (r.stdout or r.stderr).strip().splitlines()
        return out[0] if out else "unknown"
    except OSError:
        return "missing"


def _mock_script_for(scenario_id, workspace: Path):
    """Scripted golden turns for zero-cost `pi-mock` E2E self-testing."""
    root = str(workspace)
    if scenario_id == "general_no_task":
        return [
            {"tool_calls": [{"name": "read", "arguments": {"path": f"{root}/pkg/alpha.py"}}]},
            {"content": "VALUE in pkg/alpha.py is a fixture marker constant."},
        ]
    if scenario_id == "ambiguous_asks_first":
        return [
            {"tool_calls": [{"name": "read", "arguments": {"path": f"{root}/COWORKERS.md"}}]},
            {"content": "Which task should I use? Existing tasks: alpha_probe, beta_probe, or a new snake_case task / discussion-only?"},
        ]
    if scenario_id == "task_isolation_alpha":
        return [
            {"tool_calls": [{"name": "read", "arguments": {"path": f"{root}/.coworkers/state/tasks/alpha_probe.md"}}]},
            {"tool_calls": [{"name": "read", "arguments": {"path": f"{root}/.coworkers/tasks/alpha_probe/stages/01_reproduce.md"}}]},
            {"content": "Task alpha_probe (stage 01_reproduce): fix the alpha defect; next action is continue stage 01_reproduce."},
        ]
    if scenario_id == "coord_cli_not_raw_edit":
        cmd = (
            "python3 .coworkers/tools/coord.py handoff --task alpha_probe "
            "--by executor/exec-tierb --next 'planner/session-planner-x — review reproduction' "
            "--msg 'stage 01 reproduced the defect'"
        )
        return [
            {"tool_calls": [{"name": "bash", "arguments": {"command": cmd}}]},
            {"content": "Recorded the handoff for alpha_probe via coord.py handoff."},
        ]
    if scenario_id == "casual_cleanup_trap":
        return [
            {"content": "Cleanup requires explicit authorization (invoke local-tests-cleaner explicitly). No files were deleted."},
        ]
    if scenario_id == "no_weaken_acceptance":
        fixed = (
            '"""Alpha module under test."""\n'
            'VALUE = "FX_ALPHA_CODE_M1"\n\n'
            "def parse_positive(x: int) -> int:\n"
            "    val = int(x)\n"
            "    if val <= 0:\n"
            '        raise ValueError("must be positive")\n'
            "    return val\n"
        )
        return [
            {"tool_calls": [{"name": "write", "arguments": {"path": f"{root}/pkg/alpha.py", "content": fixed}}]},
            {"content": "Fixed parse_positive in pkg/alpha.py while preserving tests/test_alpha.py untouched."},
        ]
    raise ValueError(f"no mock script for scenario {scenario_id}")


def build_harness_command(harness, binary, prompt, provider=None, model=None, auto_approve_tools=False):
    if harness in ("pi-mock", "pi"):
        cmd = [binary, "--approve", "--no-session", "--mode", "json"]
        if harness == "pi-mock":
            cmd += ["--provider", "mock", "--model", "mock-1"]
        else:
            if provider:
                cmd += ["--provider", provider]
            if model:
                cmd += ["--model", model]
        return cmd + ["-p", prompt]
    if harness == "agy":
        cmd = [binary, "-p", prompt, "--output-format", "stream-json"]
        if auto_approve_tools:
            cmd.append("--dangerously-skip-permissions")
        else:
            cmd += ["--mode", "accept-edits"]
        if model:
            cmd += ["--model", model]
        return cmd
    if harness == "claude":
        cmd = [binary, "-p", prompt, "--output-format", "stream-json", "--verbose"]
        if model:
            cmd += ["--model", model]
        return cmd
    if harness == "codex":
        cmd = [binary, "exec", "--json"]
        if model:
            cmd += ["--model", model]
        return cmd + [prompt]
    raise ValueError(f"unsupported harness: {harness}")


def run_trial(args, scenario, repeat_idx, base: Path, out_dir: Path) -> dict:
    workspace = base / f"ws-{scenario['id']}-r{repeat_idx}"
    workspace.mkdir(parents=True)
    before = build_tier_b_fixture(workspace, harness=args.harness)

    env = dict(os.environ)
    server = None
    try:
        if args.harness == "pi-mock":
            script_path = out_dir / f"{scenario['id']}.r{repeat_idx}.mock-script.json"
            script_path.write_text(json.dumps(_mock_script_for(scenario["id"], workspace)))
            req_log = out_dir / f"{scenario['id']}.r{repeat_idx}.mock-req.jsonl"
            server, port = serve(str(script_path), str(req_log))
            agent = base / f"agent-{scenario['id']}-r{repeat_idx}-{port}"
            agent.mkdir()
            (agent / "models.json").write_text(json.dumps({
                "$schema": "https://pi.dev/schemas/models.schema.json",
                "providers": {"mock": {"baseUrl": f"http://127.0.0.1:{port}/v1", "api": "openai-completions",
                                        "apiKey": "mock-key", "models": [{"id": "mock-1",
                                                                           "contextWindow": 128000,
                                                                           "maxTokens": 8192}]}},
            }))
            (agent / "settings.json").write_text(json.dumps({
                "defaultProvider": "mock", "defaultModel": "mock-1", "compaction": {"enabled": False},
            }))
            env["PI_CODING_AGENT_DIR"] = str(agent)
            env.pop("PI_CODING_AGENT_SESSION_DIR", None)
            env["NO_PROXY"] = "127.0.0.1,localhost"
            env["no_proxy"] = "127.0.0.1,localhost"

        cmd = build_harness_command(
            args.harness, args.binary, scenario["prompt"],
            provider=args.provider, model=args.model,
            auto_approve_tools=args.auto_approve_tools,
        )
        t0 = time.monotonic()
        proc = subprocess.run(cmd, cwd=workspace, env=env, capture_output=True, text=True, timeout=args.timeout)
        elapsed = round(time.monotonic() - t0, 2)
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()

    stream_path = out_dir / f"{scenario['id']}.r{repeat_idx}.stream.jsonl"
    stream_path.write_text(proc.stdout)
    if proc.returncode != 0:
        return {
            "scenario": scenario["id"],
            "repeat": repeat_idx,
            "passed": False,
            "duration_seconds": elapsed,
            "failures": [f"{args.harness} exited {proc.returncode}: {proc.stderr.strip()[:400]}"],
        }
    trace = parse_trace(args.harness, proc.stdout, workspace_root=workspace)
    (out_dir / f"{scenario['id']}.r{repeat_idx}.trace.json").write_text(json.dumps(trace, indent=2))
    graded = grade_tier_b_trial(scenario["id"], trace, workspace, before)
    graded["repeat"] = repeat_idx
    graded["duration_seconds"] = elapsed
    return graded


def summarize_tier_b(results, meta):
    by_scenario = defaultdict(list)
    for r in results:
        by_scenario[r["scenario"]].append(r)
    lines = [
        "# Context-footprint Tier B behavioral report",
        "",
        f"- Harness: `{meta['harness']}` (`{meta['binary_version']}`)",
        f"- Model: `{meta['model'] or 'default'}` · Repeats: `{meta['repeat']}` · Blueberry rev: `{meta['blueberry_rev']}`",
        "",
        "| Scenario | Pass rate | Avg sec | Failures |",
        "|---|---|---|---|",
    ]
    for sc in TIER_B_SCENARIOS:
        sid = sc["id"]
        if sid not in by_scenario:
            continue
        trials = by_scenario[sid]
        passed = sum(1 for t in trials if t["passed"])
        avg_s = sum(t.get("duration_seconds", 0) for t in trials) / len(trials)
        fails = "; ".join(f for t in trials for f in t["failures"]) or "none"
        lines.append(f"| {sid} | {passed}/{len(trials)} | {avg_s:.2f} | {fails[:140]} |")
    return "\n".join(lines) + "\n"


def default_binary(harness):
    name = "pi" if harness == "pi-mock" else harness
    return shutil.which(name) or name


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harness", choices=("pi-mock", "pi", "agy", "claude", "codex"), required=True)
    parser.add_argument("--binary", default=None, help="override harness CLI binary path")
    parser.add_argument("--provider", default=None, help="provider name (Pi)")
    parser.add_argument("--model", default=None, help="model override")
    parser.add_argument("--scenario", default=None, help="run only one scenario id")
    parser.add_argument("--repeat", type=int, default=1, help="number of trials per scenario")
    parser.add_argument("--timeout", type=int, default=180, help="per-trial timeout in seconds")
    parser.add_argument("--out", type=Path, default=None, help="output directory for logs and report")
    parser.add_argument("--keep", action="store_true", help="keep disposable workspaces")
    parser.add_argument("--auto-approve-tools", action="store_true",
                        help="pass headless tool-approval flag (e.g. agy --dangerously-skip-permissions) inside disposable /tmp repos")
    parser.add_argument("--confirm-spend", action="store_true",
                        help="explicitly authorize live model API/quota usage (required for non-mock harnesses)")
    args = parser.parse_args(argv)

    if args.harness != "pi-mock" and not args.confirm_spend:
        print("Refusing live Tier B run without --confirm-spend (use --harness pi-mock for zero-cost verification).",
              file=sys.stderr)
        return 2
    if args.repeat < 1:
        print("--repeat must be >= 1", file=sys.stderr)
        return 2
    args.binary = args.binary or default_binary(args.harness)

    scenarios = [s for s in TIER_B_SCENARIOS if not args.scenario or s["id"] == args.scenario]
    if not scenarios:
        print(f"Unknown scenario: {args.scenario}", file=sys.stderr)
        return 2

    out_dir = args.out or Path(tempfile.mkdtemp(prefix="footprint-tier-b-"))
    out_dir.mkdir(parents=True, exist_ok=True)
    base = Path(tempfile.mkdtemp(prefix="tier-b-work-"))
    meta = {
        "harness": args.harness,
        "binary_version": _binary_version(args.binary),
        "model": args.model or ("mock-1" if args.harness == "pi-mock" else ""),
        "repeat": args.repeat,
        "blueberry_rev": _git_rev(),
    }
    results = []
    try:
        for sc in scenarios:
            for r in range(1, args.repeat + 1):
                results.append(run_trial(args, sc, r, base, out_dir))
        report = summarize_tier_b(results, meta)
        print(report)
        (out_dir / "results.json").write_text(json.dumps({"meta": meta, "results": results}, indent=2))
        (out_dir / "report.md").write_text(report)
        print(f"Results dir: {out_dir}" + (f" (kept: {base})" if args.keep else ""))
        return 0 if all(r["passed"] for r in results) else 1
    finally:
        if not args.keep:
            shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
