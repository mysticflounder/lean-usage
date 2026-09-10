# Build performance

Use this reference for build budgets, timing records, elaboration profiling, and
sharding decisions. For generated-proof emitters and artifact archival, read
[generated-proofs.md](generated-proofs.md).

## Contents

- [Budget](#budget)
- [Heartbeat policy](#heartbeat-policy)
- [Timing records](#timing-records)
- [Profile before optimizing](#profile-before-optimizing)
- [Shard deliberately](#shard-deliberately)
- [A/B method](#ab-method)

## Budget

With mathlib oleans warm, use the wrapper defaults as warning signals:

- `<= 10 min`: no default duration warning;
- `10–30 min`: profile and watch the slow tail;
- `> 30 min`: refactor/shard candidate.

These are default warning thresholds (`LAKE_BUILD_TARGET_S=600`,
`LAKE_BUILD_CEIL_S=1800`), not health guarantees or permission to override a
project-specific budget. Changing the variables changes the nudge; it does not
make a regression healthy.

Measure a project's own modules on a reasonably quiet host. A cold mathlib build
is a cache/setup failure, and host contention distorts wall time.

## Heartbeat policy

Heartbeat exhaustion means an elaboration/tactic budget was consumed; it is not a
recursion-depth diagnosis and a larger number is not proof progress.

Apply this order:

1. Read and honor the repository's cap or prohibition. Do not raise a limit merely
   because the generic/default limit is lower.
2. Reproduce and measure the affected declaration with the pinned toolchain. Identify
   whether elaboration, tactic execution, typeclass synthesis, term size, imports, or
   generated payload is responsible.
3. Refactor, simplify, narrow imports/search, split a meaningful declaration, or shard
   generated work before increasing the budget.
4. If a higher limit remains necessary and local policy permits it, use the smallest
   measured **finite**, declaration-scoped override. Record the baseline, measurement,
   chosen value, reason, and removal/review condition beside the declaration or in the
   repository's performance record.
5. Rebuild the original consumer and confirm statement, axiom, and trust closure are
   unchanged. A scoped resource exception does not waive promotion gates.

Distinguish the options:

- `maxHeartbeats` bounds the declaration's overall Lean heartbeat budget.
- `synthInstance.maxHeartbeats` bounds typeclass-instance synthesis and is appropriate
  only when measurement identifies instance search as the exhausted sub-budget.

Do not substitute one for the other blindly. `maxHeartbeats 0` disables the heartbeat
limit and is never the house default. Permit it only as an exceptional, measured,
locally approved policy for generated/certificate workloads whose surrounding time,
memory, input identity, and replay scope are independently bounded. Remove it when
structural fixes make a finite limit viable. Hand-written proofs should use a finite
bound or be refactored unless the repository records a specific exception.

## Timing records

`lake-build` appends one JSON object per invocation to:

```text
~/.local/state/lean-usage/build-stats.jsonl
```

Override the directory with `LEAN_USAGE_STATE_DIR`. A record contains timestamp,
Lake root, arguments, duration, exit code, an activity count, requested memory
setting, a `build_id`, the build-log path, and `interrupted`. `recompiled` counts
Lake's build-activity lines —
`Built`, `Building`, and `Compiling`, with or without warnings. It is an activity
count, not a count of distinct modules: one module can contribute more than one
line. `0` marks a fully-cached no-op (Lake is content-hash based), distinguishing
a fast cached build from a fast real one. For a module count, use the
`module-build-stats.jsonl` rows that carry the same `build_id`. `duration_s` is the
elapsed Lake build phase, from launching Lake until it returns; it excludes cache
prefetch, lock/setup work, temporary-shim setup, and teardown. `memory_mb` is the
requested `MEMORY_MB` value, not an observed or guaranteed effective cap.
`interrupted` is `true`
when the build was stopped by a signal (Ctrl-C / SIGTERM) before Lake returned;
such a record is partial — `duration_s` is the elapsed time so far, `exit_code`
is `128 + signum`, and `recompiled` counts only what finished. Records written
before a field was added omit it.

```json
{"ts":"2026-06-21T18:03:11Z","project":"/path/to/lean","args":"lake build Foo","duration_s":742,"exit_code":0,"recompiled":38,"memory_mb":16384,"build_id":"12345-1785209288","build_log":"/path/to/lean/.lake/lake-build-logs/12345-1785209288.log","interrupted":false}
```

Each wrapper invocation writes one line, but different projects are not protected
by a shared lock. Treat concurrent cross-project appends as best-effort and validate
JSON before relying on the file as a database.

```bash
jq -s 'map(select(type == "object")) | sort_by(-.duration_s) | .[:10]' \
  ~/.local/state/lean-usage/build-stats.jsonl
```

### Per-module build times

Alongside the per-build file, `lake-build` records each module's own build time to:

```text
~/.local/state/lean-usage/module-build-stats.jsonl
```

One record per `✔`/`⚠ [k/n] Built <module> (Ns)` progress line Lake emits — the
`duration_s` is Lake's own reported wall-clock for that module, `warnings` is
`true` for a `⚠` (built-with-warnings) line, and `build_id` joins back to the
per-build record above. Records are written and flushed as each module finishes,
so an interrupted build keeps the times for every module that completed before
the stop. Cached modules produce no line and therefore no record. Disable with
`LAKE_BUILD_NO_MODULE_STATS`.

```json
{"ts":"2026-06-21T18:02:29Z","build_id":"12345-1785209288","module":"Foo.Bar","duration_s":3.7,"warnings":false}
```

The slowest modules in the most recent build:

```bash
b=$(jq -rs 'map(select(type=="object"))|last|.build_id' \
  ~/.local/state/lean-usage/build-stats.jsonl)
jq -s --arg b "$b" \
  'map(select(type=="object" and .build_id==$b))|sort_by(-.duration_s)|.[:10]' \
  ~/.local/state/lean-usage/module-build-stats.jsonl
```

## Profile before optimizing

Direct Lean is an explicit profiling exception to the normal `lake-build` rule.
Dependencies must already be built, and no same-project build may run concurrently.
Preserve any explicitly pinned resource flags from the project's normal invocation
when profiling (for example `-M` and `-j`); changing them measures a
different workload. Add only the profiler switch and the resource-monitor command.

```bash
cd <lake-root>
# macOS:
/usr/bin/time -l lake env lean -Dprofiler=true path/to/File.lean
# Linux (GNU time; install it if needed):
/usr/bin/time -v lake env lean -Dprofiler=true path/to/File.lean
```

Alternatively, scope `set_option profiler true` in source while investigating and
remove it after recording the result.

Read the cumulative profiler by bucket:

| Bucket | Typical cause | First response |
|---|---|---|
| `import` | broad transitive imports | replace umbrella imports with the narrowest stable imports |
| `elaboration` | large/deep terms, many metavariables | split terms and simplify interfaces |
| `tactic execution` | flexible/heavy tactics | use more direct terms or smaller tactic blocks |
| `typeclass inference` | repeated synthesis in hot code | hoist instances or simplify representations |
| `instantiate metavars` | deep sharing/substitution | reduce term depth and factor declarations |
| `linting` | generated warning volume | fix the emitter; use only justified specific suppressions |

Compare CPU (`user + sys`) for single-file elaboration; wall time is useful for the
whole build but is sensitive to host contention.

## Shard deliberately

Lake parallelizes across modules, not inside one declaration/file. Shard when a
single module dominates incremental rebuilds or elaboration grows super-linearly.
A useful default review signal is `> 60 s` single-file CPU, but source shape and
project policy decide the actual threshold.

Before sharding certificate replay, check whether the real bottleneck is a giant
inline CNF or certificate literal elaborated before replay starts. In that case,
use the compact/runtime-ingress and checkpointed-replay procedure in
[generated-proofs.md](generated-proofs.md#bank-large-sat-certificates); later
proof-step shards alone will not remove the front-loaded cost.

Good shard boundaries:

- independently meaningful lemmas;
- certificate steps or clause batches;
- generated payload separated from hand-written checker/soundness code;
- a thin coordinator that imports and composes the shards.

Also inspect broad imports before multiplying tiny files: import-bound shards can
make total CPU worse even if wall-clock parallelism improves.

For the mechanics of a split — rendered-byte budgets, block boundaries, the
manifest, re-sharding, and validation — read [sharding.md](sharding.md).

## A/B method

1. Choose representative modules from the median and slow tail.
2. Record toolchain, source hash, CPU, wall time, peak memory, and profiler buckets.
3. Change one factor.
4. Rebuild the same artifacts on comparable host load.
5. Compare bucket deltas and verify theorem/axiom closure is unchanged.

For generated source, regenerate twice and require byte-identical output before
interpreting cache or timing results.
