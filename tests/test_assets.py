"""Template contracts and disposable Git/worktree integration, not LLM evaluation."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GENERAL = ROOT / "toolkit/general"
HELPER = GENERAL / "tools/coord.py"
spec = importlib.util.spec_from_file_location("coord_assets", HELPER)
coord = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coord)


class AssetTests(unittest.TestCase):
    def test_router_budget_and_not_a_second_board(self):
        text = (GENERAL / "system-prompts/project.md").read_text()
        self.assertLessEqual(len(text.split()), 160)
        self.assertIn("selected task", text)
        self.assertIn("discussion-only", text)
        self.assertNotIn("| Resource |", text)
        self.assertNotIn("## Current task", text)

    def test_project_index_and_task_templates_are_separate(self):
        index = (GENERAL / "templates/COWORKERS.template.md").read_text()
        task = (GENERAL / "templates/TASK.template.md").read_text()
        self.assertLessEqual(len(index.splitlines()), 60)
        self.assertIn("Active task index", index)
        self.assertNotIn("## Current task", index)
        for field in ("Goal:", "State:", "Stage:", "Planner:", "Executors:", "Next:", "Workspace:", "Plan:"):
            self.assertIn(field, task)
        self.assertIn("15 handoffs / 20 decisions", task)
        self.assertIn("from the top", task)

    def test_planner_owned_acceptance_before_ready(self):
        workflow = (GENERAL / "WORKFLOW.md").read_text()
        for rule in ("Before marking a coding task `ready`", "existing test command",
                     "negative cases", "fail for the intended reason",
                     "must not weaken", "Passing tests alone",
                     "bounded experiment"):
            self.assertIn(rule, workflow)
        for name in ("TASK", "STAGE"):
            text = (GENERAL / f"templates/{name}.template.md").read_text()
            self.assertIn("Planner-owned acceptance check", text)
            self.assertIn("before `ready`", text)
        index = (GENERAL / "templates/COWORKERS.template.md").read_text()
        self.assertIn("acceptance checks before handoff", index)

    def test_index_defines_roles_and_avoids_noise(self):
        index = (GENERAL / "templates/COWORKERS.template.md").read_text()
        self.assertLessEqual(len(index.splitlines()), 60)
        for role in ("**Planner**", "**Executor**", "**Reviewer (optional)**"):
            self.assertIn(role, index)
        for noise in ("v2", "docs/` or `notes/"):
            self.assertNotIn(noise, index)

    def test_readme_prompts_guard_missing_paths_and_cover_update_uninstall(self):
        readme = (ROOT / "README.md").read_text()
        self.assertIn("Low contextual aggressiveness", readme)
        self.assertNotIn("Low prompt intrusion", readme)
        self.assertNotIn("No ownership of a project's", readme)
        self.assertIn("flowchart TD", readme)
        self.assertIn("parallel session", readme)
        for section in ("Update an installation", "Uninstall"):
            self.assertIn(f"## {section}", readme)
        self.assertEqual(readme.count("is missing or ambiguous"), 3, "setup/update/uninstall prompts must ask first")

    def test_explicit_skill_metadata_and_new_cleanup_policy(self):
        for path in (GENERAL / "skills").glob("*/SKILL.md"):
            text = path.read_text()
            self.assertTrue(text.startswith("---\n"))
            metadata = text.split("---", 2)[1]
            self.assertIn(f"name: {path.parent.name}\n", metadata)
            self.assertIn("disable-model-invocation: true", metadata)
        cleaner = (GENERAL / "skills/local-tests-cleaner/SKILL.md").read_text()
        for required in ("Default to this session's confirmed task", "Bottom is latest",
                         "Registries are never FIFO", "15 handoffs / 20 decisions",
                         "from the top", "legacy", "AFTER acquiring", "closed-task",
                         "Never delete `.coworkers/tasks/`", ">10 GB",
                         "auto-delete", "limits never trigger deletion"):
            self.assertIn(required, cleaner)
        self.assertNotIn("Sort newest first", cleaner)

    def test_pi_prompt_has_arguments_without_executable_extension(self):
        prompt = (ROOT / "toolkit/specific/agent-specific/pi/prompts/task.md").read_text()
        self.assertIn("${1:-unspecified}", prompt)
        self.assertIn("${2:-unspecified}", prompt)
        self.assertIn("only this conversation", prompt)
        self.assertIn("discussion-only", prompt)
        package = json.loads((ROOT / "package.json").read_text())
        self.assertEqual(package["pi"], {"skills": ["toolkit/general/skills"]})
        self.assertFalse(package.get("dependencies"))
        self.assertFalse(package.get("scripts"))

    def test_antigravity_adapter_and_task_skill_contract(self):
        adapter = (ROOT / "toolkit/specific/agent-specific/antigravity/README.md").read_text()
        for required in ("AGENTS.md", ".agents/skills/<name>/", "trigger: always_on",
                         ".agents/rules/blueberry.md", "/skills reload",
                         "~/.gemini/antigravity-cli/skills/", "disable-model-invocation: true",
                         "Never blanket-ignore `.agents/`"):
            self.assertIn(required, adapter)
        skill_path = ROOT / "toolkit/specific/agent-specific/antigravity/skills/task/SKILL.md"
        skill = skill_path.read_text()
        self.assertTrue(skill.startswith("---\n"))
        metadata = skill.split("---", 2)[1]
        self.assertIn(f"name: {skill_path.parent.name}\n", metadata)
        self.assertIn("description:", metadata)
        self.assertIn("disable-model-invocation: true", metadata)
        for required in ("only this conversation", "discussion-only",
                         "current-task file", "do not read all task boards"):
            self.assertIn(required, skill)

    def test_unified_install_and_pi_agents_md_alignment(self):
        install = (ROOT / "INSTALL.md").read_text()
        for required in ("pi/README.md", "antigravity/README.md", "AGENTS.md",
                         ".agents/skills/<name>/SKILL.md", "<!-- blueberry:router:start -->",
                         "<!-- blueberry:router:end -->", "AGENTS.override.md",
                         "--path-format=absolute", "snapshot COWORKERS.md",
                         "preserved\n   untracked paths",
                         "## Multi-harness coexistence", "## Setup procedure",
                         "## Update procedure", "## Uninstall procedure",
                         "## Legacy board migration",
                         "Never blanket-ignore `.coworkers/`, `.agents/` or `.pi/`"):
            self.assertIn(required, install)
        pi_adapter = (ROOT / "toolkit/specific/agent-specific/pi/README.md").read_text()
        for required in ("AGENTS.md", ".agents/skills/<name>/", "AGENTS.override.md",
                         "--approve", ".pi/APPEND_SYSTEM.md"):
            self.assertIn(required, pi_adapter)

    def test_shared_template_is_parseable_empty_state(self):
        text = (GENERAL / "templates/SHARED.template.md").read_text()
        self.assertEqual(coord.parse_claims(text), [])
        self.assertEqual(coord.render_claims(text, []), text)

    def test_markdown_links_resolve(self):
        files = [ROOT / "README.md", ROOT / "INSTALL.md",
                 *ROOT.glob("toolkit/**/*.md"), ROOT / "tests/README.md"]
        for path in files:
            for match in re.finditer(r"\[[^\]\n]+\]\(([^)\n]+)\)", path.read_text()):
                link = match.group(1)
                if link.startswith(("http:", "https:", "mailto:", "#")) or "<" in link:
                    continue
                relative, _, anchor = link.partition("#")
                target = (path.parent / relative).resolve()
                with self.subTest(source=str(path.relative_to(ROOT)), link=link):
                    self.assertTrue(target.exists(), str(target))
                    if anchor and target.is_file():
                        headings = re.findall(r"^#+\s+(.+)$", target.read_text(), re.M)
                        anchors = [re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in headings]
                        self.assertIn(anchor, anchors)

    @unittest.skipUnless(os.name == "posix", "local POSIX helper")
    def test_copied_assets_round_trip_in_disposable_project(self):
        # An approved setup fixture, not an installer or a live harness invocation.
        with tempfile.TemporaryDirectory(prefix="blueberry-copy-") as directory:
            root = Path(directory).resolve()
            store = coord.Store(root)
            for template, destination in (("COWORKERS", "COWORKERS.md"),
                                           ("SHARED", coord.SHARED),
                                           ("TASK", ".coworkers/state/tasks/example_task.md")):
                content = (GENERAL / f"templates/{template}.template.md").read_text()
                store.update(destination, "missing", content.replace("<task_id>", "example_task"))
            shutil.copytree(GENERAL / "tools", root / ".coworkers/tools")
            shutil.copyfile(GENERAL / "WORKFLOW.md", root / ".coworkers/WORKFLOW.md")
            record = root / ".coworkers/tasks/example_task/README.md"
            record.parent.mkdir(parents=True)
            record.write_text((GENERAL / "templates/TASK_README.template.md").read_text())
            before = record.read_bytes()
            helper = root / ".coworkers/tools/coord.py"
            result = subprocess.run([sys.executable, str(helper), "--root", str(root), "claim",
                                     "--task", "example_task", "--session", "executor-1",
                                     "--resource", "workspace/main/scratch/example_task"],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            claims = coord.parse_claims(store.snapshot(coord.SHARED)["content"])
            self.assertEqual(len(claims), 1)
            self.assertEqual(claims[0]["claim"], json.loads(result.stdout)["claim"])
            self.assertEqual(claims[0]["resources"], ["workspace/main/scratch/example_task"])
            self.assertEqual(record.read_bytes(), before)
            self.assertFalse((root / "local_tests").exists())
            self.assertFalse((root / ".pi").exists())

    @unittest.skipUnless(os.name == "posix", "local POSIX helper")
    def test_scoped_snapshot_does_not_read_other_tasks_or_records(self):
        with tempfile.TemporaryDirectory(prefix="blueberry-isolation-") as directory:
            root = Path(directory).resolve()
            store = coord.Store(root)
            a = ".coworkers/state/tasks/task_a.md"
            store.update(a, "missing", "# A\nA_DETAIL_ONLY\n")
            # Any accidental eager read of B as UTF-8 would fail.
            (root / ".coworkers/state/tasks/task_b.md").write_bytes(b"\xffB_DETAIL_ONLY")
            records = root / ".coworkers/tasks/task_b"
            records.mkdir(parents=True)
            (records / "README.md").write_text("B_RECORD_ONLY")
            snapshot = store.snapshot(a)
            self.assertEqual(snapshot["content"], "# A\nA_DETAIL_ONLY\n")
            self.assertNotIn("B_", json.dumps(snapshot))


@unittest.skipUnless(os.name == "posix" and shutil.which("git"), "POSIX and Git integration")
class GitWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="blueberry-git-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
        self.git(self.repo, "init", "-q", "--template=")
        exclude = self.exclude(self.repo)
        exclude.parent.mkdir(parents=True, exist_ok=True)
        exclude.write_text("# Existing local rules\n/existing_local_only/\n")
        (self.repo / ".gitignore").write_text("existing_scratch/\n")
        self.git(self.repo, "add", ".gitignore")
        self.git(self.repo, "commit", "-qm", "fixture baseline")
        self.before_ignore = (self.repo / ".gitignore").read_bytes()
        self.worktree = self.base / "task-worktree"
        self.git(self.repo, "worktree", "add", "-qb", "task/example", str(self.worktree))

    def git(self, cwd, *args, check=True):
        return subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                               "-c", "commit.gpgSign=false", "-c", f"core.hooksPath={os.devnull}",
                               *args], cwd=cwd, env=self.environment, text=True,
                              capture_output=True, check=check, timeout=15)

    def exclude(self, workspace):
        raw = self.git(workspace, "rev-parse", "--git-path", "info/exclude").stdout.strip()
        path = Path(raw)
        return path if path.is_absolute() else workspace / path

    def test_selective_exclusion_in_regular_and_linked_worktrees(self):
        patterns = ("/COWORKERS.md", "/.coworkers/state/", "/.coworkers/tools/",
                    "/.coworkers/WORKFLOW.md", "/local_tests/")
        exclude = self.exclude(self.repo)
        original = exclude.read_text()
        exclude.write_text(original + "\n" + "\n".join(patterns) + "\n")
        self.assertEqual(exclude.resolve(), self.exclude(self.worktree).resolve())
        self.assertTrue((self.worktree / ".git").is_file())
        for workspace in (self.repo, self.worktree):
            for relative in ("COWORKERS.md", ".coworkers/state/tasks/example.md", ".coworkers/state/shared.md",
                             ".coworkers/tools/coord.py", ".coworkers/WORKFLOW.md", "local_tests/example/run/log"):
                path = workspace / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture")
                self.assertEqual(self.git(workspace, "check-ignore", "-q", relative, check=False).returncode, 0)
            record = workspace / ".coworkers/tasks/example/README.md"
            record.parent.mkdir(parents=True)
            record.write_text("# Durable record\n")
            stage = record.parent / "stages/01_reproduce.md"
            stage.parent.mkdir()
            stage.write_text("# Stage\n")
            for path in (record, stage):
                relative = str(path.relative_to(workspace))
                self.assertEqual(self.git(workspace, "check-ignore", "-q", relative, check=False).returncode, 1)
            self.assertEqual((workspace / ".gitignore").read_bytes(), self.before_ignore)
        self.git(self.worktree, "add", ".coworkers/tasks/example/README.md")
        self.assertIn(".coworkers/tasks/example/README.md",
                      self.git(self.worktree, "diff", "--cached", "--name-only").stdout)
        self.assertEqual(self.git(self.repo, "diff", "--cached", "--name-only").stdout, "")

    def test_two_workspaces_share_one_reservation_store(self):
        store = coord.Store(self.repo)
        store.update(coord.SHARED, "missing", (GENERAL / "templates/SHARED.template.md").read_text())
        for task in ("task_a", "task_b"):
            store.update(f".coworkers/state/tasks/{task}.md", "missing", f"# {task}\n")
        first = subprocess.run([sys.executable, str(HELPER), "--root", str(self.repo), "claim",
                                "--task", "task_a", "--session", "a", "--resource", "host/shared/port/tcp/8000"],
                               cwd=self.repo, capture_output=True, text=True, timeout=10)
        second = subprocess.run([sys.executable, str(HELPER), "--root", str(self.repo), "claim",
                                 "--task", "task_b", "--session", "b", "--resource", "host/shared/port/tcp/8000"],
                                cwd=self.worktree, capture_output=True, text=True, timeout=10)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 3, second.stderr)
        self.assertFalse((self.worktree / ".coworkers/state/shared.md").exists())

    def test_ignored_state_is_not_untracked_automatically(self):
        board = self.repo / "COWORKERS.md"
        board.write_text("# Existing tracked board\n")
        self.git(self.repo, "add", "COWORKERS.md")
        self.git(self.repo, "commit", "-qm", "fixture tracked board")
        before = hashlib.sha256(board.read_bytes()).hexdigest()
        exclude = self.exclude(self.repo)
        exclude.write_text(exclude.read_text() + "\n/COWORKERS.md\n")
        self.assertEqual(self.git(self.repo, "ls-files", "COWORKERS.md").stdout.strip(), "COWORKERS.md")
        self.assertEqual(hashlib.sha256(board.read_bytes()).hexdigest(), before)
        self.assertNotEqual(self.git(self.repo, "check-ignore", "-q", "COWORKERS.md", check=False).returncode, 0)

    def test_selective_exclusion_preserves_tracked_agents_files(self):
        team_rule = self.repo / ".agents/rules/project-style.md"
        team_rule.parent.mkdir(parents=True)
        team_rule.write_text("---\ntrigger: always_on\n---\n# Team style\n")
        self.git(self.repo, "add", ".agents/rules/project-style.md")
        self.git(self.repo, "commit", "-qm", "fixture team rule")
        patterns = ("/COWORKERS.md", "/.coworkers/state/", "/.coworkers/tools/",
                    "/.coworkers/WORKFLOW.md", "/local_tests/",
                    "/.agents/skills/local-tests-cleaner/", "/.agents/skills/task/",
                    "/.pi/prompts/task.md")
        exclude = self.exclude(self.repo)
        exclude.write_text(exclude.read_text() + "\n" + "\n".join(patterns) + "\n")
        for relative in (".agents/skills/local-tests-cleaner/SKILL.md",
                         ".agents/skills/task/SKILL.md", ".pi/prompts/task.md"):
            path = self.repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture")
            self.assertEqual(self.git(self.repo, "check-ignore", "-q", relative, check=False).returncode, 0)
        untracked_team_skill = self.repo / ".agents/skills/team-linter/SKILL.md"
        untracked_team_skill.parent.mkdir(parents=True)
        untracked_team_skill.write_text("---\nname: team-linter\ndescription: fixture\n---\n")
        for preserved in (".agents/rules/project-style.md", ".agents/skills/team-linter/SKILL.md"):
            self.assertNotEqual(self.git(self.repo, "check-ignore", "-q", preserved, check=False).returncode, 0)
        self.assertEqual((self.repo / ".gitignore").read_bytes(), self.before_ignore)


if __name__ == "__main__":
    unittest.main()
