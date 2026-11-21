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

## Evals

Every skill has an eval suite for `claude plugin eval`, in
`plugins/<plugin>/evals/<skill>/`. Each case is a `case.yaml` (prompt,
budget, graders) plus a `scaffold.sh` that builds a fixture in the case's
empty sandbox: a todo-app repo with `main`, `dev`, a local bare `origin`,
and whatever the case needs (`ROADMAP.md`, `CHANGELOG.md`, merged branches,
a uv project, …). The shared helpers are in `evals/_lib/fixtures.sh`.

Each skill has a case for the main path, where it should fire, and a
near-miss prompt where it shouldn't. Graders check outcomes: file contents,
commands run or never run (no `--force`, no push to `main`/`dev`, no
unapproved `uv add`, …), and a judged rubric for the final report.

```bash
scripts/run-evals.sh kb-workflow                                # whole suite, 2 runs per case
scripts/run-evals.sh kb-workflow --tag sync-dev                 # one skill
scripts/run-evals-single.sh kb-workflow                         # smoke check: 1 run per case, all Haiku
scripts/run-evals-full.sh kb-workflow                           # full suite: 3 runs, with and without the plugin (uplift Δ)
```

`run-evals-single.sh` is the cheapest option (one Haiku run per case) and only shows
whether something is broken; one run is too noisy to trust the score.
`run-evals-full.sh` costs about 3× as much; use it before a release or
after larger skill changes.

The script passes `--scaffold` (runs the case scripts),
`--allow-tools Bash Edit Write`, `--model sonnet`, `--judge-model haiku`, `--runs 2`,
`--ablation none`, `--concurrency 4` and `--no-publish`; options you add go
through to `claude plugin eval` and override these. The first run asks you to trust the plugin
directory. Results go to `plugins/<plugin>/evals/results/` (gitignored).

- **git on macOS**: the cases run git inside the eval's sandbox, which
  can't use Apple's `/usr/bin/git` (a launcher for the Command Line Tools).
  Install git with Homebrew, or run the evals on Linux.
- **No GitHub**: the fixtures have no GitHub remote, so `gh pr create` and
  `gh api` fail. The `open-pr` and `prepare-release` cases check that this
  is reported honestly, without a made-up PR link.
- **Cost**: every case runs 3 times in each arm. Use `--tag`, `--case` or
  `--runs 1` while working on one skill.

### Pre-commit hook

[`.pre-commit-config.yaml`](.pre-commit-config.yaml) has three local hooks.
Install them with `prek install` (or `pre-commit install`):

- `plugin-validate` runs `claude plugin validate` on the marketplace and
  every plugin when anything under `.claude-plugin/` or `plugins/` changes.
- `plugin-version-bump`
  ([`scripts/check-version-bump.sh`](scripts/check-version-bump.sh)) fails
  when a commit changes a plugin's `skills/`, `agents/` or `hooks/` (deletions
  included) but its `plugin.json` version isn't one step above the version
  on `origin/main` (patch, minor or major: `0.1.0` → `0.1.1`, `0.2.0` or
  `1.0.0`). It compares with the merge-base of `HEAD` and `origin/main`, so a
  branch needs one bump per plugin, not one per commit. Set
  `KB_VERSION_BASE=HEAD` to compare with the last commit instead. New plugins
  are skipped.
- `plugin-evals` ([`scripts/eval-changed.sh`](scripts/eval-changed.sh))
  runs the evals of each staged skill or agent: a change in
  `skills/<name>/`, `agents/<name>.md` or `evals/<name>/` runs
  `--tag <name>`, and a change in `hooks/`, `evals/_lib/` or
  `.claude-plugin/` runs the plugin's whole suite. A changed skill or
  agent without an eval suite gets a warning.

To keep commits fast, the hook runs 1 run per case, without the baseline
arm, 4 at a time, keeps the report local, and fails if a case scores below
0.8. Change this with `KB_EVALS_RUNS`, `KB_EVALS_ABLATION`,
`KB_EVALS_CONCURRENCY` and `KB_EVALS_THRESHOLD`. See what it would run with
`KB_EVALS_DRY_RUN=1`. Skip it for one commit with
`SKIP=plugin-evals git commit …`. Like the evals, the hook needs git from
Homebrew on macOS.

## License

[MIT](LICENSE)
