#!/usr/bin/env python3
# Copyright (c) 2026 Adam McKenna
# Released under GPL-3.0-or-later as described in the file LICENSE.
# Author: Adam McKenna <adam@mysticflounder.ai>
#
# test_build_hooks.py — regression tests for build-related tool hooks.
#
# Usage:
#   uv run --no-project python plugins/lean-usage/scripts/test_build_hooks.py
"""Synthetic hook-event tests for cache, warning, and wrapper protection hooks."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / "hooks"


def invoke(hook: str, payload: dict, env: dict | None = None) -> dict | None:
    result = subprocess.run(
        [sys.executable, str(HOOKS / hook)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"{hook} failed: {result.stderr}")
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)


class BuildHookTests(unittest.TestCase):
    def make_mathlib_project(self, directory: str) -> Path:
        root = Path(directory) / "project"
        root.mkdir()
        (root / "lakefile.toml").write_text(
            '[[require]]\nname = "mathlib"\n', encoding="utf-8"
        )
        return root

    def test_cold_cache_allows_wrapper_but_denies_raw_build(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.make_mathlib_project(directory)
            wrapper = {
                "hook_event": {
                    "tool_name": "exec_command",
                    "cwd": str(ROOT),
                    "tool_input": {"cmd": "lake-build", "workdir": str(project)},
                }
            }
            self.assertIsNone(invoke("mathlib-cache-check.py", wrapper))

            raw = {
                "hook_event": {
                    "tool_name": "exec_command",
                    "cwd": str(ROOT),
                    "tool_input": {"cmd": "lake build", "workdir": str(project)},
                }
            }
            output = invoke("mathlib-cache-check.py", raw)
            self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_compound_command_still_denies_later_raw_build(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.make_mathlib_project(directory)
            payload = {
                "hook_event": {
                    "tool_name": "exec_command",
                    "cwd": str(ROOT),
                    "tool_input": {
                        "cmd": "lake-build && lake build",
                        "workdir": str(project),
                    },
                }
            }
            output = invoke("mathlib-cache-check.py", payload)
            self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_cd_with_assignment_resolves_later_build(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.make_mathlib_project(directory)
            payload = {
                "tool_name": "exec_command",
                "tool_input": {
                    "cmd": f"ROOT={directory} cd project && lake build",
                    "workdir": directory,
                },
            }
            output = invoke("mathlib-cache-check.py", payload)
            self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_bare_cd_expands_home_before_later_build(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            project = home / "project"
            project.mkdir(parents=True)
            (home / "lakefile.toml").write_text(
                '[[require]]\nname = "mathlib"\n', encoding="utf-8"
            )
            env = dict(os.environ, HOME=str(home))
            output = invoke("mathlib-cache-check.py", {
                "tool_name": "exec_command",
                "tool_input": {"cmd": "cd && lake build", "workdir": str(project)},
            }, env=env)
            self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_harmless_echo_is_not_a_build(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.make_mathlib_project(directory)
            payload = {
                "tool_name": "exec_command",
                "tool_input": {"cmd": "echo lake-build", "cwd": str(project)},
            }
            self.assertIsNone(invoke("mathlib-cache-check.py", payload))

    def test_exec_command_cmd_payload_warns_on_direct_build(self):
        payload = {
            "hook_event": {
                "tool_name": "exec_command",
                "tool_input": {"cmd": "lake build", "workdir": str(ROOT)},
            }
        }
        output = invoke("lean-direct-warn.py", payload)
        self.assertIn("Direct lake invocation detected", output["hookSpecificOutput"]["additionalContext"])

    def test_exec_command_cmd_payload_is_protected(self):
        payload = {
            "hook_event": {
                "tool_name": "exec_command",
                "cwd": str(ROOT),
                "tool_input": {
                    "cmd": "echo replacement > .local/bin/lake-build",
                    "workdir": str(Path.home()),
                },
            }
        }
        output = invoke("protect-lake-build.py", payload)
        self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_manifests_register_exec_command_for_build_hooks(self):
        for name in ("hooks/hooks.json", "codex-hooks.json"):
            data = json.loads((ROOT / name).read_text(encoding="utf-8"))
            groups = data["hooks"]["PreToolUse"]
            for script in ("lean-direct-warn.py", "mathlib-cache-check.py", "protect-lake-build.py"):
                group = next(
                    group for group in groups
                    if any(script in hook["command"] for hook in group["hooks"])
                )
                self.assertIn("exec_command", group["matcher"].split("|"))

    def test_flat_command_workdir_overrides_host_cwd(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.make_mathlib_project(directory)
            for command in ("lake build", "env FOO=bar lake build", "command lake build"):
                with self.subTest(command=command):
                    output = invoke("mathlib-cache-check.py", {
                        "tool_name": "exec_command", "cwd": str(ROOT),
                        "tool_input": {"cmd": command, "workdir": str(project)},
                    })
                    self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")
        output = invoke("protect-lake-build.py", {
            "tool_name": "exec_command", "cwd": str(ROOT),
            "tool_input": {
                "cmd": "echo replacement > .local/bin/lake-build",
                "workdir": str(Path.home()),
            },
        })
        self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_wrapper_does_not_hide_compound_direct_warning(self):
        output = invoke("lean-direct-warn.py", {
            "tool_name": "exec_command",
            "tool_input": {"cmd": "lake-build && lake build"},
        })
        self.assertIn("Direct lake invocation detected", output["hookSpecificOutput"]["additionalContext"])

    def test_direct_warning_sees_launcher_wrapped_build(self):
        for command in (
            "env FOO=bar lake build",
            "env -u FOO lake build",
            "command -p lake env lean Main.lean",
        ):
            with self.subTest(command=command):
                output = invoke("lean-direct-warn.py", {
                    "tool_name": "exec_command",
                    "tool_input": {"cmd": command},
                })
                self.assertIn("Direct lake invocation detected", output["hookSpecificOutput"]["additionalContext"])

    def test_cache_check_ignores_unrelated_mathlib_text(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            project.mkdir()
            (project / "lakefile.toml").write_text(
                "name = 'not-mathlib'\n# mathlib is discussed here, but not required\n",
                encoding="utf-8",
            )
            output = invoke("mathlib-cache-check.py", {
                "tool_name": "exec_command",
                "tool_input": {"cmd": "lake build", "workdir": str(project)},
            })
            self.assertIsNone(output)

    def test_cache_check_recognizes_scoped_lean_mathlib_requirement(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            project.mkdir()
            (project / "lakefile.lean").write_text(
                'require "leanprover-community" / "mathlib" @ git '
                '"https://github.com/leanprover-community/mathlib4"\n',
                encoding="utf-8",
            )
            output = invoke("mathlib-cache-check.py", {
                "tool_name": "exec_command",
                "tool_input": {"cmd": "lake build", "workdir": str(project)},
            })
            self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_hooks_ignore_malformed_payloads(self):
        payloads = (
            [],
            {"toolCall": {"name": "run_command", "args": "bad"}},
            {"hook_event": {"tool_name": "exec_command", "tool_input": "bad"}},
            {"tool_name": "exec_command", "tool_input": {"cmd": 123}},
        )
        for hook in (
            "lean-direct-warn.py",
            "mathlib-cache-check.py",
            "protect-lake-build.py",
        ):
            for payload in payloads:
                with self.subTest(hook=hook, payload=payload):
                    self.assertIsNone(invoke(hook, payload))


if __name__ == "__main__":
    unittest.main()
