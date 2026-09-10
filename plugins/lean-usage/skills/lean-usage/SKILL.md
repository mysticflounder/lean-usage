---
name: lean-usage
description: "Use alongside the generic Lean 4 skill in governed Lean repositories for the house build workflow, project-indexed theorem reuse, proof obligations and tractability, axiom/native/external-evidence trust audits, or promotion and publication."
---

# Lean Usage

This is the house governance and runtime overlay, not a general Lean manual. Use the
generic Lean skill for tactics, syntax, proof-state work, and ordinary refactoring.

Discover and read every applicable instruction file recognized by the active host or
explicitly named by a parent policy, then apply the host's documented precedence
chain. Read [repository-policy.md](references/repository-policy.md) to record the
effective contract. In particular, `lake-build` is the required build path when a
build is authorized; it is not permission to build through an explicit no-build gate.

## Core workflow

1. **Read the live project contract.** Discover the project and Lake roots, applicable
   instruction chain, pinned toolchain, active plan/closure matrix, theorem-bank
   registries, trust profile, and build or publication gates.
2. **Refresh current truth.** Read current source and imports. When a project
   provides an indexed status or dependency view, refresh it before relying on
   its snapshots, anchors, or line numbers.
3. **Search before proving.** Search project banks first, then the indexed Lean
   corpora. Treat search hits as candidates until the reuse preflight below passes.
4. **Make grounded progress.** Prove a useful result, shrink the target's freedom,
   or improve supporting infrastructure/tests/docs in a way the active plan needs.
   Do not commit wrapper networks or equivalent reformulations as proof progress.
5. **Validate proportionally.** Build the smallest affected target first, then run
   broader and publication gates only when authorized and appropriate. Audit warnings,
   import reachability, dependency edges, and axioms—not only exit status.
6. **Synchronize the record.** When the theorem frontier changes, update all living
   status/plan docs in the same change so stale claims do not remain authoritative.

## Theorem search and reuse preflight

Before deriving a finite pattern, incidence lemma, local contradiction, or helper,
search the current project first, then the cross-project corpora.

Use the project's own indexed search command when one is available; it is the
fastest way to search declarations, statements, and docstrings in the CURRENT
project. Otherwise use the repository's documented search facilities:

```bash
rg -n "<terms>" .
```

For the CROSS-PROJECT route, use the host's generic indexed search over all
configured Lean corpora when one is available. This plugin does not ship an
indexer. Without an indexed search, search the project's own mathlib checkout
under `.lake/packages/mathlib` and any other configured corpora with the
repository's documented facilities.

Use both project terminology and concept-level mathematical language. Treat every
search hit as a candidate until the reuse preflight below passes.

Use `rg` for source navigation once you know which declaration you want, not as
the theorem-discovery tool.

Before reusing a candidate, verify:

- its exact current statement and hypotheses;
- source path, current elaboration, and import reachability from the consumer;
- kernel axiom closure and any approved trust boundary;
- a hypothesis-by-hypothesis map from the live obligation;
- the first missing antecedent, circularity risk, and immediate consumer.

A contradiction consumer without a producer for its hypotheses is not a closure route.
A precise negative compatibility result is still useful: record it before deriving anew.

A reuse search is scoped to one concrete search key: the proposed statement and
available hypotheses, its intended immediate consumer, and the relevant
source/import revision. Record the best candidates and the first missing
antecedent or circularity. Do not repeat semantic corpus or literature search
while that key is unchanged. Source navigation, elaboration, and proof debugging
may continue without restarting semantic search. Re-run the reuse preflight only
when the candidate statement, ingress, consumer, imports, or relevant source
revision materially changes.

A project may define its own iteration-scoped search checkpoint whose evidence is
limited to the current iteration. That checkpoint and this reuse preflight are
separate gates; passing one does not satisfy the other.

## Proof obligations and tractability

The summary below covers common gates. [proof-discipline.md](references/proof-discipline.md)
is the canonical policy; consult it for the full contract and resolve any summary
drift in its favor, subject to the target repository's instruction precedence.

- Before reporting a goal blocked or escalating proof work, record the bounded
  standard automation attempted under the generic Lean skill and the exact remaining
  goal and relevant hypotheses. If an attempt was inapplicable or execution was
  gated, state why. Do not repeat unchanged failed attempts; retry when the goal,
  hypotheses, or available rules materially change. Automation failure alone is
  not evidence that a new mathematical lemma is necessary.
- Before production mathematical proof or Lean promotion work, read the relevant
  docs and active closure plan. Require plan coverage for every current
  headline/publish-reachable `sorry`. If one of them is uncovered by the plan,
  stop and ask. This gate does not apply to configuration, repository audits, or other
  non-proof maintenance. Scratch theorem proving is still proof work, not
  maintenance; while coverage is missing, continue only the read-only source and
  plan audit needed to resolve it.
- Represent an in-project unproved obligation as a `sorry`-backed theorem against an
  explicit statement, not a named `axiom` and never a silent `True` placeholder.
