---
name: lean-shard
description: "Use when a Lean source file is too large because of compile time, import bloat, or generated proofs, or when a previously sharded file needs re-sharding. Splits it into bounded helper shards plus a thin coordinator using the lean-shard CLI: plan/apply/normalize, TOML policy, manifest format, and re-sharding."
---

# lean-shard

CLI for splitting one Lean source file into helper shards (each ≤ a byte budget) plus a coordinator that imports them in order.

**Binary:** `~/bin/lean-shard` (symlink to `~/projects/rustprojects/target/release/lean-shard`)
**Source:** `~/projects/rustprojects/lean-shard/` (`lean-shard` CLI, `lean-sharding-core` library)
**Spec:** `~/projects/rustprojects/lean-shard/usage.md`

## Subcommands

| Command     | What it does                                                             |
|-------------|--------------------------------------------------------------------------|
| `plan`      | Parse + plan + render in memory; emit manifest. **No files written.**    |
| `apply`     | Same as `plan`, plus write helpers + coordinator under `--output-dir`.   |
| `normalize` | Strip stale helper imports; emit canonical re-shardable form. Idempotent. |

All three take `--config <toml>` and `--input <lean>`.

## Correct usage

### Plan (dry run)

```bash
lean-shard plan --config policy.toml --input Source.lean
lean-shard plan --config policy.toml --input Source.lean --manifest plan.json
```

Manifest goes to stdout unless `--manifest <path>` is given. Use `plan` to verify shard count and sizes before touching the filesystem.

### Apply (write files)

```bash
lean-shard apply \
  --config     policy.toml \
  --input      Source.lean \
  --output-dir out/ \
  --manifest   out/manifest.json
```

Writes every helper first, then the coordinator — partial failure never leaves a coordinator pointing at missing helpers. Helper paths come from `helper_module_prefix` + `helper_stem_template`; coordinator path from `coordinator_file_path` (relative to `--output-dir`).

### Normalize (re-shard prep)

```bash
lean-shard normalize --config policy.toml --input Source.lean
lean-shard normalize --config policy.toml --input Source.lean --output Source.lean
```

Strips imports of `helper_module_prefix.*` and `coordinator_module_path`, dedupes and sorts the rest. **Run this before re-sharding** — otherwise stale helper imports from a previous run will be carried into the new helpers. `normalize` then `plan`/`apply` is a fixed point.

## Policy TOML

```toml
[policy]
max_bytes               = 1_000_000      # byte budget per helper (rendered UTF-8)
allow_overflow          = false          # true = oversized blocks become singleton shards
mode                    = "ImportLevel"  # ImportLevel | ProofBlock | ClauseLevel (currently advisory)
helper_module_prefix    = "Pkg.Gen"
helper_stem_template    = "Step_{n}"     # `{n}` required; replaced by zero-padded index
zero_pad                = 4
coordinator_module_path = "Pkg.Coordinator"
coordinator_file_path   = "Pkg/Coordinator.lean"

[adapter]
kind              = "regex"
block_start_regex = '^(theorem|lemma)\s+\w+'
drop_import_regex = '^Pkg\.Gen\.'        # optional: prunes prior-run helper imports during parse
```

### Field notes

- `max_bytes` is enforced on the **rendered** helper (imports + prelude + bodies), not the source slice.
- `allow_overflow = false` → planner errors with `BlockTooLarge` if a single block exceeds `max_bytes`. Set `true` only if you accept oversized singleton shards.
- `mode` is currently advisory — the planner uses one strategy (in-order bin packing) regardless. The field is preserved on the manifest so adapters can branch on it.
- `helper_stem_template` **must** contain the literal `{n}`.

### Adapter (`kind = "regex"`)

- `block_start_regex` is matched against **each full line**. Each match starts a block; the block runs from that line up to (not including) the next match, or EOF. Capture group 1 (if present) becomes the block's `kind` tag (`"theorem"`, `"lemma"`); otherwise `"block"`.
- `drop_import_regex` (optional) — imports whose module path matches are dropped during parse. Typical use: prune previous-run helpers before re-sharding.
- The Rust `regex` crate has **no look-around**. Express "drop helpers, keep everything else" as `^Pkg\.Gen\.` — not as a negative look-ahead.

## Manifest

`plan` and `apply` emit a JSON manifest with one entry per helper plus one for the coordinator:

```json
{
  "source_path": "Source.lean",
  "policy": { "max_bytes": 1000000, "mode": "ImportLevel",
              "helper_module_prefix": "Pkg.Gen",
              "coordinator_module_path": "Pkg.Coordinator" },
  "helpers": [
    { "module_path": "Pkg.Gen.Step_0001",
      "file_path":   "Pkg/Gen/Step_0001.lean",
      "size_bytes":  742, "checksum": "<sha256-hex>",
      "block_count": 3,  "helper_imports": [] }
  ],
  "coordinator": {
    "module_path": "Pkg.Coordinator",
    "file_path":   "Pkg/Coordinator.lean",
    "size_bytes":  180, "checksum": "<sha256-hex>",
    "block_count": 0,  "helper_imports": ["Pkg.Gen.Step_0001"]
  }
}
```

`checksum = sha256(rendered_bytes)`. Combined with `module_path`, that pair is enough to key a build cache.

## Determinism

For a fixed `(input, policy, adapter)`:

- Same shard count, filenames, module paths every run.
- Same byte budget → same chunk boundaries (no filesystem-order or wall-clock dependence).
- `normalize` then `plan`/`apply` is a fixed point.

Use this for caching and CI: the manifest's checksums are stable.

## Re-sharding workflow

When a file already has helper imports from a previous run:

```bash
# 1. Strip stale helper imports in place.
lean-shard normalize --config policy.toml --input Pkg/Source.lean --output Pkg/Source.lean

# 2. Re-shard cleanly.
lean-shard apply --config policy.toml --input Pkg/Source.lean \
                 --output-dir . --manifest Pkg/manifest.json
```

Skipping step 1 will leave dangling helper imports inside the new helpers and inflate their sizes.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success. |
| 1 | Planner / renderer error (`BlockTooLarge` with overflow disabled, dependency cycle, malformed config, IO failure). |
| 2 | Argument-parse error (clap). |

## Custom adapters

The bundled `regex` adapter handles the common case (one `theorem`/`lemma` per line, predictable headers). For richer parsing — DRAT emission, proof-body sharding with `have`/`show` blocks, structured dependency extraction — write a new crate that depends on `lean-sharding-core` and implements the `Adapter` trait. Don't fork `lean-shard`; either expose your own thin CLI or call the library directly.

## Common pitfalls

- **Forgetting to `normalize` before re-shard** — stale helper imports get baked into new helpers and inflate `size_bytes`.
- **Negative look-ahead in `drop_import_regex`** — not supported by the `regex` crate. Use a positive prefix match.
- **`helper_stem_template` without `{n}`** — config error; the planner needs the substitution.
- **`max_bytes` set against source byte count** — the budget is for **rendered** helper bytes (includes imports + prelude). A source slice that fits the budget can render larger; size with `plan` first.
- **`allow_overflow = true` masking real problems** — if a single block exceeds the budget, that's usually a signal to split the block (different adapter, finer `block_start_regex`), not silently emit an oversized shard.
