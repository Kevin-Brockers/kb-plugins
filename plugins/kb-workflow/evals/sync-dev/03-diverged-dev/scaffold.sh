. "$(dirname "$0")/../../_lib/fixtures.sh"
init_repo
merged_branches
# A commit on local dev that origin/dev does not have.
echo "Local note." >> README.md
commit "Local tweak on dev" README.md
git switch -q feature/json_store
