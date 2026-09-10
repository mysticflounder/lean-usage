# Generated proofs and artifacts

Use this reference for DRAT/LRAT or other certificate emitters, large generated
Lean trees, and project-owned olean archival.

## Contents

- [Preserve the trust boundary](#preserve-the-trust-boundary)
- [Deterministic generation](#deterministic-generation)
- [Emitter performance](#emitter-performance)
- [Bank large SAT certificates](#bank-large-sat-certificates)
- [Single-worker elaboration](#single-worker-elaboration)
- [Project-owned olean archival](#project-owned-olean-archival)

## Preserve the trust boundary

Generated source is not self-authenticating. Keep these layers explicit:

1. input/certificate and its exact encoding;
2. generator/emitter;
3. Lean checker and soundness theorem;
4. generated payload;
5. aggregate mathematical consumer;
6. actual kernel axiom closure.

Exclude bulk payload and term shards from search/mining only when scale requires
it. Keep hand-written checkers, soundness results, mathematical adapters, and
aggregate consumers visible to the call graph.

For native evaluation, apply the `native_decide` audit in
[proof-discipline.md](proof-discipline.md).

## Deterministic generation

Before optimizing or caching, regenerate identical input twice and compare bytes.
Remove nondeterminism from:

- unordered set/map traversal;
- timestamp, hostname, random ID, or absolute-path comments;
- counter allocation tied to unstable iteration order;
- floating-point formatting;
- environment-dependent imports or namespaces.

Store the generator command and input identity with the generated tree. Fix source
at the emitter; do not hand-edit generated Lean.

## Emitter performance

Profile representative p50/p90/p99 modules before changing the emitter. Common
high-leverage changes:

1. **Narrow imports.** Do not emit `import Mathlib.Tactic` when Core Lean or one
   tactic module suffices.
2. **Prefer direct case terms.** Large n-ary `rcases` trees can be slower than an
   emitted `match` with explicit constructors.
3. **Fix warning sources in the emitter.** If a generated family legitimately
   needs suppression, name only the specific linter at file scope.
4. **Remove emitted no-op tactics.** Linter/profiler hits such as ineffective
   `simp` calls usually indicate unconditional emitter output.
5. **Hoist repeated instances.** When typeclass inference is hot, bind stable
   `DecidableEq`/`Decidable` instances once or simplify the generated value type.
6. **Shard large proof terms.** Emit certificate-step or clause-batch lemmas into
   separate modules and compose them with a thin coordinator. Follow the split
   contract in [sharding.md](sharding.md).
7. **Scope resource overrides.** Follow the full
   [heartbeat policy](build-performance.md#heartbeat-policy). Prefer a measured finite
   declaration-local limit. Keep `maxHeartbeats 0` only for an exceptional,
   project-approved generated/certificate workload with separately bounded time,
   memory, input identity, and replay scope; remove it after structural fixes make a
   finite limit viable. Do not confuse it with `synthInstance.maxHeartbeats`, which
   applies specifically to typeclass synthesis.

After each change, regenerate the same corpus sample, compare profiler buckets,
build outputs, theorem statements, and axiom closures.

## Bank large SAT certificates

Separate Lean elaboration cost from certificate-checking cost before optimizing.
If one Lean process spends hours on one core before replay begins, inspect the
generated source for a giant inline CNF, LRAT, or clause-list literal. Sharding
only the later proof steps will not remove that front-loaded elaboration cost.

For an exact frozen DIMACS instance and a RUP-only Lean checker:

1. Solve the unchanged CNF with `cadical --plain` and retain the DRAT proof.
2. Run `drat-trim ... -L ...`; require both `s VERIFIED` and `0 RAT lemmas`.
   Treat `--plain` as a proof-shape heuristic, never as evidence by itself.
3. Densify sparse LRAT addition IDs and rewrite all hints and deletions
   consistently while preserving source-clause IDs. Independently replay the
   normalized certificate before generating Lean.
4. Avoid padding clause IDs with tautologies. A parser or checker may discard a
   tautological clause, so the apparent and checker-visible clause bases can
   differ.
5. Ingest the CNF without one enormous elaborated `List` literal: use a
   project-audited runtime DIMACS ingress, compact generated data, or bounded
   clause shards with a thin coordinator.
6. Replay the pure-RUP additions in bounded checkpointed windows. Each window
   must expose a proved state transition, and the coordinator must consume every
   window in order through the final empty clause.
7. Preserve hashes and generation commands for the CNF, DRAT, raw LRAT,
   normalized LRAT, verification log, replay manifest, and generated Lean.
8. Keep the semantic bridge explicit. Certificate replay establishes only that
   the encoded CNF is UNSAT; the publish theorem still needs an audited
   source-to-CNF or source-to-valuation theorem and a transitive axiom audit.

Do not send a general DRAT/RAT certificate to a RUP-only checker. If the checked
proof contains RAT additions, either retain a sound RAT-capable checker or
regenerate a genuinely zero-RAT proof.

## Single-worker elaboration

If Lake's scheduler fanout hurts a generated target, use the direct single-file
check described in [build-operations.md](build-operations.md). For emitted oleans,
add a project-tested helper that coordinates with `lake-build` and derives its
output paths from the active Lake version. Do not reuse the wrapper's PID-lock path
with `flock`; the protocols are different.

## Project-owned olean archival

An `.olean` is a compiled Lean environment, not proof-status evidence by itself.
It may depend on `sorryAx`, approved custom axioms, unsafe code elsewhere, or stale
inputs. Archive only after a successful build and an axiom audit of the intended
terminal theorem.

A sound reusable cache key must cover at least:

- exact Lean toolchain and Lake/output-layout version;
- module source;
- all transitive imported environments/inputs;
- generator and certificate inputs when source is emitted;
- build options that affect elaboration.

In current Lake 5 layouts, `<module>.olean.hash` is the output content hash; the
input fingerprint is the `depHash` stored in `<module>.trace`. Treat those names
as version-specific and let Lake compute/compare its input trace. Prefer a tested
content-addressed cache implementation (for example, adapting mathlib's Cache
code) over a shell recipe that copies files and touches mtimes.

If implementing a project cache:

1. define and document the key derivation before writing restore logic;
2. preserve the trace, olean/ilean content hashes, compiled environments, and any
   required IR artifacts in their exact Lake layout;
3. verify checksums on restore;
4. restore only into an idle, matching project/toolchain;
5. prove a cache hit by running Lake normally—never trick freshness with `touch`;
6. test miss, hit, changed source, changed import, changed toolchain, and corrupted
   artifact cases;
7. after restoration, let Lake validate the artifacts and repeat the terminal
   theorem's axiom/`sorry` audit;
8. keep off-host backup/retention policy separate from cache correctness.

Mathlib's `lake exe cache get` covers mathlib artifacts only. A project-generated
proof that takes hours needs its own audited archival/cache mechanism.
