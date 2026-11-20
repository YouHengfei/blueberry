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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="canonical coordination root, not an independent worktree copy")
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
    args = parser.parse_args(argv)
    try:
        store = Store(args.root, args.timeout)
        if args.command == "snapshot":
            result = store.snapshot(args.target)
        elif args.command == "update":
            content = sys.stdin.buffer.read(MAX_BYTES + 1)
            if len(content) > MAX_BYTES:
                raise CoordinationError("board exceeds 2 MiB limit")
            result = store.update(args.target, args.expected, content.decode("utf-8"))
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
