# Lean 4 & Lake Usage Rules

House governance for Lean 4 theorem proving and builds.

## 1. Build Discipline
- **Use `lake-build`**: Always invoke builds via the global `lake-build` wrapper (e.g. `lake-build build` or `lake-build <Target>`). Never invoke raw `lake build` or `lean` directly.
- **Mathlib Cache**: Before building any project that depends on Mathlib, ensure cache oleans are present with `lake exe cache get`.

## 2. Proof & Theorem Discipline
- **Proof tracking**: Keep structured proof goals, assumptions, and tractability evidence explicit and reviewable.
- **Promotion Policy**: Do not leave unverified `sorry` declarations in promoted proofs without an explicit tracking record.
