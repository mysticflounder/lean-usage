# Security policy for downloaded Lean formalizations

A Lean formalization is executable input at the tooling boundary. Treat a proof
repository downloaded from the internet as untrusted software until its source,
dependencies, and build configuration have been reviewed.

Review can miss malicious behavior. These recommendations reduce exposure; they do
not certify a project as safe. A disposable directory or a container alone does not
establish that private files, credentials, or network services are inaccessible.

## Why checking can execute code

Lean's `#eval` command compiles and runs the expression it is given. Imported module
initializers and custom elaborators, tactics, macros, and commands can also run while
Lean elaborates a file. A `lakefile.lean` is executable build configuration, and imported
native or foreign-function code can invoke the host runtime. Lean's IO and process
APIs can read and write files, launch subprocesses, and communicate with external
services when the operating system permits it. The language server may elaborate
files while an editor is open, so merely opening an untrusted project can be an
execution event.

The logical trust story is separate. Kernel checking, `#print axioms`, and source
audits help assess whether a theorem follows from its declared logical assumptions;
they do not prevent the checking process from reading private files, using inherited
credentials, modifying the filesystem, or making network requests.

Official references:

- [Elaboration and compilation](https://lean-lang.org/doc/reference/latest/Elaboration-and-Compilation/)
- [Foreign-function interface and initialization](https://lean-lang.org/doc/reference/latest/Run-Time-Code/Foreign-Function-Interface/)
- [Lean processes](https://lean-lang.org/doc/reference/latest/IO/Processes/)
- [Lean files and streams](https://lean-lang.org/doc/reference/latest/IO/Files___-File-Handles___-and-Streams/)
- [Lake](https://lean-lang.org/doc/reference/latest/Build-Tools-and-Distribution/Lake/)

## Recommended handling

Before checking or building downloaded input:

1. Inspect the repository as data first. Review `lakefile.lean`/`lakefile.toml`,
   package manifests, scripts, generated files, imports, and dependency pins. Look
   for `#eval`, initialization, custom elaboration, `IO`, process or FFI calls, and
   native-code hooks. This is a review aid, not a complete detector.
2. Use a disposable workspace and minimize the permissions available to Lake, Lean,
   the language server, package tools, and any helper they can start.
3. Minimize network access. If dependencies must be fetched, perform that as a
   separately reviewed operation in a controlled environment, then use a prepared
   dependency cache for the check.
4. Provide no unnecessary secrets: avoid home directories and credential stores, and
   use a minimal environment without API tokens, SSH credentials, cloud metadata, or
   unrelated private files. Restrict writable paths and apply resource limits where
   the separately administered environment supports them.
5. Apply the same caution to editor/LSP sessions. An LSP that can access the host can
   execute imported code while producing diagnostics or completing a file.
6. Use separately administered isolation appropriate to the threat model when these
   recommendations are insufficient. Record the isolation policy and
   toolchain/dependency versions with the result.
   Treat a result produced without those controls as an ordinary host execution, not
   as evidence that the source was safe.

For repositories already reviewed and trusted, the normal project build workflow may
be used. That workflow still does not turn a later downloaded dependency into trusted
input automatically. Build wrappers, hooks, lock files, telemetry, regex checks, and
logical axiom audits coordinate work or provide review evidence; they are not
security boundaries.
