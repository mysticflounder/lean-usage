# Release audit and Linux Docker smoke test

Date: 10 September 2026. Plugin version: 0.1.70.

## Corrections

- SessionStart supplies an absolute Python/interpreter-and-wrapper command. No
  `~/.local/bin` PATH setup is required; the symlink remains optional and unexpected
  regular files are preserved. The skill and installation docs use this contract.
- Hooks tolerate malformed event payloads, recognize common launcher-wrapped
  commands, and avoid treating backup paths as the deployed wrapper.
- Mathlib dependency detection distinguishes declarations from incidental text in
  both the wrapper and cache hook, including scoped Lean requirements and the
  Python 3.10 TOML fallback.
- Build-time advice now keeps concurrent work outside the running source graph.
- Skill guidance clarifies no-build gates, unavailable-cache upgrade handling,
  text DRAT output, toolchain prerequisites, and preserving inputs before in-place
  shard normalization.

## Verification

- All 46 regression tests passed on macOS and Linux: 17 wrapper, 10 edit guard,
  14 build hook, and 5 SessionStart tests.
- All three skills passed structural validation; the independent reference review
  found no broken relative links.
- `bash scripts/test-docker.sh` passed on Linux/aarch64 using Debian Bookworm,
  Python 3.12, and Lean 4.28.0. The Dockerfile pins the uv base-image digest and Lean
  version. Debian package downloads still use the configured package repositories.
- Docker mounted the source read-only and tested a disposable copy. Runtime
  networking was disabled; no host credentials or Docker socket were mounted.
- The actual SessionStart JSON command was extracted and executed with
  `PATH=/usr/bin:/bin`, excluding both `~/.local/bin` and the image's Python/uv bin
  directory. Bare `lake-build` was confirmed unavailable.
- A real `lake init smoke lib` project built through the supplied wrapper command.
  A second build recompiled zero modules. Both recorded exit code zero, and the
  relative lockfile was cleaned up.

## Boundaries

These are runtime smoke tests and synthetic hook-event tests, not a live
Claude/Codex agent evaluation. The independent skill review exercised instruction
consistency, not autonomous proof completion. Windows and Linux/x86_64 were not
tested in this pass. Real mathlib downloads, large certificate replay, and the
external user-supplied lean-shard/DRAT-to-Lean tools were not exercised. Cache
prefetch success/failure behavior is covered with fixtures.

The container is removed on exit. The local `lean-usage-release-test` image remains
available for subsequent runs.
