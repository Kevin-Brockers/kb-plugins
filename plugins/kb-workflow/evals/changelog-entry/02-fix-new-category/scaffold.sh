. "$(dirname "$0")/../../_lib/fixtures.sh"
init_repo
branch_from_dev fix/empty_store
python3 - <<'PY'
from pathlib import Path

p = Path("todo.py")
p.write_text(p.read_text().replace(
    "    return json.loads(STORE.read_text())",
    "    text = STORE.read_text().strip()\n    return json.loads(text) if text else []",
))
PY
commit "Don't crash when todos.json is empty" todo.py
