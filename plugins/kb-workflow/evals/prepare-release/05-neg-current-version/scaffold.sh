. "$(dirname "$0")/../../_lib/fixtures.sh"
init_repo
pyproject_version 0.2.0.dev0
# dev has a second unreleased change.
python3 - <<'PY'
from pathlib import Path

p = Path("CHANGELOG.md")
p.write_text(p.read_text().replace(
    "- [#3](https://github.com/acme/todo/pull/3) - Store todos in a JSON file\n",
    "- [#3](https://github.com/acme/todo/pull/3) - Store todos in a JSON file\n"
    "- [#4](https://github.com/acme/todo/pull/4) - Add optional due dates to todos\n",
))
PY
commit "Add pyproject.toml" pyproject.toml AGENTS.md CHANGELOG.md
git push -q origin dev
