"""Deterministic synthetic fixture for context-footprint experiments.

Builds a small project whose files carry unique, stable detail markers. The
harness later asserts which markers entered the model context and which never
did. No randomness and no real project content.
"""

from pathlib import Path

FILLER = "filler line for realistic payload size\n"

MARKERS = {
    "router": "Task-local collaboration",
    "workflow": "FX_WORKFLOW_DETAIL_M1",
    "code_alpha": "FX_ALPHA_CODE_M1",
    "code_beta": "FX_BETA_CODE_M1",
    "board_alpha": "FX_ALPHA_BOARD_M1",
    "board_beta": "FX_BETA_BOARD_M1",
    "record_alpha": "FX_ALPHA_RECORD_M1",
    "record_beta": "FX_BETA_RECORD_M1",
    "stage_alpha_1": "FX_ALPHA_STAGE01_M1",
    "stage_alpha_2": "FX_ALPHA_STAGE02_M1",
    "stage_beta": "FX_BETA_STAGE01_M1",
    "log_alpha_1": "FX_ALPHA_LOG1_M1",
    "log_alpha_2": "FX_ALPHA_LOG2_M1",
    "log_beta": "FX_BETA_LOG_M1",
    "shared": "FX_SHARED_PROT_M1",
}


def _board(task, goal, stage, plan, marker):
    return (
        f"# Task: {task}\n\n## Current state\n\n- Goal: {goal} {marker}\n"
        f"- State: running\n- Stage: {stage}\n- Planner: session-planner-x\n"
        f"- Executors: session-executor-x\n"
        f"- Next: executor/session-executor-x — continue the current stage\n"
        f"- Workspace: {task}-worktree; branch task/{task}\n"
        f"- Records: .coworkers/tasks/{task}/README.md\n- Plan: {plan}\n\n"
        "## Decisions\n\n- 2026-11-20 10:00 executor/session-executor-x — fixture decision entry.\n\n"
        "## Handoffs\n\n- 2026-11-20 09:00 planner/session-planner-x — fixture handoff entry.\n"
    )


def _stage(task, number, marker):
    return (
        f"# {number}_fixture_stage\n\nTask: `{task}` · State: running\n\n"
        f"## Execution plan\n\n1. Fixture step one. {marker}\n"
        "2. Fixture step two with a check.\n\n## Execution notes\n\n- fixture observation.\n"
    )


def build_fixture(root: Path, install: bool = True) -> dict:
    """Create the synthetic project; returns marker map and key paths."""
    root = Path(root)
    (root / "pkg").mkdir(parents=True)
    (root / "pkg/alpha.py").write_text(
        f'"""Alpha module under test."""\nVALUE = "{MARKERS["code_alpha"]}"\n' + FILLER * 8
    )
    (root / "pkg/beta.py").write_text(
        f'"""Beta module under test."""\nVALUE = "{MARKERS["code_beta"]}"\n' + FILLER * 8
    )
    paths = {"root": str(root), "alpha_board": ".coworkers/state/tasks/alpha_probe.md"}

    if install:
        entry = root / "COWORKERS.md"
        entry.write_text(
            "# COWORKERS — project entry point\n\n"
            "An index, not a global current task.\n"
            "Coordination root: (this workspace root)\n"
            f"Workflow: `.coworkers/WORKFLOW.md` (contains {MARKERS['workflow']}).\n"
            "Helper: `.coworkers/tools/coord.py` (usage: `.coworkers/tools/README.md`).\n"
            "Shared claims/protections: `.coworkers/state/shared.md`.\n\n"
            "## Active task index\n\n| Added | Task ID | Purpose | State board |\n|---|---|---|---|\n"
            "| 2026-11-20 | alpha_probe | fixture alpha | `.coworkers/state/tasks/alpha_probe.md` |\n"
            "| 2026-11-20 | beta_probe | fixture beta | `.coworkers/state/tasks/beta_probe.md` |\n"
        )
        shared = root / ".coworkers/state/shared.md"
        shared.parent.mkdir(parents=True)
        shared.write_text(
            "# Shared coordination\n\n## Protected assets\n\n"
            f"| 2026-11-20 | protected/baseline.dat | accepted baseline | alpha_probe | manual |\n"
            f"Shared marker: {MARKERS['shared']}\n\n"
            "## Claims — helper managed\n\n"
            "<!-- blueberry:claims:start -->\n| Claim | Task | Session | Resources | Since | Job |\n"
            "|---|---|---|---|---|---|\n<!-- blueberry:claims:end -->\n"
        )
        board_a = root / ".coworkers/state/tasks/alpha_probe.md"
        board_a.parent.mkdir(parents=True)
        board_a.write_text(
            _board("alpha_probe", "Fix the alpha defect.", "01_reproduce",
                   ".coworkers/tasks/alpha_probe/stages/01_reproduce.md", MARKERS["board_alpha"])
            + FILLER * 6
        )
        (root / ".coworkers/state/tasks/beta_probe.md").write_text(
            _board("beta_probe", "Measure the beta regression.", "01_reproduce",
                   ".coworkers/tasks/beta_probe/stages/01_reproduce.md", MARKERS["board_beta"])
            + FILLER * 6
        )
        record_a = root / ".coworkers/tasks/alpha_probe"
        (record_a / "stages").mkdir(parents=True)
        (record_a / "README.md").write_text(
            f"# Alpha probe record\n\nAt a glance: {MARKERS['record_alpha']}\n" + FILLER * 6
        )
        (record_a / "stages/01_reproduce.md").write_text(
            _stage("alpha_probe", "01", MARKERS["stage_alpha_1"]) + FILLER * 6
        )
        (record_a / "stages/02_measure.md").write_text(
            _stage("alpha_probe", "02", MARKERS["stage_alpha_2"]) + FILLER * 6
        )
        record_b = root / ".coworkers/tasks/beta_probe"
        (record_b / "stages").mkdir(parents=True)
        (record_b / "README.md").write_text(
            f"# Beta probe record\n\nAt a glance: {MARKERS['record_beta']}\n" + FILLER * 6
        )
        (record_b / "stages/01_reproduce.md").write_text(
            _stage("beta_probe", "01", MARKERS["stage_beta"]) + FILLER * 6
        )
        log1 = root / "local_tests/alpha_probe/run_001/logs"
        log2 = root / "local_tests/alpha_probe/run_002/logs"
        logb = root / "local_tests/beta_probe/run_001/logs"
        for directory, marker in ((log1, MARKERS["log_alpha_1"]), (log2, MARKERS["log_alpha_2"]),
                                  (logb, MARKERS["log_beta"])):
            directory.mkdir(parents=True)
            (directory / "server.log").write_text(f"log marker {marker}\n" + FILLER * 12)
    else:
        board_a = root / ".coworkers/state/tasks/alpha_probe.md"
    paths["alpha_board_abs"] = str(board_a)
    paths["stage_alpha_1_abs"] = str(root / ".coworkers/tasks/alpha_probe/stages/01_reproduce.md")
    paths["record_alpha_abs"] = str(root / ".coworkers/tasks/alpha_probe/README.md")
    paths["shared_abs"] = str(root / ".coworkers/state/shared.md")
    paths["log_alpha_2_abs"] = str(root / "local_tests/alpha_probe/run_002/logs/server.log")
    return paths
