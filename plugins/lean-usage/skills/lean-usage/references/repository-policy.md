# Repository policy

Use this reference before governed Lean edits or promotion. Repository-specific
instructions select the local theorem semantics, build authorization, closure plan,
and trust profile; the remaining sections are workspace defaults.

## Contents

- [Discover the effective contract](#discover-the-effective-contract)
- [Record the governed context](#record-the-governed-context)
- [Headers and authorship](#headers-and-authorship)
- [Formalization source literature](#formalization-source-literature)

## Discover the effective contract

Before editing, proving, dispatching, building, or reviewing:

1. Resolve the target source path, repository root, and Lake root. They need not be
   the same directory.
2. Discover and read every applicable instruction file recognized by the active host
   or explicitly named by a parent policy. Include global, workspace, repository,
   and target-local files whenever the host marks them applicable.
3. Read the active proof plan/closure matrix, theorem-bank registry, naming glossary,
   build runbook, and publication checklist named by those instructions.
4. Apply the host's documented precedence chain, then this plugin's defaults. Within
   the repository chain, use the host's locality rule unless an explicit instruction
   specifies otherwise. A local rule may strengthen or replace the defaults for build
   commands, `sorry`, native computation, axiom whitelists, provenance, and publication.
5. If the target path or repository changes, resolve the chain again. Never assume
   instructions injected for one checkout govern a sibling checkout.

Do not infer authorization from a build tool being available. An explicit no-build,
source-only, no-network, no-`sorry`, or publication gate remains binding until the
same authority changes it. If two applicable local instructions conflict and their
precedence is not resolvable by path or an explicit rule, stop and report the conflict.

## Record the governed context

Before dispatch or promotion, carry this compact context in the worker/reviewer
contract and durable closeout:

- repository root, Lake root, target file/module, pinned Lean/Lake/mathlib identity,
  and intended build target/wrapper;
- applicable instruction files in precedence order and the effective authorization
  gates (including whether builds, network, source refresh, or generated artifacts
  are allowed);
- exact theorem statement, immediate consumer, exported/headline consumer, active
  residual, and closure measure;
- repository axiom/native/external-evidence whitelist and publication command;
- source/problem provenance record and any deliberate semantic delta.

This context is versioned project state, not an informal prompt preface. Re-read it
at verification time rather than trusting the prover's summary.

## Headers and authorship

Every authored source/configuration file that supports comments gets the project's
copyright, license, and human-author header. Strict JSON and binary formats have no
comment header. The workspace default is GPL-3.0-or-later. Match an existing
destination repository's `LICENSE` when it differs; changing that license is a
separate governed task. Preserve the creation year.

Lean files use the mathlib-style form with no email:

```lean
/-
Copyright (c) 2026 Adam McKenna. All rights reserved.
Released under GPL-3.0-or-later as described in the file LICENSE.
Authors: Adam McKenna
-/
```

Other commentable source/configuration files use the language's comment syntax:

```python
# Copyright (c) 2026 Adam McKenna. All rights reserved.
# Released under GPL-3.0-or-later as described in the file LICENSE.
# Author: Adam McKenna <adam@mysticflounder.ai>
```

For scripts, keep the shebang on line 1 and place the header immediately after it.

Rules:

- List humans only. AI tools are not authors.
- The author is the human who takes responsibility for the file's correctness.
- Join multiple Lean authors with `, ` on one `Authors:` line.
- Use one file header. Credit a different contributor to one declaration in its
  docstring rather than adding another file header.
- When adapting external work, the adapting human remains the file author; cite
  the source according to the destination repository's provenance style.

Mathlib/FLT-bound code commonly puts adaptation provenance in the commit/PR record
rather than ad hoc inline comments. Local projects may require a declaration
docstring or source citation. The destination repository decides.

## Formalization source literature

Keep a local audit copy of every paper, thesis, problem statement, or
note that defines the formalization target under `docs/references/` (or the
repository's documented equivalent). Record enough bibliographic information to
identify the exact source and version.

Copyrighted third-party material normally remains local:

- add `docs/references/` to `.gitignore` in a public repository unless individual
  files are clearly redistributable;
- do not commit or republish a PDF merely because the formalization uses it;
- commit a source only when its public-domain/open-license status is known and
  recorded;
- if copyrighted material is already in public history, flag the history cleanup
  rather than silently preserving it.

A gitignored local path is an audit aid, not a durable public citation. Public Lean
docstrings and project docs must also include a stable bibliographic citation,
DOI, or canonical URL so a clean clone remains intelligible.

For an approved external axiom, the sanction record must identify the exact source
and statement; do not cite only a bare local filename or an unstable link.
