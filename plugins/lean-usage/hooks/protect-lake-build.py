#!/usr/bin/env python3
# Copyright (c) 2026 Adam McKenna
# Released under GPL-3.0-or-later as described in the file LICENSE.
# Author: Adam McKenna <adam@mysticflounder.ai>
#
# protect-lake-build.py — block edits to the deployed lake-build wrapper.
#
# Usage:
#   Configured as a PreToolUse hook; reads hook event JSON from stdin.
"""Protect the plugin-managed ~/.local/bin/lake-build entry.

The SessionStart hook replaces this entry with a symlink to the active plugin.
Agents must edit the repository source instead of this deployed path.
"""

import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any, Iterator


PROTECTED_RELATIVE = Path(".local") / "bin" / "lake-build"
PATCH_PATH_RE = re.compile(
    r"^\*\*\* (?:Add|Update|Delete) File: (.+)$|^\*\*\* Move to: (.+)$",
    re.MULTILINE,
)
SHELL_MUTATORS = {
    "add-content",
    "apply_patch",
    "bash",
    "chmod",
    "chown",
    "clear-content",
    "cmd",
    "copy-item",
    "dd",
    "del",
    "emacs",
    "erase",
    "mv",
    "move-item",
    "nano",
    "new-item",
    "node",
    "out-file",
    "patch",
    "perl",
    "powershell",
    "pwsh",
    "python",
    "python3",
    "rm",
    "remove-item",
    "ruby",
    "set-content",
    "sh",
    "sudo",
    "tee",
    "touch",
    "truncate",
    "unlink",
    "uv",
    "vi",
    "vim",
    "xargs",
    "zsh",
}
PATH_KEYS = {"file_path", "filepath", "notebook_path", "path", "target"}


def protected_path() -> Path:
    """Return the deployed wrapper path without resolving its symlink."""
    return Path.home() / PROTECTED_RELATIVE


def normalize_path(value: str, cwd: str) -> str:
    expanded = os.path.expanduser(os.path.expandvars(value.strip().strip("'\"")))
    path = Path(expanded)
    if not path.is_absolute():
        path = Path(cwd) / path
    return os.path.normcase(os.path.abspath(path))


def is_protected_path(value: str, cwd: str) -> bool:
    try:
        return normalize_path(value, cwd) == normalize_path(str(protected_path()), cwd)
    except (OSError, TypeError, ValueError):
        return False


