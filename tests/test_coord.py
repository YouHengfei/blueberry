"""Isolated, CPU-only tests. All writes are under TemporaryDirectory."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "toolkit/general/tools/coord.py"
SHARED_TEMPLATE = ROOT / "toolkit/general/templates/SHARED.template.md"
spec = importlib.util.spec_from_file_location("coord", HELPER)
coord = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coord)


@unittest.skipUnless(os.name == "posix", "local POSIX locking implementation")
class CoordinationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="blueberry-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.store = coord.Store(self.root)
        self.shared = SHARED_TEMPLATE.read_text()
        self.store.update(coord.SHARED, "missing", self.shared)
        self.board = ".coworkers/state/tasks/task_a.md"
        self.store.update(self.board, "missing", "# Task A\n")
        self.store.update(".coworkers/state/tasks/task_b.md", "missing", "# Task B\n")

    def cli(self, *args, content=None):
        return subprocess.run([sys.executable, str(HELPER), "--root", str(self.root), *args],
                              input=content, text=True, capture_output=True, timeout=10)

    def claim(self, resources=("host/worker_a/device/0",), task="task_a", session="session-a"):
        return self.store.change_claim("claim", task, session, resources, job="test job")

    def claims(self):
        return coord.parse_claims(self.store.snapshot(coord.SHARED)["content"])

    def test_snapshot_missing_is_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            result = coord.Store(root).snapshot("COWORKERS.md")
            self.assertEqual(result, {"revision": "missing", "content": None})
            self.assertEqual(list(root.iterdir()), [])

    def test_create_update_noop_and_preserved_mode(self):
        snap = self.store.snapshot(self.board)
        result = self.store.update(self.board, snap["revision"], "# Updated\n")
        self.assertTrue(result["changed"])
        self.assertEqual(self.store.snapshot(self.board)["content"], "# Updated\n")
        path = self.root / self.board
        path.chmod(0o640)
        before = path.stat().st_ino
        self.assertFalse(self.store.update(self.board, result["revision"], "# Updated\n")["changed"])
        self.assertEqual(path.stat().st_ino, before)
        self.store.update(self.board, result["revision"], "# Second\n")
        self.assertEqual(path.stat().st_mode & 0o777, 0o640)

    def test_stale_update_cannot_overwrite(self):
        snap = self.store.snapshot(self.board)
        self.store.update(self.board, snap["revision"], "# Writer one\n")
        with self.assertRaises(coord.CoordinationError) as ctx:
            self.store.update(self.board, snap["revision"], "# Stale writer\n")
        self.assertEqual(ctx.exception.code, 3)
        self.assertEqual(self.store.snapshot(self.board)["content"], "# Writer one\n")
        with self.assertRaises(coord.CoordinationError):
            self.store.update(self.board, "missing", "# Accidental reset\n")

    def test_partial_resource_set_is_not_claimed(self):
        self.claim()
        before = self.store.read(coord.SHARED)
        with self.assertRaises(coord.CoordinationError):
            self.claim(("host/worker_a/port/tcp/8000", "host/worker_a/device/0/core/1"), "task_b", "session-b")
        self.assertEqual(self.store.read(coord.SHARED), before)
        self.assertEqual(len(self.claims()), 1)

    def test_resource_prefix_boundaries_and_workspace_scopes(self):
        self.claim(("host/worker_a/device/1", "workspace/main/files/src"))
        self.claim(("host/worker_a/device/10", "workspace/other/files/src"), "task_b", "session-b")
        with self.assertRaises(coord.CoordinationError):
            self.claim(("host/worker_a",))
        with self.assertRaises(coord.CoordinationError):
            self.claim(("workspace/main/files/src/module.py",))
        self.assertEqual(len(self.claims()), 2)

    def test_redundant_resources_rejected_atomically(self):
        for resources in (("host/a", "host/a"), ("host/a", "host/a/device/0")):
            with self.subTest(resources=resources), self.assertRaises(coord.CoordinationError):
                self.claim(resources)
        self.assertEqual(self.claims(), [])

    def test_namespace_validation(self):
        for value in ("/host/a", "host//a", "host/a/", "host/../a", "host/./a",
                      "host/a,b", "host/a|b", "host/a\nb", "host/a b", "single"):
            with self.subTest(value=value), self.assertRaises(coord.CoordinationError):
                self.claim((value,))
        self.assertEqual(self.claims(), [])

    def test_claim_needs_approved_task_and_shared_board(self):
        with self.assertRaises(coord.CoordinationError):
            self.claim(task="missing_task")
        (self.root / coord.SHARED).unlink()
        with self.assertRaises(coord.CoordinationError):
            self.claim()
        self.assertFalse((self.root / coord.SHARED).exists())

    def test_owner_checked_annotate_release_and_persistent_lock(self):
        result = self.claim()
        claim_id = result["claim"]
        for task, session in (("task_b", "session-a"), ("task_a", "session-b")):
            for action in ("release", "annotate"):
                with self.subTest(action=action), self.assertRaises(coord.CoordinationError):
                    self.store.change_claim(action, task, session, claim_id=claim_id, job="PID 1")
        self.store.change_claim("annotate", "task_a", "session-a", claim_id=claim_id, job="PID 123; log path")
        self.assertEqual(self.claims()[0]["job"], "PID 123; log path")
        self.store.change_claim("release", "task_a", "session-a", claim_id=claim_id)
        self.assertEqual(self.claims(), [])
        self.assertTrue(list((self.root / ".coworkers/state/locks").glob("*.lock")))
        with self.assertRaises(coord.CoordinationError):
            self.store.change_claim("release", "task_a", "session-a", claim_id=claim_id)

    def test_claim_preserves_surrounding_text_and_order(self):
        snap = self.store.snapshot(coord.SHARED)
        self.store.update(coord.SHARED, snap["revision"], snap["content"] + "\nProtected external evidence.\n")
        first = self.claim(("host/a",))["claim"]
        second = self.claim(("host/b",), "task_b", "session-b")["claim"]
        self.assertEqual([c["claim"] for c in self.claims()], [first, second])
        self.assertTrue(self.store.snapshot(coord.SHARED)["content"].endswith("Protected external evidence.\n"))

    def test_generic_update_cannot_edit_claims(self):
        self.claim()
        snap = self.store.snapshot(coord.SHARED)
        with self.assertRaises(coord.CoordinationError):
            self.store.update(coord.SHARED, snap["revision"], self.shared)
        self.assertEqual(self.store.snapshot(coord.SHARED), snap)
        # Protection notes may change without losing/reordering claim data.
        self.store.update(coord.SHARED, snap["revision"], snap["content"] + "\nNew protection.\n")
        self.assertEqual(len(self.claims()), 1)

    def test_new_claim_invalidates_stale_protection_update(self):
        snap = self.store.snapshot(coord.SHARED)
        self.claim()
        with self.assertRaises(coord.CoordinationError) as ctx:
            self.store.update(coord.SHARED, snap["revision"], snap["content"] + "\nProtection update\n")
        self.assertEqual(ctx.exception.code, 3)
        fresh = self.store.snapshot(coord.SHARED)
        self.store.update(coord.SHARED, fresh["revision"], fresh["content"] + "\nProtection update\n")
        self.assertEqual(len(self.claims()), 1)

    def test_invalid_shared_state_fails_closed(self):
        for content in ("legacy board", self.shared + coord.START,
                        self.shared.replace(coord.SEPARATOR, "| malformed |")):
            with self.subTest(content=content[:20]):
                # Simulates an uncooperative editor; the helper must not reset it.
                (self.root / coord.SHARED).write_text(content)
                with self.assertRaises(coord.CoordinationError):
                    self.claim()
                with self.assertRaises(coord.CoordinationError):
                    self.store.snapshot(coord.SHARED)
                self.assertEqual((self.root / coord.SHARED).read_text(), content)

    def test_duplicate_claims_invalid_timestamps_and_overlap_fail_closed(self):
        self.claim()
        text = self.store.snapshot(coord.SHARED)["content"]
        rows = coord.parse_claims(text)
        cases = []
        cases.append(coord.render_claims(text, rows + rows))
        bad = dict(rows[0], since="yesterday")
        cases.append(coord.render_claims(text, [bad]))
        bad = dict(rows[0], claim="1" * 32, resources=["host/worker_a/device/0/core/1"])
        cases.append(coord.render_claims(text, rows + [bad]))
        for content in cases:
            with self.subTest(content=content[-40:]), self.assertRaises(coord.CoordinationError):
                coord.parse_claims(content)

    def test_disallowed_targets_and_task_ids(self):
        for target in ("README.md", "../outside.md", "/tmp/outside.md", ".coworkers/state/../x.md",
                       ".coworkers/tasks/task_a/README.md", ".coworkers/state/tasks/bad-task.md"):
            with self.subTest(target=target), self.assertRaises(coord.CoordinationError):
                self.store.update(target, "missing", "must not write")
        for task in ("Task", "a__b", "../x", "x" * 65):
            with self.subTest(task=task), self.assertRaises(coord.CoordinationError):
                self.claim(task=task)

    def test_symlink_target_and_parent_are_rejected(self):
        outside = self.root / "outside.md"
        outside.write_text("protected")
        board = self.root / self.board
        board.unlink()
        board.symlink_to(outside)
        with self.assertRaises(coord.CoordinationError):
            self.store.snapshot(self.board)
        self.assertEqual(outside.read_text(), "protected")
        board.unlink()
        tasks = board.parent
        for child in tasks.iterdir():
            child.unlink()
        tasks.rmdir()
        tasks.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(coord.CoordinationError):
            self.store.update(self.board, "missing", "no")
        self.assertFalse((self.root / "task_a.md").exists())

    def test_noncanonical_root_and_cross_device_guard(self):
        with self.assertRaises(coord.CoordinationError):
            coord.Store(str(self.root / ".coworkers" / ".."))
        # Exercise the guard without creating a mount or touching host resources.
        self.store.device += 1
        with self.assertRaises(coord.CoordinationError):
            self.store.snapshot(self.board)

    def test_symlink_root_and_hardlinked_target_are_rejected(self):
        alias = self.root / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(coord.CoordinationError):
            coord.Store(alias)
        os.link(self.root / self.board, self.root / "hardlink")
        with self.assertRaises(coord.CoordinationError):
            self.store.snapshot(self.board)

    def test_symlink_lock_is_rejected(self):
        name = ".coworkers/state/tasks/task_c.md"
        key = hashlib.sha256(name.encode()).hexdigest()
        lock = self.root / f".coworkers/state/locks/{key}.lock"
        lock.symlink_to(self.root / self.board)
        with self.assertRaises(coord.CoordinationError):
            self.store.update(name, "missing", "# C\n")
        self.assertEqual(self.store.snapshot(self.board)["content"], "# Task A\n")

    def test_write_failure_preserves_old_file_and_cleans_temporary(self):
        snapshot = self.store.snapshot(self.board)
        with patch.object(coord.os, "replace", side_effect=OSError("simulated failure")):
            with self.assertRaises(OSError):
                self.store.update(self.board, snapshot["revision"], "new")
        self.assertEqual(self.store.snapshot(self.board), snapshot)
        self.assertEqual(list((self.root / self.board).parent.glob(".coord-*")), [])

    def test_size_bound_and_utf8_errors(self):
        snap = self.store.snapshot(self.board)
        with self.assertRaises(coord.CoordinationError):
            self.store.update(self.board, snap["revision"], "x" * (coord.MAX_BYTES + 1))
        (self.root / self.board).write_bytes(b"\xff")
        result = self.cli("snapshot", self.board)
        self.assertEqual(result.returncode, 2)
        self.assertIn("error", json.loads(result.stderr))
        self.assertNotIn("Traceback", result.stderr)

    def test_busy_lock_is_bounded_and_other_board_can_progress(self):
        with self.store.lock(self.board):
            start = time.monotonic()
            result = self.cli("--timeout", "0.05", "update", self.board,
                              "--expected", self.store.snapshot(self.board)["revision"], content="new")
            self.assertEqual(result.returncode, 4, result.stderr)
            self.assertLess(time.monotonic() - start, 3)
            other = self.cli("update", ".coworkers/state/tasks/task_c.md", "--expected", "missing", content="# C\n")
            self.assertEqual(other.returncode, 0, other.stderr)

    def test_unsupported_platform_fails_explicitly(self):
        with patch.object(coord, "fcntl", None):
            with self.assertRaisesRegex(coord.CoordinationError, "unsupported platform"):
                coord.Store(self.root)

    def test_post_replace_io_error_requires_snapshot_not_blind_retry(self):
        snap = self.store.snapshot(self.board)
        original_fsync = coord.os.fsync
        calls = 0

        def fail_directory_sync(fd):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated directory sync failure after replace")
            return original_fsync(fd)

        with patch.object(coord.os, "fsync", side_effect=fail_directory_sync):
            with self.assertRaises(OSError):
                self.store.update(self.board, snap["revision"], "# Already replaced\n")
        self.assertEqual(self.store.snapshot(self.board)["content"], "# Already replaced\n")
        with self.assertRaises(coord.CoordinationError):
            self.store.update(self.board, snap["revision"], "# Blind retry\n")

    def test_timeout_validation(self):
        for value in (-1, 31, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(coord.CoordinationError):
                coord.Store(self.root, value)

    def test_simultaneous_cas_writers_one_wins(self):
        expected = self.store.snapshot(self.board)["revision"]
        processes = []
        with self.store.lock(self.board):
            for text in ("# One\n", "# Two\n"):
                process = subprocess.Popen([sys.executable, str(HELPER), "--root", str(self.root),
                                            "update", self.board, "--expected", expected],
                                           stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, text=True)
                process.stdin.write(text)
                process.stdin.close()
                process.stdin = None
                processes.append(process)
            time.sleep(0.1)
        for process in processes:
            process.communicate(timeout=10)
        self.assertEqual(sorted(p.returncode for p in processes), [0, 3])
        self.assertIn(self.store.snapshot(self.board)["content"], ("# One\n", "# Two\n"))

    def test_parallel_first_time_task_creation(self):
        fresh = self.root / "fresh"
        fresh.mkdir()
        processes = []
        for task in ("task_a", "task_b"):
            process = subprocess.Popen([sys.executable, str(HELPER), "--root", str(fresh), "update",
                                        f".coworkers/state/tasks/{task}.md", "--expected", "missing"],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True)
            process.stdin.write(f"# {task}\n")
            process.stdin.close()
            process.stdin = None
            processes.append(process)
        for process in processes:
            _, error = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0, error)
        self.assertEqual(len(list((fresh / ".coworkers/state/tasks").glob("*.md"))), 2)

    def test_simultaneous_claims_one_wins(self):
        processes = []
        with self.store.lock(coord.SHARED):
            for task in ("task_a", "task_b"):
                processes.append(subprocess.Popen([sys.executable, str(HELPER), "--root", str(self.root),
                                                    "claim", "--task", task, "--session", task,
                                                    "--resource", "host/shared/device/0"],
                                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
            time.sleep(0.1)
        for process in processes:
            process.communicate(timeout=10)
        self.assertEqual(sorted(p.returncode for p in processes), [0, 3])
        self.assertEqual(len(self.claims()), 1)

    def test_crashed_lock_holder_does_not_erase_reservation(self):
        self.claim()
        code = (f"import sys,time; sys.path.insert(0, {str(HELPER.parent)!r}); import coord; "
                f"store=coord.Store({str(self.root)!r}); "
                "\nwith store.lock(coord.SHARED):\n print('ready', flush=True)\n time.sleep(30)\n")
        process = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
        try:
            ready, _, _ = select.select([process.stdout], [], [], 5)
            self.assertTrue(ready, "child failed to acquire lock in time")
            self.assertEqual(process.stdout.readline().strip(), "ready")
            blocked = self.cli("--timeout", "0", "claim", "--task", "task_b", "--session", "b",
                               "--resource", "host/free/device/0")
            self.assertEqual(blocked.returncode, 4, blocked.stderr)
        finally:
            process.kill()  # Only this test's child, never a project/device process.
            process.communicate(timeout=5)
        with self.store.lock(coord.SHARED):
            self.assertEqual(len(self.claims()), 1)
        with self.assertRaises(coord.CoordinationError):
            self.claim(task="task_b", session="b")

    def test_cli_round_trip(self):
        snap = self.cli("snapshot", self.board)
        self.assertEqual(snap.returncode, 0)
        expected = json.loads(snap.stdout)["revision"]
        result = self.cli("update", self.board, "--expected", expected, content="# CLI\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        claim = self.cli("claim", "--task", "task_a", "--session", "cli",
                         "--resource", "host/cli/port/tcp/8000")
        self.assertEqual(claim.returncode, 0, claim.stderr)
        claim_id = json.loads(claim.stdout)["claim"]
        note = self.cli("annotate", "--task", "task_a", "--session", "cli", "--claim", claim_id, "--job", "PID 99")
        self.assertEqual(note.returncode, 0, note.stderr)
        release = self.cli("release", "--task", "task_a", "--session", "cli", "--claim", claim_id)
        self.assertEqual(release.returncode, 0, release.stderr)

    def test_init_task_status_handoff_and_decide_round_trip(self):
        coworkers = (ROOT / "toolkit/general/templates/COWORKERS.template.md").read_text()
        self.store.update("COWORKERS.md", "missing", coworkers)
        init = self.cli("init-task", "--task", "multi_agent_bus",
                        "--goal", "Verify ergonomic commands", "--planner", "planner/claude-1")
        self.assertEqual(init.returncode, 0, init.stderr)
        payload = json.loads(init.stdout)
        self.assertTrue(payload["record_created"])
        self.assertTrue((self.root / ".coworkers/tasks/multi_agent_bus/README.md").is_file())
        self.assertIn("| multi_agent_bus |", self.store.snapshot("COWORKERS.md")["content"])
        # Duplicate init-task fails closed with stale/conflict exit 3.
        dup = self.cli("init-task", "--task", "multi_agent_bus", "--goal", "Duplicate")
        self.assertEqual(dup.returncode, 3)

        ho = self.cli("handoff", "--task", "multi_agent_bus", "--by", "planner/claude-1",
                      "--state", "running", "--stage", "01_core",
                      "--next", "executor/codex-1 — run regression suite",
                      "--blocker", "waiting on GPU 0", "--msg", "core code ready", "--print-prompt")
        self.assertEqual(ho.returncode, 0, ho.stderr)
        ho_data = json.loads(ho.stdout)
        self.assertEqual(ho_data["state"], "running")
        self.assertIn("multi_agent_bus", ho_data["pickup_prompt"])

        dec = self.cli("decide", "--task", "multi_agent_bus", "--by", "executor/codex-1",
                       "--blocker", "", "--msg", "keep stdlib only; no deps; tests pass")
        self.assertEqual(dec.returncode, 0, dec.stderr)

        st_json = self.cli("status")
        self.assertEqual(st_json.returncode, 0, st_json.stderr)
        status = json.loads(st_json.stdout)
        row = next(t for t in status["tasks"] if t["task"] == "multi_agent_bus")
        self.assertEqual(row["state"], "running")
        self.assertEqual(row["stage"], "01_core")
        self.assertEqual(row["blocked"], "")
        st_text = self.cli("status", "--format", "text")
        self.assertEqual(st_text.returncode, 0, st_text.stderr)
        self.assertIn("multi_agent_bus [running]", st_text.stdout)

    def test_concurrent_handoffs_and_decisions_both_preserved(self):
        coworkers = (ROOT / "toolkit/general/templates/COWORKERS.template.md").read_text()
        self.store.update("COWORKERS.md", "missing", coworkers)
        self.store.init_task("parallel_ho", "Concurrent append check", "planner/agy-1")
        board = ".coworkers/state/tasks/parallel_ho.md"
        procs = []
        with self.store.lock(board):
            procs.append(subprocess.Popen(
                [sys.executable, str(HELPER), "--root", str(self.root), "handoff",
                 "--task", "parallel_ho", "--by", "executor/codex-1", "--msg", "worker one finished"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
            procs.append(subprocess.Popen(
                [sys.executable, str(HELPER), "--root", str(self.root), "decide",
                 "--task", "parallel_ho", "--by", "reviewer/pi-1", "--msg", "approved diff"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
            time.sleep(0.1)
        for p in procs:
            _, err = p.communicate(timeout=10)
            self.assertEqual(p.returncode, 0, err)
        content = self.store.snapshot(board)["content"]
        self.assertIn("executor/codex-1 — worker one finished", content)
        self.assertIn("reviewer/pi-1 — approved diff", content)

    def test_auto_root_resolves_from_regular_and_linked_git_worktrees(self):
        import shutil
        if not shutil.which("git"):
            self.skipTest("git not available")
        repo = self.root / "gitrepo"
        wt = self.root / "gitwt"
        repo.mkdir()
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
        git = lambda cwd, *a: subprocess.run(
            ["git", "-c", "user.name=T", "-c", "user.email=t@invalid",
             "-c", "commit.gpgSign=false", *a],
            cwd=cwd, env=env, text=True, capture_output=True, check=True, timeout=15)
        git(repo, "init", "-q", "--template=")
        (repo / "f.txt").write_text("x\n")
        git(repo, "add", "f.txt")
        git(repo, "commit", "-qm", "init")
        git(repo, "worktree", "add", "-qb", "task/auto", str(wt))
        coord.Store(repo).update(coord.SHARED, "missing", self.shared)
        for cwd in (repo, wt):
            proc = subprocess.run([sys.executable, str(HELPER), "status"],
                                  cwd=cwd, env=env, text=True, capture_output=True, timeout=10)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(proc.stdout)["root"], str(repo.resolve()))


if __name__ == "__main__":
    unittest.main()
