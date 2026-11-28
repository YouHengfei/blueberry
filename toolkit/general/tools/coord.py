#!/usr/bin/env python3
"""Cooperative Markdown coordination on local POSIX filesystems; stdlib only."""

import argparse
from contextlib import contextmanager
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import time
import uuid

try:
    import fcntl
except ImportError:
    fcntl = None

MAX_BYTES = 2 * 1024 * 1024
SHARED = ".coworkers/state/shared.md"
START = "<!-- blueberry:claims:start -->"
END = "<!-- blueberry:claims:end -->"
HEADER = "| Claim | Task | Session | Resources | Since | Job |"
SEPARATOR = "|---|---|---|---|---|---|"
TASK = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*\Z")
SESSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
COMPONENT = re.compile(r"[A-Za-z0-9_.:-]+\Z")
STATES = ("ready", "running", "blocked", "review", "done", "cancelled")


class CoordinationError(Exception):
    def __init__(self, message, code=2):
        super().__init__(message)
        self.code = code


def check_task(value):
    if len(value) > 64 or not TASK.fullmatch(value):
        raise CoordinationError("task must be snake_case, start with a letter, and be <=64 characters")
    return value


def check_session(value):
    if not SESSION.fullmatch(value):
        raise CoordinationError("invalid session identity")
    return value


def cell(value):
    if not value or len(value) > 512 or value != value.strip():
        raise CoordinationError("empty, padded or oversized table cell")
    if "|" in value or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise CoordinationError("table cells cannot contain pipes or control characters")
    return value


def resource(value):
    cell(value)
    parts = value.split("/")
    if len(parts) < 2 or any(p in ("", ".", "..") or not COMPONENT.fullmatch(p) for p in parts):
        raise CoordinationError("resource must be a canonical slash-separated namespace, without dot segments")
    return value


def overlaps(left, right):
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def revision(content):
    return "missing" if content is None else hashlib.sha256(content).hexdigest()


