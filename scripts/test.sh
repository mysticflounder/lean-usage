#!/usr/bin/env bash
# Copyright (c) 2026 Adam McKenna
# Released under the Apache 2.0 license
# Author: Adam McKenna <adam@mysticflounder.ai>
#
# test.sh — run the repository checks: manifest version parity for every
# plugin, then the lake-build wrapper's lock/shim/telemetry tests.
#
# Usage:
#   scripts/test.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT/scripts/check-manifest-versions.sh"
cd "$ROOT/plugins/lean-usage"
uv run --no-project python scripts/test_lake_build_lock.py
