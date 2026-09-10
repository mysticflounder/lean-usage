#!/usr/bin/env bash
# Copyright (c) 2026 Adam McKenna
# Released under GPL-3.0-or-later as described in the file LICENSE.
# Author: Adam McKenna <adam@mysticflounder.ai>
#
# test.sh — run the repository checks: manifest version parity for every
# plugin, then the wrapper, edit-guard, and build-hook event regression tests.
#
# Usage:
#   scripts/test.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT/scripts/check-manifest-versions.sh"
cd "$ROOT/plugins/lean-usage"
uv run --no-project python scripts/test_lake_build_lock.py
uv run --no-project python scripts/test_lake_build_edit_guard.py
uv run --no-project python scripts/test_build_hooks.py
