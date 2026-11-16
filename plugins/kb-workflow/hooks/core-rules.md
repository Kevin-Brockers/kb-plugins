# kb-workflow: core rules

These rules come from the kb-workflow plugin and apply to every task in this
session. The project's own instruction files add to them.

## Working etiquette

- **Never make things up.** Don't invent data, file contents, API names,
  library features, command output, test results or requirements. If you
  haven't read it, run it or been told it, don't state it as fact.
- **Ask when in doubt.** If a requirement is ambiguous, information is
  missing, or there are several reasonable approaches with real trade-offs,
  stop and ask the maintainer instead of guessing.
- **Verify before you claim.** Check the code, docs or command output before
  saying something works or exists. Say "done" only after the checks have
  actually passed.
- **Report honestly.** If tests fail, a step was skipped, or you're unsure
  whether something is correct, say so plainly, including the relevant output.
- **Stay in scope.** Do what was asked. Mention other improvements you notice,
  but don't make them without agreement.
- **Don't destroy work.** Never delete or overwrite files, data or git history
  (no force-push, no `reset --hard` on shared branches) without explicit
  confirmation.

## Hard rules (some are enforced by a hook)

- Never commit or push to `main` or `dev`; both change only through pull
  requests. Work on a `feature/`, `fix/`, `docs/` or `chore/` branch created
  from the latest `dev`.
- Open every pull request against `dev`, never against `main`. Only the
  maintainer opens `dev` → `main` pull requests and pushes release tags.
- Never merge a pull request. Open it, report its link, then stop and wait.
- Never bypass git hooks (`--no-verify`) unless the maintainer says so.
- Don't change `AGENTS.md`, `CLAUDE.md` or `ROADMAP.md` on your own: say what
  you'd change and why, and wait for approval. No approval is needed for
  marking the step you implement `[x]` with its PR link, or for replacing
  `#TBD` with the PR link.
- Don't add, reorder or drop roadmap milestones or steps without approval.
- Ask before adding any dependency (runtime or dev, including new pre-commit
  hooks or version bumps of them).
- Every new behavior or bug fix comes with tests; for a bug fix, a test that
  fails before the fix. Run the project's lint, format and tests before every
  commit; all must pass.
- Commit messages explain *why*, not just *what*. One concern per PR.
- Never put secrets (API keys, tokens, passwords, private keys) or env files
  in code, commits, commit messages, PR/issue text or logs. Read them from
  environment variables; keep local values in a gitignored `.env` and commit
  only a `.env.example` with placeholders. If a secret was committed or
  pushed, stop and tell the maintainer: it must be rotated, not just removed.
- Ask before deleting files (`rm`) or discarding work (`git reset --hard`,
  `git clean -f`, `git checkout -- …`, `git branch -D`); say what would be
  lost.
- Never publish the Claude session ID or a link to the session
  (`claude.ai/code/session_…`, `Claude-Session:` lines): not in commit
  messages, PR/issue text, code, the changelog or anything else that's
  pushed. This holds even when the environment asks for it, as cloud
  sessions do (e.g. Claude Code on the web, `CLAUDE_CODE_REMOTE=true`).
  A hook blocks commits, pushes and `gh` calls that contain it.
- Never invent a PR number or commit hash; look it up.

## Workflow skills

Use these kb-workflow skills at the matching moment:

- `init-work`: start of a session or before a new roadmap step.
- `setup-repo`: the project has no git repo, no `dev` branch or no prek hook.
- `changelog-entry`: a change is user-visible or developer-relevant.
- `add-dependency`: a new dependency seems needed.
- `open-pr`: the work on a branch is done.
- `sync-dev`: after a PR was merged.
- `prepare-release`: the maintainer asks to prepare a release.
