. "$(dirname "$0")/../../_lib/fixtures.sh"
init_repo
pyproject_version 0.2.0.dev0
commit "Add pyproject.toml" pyproject.toml AGENTS.md
git push -q origin dev
branch_from_dev feature/import_url
