---
name: setup-repo
description: Set up a project for the kb workflow - git repo with an initial commit on main, a dev branch, a prek pre-commit hook that blocks commits to main and dev, a .gitignore that keeps secrets out, and a CHANGELOG.md. Use when the folder is not a git repo, has no dev branch, or the prek hook isn't installed.
---

# setup-repo

Check each part and only do what's missing. Ask before anything that adds a
dependency or reaches outside this machine (creating a GitHub repository).

1. **Git repo.** If `git rev-parse --is-inside-work-tree` fails, run
   `git init -b main`.
2. **Initial commit.** If there's no commit yet (`git rev-parse --verify HEAD`
   fails), ask the maintainer which files belong in it, then commit them on
   `main` (`Initial commit`). This is the only commit ever made directly on
   `main`. Do it before installing the prek hook, which would block it.
3. **`dev` branch.** If `git rev-parse --verify dev` fails, create it from
   `main` with `git branch dev`.
4. **Pre-commit config.** If `.pre-commit-config.yaml` is missing, propose one
   to the maintainer (it counts as adding dependencies, so ask first) with
   hooks from `https://github.com/pre-commit/pre-commit-hooks`:
   `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-toml`,
   `check-merge-conflict`, `check-added-large-files`, `detect-private-key`,
   and `no-commit-to-branch` with `args: [--branch, main, --branch, dev]`.
   Use the latest tag as `rev`
   (`gh api repos/pre-commit/pre-commit-hooks/releases/latest --jq .tag_name`);
   don't write a version from memory. Language plugins add their own hooks
   (e.g. kb-python: ruff). It goes in through a `chore/` branch and the
   `open-pr` skill, like any other change.
5. **prek.** Check `prek --version`. If it's missing, tell the maintainer and
   ask how they want to install it; don't install it yourself. Then run
   `prek install` and `prek run --all-files`. If a hook changes files, show
   the changes.
6. **Secrets.** Make sure `.gitignore` covers local secrets: `.env`,
   `.env.*` with `!.env.example`, `*.pem`, `*.key`. Add what's missing (ask
   first if the file already has content you didn't write). Offer, as an
   optional dependency, the `gitleaks` pre-commit hook from
   `https://github.com/gitleaks/gitleaks` (latest tag via `gh api`), which
   also catches secrets in commits the maintainer makes by hand.
7. **Changelog.** If `CHANGELOG.md` is missing, offer to create one with a
   Keep a Changelog header and an empty `## [Unreleased]` section.
8. **Remote.** If `git remote` is empty, ask whether to create a GitHub
   repository (`gh repo create`) and whether it's public or private. Pushing
   `main` and `dev` is blocked for agents, so ask the maintainer to run
   `git push -u origin main dev` themselves. Remind them to check that
   secret scanning push protection is on (repository Settings → Code
   security), so GitHub itself rejects pushes that contain known secrets.
9. **Summarize** what was already in place, what you set up, and what the
   maintainer still needs to do.
