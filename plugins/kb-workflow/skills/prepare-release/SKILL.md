---
name: prepare-release
description: Prepare a release through a pull request into dev - rename [Unreleased] in CHANGELOG.md to the version and date and set the version - and afterwards set the next development version. Use only when the maintainer asks to prepare or cut a release.
---

# prepare-release

A release is prepared in a pull request into `dev`, like any other change.
Only the maintainer opens the `dev` → `main` pull request and pushes the
release tag.

## Release PR

1. **Confirm** the version (e.g. `0.1.0`) and the planned release date with
   the maintainer. Don't pick them yourself.
2. **Branch** `chore/release_<version>` from the latest `dev` (as in
   `init-work`).
3. **Check `[Unreleased]`** in `CHANGELOG.md` has entries. If it's empty,
   stop and ask; a release needs a changelog section with entries.
4. **Rename** `## [Unreleased]` to `## [<version>] - <YYYY-MM-DD>` and add a
   new, empty `## [Unreleased]` above it.
5. **Set the version** where the project declares it. For Python projects the
   kb-python rules say how; otherwise follow the project's `AGENTS.md`/
   `CLAUDE.md`, and ask if it isn't documented.
6. **Open the PR** with the `open-pr` skill. The rename and the version get
   no changelog entry of their own.
7. **Tell the maintainer**: from this PR's merge until the release is tagged,
   no other pull request may merge into `dev`. If the date slips, a pull
   request into `dev` corrects it first. The `dev` → `main` PR must carry the
   version and changelog section to `main` unchanged; the release workflow
   (if the project has one) stops on a tag whose version or changelog section
   isn't on `main`.

## After the tag

When the maintainer says the release is tagged:

1. Branch `chore/next_dev_version` from the latest `dev`.
2. Set the next development version (e.g. `0.2.0.dev0` after `0.1.0`; confirm
   the number with the maintainer).
3. Open the PR with `open-pr`, without a changelog entry.
