# Rigor standards

Use this reference when assessing a mathematical claim, reviewing a formalization,
or deciding what evidence permits you to say. It applies to prose arguments, Lean
proofs, and computation-assisted results. It defines review obligations, not an
automated verifier; a successful build or hook run does not establish compliance.

## State exactly what is claimed

Identify the proposition, its domain, hypotheses, quantifiers, parameter ranges,
and conclusion before judging the evidence. Keep the original claim distinct from
lemmas, restricted cases, equivalent formulations, and conjectured extensions.

For a formalization, retain a durable mapping between the source statement and the
elaborated proposition. Identify the source and version, explain how each assumption
and conclusion is represented, and disclose every intentional difference. A citation
is not a substitute for checking that the cited result actually applies.

Do not silently alter a statement to make it provable. In particular, do not add an
assumption equivalent to the desired conclusion, restrict a domain without saying
so, or exploit inconsistent hypotheses to imply that the intended theorem is proved.
When a statement is false or underspecified, report that finding and seek agreement
on a corrected target. A proof of a corrected target remains a different claim.

## Match the label to the evidence

- **PROVEN:** a complete argument establishes the exact claim under explicitly
  stated assumptions. Specify whether the evidence is a reviewed prose argument,
  a kernel-checked formal proof, or another accepted proof method. The label alone
  does not assert formal verification or unconditional truth.
- **CONJECTURED:** a mathematical claim not yet established. State the open gap;
  plausibility and repeated failed attempts to refute it are not proofs.
- **EMPIRICALLY VERIFIED:** the reported observations or computations succeeded
  over stated inputs under a recorded procedure. Give the tested scope and limits;
  do not infer an unrestricted theorem from those observations.
- **HEURISTIC:** a useful but non-guaranteed method, estimate, or expectation.
  State why it is being used and what could invalidate it.

These labels classify evidence, not administrative readiness. A candidate checked
only by its author has not passed independent promotion review. Conversely, an
externally stated result is not disproved merely because its local formalization is
unfinished. Keep the status of each evidence layer separate.

Distinguish sampled computation, exhaustive checking of a finite domain, and a
general theorem. A finite search proves a broader claim only with a checked reduction
showing coverage, faithful encoding, and a valid route from the search result to that
claim. Resource exhaustion, timeout, and missing output are inconclusive, not negative
answers. Approximate numerical results require justified error bounds before they
support an exact conclusion.

## Close the argument, not just the file

Every necessary step needs a justification. Explain why a cited lemma's hypotheses
hold, why a case split covers the domain, and why any induction or recursive
reduction terminates. Do not replace a missing argument with words such as
"clearly," "standard," or "routine" when the omitted step is load-bearing.

Name the final result that consumes each claimed contribution. A helper compiling
in isolation does not prove that it applies to, is imported by, or closes the original
target. Check the complete dependency path and the combined coverage of subcases.

Count progress by obligations actually discharged or made strictly more tractable,
not by added declarations, reduced file sizes, or renamed assumptions. Equivalent
reformulations and infrastructure can be useful work; describe them as such rather
than as mathematical closure. When work stalls, report the precise residual claim
instead of concealing it behind additional wrappers.

## Make assumptions and execution trust explicit

An unfinished local proof obligation must remain visibly unfinished. A tracking
record, comment, or renamed axiom does not turn it into a proved fact. Any Lean
result depending transitively on `sorryAx` is **SKETCH — NOT PROMOTABLE**, even if
the file builds or the exported theorem contains no literal `sorry`.

The following checks are the Lean application of that general standard, not a
claim that every mathematical proof uses Lean or shares one foundational system.

Inspect the literal transitive axiom dependencies of the named final consumer under
the actual toolchain and imports. A source-text scan alone is insufficient. Reject
unapproved assumptions, including those inherited indirectly. A deliberately adopted
external assumption must be genuine, explicitly approved, cited, and retained in the
statement of the result's conditional status; it must not disguise the missing proof.

The destination repository specifies its accepted foundational axioms and trust
profile. Do not invent a universal axiom allowlist or infer permission from an
existing import. A missing policy is not approval for a new trust boundary.

Distinguish kernel checking from execution trusted outside the kernel. Native
evaluation and inherited compiler-trust dependencies require explicit repository
opt-in before promotion. Even with that permission, inspect the evaluated path for
unapproved `unsafe`, `partial`, `@[implemented_by]`, or `@[extern]` behavior. An
optimization must not silently change what is trusted.

## Bind computational evidence to the claim

Treat solver output, generated proofs, certificates, and archived compiled artifacts
as candidates until the relevant checks have run. Record exact inputs and outputs,
content identities, tool and dependency versions, commands, outcomes, and coverage.
Hashes identify bytes; they do not establish mathematical correctness.

Audit the encoding and the semantic bridge as well as the checker. A verified
certificate for the wrong problem is not evidence for the intended theorem. Require
local replay/checking of the evidence and a checked proof path through the semantic
bridge to the named final consumer in the
recorded environment. Do not reuse old success claims after material changes to
sources, imports, options, toolchains, or artifacts without revalidation.

Test rejection as well as acceptance: use suitable corrupted, truncated, wrong-input,
or otherwise invalid evidence to check that the verification path rejects it. Negative
controls help expose a checker that ignores its input; they are not a substitute for
a soundness argument or an audited trust boundary.

For certificate-bank workflows, this skill uses three distinct artifact states;
they describe evidence handling, not universal categories of mathematical truth.
**Frozen** identifies a stable bank, **verified** records
checks against it, and **published** records an authorized, evidence-bound handoff.
None implies either of the others automatically. Missing coverage, provenance, or
consumer bindings blocks a promotion claim rather than becoming an implicit default.

## Require independent review and honest handoff

The author or generator does not self-certify promotion. A separate verifier must
inspect the exact claim and source mapping, reproduce the relevant checks, examine
final-consumer reachability and trust closure, and account for every remaining gap.
Simply repeating the author's summary or accepting its success log is not an
independent check. Record the verifier, revision, commands or artifacts inspected,
and the result.

Promote only when all applicable proof, trust, provenance, coverage, and independent
review gates have passed. Otherwise report the candidate's actual status, the missing
check or obligation, and what would resolve it. Never label a sketch, conditional
result, sampled observation, or author-only verification as something stronger.

Review requirements do not grant permission to execute commands or publish results.
Honor explicit no-build/no-run gates and other authorization limits. When a required
check cannot be run, mark it incomplete and withhold the corresponding claim.

## Operational references

- [Proof discipline](proof-discipline.md): Lean-specific obligation, trust, and
  final-consumer publication checks.
- [Worker/promotion contract](worker-promotion-contract.md): compact instructions
  for delegated work; use its designated text rather than an improvised policy copy.
- [Freezing certificate banks](freezing-certificate-banks.md): artifact identity,
  reproducibility, verification, and handoff records.
- [Repository policy](repository-policy.md): destination-local instructions,
  source attribution, and durable references.
