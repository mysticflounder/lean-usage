---
name: drat-to-lean
description: "Run a user-provided DRAT-to-Lean pipeline checkout: encode a magma non-existence claim to CNF, solve with CaDiCaL, trim to LRAT, and emit a Lean 4 proof candidate. The generated file requires a source-to-CNF audit and final consumer trust audit; deeper output can contain `sorry`."
---

# drat-to-lean

Six-stage pipeline that turns a magma/Latin-square non-existence claim into a
Lean 4 theorem candidate. A successful pipeline run does not by itself show
that the source claim was encoded faithfully or that the emitted theorem is
acceptable to a downstream consumer. Depth 1 may produce a theorem with only
`propext` after the required audits; deeper proofs can still carry `sorry`
(see [Lean output](#lean-output)):

```
encode_cnf  →  cadical  →  drat-trim  →  pipeline.run_pipeline_from_cnf  →  emit_lean  →  lake env lean
   (1)         (2)          (3)                  (4)                          (5)          (6)
```

This distribution does not include the pipeline checkout, CaDiCaL, or
`drat-trim`. Use a checkout and binaries supplied by the user. Discover
executables on `PATH` (for example, `command -v cadical` and
`command -v drat-trim`) or pass explicit paths, then run the pipeline's
`--help` before doing a long run. Do not assume an installation directory or
invent a download URL.

**Entry point:** `<supplied-checkout>/scripts/drat_to_lean.py`

## Correct usage

### Full pipeline from a depth `d`

```bash
cd /path/to/the-missing-pair       # checkout supplied by the user
uv run --no-project python scripts/drat_to_lean.py --help
uv run --no-project python scripts/drat_to_lean.py 7 \
  --workdir lean/scratch/drat-work/d7 \
  --out lean/scratch/MyProof.lean \
  --theorem-name my_thm \
  --encoder drat_mine                  # or drat_extract
```

The checkout path, output path, and work directory above are examples only;
replace them with paths supplied by the user. Keep generated artifacts in the
checkout's project-local scratch area so the run is reviewable and does not
depend on a private global directory.
Keep an explicit `--workdir` on generation invocations; the external script's
default scratch directory may be outside the checkout.
If the checkout or required dependencies are absent, report what is missing and
stop before generation. Follow that checkout's documented dependency setup.

### Reusing existing CNF + DRAT (gap-1, gap-2+)

If you already have artifacts (e.g. from a long cube-and-conquer run):

```bash
uv run --no-project python scripts/drat_to_lean.py 7 \
  --workdir lean/scratch/drat-work/d7 \
  --cnf  /path/to/artifact.cnf \
  --proof /path/to/artifact.drat \
  --out   lean/scratch/GapNOutput.lean
```

Pipeline skips stages (1) and (2) and jumps straight to drat-trim.

### Override binaries

```bash
uv run --no-project python scripts/drat_to_lean.py 7 \
  --workdir lean/scratch/drat-work/d7 \
  --cadical   /path/to/supplied/cadical \
  --drat-trim /path/to/supplied/drat-trim
```

Prefer an explicit `--drat-trim` path discovered from the user's environment.
Inspect the supplied script's lookup behavior; fallback directories vary by
revision and are not an installation mechanism.

## The six stages in detail

| # | Stage | Command / call |
|---|-------|----------------|
| 1 | Encode | `no-algebra/drat/drat_mine.py:encode_cnf(d)` → ~`d³` vars, ~`2d³` clauses |
| 2 | SAT solve | `cadical --no-binary <cnf> <drat>` (rc 20 = UNSAT, 10 = SAT) |
| 3 | Trim to LRAT | `drat-trim <cnf> <drat> -L <lrat> -c <core.cnf>` (expect `s VERIFIED`) |
| 4 | Parse proof | `drat_reader.pipeline.run_pipeline_from_cnf()` — builds the DAG, attributes clauses |
| 5 | Emit Lean | `emit_lean()` → `lean/scratch/DratGap0D<d>.lean` by default |
| 6 | Verify | `lake env lean <path>` checks elaboration only. A file with `sorry` still elaborates, so inspect the generated file, run `#print axioms`, and perform the final consumer audit before treating the result as trusted. |

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

- **Depth-1 outputs** (pure unit propagation): after both required audits,
  `#print axioms` may show `[propext]`; verify this for each generated file
  before calling it kernel-trusted.
- **Depth >1** (resolution trees): output can contain branches with `sorry`.
  Such output remains partial until the holes close and the trust audits pass.

## Common mistakes / footguns

- **Cadical option spelling**: pass options in the form accepted by the
  supplied binary; check `cadical --help` before a long run, and keep option
  arguments space-separated where the binary requires it.
- **Missing `--no-binary`**: cadical defaults to binary DRAT which `drat-trim` accepts but the repo's parsers expect text DRAT. Always pass `--no-binary` when feeding the Python `drat_reader` stack.
- **drat-trim not on PATH**: no fallback solver — pipeline fails. Pass
  `--drat-trim` explicitly with a user-supplied binary.
- **drat-trim hangs with no timeout**: there is no subprocess timeout around drat-trim (unlike cadical). For hostile instances add a timeout in `drat_reader/trim.py`.
- **Negative LRAT antecedents dropped**: `emit_lean()` silently drops negative (RAT) hints. Proofs that rely on RAT steps emit `sorry` instead of resolving them. Check for `sorry` in output.
- **Backend compatibility**: inspect the supplied checkout's PySAT and CaDiCaL
  pins and proof-format requirements. A backend name does not establish the
  external executable's version or performance.
- **Depth >1 not fully verified**: reject `sorryAx` and unapproved axioms.
  Compare the actual final-consumer closure with the project's trust policy;
  an axiom beyond `propext` is not automatically an unsound axiom.
- **`--encoder` picks wrong variant**: `drat_mine` (default) and `drat_extract` produce different CNFs for the same `d`; don't mix a CNF from one with a proof from the other.

## Required trust audits

A successfully replayed DRAT certificate establishes the supplied CNF is
unsatisfiable under that checker's trust boundary. Before
calling the result a proof of the intended mathematical claim, complete both
audits below.

1. **Source-to-CNF bridge:** inspect the encoder, variable mapping, clause
   groups, fixed hypotheses, and the negated target (for example `NOT_E255`).
   Require a checked reduction connecting the source claim to the exact CNF
   for a kernel-proof claim; encoder inspection alone is insufficient.
2. **Final consumer:** compile the exact generated file in its target Lean
   project, inspect the theorem's `#print axioms` output, search the file and
   dependencies for `sorry`, and exercise the theorem from the downstream
   consumer context. Audit the named final consumer's transitive axioms too.
   Reject a result with `sorryAx` or any unapproved axiom.

Only when both audits pass may a depth-1 result be described as kernel-checked;
`[propext]` must be observed, not assumed. A depth >1 result remains partial
until every generated hole is closed and the same audits pass.

## Inspecting the generated theorem

Use `lake-build` for normal aggregate builds. The direct single-file check below
requires built dependencies, project permission, and no concurrent build; follow
the [build exceptions](../lean-usage/references/build-operations.md#direct-lake-env-lean-exceptions).

```bash
cd /path/to/the-missing-pair       # checkout supplied by the user
lake env lean lean/scratch/DratGap0D7.lean
# Add `#print axioms drat_gap0_d7_unsat` to the file and re-run to see the axiom list.
# For a fully audited depth-1 result, the observed list should be [propext].
```

## Reference files in the repo

- `scripts/drat_to_lean.py` — the orchestrator
- `no-algebra/drat/drat_mine.py` — encoder + DRAT pipeline
- `no-algebra/drat/drat_extract.py` — alternate encoder
- `drat_reader/pipeline.py`, `drat_reader/trim.py`, `drat_reader/emit_lean.py` — proof parsing + Lean codegen
- `lean/scratch/` — generated theorems live here
