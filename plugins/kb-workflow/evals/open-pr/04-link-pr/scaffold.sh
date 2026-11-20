. "$(dirname "$0")/../../_lib/fixtures.sh"
init_repo
# An earlier change on dev still has #TBD (not this branch's business).
python3 - <<'PY'
from pathlib import Path

p = Path("CHANGELOG.md")
p.write_text(p.read_text().replace(
    "- [#3](https://github.com/acme/todo/pull/3) - Store todos in a JSON file\n",
    "- [#3](https://github.com/acme/todo/pull/3) - Store todos in a JSON file\n"
    "- #TBD - Export todos as Markdown\n",
))
PY
commit "Add changelog entry for the Markdown export" CHANGELOG.md
git push -q origin dev

# The branch is committed and pushed, with #TBD in the changelog and roadmap.
branch_from_dev feature/due_dates
add_due_dates
python3 - <<'PY'
from pathlib import Path

p = Path("CHANGELOG.md")
p.write_text(p.read_text().replace(
    "- #TBD - Export todos as Markdown\n",
    "- #TBD - Export todos as Markdown\n- #TBD - Add optional due dates to todos\n",
))
p = Path("ROADMAP.md")
p.write_text(p.read_text().replace(
    "- [ ] M1.2 Add optional due dates to todos (branch: feature/due_dates; depends on: M1.1)",
    "- [x] M1.2 Add optional due dates to todos (branch: feature/due_dates; depends on: M1.1) #TBD",
))
PY
commit "Add optional due dates to todos" todo.py CHANGELOG.md ROADMAP.md
git push -q -u origin feature/due_dates
