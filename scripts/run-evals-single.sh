#!/usr/bin/env bash
# Super lightweight smoke check of a plugin's evals: every case once, no
# no-plugin baseline, Haiku for both the cases and the judge. Catches broken skills and fixtures;
# scores are noisy with a single run, so use scripts/run-evals.sh (2 runs) or
# scripts/run-evals-full.sh (3 runs + baseline) before trusting a number.
#
#   scripts/run-evals-single.sh <plugin> [claude plugin eval options...]
#
# Examples:
#   scripts/run-evals-single.sh kb-workflow
#   scripts/run-evals-single.sh kb-workflow --tag sync-dev
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
plugin="${1:?usage: scripts/run-evals-single.sh <plugin> [claude plugin eval options...]}"
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
  --model haiku \
  --judge-model haiku \
  --runs 1 \
  --ablation none \
  --concurrency 4 \
  --no-publish \
  "$@"
