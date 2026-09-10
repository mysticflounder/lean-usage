#!/usr/bin/env bash
# Copyright (c) 2026 Adam McKenna
# Released under GPL-3.0-or-later as described in the file LICENSE.
# Author: Adam McKenna <adam@mysticflounder.ai>
#
# check-manifest-versions.sh — release gate for manifest and Lean-worker drift.
#
# Every plugin ships .claude-plugin/plugin.json (Claude keys its cache on this),
# .codex-plugin/plugin.json (Codex keys its cache AND its per-hook trust on this),
# and a compatibility copy at the plugin root. All three carry the same version. The bump workflow historically only touched the
# Claude manifest, so the Codex version froze while hook content kept changing.
# Codex then sees changed content under an unchanged version on every marketplace
# sync, invalidates the trusted_hash, and disables/re-prompts the plugin's hooks
# — i.e. "the codex hooks break every time it updates". Keeping the two versions
# equal makes Codex rebuild + re-trust cleanly on each real update.
#
# Usage:
#   scripts/check-manifest-versions.sh          # report drift, exit 1 if any
#   scripts/check-manifest-versions.sh --fix     # set other versions := claude version
#
# Only plugins that ship BOTH manifests are compared; single-host plugins
# (claude-only or codex-only) are skipped.

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
plugins_dir="$repo_root/plugins"

fix=0
[ "${1:-}" = "--fix" ] && fix=1

drift=0
checked=0
fixed=0

for d in "$plugins_dir"/*/; do
  name="$(basename "$d")"
  cl="${d}.claude-plugin/plugin.json"
  cx="${d}.codex-plugin/plugin.json"
  [ -f "$cl" ] && [ -f "$cx" ] || continue

  clv="$(jq -r '.version // empty' "$cl")"
  checked=$((checked + 1))

  if [ -z "$clv" ]; then
    printf 'WARN   %-22s missing version (claude=none)\n' "$name"
    drift=1
    continue
  fi

  # Compare the Codex manifest and the plugin-root compatibility copy against it.
  for other in "${d}.codex-plugin/plugin.json" "${d}plugin.json"; do
    [ -f "$other" ] || continue
    label="codex"
    [ "$other" = "${d}plugin.json" ] && label="root "

    ov="$(jq -r '.version // empty' "$other")"
    if [ -z "$ov" ]; then
      printf 'WARN   %-22s %s manifest missing version\n' "$name" "$label"
      drift=1
      continue
    fi

    if [ "$clv" != "$ov" ]; then
      if [ "$fix" -eq 1 ]; then
        tmp="$(mktemp)"
        jq --indent 2 --arg v "$clv" '.version = $v' "$other" >"$tmp" && mv "$tmp" "$other"
        printf 'FIXED  %-22s %s %s -> %s\n' "$name" "$label" "$ov" "$clv"
        fixed=$((fixed + 1))
      else
        printf 'DRIFT  %-22s claude=%-8s %s=%-8s\n' "$name" "$clv" "$label" "$ov"
        drift=1
      fi
    fi
  done
done

if [ "$fix" -eq 1 ]; then
  echo
  echo "Re-synced $fixed plugin(s); remember to bump and commit, then /plugin refresh."
  exit 0
fi

if [ "$drift" -ne 0 ]; then
  echo
  echo "Manifest version drift detected. The Codex manifest (.codex-plugin/plugin.json)"
  echo "and the plugin-root copy (plugin.json) must match the Claude manifest"
  echo "(.claude-plugin/plugin.json): Codex keys its cache and per-hook trust on its own"
  echo "version, so a frozen version makes it re-trust (break) the plugin's hooks on"
  echo "every marketplace sync. Run with --fix to re-sync."
  exit 1
fi

echo "OK: $checked plugin(s) have matching versions across every manifest."
