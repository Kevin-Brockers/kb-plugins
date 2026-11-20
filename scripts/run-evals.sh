#!/usr/bin/env bash
# Run a plugin's eval suite (plugins/<plugin>/evals/) with the flags its
# cases need: --scaffold builds each case's git fixture, Bash/Edit/Write let
# the skills do real work, and a Sonnet judge grades the llm rubrics.
#
#   scripts/run-evals.sh <plugin> [claude plugin eval options...]
#
# Examples:
#   scripts/run-evals.sh kb-workflow --tag sync-dev
#   scripts/run-evals.sh kb-python --runs 1 --no-publish
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
plugin="${1:?usage: scripts/run-evals.sh <plugin> [claude plugin eval options...]}"
shift

# The skills run git inside the eval's OS sandbox. On macOS, /usr/bin/git is
# only a launcher for the Xcode Command Line Tools, which the sandbox can't
# reach, so every git command would fail and every case would score 0.
if [ "$(uname -s)" = Darwin ] && [ "$(command -v git)" = /usr/bin/git ]; then
  echo "error: git is Apple's /usr/bin/git, which fails inside the eval sandbox." >&2
  echo "Install git with Homebrew (brew install git) or run the evals on Linux." >&2
  exit 1
fi

exec claude plugin eval "$root/plugins/$plugin" \
  --scaffold \
  --allow-tools Bash Edit Write \
  --judge-model sonnet \
  "$@"
