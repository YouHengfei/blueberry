# Coordination helper (`coord.py`)

Python 3.10+ stdlib CLI for atomic, revision-checked Markdown board updates and exclusive
resource claims on local POSIX filesystems (no daemon, network-FS guarantee, or process
control). Copy to `.coworkers/tools/`.

## Rules and limits

- Use one real canonical `--root` (no symlinks, hardlinks, or cross-device subtrees).
- Allowed targets only: `COWORKERS.md`, `.coworkers/state/shared.md`,
  `.coworkers/state/tasks/<task_id>.md` (≤2 MiB UTF-8). All writers must cooperate.
- Short advisory locks only during file writes (never held while thinking or running jobs).
  Generic `update` on `shared.md` cannot modify claims; malformed claims fail closed.
- IDs: `task` snake_case ≤64 chars; `session` `[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}`;
  resources slash-separated case-sensitive namespaces (parent/child conflict; aliases are
  not resolved); cells single-line ≤512 chars, no `|` or control chars.

## Commands

```bash
# Snapshot (read-only; missing returns {"revision":"missing","content":null})
python3 .coworkers/tools/coord.py --root <root> snapshot COWORKERS.md
python3 .coworkers/tools/coord.py --root <root> snapshot .coworkers/state/tasks/<id>.md

# Revision-checked create/update (--expected missing for approved creation; stdin = full file)
python3 .coworkers/tools/coord.py --root <root> update <target> --expected <sha256|missing> < proposed.md

# All-or-nothing exclusive claims (task & shared boards must exist; verify live occupancy first)
python3 .coworkers/tools/coord.py --root <root> claim \
  --task <id> --session <session> --resource <ns1> --resource <ns2> --job '<summary>'

# Annotate live job metadata / release after owned job stops
python3 .coworkers/tools/coord.py --root <root> annotate --task <id> --session <session> --claim <claim-id> --job '<PID/port/log>'
python3 .coworkers/tools/coord.py --root <root> release  --task <id> --session <session> --claim <claim-id>
```

## Exit codes and recovery

- **0** success (JSON stdout) · **2** invalid input/state/I/O · **3** stale revision,
  ownership mismatch, or resource conflict · **4** busy lock (`--timeout 0..30`, default 2).
- On stale revision (exit 3) or I/O failure: always `snapshot` afresh and merge—never
  assume rollback or replay an old body with a new hash.
- Never unlink persistent `.coworkers/state/locks/*.lock` files. OS locks clear on crash;
  claim rows persist. Stale claim release requires owner/user approval + live evidence
  recorded in the task record. Clean leftover `.coord-*` temp files only in a paused window.
