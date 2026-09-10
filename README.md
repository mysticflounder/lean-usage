# lean-usage

> **WARNING: EXPERIMENTAL AI SOFTWARE — USE AT YOUR OWN RISK.** This early-alpha
> plugin includes AI-assisted code and instructions that can be wrong or unsafe.
> Hooks can execute commands and change local files automatically. To the fullest
> extent permitted by law, no warranty is provided and liability is disclaimed.
> Review the [risk notice and full disclaimer](plugins/lean-usage/DISCLAIMER.md)
> before installation or use. Keep backups and independently verify all results.

Lean 4 build governance for AI coding agents, packaged as a Claude Code and
Codex plugin marketplace, together with the engineering report that documents
what these conventions did for Lean build throughput across several
formalization projects.

## Introduction

Developed from about five months of AI session logs from attempts to solve and
formalize open mathematical problems, lean-usage collects practical guidance for authoring and maintaining
Lean projects: theorem reuse, profiling, generated certificates, sharding,
certificate-bank freezing, Lean/mathlib upgrades, and proof trust audits. It
complements a general Lean skill; the specialized sharding and certificate-generation
workflows require separately supplied tools.

The included `lake-build` wrapper coordinates same-project builds, fetches the
mathlib cache, captures logs and timing, and records caller session/pane metadata
when available. Companion hooks warn about direct builds and guard against
accidental edits to the deployed wrapper. These are workflow safeguards, not hard
CPU/memory limits or security boundaries. This is an early alpha, released under
GPL-3.0-or-later; human-reviewed, AI-assisted contributions and issue reports are
welcome.

**Report:** [Faster Lean verification with controlled memory and CPU](docs/reports/2026-09-07-lean-optimization-report.md)
([PDF](docs/reports/2026-09-07-lean-optimization-report.pdf)) — Adam McKenna, 7 September 2026.
The report cites the plugin sources in this repository, so its links resolve here.

## What is in the box

| Component | Path | Purpose |
|---|---|---|
| `lake-build` wrapper | `plugins/lean-usage/bin/lake-build` | Global Lake build entry point: walks up to the lakefile, serializes top-level builds with a stale-PID-aware lockfile, prefetches the mathlib binary cache, requests each `lean` worker's memory setting through a PATH shim (Lake may bypass the shim by invoking an absolute compiler path), and records per-build and per-module timing to JSONL logs. |
| Guard hooks | `plugins/lean-usage/hooks/` | Deploys the wrapper at session start, warns on direct `lake`/`lean` invocations, and blocks builds when the mathlib cache is missing or stale. |
| Skills | `plugins/lean-usage/skills/` | See the table below. |
| Report and data | `docs/reports/` | The report, its PDF rendering, the weekly chart, and the CSV files behind it. |

## Plugin hooks

Hooks run automatically at host lifecycle events; they are separate from the
model-invoked skills.

| Host/event | Hook behavior |
|---|---|
| Claude and Codex `SessionStart` | Supplies an absolute wrapper invocation to the agent and maintains an optional `~/.local/bin/lake-build` symlink via [`sync-lake-build.py`](plugins/lean-usage/hooks/sync-lake-build.py). No PATH setup is needed. |
| Claude and Codex `PreToolUse` (Bash, run_command, exec_command) | Warns on direct `lake`/`lean` calls via [`lean-direct-warn.py`](plugins/lean-usage/hooks/lean-direct-warn.py) and denies recognized raw mathlib builds with a missing or stale cache via [`mathlib-cache-check.py`](plugins/lean-usage/hooks/mathlib-cache-check.py). Managed wrapper calls proceed to their own cache prefetch. |
| Claude and Codex `PreToolUse` (file edits, patches, shell commands) | [`protect-lake-build.py`](plugins/lean-usage/hooks/protect-lake-build.py) denies direct edits and recognized shell writes to the managed `~/.local/bin/lake-build`; edit the plugin source instead. |

Claude registers these in [`hooks/hooks.json`](plugins/lean-usage/hooks/hooks.json);
Codex registers them in [`codex-hooks.json`](plugins/lean-usage/codex-hooks.json).
The hook commands use `uv` and the host-provided plugin root, so they do not
depend on Homebrew or a fixed checkout path.

