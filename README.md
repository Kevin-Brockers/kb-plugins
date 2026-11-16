# kb-plugins

My personal Claude Code plugin marketplace (`kb-plugins`).

## Plugins

### [`kb-workflow`](plugins/kb-workflow)

My shared working rules and the git/GitHub workflow around a `ROADMAP.md`.

- **Core rules**: a `SessionStart` hook adds
  [`core-rules.md`](plugins/kb-workflow/hooks/core-rules.md) (working
  etiquette and hard rules) to every session.
- **Guard**: a `PreToolUse` hook ([`guard.py`](plugins/kb-workflow/hooks/guard.py),
  checks in [`guard_lib/`](plugins/kb-workflow/hooks/guard_lib)) on every
  Bash command and file edit. It looks inside `bash -c`, `eval` and `xargs`.
  - *Workflow*: blocks pushes and commits to `main`/`dev` (except a new
    repo's first commit), force pushes, `--no-verify`, `gh pr merge`, and
    `gh pr create` without `--base` or against `main`. Asks before edits to
    `AGENTS.md`, `CLAUDE.md` or `ROADMAP.md` and before deleting remote
    branches.
  - *Destructive commands*: blocks `rm -r` on `/`, home, the project, its
    parents, `*` or `.git`, plus `dd of=/dev/…`, `mkfs`, `diskutil erase…`
    and `gh repo delete`. Allows `rm -r` on `build`, `dist` and
    `node_modules` folders inside the project. Asks before any other `rm`,
    `find -delete`, `sudo`, recursive `chmod`/`chown`, `curl … | sh`, and git
    commands that discard work (`reset --hard`, `clean -f`, `branch -D`,
    `checkout --`, `restore`, `stash drop`).
  - *Secrets*: on `git commit` (including a `git add` in the same command)
    it blocks env/key files (`.env`, `*.pem`, `id_rsa`, … but not
    `.env.example`) and known token formats (AWS, GitHub, Anthropic, OpenAI,
    Slack, Google, Stripe, private keys). It asks on generic
    `password = "…"` values and URLs with passwords. The same scan covers
    the commit message (including `-F` files) and `gh pr/issue/release/api`
    text (including `--body-file` files); `gh gist create` always asks.
    Writing a known token into a source file asks first. A line containing `allow-secret` is
    skipped, for test fixtures.
  - *Session ID*: blocks commits, tags, pushes and `gh` text that contain
    the Claude session ID, a `claude.ai/code/session_…` link or a
    `Claude-Session:` line, which cloud sessions ask agents to add. It checks
    commit messages (including `-F` files and heredocs), staged content, the
    commits about to be pushed, and `--body-file` files.

  The guard is a safety net, not a sandbox: a script Claude writes and runs
  can still do anything the shell can. Pair it with gitleaks in pre-commit
  and GitHub push protection (`setup-repo` offers both).
- **Skills**: Claude uses them when the task fits; you can also call one
  directly with the plugin name in front, e.g. `/kb-workflow:init-work`.

  | Skill | Use it |
  | --- | --- |
  | `init-work` | at the start of a session: reads `ROADMAP.md`, summarizes the next open step, creates its branch from `dev` |
  | `setup-repo` | for a new project: git repo, initial commit, `dev` branch, prek hook, `.gitignore` for secrets, changelog; offers gitleaks and GitHub push protection |
  | `changelog-entry` | for every user-visible or developer-relevant change |
  | `add-dependency` | before adding a dependency or pre-commit hook |
  | `open-pr` | when a branch is done: checks, commit, push, PR against `dev`, `#TBD` → PR link, stop |
  | `sync-dev` | after a PR was merged: fast-forwards `dev`, deletes merged local branches |
  | `prepare-release` | when cutting a release: changelog and version PR, then the next dev version |

The guard hook needs Python 3.9 or newer as `python3` on the `PATH`.

### [`kb-python`](plugins/kb-python)

Python conventions (uv, ruff, pytest, CI, releases). A `SessionStart` hook
adds [`python-rules.md`](plugins/kb-python/hooks/python-rules.md) only in
projects with a `pyproject.toml`. The `check` skill runs ruff lint, ruff
format and pytest (`/kb-python:check`).

Project-specific facts (tech stack, commands, approved dependencies) belong
in each project's own `AGENTS.md` or `CLAUDE.md`.

## Installation

```bash
# from GitHub
claude plugin marketplace add Kevin-Brockers/kb-plugins
# or from a local clone
claude plugin marketplace add /path/to/kb-plugins

claude plugin install kb-workflow@kb-plugins
claude plugin install kb-python@kb-plugins
```

Pull updates with `claude plugin marketplace update kb-plugins`.

## Adding a plugin

1. Create `plugins/<name>/.claude-plugin/plugin.json` with `name`,
   `description` and `version`.
2. Add skills as `plugins/<name>/skills/<skill>/SKILL.md` (frontmatter with
   `name` and `description`), agents as `plugins/<name>/agents/<agent>.md`,
   hooks in `plugins/<name>/hooks/hooks.json`.
3. Add an entry to `.claude-plugin/marketplace.json` with
   `"source": "./plugins/<name>"`.
4. Run `claude plugin validate .` and `claude plugin validate plugins/<name>`.

Bump a plugin's `version` when you change it, so installs pick up the update.

## License

[MIT](LICENSE)