def iter_declared_paths(value: Any) -> Iterator[str]:
    """Yield path-like fields from Edit/Write-style tool inputs."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in PATH_KEYS and isinstance(child, str):
                yield child
            elif isinstance(child, (dict, list)):
                yield from iter_declared_paths(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_declared_paths(child)


def extract_event(data: dict[str, Any]) -> tuple[str, str, dict[str, Any], str]:
    """Return platform, tool name, tool input, and cwd for supported hosts."""
    if isinstance(data.get("toolCall"), dict):
        call = data["toolCall"]
        args = call.get("args") if isinstance(call.get("args"), dict) else {}
        workspaces = data.get("workspacePaths") or []
        cwd = args.get("Cwd") or args.get("cwd") or args.get("workdir") or (
            workspaces[0] if workspaces else os.getcwd()
        )
        return "antigravity", str(call.get("name", "")), args, str(cwd)

    if isinstance(data.get("hook_event"), dict):
        event = data["hook_event"]
        tool_input = event.get("tool_input")
        if not isinstance(tool_input, dict):
            tool_input = {}
        cwd = (
            tool_input.get("cwd")
            or tool_input.get("workdir")
            or event.get("cwd")
            or event.get("workdir")
            or data.get("cwd")
            or data.get("workdir")
            or os.getcwd()
        )
        return "codex", str(event.get("tool_name", "")), tool_input, str(cwd)

    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}
    cwd = (
        tool_input.get("cwd")
        or tool_input.get("workdir")
        or data.get("cwd")
        or data.get("workdir")
        or os.getcwd()
    )
    return "claude", str(data.get("tool_name", "")), tool_input, str(cwd)


def patch_touches_protected(command: str, cwd: str) -> bool:
    for match in PATCH_PATH_RE.finditer(command):
        candidate = match.group(1) or match.group(2)
        if is_protected_path(candidate, cwd):
            return True
    return False


def command_mentions_protected(command: str) -> bool:
    target = protected_path()
    aliases = {
        str(target),
        target.as_posix(),
        "~/.local/bin/lake-build",
        "~\\.local\\bin\\lake-build",
        "$HOME/.local/bin/lake-build",
        "${HOME}/.local/bin/lake-build",
        "%USERPROFILE%\\.local\\bin\\lake-build",
        "%USERPROFILE%/.local/bin/lake-build",
        "$env:USERPROFILE\\.local\\bin\\lake-build",
        "$env:USERPROFILE/.local/bin/lake-build",
    }
    folded = command.casefold()
    return any(alias.casefold() in folded for alias in aliases)


def is_indirect_reference(value: str) -> bool:
    return bool(
        re.search(
            r"\$\(\s*(?:which|command\s+-v)\s+lake-build\s*\)",
            value,
            re.IGNORECASE,
        )
    )


def token_is_protected(token: str, cwd: str) -> bool:
    return is_protected_path(token, cwd)


def token_mentions_protected(token: str, cwd: str) -> bool:
    return (
        token_is_protected(token, cwd)
        or command_mentions_protected(token)
        or is_indirect_reference(token)
    )


def invocation_mutates_target(
    executable: str,
    args: list[str],
    cwd: str,
    mentions_target: bool,
) -> bool:
    """Return whether one parsed command can mutate the protected entry."""
    executable = executable.casefold()
    if executable in {"cp", "install", "ln"}:
        for index, arg in enumerate(args):
            if arg.startswith("--target-directory="):
                return token_mentions_protected(arg.split("=", 1)[1], cwd)
            if arg in {"--target-directory", "-t"} and index + 1 < len(args):
                return token_mentions_protected(args[index + 1], cwd)
        positional = [arg for arg in args if not arg.startswith("-")]
        return bool(positional and token_mentions_protected(positional[-1], cwd))
    if executable == "sed":
        return mentions_target and any(
            arg == "-i" or arg.startswith("-i") or arg.startswith("--in-place")
            for arg in args
        )
    if executable == "perl":
        return mentions_target and any(
            arg.startswith("-") and "i" in arg[1:] for arg in args
        )
    if executable == "dd":
        return any(
            arg.startswith("of=") and token_mentions_protected(arg[3:], cwd)
            for arg in args
        )
    if executable in {"bash", "cmd", "powershell", "pwsh", "sh", "zsh"}:
        command_flags = {"-c", "/c", "-command", "--command"}
        for index, arg in enumerate(args):
            if arg.casefold() in command_flags and index + 1 < len(args):
                nested = args[index + 1]
                if shell_touches_protected(nested, cwd):
                    return True
                if mentions_target and executable == "cmd":
                    return bool(re.search(
                        r"(?:^|\s)(?:copy|del|echo|erase|move|ren|rename)(?:\s|$)|[<>]",
                        nested,
                        re.IGNORECASE,
                    ))
                if mentions_target and executable in {"powershell", "pwsh"}:
                    return bool(re.search(
                        r"\b(?:Add|Clear|Copy|Move|New|Out|Remove|Rename|Set)-"
                        r"(?:Content|File|Item)\b",
                        nested,
                        re.IGNORECASE,
                    ))
        return False
    if executable in {"command", "env"}:
        nested = [
            arg
            for arg in args
            if not arg.startswith("-")
            and not re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", arg)
        ]
        if nested:
            return invocation_mutates_target(
                os.path.basename(nested[0]), nested[1:], cwd, mentions_target
            )
    if executable == "sudo":
        nested = [arg for arg in args if not arg.startswith("-")]
        if nested:
            return invocation_mutates_target(
                os.path.basename(nested[0]), nested[1:], cwd, mentions_target
            )
    if executable in {"node", "python", "python3", "ruby", "uv"}:
        mutation = re.search(
            r"\b(?:chmod|chown|remove|rename|replace|truncate|unlink|write|"
            r"writefile|write_text|write_bytes)\b|"
            r"open\s*\([^)]*,\s*['\"][^'\"]*(?:[wax]|\+)",
            " ".join(args),
            re.IGNORECASE,
        )
        return mentions_target and mutation is not None
    return mentions_target and executable in SHELL_MUTATORS


def shell_touches_protected(command: str, cwd: str) -> bool:
    """Recognize common shell writes to the managed path without blocking reads."""
    indirect = is_indirect_reference(command)
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>")
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return False

    mentions_target = (
        indirect
        or command_mentions_protected(command)
        or any(token_is_protected(token, cwd) for token in tokens)
    )
    if not mentions_target:
        return False

    for index, token in enumerate(tokens):
        if token in {">", ">>", ">|", "<>"}:
            if index + 1 < len(tokens) and token_is_protected(tokens[index + 1], cwd):
                return True

    command_tokens: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in {";", "&&", "||", "&", "|"}:
            if current:
                command_tokens.append(current)
                current = []
            continue
        current.append(token)
    if current:
        command_tokens.append(current)

    for segment in command_tokens:
        while segment and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", segment[0]):
            segment = segment[1:]
        if not segment:
            continue
        executable = os.path.basename(segment[0]).casefold()
        segment_mentions = indirect or any(
            token_mentions_protected(token, cwd)
            for token in segment
        )
        if invocation_mutates_target(executable, segment[1:], cwd, segment_mentions):
            return True
    return False


def deny(platform: str) -> None:
    reason = (
        "The deployed ~/.local/bin/lake-build is managed by the lean-usage "
        "SessionStart hook and must not be edited directly. Edit "
        "plugins/lean-usage/bin/lake-build in the plugin source and update the "
        "plugin instead."
    )
    if platform == "antigravity":
        print(json.dumps({"decision": "deny", "reason": reason}))
        return
    print(json.dumps({
        "systemMessage": f"[protect-lake-build] {reason}",
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        },
    }))


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        return

    platform, tool_name, tool_input, cwd = extract_event(data)
    lowered = tool_name.lower()
    blocked = False

    if lowered in {"edit", "write", "multiedit", "notebookedit"}:
        blocked = any(is_protected_path(path, cwd) for path in iter_declared_paths(tool_input))
    elif lowered == "apply_patch":
        command = (
            tool_input.get("command")
            or tool_input.get("patch")
            or tool_input.get("input")
            or ""
        )
        blocked = isinstance(command, str) and patch_touches_protected(command, cwd)
    elif lowered in {"bash", "run_command", "exec_command"}:
        command = (
            tool_input.get("command")
            or tool_input.get("CommandLine")
            or tool_input.get("cmd")
            or ""
        )
        blocked = isinstance(command, str) and shell_touches_protected(command, cwd)

    if blocked:
        deny(platform)


if __name__ == "__main__":
    main()
