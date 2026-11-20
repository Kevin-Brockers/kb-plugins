. "$(dirname "$0")/../../_lib/fixtures.sh"
init_repo
# M1.2 is listed first but depends on M1.3, which is still open.
python3 - <<'PY'
from pathlib import Path

p = Path("ROADMAP.md")
s = p.read_text()
s = s.replace("feature/due_dates; depends on: M1.1)", "feature/due_dates; depends on: M1.3)")
s = s.replace("feature/overdue_list; depends on: M1.2)", "feature/overdue_list; depends on: M1.1)")
p.write_text(s)
PY
commit "Reorder roadmap dependencies" ROADMAP.md
git push -q origin dev
