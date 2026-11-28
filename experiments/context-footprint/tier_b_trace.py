"""Normalize headless JSONL event streams from Pi, Antigravity, Claude Code, and Codex."""

import json
from pathlib import Path
import re

READ_TOOLS = {"read", "read_file", "view_file", "view_file_outline", "view_code_item"}
WRITE_TOOLS = {
    "write", "edit", "write_file", "write_to_file", "edit_file",
    "replace_file_content", "multi_replace_file_content", "multiedit",
}
SHELL_TOOLS = {"bash", "run_command", "command_execution"}


def normalize_path(raw_path, workspace_root):
    """Convert an absolute or workspace-relative path to a clean repo-relative POSIX path."""
    if not raw_path or not isinstance(raw_path, str):
        return ""
    cleaned = raw_path.strip().strip("'\"")
    if not cleaned:
        return ""
    root = Path(workspace_root).resolve() if workspace_root else None
    candidate = Path(cleaned)
    if root is not None:
        if candidate.is_absolute():
            try:
                return candidate.resolve().relative_to(root).as_posix()
            except ValueError:
                return candidate.as_posix()
        return candidate.as_posix().lstrip("./")
    return candidate.as_posix().lstrip("./")


def _extract_path_arg(args):
    if not isinstance(args, dict):
        return ""
    for key in ("path", "Path", "file_path", "TargetFile", "AbsolutePath", "file"):
        val = args.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""


def _extract_cmd_arg(args):
    if not isinstance(args, dict):
        return ""
    for key in ("command", "CommandLine", "cmd"):
        val = args.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""


def _record_tool(trace, name, args, workspace_root):
    low = (name or "").lower()
    path = normalize_path(_extract_path_arg(args), workspace_root)
    cmd = _extract_cmd_arg(args)
    if low in READ_TOOLS:
        kind = "read"
        if path and path not in trace["files_read"]:
            trace["files_read"].append(path)
    elif low in WRITE_TOOLS:
        kind = "write"
        if path and path not in trace["files_written"]:
            trace["files_written"].append(path)
    elif low in SHELL_TOOLS:
        kind = "shell"
        if cmd:
            trace["commands_run"].append(cmd)
    else:
        kind = "other"
    trace["tool_calls"].append({"name": name, "kind": kind, "path": path, "command": cmd})


def _extract_text_blocks(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "".join(parts)
    return ""


def _iter_jsonl(text):
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or not stripped.startswith("{"):
            continue
        try:
            yield json.loads(stripped)
        except json.JSONDecodeError:
            continue


def _empty_trace(harness):
    return {
        "harness": harness,
        "files_read": [],
        "files_written": [],
        "commands_run": [],
        "tool_calls": [],
        "reply": "",
        "usage": {},
        "raw_events": 0,
    }


def parse_pi_jsonl(text, workspace_root=None):
    trace = _empty_trace("pi")
    replies = []
    for ev in _iter_jsonl(text):
        trace["raw_events"] += 1
        etype = ev.get("type")
        if etype == "tool_execution_start":
            _record_tool(trace, ev.get("toolName", ""), ev.get("args", {}), workspace_root)
        elif etype == "message_end":
            msg = ev.get("message") or {}
            if msg.get("role") == "assistant":
                txt = _extract_text_blocks(msg.get("content"))
                if txt.strip():
                    replies.append(txt.strip())
                if isinstance(msg.get("usage"), dict):
                    trace["usage"] = msg["usage"]
        elif etype == "message_update" and isinstance(ev.get("usage"), dict):
            trace["usage"] = ev["usage"]
    trace["reply"] = "\n".join(replies)
    return trace


def parse_agy_jsonl(text, workspace_root=None):
    trace = _empty_trace("agy")
    deltas = []
    seen_steps = set()
    for ev in _iter_jsonl(text):
        trace["raw_events"] += 1
        etype = ev.get("event")
        if etype == "step_update":
            su = ev.get("step_update") or {}
            stype = su.get("step_type")
            idx = su.get("step_index")
            if stype == "tool" and su.get("state") == "DONE" and idx not in seen_steps:
                seen_steps.add(idx)
                info = su.get("tool_info") or {}
                tname = info.get("name") or su.get("tool_name") or ""
                params = info.get("parameters") or {}
                _record_tool(trace, tname, params, workspace_root)
            elif stype == "agent_response" and isinstance(su.get("text_delta"), str):
                deltas.append(su["text_delta"])
        elif etype == "result":
            res = ev.get("result") or {}
            if isinstance(res.get("response"), str):
                trace["reply"] = res["response"].strip()
            if isinstance(res.get("usage"), dict):
                trace["usage"] = res["usage"]
    if not trace["reply"] and deltas:
        trace["reply"] = "".join(deltas).strip()
    return trace


def parse_claude_jsonl(text, workspace_root=None):
    trace = _empty_trace("claude")
    replies = []
    for ev in _iter_jsonl(text):
        trace["raw_events"] += 1
        etype = ev.get("type")
        if etype == "assistant":
            msg = ev.get("message") or {}
            content = msg.get("content")
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    btype = block.get("type")
                    if btype == "tool_use":
                        _record_tool(trace, block.get("name", ""), block.get("input", {}), workspace_root)
                    elif btype == "text" and block.get("text", "").strip():
                        replies.append(block["text"].strip())
        elif etype == "result":
            if isinstance(ev.get("result"), str) and ev["result"].strip():
                trace["reply"] = ev["result"].strip()
            if isinstance(ev.get("usage"), dict):
                trace["usage"] = ev["usage"]
    if not trace["reply"] and replies:
        trace["reply"] = "\n".join(replies)
    return trace


def parse_codex_jsonl(text, workspace_root=None):
    trace = _empty_trace("codex")
    replies = []
    for ev in _iter_jsonl(text):
        trace["raw_events"] += 1
        etype = ev.get("type")
        if etype == "item.completed":
            item = ev.get("item") or {}
            itype = item.get("type")
            if itype == "command_execution":
                _record_tool(trace, "command_execution", {"command": item.get("command", "")}, workspace_root)
            elif itype == "file_change":
                for change in item.get("changes") or []:
                    if isinstance(change, dict) and change.get("path"):
                        _record_tool(trace, "write_file", {"path": change["path"]}, workspace_root)
            elif itype == "agent_message" and isinstance(item.get("text"), str):
                replies.append(item["text"].strip())
        elif etype == "turn.completed" and isinstance(ev.get("usage"), dict):
            trace["usage"] = ev["usage"]
    trace["reply"] = "\n".join(r for r in replies if r)
    return trace


def parse_trace(harness, text, workspace_root=None):
    key = "pi" if harness == "pi-mock" else harness
    parsers = {
        "pi": parse_pi_jsonl,
        "agy": parse_agy_jsonl,
        "claude": parse_claude_jsonl,
        "codex": parse_codex_jsonl,
    }
    if key not in parsers:
        raise ValueError(f"unsupported harness for trace parsing: {harness}")
    return parsers[key](text, workspace_root)


def shell_mentions_path(commands, rel_path):
    """True when any executed shell command references rel_path (e.g., via cat/sed/head)."""
    needle = re.escape(rel_path)
    return any(re.search(rf"(?:^|[\s'\"/]){needle}(?:$|[\s'\"])", cmd) for cmd in commands)
