#!/usr/bin/env python3
# Copyright (c) 2026 Adam McKenna
# Released under GPL-3.0-or-later as described in the file LICENSE.
# Author: Adam McKenna <adam@mysticflounder.ai>
#
# test_lake_build_edit_guard.py — regression tests for the deployed-wrapper guard.
#
# Usage:
#   uv run --no-project python plugins/lean-usage/scripts/test_lake_build_edit_guard.py

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parent.parent
GUARD = PLUGIN_ROOT / "hooks" / "protect-lake-build.py"
SYNC = PLUGIN_ROOT / "hooks" / "sync-lake-build.py"


class LakeBuildEditGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.home = Path(self.tempdir.name)
        self.target = self.home / ".local" / "bin" / "lake-build"
        self.env = os.environ.copy()
        self.env["HOME"] = str(self.home)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_guard(self, payload: dict) -> dict | None:
        result = subprocess.run(
            [sys.executable, str(GUARD)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=self.env,
            check=True,
        )
        if not result.stdout.strip():
            return None
        return json.loads(result.stdout)

    def assert_denied(self, payload: dict) -> None:
        output = self.run_guard(payload)
        self.assertIsNotNone(output)
        hook_output = output.get("hookSpecificOutput", {})
        decision = hook_output.get("permissionDecision") or output.get("decision")
        self.assertEqual(decision, "deny")
        self.assertIn("managed", json.dumps(output))

    def bash_payload(self, command: str) -> dict:
        return {
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": str(self.home),
        }

    def test_blocks_direct_file_edit_tools(self) -> None:
        for tool_name, path_key, path in (
            ("Edit", "file_path", str(self.target)),
            ("Write", "file_path", "~/.local/bin/lake-build"),
            ("NotebookEdit", "notebook_path", str(self.target)),
        ):
            with self.subTest(tool_name=tool_name):
                self.assert_denied({
                    "tool_name": tool_name,
                    "tool_input": {path_key: path},
                    "cwd": str(self.home),
                })

    def test_blocks_codex_apply_patch(self) -> None:
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {self.target}\n"
            "@@\n-old\n+new\n"
            "*** End Patch\n"
        )
        payloads = (
            {
                "tool_name": "apply_patch",
                "tool_input": {"command": patch},
                "cwd": str(self.home),
            },
            {
                "hook_event": {
                    "tool_name": "apply_patch",
                    "tool_input": {"command": patch},
                    "cwd": str(self.home),
                }
            },
            {
                "tool_name": "apply_patch",
                "tool_input": {"input": patch},
                "cwd": str(self.home),
            },
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                self.assert_denied(payload)

    def test_blocks_common_shell_mutations(self) -> None:
        commands = (
            "echo replacement > ~/.local/bin/lake-build",
            "rm ~/.local/bin/lake-build",
            "cp replacement ~/.local/bin/lake-build",
            "sed -i s/old/new/ ~/.local/bin/lake-build",
            "cat replacement | tee ~/.local/bin/lake-build",
            "printf replacement | sudo tee ~/.local/bin/lake-build",
            "python -c 'open(\"~/.local/bin/lake-build\", \"w\")'",
            "sed -i s/old/new/ $(which lake-build)",
            "cp replacement \"$(which lake-build)\"",
            "cp --target-directory ~/.local/bin/lake-build replacement",
            "zsh -c 'echo replacement > ~/.local/bin/lake-build'",
            "PowerShell -Command 'Set-Content ~/.local/bin/lake-build replacement'",
            "python3 -c 'open(\"~/.local/bin/lake-build\", \"r+\")'",
            "env cp replacement ~/.local/bin/lake-build",
            "command cp replacement ~/.local/bin/lake-build",
            "cmd /c \"echo replacement > %USERPROFILE%\\.local\\bin\\lake-build\"",
            "PowerShell -Command \"Set-Content "
            "$env:USERPROFILE\\.local\\bin\\lake-build replacement\"",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assert_denied(self.bash_payload(command))

    def test_allows_reads_execution_and_source_edits(self) -> None:
        allowed_payloads = (
            self.bash_payload("cat ~/.local/bin/lake-build"),
            self.bash_payload("sed -n 1,20p ~/.local/bin/lake-build"),
            self.bash_payload("cp ~/.local/bin/lake-build /tmp/lake-build.backup"),
            self.bash_payload("~/.local/bin/lake-build Foo.Bar"),
            self.bash_payload(
                "python3 -c 'print(open(\"~/.local/bin/lake-build\").read())'"
            ),
            self.bash_payload(
                "python3 -c 'open(\"~/.local/bin/lake-build.bak\", \"w\").write(\"x\")'"
            ),
            {
                "tool_name": "Edit",
                "tool_input": {"file_path": str(PLUGIN_ROOT / "bin" / "lake-build")},
                "cwd": str(PLUGIN_ROOT),
            },
            {
                "tool_name": "apply_patch",
                "tool_input": {
                    "command": "*** Begin Patch\n*** Update File: README.md\n*** End Patch\n"
                },
                "cwd": str(PLUGIN_ROOT),
            },
        )
        for payload in allowed_payloads:
            with self.subTest(payload=payload):
                self.assertIsNone(self.run_guard(payload))

    def test_patch_header_with_crlf_still_blocks(self) -> None:
        patch = (
            "*** Begin Patch\r\n"
            f"*** Update File: {self.target}\r\n"
            "@@\r\n-old\r\n+new\r\n"
            "*** End Patch\r\n"
        )
        self.assert_denied({
            "tool_name": "apply_patch",
            "tool_input": {"command": patch},
            "cwd": str(self.home),
        })

    def test_antigravity_denial_shape(self) -> None:
        output = self.run_guard({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "rm ~/.local/bin/lake-build", "Cwd": str(self.home)},
            }
        })
        self.assertEqual(output.get("decision"), "deny")

    def test_sync_preserves_unexpected_regular_file(self) -> None:
        self.target.parent.mkdir(parents=True)
        self.target.write_text("local work\n", encoding="utf-8")
        subprocess.run(
            [sys.executable, str(SYNC)],
            input="{}",
            text=True,
            capture_output=True,
            env=self.env,
            check=True,
        )
        self.assertFalse(self.target.is_symlink())
        self.assertEqual(self.target.read_text(encoding="utf-8"), "local work\n")

    def test_sync_installs_symlink_when_target_is_missing(self) -> None:
        subprocess.run(
            [sys.executable, str(SYNC)],
            input="{}",
            text=True,
            capture_output=True,
            env=self.env,
            check=True,
        )
        self.assertTrue(self.target.is_symlink())
        self.assertEqual(self.target.resolve(), (PLUGIN_ROOT / "bin" / "lake-build").resolve())

    def test_sync_skips_repeated_antigravity_invocation(self) -> None:
        subprocess.run(
            [sys.executable, str(SYNC)],
            input=json.dumps({"invocationNum": 2}),
            text=True,
            capture_output=True,
            env=self.env,
            check=True,
        )
        self.assertFalse(self.target.exists())

    def test_hook_manifests_register_guard_for_edit_tools(self) -> None:
        for manifest_name in ("hooks/hooks.json", "codex-hooks.json"):
            with self.subTest(manifest=manifest_name):
                data = json.loads((PLUGIN_ROOT / manifest_name).read_text(encoding="utf-8"))
                groups = data["hooks"]["PreToolUse"]
                guard_groups = [
                    group
                    for group in groups
                    if any("protect-lake-build.py" in hook["command"] for hook in group["hooks"])
                ]
                self.assertEqual(len(guard_groups), 1)
                matcher = set(guard_groups[0]["matcher"].split("|"))
                self.assertTrue({
                    "Bash",
                    "run_command",
                    "apply_patch",
                    "Write",
                    "Edit",
                    "MultiEdit",
                    "NotebookEdit",
                }.issubset(matcher))


if __name__ == "__main__":
    unittest.main()
