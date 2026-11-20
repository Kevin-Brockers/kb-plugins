. "$(dirname "$0")/../../_lib/fixtures.sh"
# A new project: git init was run, nothing is committed yet.
git init -q -b main
write_app
echo "TODO_SYNC_TOKEN=local-dev-only" > .env
