#!/usr/bin/env python3
# Copyright (c) 2026 Adam McKenna
# Released under GPL-3.0-or-later as described in the file LICENSE.
# Author: Adam McKenna <adam@mysticflounder.ai>
#
# mathlib-cache-check.py — block Lean builds with a missing or stale mathlib cache.
#
# Usage:
#   Configured as a PreToolUse hook; reads hook event JSON from stdin.
"""mathlib-cache-check.py — Block `lake build` / `lake env lean` / `lake-build` when
the project depends on mathlib but `lake exe cache get` has not been run for it.

Two ways the cache can be unusable:
  * empty/thin — fewer than OLEAN_THRESHOLD oleans on disk (fresh clone);
  * STALE — plenty of oleans, but a toolchain bump (a merge or checkout that
    rewrites `lean-toolchain`) made every one of them invalid. The count check
    is blind to this, so compare `lean-toolchain` against `Mathlib.olean` too.

Saves ~1 hour of cold source-compile per project. Bypass with
`LEAN_USAGE_SKIP_CACHE_CHECK=1`. Handles both Claude Code (flat payload) and
Codex CLI (nested hook_event payload).
"""
import json
import os
import shlex
import sys
from pathlib import Path

OLEAN_THRESHOLD = 100  # fresh `lake exe cache get` produces ~8000; any real build produces >>100


def split_statements(command_str):
    """Tokenize a shell command into one token-list per statement (split on ; && || & |)."""
    separators = {";", "&&", "||", "&", "|"}
    statements = []
    for line in command_str.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            lex = shlex.shlex(line, posix=True, punctuation_chars=";&|")
            lex.whitespace_split = True
            tokens = list(lex)
        except ValueError:
            continue
        cur = []
        for tok in tokens:
            if tok in separators:
                if cur:
                    statements.append(cur)
                    cur = []
            else:
                cur.append(tok)
        if cur:
            statements.append(cur)
    return statements


def is_build_invocation(tokens):
    """True iff tokens contain `lake build`, `lake env lean`, or a `lake-build` / `lake-build.sh` invocation."""
    for i, tok in enumerate(tokens):
        basename = os.path.basename(tok)
        if basename in ("lake-build", "lake-build.sh"):
            return True
        if basename == "lake" and i + 1 < len(tokens):
            sub = tokens[i + 1]
            if sub == "build":
                return True
            if sub == "env" and i + 2 < len(tokens) and tokens[i + 2] == "lean":
                return True
    return False


def is_cd(tokens):
    return len(tokens) >= 2 and tokens[0] == "cd"


def resolve_cwd_at(initial_cwd, statements, target_idx):
    """Apply any `cd` statements before target_idx to compute effective cwd."""
    cwd = Path(initial_cwd)
    for i in range(target_idx):
        stmt = statements[i]
        if is_cd(stmt):
            target = stmt[1]
            cwd = Path(target) if os.path.isabs(target) else (cwd / target)
    try:
        return cwd.resolve()
    except (OSError, RuntimeError):
        return cwd


def find_project_root(cwd):
    """Walk up looking for lakefile.{toml,lean}."""
    cur = Path(cwd)
    try:
        cur = cur.resolve()
    except (OSError, RuntimeError):
        pass
    while True:
        if (cur / "lakefile.toml").exists() or (cur / "lakefile.lean").exists():
            return cur
        if cur == cur.parent:
            return None
        cur = cur.parent


def uses_mathlib(project_root):
    """True if the project depends on mathlib (manifest or lakefile mention)."""
    manifest = project_root / "lake-manifest.json"
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text())
            for pkg in data.get("packages", []):
                if pkg.get("name") == "mathlib":
                    return True
        except (json.JSONDecodeError, OSError):
            pass
    for fn in ("lakefile.toml", "lakefile.lean"):
        f = project_root / fn
        if f.exists():
            try:
                if "mathlib" in f.read_text().lower():
                    return True
            except OSError:
                pass
    return False


def count_oleans(root, limit):
    """Count `.olean` files under root, stopping at limit."""
    count = 0
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.endswith(".olean"):
                count += 1
                if count >= limit:
                    return count
    return count


def find_toolchain(project_root):
    """Return the `lean-toolchain` that governs project_root, or None.

    elan resolves the toolchain by walking up from the build directory, so a
    Lake root nested under the repo root (`repo/lean/`) may inherit the file
    from a parent. Walk the same way.
    """
    d = project_root.resolve()
    while True:
        candidate = d / "lean-toolchain"
        if candidate.is_file():
            return candidate
        if d.parent == d:
            return None
        d = d.parent


