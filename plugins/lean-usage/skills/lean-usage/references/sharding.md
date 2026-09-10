# Sharding a large Lean file

Use this reference to split one oversized Lean module into bounded helper
modules plus a thin coordinator. For the decision to shard at all, read
[build-performance.md](build-performance.md#shard-deliberately).

This plugin ships no sharder. A project supplies its own script or CLI; this
reference is the contract that tool and its output must satisfy.

## Contents

- [Shape of a sharded file](#shape-of-a-sharded-file)
- [Budget the rendered bytes](#budget-the-rendered-bytes)
- [Choose block boundaries](#choose-block-boundaries)
- [Keep generation deterministic](#keep-generation-deterministic)
- [Record a manifest](#record-a-manifest)
- [Re-shard from a normalized source](#re-shard-from-a-normalized-source)
- [Validate the split](#validate-the-split)
- [Common failures](#common-failures)

## Shape of a sharded file

A split has two parts:

- **helpers** — each holds a whole number of source blocks and stays inside the
  byte budget. Give them a stable module prefix and a zero-padded index
  (`Pkg.Gen.Step_0001`) so the order is lexicographic and diffs stay small.
- **a coordinator** — a thin module that imports every helper in order and
  carries the public or aggregate declaration.

Write every helper first and the coordinator last. A failed run must never leave
a coordinator that imports a helper that does not exist.

Keep hand-written checkers, soundness theorems, and aggregate consumers out of
the generated payload. Read
[generated-proofs.md](generated-proofs.md#preserve-the-trust-boundary) for that
boundary.

## Budget the rendered bytes

The budget applies to the **rendered** helper — imports, prelude, and bodies —
not to the source slice. A slice that fits the budget can render larger.

- Plan the split as a dry run first. Check the shard count and the rendered
  sizes before you write files.
- Measure the budget for the workload. Working policies differ by two orders of
  magnitude; do not copy a number from another project.
- If one block alone exceeds the budget, split the block with a finer boundary.
  Do not emit an oversized shard. An overflow permission hides the real problem.

## Choose block boundaries

A block starts at a top-level declaration and runs to the next one. Good
boundaries are:

- independently meaningful lemmas;
- certificate steps or clause batches;
- generated payload kept apart from hand-written code.

Do not cut inside a proof body with a line rule. A split inside a term needs a
structured parser that knows the declaration, not a start-of-line match.

Keep the imports of each helper narrow. Shards that all carry broad imports can
increase total CPU even when wall-clock parallelism improves.

## Keep generation deterministic

For one source and one policy, every run must give the same shard count, file
names, module paths, and boundaries.

Remove unordered traversal, timestamps, host names, absolute paths, and random
identifiers from the output. Regenerate the same input twice and compare bytes
before you trust a cache or timing result. Read
[generated-proofs.md](generated-proofs.md#deterministic-generation).

## Record a manifest

Emit one record for each helper and one for the coordinator:

- module path and file path;
- rendered size in bytes;
- a checksum of the rendered bytes;
- block count and the helper imports.

Module path with checksum is enough to key a build cache. Store the generator
command and the source identity beside the manifest.

## Re-shard from a normalized source

A source file that was sharded before still imports the previous run's helpers.
Strip those imports and the coordinator import first.

- Normalization must be idempotent: normalize, shard, normalize again gives the
  same source.
- Skipping it bakes stale helper imports into the new helpers and inflates their
  rendered size.
- Do not hand-edit a generated helper. Change the source or the generator; the
  next run discards the edit.

## Validate the split

- Build the coordinator, not one helper. A green helper says nothing about the
  aggregate.
- Confirm that a real aggregate or CI target imports the new modules. An
  unimported helper is never built.
- Compare the axiom closure at the final consumer before and after. A split must
  not change a statement or a trust boundary.
- Compare module times to show that the split helped. Read
  [build-performance.md](build-performance.md#per-module-build-times).

## Common failures

- The budget was applied to source bytes instead of rendered bytes.
- The source was re-sharded without normalization, so helper imports are stale.
- An overflow permission passed a block that needed a finer boundary.
- The coordinator was written before its helpers.
- The shard count grew while the imports stayed broad, so total CPU rose.
- A generated helper was edited by hand.