def resolve_root(explicit_root=None, cwd=None):
    """Return explicit canonical root or auto-detect main Git repo root via git-common-dir."""
    if explicit_root is not None:
        return Path(explicit_root)
    base = Path(cwd) if cwd is not None else Path.cwd()
    try:
        proc = subprocess.run(
            ["git", "-C", str(base), "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True, text=True, timeout=5,
        )
    except OSError as exc:
        raise CoordinationError("git unavailable; pass --root explicitly") from exc
    if proc.returncode != 0:
        raise CoordinationError("not inside a Git worktree; pass --root explicitly")
    common = Path(proc.stdout.strip())
    if common.name != ".git":
        raise CoordinationError("cannot infer workspace root from bare Git common dir; pass --root explicitly")
    return common.parent.resolve()


def parse_claims(text):
    if text.count(START) != 1 or text.count(END) != 1:
        raise CoordinationError("shared board needs exactly one claims block; no automatic migration")
    start, end = text.index(START) + len(START), text.index(END)
    if end < start:
        raise CoordinationError("reversed claims markers")
    lines = text[start:end].strip().splitlines()
    if lines[:2] != [HEADER, SEPARATOR]:
        raise CoordinationError("invalid claims table header")
    claims, seen, occupied = [], set(), []
    for line in lines[2:]:
        if not line.startswith("|") or not line.endswith("|"):
            raise CoordinationError("invalid claims row")
        fields = [p.strip() for p in line[1:-1].split("|")]
        if len(fields) != 6:
            raise CoordinationError("claims rows need six cells")
        claim_id, task, session, resources, since, job = map(cell, fields)
        if not re.fullmatch(r"[0-9a-f]{32}", claim_id) or claim_id in seen:
            raise CoordinationError("invalid or duplicate claim ID")
        check_task(task)
        check_session(session)
        try:
            datetime.strptime(since, "%Y-%m-%d %H:%M")
        except ValueError as exc:
            raise CoordinationError("invalid claim timestamp") from exc
        items = [resource(item) for item in resources.split(", ")]
        for item in items:
            if any(overlaps(item, previous) for previous in occupied):
                raise CoordinationError("existing claims contain overlapping resources; resolve with owners")
            occupied.append(item)
        seen.add(claim_id)
        claims.append(dict(zip(("claim", "task", "session", "resources", "since", "job"),
                               (claim_id, task, session, items, since, job))))
    return claims


def render_claims(text, claims):
    rows = [HEADER, SEPARATOR]
    for claim in claims:
        rows.append("| " + " | ".join((claim["claim"], claim["task"], claim["session"],
                                       ", ".join(claim["resources"]), claim["since"], claim["job"])) + " |")
    before, remainder = text.split(START)
    _, after = remainder.split(END)
    return before + START + "\n" + "\n".join(rows) + "\n" + END + after


def _section_bounds(lines, heading):
    start = next((i for i, line in enumerate(lines) if line.strip() == heading), None)
    if start is None:
        raise CoordinationError(f"missing required section: {heading}")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return start, end


def _parse_task_fields(text):
    fields = {}
    for line in text.splitlines():
        if line.startswith("## ") and fields:
            break
        match = re.match(r"^- ([^:]+):\s*(.*)$", line)
        if match:
            fields[match.group(1).strip()] = match.group(2).strip()
    return fields


def _update_section_field(lines, start, end, label, value):
    prefix = f"- {label}:"
    for idx in range(start + 1, end):
        if lines[idx].startswith(prefix):
            if value == "":
                del lines[idx]
                return end - 1
            lines[idx] = f"{prefix} {value}"
            return end
    if value == "":
        return end
    insert_at = end
    while insert_at > start + 1 and not lines[insert_at - 1].strip():
        insert_at -= 1
    lines.insert(insert_at, f"{prefix} {value}")
    return end + 1


def _append_section_line(lines, heading, entry):
    start, end = _section_bounds(lines, heading)
    insert_at = end
    while insert_at > start + 1 and not lines[insert_at - 1].strip():
        insert_at -= 1
    lines.insert(insert_at, entry)
    return lines


def _append_index_row(text, row):
    lines = text.splitlines()
    start, end = _section_bounds(lines, "## Active task index")
    sep = next((i for i in range(start + 1, end) if lines[i].strip().startswith("|---")), None)
    if sep is None:
        raise CoordinationError("missing Active task index table in COWORKERS.md")
    insert_at = sep + 1
    while insert_at < end and lines[insert_at].lstrip().startswith("|"):
        insert_at += 1
    lines.insert(insert_at, row)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _remove_index_row(text, task):
    lines = text.splitlines()
    start, end = _section_bounds(lines, "## Active task index")
    removed = False
    kept = []
    for idx, line in enumerate(lines):
        if start < idx < end and line.lstrip().startswith("|") and f"| {task} |" in line:
            removed = True
            continue
        kept.append(line)
    return "\n".join(kept) + ("\n" if text.endswith("\n") else ""), removed


def _render_task_board(task, goal, planner, workspace):
    return (
        f"# Task: {task}\n\n"
        "## Current state\n\n"
        f"- Goal: {goal}\n"
        "- State: ready\n"
        "- Stage: single_stage\n"
        f"- Planner: {planner}\n"
        "- Executors: (unassigned)\n"
        "- Reviewer: (optional)\n"
        f"- Next: {planner} — define plan and acceptance checks\n"
        f"- Workspace: {workspace}\n"
        f"- Records: .coworkers/tasks/{task}/README.md\n"
        "- Plan: (inline or stage link)\n\n"
        "## Scope and acceptance\n\n"
        "- Write scope & non-goals: (intended scope is not an active claim)\n"
        "- Acceptance: (observable checks, thresholds, exceptions)\n"
        "- Planner-owned acceptance check (before `ready`): (plan/command, expected result, negative cases; WORKFLOW.md §2)\n"
        "- Dependencies: (register cross-task uses in `shared.md`)\n\n"
        "## Open questions\n\n"
        "## Decisions\n\n"
        "## Handoffs\n\n"
        "## Retained artifacts\n\n"
        "| Added | Path | Purpose / reproduction | Consumers / protection | Last used |\n"
        "|---|---|---|---|---|\n\n"
        "## Closure\n\n"
        "- Acceptance / exceptions:\n"
        "- Task README & cleanup disposition:\n"
        "- Owned jobs stopped & claims released:\n"
        "- Publication: local only unless authorized.\n"
    )


def _render_task_record(task, goal):
    return (
        f"# {task}\n\n"
        f"Task ID: `{task}` · Outcome: in progress\n\n"
        "## At a glance\n\n"
        f"{goal}\n\n"
        "## Validation\n\n"
        "| Check | Code / config / environment | Baseline | Result | Acceptance / exception |\n"
        "|---|---|---|---|---|\n\n"
        "## Evidence manifest\n\n"
        "| Artifact / real workspace | Retained or removed | Provenance / checksum | Purpose |\n"
        "|---|---|---|---|---|\n\n"
        "## Closure\n\n"
        "- Acceptance & exceptions:\n"
        "- Keep / promote / delete / defer disposition:\n"
        "- Owned jobs stopped / claims released:\n"
        "- Publication status: local only unless authorized\n"
    )


class Store:
    def __init__(self, root, timeout=2):
        if fcntl is None or not hasattr(os, "O_NOFOLLOW"):
            raise CoordinationError("local POSIX filesystem support is required; unsupported platform")
        self.root = Path(root).expanduser().absolute()
        if self.root != self.root.resolve():
            raise CoordinationError("use the real canonical root, without symlinks or dot segments")
        if not math.isfinite(timeout) or not 0 <= timeout <= 30:
            raise CoordinationError("lock timeout must be between 0 and 30 seconds")
        self.timeout = timeout
        # Do not silently resolve aliases: every writer must use the same real root.
        for path in (*reversed(self.root.parents), self.root):
            if path.is_symlink() or not path.is_dir():
                raise CoordinationError("coordination root and its parents must be real directories")
        self.device = self.root.stat().st_dev

    def target(self, name):
        valid = name in ("COWORKERS.md", SHARED)
        match = re.fullmatch(r"\.coworkers/state/tasks/([^/]+)\.md", name)
        if match:
            check_task(match[1])
            valid = True
        if not valid:
            raise CoordinationError("target must be COWORKERS.md, shared.md or a task state board")
        return self.safe_path(name)

    def safe_path(self, relative, create_parents=False):
        path = self.root
        parts = Path(relative).parts
        if Path(relative).is_absolute() or any(p in (".", "..") for p in parts):
            raise CoordinationError("unsafe relative path")
        for index, part in enumerate(parts):
            path = path / part
            if path.is_symlink():
                raise CoordinationError("symlink destinations and parents are not supported")
            if not path.exists():
                if create_parents and index < len(parts) - 1:
                    path.mkdir(mode=0o700, exist_ok=True)
                else:
                    continue
            info = path.lstat()
            if info.st_dev != self.device:
                raise CoordinationError("coordination paths cannot cross mounts")
            if index < len(parts) - 1 and not stat.S_ISDIR(info.st_mode):
                raise CoordinationError("non-directory parent")
            if index == len(parts) - 1 and (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1):
                raise CoordinationError("target must be a regular, non-hardlinked file")
        return path

    def read(self, name):
        path = self.target(name)
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        except FileNotFoundError:
            return None
        with os.fdopen(fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise CoordinationError("not a regular file")
            content = stream.read(MAX_BYTES + 1)
        if len(content) > MAX_BYTES:
            raise CoordinationError("board exceeds 2 MiB limit")
        content.decode("utf-8")
        return content

    @contextmanager
    def lock(self, name):
        if fcntl is None:
            raise CoordinationError("OS advisory locking requires POSIX; unsupported platform")
        self.target(name)
        key = hashlib.sha256(name.encode()).hexdigest()
        path = self.safe_path(f".coworkers/state/locks/{key}.lock", create_parents=True)
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise CoordinationError("unsafe lock file")
            deadline = time.monotonic() + self.timeout
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise CoordinationError("coordination lock busy; retry later", 4)
                    time.sleep(0.01)
            yield
        finally:
            os.close(fd)  # Closing releases flock; never unlink the persistent lock file.

    def replace(self, name, content):
        self.target(name)
        path = self.safe_path(name, create_parents=True)
        if len(content) > MAX_BYTES:
            raise CoordinationError("board exceeds 2 MiB limit")
        mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
        fd, temporary = tempfile.mkstemp(prefix=".coord-", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                os.fchmod(stream.fileno(), mode)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            self.target(name)
            os.replace(temporary, path)
            directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def snapshot(self, name):
        content = self.read(name)
        if name == SHARED and content is not None:
            parse_claims(content.decode())
        return {"revision": revision(content), "content": None if content is None else content.decode()}

    def update(self, name, expected, content):
        encoded = content.encode("utf-8")
        if len(encoded) > MAX_BYTES:
            raise CoordinationError("board exceeds 2 MiB limit")
        with self.lock(name):
            previous = self.read(name)
            if revision(previous) != expected:
                raise CoordinationError("stale revision; snapshot again and merge, do not retry unchanged", 3)
            if name == SHARED:
                old_claims = [] if previous is None else parse_claims(previous.decode())
                if parse_claims(content) != old_claims:
                    raise CoordinationError("generic update cannot change claims; use claim, annotate or release")
            if previous != encoded:
                self.replace(name, encoded)
        return {"revision": revision(encoded), "changed": previous != encoded}

    def change_claim(self, action, task, session, resources=(), claim_id=None, job="-"):
        check_task(task)
        check_session(session)
        cell(job)
        items = [resource(item) for item in resources]
        if action == "claim":
            if not items:
                raise CoordinationError("at least one resource is required")
            if self.read(f".coworkers/state/tasks/{task}.md") is None:
                raise CoordinationError("task state board missing; obtain task selection/setup approval first")
        with self.lock(SHARED):
            previous = self.read(SHARED)
            if previous is None:
                raise CoordinationError("shared board missing; request setup, do not infer free resources")
            text = previous.decode()
            claims = parse_claims(text)
            if action == "claim":
                occupied = [item for claim in claims for item in claim["resources"]]
                for item in items:
                    if any(overlaps(item, other) for other in occupied):
                        raise CoordinationError(f"conflicting resource: {item}", 3)
                    occupied.append(item)
                claim_id = uuid.uuid4().hex
                claims.append({"claim": claim_id, "task": task, "session": session,
                               "resources": items, "since": datetime.now().strftime("%Y-%m-%d %H:%M"),
                               "job": job})
            else:
                found = next((c for c in claims if c["claim"] == claim_id), None)
                if found is None or found["task"] != task or found["session"] != session:
                    raise CoordinationError("claim not found or ownership mismatch", 3)
                if action == "release":
                    claims.remove(found)
                elif action == "annotate":
                    found["job"] = job
                else:
                    raise CoordinationError("invalid claim operation")
            new_text = render_claims(text, claims)
            parse_claims(new_text)
            self.replace(SHARED, new_text.encode())
        return {"claim": claim_id, "revision": revision(new_text.encode()), "action": action}

    def status(self):
        """Read-only cross-task and claims summary; creates no files or locks."""
        shared = self.read(SHARED)
        claims = parse_claims(shared.decode()) if shared is not None else []
        tasks = []
        tasks_dir = self.root / ".coworkers/state/tasks"
        if tasks_dir.exists() and not tasks_dir.is_symlink() and tasks_dir.is_dir():
            for entry in sorted(tasks_dir.iterdir()):
                if entry.suffix != ".md" or not TASK.fullmatch(entry.stem) or len(entry.stem) > 64:
                    continue
                rel = f".coworkers/state/tasks/{entry.name}"
                raw = self.read(rel)
                if raw is None:
                    continue
                fields = _parse_task_fields(raw.decode())
                tasks.append({
                    "task": entry.stem,
                    "state": fields.get("State", ""),
                    "stage": fields.get("Stage", ""),
                    "next": fields.get("Next", ""),
                    "planner": fields.get("Planner", ""),
                    "executors": fields.get("Executors", ""),
                    "blocked": fields.get("Blocked by / Unblock", ""),
                })
        return {"root": str(self.root), "tasks": tasks, "claims": claims}

    def init_task(self, task, goal, planner="(unassigned)", workspace="(current workspace)", purpose=None):
        """Create task state board, durable README (if absent), and append COWORKERS.md row."""
        check_task(task)
        cell(goal)
        cell(planner)
        cell(workspace)
        summary = cell(purpose if purpose is not None else goal)
        if self.read("COWORKERS.md") is None:
            raise CoordinationError("COWORKERS.md missing; run approved setup first")
        board = f".coworkers/state/tasks/{task}.md"
        result = self.update(board, "missing", _render_task_board(task, goal, planner, workspace))
        record_rel = f".coworkers/tasks/{task}/README.md"
        record_path = self.safe_path(record_rel, create_parents=True)
        record_created = False
        if not record_path.exists():
            fd = os.open(record_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(_render_task_record(task, goal).encode("utf-8"))
                    stream.flush()
                    os.fsync(stream.fileno())
                record_created = True
            except Exception:
                raise
        today = datetime.now().strftime("%Y-%m-%d")
        row = f"| {today} | {task} | {summary} | `{board}` |"
        with self.lock("COWORKERS.md"):
            raw = self.read("COWORKERS.md")
            if raw is None:
                raise CoordinationError("COWORKERS.md missing; run approved setup first")
            text = raw.decode()
            if f"| {task} |" not in text:
                updated = _append_index_row(text, row)
                self.replace("COWORKERS.md", updated.encode("utf-8"))
        return {"task": task, "board": board, "record": record_rel,
                "record_created": record_created, "revision": result["revision"]}

    def record_entry(self, task, kind, actor, message, state=None, next_action=None,
                     stage=None, blocker=None, print_prompt=False):
        """Atomically append a timestamped handoff or decision and optionally update state fields."""
        check_task(task)
        cell(actor)
        cell(message)
        if kind not in ("handoff", "decision"):
            raise CoordinationError("kind must be handoff or decision")
        if state is not None and state not in STATES:
            raise CoordinationError(f"state must be one of: {', '.join(STATES)}")
        if next_action is not None:
            cell(next_action)
        if stage is not None:
            cell(stage)
        if blocker is not None and blocker != "":
            cell(blocker)
        board = f".coworkers/state/tasks/{task}.md"
        heading = "## Handoffs" if kind == "handoff" else "## Decisions"
        entry = f"- {datetime.now().strftime('%Y-%m-%d %H:%M')} {actor} — {message}"
        with self.lock(board):
            previous = self.read(board)
            if previous is None:
                raise CoordinationError("task state board missing; create task first")
            text = previous.decode()
            lines = text.splitlines()
            if any(v is not None for v in (state, next_action, stage, blocker)):
                cs_start, cs_end = _section_bounds(lines, "## Current state")
                if state is not None:
                    cs_end = _update_section_field(lines, cs_start, cs_end, "State", state)
                if stage is not None:
                    cs_end = _update_section_field(lines, cs_start, cs_end, "Stage", stage)
                if next_action is not None:
                    cs_end = _update_section_field(lines, cs_start, cs_end, "Next", next_action)
                if blocker is not None:
                    _update_section_field(lines, cs_start, cs_end, "Blocked by / Unblock", blocker)
            _append_section_line(lines, heading, entry)
            new_text = "\n".join(lines) + "\n"
            encoded = new_text.encode("utf-8")
            self.replace(board, encoded)
            fields = _parse_task_fields(new_text)
        out = {"task": task, "kind": kind, "entry": entry, "revision": revision(encoded),
               "state": fields.get("State", ""), "next": fields.get("Next", "")}
        if print_prompt:
            nxt = fields.get("Next", "continue task")
            out["pickup_prompt"] = (
                f"Work on task {task}: read COWORKERS.md and {board}, "
                f"then pick up Next ({nxt})."
            )
        return out

    def close_task(self, task, actor, verdict, outcome="done", disposition=None, record=None):
        """Close a task atomically after verifying no active claims and durable README exists."""
        check_task(task)
        cell(actor)
        cell(verdict)
        if outcome not in ("done", "cancelled"):
            raise CoordinationError("outcome must be done or cancelled")
        if disposition is not None:
            cell(disposition)
        record_rel = f".coworkers/tasks/{task}/README.md"
        if record is None:
            record_path = self.safe_path(record_rel)
            if not record_path.is_file():
                raise CoordinationError(
                    f"durable task record {record_rel} missing; pass --record <worktree-path> or record outcome first"
                )
        else:
            record_path = Path(record).expanduser().absolute()
            if record_path.is_symlink() or not record_path.is_file() or not record_path.as_posix().endswith(f"/{record_rel}"):
                raise CoordinationError(f"--record must point to an existing regular {record_rel} file")
        with self.lock(SHARED):
            shared = self.read(SHARED)
            if shared is not None:
                active = [c for c in parse_claims(shared.decode()) if c["task"] == task]
                if active:
                    raise CoordinationError(
                        f"task {task} still holds {len(active)} active claim(s); stop jobs and release first", 3
                    )
        board = f".coworkers/state/tasks/{task}.md"
        entry = f"- {datetime.now().strftime('%Y-%m-%d %H:%M')} {actor} — closed ({outcome}): {verdict}"
        with self.lock(board):
            previous = self.read(board)
            if previous is None:
                raise CoordinationError("task state board missing")
            lines = previous.decode().splitlines()
            cs_start, cs_end = _section_bounds(lines, "## Current state")
            cs_end = _update_section_field(lines, cs_start, cs_end, "State", outcome)
            cs_end = _update_section_field(lines, cs_start, cs_end, "Next", f"closed ({outcome})")
            _update_section_field(lines, cs_start, cs_end, "Blocked by / Unblock", "")
            if any(line.strip() == "## Closure" for line in lines):
                cl_start, cl_end = _section_bounds(lines, "## Closure")
                cl_end = _update_section_field(lines, cl_start, cl_end, "Acceptance / exceptions", verdict)
                if disposition is not None:
                    cl_end = _update_section_field(
                        lines, cl_start, cl_end, "Task README & cleanup disposition", disposition
                    )
                _update_section_field(
                    lines, cl_start, cl_end, "Owned jobs stopped & claims released", "verified none active"
                )
            _append_section_line(lines, "## Handoffs", entry)
            encoded = ("\n".join(lines) + "\n").encode("utf-8")
            self.replace(board, encoded)
        index_removed = False
        with self.lock("COWORKERS.md"):
            raw = self.read("COWORKERS.md")
            if raw is not None:
                updated, index_removed = _remove_index_row(raw.decode(), task)
                if index_removed:
                    self.replace("COWORKERS.md", updated.encode("utf-8"))
        return {"task": task, "outcome": outcome, "revision": revision(encoded),
                "index_removed": index_removed, "entry": entry}


def format_status_text(data):
    lines = [f"Root: {data['root']}", "Tasks:"]
    if not data["tasks"]:
        lines.append("  (none)")
    for t in data["tasks"]:
        extra = f" | blocked: {t['blocked']}" if t["blocked"] else ""
        lines.append(f"  - {t['task']} [{t['state'] or '?'}] stage={t['stage'] or '?'} | next: {t['next'] or '?'}{extra}")
    lines.append("Claims:")
    if not data["claims"]:
        lines.append("  (none)")
    for c in data["claims"]:
        lines.append(f"  - {c['claim'][:8]} {c['task']} ({c['session']}): {', '.join(c['resources'])} [{c['job']}]")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None, help="canonical coordination root (defaults to Git common repo root)")
    parser.add_argument("--timeout", type=float, default=2, help="lock timeout in seconds (0..30)")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("snapshot", "update"):
        p = commands.add_parser(command)
        p.add_argument("target")
        if command == "update":
            p.add_argument("--expected", required=True, help="snapshot revision, or 'missing' for approved creation")
    for command in ("claim", "annotate", "release"):
        p = commands.add_parser(command)
        p.add_argument("--task", required=True)
        p.add_argument("--session", required=True)
        if command == "claim":
            p.add_argument("--resource", action="append", required=True)
            p.add_argument("--job", default="-")
        else:
            p.add_argument("--claim", required=True)
            if command == "annotate":
                p.add_argument("--job", required=True)
    p_status = commands.add_parser("status")
    p_status.add_argument("--format", choices=("json", "text"), default="json")
    p_init = commands.add_parser("init-task")
    p_init.add_argument("--task", required=True)
    p_init.add_argument("--goal", required=True)
    p_init.add_argument("--planner", default="(unassigned)")
    p_init.add_argument("--workspace", default="(current workspace)")
    p_init.add_argument("--purpose", default=None)
    for command in ("handoff", "decide"):
        p = commands.add_parser(command)
        p.add_argument("--task", required=True)
        p.add_argument("--by", required=True, help="role/session label, e.g. planner/claude-1")
        p.add_argument("--msg", required=True, help="single-line entry summary")
        p.add_argument("--state", choices=STATES, default=None)
        p.add_argument("--stage", default=None)
        p.add_argument("--next", dest="next_action", default=None)
        p.add_argument("--blocker", default=None, help="set blocker text, or '' to clear")
        if command == "handoff":
            p.add_argument("--print-prompt", action="store_true", help="include 1-line pickup prompt")
    p_close = commands.add_parser("close-task")
    p_close.add_argument("--task", required=True)
    p_close.add_argument("--by", required=True, help="role/session label recording closure")
    p_close.add_argument("--verdict", required=True, help="acceptance verdict or cancellation summary")
    p_close.add_argument("--outcome", choices=("done", "cancelled"), default="done")
    p_close.add_argument("--disposition", default=None, help="keep/promote/delete/defer summary")
    p_close.add_argument("--record", default=None, help="durable README path when living in a linked worktree")
    args = parser.parse_args(argv)
    try:
        store = Store(resolve_root(args.root), args.timeout)
        if args.command == "snapshot":
            result = store.snapshot(args.target)
        elif args.command == "update":
            content = sys.stdin.buffer.read(MAX_BYTES + 1)
            if len(content) > MAX_BYTES:
                raise CoordinationError("board exceeds 2 MiB limit")
            result = store.update(args.target, args.expected, content.decode("utf-8"))
        elif args.command == "status":
            result = store.status()
            if args.format == "text":
                print(format_status_text(result))
                return 0
        elif args.command == "init-task":
            result = store.init_task(args.task, args.goal, args.planner, args.workspace, args.purpose)
        elif args.command == "close-task":
            result = store.close_task(args.task, args.by, args.verdict, args.outcome, args.disposition, args.record)
        elif args.command in ("handoff", "decide"):
            result = store.record_entry(
                args.task, "handoff" if args.command == "handoff" else "decision",
                args.by, args.msg, state=args.state, next_action=args.next_action,
                stage=args.stage, blocker=args.blocker,
                print_prompt=getattr(args, "print_prompt", False),
            )
        else:
            result = store.change_claim(args.command, args.task, args.session,
                                        getattr(args, "resource", ()), getattr(args, "claim", None),
                                        getattr(args, "job", "-"))
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (CoordinationError, OSError, ValueError, RuntimeError) as exc:
        code = exc.code if isinstance(exc, CoordinationError) else 2
        print(json.dumps({"error": str(exc), "exit_code": code}), file=sys.stderr)
        return code


if __name__ == "__main__":
    sys.exit(main())
