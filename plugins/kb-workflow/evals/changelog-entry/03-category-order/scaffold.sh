. "$(dirname "$0")/../../_lib/fixtures.sh"
init_repo
# [Unreleased] already has Added and Fixed sections.
python3 - <<'PY'
from pathlib import Path

p = Path("CHANGELOG.md")
p.write_text(p.read_text().replace(
    "- [#3](https://github.com/acme/todo/pull/3) - Store todos in a JSON file\n",
    "- [#3](https://github.com/acme/todo/pull/3) - Store todos in a JSON file\n\n"
    "### Fixed\n\n"
    "- [#4](https://github.com/acme/todo/pull/4) - Don't crash when todos.json is empty\n",
))
PY
commit "Update changelog" CHANGELOG.md
git push -q origin dev
branch_from_dev chore/drop_csv_export
echo "# The CSV export (todo.py export --csv) was removed." >> todo.py
commit "Remove the CSV export" todo.py
