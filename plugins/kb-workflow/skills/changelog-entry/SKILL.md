---
name: changelog-entry
description: Add an entry to CHANGELOG.md under [Unreleased] in Keep a Changelog format, with #TBD until the pull request exists. Use for every user-visible or developer-relevant change, before opening the PR.
---

# changelog-entry

`CHANGELOG.md` follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).

1. **Find the section.** Open `CHANGELOG.md` and find `## [Unreleased]`. If
   the file or the section doesn't exist, ask the maintainer before creating
   it.
2. **Pick the category** under `[Unreleased]`: `Added`, `Changed`,
   `Deprecated`, `Removed`, `Fixed` or `Security`. Create the `### <Category>`
   heading if it's missing, keeping that order.
3. **Write one entry per change**, short and from the reader's point of view:
   - Before the PR exists: `- #TBD - Add due dates`
   - After it exists (the `open-pr` skill does this):
     `- [#12](https://github.com/<owner>/<repo>/pull/12) - Add due dates`.
     PR numbers stay valid after squash or rebase merges; branch commit
     hashes don't.
   - Only for a change that reached `dev` or `main` without a PR (like the
     initial commit), link the short hash to the full commit:
     `- [7982e5c](https://github.com/<owner>/<repo>/commit/<full-hash>) - Initial commit`.
4. **Get the repository URL** with `gh repo view --json url --jq .url`, and
   PR numbers or hashes from `gh pr view` or `git log`. Never invent them.

Release preparation (renaming `[Unreleased]` to a version) and version bumps
get no entry of their own; see the `prepare-release` skill.
