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
lake-build --spine-archive              # + pack the ACTIVE spine (default: off)
```

It:

- finds the Lake root by walking upward to `lakefile.toml`/`lakefile.lean`;
- when invoked above a nested Lake tree, consults the nearest `.blueprint.toml`
  `[paths].lean_root`, then `[paths].lean_lib`;
- lets `LEAN_ROOT` override discovery;
- uses a stale-PID-aware lock at `<lake-root>/.lake/lake-build.lock` to prevent
  concurrent top-level builds in the same project;
- puts a temporary `lean` shim on `PATH` to inject the per-worker memory cap;
- records one per-build timing record per invocation, plus one per-module record
  (build time, warnings flag) read from Lake's `Built <module> (Ns)` output, and
  always removes its shim/lock — a signal interrupt still writes a partial
  per-build record and keeps the per-module records for modules already finished
  (see build-performance for the two JSONL files);
- after a successful proof-blueprint build, best-effort runs
  `proof-blueprint sync` and rewrites `docs/live-blueprint.md` (the file leads
  with `spine`'s own do-not-edit banner — the wrapper adds no header of its own);
- optionally packs the ACTIVE spine sources into a `.tar.gz` (`--spine-archive`).

The post-build proof-blueprint refresh is best-effort and does not change the
build exit code. Confirm freshness before relying on its output.

## `--spine-archive` — packing the ACTIVE spine

Off by default. `--spine-archive` and `-h`/`--help` are the only arguments the
wrapper interprets; everything else forwards to `lake build`. It is consumed
before the first `--`, so `lake-build -- --spine-archive` passes the string
through to Lake instead.

```bash
lake-build --spine-archive                       # -> <blueprint-project>/spine.tar.gz
lake-build --spine-archive=/tmp/p97.tar.gz Foo.Bar
```

The value form needs `=`; a space-separated path would be indistinguishable from
a build target. A relative PATH resolves against the blueprint project dir.

| Aspect | Behavior |
|---|---|
| Requires | A proof-blueprint project (`.blueprint.toml` at or above the Lake root) and `proof-blueprint` on `PATH`. |
| File set | `proof-blueprint spine --files` — every indexed `.lean` declaring a symbol reachable from the `[publish] target_symbol(s)`. Dead and off-spine WIP sources are excluded. |
| Also packed | `lakefile.toml`, `lakefile.lean`, `lean-toolchain`, `lake-manifest.json`, when present at the Lake root. |
| Layout | One top-level dir named for the archive; members sit at their path relative to the Lake root. Ownership is zeroed. |
| Ordering | Runs after the post-build resync, so the file set reflects the build that just finished. |
| Failed build | Skipped; the build's own exit code is returned unchanged. |
| Failed archive | Reported on stderr; an otherwise-successful run exits 1. Unlike the resync, this is not best-effort — it was explicitly requested. |

The spine file set is reachability-derived, **not import-closed**: a spine file
can import a module that contributes no reachable symbol, so that module is
absent and the tree may not build as-is. The wrapper checks and names every
unsatisfied project import after writing. Treat the archive as the active proof
source, not as a guaranteed standalone build.

## Environment overrides

| Variable | Effect |
|---|---|
| `LEAN_ROOT` | Explicit Lake root. |
| `MEMORY_MB` | Per-`lean` memory cap; default `16384`. |
| `LOCKFILE` | PID-lock path; default `<lake-root>/.lake/lake-build.lock`. |
| `REAL_LAKE`, `REAL_LEAN` | Explicit toolchain executables. |
| `LEAN_USAGE_STATE_DIR` | Stats directory; default `~/.local/state/lean-usage`. |
| `LAKE_BUILD_TARGET_S`, `LAKE_BUILD_CEIL_S` | Warning thresholds; defaults `600` and `1800`. They configure nudges, not a universal project policy. |
| `LAKE_BUILD_NO_REFRESH` | Skip proof-blueprint sync and `docs/live-blueprint.md` rewrite. Refresh manually before proof-state claims. |
| `LAKE_BUILD_NO_MODULE_STATS` | Skip writing per-module timing records to `module-build-stats.jsonl` (the per-build `build-stats.jsonl` is still written). |
| `LEAN_USAGE_SKIP_CACHE_CHECK=1` | Bypass the pre-build mathlib-cache guard for a deliberate source build. |

If `lake-build` is missing from `PATH`, restart a session with the plugin enabled
and ensure `~/.local/bin` is on `PATH`. The plugin's session hook maintains the
symlink to the active cached wrapper.

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
sysctl -n vm.loadavg        # macOS
sysctl -n hw.ncpu           # macOS
```

These are signals, not proofs: a Lean process may be unrelated, and zero Lean
processes does not imply adequate memory or I/O headroom. If another Lean build is
active, coordinate with its owner or wait. Lowering `MEMORY_MB` reduces each
worker's ceiling but does not cap worker count.

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
3. applies the same memory cap; and
4. fails if a top-level build is active.

Do not copy a hard-coded `.lake/build/lib[/lean]` path between toolchain versions;
Lake output layouts vary. A specialized helper is justified; a second general
build wrapper is not.

## Mathlib cache

From the directory containing the lakefile:

```bash
lake exe cache get
```

The mathlib package must already be fetched. The cache is per project and covers
mathlib oleans only, not the project's own generated proof artifacts. Treat the
reported decompression result and the actual `.lake/packages/mathlib` build tree
as the check; do not charge a cold from-source mathlib compile to the project's
normal build budget.

The plugin's pre-tool hook blocks recognized build/direct-Lean commands when a
mathlib dependency has no populated cache. Use `LEAN_USAGE_SKIP_CACHE_CHECK=1`
only when a source compile is intentional and its cost has been accepted.

For project-generated artifacts, read
[generated-proofs.md](generated-proofs.md). For dependency pinning and toolchain
alignment, read [vendoring.md](vendoring.md).
