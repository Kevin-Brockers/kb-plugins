. "$(dirname "$0")/../../_lib/fixtures.sh"
init_repo
merged_branches
git switch -q feature/wip
echo "# TODO: tag colors" >> todo.py
