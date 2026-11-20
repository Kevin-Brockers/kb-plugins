# Shared fixtures for the kb-workflow eval cases.
#
# Each case's scaffold.sh sources this file. The eval runner (with --scaffold)
# starts that script with the case's empty workspace as the current directory
# and a sandbox HOME whose .gitconfig already sets a user name and email.

set -euo pipefail

# The todo app every fixture is built around, with an AGENTS.md that names
# the project's checks and a check.sh that stands in for lint, format and
# tests.
write_app() {
  cat > README.md <<'EOF'
# todo

A small command-line todo list.
EOF
  cat > AGENTS.md <<'EOF'
# todo

A small command-line todo list (`todo.py`).

## Commands

- Checks (lint, format and tests): `sh check.sh`. Run them before every
  commit; all must pass.
EOF
  cat > check.sh <<'EOF'
#!/bin/sh
# Stand-in for the project's lint, format and tests.
echo "lint: ok"
echo "format: ok"
echo "tests: 12 passed"
EOF
  cat > todo.py <<'EOF'
"""A small command-line todo list."""

import json
import sys
from pathlib import Path

STORE = Path("todos.json")


def load() -> list[dict]:
    if not STORE.exists():
        return []
    return json.loads(STORE.read_text())


def save(todos: list[dict]) -> None:
    STORE.write_text(json.dumps(todos, indent=2))


def main(argv: list[str]) -> None:
    todos = load()
    if argv[:1] == ["add"]:
        todos.append({"title": " ".join(argv[1:]), "done": False})
        save(todos)
    for i, todo in enumerate(todos, 1):
        print(f"{i}. [{'x' if todo['done'] else ' '}] {todo['title']}")


if __name__ == "__main__":
    main(sys.argv[1:])
EOF
}

# Make check.sh fail with a test failure.
failing_checks() {
  cat > check.sh <<'EOF'
#!/bin/sh
# Stand-in for the project's lint, format and tests.
echo "lint: ok"
echo "format: ok"
echo "tests: 11 passed, 1 failed"
echo "FAILED tests/test_todo.py::test_due_date_is_optional - KeyError: 'due'"
exit 1
EOF
}

write_roadmap() {
  cat > ROADMAP.md <<'EOF'
# Roadmap

Format: each step is `- [ ] <ID> <description> (branch: <branch>; depends
on: <IDs>)`. When a step is done it is marked `[x]` and gets its pull
request link at the end; until the pull request exists the link is `#TBD`.

## M1 - Basic todo list

- [x] M1.1 Store todos in a JSON file (branch: feature/json_store) [#3](https://github.com/acme/todo/pull/3)
- [ ] M1.2 Add optional due dates to todos (branch: feature/due_dates; depends on: M1.1)
- [ ] M1.3 List overdue todos (branch: feature/overdue_list; depends on: M1.2)

## M2 - Sharing

- [ ] M2.1 Export todos as Markdown (branch: feature/markdown_export; depends on: M1.1)
EOF
}

write_changelog() {
  cat > CHANGELOG.md <<'EOF'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- [#3](https://github.com/acme/todo/pull/3) - Store todos in a JSON file

## [0.1.0] - 2026-10-01

### Added

- [7982e5c](https://github.com/acme/todo/commit/7982e5c4b1d2a3f4e5d6c7b8a9f0e1d2c3b4a5f6) - Initial commit
EOF
}

# Initial commit on main, a dev branch, and both pushed to a bare "origin".
# The bare repo lives inside .git, so it never shows up in git status.
init_repo() {
  git init -q -b main
  write_app
  [ "${1:-}" = "--no-plans" ] || { write_roadmap; write_changelog; }
  git add -A
  git commit -q -m "Initial commit"
  git branch dev
  git init -q --bare .git/origin.git
  git remote add origin "$PWD/.git/origin.git"
  git push -q origin main dev
  git branch -q --set-upstream-to=origin/main main
  git branch -q --set-upstream-to=origin/dev dev
  git switch -q dev
}

# commit <message> <file>...: stage the given files and commit them.
commit() {
  local message="$1"
  shift
  git add -- "$@"
  git commit -q -m "$message"
}

# Start a branch from dev (not pushed).
branch_from_dev() {
  git switch -q -c "$1" dev
}

# Add due dates to todo.py (the change most fixtures pretend to have made).
add_due_dates() {
  python3 - <<'EOF'
from pathlib import Path

p = Path("todo.py")
s = p.read_text()
s = s.replace(
    '        todos.append({"title": " ".join(argv[1:]), "done": False})',
    '        due = None\n'
    '        if "--due" in argv:\n'
    '            i = argv.index("--due")\n'
    '            due = argv[i + 1]\n'
    '            argv = argv[:i] + argv[i + 2 :]\n'
    '        todos.append({"title": " ".join(argv[1:]), "done": False, "due": due})',
)
s = s.replace(
    "        print(f\"{i}. [{'x' if todo['done'] else ' '}] {todo['title']}\")",
    "        due = f\" (due {todo['due']})\" if todo.get(\"due\") else \"\"\n"
    "        print(f\"{i}. [{'x' if todo['done'] else ' '}] {todo['title']}{due}\")",
)
p.write_text(s)
EOF
}

# Make the todo app a Python project with a version in pyproject.toml.
# pyproject_version <version>
pyproject_version() {
  cat > pyproject.toml <<TOML
[project]
name = "todo"
version = "$1"
description = "A small command-line todo list"
requires-python = ">=3.9"
dependencies = []

[dependency-groups]
dev = ["pytest>=8"]
TOML
  echo '- The version is the `version` field in `pyproject.toml`.' >> AGENTS.md
}

# State after pull requests were merged on GitHub (origin):
#   feature/json_store  merged with a merge commit, deleted on origin
#   feature/priorities  squash-merged, deleted on origin (its own commit is
#                       not in dev, so `git branch -d` refuses it)
#   feature/empty       created from dev, no commits of its own
#   feature/wip         two unmerged commits, still on origin
# Local dev and origin/dev still point at the old dev, so a fetch is needed.
merged_branches() {
  local old
  old=$(git rev-parse dev)

  branch_from_dev feature/json_store
  echo 'STORE_VERSION = 1' >> todo.py
  commit "Version the JSON store" todo.py
  git push -q -u origin feature/json_store

  branch_from_dev feature/priorities
  echo 'Todos have a priority: low, normal or high.' >> README.md
  commit "Add priorities" README.md
  git push -q -u origin feature/priorities

  branch_from_dev feature/empty

  branch_from_dev feature/wip
  echo '# TODO: tags' >> todo.py
  commit "Sketch tags" todo.py
  echo '# TODO: filter by tag' >> todo.py
  commit "Sketch tag filter" todo.py
  git push -q -u origin feature/wip

  # GitHub merges both pull requests into dev and deletes their branches.
  git switch -q --detach dev
  git merge -q --no-ff feature/json_store -m "Merge pull request #4 from acme/feature/json_store"
  git merge -q --squash feature/priorities
  git commit -q -m "Add priorities (#5)"
  git push -q origin HEAD:dev
  git push -q origin --delete feature/json_store feature/priorities
  git update-ref refs/remotes/origin/dev "$old"
  git switch -q dev
}
