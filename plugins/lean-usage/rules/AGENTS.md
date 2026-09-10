# Lean 4 & Lake Usage Rules

House governance for Lean 4 theorem proving and builds.

## 1. Build Discipline
- **Use `lake-build`**: When builds are authorized, use the absolute wrapper command supplied by SessionStart; `lake-build` in these rules is shorthand for that command. Append `<Target>` for one target and never pass `build` yourself. Deliberate single-file/profiler checks and authorized mathlib source builds follow [build-operations.md](../skills/lean-usage/references/build-operations.md) and the target project's policy; this rule never overrides a no-build gate. No PATH edits are required. Where hooks are disabled, use `uv run --no-project python <plugin-root>/bin/lake-build` with the installed plugin path.
- **Mathlib Cache**: `lake-build` runs `lake exe cache get` itself in a Mathlib project and refuses to build from source if that prefetch fails. Run the cache command by hand only for a build that does not go through the wrapper.

## 2. Proof & Theorem Discipline
- **Proof tracking**: Keep structured proof goals, assumptions, and tractability evidence explicit and reviewable.
- **Promotion Policy**: Do not leave unverified `sorry` declarations in promoted proofs without an explicit tracking record.
