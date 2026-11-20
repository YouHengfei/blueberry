# <Task title>

Task ID: `<task_id>` · Outcome: in progress / solved / partial / rejected / cancelled

## At a glance

What was wrong, what changed, did it work, and where is the proof? Keep this opening
short enough for a human or a fresh agent to understand without reading the history.

## Problem and scope

- Impact, starting point, goals and non-goals.
- Relevant project rules and dependencies (links, not copies).

## Cause and solution

- Supported explanation; distinguish measured facts from remaining hypotheses.
- Changes and why they address the problem.
- Important alternatives rejected, with reasons and evidence.

## Stages and revisions

| Stage | Plan / findings | Tested code revision | Outcome |
|---|---|---|---|

Stage documents are optional for small tasks. Keep local checkpoint references
reachable through history rewriting; a moving branch name is not test provenance.

## Validation

| Check | Code / config / environment | Baseline | Result | Acceptance / exception |
|---|---|---|---|---|

Unchanged baseline failures are not passing tests. Incomparable evidence is
inconclusive. State what was not tested; do not turn partial evidence into acceptance.

## Reproduce

Prerequisites, immutable code/config inputs, commands and expected observations.
Do not store credentials or unredacted sensitive logs, even in local Git history.

## Evidence manifest

| Artifact / real workspace | Retained or intentionally removed | Provenance / checksum | Purpose |
|---|---|---|---|

Retained raw outputs normally stay outside Git. If removed, record the conclusion,
removal disposition and verification limitations; do not leave misleading live links.

## Limitations and follow-up

Open risks, constraints and useful next questions. Promote supported engineering
knowledge into the project's existing docs only after approval; do not duplicate this
entire investigation there.

## Closure

- Planner/user acceptance and any explicit exceptions:
- Keep / promote / delete / defer disposition and approval:
- Cross-task dependencies and retained evidence registrations:
- Owned jobs stopped / reservations released:
- Publication candidate and validation (if authorized); otherwise local only:
