# Dependency pinning and vendoring

Lake resolves `[[require]]` entries and records concrete resolutions in
`lake-manifest.json`. Commit the manifest; regenerate it with Lake rather than
editing it by hand.

## Revisions

```toml
[[require]]
name = "mathlib"
scope = "leanprover-community"
rev = "v4.29.0"
```

- A full commit SHA identifies immutable content.
- A release tag is conventional and often required for prebuilt mathlib cache
  availability, but Git tags are technically movable. Review the resolved commit
  in `lake-manifest.json` and unexpected manifest changes.
- A branch such as `master` intentionally floats and is unsuitable for a
  reproducible release unless the committed manifest and update policy make that
  choice explicit.

Cache availability is artifact- and commit-dependent, not tag-dependent. Releases
usually have broad coverage, but an arbitrary commit can also hit when matching
artifacts were uploaded. Confirm the exact cache result rather than inferring it
from how `rev` is spelled.

## Match `lean-toolchain`

Update the Lean toolchain and mathlib revision together. A mismatched toolchain can
invalidate downloaded oleans and force source elaboration or fail to load them.
Confirm the compatibility declared by the chosen mathlib release; do not infer it
only from similar version numbers.

## Local path dependencies

Use a path requirement for deliberate sibling co-development:

```toml
[[require]]
name = "foo"
path = "../foo"
```

This picks up sibling edits without a network round trip, but CI and other clones
must have the same layout. Replace it with a reproducible remote/revision before
shipping unless the monorepo layout is part of the contract.

## Third-party Git dependencies

```toml
[[require]]
name = "foo"
git = "https://github.com/owner/repo"
rev = "<full-commit-sha-or-reviewed-release-tag>"
```

Reservoir `scope` applies to indexed packages; omit it for a direct Git URL unless
the current Lake schema explicitly requires otherwise.

## Mirrors and air-gapped hosts

Lake invokes Git and therefore honors Git URL rewrites:

```bash
git config --global \
  url."https://internal-mirror/leanprover-community/mathlib4".insteadOf \
  "https://github.com/leanprover-community/mathlib4"
```

Keep the lakefile's logical upstream unchanged and document the host-level mirror.

## Disk use

Each project has its own `.lake/packages` tree. Even identical mathlib revisions
can consume several gigabytes per project. Use `lake exe cache get` for supported
mathlib oleans; use the audited project-artifact approach in
[generated-proofs.md](generated-proofs.md) for expensive project-owned modules.
