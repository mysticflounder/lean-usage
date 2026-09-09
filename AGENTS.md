# AGENTS — lean-usage

> Codex-native project doc, also imported by Claude Code via `@AGENTS.md`
> in `CLAUDE.md`. Single source of truth for agent-relevant instructions in
> this repository.

## What this is

A Claude Code and Codex plugin marketplace that packages the `lean-usage`
plugin — the global `lake-build` wrapper, its hooks, and the Lean 4 house
governance skill — together with the engineering report that describes what
the wrapper's telemetry and the skills' conventions did for Lean build
throughput. The report lives in `docs/reports/`; the plugin sources it cites
live under `plugins/`, so its links resolve inside this repository.

The plugin sources are a snapshot of the private `local-plugins` marketplace.
Edits made here do not flow back automatically; keep the two in sync by hand
or treat this repository as the publication copy.

## Where things live

| Thing | Path |
|---|---|
| Marketplace manifest (Claude) | `.claude-plugin/marketplace.json` |
| Marketplace manifest (Codex) | `.agents/plugins/marketplace.json` |
| Plugin manifest (Claude) | `plugins/<plugin>/.claude-plugin/plugin.json` |
| Plugin manifest (Codex) | `plugins/<plugin>/.codex-plugin/plugin.json` |
| Plugin skills | `plugins/<plugin>/skills/<name>/SKILL.md` (+ `references/`) |
| Plugin hooks (Claude) | `plugins/lean-usage/hooks/*.py` + `plugins/lean-usage/hooks/hooks.json` |
| Plugin hooks (Codex) | `plugins/lean-usage/codex-hooks.json` (absolute paths; edit for your checkout) |
| The `lake-build` wrapper | `plugins/lean-usage/bin/lake-build` (deployed to `~/.local/bin/lake-build` by the SessionStart hook) |
| Wrapper tests | `plugins/lean-usage/scripts/test_lake_build_lock.py` |
| Engineering report | `docs/reports/2026-09-07-lean-optimization-report.md` (+ `.pdf`, `assets/`) |
| Repo scripts | `scripts/test.sh`, `scripts/check-manifest-versions.sh` |

## Rules

- **Bump the `version` in BOTH plugin manifests** to the same value whenever a
  plugin's hooks, scripts, or skills change, and keep them equal.
  `scripts/check-manifest-versions.sh` reports drift; `--fix` resyncs Codex to
  Claude.
- **The file the `hooks` key names must be committed.**
- Builds in Lean projects go through `lake-build`, never raw `lake build` or
  `lean`; the `lean-direct-warn` hook enforces this.
- Python runs through `uv` (`uv run --no-project python …`); no bare `python3`
  or `pip`.
- Shell and Python sources carry the header block: copyright, "Released under
  GPL-3.0-or-later as described in the file LICENSE.", author, purpose, and
  `Usage:` lines.
- `docs/` is date-prefixed: `docs/<kind>/YYYY-MM-DD-slug.md`.
- Commit only your own edits; `git pull --rebase --autostash` before pushing.
- macOS only.
