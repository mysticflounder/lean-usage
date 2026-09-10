# lean-usage skill audit — open items

Date: 2026-09-09
Scope: `plugins/lean-usage/skills/` (`lean-usage`, `lean-shard`, `drat-to-lean`),
their references, `plugins/lean-usage/rules/AGENTS.md`, and the repository files
those skills describe.

Findings 1-6 and 9-16 were applied in the same session; they are listed at the
end for the record. The items below are still open.

## Open

### A. Private home paths in two skills

Both skills point at a home directory, so no other installation can follow them.

| File | Lines | Content |
|---|---|---|
| `plugins/lean-usage/skills/drat-to-lean/SKILL.md` | 3, 15, 22, 120 | `~/the-missing-pair` |
| `plugins/lean-usage/skills/lean-shard/SKILL.md` | 10, 11, 12 | `~/bin/lean-shard`, `~/projects/rustprojects/lean-shard/`, its `usage.md` |

The report already cites the DRAT pipeline at
`github.com/flound1129/the-missing-pair`, so that skill needs the public URL, not
a new location. The `lean-shard` CLI has no public location in this repository or
in the report; reference 71 of the report points at the SKILL.md itself, at the
old `plugins/math-toolchain/…` path and pinned commit `4b796af`.

Action when the two CLIs are released: replace each home path with the release
URL, keep the home path only as an optional local convenience, and say how a
reader installs the tool. {{NEEDS_ADAM_INPUT}} — the release URLs.

Related: `plugins/lean-usage/skills/drat-to-lean/SKILL.md:106,130` cites
`docs/2026-04-18-cadical-usage-cleanup.md`, a file inside that same repo. Once the
repo is public the citation resolves; until then it is unreachable for a reader.

### B. SKILL.md repeats proof-discipline.md

`plugins/lean-usage/skills/lean-usage/SKILL.md` carries about 35 lines under
"Proof obligations and tractability" that restate
`references/proof-discipline.md`. The two texts agree now — the "anchored `sorry`"
wording was aligned in this pass — but every future policy change has to be made
twice.

Options: keep the summary (progressive disclosure, one read for the common case),
or cut it to the gate plus a pointer. Not a defect either way.
{{NEEDS_ADAM_INPUT}} — which shape you want.

### C. Internal plugin names in a hook docstring

`plugins/lean-usage/hooks/sync-lake-build.py:16` says "same pattern as py-run /
auto-compact". Those are private plugin names with no meaning to a reader of the
public plugin. Left untouched because another agent held that file during the
audit.

### D. Items that follow the new protect-lake-build hook

The hook `plugins/lean-usage/hooks/protect-lake-build.py` and its test arrived
during the audit and were not reviewed. When they land:

- `references/build-operations.md` needs a line describing what the hook blocks,
  with the same trust caveat the cache guard now carries: a host runs a plugin
  hook only when the user trusts it, so the block is a convenience, not a
  guarantee.
- `AGENTS.md` "Where things live" lists only
  `plugins/lean-usage/scripts/test_lake_build_lock.py` under wrapper tests; add
  the new test file.
- `README.md` "Plugin hooks" table needs the new row for both hosts.

## Applied in this pass

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
10. Replaced the `E677`/`Piqd` namespace example and the erdos-97-96 glossary
    reference with generic ones; removed the agent-smith and `attic` sentence.
11. The `nthdegree` cross-project search route is now conditional, with a stated
    fallback.
12. Added `skills/lean-usage/agents/openai.yaml`.
13. `scripts/check-manifest-versions.sh` now covers the plugin-root manifest
    copy; `AGENTS.md` documents it and the bump rule names every manifest.
14. `AGENTS.md` no longer says `codex-hooks.json` holds absolute paths.
15. `hooks/lean-direct-warn.py` docstring says `lake-build`, not `lake-build.sh`.
16. The cache-guard paragraph now names the stale-toolchain deny.

Also in this pass: `examples/lake-build-example` and its README section were
removed at your request, and `references/sharding.md` was added as a tool-neutral
split contract.
