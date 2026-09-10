#!/usr/bin/env bash
# Copyright (c) 2026 Adam McKenna
# Released under GPL-3.0-or-later as described in the file LICENSE.
# Author: Adam McKenna <adam@mysticflounder.ai>
# Purpose: container-only regression and real-Lean smoke checks.
# Usage: invoked by bash scripts/test-docker.sh
set -euo pipefail
cp -R /source/plugins /source/scripts /work/
cd /work
bash scripts/test.sh
PLUGIN_ROOT=/work/plugins/lean-usage
export PLUGIN_ROOT
uv run --no-project python "$PLUGIN_ROOT/hooks/sync-lake-build.py" </dev/null > /work/session-start.json
test "$(readlink /root/.local/bin/lake-build)" = "$PLUGIN_ROOT/bin/lake-build"
WRAPPER_COMMAND=$(jq -er '.hookSpecificOutput.additionalContext | capture("```sh\n(?<command>[^\n]+)\n```").command' /work/session-start.json)
# Deliberately exclude both the optional symlink and the image's Python/uv bin.
export PATH=/usr/bin:/bin
if command -v lake-build >/dev/null; then
  echo 'Test setup error: lake-build unexpectedly resolves on PATH' >&2
  exit 1
fi
bash -c "$WRAPPER_COMMAND --help" >/dev/null
mkdir /work/lean-smoke
cd /work/lean-smoke
lake init smoke lib
LOCKFILE=lake-build.lock bash -c "$WRAPPER_COMMAND"
test ! -e lake-build.lock
test -s /root/.local/state/lean-usage/build-stats.jsonl
LOCKFILE=lake-build.lock bash -c "$WRAPPER_COMMAND"
jq -e -s 'length == 2 and all(.[]; .exit_code == 0) and .[1].recompiled == 0' \
  /root/.local/state/lean-usage/build-stats.jsonl
echo 'Linux smoke test passed: PATH-independent SessionStart command, real Lean cold/warm builds, lock cleanup, telemetry.'
