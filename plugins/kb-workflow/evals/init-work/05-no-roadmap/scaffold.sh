. "$(dirname "$0")/../../_lib/fixtures.sh"
init_repo --no-plans
write_changelog
commit "Add changelog" CHANGELOG.md
git push -q origin dev
