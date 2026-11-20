. "$(dirname "$0")/../../_lib/fixtures.sh"
init_repo
failing_checks
commit "Run the real tests" check.sh
git push -q origin dev
branch_from_dev feature/due_dates
add_due_dates
