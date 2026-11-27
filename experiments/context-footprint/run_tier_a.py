#!/usr/bin/env python3
"""Tier A: mechanical context-footprint measurement against the real Pi harness.

Runs the documented scenarios with a scripted OpenAI-compatible mock provider,
so no API credit is spent and no real model judges anything. Each run uses a
disposable agent directory (PI_CODING_AGENT_DIR) and a disposable fixture
workspace; user-level configuration is never touched.

Usage:
    python run_tier_a.py [--pi /path/to/pi] [--out DIR] [--scenario ID] [--keep]

Outputs report.md and results.json under --out (default: a new temp directory,
printed on completion). Tier A passing means: the harness assembles the
expected minimal context and the always-loaded overhead stays within budget.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parent))
from fixtures import MARKERS, build_fixture  # noqa: E402
from mock_provider import serve  # noqa: E402
from scenarios import baseline_scenario, build_scenarios  # noqa: E402
from grade import grade_scenario, summarize  # noqa: E402

ROUTER_BUDGET_WORDS = 160
OVERHEAD_BUDGET_WORDS = 260  # router + skill descriptions + harness boilerplate delta

SKILL_SOURCE = Path(__file__).resolve().parents[2] / "toolkit/general/skills/local-tests-cleaner"
ROUTER_SOURCE = Path(__file__).resolve().parents[2] / "toolkit/general/system-prompts/project.md"


def build_agent_dir(base: Path, label: str, port: int) -> Path:
    agent = base / f"agent-{label}-{port}"
    (agent / "skills").mkdir(parents=True)
    (agent / "models.json").write_text(json.dumps({
        "$schema": "https://pi.dev/schemas/models.schema.json",
        "providers": {"mock": {"baseUrl": f"http://127.0.0.1:{port}/v1", "api": "openai-completions",
                                "apiKey": "mock-key", "models": [{"id": "mock-1",
                                                                   "contextWindow": 128000,
                                                                   "maxTokens": 8192}]}},
    }, indent=2))
    (agent / "settings.json").write_text(json.dumps({
        "defaultProvider": "mock", "defaultModel": "mock-1", "compaction": {"enabled": False},
    }))
    return agent


def install_workspace_assets(workspace: Path) -> None:
    router = ROUTER_SOURCE.read_text()
    (workspace / "AGENTS.md").write_text(
        f"<!-- blueberry:router:start -->\n{router}<!-- blueberry:router:end -->\n"
    )
    shutil.copytree(SKILL_SOURCE, workspace / ".agents/skills/local-tests-cleaner")


def run_scenario(pi, workspace, base, scenario, out_dir):
    script_path = out_dir / f"{scenario['id']}.script.json"
    script_path.write_text(json.dumps(scenario["turns"]))
    log_path = out_dir / f"{scenario['id']}.requests.jsonl"
    server, port = serve(str(script_path), str(log_path))
    try:
        agent_dir = build_agent_dir(base, "blueberry", port)
        env = dict(os.environ)
        env["PI_CODING_AGENT_DIR"] = str(agent_dir)
        env.pop("PI_CODING_AGENT_SESSION_DIR", None)
        # The mock provider is loopback-only; never tunnel it through an ambient proxy.
        for key in ("NO_PROXY", "no_proxy"):
            env[key] = "127.0.0.1,localhost"
        process = subprocess.run(
            [pi, "--approve", "--no-session", "--provider", "mock", "--model", "mock-1",
             "-p", scenario["user"]],
            cwd=workspace, env=env, capture_output=True, text=True, timeout=120)
    finally:
        server.shutdown()
        server.server_close()
    if process.returncode != 0:
        return {"id": scenario["id"], "requests": 0, "passed": False,
                "failures": [f"pi exited {process.returncode}: {process.stderr.strip()[:400]}"]}
    result = grade_scenario(scenario, log_path)
    result["pi_stdout"] = process.stdout.strip()[:200]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pi", default=shutil.which("pi") or "pi")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--scenario", default=None, help="run one scenario id only")
    parser.add_argument("--keep", action="store_true", help="keep temp fixture/agent dirs")
    args = parser.parse_args()

    out_dir = args.out or Path(tempfile.mkdtemp(prefix="footprint-tier-a-"))
    out_dir.mkdir(parents=True, exist_ok=True)
    base = Path(tempfile.mkdtemp(prefix="footprint-work-"))
    results = []

    try:
        configurations = (("baseline", False), ("blueberry", True))
        captures = {}
        for name, install_assets in configurations:
            workspace = base / f"workspace-{name}"
            workspace.mkdir()
            (workspace / ".git").mkdir()
            paths = build_fixture(workspace, install=install_assets)
            if install_assets:
                install_workspace_assets(workspace)
            script_path = out_dir / f"{name}-boot.json"
            script_path.write_text(json.dumps([{"content": "Fixture explanation."}]))
            # Boot run only captures the assembled system prompt (single scripted reply).
            log_path = out_dir / f"{name}-boot.requests.jsonl"
            server, port = serve(str(script_path), str(log_path))
            try:
                agent_dir = build_agent_dir(base, name, port)
                env = dict(os.environ)
                env["PI_CODING_AGENT_DIR"] = str(agent_dir)
                env.pop("PI_CODING_AGENT_SESSION_DIR", None)
                for key in ("NO_PROXY", "no_proxy"):
                    env[key] = "127.0.0.1,localhost"
                prompt = ("Explain in one sentence what the VALUE constant in pkg/beta.py is for. "
                          "Do not read any files.")
                if name == "blueberry":
                    prompt = "Task: alpha_probe. " + prompt
                process = subprocess.run(
                    [args.pi, "--approve", "--no-session", "--provider", "mock",
                     "--model", "mock-1", "-p", prompt],
                    cwd=workspace, env=env, capture_output=True, text=True, timeout=120)
            finally:
                server.shutdown()
                server.server_close()
            if process.returncode != 0:
                print(f"boot run failed for {name}: {process.stderr[:400]}", file=sys.stderr)
                return 2
            captures[name] = {"agent_dir": agent_dir, "log": log_path}

        # Measure always-loaded overhead from the two boot logs.
        from grade import load_log, system_prompt
        baseline_words = len(system_prompt(load_log(captures["baseline"]["log"])[0]).split())
        blueberry_words = len(system_prompt(load_log(captures["blueberry"]["log"])[0]).split())
        overhead = blueberry_words - baseline_words
        boot_result = {"id": "router_overhead", "requests": 1,
                       "baseline_system_words": baseline_words,
                       "blueberry_system_words": blueberry_words,
                       "overhead_words": overhead, "passed": overhead <= OVERHEAD_BUDGET_WORDS,
                       "failures": [] if overhead <= OVERHEAD_BUDGET_WORDS
                       else [f"overhead {overhead} words exceeds budget {OVERHEAD_BUDGET_WORDS}"]}
        router = ROUTER_SOURCE.read_text()
        if len(router.split()) > ROUTER_BUDGET_WORDS:
            boot_result["failures"].append(f"router exceeds {ROUTER_BUDGET_WORDS} words")
        boot_result["passed"] = not boot_result["failures"]
        results.append(boot_result)

        workspace = base / "workspace-blueberry2"
        workspace.mkdir()
        (workspace / ".git").mkdir()
        paths = build_fixture(workspace, install=True)
        install_workspace_assets(workspace)
        for scenario in build_scenarios(paths):
            if args.scenario and scenario["id"] != args.scenario:
                continue
            results.append(run_scenario(args.pi, workspace, base, scenario, out_dir))

        print(summarize(results, overhead))
        (out_dir / "results.json").write_text(json.dumps(results, indent=2))
        (out_dir / "report.md").write_text(summarize(results, overhead))
        failed = [r["id"] for r in results if not r["passed"]]
        print(f"Results dir: {out_dir}" + (f" (kept: {base})" if args.keep else ""))
        if failed:
            print("FAILED scenarios:", ", ".join(failed), file=sys.stderr)
            return 1
        return 0
    finally:
        if not args.keep:
            shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
