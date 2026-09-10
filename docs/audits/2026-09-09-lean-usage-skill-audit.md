# lean-usage skill audit — closeout

Date: 2026-09-09
Scope: `plugins/lean-usage/skills/` (`lean-usage`, `lean-shard`, `drat-to-lean`),
their references, `plugins/lean-usage/rules/AGENTS.md`, and the repository files
those skills describe.

Findings 1-6 and 9-16 were applied in the same session; they are listed at the
end for the record. The A-D follow-up items and the missed README trust claim
were resolved in the closeout below. No repository-controlled items remain open.

## Resolved follow-up

### A. Private home paths in two skills

The skills now describe both CLIs as user-supplied external dependencies. They
support portable discovery on `PATH` or an explicit path in a supplied checkout,
and tell the reader when a compatible executable or checkout is unavailable.
They no longer require a private home-directory layout, invent a release URL, or
promise an installation route that this repository cannot provide.

This resolves the portability and claim-scope defect; it does not claim that the
external source release exists, is public, or has been installed. The report's
existing provenance links, including the historical pinned `plugins/math-toolchain`
reference, remain unchanged.

### B. SKILL.md repeats proof-discipline.md

The common-case summary is intentionally retained for progressive disclosure.
It now opens with the canonical policy sentence: `proof-discipline.md` is the
canonical policy; readers must consult it for the full contract and resolve any
summary drift in its favor, subject to repository instruction precedence. The
summary remains a concise gate overview rather than a competing policy source.

### C. Internal plugin names in a hook docstring

The `sync-lake-build.py` docstring no longer names unrelated private plugins.
The Codex hook documentation also uses the host's
`${PLUGIN_ROOT}` resolution rather than the stale fixed-checkout-path comment.

### D. Items that follow the new protect-lake-build hook

`references/build-operations.md` now documents that `protect-lake-build.py`
blocks file edits, patches, and recognized shell writes to the deployed wrapper.
It carries the required caveat: hooks run only when enabled and trusted, shell
recognition is heuristic, and the guard is workflow assistance rather than an
operating-system security boundary. The SessionStart hook preserves an
unexpected regular file instead of overwriting local work.

`README.md` now has the Claude/Codex protect-hook row and repeats the trust,
heuristic, and regular-file-preservation caveats. `AGENTS.md` inventories both
wrapper tests: `test_lake_build_lock.py` and `test_lake_build_edit_guard.py`.

The new `freezing-certificate-banks.md` guide was added separately; its presence
is recorded here without folding it into the historical applied-item list.

## Applied in this pass

The subsequent report/reference comparison also corrected requested-versus-enforced
memory limits, Lake-phase timing scope, warning-threshold wording, profiling flags,
and the incomplete sharding cache-key claim. Attribution examples now use actual
contributor/rightsholder placeholders and preserve original credits. The report's
public edition replaces inaccessible links with qualified historical evidence
labels and removes internal-tool names; the companion PDF is regenerated with it.

1. `SKILL.md` and `references/build-operations.md` — the wrapper prefetches the
   mathlib cache itself and fails closed; the manual `lake exe cache get` is now
   marked as the no-wrapper path only.
2. `LEAN_USAGE_SKIP_CACHE_CHECK=1` is documented as a hook switch that does not
   reach the wrapper. Both files now state that hooks run only where the user
   trusts them, and give the fallback entry points for `lake-build`.
3. `rules/AGENTS.md` — removed `lake-build build`, which becomes `lake build
   build`, because arguments are forwarded verbatim.
4. `references/build-performance.md` — `recompiled` is an activity count over
   `Built`, `Building`, and `Compiling` lines, not a module count; the record
   field list and the example JSON gained `build_log`.
5. Removed the "byte-checked" and "mechanically checked" claims for the worker
   contract, and the stale contract-check claim in
   `scripts/check-manifest-versions.sh`.
6. `drat-to-lean` no longer promises a kernel-checked proof in its description,
   its opening line, or stage 6; depth > 1 can still emit `sorry`.
7. Removed the stray `<!-- created_from: 752c93d -->` marker.
9. Replaced the undefined "CEGAR wave-boundary checkpoint" and "anchored `sorry`"
   terms.
10. Replaced the project-specific namespace example and glossary
    reference with generic ones; removed the agent-smith and `attic` sentence.
11. The external cross-project search route was made conditional with a stated
    fallback; the subsequent review replaced its internal-tool example with
    tool-neutral discovery guidance.
12. Added `skills/lean-usage/agents/openai.yaml`.
13. `scripts/check-manifest-versions.sh` now covers the plugin-root manifest
    copy; `AGENTS.md` documents it and the bump rule names every manifest.
14. `AGENTS.md` no longer says `codex-hooks.json` holds absolute paths.
15. `hooks/lean-direct-warn.py` docstring says `lake-build`, not `lake-build.sh`.
16. The cache-guard paragraph now names the stale-toolchain deny.

Also in this pass: `examples/lake-build-example` and its README section were
removed at your request, and `references/sharding.md` was added as a tool-neutral
split contract.
