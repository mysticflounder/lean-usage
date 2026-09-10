#!/usr/bin/env python3
# Copyright (c) 2026 Adam McKenna
# Released under GPL-3.0-or-later as described in the file LICENSE.
# Author: Adam McKenna <adam@mysticflounder.ai>
#
# lean-direct-warn.py — warn when Lean or Lake bypasses the lake-build wrapper.
#
# Usage:
#   Configured as a PreToolUse hook; reads hook event JSON from stdin.
"""lean-direct-warn.py — Warn when lake or lean is called directly instead of via lake-build.
Handles both Claude Code (flat payload) and Codex CLI (nested hook_event payload).
"""
import json
import os
import re
import shlex
import sys

LEAN_TOOLS = {"lake", "lean"}
INFO_ARGS = {"--version", "-v", "--help", "-h", "--info"}
LAKE_BUILD_SUBCMDS = {"build", "test"}

WARNING = (
    "Direct {tools} invocation detected. "
    "Prefer the global `lake-build` wrapper, which adds a lockfile (prevents "
    "concurrent builds) and per-build timing stats. Its PATH shim requests a "
    "Lean memory limit (default -M 16384 MB), but Lake can bypass the shim by "
    "invoking Lean by absolute path; this is not a guaranteed worker cap."
)


def extract_commands(command_str):
    """Return list of (executable_basename, args_list) pairs.

    args_list is every token following the executable up to the next shell separator,
    so callers can inspect subcommands (e.g. `lake env lean`).
    """
    results = []
    separators = {";", "&&", "||", "&", "|", ";;"}

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

        i = 0
        expecting_cmd = True
        while i < len(tokens):
            tok = tokens[i]
            if tok in separators:
                expecting_cmd = True
                i += 1
                continue
            if expecting_cmd:
                if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tok):
                    i += 1
                    continue
                basename = os.path.basename(tok)
                args = []
                j = i + 1
                while j < len(tokens) and tokens[j] not in separators:
                    args.append(tokens[j])
                    j += 1
                results.append((basename, args))
                expecting_cmd = False
            i += 1

    return results


def is_direct_build_call(exe, args):
    """True if (exe, args) is a build/compile invocation we want to warn about."""
    # `env` and `command` are common ways to preserve the caller's environment
    # while invoking a program.  Inspect their command operand so the warning
    # is not bypassed by a harmless-looking launcher.
    if exe in {"env", "command"}:
        index = 0
        while index < len(args):
            arg = args[index]
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", arg):
                index += 1
                continue
            if exe == "env" and arg in {
                "-i", "--ignore-environment", "-0", "--null", "--",
            }:
                index += 1
                continue
            if exe == "env" and arg in {"-u", "--unset", "-C", "--chdir"}:
                index += 2
                continue
            if exe == "command" and arg in {"-p", "--"}:
                index += 1
                continue
            if arg.startswith("-"):
                # Unknown launcher options may consume a value; do not guess
                # past them and risk classifying an option value as a command.
                return False
            return bool(args[index:]) and is_direct_build_call(
                os.path.basename(arg), args[index + 1:]
            )
        return False
    if exe == "lean":
        return not (args and args[0] in INFO_ARGS)
    if exe != "lake":
        return False
    if not args:
        return False  # bare `lake` prints help
    sub = args[0]
    if sub in INFO_ARGS:
        return False
    if sub in LAKE_BUILD_SUBCMDS:
        return True
    if sub == "env" and len(args) >= 2 and args[1] == "lean":
        return True
    return False


def direct_build_executable(exe, args):
    """Return the underlying direct-build executable, if any."""
    if exe in LEAN_TOOLS and is_direct_build_call(exe, args):
        return exe
    if exe not in {"env", "command"}:
        return None
    index = 0
    while index < len(args):
        arg = args[index]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", arg):
            index += 1
            continue
        if exe == "env" and arg in {
            "-i", "--ignore-environment", "-0", "--null", "--",
        }:
            index += 1
            continue
        if exe == "env" and arg in {"-u", "--unset", "-C", "--chdir"}:
            index += 2
            continue
        if exe == "command" and arg in {"-p", "--"}:
            index += 1
            continue
        if arg.startswith("-"):
            return None
        nested_exe = os.path.basename(arg)
        return nested_exe if is_direct_build_call(nested_exe, args[index + 1:]) else None
    return None


def extract_tool_and_command(data: dict) -> tuple[str, str, str]:
    if "toolCall" in data and isinstance(data["toolCall"], dict):
        tc = data["toolCall"]
        tname = tc.get("name", "")
        args = tc.get("args") if isinstance(tc.get("args"), dict) else {}
        cmd = args.get("CommandLine") or args.get("command") or args.get("cmd") or ""
        return ("antigravity", tname, cmd)
    if "hook_event" in data and isinstance(data["hook_event"], dict):
        event = data["hook_event"]
        tname = event.get("tool_name", "")
        tinput = event.get("tool_input") if isinstance(event.get("tool_input"), dict) else {}
        cmd = tinput.get("command") or tinput.get("CommandLine") or tinput.get("cmd") or ""
        return ("codex", tname, cmd)
    tname = data.get("tool_name", "")
    tinput = data.get("tool_input") if isinstance(data.get("tool_input"), dict) else {}
    cmd = tinput.get("command") or tinput.get("CommandLine") or tinput.get("cmd") or ""
    return ("claude", tname, cmd)


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        return

    if not isinstance(hook_input, dict):
        return

    platform, tool_name, command = extract_tool_and_command(hook_input)

    if tool_name not in ("Bash", "run_command", "exec_command"):
        return

    if not isinstance(command, str) or not command:
        return

    commands = extract_commands(command)
    direct = [
        detected
        for exe, args in commands
        if (detected := direct_build_executable(exe, args)) is not None
    ]

    if not direct:
        return

    tools_str = "/".join(sorted(set(direct)))
    msg = WARNING.format(tools=tools_str)

    if platform == "antigravity":
        print(json.dumps({
            "decision": "allow",
            "reason": f"[lean-direct-warn] {msg}",
        }))
    else:
        print(json.dumps({
            "systemMessage": f"[lean-direct-warn] {msg}",
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": f"[lean-direct-warn] {msg}",
            },
        }))


if __name__ == "__main__":
    main()
