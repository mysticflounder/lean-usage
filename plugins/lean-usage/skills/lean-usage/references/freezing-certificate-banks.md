# Freezing certificate banks

Use this reference when a generated certificate corpus must become a stable input
to replay, Lean generation, archival, CI, or publication. A freeze establishes
which exact bytes and tools a later result refers to. It does not itself verify the
certificates or promote their mathematical claim.

Generation, replay, and builds below require the target project's authorization.
Under a no-build/no-run gate, record existing evidence and mark missing checks
incomplete; do not execute them or claim verification to finish the freeze record.

## Keep the claims separate

- **Frozen** means the complete bank has a content-bound identity and can be
  reproduced or retrieved without consulting a changing working tree.
- **Verified** means the frozen bytes were checked by the stated verifier under the
  recorded environment, with the expected coverage and proof shape.
- **Published** means a publication record binds the bank ID and its verification
  evidence ID to the semantic bridge, named Lean ingress and final consumer, and
  the repository's promotion gate.

Do not use “frozen” as a synonym for “verified,” “kernel checked,” or “published.”
A read-only directory is not a freeze unless its contents are independently bound by
the bank manifest.

## Define the bank boundary

Name the logical bank and list every layer needed to interpret it. Depending on the
pipeline, that normally includes:

1. source instances and their encoding configuration;
2. generator or encoder source and command;
3. solver output such as DRAT;
4. normalized or replay-ready certificates such as LRAT;
5. generated Lean payload and shard manifest, when generated before replay;
6. the hand-written checker and soundness theorem;
7. the source-to-encoding semantic bridge and named final consumer.

These are the immutable **input bank**. Replay logs, observed coverage, fresh build
results, and trust-audit output form a separate **verification evidence bundle**
that names the frozen bank ID. Seal that bundle only after verification; never add
new output files to an already frozen input bank.

