# blueberry

This repository is for building an agentic development workflow for specific scenarios.

## Private agentic toolkit layout

Use `/toolkit` as the home for your private reusable assets:

- `/toolkit/general/`: cross-repository assets (global system prompts, shared skills, reusable templates)
- `/toolkit/specific/`: repository-local assets split into:
  - `repo-specific/` for repository-level prompts and workflows
  - `agent-specific/` for code-agent-targeted prompts (for example, `pi`)

Start with `/toolkit/README.md` for structure and maintenance guidance.
