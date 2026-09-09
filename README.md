# lean-usage

Lean 4 build governance for AI coding agents, packaged as a Claude Code and
Codex plugin marketplace, together with the engineering report that documents
what these conventions did for Lean build throughput across several
formalization projects.

**Report:** [Faster Lean verification with controlled memory and CPU](docs/reports/2026-09-07-lean-optimization-report.md)
([PDF](docs/reports/2026-09-07-lean-optimization-report.pdf)) — Adam McKenna, 7 September 2026.
The report cites the plugin sources in this repository, so its links resolve here.

## What is in the box

| Component | Path | Purpose |
|---|---|---|
| `lake-build` wrapper | `plugins/lean-usage/bin/lake-build` | Global Lake build entry point: walks up to the lakefile, serializes top-level builds with a stale-PID-aware lockfile, prefetches the mathlib binary cache, caps each `lean` worker's memory through a PATH shim, and records per-build and per-module timing to JSONL logs. |
| Guard hooks | `plugins/lean-usage/hooks/` | Deploys the wrapper at session start, warns on direct `lake`/`lean` invocations, and blocks builds when the mathlib cache is missing or stale. |
| Skills | `plugins/lean-usage/skills/` | See the table below. |
| Report and data | `docs/reports/` | The report, its PDF rendering, the weekly chart, and the CSV files behind it. |
| Example wrapper | `examples/lake-build-example` | A portable, trimmed version of the wrapper for adoption elsewhere. See below. |

## Plugin hooks

Hooks run automatically at host lifecycle events; they are separate from the
model-invoked skills.

| Host/event | Hook behavior |
|---|---|
| Claude `SessionStart` | Keeps `~/.local/bin/lake-build` pointed at the active wrapper via [`sync-lake-build.py`](plugins/lean-usage/hooks/sync-lake-build.py). |
| Claude `PreToolUse` (Bash) | Warns on direct `lake`/`lean` calls via [`lean-direct-warn.py`](plugins/lean-usage/hooks/lean-direct-warn.py) and denies recognized mathlib builds with a missing or stale cache via [`mathlib-cache-check.py`](plugins/lean-usage/hooks/mathlib-cache-check.py). |
| Codex `SessionStart` | Synchronizes the `lake-build` wrapper. |
| Codex `PreToolUse` (Bash) | Applies the same direct-build warning and mathlib-cache guard. |

Claude registers these in [`hooks/hooks.json`](plugins/lean-usage/hooks/hooks.json);
Codex registers them in [`codex-hooks.json`](plugins/lean-usage/codex-hooks.json).
The hook commands use `uv` and the host-provided plugin root, so they do not
depend on Homebrew or a fixed checkout path.

## Skills

| Skill | Command | Description |
|-------|---------|-------------|
| Lean Usage | `/lean-usage:lean-usage` | House governance for Lean 4 repositories: the `lake-build` workflow, project-indexed theorem reuse, proof obligations and tractability, axiom/native/external-evidence trust audits, promotion and publication. References cover build operations, build performance, generated proofs, proof discipline, code quality, vendoring, and the worker promotion contract. |
| Lean Shard | `/lean-usage:lean-shard` | Split a large Lean source file into bounded helper shards plus a thin coordinator; wraps the `lean-shard` CLI (plan/apply/normalize, TOML policy, manifest, re-sharding). |
| DRAT to Lean | `/lean-usage:drat-to-lean` | Encode a claim to CNF, solve with CaDiCaL, trim to LRAT, and emit a kernel-checked Lean 4 proof. |

The `lean-shard` and `drat-to-lean` CLIs that these skills drive are not part of this repository.

## Telemetry

The wrapper writes two JSONL logs under `~/.local/state/lean-usage/`
(override with `LEAN_USAGE_STATE_DIR`):

- `build-stats.jsonl` — one row per invocation: timestamp, project, arguments, wall time, exit code, memory, recompile-activity count, build ID, interruption flag, log path.
- `module-build-stats.jsonl` — one row per module compile, read from Lake's `Built <module> (Ns)` progress lines, joinable to the invocation through `build_id`.

The report's compile-cost figures come from the second log. Whole-run wall
times are not a cost measure, because a run's record does not say how much of
the project it rebuilt; the report explains this in its timing section.

## Example wrapper

`examples/lake-build-example` is a self-contained Python script, based on the
production wrapper, that keeps the parts behind the report's telemetry and
drops the house-specific telemetry, session identity, and hook deployment. It
needs only Python 3 and a Lean toolchain on
`PATH`. From anywhere inside a Lake project:

```
examples/lake-build-example              # lake build
examples/lake-build-example Foo.Bar      # lake build Foo.Bar
MEMORY_MB=8192 examples/lake-build-example
```

It walks up to the lakefile, takes a stale-PID-aware lock per project, keeps
the live output in `.lake/lake-build-logs/`, caps each `lean` worker's memory
through a PATH shim, runs `lake exe cache get` first for mathlib projects and
refuses to build if that fails, and writes the same two JSONL logs as the
production wrapper. Its header comment documents every environment variable and
gives `jq` recipes for reading the logs.

## Install

Claude Code:

```
/plugin marketplace add mysticflounder/lean-usage
/plugin install lean-usage
```

Codex reads `.agents/plugins/marketplace.json`. Its hook file,
`plugins/lean-usage/codex-hooks.json`, resolves scripts through the installed
plugin root and does not require a checkout-specific path.

Requirements: macOS or Linux, Python 3 through `uv`, `jq`, Lean 4 with Lake,
and `lake exe cache` for mathlib projects.

## Tests

```
scripts/test.sh
```

This checks that every plugin's Claude and Codex manifests carry the same
version, then runs the wrapper's lock, shim, and telemetry tests.

## Provenance

The plugin sources are a snapshot of the private `local-plugins` marketplace
at commit `dc1a00a`. The report was written against that marketplace's commit
`983f660`; line anchors in the report were re-pointed to the files in this
repository.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).

Contributions, including responsibly reviewed AI-assisted contributions, are
welcome under the policy in [CONTRIBUTING.md](CONTRIBUTING.md).