- Every `sorry` introduced or actively refactored by the current plan must be
  load-bearing for the headline/publish theorem and wired to its consumer.
- For each production promotion change, name the publish target, residual,
  immediate consumer, and an explicit well-founded measure on the obligation
  frontier. Accept the change as proof progress only when that measure strictly
  decreases. A kernel-checked case split may increase the raw `sorry` count only
  when the split is proved exhaustive, every new leaf is relevant, every branch
  strictly narrows the recorded measure, and aggregate expected closure cost
  decreases.
- Record the coordinator-interface frontier before and after the change, publish
  reachability, chosen measure, and immediate constructor fan-out in the active
  closure plan. Report the named residual and verify it with a fresh project
  status/dependency query; a standalone green `lake-build` is insufficient.
- If the obligation cannot be wired to its intended consumer, stop and report the
  exact blocker instead of adding unrelated lemmas. State the target, residual,
  measure, direct consumer, and strict reduction requirement in every production
  Lean dispatch.
- Judge decomposition by aggregate tractability, not raw `sorry` count. Many named,
  independently buildable branch leaves can be better than one theorem hiding many
  case holes when the measured frontier narrows. Do not create orphan obligations
  merely to improve a count.
- Named axioms are reserved for genuine external assumptions with project approval,
  reason, and citation. Never approve a local IOU as an external axiom.
- Label a statement-only or `sorry`-bearing formalization `SKETCH — NOT PROMOTABLE`.
  Compilation of a sketch is statement/type feedback, never proof or promotion.
- Establish reachability from the headline theorem by source/import inspection,
  make the consumer explicit in the change, and use the repository's active-plan
  measure for the same strict-reduction check.

Read [proof-discipline.md](references/proof-discipline.md) before changing obligations,
using `native_decide`, importing archived/mined Lean, or evaluating solver evidence.
When a worker cannot load this skill, copy the compact
[worker/promotion contract](references/worker-promotion-contract.md) verbatim between
its markers; do not hand-write a new policy summary.

## Evidence and claim scope

Use the rigor labels `PROVEN`, `CONJECTURED`, `EMPIRICALLY VERIFIED`, and `HEURISTIC`
for claims. For computations, also state whether the result is exhaustive within a
specified abstraction, externally exact, or sampled. Exhausting a finite abstraction
does not by itself prove the intended geometric or ambient theorem.

Generated metadata, normalized statement shapes, a source scan with no `sorry`, solver
output, and old `.olean` files are discovery evidence—not current kernel proof or
immediate applicability. Require a fresh build and axiom audit before calling archived
or unimported Lean reusable. State the exact trust boundary of SAT/SMT/CAS/native
computation rather than upgrading it to “kernel checked.”