Raw certificates, generated Lean, compact proofs, and `.olean` files are different
layers. Record them separately; do not combine their counts or sizes under one
ambiguous “bank size.” Compiled artifacts follow the separate cache and archival
rules in [generated-proofs.md](generated-proofs.md#project-owned-olean-archival).

## Freeze procedure

### 1. Pin source and environment identity

Start from a commit or immutable source snapshot. Record:

- repository identity and commit, or an archive digest when no commit exists;
- dataset snapshot, selection filters, configuration, patches, submodules, and LFS
  object identities needed to reconstruct the exact input closure;
- exact Lean toolchain, Lake version, and dependency lock state;
- encoder, generator, solver, normalizer, replay-tool, executable, and worker-image
  digests—not only human-readable version strings;
- complete commands, options, seeds, and output-affecting environment variables;
- exact ingress, checker, semantic-bridge, import, and aggregate-consumer paths,
  bytes, and declaration identities;
- resource limits and worker image when they affect replay or reproducibility.

Generate from a clean detached checkout or declared source archive with no
undeclared local inputs. Do not identify a freeze only by the mutable branch name
or current checkout.

### 2. Check repeatable generation

Generate the bank at least twice from the same pinned inputs in separate empty
directories and clean processes; use independently provisioned matching
environments when practical. Compare the manifests and every output byte. This is
empirical repeatability over the environments tested, not proof that every possible
environment is deterministic. Record the tested scope. Remove or normalize sources
of drift:

- timestamps, hostnames, temporary or absolute paths, and random identifiers;
- unordered map, set, filesystem, or parallel traversal;
- counter allocation tied to unstable iteration order;
- locale, floating-point formatting, line endings, and environment-dependent imports;
- nondeterministic solver settings or unrecorded seeds.

Fix generated output at the emitter. Never hand-edit one generated bank until it
matches another.

### 3. Write a complete manifest

Use a versioned machine-readable manifest. For every retained file, record at least
its repository-relative logical path, role, byte count, and SHA-256 digest. Also
record the pinned identities and commands above, the manifest schema version, and
the expected file count.

Bind coverage independently of the files that happened to be emitted. Record the
expected instance, certificate, shard, and replay-window identifiers (or closed
ranges), a digest of each canonical identifier set, and the frozen source/config or
declared upstream certificate inventory that derives it. Counts are summaries only:
changing a count to match an omitted artifact must not make an incomplete bank pass.

Represent coverage identifiers as unique NFC-normalized JSON strings with no NUL.
For a set digest, sort by unsigned UTF-8 byte sequence and apply RFC 8785 JCS to the
resulting JSON array before hashing it with SHA-256; encode the digest as lowercase
hex. Where order matters, retain and hash the source-derived ordered array instead
of sorting it.

This is an illustrative shape, not a required serialization:

```json
{
  "schema": "certificate-bank-freeze/v1",
  "bank": "example-bank",
  "source": {"repository": "…", "commit": "…"},
  "toolchain": {"lean": "…", "lake": "…", "dependencies": "…"},
  "generation": {"command": ["…"], "tools": {"encoder": "…"}},
  "coverage": {
    "instanceSetSha256": "…", "certificateSetSha256": "…",
    "shardSetSha256": "…"
  },
  "files": [
    {"path": "certificates/0001.lrat", "role": "normalized-lrat",
     "bytes": 0, "sha256": "…"}
  ]
}
```

Manifest paths are UTF-8 NFC logical paths with `/` separators. Reject empty, `.`,
or `..` components; leading `/`; drive or UNC prefixes; backslashes; NUL/control
bytes; trailing dots/spaces in a component; Windows reserved device basenames; and
exact or case-folded path collisions. Paths must be unique and confined to the bank
root. Reject duplicate manifest keys, symlinks, hardlinks, missing files, extra
unlisted files, and byte-count or digest mismatches.

### 4. Derive and seal the bank identity

Encode the manifest as UTF-8 JSON and canonicalize it with RFC 8785 JSON
Canonicalization Scheme (JCS). Reject duplicate keys while parsing, before
canonicalization. The schema must use integers for counts and byte sizes and must
not admit non-finite numbers. Canonicalize the manifest without a self-referential
ID field, then derive a domain-separated identifier:

```text
bank_id = sha256("lean-usage-certificate-bank-v1\0" || canonical_manifest_bytes)
```

Encode the resulting digest as lowercase hex.

Store artifacts under that identity in immutable or content-addressed storage, or
create a reproducible archive whose digest is recorded separately. A reproducible
archive must normalize member ordering and paths, timestamps, ownership, modes, and
compression metadata. Verify its expected digest before extraction and verify the
bank manifest again afterward.

Record the expected bank ID in a trusted repository commit or authenticated
attestation outside the artifact store. A manifest and ID retrieved from the same
untrusted location do not authenticate each other. Publish the manifest and bank
atomically: consumers must never observe a new manifest paired with old or partial
files. Filesystem permissions are defense in depth, not the identity mechanism.

Any change to canonical bound input, artifact, command, tool, coverage, or manifest
content creates a new bank identity. Whitespace and object-key order are normalized
by JCS; reject or canonicalize alternate representations at ingress. Do not patch a
frozen bank in place or reuse its ID.

### 5. Verify only the frozen copy

Run checking and Lean generation from the frozen/content-addressed bank, not by
regenerating from the current working tree. For SAT banks, apply the DRAT/LRAT and
RUP requirements in [generated-proofs.md](generated-proofs.md#bank-large-sat-certificates).
Rederive the expected identifier sets from the frozen source/config plus any
declared upstream certificate inventory, and compare them exactly with the observed
instance, certificate, shard, and window IDs. Check the upstream-derived order
wherever replay order matters, and fail on missing, duplicate, reordered, or
unexpected work.

Record the verifier commands, executable/image digests, exit status, observed
coverage, logs, and output digests in a versioned evidence manifest that names the
bank ID. Encode it as UTF-8 JSON, reject duplicate keys, and apply RFC 8785 JCS
without a self-referential `evidence_id` field. Derive its lowercase-hex identity as:

```text
evidence_id = sha256("lean-usage-certificate-evidence-v1\0" || canonical_evidence_bytes)
```

Bank IDs, evidence IDs, and publication-record IDs are typed and must not substitute
for one another. A solver success or `s VERIFIED` establishes only the encoded claim
until the semantic bridge reaches the named final consumer.

### 6. Recapture before handoff

After replay and any generated-Lean build, recalculate the frozen input inventory
and digests from storage. Require an exact match with the pre-replay freeze, then
seal the separate evidence bundle. A changed input, generated artifact, manifest,
or aggregate source declared in the input-bank manifest invalidates the result and
requires a new bank identity and fresh verification. Generated outputs not declared
in that manifest receive output digests in the evidence bundle instead.

Before a promotion claim, separately apply the
[Lean-ingress publication gate](proof-discipline.md#lean-ingress-publication-gate):
check declaration existence, named-consumer reachability, the semantic bridge,
transitive trust closure, and publication integrity. Freeze evidence is an input to
that gate, not a substitute for it.

## Agent handoff checklist

Report the following explicitly:

- bank name, schema version, bank ID, and storage or archive identity;
- trusted commit/attestation that supplies the expected bank ID;
- pinned source closure, dependency, tool/image digest, command, seed, and
  environment identities;
- empirical repeatability result and the clean environments tested;
- manifest file counts, roles, byte totals, expected identifier sets, coverage
  digests, and digest algorithm;
- pre- and post-replay manifest comparison;
- evidence ID, verifier/replay result, and whether coverage was exhaustive;
- generated Lean aggregate and named final consumer, when applicable;
- semantic-bridge and final-consumer trust-audit status;
- independent promotion verifier identity/session, source revision, commands and
  artifacts checked, result, and authorized publication-gate result;
- any missing field or failed check.

If any required field, file, or check is missing, label the bank `UNFROZEN` or the
verification `INCOMPLETE` as applicable. It may remain diagnostic evidence, but do
not describe it as reproducible, verified, promoted, or publishable.
If promotion was checked only by the author, report
`candidate verified by author only — NOT PROMOTED`.

## Mutation tests

Automate fail-closed tests where the bank is part of a durable pipeline. At minimum,
the relevant freeze verifier, evidence verifier, or publication gate must reject
mutations to:

- one input or certificate byte;
- an artifact path, role, byte count, or digest;
- the generator command, tool/image digest, seed, or source/input-closure identity;
- the expected file count, expected identifier set, source-to-coverage rule, or
  coverage digest;
- ingress or aggregate source bytes;
- the Lean ingress declaration/path, including a same-byte replacement or path
  swap, aggregate import edge, or transitive import-closure digest;
- a typed parent link or certificate sign/parity branch used by publication.

Every field bound by the freeze, evidence, or publication schema must affect its
own domain-separated self-hash, and record types must not accept one another's IDs.

Also test missing and extra files, path traversal, duplicate entries, symlink and
hardlink substitution, truncated archives, stale manifests, and mutation after
replay. These tests show that custody failures are detected; they do not by
themselves verify certificate semantics.