Claude Code runs these hooks automatically when the installed plugin is enabled;
there is no separate per-hook approval step. Codex applies its hook trust and
enablement controls. Installing/enabling the plugin in Claude therefore enables
the command execution and local-file effects described above, including the
SessionStart symlink. See [Claude's plugin hook reference](https://code.claude.com/docs/en/plugins-reference#hooks).
SessionStart also emits an experimental-software warning through the host's
hook message output; this is a notice, not an approval prompt.

The edit guard recognizes
common write operations; it is a workflow aid, not an operating-system security
boundary. SessionStart preserves an unexpected regular file at the deployment
path instead of overwriting local work.

## Skills

### Companion Lean 4 plugin

We use the `lean4` plugin from
[mysticflounder/lean4-skills](https://github.com/mysticflounder/lean4-skills), a fork
of [Cameron Freer's lean4-skills](https://github.com/cameronfreer/lean4-skills).
Install it separately for general Lean proof development, tactic selection,
proof-state inspection, and theorem search. This plugin complements it with build
coordination, evidence and rigor standards, and project-governance guidance; the
companion plugin is not bundled here. See its repository for installation instructions.

### Included skills

| Skill | Command | Description |
|-------|---------|-------------|
| Lean Usage | `/lean-usage:lean-usage` | House governance for Lean 4 repositories: the `lake-build` workflow, project-indexed theorem reuse, proof obligations and tractability, axiom/native/external-evidence trust audits, promotion and publication. References cover build operations, build performance, generated proofs, proof discipline, code quality, sharding, vendoring, and the worker promotion contract. |
| Lean Shard | `/lean-usage:lean-shard` | Split a large Lean source file into bounded helper shards plus a thin coordinator; wraps the `lean-shard` CLI (plan/apply/normalize, TOML policy, manifest, re-sharding). |
| DRAT to Lean | `/lean-usage:drat-to-lean` | Drive a compatible external CNF/DRAT/LRAT pipeline and emit candidate Lean proofs. Output may contain `sorry`; replay, semantic-bridge checks, and a final-consumer trust audit are required. |

The `lean-shard` and `drat-to-lean` CLIs that these skills drive are not part of this repository.
Their skills require a compatible executable or checkout supplied by the user;
this plugin does not install them. Tool-neutral splitting guidance is included in
[sharding.md](plugins/lean-usage/skills/lean-usage/references/sharding.md).
For certificate custody and replay handoff, see
[freezing-certificate-banks.md](plugins/lean-usage/skills/lean-usage/references/freezing-certificate-banks.md).

## lake-build

The wrapper declines a second build while another wrapper-managed build holds the
project lock. Its diagnostic identifies the owning process and includes the caller
session, tmux pane, and retained build-log path when available. For example:

```text
$ lake-build
lake-build: another build is already running (pid 87233): /Users/adam/projects/my-project/lean/.lake/lake-build.lock (sid='8a3f1937-3bb8-4c1f-b3de-dd295a470f5d', tmux_pane='%11', build_log='/Users/adam/projects/my-project/lean/.lake/lake-build-logs/87233-1789062894654733000.log')
```

The paths and IDs above are illustrative, not installation requirements. In agent
sessions, use the PATH-independent command supplied by SessionStart in place of
the `lake-build` shorthand. Session/pane metadata describes the active lock owner;
it is not a guaranteed agent identity or a persistent session-history log.

### Telemetry

The wrapper writes two JSONL logs under `~/.local/state/lean-usage/`
(override with `LEAN_USAGE_STATE_DIR`):

- `build-stats.jsonl` — one row per invocation: timestamp, project, arguments, Lake build-phase duration, exit code, requested memory setting, recompile-activity count, build ID, interruption flag, log path. The duration excludes cache prefetch, wrapper setup, and teardown.
- `module-build-stats.jsonl` — one row per module compile, read from Lake's `Built <module> (Ns)` progress lines, joinable to the invocation through `build_id`.

The report's compile-cost figures come from the second log. Whole-run wall
times are not a cost measure, because a run's record does not say how much of
the project it rebuilt; the report explains this in its timing section.

## Install

Claude Code:

```
/plugin marketplace add mysticflounder/lean-usage
/plugin install lean-usage
```

Codex reads `.agents/plugins/marketplace.json`. Its hook file,
`plugins/lean-usage/codex-hooks.json`, resolves scripts through the installed
plugin root and does not require a checkout-specific path.

Supported platforms are macOS and Linux. Windows support is intended, but has
not yet been tested; please [open an issue](https://github.com/mysticflounder/lean-usage/issues)
if you encounter a Windows-specific problem.

Requirements: `uv` with Python 3.10+, a POSIX shell (`/bin/sh`), Lean 4 with Lake,
and `lake exe cache` for mathlib projects. Repository checks also require
Bash, `jq`, and Python 3.11+ (the tests use `contextlib.chdir`).

No `PATH` or shell-profile changes are required for the wrapper. When SessionStart
runs, it supplies the agent with a command using the absolute paths
of its working Python interpreter and the installed wrapper. The optional symlink
is only a convenience; a missing symlink or missing `~/.local/bin` on `PATH` does
not prevent the supplied command from working. For hook-disabled sessions, use
`uv run --no-project python <plugin-root>/bin/lake-build` with the installed plugin
path. Windows shell and hook integration remain untested.

## Tests

```
scripts/test.sh
```

This checks that every plugin's Claude, Codex, and compatibility manifests carry
the same version, then runs the wrapper's lock, shim, telemetry, deployed-file
edit-guard, and build-hook event tests. Synthetic hook events do not replace
live host integration testing.

For an isolated Linux test with a real Lean 4.28.0 toolchain:

```bash
bash scripts/test-docker.sh
```

This requires Docker and network access to build the test image. The test run
itself has networking disabled, mounts the checkout read-only, and uses a disposable
copy without host credentials. It runs the regression suite, installs the wrapper
through SessionStart, then checks real Lean cold/warm builds, lock cleanup, and
telemetry. The image is retained for reuse; the container is removed on exit.
This is a runtime smoke test, not a Claude/Codex agent evaluation or a real mathlib
cache-download test; cache-failure behavior is covered by regression fixtures.

## Provenance

The plugin sources are a historical source snapshot. The report was written
against an earlier source revision; line anchors in the report were re-pointed
to the files in this repository.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE), including its warranty and liability
provisions, and the [experimental-software disclaimer](plugins/lean-usage/DISCLAIMER.md).

Contributions, including responsibly reviewed AI-assisted contributions, are
welcome under the policy in [CONTRIBUTING.md](CONTRIBUTING.md).