Any solver or certificate artifact that names or relies on a Lean declaration must pass
the Lean-ingress publication gate before it is described as promoted, publishable, or
consumer-reachable. An isolated module build, theorem-name string, source comment, or
unverified source hash is not sufficient. Omission of any bound field is fail-closed:
the artifact may remain diagnostic, but it carries no promotion claim. Read
[Lean-ingress publication gate](references/proof-discipline.md#lean-ingress-publication-gate)
before promoting solver or generated evidence into Lean.

Preserve durable statement provenance for every promoted declaration: exact informal
source and version, the formal declaration and statement, hypothesis-by-hypothesis
mapping, named final consumer, and any deliberate semantic delta. A chat transcript or
scratch note is not a durable provenance record.

Before freezing, replaying, archiving, or publishing a certificate bank, read
[freezing-certificate-banks.md](references/freezing-certificate-banks.md).

## Build quick start

```bash
lake-build                 # whole project
lake-build Foo.Bar         # one target
lake-build --jobs 4        # forwarded to `lake build`; advisory, not a hard cap
```

`lake-build` reaches `PATH` through the plugin's SessionStart hook, and a host runs a
plugin hook only when the user trusts it. Do not assume the wrapper is installed. If
the bare name is not found, run the plugin's own `bin/lake-build` by path, or symlink
it into a directory on `PATH`; see
[build-operations.md](references/build-operations.md#lake-build).

In a mathlib project the wrapper runs `lake exe cache get` itself and refuses to build
from source when that prefetch fails. Run the cache command by hand only for a build
that does not go through the wrapper:

```bash
cd <lake-root>
lake exe cache get         # only without lake-build; mathlib oleans, per project
```

Honor repository heartbeat caps. Profile and refactor/split first; use only the
smallest measured, permitted, declaration-scoped finite override. `maxHeartbeats 0`
is exceptional generated/certificate policy, never a default, and
`synthInstance.maxHeartbeats` is a distinct typeclass-synthesis budget. Read the
full [heartbeat policy](references/build-performance.md#heartbeat-policy).

`lake-build` locates the Lake root, serializes top-level builds per project, prefetches
the mathlib cache, requests each Lean worker's memory setting through a temporary
PATH shim, records timing, and cleans up its lock/shim. Lake commonly invokes its
compiler by absolute path, so the shim can be bypassed; `MEMORY_MB` is a requested
setting, not proof that an effective memory cap was enforced. Build status and
publication records are project-owned; follow the project's own refresh commands and
gates when they exist.

Do not edit files in the running build's source graph and then cite that build as
validation of the edited state. Prepare notes or the next change separately and wait
for a fresh build after source changes.

Build time is work time, not wait time. Always run `lake-build` in the background.
If the harness automatically delivers a completion notice with the build's exit status
and output, rely on it. Otherwise, collect the terminal result via the returned session
ID using the host's blocking session-wait operation. Never busy-poll: no `sleep`,
repeated status or log checks, `tail -f`, or watch loops.

Spend that interval on work the plan needs that stays outside the build's source
graph: theorem search and reuse preflight, reading references and dead-ends, drafting
the next change as notes, updating status/plan docs, or auditing prior output. If the
build result is genuinely the sole blocker and nothing else is in flight, end the turn
only when the host can resume it via a completion notice; otherwise, use the host's
blocking session-wait operation. Do not busy-poll to hold the turn open.

Read [build-operations.md](references/build-operations.md) for root detection,
environment overrides, concurrency, direct single-file exceptions, and mathlib cache.
Read [build-performance.md](references/build-performance.md) when a build is slow.

## Validation closeout

- A green root target says nothing about modules outside its import closure. Build any
  active unimported module explicitly or add it to a real aggregate/CI target.
- Treat warnings introduced or touched by the change as defects. In a noisy inherited
  tree, record the baseline and avoid unrelated cleanup unless it is in scope.
- Confirm fresh source/dependency status, actual axiom closure, focused tests, and
   the project's publication gate when publishing.
- Audit the actual exported/final consumer, not only a helper: run transitive axiom
  closure and classify `sorryAx`, custom axioms, `Lean.ofReduceBool`/native trust,
  `unsafe`, `partial`, `implemented_by`, `extern`, and external artifacts under the
  repository's explicit trust profile. Absence of an opt-in makes native-reduction
  evidence non-promotable.
- Require an independent promotion verifier to re-read the effective repository
  contract and check statement fidelity, final-consumer reachability, build result,
   transitive trust closure, and fresh publication state. The prover's completion
  report is not the verification. If no independent pass ran, report promotion as
  unverified.
- Keep generated-payload exclusions narrow: omit bulk term shards when necessary, but
  keep hand-written checkers, soundness theorems, geometry, and aggregate consumers
  visible to proof mining and closure audits.
- If validation is gated or incomplete, report exactly what was not run.

For project-specific publication or proof-index command semantics, follow the
tooling and documentation shipped by that project.

## Code and repository hygiene

- Fix new lint warnings promptly; suppress only with the narrowest justified scope.
- Use mathematical names and neutral status language. Name new declarations for the
  mathematics, not the pipeline: do not coin house/software jargon or codenames for a
  math object, encode tool names in theorem schemas, or present project shorthand as
  established terminology. Conform to a project's naming glossary when one exists.
- Keep the public interface intentional. Mark non-interface helpers `private`;
  an `Internal` namespace groups names but does not hide them.
- Give new hand-written public mathematical declarations useful semantic docstrings
  and new hand-written Lean modules module docs. Document non-obvious private helpers;
  generated payloads may centralize searchable context in their generator or module.
  Historical documentation gaps are not, by themselves, promotion failures.
- Follow project header/authorship and source-literature policy for new files.
- For mathlib/FLT-bound code, apply the stricter repository idiom before review.

Read [code-quality.md](references/code-quality.md) for governed review gates,
[repository-policy.md](references/repository-policy.md) for headers/references, and
[mathlib-flt-idiom.md](references/mathlib-flt-idiom.md) for mathlib/FLT review.

## Reference map

| Task | Read |
|---|---|
| Wrapper behavior, host sharing, raw Lean exceptions, mathlib cache | [build-operations.md](references/build-operations.md) |
| Budgets, heartbeat policy, stats, and elaboration profiling | [build-performance.md](references/build-performance.md) |
| Generated proofs, DRAT emitters, project olean archival | [generated-proofs.md](references/generated-proofs.md) |
| Certificate-bank custody, reproducibility, verification, and handoff | [freezing-certificate-banks.md](references/freezing-certificate-banks.md) |
| Promotion; provenance; `sorry`; axioms; case splits; native/external trust | [proof-discipline.md](references/proof-discipline.md) |
| Compact policy for workers/reviewers that cannot load this skill | [worker-promotion-contract.md](references/worker-promotion-contract.md) |
| Governed review gates, lints, naming/tone, and public API | [code-quality.md](references/code-quality.md) |
| Headers, authorship, provenance, local literature | [repository-policy.md](references/repository-policy.md) |
| Mathlib/FLT style and pre-review audit | [mathlib-flt-idiom.md](references/mathlib-flt-idiom.md) |
| Splitting one oversized module into shards plus a coordinator | [sharding.md](references/sharding.md) |
| Lake dependency pins, local paths, mirrors | [vendoring.md](references/vendoring.md) |
