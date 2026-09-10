# Governed Lean review gates

Use this reference for house lint, naming, and public-interface promotion gates.
Use the generic Lean skill for syntax, tactic selection, and ordinary refactoring.
Mathlib/FLT-bound code follows the stricter
[mathlib-flt-idiom.md](mathlib-flt-idiom.md) where the two differ.

## Contents

- [Warning policy](#warning-policy)
- [Documentation and searchability](#documentation-and-searchability)
- [Mathematical naming and neutral prose](#mathematical-naming-and-neutral-prose)
- [Public interface](#public-interface)
- [Fast review checks](#fast-review-checks)

## Warning policy

- Fix warnings introduced or touched by the current change.
- In a noisy inherited tree, record the existing baseline and avoid unrelated
  cleanup unless it is part of the task.
- Read the linter's purpose before suppressing it.
- When suppression is legitimate, use the narrowest declaration/file scope and
  name the specific linter. Add a short reason when the cause is not obvious.
- Generated files may use specific file-level suppressions when the emitter owns
  them; fix recurring issues in the emitter, not by patching generated output.

Do not use `linter.all false` for hand-written code.

## Documentation and searchability

Write documentation for future readers and project-indexed semantic search, not
merely to silence a linter.

- Give every new hand-written public mathematical declaration a useful semantic
  docstring. Describe the mathematical concept or result, its role, and any key
  hypotheses or conventions that are not already obvious from the name and type.
  Do not substitute a tactic walkthrough, transient proof status, or tool provenance.
- Give every new hand-written Lean module a module doc that states its scope, main
  vocabulary, and public results. Use section headings when they make that structure
  easier to navigate.
- Document a private helper when its mathematical role is not obvious from its name
  and type. Routine local bookkeeping does not need ceremonial prose.
- Generated declarations are exempt from declaration-by-declaration docstrings when
  that would only duplicate mechanical data. The generator or generated module must
  still provide searchable semantic context, and hand-written public checkers,
  soundness theorems, and aggregate consumers remain subject to the normal baseline.
- An inherited documentation gap is not, by itself, a promotion failure. Do not turn
  historical docstring coverage into a hard gate or unrelated cleanup project; add
  or update documentation when introducing a declaration or materially changing its
  statement or public role.

## Mathematical naming and neutral prose

Name namespaces, definitions, and theorems after mathematics, not the tool,
daemon, script, certificate format, or pipeline that produced them.

- Name the namespace for the mathematics, not for the pipeline that produced the
  declarations: prefer `namespace Diophantine.PadicShift` over
  `namespace SolverPipeline.PadicShift`.
- A generated instance may use a stable parameter/hash suffix, but it should
  instantiate or apply a math-named theorem.
- Fix tool-flavored generated names at the emitter.

### Naming requirements for new declarations

New code must not accrue naming debt that a later de-jargonification pass has to
undo. When you introduce a declaration, namespace, field, or case label, name it
for the mathematical object, not the software/pipeline metaphor that carried it.

- **Do not coin house/software jargon for a math object.** Borrowed
  CS/networking/pipeline words — `packet`, `row`, `shell`, `slot`, `tail`,
  `skeleton`, `live`/`liveData`, `manifest`, `blocker`, `dangerous` — read as
  infrastructure, not mathematics. Name the actual object: the center with its
  exact distance class, the residual case, the obstruction, the configuration
  data, the fixed triple.
- **Do not coin codenames or bare acronyms for a stated result.** If a theorem
  already has a formal numbered/lettered label in the proof architecture, use it
  (`Theorem IV`, not an acronym like `RVOL`). Name a case by its defining
  condition ("the q-source case"), not an internal codename (`LIVE-Q`,
  `K-A-PAIR`, `ATAIL`).
- **Name the declaration for what it actually is.** A proved
  `theorem`/`def`/`structure` must not be named `…Axiom`, nor carry a historical
  label that now misdescribes it; reserve `axiom`-flavored names for genuine
  `axiom` declarations. Audit an inherited name against the declaration kind
  before reusing or extending it.
- **Do not over-correct generated/mined artifact names.** A name that encodes
  solver/mining parameters — seed, mask, participant id, SAT case index
  (`erasedPinRow_ep_right_m0_s1_l1_r2_…`, `Record001`) — is accurate
  infrastructure naming: the index *is* the content, and forcing a "pure math"
  term onto a case-table index is a category error. Likewise keep plain-English
  math terms already in use (`Surplus`, `Anchor`, coordinate `Frame`) rather
  than renaming for its own sake.
- **Conform to a project's locked naming glossary when one exists.** When a
  repository maintains a de-jargonification map or naming glossary (for example a
  `docs/de-jargonification-map-*.md` file), a new declaration must use the
  standardized term, never reintroduce a token the glossary has retired.

Use neutral, audit-friendly status language. State what is proved, open, exact
within a model, or conjectural. Avoid dramatic obstruction names and difficulty
editorializing. Project shorthand is not standard terminology; pair it with
concept-level mathematical language in docs and searches.

## Public interface

Expose the mathematical API downstream users are meant to depend on. Mark proof
bookkeeping `private` when it is not intended as reusable library API. An internal
namespace can group helpers but does not make them private or unimportable.

Current consumers are strong evidence for an interface, but not the only evidence:
libraries may intentionally publish reusable abstractions before an in-repo consumer
exists. Make that design intent explicit rather than applying a mechanical “no
consumer means private” rule.

During review:

1. List new public declarations.
2. For each, identify a current consumer or the intended stable library role.
3. Check that names express the math at the right namespace depth.
4. Keep the headline/coordinator readable; hide local bookkeeping.

## Fast review checks

Use `rg` for these source scans; interpret each hit rather than suppressing it
mechanically.

```bash
rg -n 'set_option (maxHeartbeats|synthInstance\.maxHeartbeats)|set_option linter\.|@\[nolint' path/to/File.lean
rg -n 'native_decide|Lean\.ofReduce(Bool|Nat)|trustCompiler|unsafe|partial|implemented_by|extern' path/to/File.lean
rg -n '\bsorry\b|\baxiom\b' path/to/File.lean
rg -n '^[[:space:]]*((private|protected|public|noncomputable|nonrec)[[:space:]]+)*(theorem|lemma|def|structure|instance)[[:space:]]+' path/to/File.lean
awk 'length > 120 { print NR " (" length ")" }' path/to/File.lean
wc -l path/to/File.lean
```

These scans are triage, not transitive proof or implementation-closure audits.
Interpret every hit under the repository contract. Heartbeat overrides, broad
suppressions, unexpected trust boundaries, long names, and large files are review
signals, not universal failures; apply the project's own limits and the canonical
[promotion contract](proof-discipline.md).
