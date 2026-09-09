---
name: proof-blueprint
description: "Use to drive the proof-blueprint CLI in Lean 4 projects with a .blueprint.toml: kernel-mined branch state, in-project symbol search, refs/spine mining, session anchors, durable bibliography references, axiom approval, computational-evidence manifests ([trust]/[computations]), audit and verify-publish gates, and live-blueprint.md."
---

# proof-blueprint

`proof-blueprint` is a single global CLI that reports the **exact current state of a Lean 4 formalization at the moment you ask**, computed from the `.lean` source and the Lean kernel — never from a stored "this is proven" flag.

**Design principle — truth by construction.** Proof **structure is not authorable**: it is the kernel-mined call graph from `target_symbol` (`getUsedConstants` edges mined out of the compiled oleans). The DB stores only that mined **index** plus human **intent** (approved axioms, prose labels, notes, bibliography); it never stores derived state. Branch openness, completeness, and axiom closures are computed per query. Hand-edit a `.lean` file and the next query reflects it. **There is no proof-structure sync step, no subcommand that asserts provenness, and no command to author proof structure.** This exists because (a) a stored "all clean" flag once masked a custom axiom (`elekes_sharir_guth_katz_…`) sitting on a proof spine until the moment of submission, and (b) an agent-authored obligation tree let sessions anchor work to stubs with no dependencies — structure an agent writes enforces nothing. The kernel is the only thing that gets to say "proven," and the kernel's call graph is the only thing that gets to say "this is part of the proof."

> **Relationship to `proof-prose`.** This is the tool that *grounds* a prose proof's completion matrix. proof-prose's "PROVEN-via-Lean" (cited lemma, compiles, no `sorry` in the transitive chain) is exactly what `verify-publish` / `spine` check — plus the axiom-closure check the prose layer can't see. When a prose proof claims a step is `done`, that claim should be backed by a ✓-closed spine branch (or 🪶 under a deliberately approved axiom) here, not by eyeballing the file.

## Install / upgrade

The deployed CLI is the **Rust port** — workspace member `proof-blueprint` in
`~/projects/rustprojects`. Both `~/bin/proof-blueprint` and
`~/.local/bin/proof-blueprint` are symlinks to
`~/projects/rustprojects/target/release/proof-blueprint`; upgrade in place by
rebuilding the release binary:

```bash
cargo build --release -p proof-blueprint --manifest-path ~/projects/rustprojects/Cargo.toml
proof-blueprint --version
```

**Version skew (as of 2026-09-01):** the deployed release was last built
2026-08-20 and **predates the computational-hygiene and durable-references
extensions** below. Until the release is rebuilt, exercise
`references` and `[trust]`/`[computations]` enforcement with
`cargo run -p proof-blueprint -- <cmd>` from `~/projects/rustprojects`. The
legacy Python tool at `~/projects/math-projects/proof-blueprint` is no longer
installed (no uv tool); it survives only as the frozen parity baseline for the
Rust port's golden/differential tests. Crate docs:
`~/projects/rustprojects/proof-blueprint/{README,USAGE}.md`.

## Two prerequisites before anything reports

1. **A `.blueprint.toml` sentinel.** The CLI finds the active project by walking *up* from cwd for `.blueprint.toml`. None found → exit 2 with *"run `proof-blueprint init`."* You can run from anywhere inside the project tree.
2. **A mined call graph** (for the structural commands). `refs --refresh` mines the graph from the compiled oleans — it needs a warm `lake build` first. Without any mine, `spine` / `status` / `anchor` report every project symbol as ❓ unmined.

| You have… | These work |
|---|---|
| `.blueprint.toml` + a Lean lib | `index`, `symbols`, `axioms` (source-only) |
| …plus a warm build + `refs --refresh` | `status`, `spine`/`tree`, `anchor`, `audit`, `verify-publish` |

**Auto-refresh (stale graph only):** `spine` and `anchor` (both show and set) automatically run `refs --refresh` when the graph fingerprint is out of date for the current build. This handles the "edited `.lean`, ran `lake build`, forgot to re-mine" case without manual intervention. It does **not** handle the case where no build exists at all — if `fp is None` (no compiled oleans), `anchor set` still exits with an error and requires you to run `lake build` first.

## Cached vs kernel — read before trusting a "clean"

`#print axioms` and graph mining need a **warm Lake build** (`.lake/packages` present, mathlib cached). To stay fast, queries read the **cached** mined graph and `kernel_axiom_closure` table.

- **No build required (cached / source-only):** `status`, `spine`, `tree`, `anchor`, `audit`, `refs --check`, `verify-publish --no-refresh` (state probe only — under the 2026-08-30 extension it fails closed and cannot yield a publication verdict), `index`, `symbols`.
- **Kernel-invoking (needs Lake warm):** `refs --refresh`, `audit --refresh`, `verify-publish` (default), `axioms <symbol>`.

