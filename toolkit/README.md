# Private Agentic Toolkit

This directory helps you manage reusable prompts, skills, and workflow notes in a clean split between global and repository-local assets.

## Structure

```text
toolkit/
├── general/
│   └── README.md
└── specific/
    ├── README.md
    ├── agent-specific/
    │   └── README.md
    └── repo-specific/
        └── README.md
```

## What to place where

- `general/`
  - cross-repository system prompts
  - reusable skill definitions
  - common runbooks/checklists
- `specific/`
  - `repo-specific/`: prompts tied to this repository only, repo workflows, local constraints
  - `agent-specific/`: prompts and workflows for individual coding agents (for example, `pi`)

## Management advice

1. Keep one concept per file (for example: one skill, one prompt, one runbook).
2. Use clear file names, such as:
   - `general/system_prompt_default.md`
   - `specific/repo-specific/system_prompt_blueberry.md`
   - `specific/agent-specific/pi_system_prompt.md`
3. Add a short changelog section at the bottom of each file when the behavior changes.
4. Avoid storing secrets directly in files; reference secure secret stores instead.
