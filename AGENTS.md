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
| Plugin manifest (compatibility copy) | `plugins/<plugin>/plugin.json` — same content as the Claude manifest |
| Plugin skills | `plugins/<plugin>/skills/<name>/SKILL.md` (+ `references/`) |
| Plugin hooks (Claude) | `plugins/lean-usage/hooks/*.py` + `plugins/lean-usage/hooks/hooks.json` |
| Plugin hooks (Codex) | `plugins/lean-usage/codex-hooks.json` (paths resolve through `${PLUGIN_ROOT}`; no checkout-specific edit) |
| The `lake-build` wrapper | `plugins/lean-usage/bin/lake-build` (deployed to `~/.local/bin/lake-build` by the SessionStart hook) |
| Wrapper tests | `plugins/lean-usage/scripts/test_lake_build_lock.py` and `plugins/lean-usage/scripts/test_lake_build_edit_guard.py` |
| Engineering report | `docs/reports/2026-09-07-lean-optimization-report.md` (+ `.pdf`, `assets/`) |
| Repo scripts | `scripts/test.sh`, `scripts/check-manifest-versions.sh` |

## Rules

- **Bump the `version` in EVERY plugin manifest** to the same value whenever a
  plugin's hooks, scripts, or skills change, and keep them equal: the Claude
  manifest, the Codex manifest, and the compatibility copy at the plugin root.
  `scripts/check-manifest-versions.sh` reports drift; `--fix` resyncs the other
  two to Claude.
- **The file the `hooks` key names must be committed.**
- Builds in Lean projects go through `lake-build`; the `lean-direct-warn` hook
  warns on direct build calls. Deliberate single-file checks and authorized
  mathlib source builds follow the skill's build-operations reference and
  the target project's policy.
- Python runs through `uv` (`uv run --no-project python …`); no bare `python3`
  or `pip`.
- Shell and Python sources carry the header block: copyright, "Released under
  GPL-3.0-or-later as described in the file LICENSE.", author, purpose, and
  `Usage:` lines.
- `docs/` is date-prefixed: `docs/<kind>/YYYY-MM-DD-slug.md`.
- Commit only your own edits; `git pull --rebase --autostash` before pushing.
- macOS and Linux are supported. Windows support is intended but untested;
  treat Windows-specific problems as bugs and direct users to the issue tracker.