Graph freshness tracks the **build**, not the source text: the mine is keyed on a build fingerprint (hash of the project's oleans). Editing a `.lean` file without rebuilding does **not** stale the graph — that edit isn't verified until the next build. A `lake build` that changes any olean flips affected symbols to ⏳ stale until you re-mine. Warm the kernel once:

```bash
cd <project>/lean && lake exe cache get && lake build
```

## `docs/live-blueprint.md` is a build artifact

Every successful `lake-build` in a proof-blueprint project regenerates
`docs/live-blueprint.md` — it runs `proof-blueprint sync`, then snapshots `spine`
(the open frontier) over that file via an atomic temp-file replace. **It is generated
output, not a document you author.** Never hand-edit it; the next build overwrites it.
To change what it says, change the Lean and rebuild. When you need the current frontier,
read that file or re-run `spine` — do not reconstruct it by hand.

The generated file opens with a `<!-- GENERATED FILE — DO NOT EDIT -->` banner,
emitted by `spine` itself whenever its stdout is a regular file (`spine > file`); a
tty or a pipe gets no banner, so a render you read through Bash stays clean. Force
either way with `spine --banner` / `--no-banner`. `--files` never emits it.

The regeneration is **best-effort and conditional**: it needs the build to exit 0,
`proof-blueprint` on `PATH`, a `.blueprint.toml` at or above the Lake tree, and a
non-empty `spine` render. `LAKE_BUILD_NO_REFRESH=1` skips it entirely. A failed render
prints a notice and leaves the previous file in place without failing the build — so a
green build can coexist with a stale `live-blueprint.md`. Confirm the
`wrote …/docs/live-blueprint.md` line before citing it as current proof state.

## First-run: standing up a project

```bash
cd /path/to/some-lean-project
proof-blueprint init --lean-lib lean --target-symbol Foo.main_theorem   # .blueprint.toml + empty schema-v2 DB
proof-blueprint index --refresh        # scan source into lean_symbols (idempotent)
proof-blueprint refs --refresh         # mine the kernel call graph (needs warm lake build)
proof-blueprint spine                  # where the proof is open
proof-blueprint verify-publish
```

On a fresh clone or new git worktree of an adopted project, replace init+index with the one-shot `proof-blueprint bootstrap` (= init if needed + `intent import` if `intent/` exists + `index --refresh`); then `refs --refresh`.

`.blueprint.toml` records `[paths] db`/`lean_lib`, `[publish] target_symbol`+`state`, `[axioms] approved`, `[search] fts` (default `true`), the legacy excludes `[mining] skip` (dotted modules out of the kernel mine, still indexed) / `[index] skip` (relative source paths out of the index entirely), and the Rust-only `[trust]`/`[computations]` sections (see the computational-evidence section below). `target_symbol` is a string (one claim) **or** a list (`["A.thm", "B.cor"]`) to gate/render several; the first is primary. `spine` (no positional symbol), `verify-publish`, `anchor`, and `status` all act on the whole set — render one block each / gate every target / accept work on any target's spine / report each.

## Command reference

**Index (source → DB)**
```bash
proof-blueprint index --refresh        # re-scan; idempotent, mtime-gated (unchanged mtime → file skipped unread)
proof-blueprint index --refresh --force  # re-read EVERY file, ignoring the skip — run once after a CLI upgrade
proof-blueprint index --check          # report drift, no writes, exit 1 if drift (always content-hash based)
proof-blueprint symbols [--kind axiom | --axioms-only | --with-sorry]   # full census, no matching
```
The metadata gate is keyed on the *file*, so a CLI upgrade that starts capturing a new column cannot backfill it on a plain `--refresh` — nothing about the sources changed, so every file takes the skip path. See the `search` upgrade step below.

**Search — the query surface for this project's corpus, and the only one that knows the spine**

> **Routing rule — which search tool.** `proof-blueprint search` is **always** the tool for Lean search **inside the current project**. `nthdegree docs search --lean` is the tool for **cross-project** search — mathlib, other projects' corpora, ingested papers. This is a difference of job, not of quality: nthdegree cannot see this project's index, spine, sorries, docstring/attribute columns, or registrations; `proof-blueprint` cannot see anything outside this project. **In-project → `proof-blueprint search`. Across projects → `nthdegree docs search --lean`.** `rg` is for reading the source once you already know which declaration you want.

```bash
proof-blueprint search arc_partition               # name OR statement OR docstring
proof-blueprint search card swap cycle             # whitespace = AND; every term must match
proof-blueprint search --name 'Ns.*.false_of_*'    # name only; literal pattern, glob
proof-blueprint search --sig 'ConvexIndep'         # statement text only
proof-blueprint search --doc pigeonhole            # docstring only; previews the matched doc
proof-blueprint search --attr simp --namespace Ns.Arc      # attribute / namespace facets
proof-blueprint search --in 'E677/Spine/*' --with-sorry    # by source path, rel. to the lean lib root
proof-blueprint search --uses Finset.sum_le_sum     # decls that reference SYM   (mined call graph)
proof-blueprint search --used-by Ns.main_theorem    # decls that SYM references  (mined call graph)
proof-blueprint search <query> --spine             # only what a publish target reaches
proof-blueprint search --off-spine --with-sorry    # off-spine placeholders
proof-blueprint search --off-spine --unregistered  # ... not yet declared deliberate
proof-blueprint search <query> [--kind K] [--private] [--limit N|--all] [--files] [--json]
```

A bare `QUERY` splits on whitespace into terms that must **all** match, each against the fully-qualified **name** or the **statement text** or the **docstring** — so `search card swap cycle` narrows instead of failing on a phrase that never occurs verbatim, and you can find a theorem by a constant it mentions or by what its prose says it is for. Ranking: name hits, then statement hits, then docstring-only hits. `--name`/`--sig`/`--doc` restrict to one field and take a **literal single pattern** (no term splitting; whitespace included). No glob character → **substring**; `*`/`?` → **anchored glob**. `_` and `%` are literal (escaped), since nearly every Lean name contains `_`. Case-insensitive. `private` decls are excluded unless `--private`. Results are marked `🌲` on-spine / `·` off-spine, plus `📌 <category>` when registered. `--json` records carry `doc` and `attributes` alongside `symbol`/`kind`/`file`/`line`/`has_sorry`/`private`/`signature`, plus `on_spine` under a spine flag and `registered` when registered. Exit **0** matches, **1** none, **2** no criteria given or a requested spine scope could not be established.

`--uses`/`--used-by` read the kernel-mined `symbol_refs` edges; both directions are indexed, so each is a lookup, not a graph walk. When the graph cannot answer, an explicit note goes to **stderr** — nothing mined yet, the symbol is indexed but unmined/stale, or the symbol is not an indexed declaration at all. Never read a silent empty result as "nothing references it" without checking that stderr line.

**Upgrade step — run once per project after upgrading the CLI:**
```bash
proof-blueprint index --refresh --force
```
`--doc`/`--attr` read `lean_symbols.doc_string`/`attributes`, which a plain `index --refresh` will **not** populate: a CLI upgrade doesn't change file content hashes, so the fast path skips every unchanged file and those filters silently match nothing. The same `--force` pass builds the FTS index below.

**Two accelerators, neither of which changes which rows match.**
- **FTS5 trigram index** over name + signature + docstring (external-content, trigger-synced), built by `index --refresh`. Pure accelerator — identical rows, found faster: 23x–113x on selective queries over a 295k-symbol corpus, and a signature scan on a 236k-symbol corpus went 251 ms → 0.6 ms. It falls back **transparently** to the correct LIKE scan when the index was never built (stderr names the one command that fixes it), when a term is **under 3 characters**, or when a term contains `*`/`?`. Opt out per project with `[search] fts = false` in `.blueprint.toml` (default `true`); the next `index --refresh` drops the index and keeps the slower correct scan.
- **`spine_cache`** materializes reachability, so `--spine`/`--off-spine` read a table stamped with the build fingerprint instead of re-walking the graph; `status` refreshes it for free (it already computed the reachable set). On a 61.8k-declaration corpus: `spine` 3.9s · unscoped `search` 0.5s · `search --spine` cold 3.8s · **warm 0.3s**. A snapshot whose stamp doesn't match the current build is never silently used — it rebuilds by default, or with `--no-refresh` prints `⚠ spine cache STALE` (exit 2 if there is no snapshot at all).

**Declaring deliberate off-spine work: `register`** — so audits can tell a diagnostic harness from orphan drift.
```bash
proof-blueprint register add <Lean.symbol> --reason "…" [--category diagnostic|infra|compat|scratch]
proof-blueprint register                   # bare: list them all
proof-blueprint register list [--stale] [--json]
proof-blueprint register remove <symbol>
proof-blueprint register prune [--dry-run]
```
You author only the justification; both facts under it are re-derived, never stored. `register add` refuses unless the symbol is **in the index** (else exit 2) and is **genuinely unreachable from every `target_symbol` in a live mined graph** (else exit 1) — and refuses outright (exit 2) when there is no build or no mined graph to check against. So it can mark an off-spine decl deliberate; it can never make on-spine work look off-spine, and it cannot keep a deleted symbol alive.

`register list` re-checks every row: `✗` symbol left the index, `⚠` **now on-spine** (the happy case — scaffolding got wired into the real proof, so the registration is obsolete). `register prune` drops both; without a live graph it prunes only the vanished ones and says so. Registrations are **intent** — exported to `intent/offspine.toml`, so they land in git and get reviewed (unlike `anchor`, which is ephemeral). Downstream: `packet-audit` splits them out of its off-spine inventory ③, `status` marks them `📌`, and `search --registered/--unregistered` facet on them.

**Kernel-mined call graph — the only proof structure**
```bash
proof-blueprint refs --refresh         # mine getUsedConstants edges from the oleans (needs warm Lake)
proof-blueprint refs --refresh --force # re-mine every built module, ignoring incrementality (use after a miner change)
proof-blueprint refs --check           # staleness report vs current build; no kernel
proof-blueprint spine [<symbol>] [--max-depth N] [--full]   # structural tree rooted at target_symbol (or <symbol>)
proof-blueprint spine --all-roots [--full]   # one spine block per top-level root symbol (ignores symbol/target_symbol)
proof-blueprint spine --files          # machine-readable: absolute path of every ACTIVE spine source file
proof-blueprint tree  [<symbol>] [--max-depth N] [--full]   # alias of spine
proof-blueprint show-targets           # configured target_symbol(s) (w/ OPEN/closed state) + available root symbols
proof-blueprint status                 # last build (outcome·cached/built N·dur·age) + graph-mine age + index counts + spine state + live-sorry cache (fresh/offline) + anchor fleet + your anchor
proof-blueprint axioms <symbol> [--memory-mb N]    # live #print axioms for one symbol
```
`spine` auto-refreshes a stale graph if the build is warm (no manual `refs --refresh` needed in that case). Output structure, in order:

1. **Header**: `spine rooted at: <symbol>`, approved axiom set.
2. **Progress**: `open: N/M node(s)` — the OPEN count (goal 0), not closed. Closed rises when you *add* proven nodes to the spine (reads as progress that isn't); the open count only drops when an on-spine sorry is actually discharged, so that is the number to watch.
3. **Flat open-obligations list**: `open obligations (N):` — one line per open leaf (`symbol  [sorry|unmined|stale]`). This is the primary answer to "what's left?"; read this first.
4. **Tree view**: open-frontier rendering by default — closed subtrees collapse to `✓ N closed dep(s)` (pass `--full` to expand). Each project node carries `⚠ subtree-axioms: {…}` for unapproved axioms reachable from that subtree. **Session anchors render on the node they sit on**, as `⚓ <short-sid>` plus ` (YOU)` for this session and the note when one is set; several sessions on one node all appear there, most recently updated first. There is **no** `active anchors` list above the tree. An anchor the tree did not reach is reported below it under `anchors not on this tree (N):` with a reason — `not on this spine` (belongs to a different target), `closed subtree — collapsed; --full shows it` (the work there is usually finished), or `not drawn — below --max-depth`.

When several targets are configured (the list form) and no positional symbol is given, `spine` renders one block per target (`target spine view: N configured target_symbol(s)` → a spine each → `targets summary: K/M target(s) still open`, goal 0); exit 0 only if all pass. A positional symbol overrides this and renders just that one. `--all-roots` renders the above blocks (header → verdict) once per top-level root symbol — every call-graph root, not just the configured targets — then one combined off-spine section and an `all-roots summary: K/M root(s) still open` line. It ignores any positional symbol, exits 0 only if every root is kernel-complete (else 1), and composes with `--full`.
5. **Unapproved-axiom summary**: `branches with unapproved axioms (N):` — every flagged branch in one place.
6. **Kernel-complete verdict**: `✅ kernel-complete` or `❌ NOT kernel-complete — spine has: …`
7. **Off-spine sorries** (advisory): `⚠ off-spine sorries (N …) — placeholder sorries are no longer allowed; all live work must be wired into the spine` lists `has_sorry` decls in imported files the target doesn't reach. Standing policy — a sorry *off* the spine is a placeholder to wire into the target's spine or delete; a sorry *on* the spine is the legitimate open frontier (listed under open obligations). `status` and `verify-publish` print `off-spine sorries: none — all live work is wired into the spine` when clean. Never changes an exit code (`spine`/`tree`/`status`/`verify-publish` all carry it).
8. **Unimported files**: `unimported files (N file(s), M symbol(s) ...)` — Lean source files not reachable via the import graph (off the call spine). Sorry symbols inside them are listed. These don't block the publication gate but represent dead or disconnected code worth auditing.

**`--files` — the ACTIVE spine file set.** Replaces the whole render with one absolute `.lean` path per line on stdout (everything else, including an auto-refresh mine's progress, goes to stderr), sorted and deduped. The set is every indexed file declaring a symbol reachable from the root(s) — the union across targets, or across every root under `--all-roots`; a positional symbol scopes it to that one. Dead and off-spine WIP sources are excluded by construction. Exit is **0 with a non-empty list, 2 when empty** — deliberately *not* the render's open/closed exit, so a consumer of the file list doesn't have to treat the normal open spine as a failure. `--max-depth`/`--full` don't apply. This is what `lake-build --spine-archive` packs; the set is reachability-derived and **not import-closed**, so a spine file may import a module absent from it.

A root is **kernel-complete** iff every branch closes under the approved set; exit 1 if not.

**Session work cursor: `anchor`** — where this session is working on the spine; keyed on `$CLAUDE_SESSION_ID` (override `--session`), one anchor per session.
```bash
proof-blueprint anchor                 # show this session's anchor + spine context around it
proof-blueprint anchor set <Lean.symbol> [--note "…"] [--force]
proof-blueprint anchor clear           # --session <id> clears another session (full id or short 8-char prefix)
proof-blueprint anchor list            # every session's anchor (who is working where)
proof-blueprint anchor prune [--dry-run] [--superseded] [--older-than DAYS]
```
`anchor prune` clears other sessions' dead cursors — never your own (`clear` does that), and it echoes each removed symbol + note. Default categories are `gone` (symbol absent from the source index) and `closed` (subtree closes; skipped, not guessed, with no mined graph). An indexed-but-stale/unmined symbol is never pruned — that calls for `refs --refresh`, not deletion. `--older-than DAYS` (abandoned session) and `--superseded` (a newer anchor holds the same symbol) are opt-in, because a long-running branch and a concurrent fleet look identical to those rules; a default run reports how many it left for each.

**Kernel-validated — an anchor cannot point at fiction.** `anchor set` rejects the target unless ALL of:
1. there is a **compiled build** (`lake build` must have run — no oleans → error; stale graph → auto-refreshes with a 15s timeout),
2. it is an **indexed project symbol reachable from `target_symbol`** in the mined graph — or from any one of them when several targets are configured (off-spine work cannot be anchored — the compiled proof doesn't use it),
3. its kernel subtree is **still open** — reaches `sorry`, an unapproved axiom, or something stale/unmined (finished branches cannot be anchored),
4. the move **descends** along kernel call edges from the current anchor; anything else requires `--force --note '…'` (a deliberate, recorded jump, never silent drift).

For openness, `sorryAx` is never treated as approved — even in `wip` state, a sorry is exactly the open work the cursor points at. Running bare `anchor` with no cursor set while the target's spine is open prints a warning on stdout (the stream a SessionStart hook injects as context): anchor onto the open frontier before doing anything else. The anchor is **ephemeral, machine-local** — never exported to `intent/`, forgotten when the DB build artifact is rebuilt, and it asserts no truth (branch state is recomputed on every show).

**Publication gate** — exit 1 on any failure; wire into pre-push:
```bash
proof-blueprint verify-publish [--target-symbol SYM] [--no-refresh] [--memory-mb N]
```
1. `target_symbol` is kernel-clean — `#print axioms` on the top theorem; any custom axiom not approved blocks. *This catches an axiom hiding on the spine.*
2. The mined spine of `target_symbol` is **live and closed** — no stale/unmined symbols, no reachable `sorry`.
3. *(2026-08-30 extension)* **Runtime trust and computational evidence.** Native reduction and evaluated `unsafe`/`partial`/`@[implemented_by]`/`@[extern]` boundaries on a target must be covered by `[trust]`, and every configured `[computations]` promotion manifest must pass its custody/replay/ingress checks — promotion findings become blockers. `--no-refresh` now **fails closed**: it disables the live kernel checks and therefore blocks a publication verdict (usable as a state probe, never as a pass).

All checks read only kernel artifacts and retained, digest-bound evidence; no agent-authored input can satisfy them. With several configured targets the checks run against every one and the gate passes only if all clear; `--target-symbol SYM` overrides to gate exactly one. `sorryAx` and unapproved axioms always block publish regardless of `[publish].state`. The header always prints the claimed `target_symbol`(s) and the full approved-axiom list — the two irreducible trust surfaces.

**Consistency audit** — exit 1 on any ERROR, warnings exit 0:
```bash
proof-blueprint audit [--refresh] [--memory-mb N]
```
| Finding | Sev | Meaning |
|---|---|---|
| unsanctioned axiom on target spine ❌ | ERROR | `target_symbol`'s kernel closure has an unapproved custom axiom (needs `--refresh`). |
| promotion-record finding ❌ | ERROR | *(2026-08-30 extension)* A configured `[computations]` promotion manifest is malformed, stale, unbound, or fails a custody/replay/ingress check. |
| diagnostic-record finding ⚠ | WARN | *(2026-08-30 extension)* A configured diagnostic manifest fails a check — advisory; a diagnostic record never promotes a claim. |
| call graph stale/missing ⚠ | WARN | Mined graph doesn't match the current build — `refs --refresh`. |
| sanction matches no axiom ⚠ | WARN | An approved axiom matches no indexed `axiom` symbol (stale/typo). |
| target unset ⚠ | WARN | `[publish] target_symbol` missing — nothing is being claimed; no target kernel query runs. |

With publication targets configured, bare `audit` inventories the configured evidence and current DB/index/graph state while explicitly warning that target closures were **not** re-checked; `audit --refresh` queries the targets' axiom closures — and, when native reduction is present, runtime trust — live through Lean.

**Axiom approval — `.blueprint.toml` is the source of truth**
```toml
[publish]
target_symbol = "Mod.theorem"
state = "wip"        # "wip" | "complete" — config compat; affects no verdict

[axioms]
approved = ["MyProj.literature_axiom_xyz"]   # deliberate imports; core axioms are implicit — don't list them
```
The tool implicitly approves `propext`, `Classical.choice`, `Quot.sound`,
`Lean.ofReduceBool`, `Lean.ofReduceNat`, and `Lean.trustCompiler` — the last three
being native-reduction trust, which `axioms` labels `core*` with a footnote naming
the compiler-trust cost. This is a tool classification, not a repository's
proof-policy whitelist: a repository may be stricter, and a `core*` pass is not a
native-decision audit. `sorryAx` is **never** approved in any view — a sorry is
always open work. Legacy DB sanctions (`sanction-axiom`/`unsanction-axiom`) still
work and are unioned in for back-compat, but edit the toml instead;
`migrate-sanctions` prints the toml lines for existing DB rows (does not auto-edit).

**Removed: authored proof structure.** The entire `obligation {add,rm,back,unback,depend,undepend,mark,ingest,set-layer}` / `layer` / `derive` surface is **gone**. An agent-authored obligation tree is not a trust surface — an agent can hide a gap by not modelling it, or anchor work to a stub. The legacy tables remain in old DBs but are dormant: nothing writes them, nothing reads them for enforcement. To carry legacy obligation titles forward as prose labels on spine symbols (zero structural power):
```bash
proof-blueprint migrate-labels [--dry-run]   # keeps only backings that sit on the live spine
```

**Scaffold / v1 migration**
```bash
proof-blueprint scaffold module <Mod.Path> [--import M]... [--namespace NS|--no-namespace]   # never overwrites (exit 2)
proof-blueprint migrate [--from-db PATH] [--dry-run]    # import v1 intent into the active v2 DB
```

**Intent export/import (DB is a build artifact, `intent/` is source of truth)**
```bash
proof-blueprint intent export   # DB intent tables -> intent/*.toml (5 stable-sorted files)
proof-blueprint intent import   # rebuild DB intent from TOMLs; refuses non-empty DB unless --force
proof-blueprint intent diff     # row-level DB-vs-TOML sync check (useful pre-commit)
proof-blueprint bootstrap       # init + import (if intent/ exists and DB empty) + index --refresh
```

`data/proof-blueprint.db` is gitignored in adopted projects; **`intent/` is checked in and is the durable record** of what humans authored: `labels.toml`, `axiom_sanctions.toml`, `notes.toml`, `literature.toml`, `offspine.toml`. Structure is deliberately absent — it is re-mined from the oleans, not imported. After DB-only intent mutations such as `register` or the legacy migration/sanction commands, run `intent export` and commit the TOML diff; `references` mutations are the exception because they persist their TOML themselves. `intent diff` confirms the records agree. Worktree drift is gone because there's no per-worktree DB to drift — each worktree rebuilds from the shared TOMLs + its own `refs --refresh`.

**Durable bibliography references**
```bash
proof-blueprint references add KEY --title TITLE [--citation C] [--url URL] [--note NOTE]
proof-blueprint references update KEY [--title TITLE] [--citation C] [--url URL] [--note NOTE]
proof-blueprint references list [--json]
proof-blueprint references show KEY [--json]
proof-blueprint references remove KEY
```

`intent/literature.toml` is the checked-in canonical bibliography; SQLite's
`literature` table is its rebuildable working copy, and `KEY` is the stable
legacy-compatible literature slug. `add`/`update`/`remove` hold the shared
intent lock and persist DB plus canonical TOML as one compensated operation:
on a write or commit failure the prior durable bytes and DB transaction are
restored. Do **not** follow a successful references mutation with `intent
export`.

Every references command, including `list` and `show`, fails closed (exit 2)
when an existing `intent/literature.toml` differs from the DB; it never reads
through or overwrites drift. Decide which side is authoritative, then run
`intent import --force` when TOML wins or `intent export` when DB wins.
`intent diff` includes literature field drift and also reports duplicate,
unsupported, commented, or otherwise noncanonical TOML instead of silently
normalizing it.

**Placeholder policy (since 2026-06-04): axiom approvals are for genuine literature imports only.** An in-project claim that isn't proven yet is a `sorry`-backed theorem (💧 open branch), not a named `axiom` — do not declare a local axiom for work the project intends to prove, and do not approve one to make a gate pass. See the lean-usage skill's "Proof obligations and tractability" policy for the canonical pattern and measured-frontier requirements.

**`native_decide` policy (since 2026-06-05): allowed under the `bv_decide`
standard.** Audit the literal `axioms <symbol>` output against the repository's
exact whitelist. Under the math-projects policy it may contain only `propext`,
`Classical.choice`, `Quot.sound`, `Lean.ofReduceBool`, and `Lean.trustCompiler`;
reject `sorryAx` and every axiom outside that whitelist even if the generic gate
approves it, and report the `Lean.trustCompiler` compiler-trust cost explicitly.
`Lean.trustCompiler` is core-allowed by the tool and needs no `[axioms].approved`
entry (`axioms` prints it as `core*` under the native-reduction-trust footnote —
that is the reporting channel, not the audit). Separately inspect the
transitive evaluated
`Decidable` closure and reject any `unsafe`, `@[implemented_by]`, or `@[extern]`.
A textual grep is only a preflight, not proof of a clean closure. See the lean-usage
skill's `native_decide` policy for the full procedure. Under the 2026-08-30
extension this audit is machine-enforced for publication targets via `[trust]` —
see the next section.

## Computational evidence — `[trust]` + `[computations]` (Rust extension, 2026-08-30)

Computational results (SAT/SMT, CAS, first-order provers, DRAT/LRAT, generated
code, CEGAR waves, external services) are **promotion input, not proof by
assertion**. A promotion record must bind the exact mathematical claim, its Lean
consumers, the computation that produced the evidence, retained artifacts,
checked replays, and the current Lean build. There is no new subcommand:
**`audit` checks all configured records; `verify-publish` treats promotion
findings as blockers** for the selected targets. A `diagnostic` record is still
checked but only warns and never promotes a claim — and a diagnostic parent
relied on by a promotion is revalidated at error severity, so warning-grade
history cannot smuggle broken evidence into publication.

```toml
[trust]                      # exact fully-qualified names; all default empty
native_axioms = []           # complete native-axiom closure, else native reduction cannot promote
unsafe = []                  # evaluated boundaries — each must be explicitly listed
partial = []
implemented_by = []
extern = []

[computations]
manifests = ["evidence/example.toml"]   # ordered, repo-relative .toml paths
```

- **Trust sets are the machine-checked form of the `native_decide` audit above.**
  Native reduction is forbidden for promotion unless the complete native-axiom
  closure is listed in `native_axioms` — and an ordinary custom axiom stays
  forbidden in that closure even when `[axioms].approved` lists it. Evaluated
  `unsafe`, `partial`, `implemented_by`, and `extern` boundaries must each be
  explicitly listed.
- **Manifests** are strict schema-1 TOML envelopes: `record_kind = "promotion" |
  "diagnostic"`, a lane, and one domain-separated `self_hash`. Blank, duplicate,
  escaping, absolute, non-`.toml`, symlinked, and hard-linked manifest paths are
  rejected. Every bound path is read as a regular repository file and rehashed,
  including artifacts reached only through recursive parent records. There is
  **no manifest-writing subcommand**: fill `self_hash` from the expected digest
  reported by the audit/publish mismatch, then rerun.
- **Ten lanes**, each with mandatory artifact roles, check kinds, Lean
  obligations, and a fail-closed terminal result:
  `sat-unsat`/`smt-unsat`/`piqd-unsat`/`cegar` → `CERTIFIED_UNSAT`;
  `sat-model`/`smt-model`/`fo-model` → `VERIFIED_WITNESS`;
  `cas-exact`/`external` → `EXACT_CHECKED`; `fo-proof` → `CHECKED_PROOF`;
  `drat-lrat`/`generated` → `KERNEL_CHECKED`. An absent, malformed, stale,
  `UNKNOWN`, timed-out, budget-exceeded, or disagreeing result never promotes.
  An UNSAT claim needs a retained certificate, a checked replay, and an
  **independent replay by a verifier whose binary digest differs from the
  producing run's**. A check's name is not a semantic assertion — promotion also
  requires a successful result, zero exit status, and nonempty
  command/input/output bindings.
- **Lean ingress binds the graph.** The ingress declaration, immediate checked
  consumer, and final publication consumer must be three distinct declarations,
  all fresh in the live mined graph with final → immediate → ingress
  reachability, hash-bound to source captures before and after replay, the
  recomputed import closure, and the current build fingerprint. Every promotion
  obligation must match exactly one live indexed declaration by statement and
  raw-signature hash.
- **Exclusions are not escape hatches.** Every configured `[mining].skip` /
  `[index].skip` pattern must be exactly named by a valid promotion's
  `[exclusions]`.
- **Boundary.** The manifest is a custody-and-binding envelope, not an execution
  engine: proof-blueprint never executes the recorded commands, inspects solver
  semantics, or proves a certificate mathematically sound. It enforces bindings,
  digests, bounded vocabularies, roles, and terminal labels/status codes.

Full schema and workflow:
`~/projects/rustprojects/proof-blueprint/docs/computational-hygiene.md` and
`docs/computation-manifest-v1.md`; a complete fixture-shaped SAT/UNSAT record is
`docs/examples/computation-manifest-sat-unsat.toml`.

## Branch-state glossary

`spine` / `tree` annotate each branch, and `anchor` reports its subtree, with kernel-derived states:

| Marker | State | Meaning |
|---|---|---|
| 💧 | sorry | Branch reaches `sorryAx` — open work, in every view; blocks publish. |
| ❌ | unapproved axiom | A custom axiom on the branch is not in the approved set. *Silent blocker — looks "compiled."* |
| 🪶 | approved axiom | A deliberately approved non-core axiom is on the branch (visible, allowed). |
| ⏳ | stale | Mined against an older build — `refs --refresh`. |
| ❓ | unmined | A project symbol the graph has never vouched for — unknown, not clean. |
| ✓ | closed | The subtree closes under the approved set. |

A branch is **open** (anchorable) iff it reaches a sorry, an unapproved axiom, or anything stale/unmined; the default `spine` view shows exactly those branches. Only ✓ (and 🪶, modulo its stated axiom) means "proven." When mapping to proof-prose: ✓/🪶 → matrix row `✅ done`; 💧/❌/⏳/❓ → `⬜ open` (or 🟡 partial). Never report ⏳/❓ as done — "the kernel hasn't looked at this build" is not "it's clean."

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success (or audit clean-of-errors with warnings). |
| 1 | A gate failed: `verify-publish` blocker, `audit` ERROR, `spine`/`status` not kernel-complete (sorry/unapproved axiom on spine), `index --check` drift, `search` matched nothing, or `register add` was handed an **on-spine** symbol. |
| 2 | Prereq not met or usage error: no `.blueprint.toml`, mined graph absent or stale (`status` exits 2 when refs need refresh), rejected anchor, off-spine symbol, file exists, schema mismatch, `search` given no criteria or an unestablishable spine scope, `register add` given an unindexed symbol or no live graph. |
| 3 | Lean kernel invocation failed (bad Lake project, OOM, timeout). |

## Common mistakes

- **Trusting a cold "clean."** `verify-publish --no-refresh` / `audit` without `--refresh` never invoke the kernel; the run that means something is the one after a warm `lake build`. The 2026-08-30 extension makes this structural: `--no-refresh` blocks the publication verdict outright.
- **Reaching for `rg` — or for `nthdegree` — to find a theorem in *this* project.** In-project Lean search is `proof-blueprint search`, always: it matches names, statements *and* docstrings over the index, and it is the only tool that can answer "is this hit on the publish spine?". `nthdegree docs search --lean` is the cross-project tool — use it when the target lives in mathlib, another project, or an ingested paper. Grep the source once you already know which declaration you want.
- **Running `index --refresh` after a CLI upgrade and expecting new columns.** Unchanged sources take the skip path, so `--doc`/`--attr` match nothing and the FTS index isn't built. `index --refresh --force`, once.
- **Deleting off-spine work to quiet an audit.** If it is deliberate (a diagnostic, a harness, a compat wrapper), `register add` it with a reason. If it isn't, wire it in or delete it — but don't silence the signal by hand.
- **Reading ⏳/❓ as proven.** Stale and unmined are unknown, not clean.
- **Editing `.lean` and expecting the graph to notice.** Freshness tracks the *build* fingerprint. Until you `lake build` + `refs --refresh`, the graph describes the last clean build.
- **Expecting a "mark proven" or `obligation add` command.** Neither exists by design. You change state by changing the Lean (or approving an axiom with justification in the toml). If you reach for obligation/layer/derive commands from old docs, you're on a stale skill — structure is `refs --refresh` → `spine`.
- **Anchoring before building.** A stale graph auto-refreshes (15s timeout) — you don't need to manually re-mine after a warm `lake build`. But if no compiled build exists at all (`lake build` has never run or the build dir was wiped), `anchor set` exits with an error. Fix: `lake build`, then retry — `anchor set` will auto-mine from there.
- **Following the math-projects README's wrapper pattern.** The legacy Python repo at `~/projects/math-projects/proof-blueprint` (v1 `cli.py` + per-project wrapper scripts) is superseded twice over: by the global v2 CLI, and now by the Rust port. The current source of truth is `~/projects/rustprojects/proof-blueprint/USAGE.md`. Use `proof-blueprint` directly.
- **Expecting the deployed binary to enforce `[trust]`/`[computations]`.** The release binary on `PATH` may predate the 2026-08-30 extension (check the Install section's version-skew note) — a pass from an old binary is not a computational-hygiene pass. Rebuild the release, or run via `cargo run -p proof-blueprint`.
