"""Scenario definitions: scripted turns plus context expectations.

Tier A uses a scripted mock model, so expectations verify harness CONTEXT
ASSEMBLY (which markers enter the payload), not model judgment. Behavioral
selection belongs to Tier B with a real model and explicit spending consent.
"""

from pathlib import Path

from fixtures import MARKERS


def build_scenarios(paths):
    root = Path(paths["root"])
    return [
        {
            "id": "general_no_task",
            "description": "General question: no task board content may enter context.",
            "user": "Explain in one sentence what the VALUE constant in pkg/alpha.py is for. Do not read any other files.",
            "turns": [{"content": "It is a fixture marker constant."}],
            "allowed": [MARKERS["router"]],
            "forbidden": [MARKERS["board_alpha"], MARKERS["board_beta"], MARKERS["log_alpha_1"],
                          MARKERS["shared"], MARKERS["workflow"], MARKERS["code_alpha"]],
            "system_must_contain": [MARKERS["router"]],
        },
        {
            "id": "task_isolation_alpha",
            "description": "Task A state + current stage: sibling task, other stages and logs stay out.",
            "user": "Work on task alpha_probe as Executor: read the task state and the current stage plan, then state the next action.",
            "turns": [
                {"tool_calls": [{"name": "read", "arguments": {"path": paths["alpha_board_abs"]}}]},
                {"tool_calls": [{"name": "read",
                                 "arguments": {"path": paths["stage_alpha_1_abs"]}}]},
                {"content": "Next: continue stage 01_reproduce."},
            ],
            "allowed": [MARKERS["router"], MARKERS["board_alpha"], MARKERS["stage_alpha_1"]],
            "forbidden": [MARKERS["board_beta"], MARKERS["stage_alpha_2"], MARKERS["record_alpha"],
                          MARKERS["log_alpha_1"], MARKERS["log_alpha_2"], MARKERS["log_beta"],
                          MARKERS["shared"], MARKERS["code_beta"]],
            "system_must_contain": [MARKERS["router"]],
        },
        {
            "id": "evidence_scoping",
            "description": "One evidence log: sibling logs and plan files stay out.",
            "user": "Work on task alpha_probe as Executor: check the task state, then inspect the run_002 server log and summarize it.",
            "turns": [
                {"tool_calls": [{"name": "read", "arguments": {"path": paths["alpha_board_abs"]}}]},
                {"tool_calls": [{"name": "read",
                                 "arguments": {"path": paths["log_alpha_2_abs"]}}]},
                {"content": "run_002 log summarized; marker recorded."},
            ],
            "allowed": [MARKERS["router"], MARKERS["board_alpha"], MARKERS["log_alpha_2"]],
            "forbidden": [MARKERS["board_beta"], MARKERS["stage_alpha_1"], MARKERS["stage_alpha_2"],
                          MARKERS["record_alpha"], MARKERS["log_alpha_1"], MARKERS["log_beta"],
                          MARKERS["shared"], MARKERS["code_alpha"]],
            "system_must_contain": [MARKERS["router"]],
        },
        {
            "id": "shared_and_record",
            "description": "Shared protections + durable record: task boards and logs stay out.",
            "user": "Work on task alpha_probe as Executor: refresh shared protections, then read the durable task record.",
            "turns": [
                {"tool_calls": [{"name": "read", "arguments": {"path": paths["shared_abs"]}}]},
                {"tool_calls": [{"name": "read", "arguments": {"path": paths["record_alpha_abs"]}}]},
                {"content": "Protections refreshed; record read."},
            ],
            "allowed": [MARKERS["router"], MARKERS["shared"], MARKERS["record_alpha"]],
            "forbidden": [MARKERS["board_alpha"], MARKERS["board_beta"], MARKERS["stage_alpha_1"],
                          MARKERS["stage_alpha_2"], MARKERS["stage_beta"], MARKERS["log_alpha_1"],
                          MARKERS["log_alpha_2"], MARKERS["log_beta"], MARKERS["workflow"]],
            "system_must_contain": [MARKERS["router"]],
        },
    ]


def baseline_scenario(paths):
    """Fixture WITHOUT blueberry assets: single response; nothing fixture-specific allowed."""
    return {
        "id": "baseline",
        "description": "No blueberry assets: system prompt must not contain the router.",
        "user": "Explain in one sentence what the VALUE constant in pkg/beta.py is for. Do not read any files.",
        "turns": [{"content": "It is a fixture marker constant."}],
        "allowed": [MARKERS["code_beta"]],
        "forbidden": [MARKERS["router"], MARKERS["board_alpha"], MARKERS["board_beta"],
                      MARKERS["workflow"], MARKERS["shared"]],
        "system_must_forbid": [MARKERS["router"]],
        "system_must_contain": [],
    }
