# Lean worker and promotion contract

This compact block is the canonical load-bearing contract for Lean proof workers and
promotion reviewers that cannot load the full `lean-usage` skill. If a copy is ever
embedded elsewhere, keep it byte-for-byte identical between its markers. (The former
agent-smith mirror and its `check-lean-worker-contract.sh` sync check were retired
to the `attic` plugin on 2026-08-14.)

<!-- BEGIN LEAN-WORKER-PROMOTION-CONTRACT v1 -->
## Lean worker and promotion contract

1. **Resolve governance first.** Resolve the repository root, Lake root, target file,
   pinned toolchain, and intended build target. Discover and read every applicable
   instruction file recognized by the active host or explicitly named by a parent
   policy, then apply the host's documented precedence chain. Record build/network/
   publication authorization and do not cross an explicit gate.
2. **Fix the claim and consumer.** Record the exact qualified proof target, exact
   formal statement, informal source/version or stable locator, hypothesis-by-
   hypothesis correspondence, any deliberate semantic delta, immediate consumer,
   and exported/headline final consumer. Never weaken or silently repair a statement
   to make it compile. Label statement-only or `sorry`-bearing work
   `SKETCH — NOT PROMOTABLE`.
3. **Keep obligations honest and on-spine.** Represent an in-project unproved claim
   as an explicit `sorry`-backed theorem, never a local `axiom`, `True`, or vacuous
   substitute. Before production proof work, require active-plan coverage for every
   final-consumer-reachable `sorry`; an uncovered on-spine `sorry` is a hard stop.
   Every introduced/refactored obligation must reach the named final consumer.
4. **Accept only tractable splits.** A finite case split is progress only when the
   parent proves complete branch coverage, every leaf has a named on-spine consumer,
   every branch strictly decreases the recorded well-founded frontier measure, and
   the aggregate expected closure cost decreases. Record before/after frontier,
   fan-out, per-branch residual/measure, and disjointness when consumers need it.
   Raw `sorry` or line counts are not tractability measures.
5. **Verify the actual final consumer.** Build the original authorized target, not
   only a scratch helper, then inspect literal transitive axiom closure at the
   exported/headline consumer with `#print axioms` or the repository's fresh kernel
   audit. Reject `sorryAx` and unapproved custom/local axioms. An approved genuine
   external axiom remains conditional and must retain its sanction and citation.
6. **Classify every trust boundary.** Without explicit repository opt-in,
   `native_decide` and inherited `Lean.ofReduceBool`, `Lean.ofReduceNat`, or
   `Lean.trustCompiler` are not promotable. Even with opt-in, audit the evaluated
   transitive path for `unsafe`, `partial`, `@[implemented_by]`, and `@[extern]` and
   reject unapproved execution redirection. Treat solver, remote-prover, CAS,
   generated-term/certificate, oracle, and archived-olean output as external
   candidates until locally replayed/checked and lifted to the final consumer with
   exact inputs, hashes, commands, versions, coverage, encoding, and semantic bridge.
7. **Treat heartbeats as measured policy.** Honor repository caps. Profile and
   refactor/simplify/split first. If permitted and still necessary, use the smallest
   measured finite declaration-scoped `maxHeartbeats` override and record its reason
   and review/removal condition. `synthInstance.maxHeartbeats` is a distinct
   typeclass-synthesis budget. `maxHeartbeats 0` is exceptional, locally approved
   generated/certificate policy with separately bounded time, memory, input, and
   replay scope—never a default for hand-written proofs.
8. **Do not self-promote.** A separate verifier that did not author the candidate
   must re-read the effective instructions and independently check statement/source
   fidelity, original-consumer build and reachability, transitive axiom and execution
   trust, on-spine `sorry` status, split coverage/tractability, and the authorized
   publication gate. Record revision, verifier, commands/artifacts, and result. If no
   independent pass ran, report `candidate verified by author only — NOT PROMOTED`.
9. **Bind Lean ingress before publication.** A handoff that names a Lean declaration
   must carry every field below, or publication is blocked: (a) exact
   repository-relative ingress source path, captured bytes, byte count, and SHA-256;
   (b) fully qualified Lean declaration name; (c) exact named aggregate/final-consumer
   source path, captured bytes, byte count, and SHA-256; (d) the exact import edge from
   that aggregate to the ingress module, plus the repository-local transitive import
   closure and its digest; (e) semantic declaration validation under the pinned
   Lean/Lake toolchain (`#check`/`#print` or an equivalent checked harness), never
   substring search; (f) a fresh build of the named aggregate or final consumer after
   capture; (g) post-replay recapture proving ingress and aggregate bytes did not change
   during certificate replay/publication; (h) a versioned, domain-separated self-hash
   over the complete binding; and (i) typed, domain-separated parent links binding
   parent schema, record kind, and parent record digest. This is fail-closed: omission
   of any field blocks publication. The evidence may remain diagnostic/off-spine, but
   no promotion, publication, or consumer-reachability claim may be made. A green
   isolated module build, a theorem-name string, or a source hash outside the
   certificate self-hash satisfies none of it.
<!-- END LEAN-WORKER-PROMOTION-CONTRACT v1 -->
