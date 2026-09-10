#!/usr/bin/env python3
# Copyright (c) 2026 Adam McKenna
# Released under GPL-3.0-or-later as described in the file LICENSE.
# Author: Adam McKenna <adam@mysticflounder.ai>
#
# test_lake_build_lock.py — test lake-build locking, shims, cache checks, and telemetry.
#
# Usage:
#   uv run --no-project python plugins/lean-usage/scripts/test_lake_build_lock.py
"""Unit tests for lake-build's caller-aware PID lock."""

import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


sys.dont_write_bytecode = True


WRAPPER_PATH = Path(
    os.environ.get("LAKE_BUILD_UNDER_TEST")
    or Path(__file__).resolve().parent.parent / "bin" / "lake-build"
).resolve()


def load_wrapper():
    path = WRAPPER_PATH
    loader = importlib.machinery.SourceFileLoader("lake_build_under_test", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError(f"could not load lake-build from {path}")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


lake_build = load_wrapper()


class LakeBuildLockTests(unittest.TestCase):
    sid_vars = (
        "CODEX_THREAD_ID",
        "CODEX_SESSION_ID",
        "OPENCODE_SESSION_ID",
        "CLAUDE_SESSION_ID",
        "CLAUDE_CODE_SESSION_ID",
    )

    def setUp(self):
        self.env = mock.patch.dict(os.environ, {name: "" for name in self.sid_vars}, clear=False)
        self.env.start()
        os.environ.pop("TMUX_PANE", None)
        lake_build._STATE.update(wrap_dir=None, lockfile=None, lock_held=False, log_file=None)

    def tearDown(self):
        self.env.stop()
        lake_build._STATE.update(wrap_dir=None, lockfile=None, lock_held=False, log_file=None)

    def test_calling_session_is_null_without_sid_or_pane(self):
        with tempfile.TemporaryDirectory() as cwd:
            Path(cwd, ".current-session").write_text("sentinel\n", encoding="utf-8")
            with contextlib.chdir(cwd):
                self.assertEqual(lake_build.calling_session(), {"sid": None, "tmux_pane": None})

    def test_calling_session_precedence_and_aliases(self):
        values = {
            "CODEX_THREAD_ID": " thread ",
            "CODEX_SESSION_ID": "session",
            "OPENCODE_SESSION_ID": "opencode",
            "CLAUDE_SESSION_ID": "claude",
            "CLAUDE_CODE_SESSION_ID": "claude-code",
        }
        os.environ.update(values)
        os.environ["TMUX_PANE"] = " %1 "
        self.assertEqual(lake_build.calling_session(), {"sid": "thread", "tmux_pane": "%1"})

        for name in self.sid_vars[1:]:
            for key in self.sid_vars:
                os.environ[key] = ""
            os.environ[name] = f" {name.lower()} "
            self.assertEqual(lake_build.calling_session()["sid"], name.lower())

    def test_normalize_lockfile_anchors_relative_paths_to_invocation_cwd(self):
        with tempfile.TemporaryDirectory() as directory:
            invocation_cwd = Path(directory, "project", "work")
            self.assertEqual(
                lake_build.normalize_lockfile("lake-build.lock", str(invocation_cwd)),
                os.path.abspath(str(invocation_cwd / "lake-build.lock")),
            )
            self.assertEqual(
                lake_build.normalize_lockfile("../locks/./lake-build.lock", str(invocation_cwd)),
                os.path.abspath(str(invocation_cwd / "../locks/./lake-build.lock")),
            )
            absolute_path = invocation_cwd / ".lake" / "lake-build.lock"
            self.assertEqual(
                lake_build.normalize_lockfile(str(absolute_path), str(Path(directory, "other"))),
                os.path.abspath(str(absolute_path)),
            )

    def test_acquire_lock_writes_pid_and_json_metadata(self):
        os.environ["CODEX_SESSION_ID"] = ' codex-"session\nsecond-line '
        os.environ["TMUX_PANE"] = " %1 "
        with tempfile.TemporaryDirectory() as directory:
            lockfile = Path(directory, "lake-build.lock")
            build_log = Path(directory, "lake-build-logs", "build.log").resolve()
            with mock.patch.object(lake_build.os, "getpid", return_value=4242):
                lake_build.acquire_lock(str(lockfile), str(build_log))
            lines = lockfile.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(lines[0], "4242")
            self.assertEqual(json.loads(lines[1]), {
                "sid": 'codex-"session\nsecond-line', "tmux_pane": "%1",
                "build_log": str(build_log),
            })
            self.assertTrue(lake_build._STATE["lock_held"])

            lake_build.cleanup()

    def test_acquire_lock_records_null_build_log_when_unspecified(self):
        with tempfile.TemporaryDirectory() as directory:
            lockfile = Path(directory, "lake-build.lock")
            lake_build.acquire_lock(str(lockfile))
            self.assertIsNone(json.loads(lockfile.read_text(encoding="utf-8").splitlines()[1])["build_log"])
            lake_build.cleanup()

    def test_cleanup_removes_owned_lock_but_not_busy_other_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            owned = Path(directory, "owned.lock")
            owned.write_text("1\n", encoding="utf-8")
            wrap_dir = Path(directory, "wrap")
            wrap_dir.mkdir()
            lake_build._STATE.update(wrap_dir=str(wrap_dir), lockfile=str(owned), lock_held=True)
            lake_build.cleanup()
            self.assertFalse(owned.exists())
            self.assertFalse(wrap_dir.exists())

            busy = Path(directory, "busy.lock")
            busy.write_text("2\n", encoding="utf-8")
            lake_build._STATE.update(lockfile=str(busy), lock_held=False)
            lake_build.cleanup()
            self.assertTrue(busy.exists())

    def test_cleanup_closes_but_preserves_build_log(self):
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory, "build.log")
            log_file = log_path.open("w", encoding="utf-8")
            lockfile = Path(directory, "owned.lock")
            lockfile.write_text("1\n", encoding="utf-8")
            lake_build._STATE.update(log_file=log_file, lockfile=str(lockfile), lock_held=True)
            lake_build.cleanup()
            self.assertTrue(log_path.exists())
            self.assertTrue(log_file.closed)

    def test_log_write_failure_does_not_mask_notice_or_warn_again(self):
        broken_log = mock.Mock()
        broken_log.write.side_effect = OSError("disk full")
        lake_build._STATE["log_file"] = broken_log
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            lake_build.err("first notice")
            lake_build.err("second notice")
        output = stderr.getvalue()
        self.assertIn("first notice\n", output)
        self.assertIn("second notice\n", output)
        self.assertEqual(output.count("build log write failed"), 1)
        self.assertIsNone(lake_build._STATE["log_file"])
        broken_log.close.assert_called_once_with()

    def assert_busy(self, contents, kill_side_effect=None):
        with tempfile.TemporaryDirectory() as directory:
            lockfile = Path(directory, "lake-build.lock")
            lockfile.write_text(contents, encoding="utf-8")
            stderr = io.StringIO()
            kill_patch = mock.patch.object(
                lake_build.os, "kill", side_effect=kill_side_effect
            ) if kill_side_effect is not None else mock.patch.object(
                lake_build.os, "kill", return_value=None
            )
            with kill_patch, contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as caught:
                    lake_build.acquire_lock(str(lockfile))
            self.assertEqual(caught.exception.code, 1)
            self.assertEqual(lockfile.read_text(encoding="utf-8"), contents)
            return stderr.getvalue()

    def test_busy_legacy_pid_only_lock_keeps_old_error_shape(self):
        error = self.assert_busy("777\n")
        self.assertIn("another build is already running (pid 777)", error)
        self.assertNotIn("sid=", error)
        self.assertNotIn("tmux_pane=", error)

    def test_malformed_or_nonobject_metadata_cannot_bypass_live_lock(self):
        for metadata in ("not-json", "[]", '"sid"'):
            with self.subTest(metadata=metadata):
                error = self.assert_busy(f"777\n{metadata}\n")
                self.assertIn("another build is already running (pid 777)", error)

    def test_busy_error_includes_owner_details_with_repr_escaping(self):
        owner = {
            "sid": "owner'\n",
            "tmux_pane": "%1\\pane",
            "build_log": "/tmp/log'\npath",
        }
        error = self.assert_busy(f"777\n{json.dumps(owner)}\n")
        self.assertIn(f"sid={owner['sid']!r}", error)
        self.assertIn(f"tmux_pane={owner['tmux_pane']!r}", error)
        self.assertIn(f"build_log={owner['build_log']!r}", error)
        permission_error = self.assert_busy(
            f"777\n{json.dumps(owner)}\n", kill_side_effect=PermissionError
        )
        self.assertIn(f"build_log={owner['build_log']!r}", permission_error)

    def test_dead_lock_is_replaced_with_current_metadata(self):
        os.environ["OPENCODE_SESSION_ID"] = " opencode-1 "
        with tempfile.TemporaryDirectory() as directory:
            lockfile = Path(directory, "lake-build.lock")
            lockfile.write_text("777\n{" + '"sid":"old"' + "}\n", encoding="utf-8")
            with mock.patch.object(lake_build.os, "kill", side_effect=ProcessLookupError), mock.patch.object(
                lake_build.os, "getpid", return_value=888
            ):
                lake_build.acquire_lock(str(lockfile))
            lines = lockfile.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[0], "888")
            self.assertEqual(json.loads(lines[1]), {
                "sid": "opencode-1", "tmux_pane": None, "build_log": None,
            })

    @staticmethod
    def write_fake_lake(directory):
        fake = Path(directory, "fake-lake")
        fake.write_text(
            f"#!{sys.executable}\n"
            "import json\n"
            "import os\n"
            "from pathlib import Path\n"
            "import sys\n"
            "calls = os.environ.get('FAKE_LAKE_CALLS')\n"
            "if calls:\n"
            "    with Path(calls).open('a', encoding='utf-8') as fh:\n"
            "        fh.write(json.dumps(sys.argv[1:]) + '\\n')\n"
            "lock = Path(os.environ['LOCKFILE'])\n"
            "metadata = json.loads(lock.read_text(encoding='utf-8').splitlines()[1])\n"
            "print('FAKE_LAKE_STDOUT_SENTINEL')\n"
            "print('FAKE_LAKE_METADATA=' + json.dumps(metadata, sort_keys=True))\n"
            "print('FAKE_LAKE_STDERR_SENTINEL', file=sys.stderr)\n"
            "sys.stdout.flush()\n"
            "sys.stderr.flush()\n"
            "is_cache = sys.argv[1:] == ['exe', 'cache', 'get']\n"
            "exit_var = 'FAKE_CACHE_EXIT' if is_cache else 'FAKE_LAKE_EXIT'\n"
            "raise SystemExit(int(os.environ.get(exit_var, '0')))\n",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        return fake

    def run_integration_build(self, exit_code, custom_lock, relative_lock=False):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            lean_root = base / "lean-root"
            lean_root.mkdir()
            (lean_root / "lakefile.toml").write_text("", encoding="utf-8")
            fake_lake = self.write_fake_lake(base)
            tmp_dir = base / "tmp"
            tmp_dir.mkdir()
            lockfile = (base / "custom" / "wrapper.lock") if custom_lock else lean_root / ".lake" / "lake-build.lock"
            if relative_lock:
                lockfile = lean_root / "lake-build.lock"
            lockfile_value = os.path.relpath(lockfile, lean_root) if relative_lock else str(lockfile)
            expected_lockfile = (
                Path(os.path.realpath(lean_root), lockfile_value)
                if relative_lock else lockfile
            )
            if relative_lock:
                self.assertEqual(lockfile_value, "lake-build.lock")
                self.assertEqual(expected_lockfile, Path(os.path.realpath(lean_root), "lake-build.lock"))
            state_dir = base / "state"
            env = os.environ.copy()
            env.update({
                "LEAN_ROOT": str(lean_root),
                "LOCKFILE": lockfile_value,
                "LEAN_USAGE_STATE_DIR": str(state_dir),
                "TMPDIR": str(tmp_dir),
                "REAL_LAKE": str(fake_lake),
                "REAL_LEAN": "/bin/true",
                "LAKE_BUILD_NO_MODULE_STATS": "1",
                "FAKE_LAKE_EXIT": str(exit_code),
                "CODEX_SESSION_ID": "integration-session",
                "TMUX_PANE": "%integration",
            })
            result = subprocess.run(
                [sys.executable, str(WRAPPER_PATH)],
                cwd=lean_root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, exit_code, result.stderr)
            self.assertFalse(lockfile.exists())
            marker = next(line for line in result.stdout.splitlines() if line.startswith("FAKE_LAKE_METADATA="))
            metadata = json.loads(marker.split("=", 1)[1])
            self.assertEqual(metadata["sid"], "integration-session")
            self.assertEqual(metadata["tmux_pane"], "%integration")
            log_path = Path(metadata["build_log"])
            self.assertTrue(log_path.is_absolute())
            self.assertEqual(log_path.parent, expected_lockfile.parent / "lake-build-logs")
            self.assertTrue(log_path.exists())
            log_text = log_path.read_text(encoding="utf-8")
            self.assertIn("FAKE_LAKE_STDOUT_SENTINEL", log_text)
            self.assertIn("FAKE_LAKE_STDERR_SENTINEL", log_text)
            self.assertIn(f"lake build exited {exit_code}", log_text)
            stats_lines = (state_dir / "build-stats.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(stats_lines), 1)
            self.assertEqual(json.loads(stats_lines[0])["build_log"], str(log_path))
            self.assertIn("FAKE_LAKE_STDOUT_SENTINEL", result.stdout)
            self.assertIn("FAKE_LAKE_STDERR_SENTINEL", result.stdout)
            self.assertIn(f"lake build exited {exit_code}", result.stderr)

    def test_main_persists_build_log_and_stats_for_success_and_failure(self):
        self.run_integration_build(0, custom_lock=False)
        self.run_integration_build(7, custom_lock=True)

    def test_main_accepts_relative_lockfile_end_to_end(self):
        self.run_integration_build(0, custom_lock=False, relative_lock=True)

    def test_mathlib_cache_prefetch_runs_before_build_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            lean_root = base / "lean-root"
            lean_root.mkdir()
            (lean_root / "lakefile.toml").write_text(
                '[[require]]\nname = "mathlib"\ngit = "https://github.com/leanprover-community/mathlib4"\n',
                encoding="utf-8",
            )
            fake_lake = self.write_fake_lake(base)
            calls = base / "calls.jsonl"
            common_env = os.environ.copy()
            common_env.update({
                "LEAN_ROOT": str(lean_root),
                "LOCKFILE": str(base / "lake-build.lock"),
                "LEAN_USAGE_STATE_DIR": str(base / "state"),
                "TMPDIR": str(base),
                "REAL_LAKE": str(fake_lake),
                "REAL_LEAN": "/bin/true",
                "LAKE_BUILD_NO_MODULE_STATS": "1",
                "FAKE_LAKE_CALLS": str(calls),
                "FAKE_LAKE_EXIT": "0",
            })

            success_env = dict(common_env, FAKE_CACHE_EXIT="0")
            success = subprocess.run(
                [sys.executable, str(WRAPPER_PATH)], cwd=lean_root, env=success_env,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
            )
            self.assertEqual(success.returncode, 0, success.stderr)
            self.assertEqual(
                [json.loads(line) for line in calls.read_text(encoding="utf-8").splitlines()],
                [["exe", "cache", "get"], ["build"]],
            )

            calls.unlink()
            failure_env = dict(common_env, FAKE_CACHE_EXIT="9")
            failure = subprocess.run(
                [sys.executable, str(WRAPPER_PATH)], cwd=lean_root, env=failure_env,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
            )
            self.assertEqual(failure.returncode, 9, failure.stderr)
            self.assertEqual(
                [json.loads(line) for line in calls.read_text(encoding="utf-8").splitlines()],
                [["exe", "cache", "get"]],
            )
            self.assertIn("refusing source build", failure.stderr)

    def test_mathlib_detection_is_dependency_specific(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "lakefile.toml").write_text(
                'name = "mathlib-themed-project"\n'
                '[[require]]\nname = "other-package"\n'
                '[package]\nsummary = "mathlib is mentioned in documentation"\n',
                encoding="utf-8",
            )
            self.assertFalse(lake_build.uses_mathlib(str(root)))

            (root / "lakefile.lean").write_text(
                'require "leanprover-community" / "mathlib" @ git '
                '"https://github.com/leanprover-community/mathlib4"\n',
                encoding="utf-8",
            )
            self.assertTrue(lake_build.uses_mathlib(str(root)))

    def test_busy_main_does_not_create_build_log(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            lean_root = base / "lean-root"
            lean_root.mkdir()
            (lean_root / "lakefile.toml").write_text("", encoding="utf-8")
            tmp_dir = base / "tmp"
            tmp_dir.mkdir()
            lockfile = base / "custom" / "wrapper.lock"
            lockfile.parent.mkdir()
            busy_log = (lockfile.parent / "lake-build-logs" / "busy.log").resolve()
            lockfile.write_text(
                f"{os.getpid()}\n"
                + json.dumps({"sid": "busy-session", "tmux_pane": "%busy", "build_log": str(busy_log)})
                + "\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env.update({
                "LEAN_ROOT": str(lean_root),
                "LOCKFILE": str(lockfile),
                "TMPDIR": str(tmp_dir),
                "REAL_LAKE": "/bin/true",
                "REAL_LEAN": "/bin/true",
                "LEAN_USAGE_STATE_DIR": str(base / "state"),
            })
            result = subprocess.run(
                [sys.executable, str(WRAPPER_PATH)], cwd=lean_root, env=env,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn(f"sid='busy-session'", result.stderr)
            self.assertIn(f"tmux_pane='%busy'", result.stderr)
            self.assertIn(f"build_log={str(busy_log)!r}", result.stderr)
            self.assertFalse((lockfile.parent / "lake-build-logs").exists())
            self.assertFalse(busy_log.exists())


if __name__ == "__main__":
    unittest.main()