def stale_toolchain_reason(project_root, mathlib_lib):
    """Return a reason string when the mathlib oleans predate the toolchain.

    A toolchain bump — a merge or checkout that rewrites `lean-toolchain` —
    leaves every existing olean on disk but makes all of them unusable. The
    olean count still passes, so `count_oleans` alone cannot see this; compare
    mtimes instead.

    `Mathlib.olean` is the import-everything root module: `lake exe cache get`
    always delivers it, and a source build writes it only at the very end. So
    "root olean older than lean-toolchain" means the cache on disk was built
    for the previous toolchain. When the root olean is absent we say nothing
    and let the count check decide, so a project that legitimately never builds
    that module is not blocked forever.
    """
    toolchain = find_toolchain(project_root)
    if toolchain is None:
        return None

    root_olean = mathlib_lib / "lean" / "Mathlib.olean"
    try:
        toolchain_mtime = toolchain.stat().st_mtime
        olean_mtime = root_olean.stat().st_mtime
    except OSError:
        return None

    if toolchain_mtime <= olean_mtime:
        return None

    try:
        version = toolchain.read_text(encoding="utf-8").strip()
    except OSError:
        version = "unknown"

    return (
        f"mathlib cache is STALE: {toolchain} ({version}) is newer than "
        f"{root_olean}, so the oleans on disk were built for the previous "
        f"toolchain. They still count toward the {OLEAN_THRESHOLD}-olean "
        f"threshold but Lake will recompile all of mathlib from source. "
        f"Run `cd {project_root} && lake exe cache get` first. "
        f"To bypass, set LEAN_USAGE_SKIP_CACHE_CHECK=1."
    )


def extract_tool_info(data: dict) -> tuple[str, str, str, str]:
    if "toolCall" in data and isinstance(data["toolCall"], dict):
        tc = data["toolCall"]
        tname = tc.get("name", "")
        args = tc.get("args") or {}
        cmd = args.get("CommandLine") or args.get("command") or ""
        cwd = args.get("Cwd") or (data.get("workspacePaths") or [os.getcwd()])[0]
        return ("antigravity", tname, cmd, cwd)
    if "hook_event" in data and isinstance(data["hook_event"], dict):
        event = data["hook_event"]
        tname = event.get("tool_name", "")
        tinput = event.get("tool_input", {}) or {}
        cmd = tinput.get("command") or tinput.get("CommandLine") or ""
        cwd = event.get("cwd") or data.get("cwd") or os.getcwd()
        return ("codex", tname, cmd, cwd)
    tname = data.get("tool_name", "")
    tinput = data.get("tool_input", {}) or {}
    cmd = tinput.get("command") or tinput.get("CommandLine") or ""
    cwd = data.get("cwd") or tinput.get("cwd") or os.getcwd()
    return ("claude", tname, cmd, cwd)


def main():
    if os.environ.get("LEAN_USAGE_SKIP_CACHE_CHECK") == "1":
        return

    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        return

    platform, tool_name, command, cwd = extract_tool_info(hook_input)

    if tool_name not in ("Bash", "run_command"):
        return

    if not command:
        return

    statements = split_statements(command)
    build_idx = next((i for i, s in enumerate(statements) if is_build_invocation(s)), None)
    if build_idx is None:
        return

    effective_cwd = resolve_cwd_at(cwd, statements, build_idx)
    project_root = find_project_root(effective_cwd)
    if project_root is None:
        return  # not in a Lake project — let it through

    if not uses_mathlib(project_root):
        return  # no mathlib dep — no check needed

    mathlib_lib = project_root / ".lake" / "packages" / "mathlib" / ".lake" / "build" / "lib"
    if not mathlib_lib.exists():
        reason = (
            f"mathlib cache is empty (no {mathlib_lib}). "
            f"Run `cd {project_root} && lake exe cache get` before any `lake build` — "
            f"it downloads ~8000 precompiled oleans. Skipping it triggers ~1 hour of source compile. "
            f"If you genuinely need to source-compile mathlib, set LEAN_USAGE_SKIP_CACHE_CHECK=1."
        )
    elif (stale := stale_toolchain_reason(project_root, mathlib_lib)) is not None:
        reason = stale
    else:
        count = count_oleans(mathlib_lib, OLEAN_THRESHOLD)
        if count >= OLEAN_THRESHOLD:
            return  # cache (or prior build) populated — proceed
        reason = (
            f"Only {count} mathlib oleans found under {mathlib_lib} (threshold {OLEAN_THRESHOLD}). "
            f"Run `cd {project_root} && lake exe cache get` first to populate ~8000 precompiled oleans. "
            f"Source-compiling mathlib costs ~1 hour. "
            f"To bypass, set LEAN_USAGE_SKIP_CACHE_CHECK=1."
        )

    if platform == "antigravity":
        print(json.dumps({
            "decision": "deny",
            "reason": f"[mathlib-cache-check] {reason}",
        }))
    else:
        print(json.dumps({
            "systemMessage": f"[mathlib-cache-check] {reason}",
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            },
        }))


if __name__ == "__main__":
    main()
