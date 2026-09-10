#!/usr/bin/env bash
# Copyright (c) 2026 Adam McKenna
# Released under GPL-3.0-or-later as described in the file LICENSE.
# Author: Adam McKenna <adam@mysticflounder.ai>
# Purpose: test the plugin in Linux with a real pinned Lean toolchain.
# Usage: bash scripts/test-docker.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
docker build -t lean-usage-release-test -f "$ROOT/scripts/docker/Dockerfile" "$ROOT/scripts/docker"
# No host credentials, Docker socket, or writable source mount enters the container.
# Tests modify only the disposable copy; retain their output in the invoking terminal.
docker run --rm --network none --cpus 2 --memory 4g \
  --mount "type=bind,source=$ROOT,target=/source,readonly" \
  lean-usage-release-test bash /source/scripts/docker/run-tests.sh
