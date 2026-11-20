. "$(dirname "$0")/../../_lib/fixtures.sh"
init_repo
pyproject_version 0.2.0
# 0.2.0 was released: its section exists and [Unreleased] is empty.
python3 - <<'PY'
from pathlib import Path

p = Path("CHANGELOG.md")
p.write_text(p.read_text().replace(
    "## [Unreleased]\n\n",
    "## [Unreleased]\n\n## [0.2.0] - 2026-11-17\n\n",
))
PY
commit "Release 0.2.0" pyproject.toml AGENTS.md CHANGELOG.md
git push -q origin dev
git switch -q main
git merge -q --ff-only dev
git tag v0.2.0
git push -q origin main v0.2.0
git switch -q dev
