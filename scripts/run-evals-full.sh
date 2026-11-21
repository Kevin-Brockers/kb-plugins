#!/usr/bin/env bash
# Run a plugin's full eval suite: 3 runs per case, each with and without the
# plugin, so the report shows the uplift (Δ) the plugin gives. This costs
# about 3x as much as scripts/run-evals.sh; use that one for everyday checks.
#
#   scripts/run-evals-full.sh <plugin> [claude plugin eval options...]
#
# Examples:
#   scripts/run-evals-full.sh kb-workflow
#   scripts/run-evals-full.sh kb-workflow --tag sync-dev
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
plugin="${1:?usage: scripts/run-evals-full.sh <plugin> [claude plugin eval options...]}"
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
  --model sonnet \
  --judge-model haiku \
  --runs 3 \
  --ablation with-without \
  --concurrency 4 \
  --no-publish \
  "$@"
