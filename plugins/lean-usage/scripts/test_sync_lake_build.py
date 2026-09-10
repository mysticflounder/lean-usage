#!/usr/bin/env python3
# Copyright (c) 2026 Adam McKenna
# Released under GPL-3.0-or-later as described in the file LICENSE.
# Author: Adam McKenna <adam@mysticflounder.ai>
#
# test_sync_lake_build.py — regression tests for the SessionStart wrapper sync.
#
# Usage:
#   uv run --no-project python plugins/lean-usage/scripts/test_sync_lake_build.py

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parent.parent
HOOK = PLUGIN_ROOT / "hooks" / "sync-lake-build.py"
WRAPPER = PLUGIN_ROOT / "bin" / "lake-build"


class SyncLakeBuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory(prefix="sync lake build ")
        self.home = Path(self.tempdir.name)
        self.env = os.environ.copy()
        self.env["HOME"] = str(self.home)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_hook(self, payload: dict | None = None, hook: Path = HOOK) -> dict:
        result = subprocess.run(
            [sys.executable, str(hook)],
            input=json.dumps(payload or {}),
            text=True,
            capture_output=True,
            env=self.env,
            check=True,
        )
        self.assertEqual(result.stderr, "")
        self.assertTrue(result.stdout.strip())
        return json.loads(result.stdout)

    def context_command(self, output: dict) -> str:
        context = output["hookSpecificOutput"]["additionalContext"]
        start = "```sh\n"
        end = "\n```"
        self.assertIn(start, context)
        command = context.split(start, 1)[1]
        self.assertIn(end, command)
        return command.split(end, 1)[0]

    def assert_context_command(self, output: dict, wrapper: Path = WRAPPER) -> None:
        command = self.context_command(output)
        self.assertEqual(
            shlex.split(command),
            [str(Path(sys.executable).resolve()), str(wrapper.resolve())],
        )
        self.assertEqual(
            output["hookSpecificOutput"]["hookEventName"], "SessionStart"
        )

    def test_direct_command_does_not_require_local_bin_on_path(self) -> None:
        self.env["PATH"] = "/usr/bin:/bin"
        output = self.run_hook()
        self.assertTrue((self.home / ".local" / "bin" / "lake-build").is_symlink())
        self.assert_context_command(output)

    def test_session_start_includes_visible_experimental_notice(self) -> None:
        output = self.run_hook()
        self.assertIn("EXPERIMENTAL AI SOFTWARE", output["systemMessage"])
        self.assertIn("DISCLAIMER.md", output["systemMessage"])
        self.assert_context_command(output)

    def test_context_shell_quotes_wrapper_path_with_spaces(self) -> None:
        plugin = self.home / "plugin cache with spaces"
        copied_hook = plugin / "hooks" / "sync-lake-build.py"
        copied_wrapper = plugin / "bin" / "lake-build"
        copied_hook.parent.mkdir(parents=True)
        copied_wrapper.parent.mkdir(parents=True)
        shutil.copy2(HOOK, copied_hook)
        shutil.copy2(WRAPPER, copied_wrapper)

        output = self.run_hook(hook=copied_hook)
        command = self.context_command(output)
        self.assertIn(shlex.quote(str(copied_wrapper.resolve())), command)
        self.assert_context_command(output, copied_wrapper)

    def test_regular_file_collision_is_preserved(self) -> None:
        target = self.home / ".local" / "bin" / "lake-build"
        target.parent.mkdir(parents=True)
        original = b"local wrapper\n"
        target.write_bytes(original)

        output = self.run_hook()
        self.assertFalse(target.is_symlink())
        self.assertEqual(target.read_bytes(), original)
        self.assert_context_command(output)

    def test_symlink_install_is_idempotent(self) -> None:
        target = self.home / ".local" / "bin" / "lake-build"
        self.run_hook()
        first = target.lstat()
        self.assertEqual(target.resolve(), WRAPPER.resolve())

        output = self.run_hook()
        second = target.lstat()
        self.assertEqual(first.st_ino, second.st_ino)
        self.assert_context_command(output)

    def test_install_failure_still_emits_context(self) -> None:
        # A file where ~/.local/bin should be makes mkdir fail without touching
        # the real home directory.
        (self.home / ".local").write_text("not a directory\n")
        output = self.run_hook()
        self.assert_context_command(output)


if __name__ == "__main__":
    unittest.main()
