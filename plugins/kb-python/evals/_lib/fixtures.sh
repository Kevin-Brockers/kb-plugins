# Shared fixtures for the kb-python eval cases.
#
# Each case's scaffold.sh sources this file. The eval runner (with --scaffold)
# starts that script with the case's empty workspace as the current directory
# and a sandbox HOME whose .gitconfig already sets a user name and email.

set -euo pipefail

# A small uv project with ruff and pytest as dev dependencies, synced and
# committed. The scaffold runs outside the agent's sandbox, so this is where
# uv downloads the packages; the agent's `uv run` then works offline.
# python_project [dev dependencies...]
python_project() {
  local deps='"pytest>=8", "ruff>=0.6"'
  [ $# -eq 0 ] || deps="$*"
  git init -q -b main
  cat > pyproject.toml <<TOML
[project]
name = "calc"
version = "0.1.0"
description = "A tiny calculator"
requires-python = ">=3.9"
dependencies = []

[dependency-groups]
dev = [$deps]

[tool.pytest.ini_options]
pythonpath = ["."]
TOML
  cat > calc.py <<'PY'
"""A tiny calculator."""


def add(a: int, b: int) -> int:
    return a + b


def sub(a: int, b: int) -> int:
    return a - b
PY
  mkdir -p tests
  cat > tests/test_calc.py <<'PY'
from calc import add, sub


def test_add():
    assert add(2, 2) == 4


def test_sub():
    assert sub(3, 1) == 2
PY
  printf '.venv/\n__pycache__/\n.pytest_cache/\n.ruff_cache/\n' > .gitignore
  uv sync -q
  git add -A
  git commit -q -m "Initial commit"
}

# replace <file> <old> <new>: replace text in a file (fails if <old> is missing).
replace() {
  python3 - "$@" <<'PY'
import sys
from pathlib import Path

path, old, new = sys.argv[1:]
p = Path(path)
s = p.read_text()
if old not in s:
    sys.exit(f"{old!r} not in {path}")
p.write_text(s.replace(old, new))
PY
}
