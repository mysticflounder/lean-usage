# Proof discipline and evidence

This is the canonical house promotion contract. Use it when changing open
obligations, decomposing a proof, reusing mined/archived Lean, relying on
computation, or claiming that a declaration is ready for a final consumer.
For workers that cannot load this full reference, embed the mechanically checked
[compact worker/promotion contract](worker-promotion-contract.md) rather than a
hand-maintained summary.

## Contents

- [Grounded proof progress](#grounded-proof-progress)
- [Fix the statement and promotion target](#fix-the-statement-and-promotion-target)
- [Represent unproved in-project obligations loudly](#represent-unproved-in-project-obligations-loudly)
- [Keep active `sorry`s load-bearing](#keep-active-sorrys-load-bearing)
- [Require measured frontier reduction](#require-measured-frontier-reduction)
- [Proof-blueprint state is live state](#proof-blueprint-state-is-live-state)
- [Theorem-bank and archive evidence](#theorem-bank-and-archive-evidence)
- [Solver and computation claims](#solver-and-computation-claims)
- [Lean-ingress publication gate](#lean-ingress-publication-gate)
- [Audit trust at the final consumer](#audit-trust-at-the-final-consumer)
- [`native_decide`](#native_decide)
- [Independent promotion verification](#independent-promotion-verification)

## Grounded proof progress

For proof-facing work, keep a new declaration when its assumptions are produced
on the active branch and an on-spine consumer immediately uses it, or when it
strictly removes target freedom: it closes a branch, excludes cases, or narrows
a family.

Discard:

- wrapper networks that rename or repackage an unchanged open obligation;
- `iff` reformulations that move rather than reduce the difficulty;
- speculative generalizations whose proof is no closer than the target;
- scratch declarations that nothing on the active proof path consumes.

A required compatibility wrapper may remain only when explicitly marked
compatibility-only and kept private or off-spine. It does not count as proof
progress or closure.

Supporting infrastructure, tests, documentation, and reusable APIs can be valid
work when the active plan calls for them; do not misreport them as proof closure.

## Fix the statement and promotion target

Before proving or dispatching work, name the exact qualified declaration to be
promoted and the exported/headline theorem that must transitively consume it. Do
not silently weaken, strengthen, generalize, specialize, or repair the statement
merely to obtain a compiling proof.

Keep a durable repository record containing:

1. the informal source/problem identifier, exact version or stable locator, and a
   short exact quotation or content digest sufficient to identify the claim;
2. the qualified Lean declaration and its exact elaborated proposition;
3. a mapping for every hypothesis, quantifier, constant, bound, and conclusion,
   with every intentional semantic delta explained;
4. the immediate consumer and named final/exported consumer;
5. the repository trust profile and toolchain/import identity used for promotion.

Use the repository's declared location: a theorem docstring, formalization index,
blueprint citation, or versioned closure record. A chat transcript, worker prompt,
or scratch file is not durable provenance. Recheck the record after statement or
source changes.

Label any statement-only, `sorry`-bearing, or otherwise provisional translation:

```text
SKETCH — NOT PROMOTABLE
```

A sketch that elaborates can provide useful statement feedback, but it is neither a
proved claim nor a candidate for promotion until the exact statement and all proof
and trust gates below pass at the original final consumer.

## Represent unproved in-project obligations loudly

Use a `sorry`-backed theorem against an explicit statement, not a named axiom:

```lean
/-- Statement tracked by obligation `<slug>`. -/
abbrev FooStatement : Prop := ...

/-- Open obligation `<slug>`. -/
theorem foo : FooStatement := sorry
```

This keeps the intended proposition stable while exposing `sorryAx` to builds
and kernel-closure audits. Reserve `axiom` for a genuine external assumption;
record project approval, a reason, and a source citation.

Never replace an open proposition with a silent `True` equivalent:

```lean
def Foo : Prop := True
theorem foo : Foo := trivial
```

The same prohibition covers `by trivial`, `True.intro`, or `simp`/`decide` when
the only reason it succeeds is that the intended obligation was weakened to
`True`. If a theorem is intentionally trivial, make that mathematical fact clear
in its statement and docstring.

## Keep active `sorry`s load-bearing

Before production mathematical proof or Lean promotion work, read the relevant
docs and active closure plan. Every current `sorry` reachable from the headline
or publish target must be covered by that plan. If the current anchor names an
uncovered `sorry`, stop and ask before editing. This plan-coverage gate does not
apply to configuration work, repository audits, or other non-proof maintenance.
Scratch theorem proving is still proof work, not maintenance. Until coverage is
added, limit activity to the read-only source and plan audit needed to identify
the blocker.

The same-change load-bearing rules below apply to obligations introduced or
actively refactored by the current plan, not every parked `sorry` in a large
repository. The plan-coverage gate above still covers every current on-spine
`sorry`.

- Name the headline or publish theorem that transitively consumes the obligation.
- Add or update the consumer in the same change. An unwired theorem is an orphan.
- A chain of placeholders is still orphaned if it never reaches the headline.
- Remove scratch `sorry`s left by a failed route.
- In proof-blueprint projects, verify reachability on the refreshed kernel spine.
- Elsewhere, establish it from current imports and explicit theorem applications.

If wiring is blocked, stop and report the exact missing producer, consumer, import,
or interface edge. Do not land more off-spine lemmas around the blocker.

Do not optimize raw counts. One theorem can hide dozens of branch-local holes;
many named leaves can make the total problem more tractable when each is smaller,
independently buildable, and auditable. Report both `sorry`-bearing declarations
and meaningful textual/case holes when assessing the remaining surface.

Keep the public consumer/coordinator thin when extraction improves tractability,
but do not manufacture orphan lemmas merely to reduce the size of one theorem.

## Require measured frontier reduction

For every production Lean promotion change in a proof-blueprint project:

1. Name the publish target, current anchored residual, and immediate consumer.
2. Choose an explicit well-founded measure on the kernel-mined obligation frontier.
3. Record the coordinator-interface frontier before the change, its publish-target
   reachability, the chosen measure, and immediate constructor fan-out in the
   active closure plan.
4. Accept the change as proof progress only when the measure strictly decreases.
5. Refresh the kernel graph, run `proof-blueprint spine`, and record the frontier
   after the change together with the named residual.

The coordinator-interface frontier consists of unresolved theorem obligations and
bookkeeping assumptions, structure fields, outcome enumerators, closers, or
wrappers immediately consumed by the active coordinator.

Closing or strengthening an on-spine `sorry` is the usual reduction. A
kernel-checked case split may increase the raw `sorry` count only when the parent
theorem proves that the branches cover every case, every new leaf remains on-spine,
and each branch strictly narrows the recorded measure. Record the branch enumerator,
coverage theorem, per-leaf consumer, per-leaf measure, total fan-out, and aggregate
before/after frontier. Prove disjointness when the coordinator or a downstream
counting argument relies on it.

Judge the split as a whole. Accept it only when the multiset/lexicographic frontier
measure required by the active plan strictly decreases and aggregate expected
closure cost falls. A split that replaces one hard residual with many equivalent,
duplicated, uncovered, or off-spine leaves is not progress even if every file builds.
Raw `sorry` count and source-line count are never the progress measure.

A green `lake-build` validates elaboration but does not establish this frontier
reduction. The deliverable is the on-spine reduction reported by
`proof-blueprint spine`, with the residual named explicitly. State the publish
target, residual, measure, direct consumer, and strict on-spine reduction
requirement in every production Lean dispatch.

In a project without proof-blueprint, establish the frontier from current imports
and explicit theorem applications, then apply the same strict-reduction test using
the measure required by the active plan.

## Proof-blueprint state is live state

Anchors are coordination cursors, not locks or durable ownership records. They can
move or auto-descend as the spine changes. Re-run the anchor/status commands before
editing or reporting. Distinguish:

- a fresh source/declaration index;
- a fresh kernel call graph and axiom closure;
- a rendered status document, which is only a snapshot of the above.

Use the project's own proof-index and publication-gate documentation for exact
commands and version-specific behavior.

## Theorem-bank and archive evidence

Search results and inventories discover candidates; they do not establish reuse.
For every candidate, record:

1. normalized current statement and source path;
2. import reachability from the proposed consumer;
3. fresh elaboration/build result against current dependencies;
4. actual axiom closure;
5. field-by-field or hypothesis-by-hypothesis mapping from live data;
6. first missing producer/antecedent;
7. circularity check and immediate consumer.

An old `.olean` disconnected from current elaborating source is not current proof
evidence. Generated metadata, declaration counts, and “no textual `sorry`” scans
are census evidence only. State whether the census is exhaustive over the scanned
source, exact within an abstraction, empirically checked, or heuristic.

For generated code, exclude payload/term shards from mining only when necessary.
Keep checker definitions, soundness theorems, mathematical adapters, and aggregate
consumers visible so the proof graph does not lose its trust boundary.

## Solver and computation claims

Separate three layers:

1. the mathematical reduction from the intended theorem to a finite/algebraic
   claim;
2. the computation or external certificate;
3. the checked theorem that consumes it.

Do not promote bounded solver output to a general theorem without a proof-grade
reduction. For exact CAS work, say exactly which identities, radical relations,
or certificate conditions were verified; do not imply a kernel certificate when
the trusted boundary is an external exact checker. For SAT/SMT, distinguish an
unchecked solver verdict from a replayed DRAT/LRAT proof.

Treat output from a solver, remote prover, generated-term pipeline, CAS, oracle,
or archived `.olean` as an external candidate until locally replayed or consumed
by a checked proof path. Preserve exact inputs, encodings, hashes, commands,
versions, coverage claims, and the source-level bridge. Prefer proof-producing or
replayable ingress. An external `success`, finite exhaustive result, or certificate
check proves only its encoded claim until the mathematical lift reaches the final
consumer.

When the computation changes the frontier, update status docs and tests together.

## Lean-ingress publication gate

Any solver or certificate artifact that names or relies on a Lean declaration must
pass this gate before it is called promoted, publishable, or consumer-reachable.
The gate is fail-closed: while any part is missing or unchecked, the artifact may
exist as diagnostic/off-spine evidence, but it carries no theorem-promotion claim.
For the field-by-field handoff schema, use item 9 of the compact
[worker/promotion contract](worker-promotion-contract.md).

The gate asserts five distinct claims:

- **source custody** — the exact Lean ingress bytes were captured, and they remained
  stable through replay and publication;
- **declaration existence** — the fully qualified declaration elaborates under the
  pinned Lean/Lake toolchain;
- **consumer reachability** — the *named published aggregate* imports the ingress
  module and reaches that declaration;
- **semantic bridge** — the certificate's mathematical meaning is connected to the
  checked Lean declaration;
- **publication integrity** — the complete binding is included in the payload before
  the certificate self-hash is computed.

**None of these implies another.** In particular:

- a green isolated module build does not establish consumer reachability;
- an import line does not establish declaration existence or the semantic bridge;
- a theorem-name string does not establish any Lean fact;
- a file hash taken outside the certificate self-hash is not publication custody;
- a solver result stays external evidence until its checked bridge reaches the
  *named* final consumer — a transitive import through some other aggregate does not
  substitute for the one being published.

Reachability must be checked semantically against the pinned toolchain
(`#check`/`#print` or an equivalent checked harness), not by substring or `grep`
search: a same-named theorem elsewhere in the repository is not the declaration.
Rebuild the named aggregate after capture, then recapture ingress and aggregate
bytes after replay and before atomic publication.

Require mutation tests that make the gate fail for each of:

1. ingress source bytes;
2. named aggregate bytes;
3. the declaration itself (including a same-byte replacement and a source-path swap);
4. the aggregate-to-ingress import edge;
5. the repository-local transitive import closure and its digest;
6. the typed parent link — parent and certificate hashes must not cross record kinds;
7. every symmetric sign/parity branch the certificate uses, each checked
   independently, down to single-literal sign mutations.

Every bound field must change the self-hash. Symlinks, hardlinks, escaping or
absolute paths, duplicate keys, and stale bytes must fail before publication, not
after. A post-replay mutation must fail at final recapture.

## Audit trust at the final consumer

Promotion is a property of the actual exported/headline consumer, not of an
isolated helper. Build the original target with the pinned toolchain, then inspect
transitive closure with `#print axioms <final-consumer>` or the repository's
equivalent fresh kernel audit. Compare the literal result with an explicit
repository whitelist.

Classify and report every applicable boundary:

| Boundary | Default promotion status |
|---|---|
| `sorryAx` | reject |
| unapproved custom/local axiom | reject |
| approved genuine external axiom | conditional only; cite sanction and source |
| `Lean.ofReduceBool`, `Lean.ofReduceNat`, `Lean.trustCompiler` | reject unless the project explicitly opts into that native-reduction trust profile |
| `unsafe`, `partial`, `@[implemented_by]`, `@[extern]` on an evaluated path | reject unless repository policy explicitly supplies and verifies an appropriate trust bridge |
| external solver/service/CAS/generated artifact | candidate evidence until locally replayed/checked and lifted to the final consumer |

Source grep is a preflight, not transitive closure. A green build, warning-free
file, clean helper, or generic publication command cannot override a stricter
repository trust profile. If the repository has no explicit rule for a detected
boundary, stop and classify promotion as unverified rather than inventing permission.

In proof-blueprint projects the explicit rule's machine-checked home is
`.blueprint.toml` `[trust]` (`native_axioms`, `unsafe`, `partial`,
`implemented_by`, `extern`) plus `[computations]` evidence manifests, enforced at
promotion by `audit`/`verify-publish` under the computational-hygiene extension
(2026-08-30). See the project's computational-evidence documentation for the
contract and the deployed-tool version-skew caveat.

## `native_decide`

Absent explicit repository opt-in, `native_decide` and inherited
`Lean.ofReduceBool`/`Lean.ofReduceNat`/`Lean.trustCompiler` dependencies are **not
promotable**. If the repository opts into native reduction, both conditions below
must still hold:

1. **Actual final-consumer axiom closure is audited.** Do not infer closure from the
   tactic name or audit only the leaf. Compare the literal closure with the project's
   exact whitelist. Under a project that explicitly selects the `bv_decide` standard,
   the closure may contain only `propext`, `Classical.choice`, `Quot.sound`,
   `Lean.ofReduceBool`, and `Lean.trustCompiler`. Reject `sorryAx` and every axiom
   outside that selected whitelist, including an external axiom that the project's
   generic publication gate otherwise approves.
   The compiler-trust cost represented by `Lean.trustCompiler` must be reported
   explicitly, never silently. `proof-blueprint axioms` treats the trio
   (`Lean.ofReduceBool`, `Lean.ofReduceNat`, `Lean.trustCompiler`) as core-allowed
   — no `[axioms].approved` entry needed — and prints them as `core*` under a
   native-reduction-trust footnote; quote that output. A clean generic gate does
   not discharge condition 2.
2. **The evaluated decision procedure is verified Lean code.** Its transitive
   evaluated closure must contain no `unsafe`, `partial`, `@[implemented_by]`, or
   `@[extern]` redirection that can make compiled behavior diverge from the verified
   definition.

A textual grep is a useful preflight, not a proof that the transitive evaluated
closure is clean. Use the project's source index/call graph and inspect all relevant
definitions. Record both the kernel closure and the code audit in the closeout.

A generic `proof-blueprint verify-publish` pass is necessary but not sufficient for
this stricter audit: its general axiom-sanction mechanism may admit external axioms,
and its implicit tool-level core set may differ from the repository's exact
`native_decide` whitelist. Compare the literal `proof-blueprint axioms <symbol>` or
`#print axioms` result against the repository policy. Under the computational-hygiene
extension, `verify-publish` does fail closed on native reduction whose complete
native-axiom closure is not listed in `[trust].native_axioms`, and on unlisted
evaluated `unsafe`/`partial`/`@[implemented_by]`/`@[extern]` boundaries — but that
narrows, rather than removes, the manual comparison: the repository whitelist may
still be stricter than the configured trust sets, and the deployed release binary
may predate the extension.

Prefer kernel `decide` when it is feasible. Use `native_decide` for scale only after
making the compiler trust boundary explicit. A proof inheriting native-decision
axioms through an imported theorem must report that inherited boundary too.

## Independent promotion verification

The proof author, generator, remote service, or planner does not self-certify
promotion. Before a claim is marked promoted/publishable, require an independent
verifier—a separate agent/session or designated reviewer that did not author the
candidate—to re-read the effective instruction chain and independently check:

1. durable source-to-statement fidelity and deliberate deltas;
2. build/import reachability at the original exported final consumer;
3. literal transitive axiom closure and every implementation/external trust boundary;
4. absence of uncovered on-spine `sorry`s and freshness of the proof spine/status;
5. branch coverage and aggregate tractability for any introduced decomposition;
6. the repository's publication command or `verify-publish` gate when authorized.

Record the verifier identity, source revision, commands/artifacts checked, and result
in the repository's durable review record. The prover's completion report or cached
artifact is input to this audit, not its conclusion. If independence is unavailable,
say `candidate verified by author only — NOT PROMOTED`.
