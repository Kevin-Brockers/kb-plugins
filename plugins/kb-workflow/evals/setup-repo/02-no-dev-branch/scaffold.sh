. "$(dirname "$0")/../../_lib/fixtures.sh"
# One commit on main; no dev branch, no remote, no pre-commit config, and a
# .gitignore that doesn't cover secrets yet.
git init -q -b main
write_app
write_changelog
echo "__pycache__/" > .gitignore
git add -A
git commit -q -m "Initial commit"
