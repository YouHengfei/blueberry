---
name: <skill-name>            # lowercase-hyphens, ≤64 chars; match the directory name
description: >-               # what it does + WHEN to use it; this drives routing. Required.
  Do X. Use when Y.
disable-model-invocation: true # explicit invocation only; command syntax depends on the harness
---

# <Skill title>

One paragraph: what this skill accomplishes and any preconditions (e.g. "read
docs/x.md first").

## Steps

1. Concrete, command-level steps. Paths relative to the skill directory for
   bundled files.

## Rules / Safety rails

- Hard limits, things to never do, and when to stop and ask the user.

## Report

- What changed in the selected task state/record; append a handoff at the bottom
  only for a durable outcome. Use revision-checked coordination updates. Do not
  touch other task boards or silently expand from task to project-wide scope.
