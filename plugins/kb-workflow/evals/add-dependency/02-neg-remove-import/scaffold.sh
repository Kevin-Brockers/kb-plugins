. "$(dirname "$0")/../../_lib/fixtures.sh"
init_repo
pyproject_version 0.2.0.dev0
commit "Add pyproject.toml" pyproject.toml AGENTS.md
git push -q origin dev
python3 -c 'from pathlib import Path; p = Path("todo.py"); p.write_text(p.read_text().replace("import json\n", "import json\nimport os\n"))'
commit "Prepare todo.py" todo.py
branch_from_dev chore/cleanup
