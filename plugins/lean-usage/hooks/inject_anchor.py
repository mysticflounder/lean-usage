#!/usr/bin/env python3
# Copyright (c) 2026 Adam McKenna
# Released under GPL-3.0-or-later as described in the file LICENSE.
# Author: Adam McKenna <adam@mysticflounder.ai>
#
# inject_anchor.py — surface the active proof-blueprint anchor at session start.
#
# Usage:
#   Configured as a SessionStart hook; reads hook event JSON from stdin.
"""SessionStart: inject `proof-blueprint anchor` output into the context.

When the session's cwd sits inside a proof-blueprint project (a
`.blueprint.toml` in cwd or any parent), this surfaces that session's
work cursor + proof-tree context — or a loud WARNING to set an anchor if
none is placed yet — into the agent's context at session start, so it
re-grounds on the active proof branch before drifting.

We invoke bare `proof-blueprint anchor` (no CLI args). It resolves the
session from $CLAUDE_SESSION_ID, which is NOT present in hook processes
by default, so we seed it into the subprocess environment from the
SessionStart payload. Outside a blueprint project the command exits
non-zero ("no .blueprint.toml found …", on stderr); this plugin is
opt-in and math projects have a blueprint, so on any non-zero exit we
stay silent and inject nothing.

Session-file fallback for non-Claude agents (e.g. Codex CLI): agents
that don't inject $CLAUDE_SESSION_ID into their shell env need another
path. We write the session_id to `<project_data_dir>/.current-session`
so proof-blueprint commands run by those agents can resolve the session.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def find_proof_blueprint():
    """Resolve the proof-blueprint executable, PATH first then known installs."""
    exe = shutil.which("proof-blueprint")
    if exe:
        return exe
    for cand in ("~/bin/proof-blueprint", "~/.local/bin/proof-blueprint"):
        p = os.path.expanduser(cand)
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


def find_project_data_dir(start: str) -> Path | None:
    """Walk up from start looking for .blueprint.toml; return its data/ sibling."""
    p = Path(start).resolve()
    for parent in [p, *p.parents]:
        sentinel = parent / ".blueprint.toml"
        if sentinel.exists():
            # data dir is recorded in the toml; default to <root>/data
            try:
                import tomllib  # type: ignore
            except ImportError:
                try:
                    import tomli as tomllib  # type: ignore
                except ImportError:
                    return parent / "data"
            try:
                cfg = tomllib.loads(sentinel.read_text())
                rel = cfg.get("paths", {}).get("db", "data/proof-blueprint.db")
                return (parent / rel).parent
            except Exception:
                return parent / "data"
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, OSError):
        return

    exe = find_proof_blueprint()
    if not exe:
        return

    cwd = payload.get("cwd") or (payload.get("workspacePaths") or [os.getcwd()])[0]
    session_id = payload.get("session_id") or payload.get("conversationId")
    is_antigravity = "conversationId" in payload or "workspacePaths" in payload

    if is_antigravity and payload.get("invocationNum", 1) > 1:
        return

    # Write session_id to the project data dir so agents that don't inject
    # $CLAUDE_SESSION_ID into their shell env (e.g. Codex) can still resolve it.
    if session_id:
        data_dir = find_project_data_dir(cwd)
        if data_dir:
            try:
                data_dir.mkdir(parents=True, exist_ok=True)
                (data_dir / ".current-session").write_text(session_id + "\n")
            except OSError:
                pass

    # Bare `proof-blueprint anchor` — no CLI args. It reads $CLAUDE_SESSION_ID,
    # which hook processes don't inherit, so seed it from the payload here.
    env = dict(os.environ)
    if session_id:
        env["CLAUDE_SESSION_ID"] = session_id

    try:
        proc = subprocess.run(
            [exe, "anchor"], cwd=cwd, env=env,
            capture_output=True, text=True, timeout=6,
        )
    except (subprocess.TimeoutExpired, OSError):
        return

    # Non-zero exit = "no .blueprint.toml here" (or no session id) — the message
    # lands on stderr; we never want to inject it. Stay silent.
    if proc.returncode != 0:
        return
    out = (proc.stdout or "").strip()
    if not out:
        return

    context = (
        "# proof-blueprint anchor — this session's proof-tree work cursor\n\n"
        + out
    )

    if is_antigravity:
        json.dump({
            "injectSteps": [
                {
                    "ephemeralMessage": context,
                }
            ],
        }, sys.stdout)
    else:
        json.dump({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            },
        }, sys.stdout)
    sys.stdout.write("\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
