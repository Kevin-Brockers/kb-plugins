---
name: init-work
description: Load the project's roadmap before starting work, summarize the next open step and, once the maintainer confirms it, create its branch from the latest dev. Use at the start of a session or before picking up a new task or roadmap step.
---

# init-work

Get up to speed on what comes next in this project. The general working
rules come from the kb-workflow plugin itself; this skill only reads the
plan.

1. **Read `ROADMAP.md`** at the repository root in full, using the Read tool.
   It holds the milestones and steps, which are done and which are open, and
   the format rules at its top. If it doesn't exist, say so and offer to help
   the maintainer write one; don't make one up.
2. **Summarize** for the maintainer:
   - the first open step whose dependencies are done, with its ID,
     description and branch name, as given in `ROADMAP.md`;
   - anything in the roadmap that looks inconsistent or unclear.
3. **Wait.** Don't start implementing. The maintainer may pick that step or
   ask for something else.
4. **Create the branch** once the maintainer has confirmed what to work on:
   - Check `git status --porcelain`; if anything is uncommitted, stop and
     report it.
   - `git fetch origin dev`, then `git switch -c <branch> origin/dev`.
   - Name it `<type>/<topic>` with type `feature`, `fix`, `docs` or `chore`
     (e.g. `feature/due_dates`), using the roadmap's branch name if it gives
     one.
   - If there's no `dev` branch, or the folder isn't a git repo, use the
     `setup-repo` skill first.

Only report what the roadmap actually says. If a step is too big for one PR,
suggest splitting it into sub-steps (`M1.2a`, `M1.2b`, …) and wait for the
maintainer to agree; don't edit `ROADMAP.md` on your own.
