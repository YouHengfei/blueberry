# Coordination helper

`coord.py` is a Python 3.10+ standard-library CLI for cooperative Markdown updates.
Copy this directory to `.coworkers/tools/` after setup approval. No installer,
daemon, provider call, workload runner, Git mutation or deletion engine is included.

## Preconditions and limits

- Use one verified real canonical root, with the same namespace mappings for all
  participants. Local POSIX filesystems only; network/distributed filesystems and
  Windows locking are not validated. Setup must verify suitability; the helper
  does not detect every network filesystem or make distributed guarantees.
- Every coordination writer uses the helper (including human edits via update), or
  pauses all writers. Advisory locks do not prevent direct writes by other tools.
- This is not an authorization/security boundary. Session IDs are ownership labels,
  not credentials. Do not impersonate an owner. The protocol assumes cooperating users.
- No symlink parents/destinations, hardlinked targets, or cross-device coordination
  subtrees. Only the project entry point, task state boards, and shared board may be
  written. Durable records and code use normal editing/version control.
- Atomic replacement is per file, not a transaction across boards/indexes. Shared
  claims are wholly in one file. Board text remains human-reviewed; the helper does
  not validate acceptance, state transitions, physical availability or artifact safety.

## Select a root explicitly

From the task workspace, use the root recorded in its `COWORKERS.md`:

```bash
python /path/to/coord.py --root /real/coordination/root snapshot COWORKERS.md
python /path/to/coord.py --root /real/coordination/root snapshot .coworkers/state/tasks/example_task.md
```

The examples use placeholders, not a discovery algorithm. A missing board returns
`{"revision":"missing","content":null}` without creating it. Request setup/creation
approval first. Snapshot returns JSON with UTF-8 content and a SHA-256 revision.

## Update a board

Prepare the desired full Markdown content from the snapshot, preserving others'
entries, then send it on stdin with the exact revision you read:

```bash
python /path/to/coord.py --root /real/coordination/root \
  update .coworkers/state/tasks/example_task.md --expected <snapshot-sha256> < proposed.md
```

`--expected missing` permits deliberate creation from an approved template, not
silent initialization. Do not commit temporary proposal files or leave them in scratch.
No-op updates preserve content. Boards are limited to 2 MiB to bound mistakes.

Inside a short lock, the helper rereads, checks the revision, then atomically replaces
and fsyncs the file. It never holds a lock while a model thinks or while a job runs.
If the revision is stale: snapshot again, merge deliberately, and submit the new
revision. Do not just substitute a fresh hash into an old replacement.

Generic shared-board updates may change namespaces/protections/decisions but cannot
change claim data. Malformed claims fail closed; do not replace a broken table with
an empty one. Escalate recovery, verify owners, pause writers, and preserve evidence.

## Claim, annotate, release

Create the approved task state board and shared board first. Map logical namespaces
to real hosts/workspaces in shared.md. IDs are case-sensitive, slash-separated,
without dot/empty segments, spaces, commas or pipes. Allowed segment characters:
letters, digits, underscore, dot, colon and hyphen. Aliases are not resolved for you.
A parent conflicts with all descendants, but `.../1` does not conflict with `.../10`.

```bash
python /path/to/coord.py --root /real/coordination/root claim \
  --task example_task --session executor-1 \
  --resource host/worker_a/device/0 --resource host/worker_a/port/tcp/8000 \
  --job 'planned run; log local_tests/example_task/run_01/logs/server.log'
```

The entire resource set is checked and recorded under the shared-board lock, or none
is claimed. The returned random claim ID identifies that set. Every claim is exclusive;
parent/child duplicates within the requested set are also rejected. Verify live occupancy
before claiming and again before launch as appropriate: unmanaged processes do not use
this protocol. Reserve workspace scratch scopes while producing/cleaning those outputs.

```bash
python /path/to/coord.py --root /real/coordination/root annotate \
  --task example_task --session executor-1 --claim <claim-id> \
  --job 'PID 1234; verified start identity; port 8000; log path'
# Only after the owned job has stopped:
python /path/to/coord.py --root /real/coordination/root release \
  --task example_task --session executor-1 --claim <claim-id>
```

Session labels use letters/digits plus underscore, dot, colon or hyphen (<=128
characters, starting alphanumeric); record the role separately from that identity.
Cells must be single-line, unpadded, <=512 characters and contain no pipe/control
characters. Resources in a row are separated by comma-space. The helper owns the
marked table format; use updates outside it for longer job/protection notes.

## Contention and recovery

Exit codes: **0** success, **2** invalid state/input/I/O, **3** stale revision,
ownership mismatch or resource conflict, **4** busy lock. Operational errors are JSON
on stderr; argparse usage errors use standard CLI diagnostics. Success is JSON on stdout. `--timeout` is a bounded 0..30-second lock wait (default 2).
A failure after filesystem replacement/fsync may mean the new state was written:
always snapshot before retrying an I/O failure; never assume rollback.

OS locks disappear on process exit/crash; claim rows do not. Persistent `.lock` files
are normal and must never be unlinked to "unlock" a board (that could create two lock
inodes). There are no leases, automatic expiry, force-steal, process-kill or cleanup
commands. Resolve stale claims with owners/user and live job evidence. Document explicit
human recovery approval before releasing with a dead owner's recorded identity.

Interrupted writes may leave `.coord-*` temporary files; inspect/remove only during an
approved paused-writer maintenance window. A crash around replace exposes old or new
content, not a deliberately half-written board. Do not run the helper on unsupported
filesystems and infer stronger durability/concurrency guarantees from these mechanisms.
