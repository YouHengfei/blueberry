"""Grade captured request logs against scenario expectations.

The grader inspects only the mock provider's JSONL request log (the exact
assembled model payloads). It never calls a real provider and spends nothing.
"""

import json
from pathlib import Path


def system_prompt(entry):
    for message in entry["body"].get("messages", []):
        if message.get("role") == "system":
            content = message.get("content")
            if isinstance(content, list):
                return "".join(part.get("text", "") for part in content)
            return content or ""
    return ""


def payload_text(entry):
    parts = []
    for message in entry["body"].get("messages", []):
        content = message.get("content")
        if isinstance(content, list):
            parts.append("".join(p.get("text", "") for p in content if isinstance(p, dict)))
        elif isinstance(content, str):
            parts.append(content)
        for call in message.get("tool_calls") or []:
            parts.append(json.dumps(call))
    return "\n".join(parts)


def load_log(log_path):
    return [json.loads(line) for line in Path(log_path).read_text().splitlines() if line.strip()]


def grade_scenario(scenario, log_path):
    entries = load_log(log_path)
    result = {"id": scenario["id"], "requests": len(entries), "failures": []}
    if not entries:
        result["failures"].append("no requests captured")
        return result
    system = system_prompt(entries[0])
    result["system_words"] = len(system.split())
    for phrase in scenario.get("system_must_contain", []):
        if phrase not in system:
            result["failures"].append(f"system prompt missing expected phrase: {phrase!r}")
    for phrase in scenario.get("system_must_forbid", []):
        if phrase in system:
            result["failures"].append(f"system prompt contains forbidden phrase: {phrase!r}")
    combined = "\n".join(payload_text(entry) for entry in entries)
    for marker in scenario["allowed"]:
        if marker not in combined:
            result["failures"].append(f"expected marker never entered context: {marker}")
    for marker in scenario["forbidden"]:
        if marker in combined:
            result["failures"].append(f"forbidden marker entered context: {marker}")
    if "turns" in scenario:
        expected_tool_requests = sum(1 for turn in scenario["turns"] if "tool_calls" in turn)
        if entries[-1]["body"].get("stream") is None:
            result["failures"].append("unexpected non-streaming request shape")
        if expected_tool_requests and len(entries) < expected_tool_requests + 1:
            result["failures"].append("fewer requests than the scripted tool sequence")
    result["passed"] = not result["failures"]
    return result


def summarize(results, overhead_words):
    lines = ["# Context-footprint Tier A report", "",
             "Scripted-model assembly check: verifies which fixture markers entered the",
             "assembled payloads, and the always-loaded system-prompt delta. It does NOT",
             "measure model judgment (that is Tier B).", "",
             "| Scenario | Requests | System words | Passed |", "|---|---|---|---|"]
    for result in results:
        lines.append(f"| {result['id']} | {result['requests']} | {result.get('system_words', '—')} "
                     f"| {'PASS' if result['passed'] else 'FAIL'} |")
    lines += ["", f"Always-loaded system-prompt overhead: **{overhead_words} words** vs baseline.",
              "", "## Failures"]
    failures = [f for r in results for f in r["failures"]]
    lines += [f"- {failure}" for failure in failures] or ["- none"]
    return "\n".join(lines) + "\n"
