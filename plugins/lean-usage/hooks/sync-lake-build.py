#!/usr/bin/env python3
# Copyright (c) 2026 Adam McKenna
# Released under GPL-3.0-or-later as described in the file LICENSE.
# Author: Adam McKenna <adam@mysticflounder.ai>
#
# sync-lake-build.py — install and advertise the active plugin's lake-build wrapper.
#
# Usage:
#   Configured as a SessionStart hook; reads hook event JSON from stdin.
"""lean-usage SessionStart — keep ~/.local/bin/lake-build pointing at the
plugin-shipped global build wrapper and advertise a PATH-independent command.

`lake-build` is the single global Lean/Lake build wrapper. The symlink keeps
``~/.local/bin/lake-build`` pointing at whatever version of the script is in
the active plugin cache when that directory is already on ``$PATH``. The
SessionStart context always includes a direct command for hosts that do not
put ``~/.local/bin`` on ``$PATH``.

Best-effort: exits 0 on success or failure — the symlink not being in place is
never a reason to block session start.
"""
import json
import os
import shlex
import sys
from pathlib import Path


def wrapper_path() -> Path:
    # Resolve the plugin root from the running script. hooks/ and bin/ are
    # siblings in both a source checkout and an installed host cache.
    return Path(__file__).resolve().parent.parent / "bin" / "lake-build"


def direct_wrapper_command() -> str:
    """Return a shell-safe command that does not depend on PATH shims."""
    interpreter = Path(sys.executable).resolve()
    wrapper = wrapper_path()
    return " ".join(shlex.quote(str(path)) for path in (interpreter, wrapper))


def install_symlink() -> bool:
    """Best-effort install; return whether the desired symlink is present."""
    src = wrapper_path()
    if not src.is_file():
        return False
    target_dir = Path.home() / ".local" / "bin"
    target = target_dir / "lake-build"
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        # A regular file is unexpected and may contain local work. Preserve it;
        # the PreToolUse guard should prevent agents from creating one here.
        if os.path.lexists(target) and not target.is_symlink():
            return False
        if target.is_symlink():
            try:
                if target.resolve(strict=False) == src.resolve():
                    return True
            except (OSError, RuntimeError):
                pass
        tmp = target_dir / f".lake-build.{os.getpid()}"
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        os.symlink(src, tmp)
        os.replace(tmp, target)  # atomic on POSIX
        return True
    except OSError:
        return False


def emit_session_context() -> None:
    command = direct_wrapper_command()
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": (
                "When project policy authorizes a Lean/Lake build, use this "
                "PATH-independent command (append target arguments as needed):\n"
                f"```sh\n{command}\n```"
            ),
        }
    }
    sys.stdout.write(json.dumps(output) + "\n")
    sys.stdout.flush()


def main() -> None:
    # Drain stdin so the hook host doesn't see a broken pipe; check invocationNum on Antigravity.
    install = True
    try:
        raw = sys.stdin.read()
        if raw.strip():
            data = json.loads(raw)
            if data.get("invocationNum", 1) > 1:
                install = False
    except Exception:
        pass
    if install:
        install_symlink()
    # Context is useful even when symlink installation is unavailable or is
    # skipped on a repeated SessionStart invocation.
    emit_session_context()


if __name__ == "__main__":
    main()
