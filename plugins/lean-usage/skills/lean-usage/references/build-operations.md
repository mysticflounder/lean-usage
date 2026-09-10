# Build operations

Use this reference for `lake-build` behavior, host coordination, direct-Lean
exceptions, and mathlib cache. For timing/profiling, read
[build-performance.md](build-performance.md).

## Contents

- [`lake-build`](#lake-build)
- [Environment overrides](#environment-overrides)
- [Limits and concurrency](#limits-and-concurrency)
- [Direct `lake env lean` exceptions](#direct-lake-env-lean-exceptions)
- [Mathlib cache](#mathlib-cache)

## `lake-build`

`lake-build` is the normal build entrypoint. Do not create a per-project wrapper
for ordinary builds.

```bash
lake-build
lake-build Foo.Bar
lake-build --jobs 4
```

It:

- finds the Lake root by walking upward to `lakefile.toml`/`lakefile.lean`;
- lets `LEAN_ROOT` override discovery;
- uses a stale-PID-aware lock at `<lake-root>/.lake/lake-build.lock` to prevent
  concurrent top-level builds in the same project;
- puts a temporary `lean` shim on `PATH` to request the per-worker memory setting;
  Lake commonly invokes `lean` by its absolute toolchain path, which bypasses the
  shim, so this is not proof that a cap was enforced;
- runs `lake exe cache get` first in a mathlib project and refuses the build when
  that prefetch fails, so an ordinary invocation never becomes a mathlib source
  compile;
- records one per-build timing record per invocation, plus one per-module record
  (build time, warnings flag) read from Lake's `Built <module> (Ns)` output. The
  per-build duration covers the Lake build phase, not cache prefetch, wrapper
  setup, or teardown. It always removes its shim/lock — a signal interrupt still
  writes a partial
  per-build record and keeps the per-module records for modules already finished
  (see build-performance for the two JSONL files).

## Environment overrides

| Variable | Effect |
|---|---|
| `LEAN_ROOT` | Explicit Lake root. |
| `MEMORY_MB` | Requested per-`lean` memory setting in MB; default `16384`. The `memory_mb` telemetry field records this request, not an observed or guaranteed cap. |
| `LOCKFILE` | PID-lock path; default `<lake-root>/.lake/lake-build.lock`. |
| `REAL_LAKE`, `REAL_LEAN` | Explicit toolchain executables. |
| `LEAN_USAGE_STATE_DIR` | Stats directory; default `~/.local/state/lean-usage`. |
| `LAKE_BUILD_TARGET_S`, `LAKE_BUILD_CEIL_S` | Warning thresholds; defaults `600` and `1800`. They configure nudges, not a universal project policy. |
| `LAKE_BUILD_NO_MODULE_STATS` | Skip writing per-module timing records to `module-build-stats.jsonl` (the per-build `build-stats.jsonl` is still written). |
| `LEAN_USAGE_SKIP_CACHE_CHECK=1` | Turn off the plugin's cache-guard hook. It does not change the wrapper's own prefetch. |

`LEAN_USAGE_SKIP_CACHE_CHECK` is read by the plugin's cache-guard hook. Every other
variable in the table is read by the wrapper itself.

Lean and Lake must already be installed and discoverable on `PATH` (or supplied
through `REAL_LEAN` and `REAL_LAKE`). `uv` supplies Python, not a Lean toolchain;
if these prerequisites are absent, report them before attempting a build.

The SessionStart hook supplies an absolute command containing its working
Python interpreter and the installed wrapper path. Use that command wherever this
skill says `lake-build`; append target arguments normally. It works without
`~/.local/bin` or `python3` on `PATH`, including when the optional symlink cannot
be installed. Do not ask the user to edit `PATH` or shell profiles.

Claude Code activates plugin hooks automatically with the installed, enabled
plugin; it does not require separate per-hook approval. Codex applies its hook
trust and enablement controls. Where hooks do not run, use
`uv run --no-project python <plugin-root>/bin/lake-build` with the installed plugin
root. The optional `~/.local/bin/lake-build` symlink remains available for users
whose shell already resolves it; it is not an installation prerequisite.

The `protect-lake-build` PreToolUse hook denies file edits, patches, and recognized
shell writes to the deployed `~/.local/bin/lake-build`. Make wrapper changes in
`plugins/lean-usage/bin/lake-build` in the plugin source, then update the installed
plugin. Reads and normal wrapper execution remain available. Hook activation
follows the host-specific behavior above; shell recognition is heuristic, so this is a workflow aid,
not a guarantee against arbitrary writes. SessionStart also preserves an unexpected
regular file at the deployment path rather than overwriting possible local work.

## Limits and concurrency

The lock records the wrapper PID on its first line and a JSON object on its
second line, for example:

```text
12345
{"sid": "caller-session-id", "tmux_pane": "%1", "build_log": "/project/.lake/lake-build-logs/12345-1788660518.log"}
```

`sid` comes from the first nonempty environment variable in this order:
`CODEX_THREAD_ID`, `CODEX_SESSION_ID`, `OPENCODE_SESSION_ID`,
`CLAUDE_SESSION_ID`, `CLAUDE_CODE_SESSION_ID`. `tmux_pane` comes from
`TMUX_PANE`. Missing values are `null`; no shared project session file is used
to guess the caller. When another build holds the lock, the error includes its
recorded SID, pane, and build-log path. Existing PID-only locks remain readable, and metadata
does not affect stale-PID detection. The metadata is removed with the lock when
its owning build exits; builds already running keep their original lock format.

Each acquired build writes its merged Lake stdout/stderr and wrapper notices to
`lake-build-logs/<build_id>.log` beside the lock. The absolute path is printed
at startup and saved as `build_log` in both the lock metadata and the build-stats
record. Output is flushed as it arrives, so `tail -f <build_log>` works while
the lock is held. Logs remain after successful, failed, or interrupted builds;
they are not removed with the lock. A rejected busy-lock invocation does not
create a build log.

The lock serializes top-level invocations in one project. It does not:

- limit the number of workers spawned by one Lake build;
- coordinate builds in different projects;
- make `--jobs N` or `lake -Kjobs=N` a hard process cap;
- coordinate a raw `lake env lean` process with `lake-build`.

Before starting a resource-heavy build, inspect the host rather than assuming it
is idle:

```bash
pgrep -x lean | wc -l
```

On macOS, also inspect load and CPU count with:

```bash
sysctl -n vm.loadavg
sysctl -n hw.ncpu
```

On Linux, use the corresponding portable commands:

```bash
uptime
nproc
```

These are signals, not proofs: a Lean process may be unrelated, and zero Lean
processes does not imply adequate memory or I/O headroom. If another Lean build is
active, coordinate with its owner or wait. Lowering `MEMORY_MB` changes the
requested setting where the compiler receives it, but the wrapper's PATH shim may
be bypassed by Lake's absolute compiler path; it does not cap worker count.

Do not mutate source files in a running build's dependency graph and then cite
that build as validating the modified state. Rebuild after the edit.

## Direct `lake env lean` exceptions

Raw Lean is appropriate for a deliberate single-file check or profiler run; it
is not the normal project build path.

```bash
cd <lake-root>
lake env lean -M "${MEMORY_MB:-16384}" path/to/Module.lean
lake env lean -Dprofiler=true path/to/Module.lean
```

Dependencies must already be built. Do not run this concurrently with
`lake-build` in the same project.

If a generated module needs a hard single-worker build that emits `.olean` and
`.ilean` files, use or add a project-specific helper that:

1. uses the same coordination protocol as `lake-build` rather than applying
   `flock` to its PID-file path;
2. derives output paths from that project's Lake layout;
3. applies an explicit memory setting through the compiler invocation (and records
   whether that setting is actually enforced); and
4. fails if a top-level build is active.

Do not copy a hard-coded `.lake/build/lib[/lean]` path between toolchain versions;
Lake output layouts vary. A specialized helper is justified; a second general
build wrapper is not.

## Mathlib cache

`lake-build` runs `lake exe cache get` itself before a build in a mathlib project and
refuses to build from source when that prefetch fails. Through the wrapper, no manual
cache step is needed.

Run the command by hand for a build that does not go through the wrapper: a raw
`lake build`, a `lake env lean` session, or a host where the wrapper is not installed.
From the directory containing the lakefile:

```bash
lake exe cache get
```

The mathlib package must already be fetched. The cache is per project and covers
mathlib oleans only, not the project's own generated proof artifacts. Treat the
reported decompression result and the actual `.lake/packages/mathlib` build tree
as the check; do not charge a cold from-source mathlib compile to the project's
normal build budget.

The plugin also ships a pre-tool hook that denies a recognized raw build or direct-Lean
command when the mathlib cache is empty or its oleans predate the pinned toolchain.
That hook depends on the host running the plugin's hooks, so treat it as a
convenience, not as the guarantee. Managed `lake-build` invocations are allowed
through so their own fail-closed prefetch can repair an empty or stale cache.
The wrapper's own prefetch is the part that always runs.

`LEAN_USAGE_SKIP_CACHE_CHECK=1` disables that hook alone. It does not affect the
wrapper, whose prefetch stays fail-closed. For a deliberate mathlib source compile,
call `lake build` directly, with the project's authorization for that cost.

For project-generated artifacts, read
[generated-proofs.md](generated-proofs.md). For dependency pinning and toolchain
alignment, read [vendoring.md](vendoring.md).
