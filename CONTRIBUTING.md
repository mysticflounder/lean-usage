# Contributing

Contributions from people using AI tools are welcome. Review is based on the
quality, safety, provenance, and maintainability of the contribution, not on
whether an AI system helped produce it.

## Before you submit

- Keep changes focused and explain the problem they solve.
- Read the repository's `AGENTS.md` and follow the conventions relevant to the
  files you touch.
- Run `scripts/test.sh` and report the result. If a check cannot run or fails
  for an unrelated reason, say so plainly and include the diagnostic.
- Add or update tests when behavior changes.
- When hooks, scripts, or skills change, bump the version in both
  `plugins/lean-usage/.claude-plugin/plugin.json` and
  `plugins/lean-usage/.codex-plugin/plugin.json`, keeping them equal.

## AI-assisted contributions

AI tools may be used for any part of a contribution, including exploration,
implementation, tests, documentation, and review. The human contributor must:

- review and understand the submitted change;
- be able to explain and maintain it;
- verify claims, links, generated artifacts, and test results rather than
  treating model output as evidence;
- disclose substantial AI assistance in the pull-request description, with a
  short summary of what the tools did and what was independently checked; and
- avoid listing an AI system as an author, co-author, reviewer, or signatory.

Prompt transcripts and token-level attribution are not required. A useful
disclosure is brief, for example: "AI-assisted implementation and test review;
I reviewed the diff and ran `scripts/test.sh`."

Bulk generated changes are welcome only when the generation process is
reproducible, the output has been reviewed, and the pull request is still small
enough to evaluate responsibly. Maintainers may ask for the generator, inputs,
or a smaller split.

## Licensing and provenance

This repository is licensed under GPL-3.0-or-later. By submitting a
contribution, you agree that it may be distributed under that license and
confirm that you have the right to submit it.

Do not assume AI-generated material is free of third-party obligations. Cite
sources used to derive code or documentation, preserve required notices, and
do not submit copied material whose license is unknown or incompatible. Shell
and Python sources must use the copyright, GPL-3.0-or-later, author, purpose,
and `Usage:` header form described in `AGENTS.md`.

## Privacy and security

Do not put secrets, credentials, private prompts, proprietary source, personal
data, or confidential build logs into issues, commits, model inputs, or pull
requests. Report security-sensitive problems privately to the maintainer
instead of opening a public issue.

## Pull-request notes

Include:

- what changed and why;
- tests and other verification performed;
- known limitations or follow-up work;
- substantial AI assistance, if any; and
- third-party sources or generated artifacts introduced by the change.
