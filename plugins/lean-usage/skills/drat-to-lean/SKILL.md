---
name: drat-to-lean
description: "Run the DRAT-to-Lean pipeline in ~/the-missing-pair: encode a magma non-existence claim to CNF, solve with CaDiCaL, trim to LRAT, and emit a Lean 4 proof. Depth-1 output is kernel-checked with `propext` as its only axiom; deeper output can still contain `sorry`, so audit the axioms before you promote it. Use when producing a Lean-verified UNSAT proof from CNF or reproducing or extending the E255/E677-style proofs."
---

# drat-to-lean

Six-stage pipeline that turns a magma/Latin-square non-existence claim into a Lean 4 theorem. At depth 1 the emitted theorem closes with `propext` as its only axiom; deeper proofs can still carry `sorry` (see [Lean output](#lean-output)):

```
encode_cnf  →  cadical  →  drat-trim  →  pipeline.run_pipeline_from_cnf  →  emit_lean  →  lake env lean
   (1)         (2)          (3)                  (4)                          (5)          (6)
```

**Entry point:** `~/the-missing-pair/scripts/drat_to_lean.py`

## Correct usage

### Full pipeline from a depth `d`

```bash
cd ~/the-missing-pair
scripts/drat_to_lean.py 7                           # depth 7
scripts/drat_to_lean.py 7 --out lean/scratch/MyProof.lean
scripts/drat_to_lean.py 7 --theorem-name my_thm
scripts/drat_to_lean.py 7 --workdir /tmp/d7_work    # scratch dir (default /tmp/drat_to_lean_d<d>)
scripts/drat_to_lean.py 7 --encoder drat_mine       # or drat_extract
```

### Reusing existing CNF + DRAT (gap-1, gap-2+)

If you already have artifacts (e.g. from a long cube-and-conquer run):

```bash
scripts/drat_to_lean.py 7 \
  --cnf  /path/to/artifact.cnf \
  --proof /path/to/artifact.drat \
  --out   lean/scratch/GapNOutput.lean
```

Pipeline skips stages (1) and (2) and jumps straight to drat-trim.

### Override binaries

```bash
scripts/drat_to_lean.py 7 \
  --cadical   /usr/local/bin/cadical \
  --drat-trim ~/bin/drat-trim
```

`drat-trim` is resolved from PATH, `/usr/bin`, then `~/bin`. If missing, the script errors — there is no fallback.

## The six stages in detail

| # | Stage | Command / call |
|---|-------|----------------|
| 1 | Encode | `no-algebra/drat/drat_mine.py:encode_cnf(d)` → ~`d³` vars, ~`2d³` clauses |
| 2 | SAT solve | `cadical --no-binary <cnf> <drat>` (rc 20 = UNSAT, 10 = SAT) |
| 3 | Trim to LRAT | `drat-trim <cnf> <drat> -L <lrat> -c <core.cnf>` (expect `s VERIFIED`) |
| 4 | Parse proof | `drat_reader.pipeline.run_pipeline_from_cnf()` — builds the DAG, attributes clauses |
| 5 | Emit Lean | `emit_lean()` → `lean/scratch/DratGap0D<d>.lean` by default |
| 6 | Verify | `lake env lean <path>` — elaboration only. A file with `sorry` still elaborates, so `#print axioms` decides whether the proof is kernel-checked |

## Variable encoding

DIMACS variables are 1-indexed; the mapping from magma cell `M[i][j] = k` to variable is:

```python
v(d, i, j, k) = i * d*d + j * d + k + 1
# and inversely:
decode(d, var)  →  (i, j, k)
```

Axiom groups (attributed in `encoding.py:attribute_clause`):

- **LATIN_ALO / AMO**: each cell has exactly one value
- **ROW_PERM_ALO / AMO**, **COL_PERM_ALO / AMO**: each row / column is a permutation
- **ROW_0_CYCLIC**: `M[0][j] = (j+1) mod d`
- **SIGMA_1**: `M[1][0] = d-2`
- **CONSTR_A / B**: relation constraints from the algebraic identity
- **NOT_E255**: `¬(M[d-2][0] = 0)` — the negation of the claim being falsified

No separate variable-map file is written; the encoding is deterministic and reversible via `decode`.

## Lean output

Default path: `lean/scratch/DratGap0D<d>.lean`

```lean
import Mathlib.Tactic

set_option maxHeartbeats 1000000 in

theorem drat_gap0_d<d>_unsat (M : Fin d → Fin d → Fin d)
    (hcl_<id> : <clause_prop>) ...
    : False := by
  ...
  · exact absurd h h_ne
```

**Dependencies:** `Mathlib.Tactic` only. No LeanSAT / lean-cadical / lean-auto. Tactics used: `rcases`, `intro`, `exact absurd`.

- **Depth-1 proofs** (pure unit propagation): `#print axioms` returns `[propext]`. Fully kernel-trusted.
- **Depth >1** (resolution trees): some branches emit `sorry`. Not kernel-trusted; the proof is partial until those holes close.

## Common mistakes / footguns

- **`-t60` vs `-t 60` for cadical**: arguments must be **space-separated**. Glued (`-t60`) → `error: invalid option '-t60'` and cadical exits 1. The codebase was recently swept for this — see `docs/2026-04-18-cadical-usage-cleanup.md`.
- **Missing `--no-binary`**: cadical defaults to binary DRAT which `drat-trim` accepts but the repo's parsers expect text DRAT. Always pass `--no-binary` when feeding the Python `drat_reader` stack.
- **drat-trim not on PATH**: no fallback solver — pipeline fails. Pass `--drat-trim` explicitly or symlink into `~/bin`.
- **drat-trim hangs with no timeout**: there is no subprocess timeout around drat-trim (unlike cadical). For hostile instances add a timeout in `drat_reader/trim.py`.
- **Negative LRAT antecedents dropped**: `emit_lean()` silently drops negative (RAT) hints. Proofs that rely on RAT steps emit `sorry` instead of resolving them. Check for `sorry` in output.
- **CaDiCaL backend version**: the PySAT wrapper in this repo is pinned to `Cadical195` (matching CaDiCaL 3.0.0). `Cadical153` is slower on UNSAT and will desync with the text-DRAT parsers.
- **Depth >1 not fully verified**: `#print axioms` showing anything beyond `[propext]` means kernel trust is broken. Treat those proofs as work-in-progress.
- **`--encoder` picks wrong variant**: `drat_mine` (default) and `drat_extract` produce different CNFs for the same `d`; don't mix a CNF from one with a proof from the other.

## Verifying the proof is kernel-trusted

```bash
cd ~/the-missing-pair
lake env lean lean/scratch/DratGap0D7.lean
# Add `#print axioms drat_gap0_d7_unsat` to the file and re-run to see the axiom list.
# Goal: [propext] and nothing else.
```

## Reference files in the repo

- `scripts/drat_to_lean.py` — the orchestrator
- `no-algebra/drat/drat_mine.py` — encoder + DRAT pipeline
- `no-algebra/drat/drat_extract.py` — alternate encoder
- `drat_reader/pipeline.py`, `drat_reader/trim.py`, `drat_reader/emit_lean.py` — proof parsing + Lean codegen
- `docs/2026-04-18-cadical-usage-cleanup.md` — the recent sweep's findings
- `lean/scratch/` — generated theorems live here
