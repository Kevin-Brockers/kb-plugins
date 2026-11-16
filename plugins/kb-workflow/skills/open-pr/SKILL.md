---
name: open-pr
description: Finish a branch - run the checks, commit, push, open a pull request against dev, replace #TBD in CHANGELOG.md and ROADMAP.md with the PR link, then stop and report. Use when the work on a feature/fix/docs/chore branch is done.
---

# open-pr

Commit and push to the working branch without asking first; open the pull
request; then stop. Never merge it: only the maintainer merges.

1. **Check the branch.** `git symbolic-ref --short HEAD` must not be `main`
   or `dev`. If it is, stop and say so.
2. **Run the checks.** Run the project's lint, format and tests (for Python
   projects, the kb-python `check` skill; otherwise the commands in the
   project's `AGENTS.md`/`CLAUDE.md`). If anything fails, stop and report the
   output. Don't commit failing work.
3. **Update the records**, if not already done on this branch:
   - a changelog entry with `#TBD` (`changelog-entry` skill), if the change
     is user-visible or developer-relevant;
   - if the branch implements a roadmap step, mark it `[x]` in `ROADMAP.md`
     with `#TBD` as the link, following the format at the top of that file.
4. **Commit.** Stage the intended files only (check `git status`), and write a
   message that explains *why*. If a pre-commit hook changes files, review
   the changes, stage them and commit again. Never use `--no-verify`.
5. **Push.** `git push -u origin <branch>`. On a network error, retry up to 4
   times, waiting 2, 4, 8 and 16 seconds.
6. **Open the PR** with `gh pr create --base dev --title "<title>" --body "<body>"`.
   Always pass `--base dev`. The body says what changed and why, names the
   roadmap step ID (e.g. `M1.2`) if there is one, and lists the checks that
   passed. No agent session links.
7. **Link the PR.** Get its number and URL from the `gh pr create` output.
   Find the `#TBD` lines this branch added (`git diff origin/dev --
   CHANGELOG.md ROADMAP.md`) and replace each with `[#<n>](<pr-url>)`. Leave
   any other `#TBD` alone. Commit (`Link PR #<n> in changelog and roadmap`)
   and push.
8. **Stop.** Tell the maintainer the work is done, with the PR's link, and
   wait. Don't merge, don't start the next step.

If a command fails, say which one and include its output.
