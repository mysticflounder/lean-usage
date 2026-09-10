#!/usr/bin/env python3
# Copyright (c) 2026 Adam McKenna
# Released under GPL-3.0-or-later as described in the file LICENSE.
# Author: Adam McKenna <adam@mysticflounder.ai>
#
# sync-lake-build.py — install the active plugin's lake-build wrapper on PATH.
#
# Usage:
#   Configured as a SessionStart hook; reads hook event JSON from stdin.
"""lean-usage SessionStart — keep ~/.local/bin/lake-build pointing at the
plugin-shipped global build wrapper.

`lake-build` is the single global Lean/Lake build wrapper. The skill and the
lean-direct-warn hook refer to it by bare name, so it has to be on $PATH; this
symlink keeps ~/.local/bin/lake-build pointing at whatever version of the
script is in the active plugin cache (same pattern as py-run / auto-compact).

Best-effort: exits 0 on success or failure — the symlink not being in place is
never a reason to block session start.
"""
import json
import os
import sys
from pathlib import Path


def install_symlink() -> None:
    # Self-locate the plugin root from this script's own path rather than
    # $CLAUDE_PLUGIN_ROOT. Under Codex this hook is invoked by a fixed
    # source-repo path (so it survives Codex deleting the versioned cache dir on
    # plugin update — the Claude-side hooks/hooks.json still uses
    # ${CLAUDE_PLUGIN_ROOT}), and Codex does not reliably set that env var for a
    # fixed-path command. hooks/ and bin/ are siblings in both the source tree
    # and every host's plugin cache, so parent.parent is the plugin root; the
    # resolved Claude cache path is identical to $CLAUDE_PLUGIN_ROOT.
    plugin_root = Path(__file__).resolve().parent.parent
    src = plugin_root / "bin" / "lake-build"
    if not src.is_file():
        return
    target_dir = Path.home() / ".local" / "bin"
    target = target_dir / "lake-build"
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        # A regular file is unexpected and may contain local work. Preserve it;
        # the PreToolUse guard should prevent agents from creating one here.
        if os.path.lexists(target) and not target.is_symlink():
            return
        if target.is_symlink() and Path(os.readlink(target)) == src:
            return
        tmp = target_dir / f".lake-build.{os.getpid()}"
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        os.symlink(src, tmp)
        os.replace(tmp, target)  # atomic on POSIX
    except OSError:
        return


def main() -> None:
    # Drain stdin so the hook host doesn't see a broken pipe; check invocationNum on Antigravity.
    try:
        raw = sys.stdin.read()
        if raw.strip():
            data = json.loads(raw)
            if data.get("invocationNum", 1) > 1:
                return
    except Exception:
        pass
    install_symlink()


if __name__ == "__main__":
    main()
