# Coordination helper (`coord.py`)

Python 3.10+ stdlib CLI for atomic board updates, task lifecycle and exclusive resource
claims on local POSIX filesystems (no daemon, network-FS guarantee, or process control).
Copy to `.coworkers/tools/`.

## Rules and limits

- `--root` defaults to the Git common repo root (works from linked worktrees); pass
  `--root` outside Git. No symlinks, hardlinks, or cross-device subtrees.
- Allowed state targets: `COWORKERS.md`, `.coworkers/state/shared.md`,
  `.coworkers/state/tasks/<task_id>.md` (≤2 MiB UTF-8). All writers must cooperate.
- Short advisory locks only during writes (never while running jobs). Generic `update`
  on `shared.md` cannot edit claims; malformed claims fail closed.
- IDs: `task` snake_case ≤64 chars; `session` `[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}`;
  resources slash-separated case-sensitive namespaces (parent/child conflict; aliases
  not resolved); cells single-line ≤512 chars, no `|` or control chars.

## Commands

```bash
# Cross-task dashboard (read-only; json or text)
python3 .coworkers/tools/coord.py status --format text

# Create approved task board + record README + COWORKERS.md row
python3 .coworkers/tools/coord.py init-task --task <id> --goal '<summary>' --planner <role/session>

# Atomic append handoff/decision + optional state/next update (no full-file rewrite)
python3 .coworkers/tools/coord.py handoff --task <id> --by <role/session> --state review --next '<owner — action>' --msg '<outcome>' --print-prompt
python3 .coworkers/tools/coord.py decide  --task <id> --by <role/session> --msg '<decision; rationale; evidence>'

# Close task after releasing claims and recording durable README (removes index row)
python3 .coworkers/tools/coord.py close-task --task <id> --by <role/session> --verdict '<accepted summary>' --disposition '<keep/delete>'

# Low-level snapshot & CAS update (--expected missing for approved creation)
python3 .coworkers/tools/coord.py snapshot .coworkers/state/tasks/<id>.md
python3 .coworkers/tools/coord.py update <target> --expected <sha256|missing> < proposed.md

# Exclusive all-or-nothing claims, live job annotation, and release after job stops
python3 .coworkers/tools/coord.py claim    --task <id> --session <session> --resource <ns1> --job '<summary>'
python3 .coworkers/tools/coord.py annotate --task <id> --session <session> --claim <claim-id> --job '<PID/port/log>'
python3 .coworkers/tools/coord.py release  --task <id> --session <session> --claim <claim-id>
```

## Exit codes and recovery

- **0** success (JSON stdout) · **2** invalid input/state/I/O · **3** stale revision,
  ownership mismatch, active claims, or resource conflict · **4** busy lock (`--timeout 0..30`).
- On exit 3 or I/O failure: `snapshot` afresh and merge—never replay an old body.
- Never unlink `.coworkers/state/locks/*.lock`. OS locks clear on crash; claim rows stay.
  Stale release needs owner/user approval + evidence. Clean `.coord-*` only when paused.
