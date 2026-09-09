#!/usr/bin/env bash
# Copyright (c) 2026 Adam McKenna
# Released under the Apache 2.0 license
# Author: Adam McKenna <adam@mysticflounder.ai>
#
# check-manifest-versions.sh — release gate for manifest and Lean-worker drift.
#
# Every plugin ships two manifests: .claude-plugin/plugin.json (Claude keys its
# cache on this) and .codex-plugin/plugin.json (Codex keys its cache AND its
# per-hook trust on this). The bump workflow historically only touched the
# Claude manifest, so the Codex version froze while hook content kept changing.
# Codex then sees changed content under an unchanged version on every marketplace
# sync, invalidates the trusted_hash, and disables/re-prompts the plugin's hooks
# — i.e. "the codex hooks break every time it updates". Keeping the two versions
# equal makes Codex rebuild + re-trust cleanly on each real update.
#
# Usage:
#   scripts/check-manifest-versions.sh          # report drift, exit 1 if any
#   scripts/check-manifest-versions.sh --fix     # set codex version := claude version
#
# Only plugins that ship BOTH manifests are compared; single-host plugins
# (claude-only or codex-only) are skipped.
# The canonical Lean worker contract check is also run here so the repository's
# existing release validation cannot pass while an agent or launcher has drifted.

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
  cxv="$(jq -r '.version // empty' "$cx")"
  checked=$((checked + 1))

  if [ -z "$clv" ] || [ -z "$cxv" ]; then
    printf 'WARN   %-22s missing version (claude=%s codex=%s)\n' "$name" "${clv:-none}" "${cxv:-none}"
    drift=1
    continue
  fi

  if [ "$clv" != "$cxv" ]; then
    if [ "$fix" -eq 1 ]; then
      tmp="$(mktemp)"
      jq --indent 2 --arg v "$clv" '.version = $v' "$cx" >"$tmp" && mv "$tmp" "$cx"
      printf 'FIXED  %-22s codex %s -> %s\n' "$name" "$cxv" "$clv"
      fixed=$((fixed + 1))
    else
      printf 'DRIFT  %-22s claude=%-8s codex=%-8s\n' "$name" "$clv" "$cxv"
      drift=1
    fi
  fi
done

if [ "$fix" -eq 1 ]; then
  echo
  echo "Re-synced $fixed plugin(s); remember to bump and commit, then /plugin refresh."
  exit 0
fi

if [ "$drift" -ne 0 ]; then
  echo
  echo "Manifest version drift detected. The Codex manifest (.codex-plugin/plugin.json)"
  echo "must match the Claude manifest (.claude-plugin/plugin.json): Codex keys its cache"
  echo "and per-hook trust on its own version, so a frozen version makes it re-trust"
  echo "(break) the plugin's hooks on every marketplace sync. Run with --fix to re-sync."
  exit 1
fi

echo "OK: $checked plugin(s) have matching claude/codex manifest versions."
