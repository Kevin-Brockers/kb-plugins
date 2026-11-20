. "$(dirname "$0")/../../_lib/fixtures.sh"
init_repo
pyproject_version 0.1.1.dev0
# Nothing has been recorded since 0.1.0.
python3 - <<'PY'
from pathlib import Path

p = Path("CHANGELOG.md")
p.write_text(p.read_text().replace(
    "### Added\n\n- [#3](https://github.com/acme/todo/pull/3) - Store todos in a JSON file\n\n",
    "",
))
PY
commit "Add pyproject.toml" pyproject.toml AGENTS.md CHANGELOG.md
git push -q origin dev
