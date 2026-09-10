# Lean 4 & Lake Usage Rules

House governance for Lean 4 theorem proving and builds.

## 1. Build Discipline
- **Use `lake-build`**: Always invoke builds via the global `lake-build` wrapper: `lake-build` for the whole project, `lake-build <Target>` for one target. Arguments are forwarded verbatim to `lake build`, so never pass `build` yourself. Never invoke raw `lake build` or `lean` directly. The plugin's session hook installs the wrapper on `PATH` only where the user trusts plugin hooks; if the bare name is missing, run the plugin's own `bin/lake-build` by path.
- **Mathlib Cache**: `lake-build` runs `lake exe cache get` itself in a Mathlib project and refuses to build from source if that prefetch fails. Run the cache command by hand only for a build that does not go through the wrapper.

## 2. Proof & Theorem Discipline
- **Proof tracking**: Keep structured proof goals, assumptions, and tractability evidence explicit and reviewable.
- **Promotion Policy**: Do not leave unverified `sorry` declarations in promoted proofs without an explicit tracking record.
