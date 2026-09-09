# Mathlib and FLT idiom

Use this reference for code intended for mathlib, FLT, or a repository that
explicitly adopts their review style. Match the destination repository and nearby
maintainer-written code; its current conventions override generic examples here.

## Contents

- [Documentation and provenance](#documentation-and-provenance)
- [Naming](#naming)
- [Proof style](#proof-style)
- [Options and linters](#options-and-linters)
- [File and namespace structure](#file-and-namespace-structure)
- [Design the public interface](#design-the-public-interface)
- [Pre-review audit](#pre-review-audit)

## Documentation and provenance

- Apply the general documentation baseline in
  [code-quality.md](code-quality.md). In hand-written code, give every public
  declaration a useful docstring and every file a module doc; inherited gaps do not
  excuse new declarations or material changes to an existing public interface.
- Use section/module headings when they clarify new vocabulary.
- Follow the destination's provenance convention. Record transient PR/process
  history in the commit/PR; put durable mathematical/source attribution in module
  docs, declaration docstrings, or a focused comment.
- Do not use `@[nolint docBlame]` as a substitute for ordinary documentation.
  Reserve it for a narrowly justified case such as intentionally hoverless syntax.

## Naming

- Use `snake_case` for theorem/lemma names.
- Use lower camel case for definitions, structures, and instances where the
  repository does so.
- Prefer mathematical concepts over a spelling of the type signature or proof
  mechanism.
- Let namespaces carry ambient context. Repeated long substrings in one name often
  indicate a missing namespace or an internal helper leaking into the API.
- When one mechanical naming pattern appears in parallel families, review the full
  pattern rather than renaming only the first reported instance.

Length is a review signal, not a theorem: a long established mathematical term can
be appropriate, while a short tool-flavored name can still be poor.

## Proof style

- Prefer direct terms for trivial constructions; use tactics when they improve the
  proof.
- Write `:= by` together at the declaration boundary.
- Use `↦` in function literals.
- Prefer `inferInstance`, `rfl`, or a constructor term over a tactic block that adds
  no clarity.
- Prefer stable, explicit rewrite/simp inputs. Bare `simp` is appropriate only when
  the intended simp-normal form is genuinely the contract.
- Repeated `change`/`simpa` chains often indicate a missing interface lemma or an
  awkward definition; inspect the surrounding API before extending the chain.
- Use existing abstractions such as `Equiv.ofBijective` and `fun_prop` when they
  express the mathematics more directly than manual bookkeeping.

## Options and linters

- Work within the project's heartbeat and recursion limits. A large local override
  is a signal to profile and split the proof.
- Fix linter findings when possible. If a suppression is mathematically or
  metaprogrammatically justified, scope it narrowly and explain why.
- Treat a long public name plus a large heartbeat override as one likely design
  smell: the declaration may be carrying too much context and proof work.

## File and namespace structure

- Keep files cohesive. Rough signals such as 200–300 lines typical and 500 lines
  worth reviewing are local heuristics, not universal limits.
- Independently, profile any module that dominates incremental builds; see
  [build-performance.md](build-performance.md).
- Use section variables for genuinely shared hypotheses. Frequent `omit ... in`
  can mean the section is too broad.
- Keep namespace depth proportional to real mathematical hierarchy.
- Mathlib-staging files should already use minimal hypotheses, mathlib naming, and
  mathlib proof style.

## Design the public interface

Identify the small mathematical surface downstream code and blueprint prose should
depend on. Mark proof bookkeeping `private` unless it is intentionally a reusable
library abstraction. An `Internal` namespace groups names but does not hide them.

Declare internal helpers before the public theorem that uses them:

```lean
namespace HeckeOperator

namespace Internal

private lemma maps_to_repr : ... := by
  ...

private lemma inj_on_repr : ... := by
  ...

private lemma surj_on_repr : ... := by
  ...

end Internal

/-- Mathematical decomposition consumed downstream. -/
theorem t_double_coset_decomposition (hv : v ∉ S) :
    Set.BijOn (fun t ↦ ...) ... ... := by
  exact ⟨Internal.maps_to_repr, Internal.inj_on_repr,
    Internal.surj_on_repr⟩

end HeckeOperator
```

A declaration without a current in-repo consumer may still be a valid public
library API. In that case, make the intended stable abstraction clear and test it
as such; do not publish every proof helper by default.

## Pre-review audit

Run focused source scans on every changed Lean file and inspect each hit:

```bash
rg -n 'set_option maxHeartbeats|set_option linter\.|@\[nolint' FILE
rg -n '^[[:space:]]*((private|protected|public|noncomputable|nonrec)[[:space:]]+)*(theorem|lemma|def|structure|instance)[[:space:]]+' FILE
rg -n '^[[:space:]]+change[[:space:]]' FILE
rg -n '^--[[:space:]]*(Adapted|elevated|FROM)' FILE
awk 'length > 120 { print NR " (" length ")" }' FILE
wc -l FILE
```

Also:

1. list every new public declaration and its consumer or intended library role;
2. check hypotheses for unnecessary strength;
3. compare proof and docstring shape with nearby maintainer-written declarations;
4. build the smallest affected target and address new warnings;
5. verify that refactors did not change the intended theorem or axiom closure.

If review flags a symptom such as naming, heartbeat use, or leaked helpers, search
the entire change for the underlying repeated pattern before resubmitting.
