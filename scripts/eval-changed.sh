#!/usr/bin/env bash
# Pre-commit hook: run the evals of every plugin skill or agent the commit
# touches. prek/pre-commit passes the staged paths; each one maps to a
# plugin and an eval tag (the skill or agent name):
#
#   plugins/<p>/skills/<s>/...        -> <p> --tag <s>
#   plugins/<p>/agents/<a>.md         -> <p> --tag <a>
#   plugins/<p>/evals/<s>/...         -> <p> --tag <s>
#   plugins/<p>/evals/_lib/...,
#   plugins/<p>/hooks/...,
#   plugins/<p>/.claude-plugin/...    -> <p> (whole suite)
#
# It runs scripts/run-evals-single.sh, the cheapest tier: 1 run per case on
# Haiku, no baseline arm, local report only. Override with environment
# variables (each is passed only when set):
#
#   KB_EVALS_RUNS=2 KB_EVALS_MODEL=sonnet git commit ...
#   KB_EVALS_ABLATION=with-without KB_EVALS_CONCURRENCY=2 git commit ...
#   KB_EVALS_DRY_RUN=1 scripts/eval-changed.sh plugins/kb-python/skills/check/SKILL.md
#
# Skip the hook for one commit with SKIP=plugin-evals git commit ...
set -euo pipefail
set -f # the "*" tag below must not expand to file names

root="$(cd "$(dirname "$0")/.." && pwd)"
threshold="${KB_EVALS_THRESHOLD:-0.8}"

# Options for run-evals-single.sh; its own defaults apply unless overridden.
common=(--trust-plugin --threshold "$threshold")
[ -z "${KB_EVALS_RUNS:-}" ] || common+=(--runs "$KB_EVALS_RUNS")
[ -z "${KB_EVALS_MODEL:-}" ] || common+=(--model "$KB_EVALS_MODEL")
[ -z "${KB_EVALS_ABLATION:-}" ] || common+=(--ablation "$KB_EVALS_ABLATION")
[ -z "${KB_EVALS_CONCURRENCY:-}" ] || common+=(--concurrency "$KB_EVALS_CONCURRENCY")

# One "<plugin> <tag>" line per staged path; tag "*" means the whole suite.
targets=""
for path in "$@"; do
  IFS=/ read -r top plugin kind name _ <<<"$path"
  [ "$top" = plugins ] && [ -n "$plugin" ] || continue
  case "$kind" in
    skills) tag="$name" ;;
    agents) tag="${name%.md}" ;;
    evals)
      case "$name" in
        _lib) tag='*' ;;
        results) continue ;;
        *) tag="$name" ;;
      esac
      ;;
    hooks | .claude-plugin) tag='*' ;;
    *) continue ;;
  esac
  targets+="$plugin $tag"$'\n'
done

failed=""
for plugin in $(printf '%s' "$targets" | cut -d' ' -f1 | sort -u); do
  tags="$(printf '%s' "$targets" | awk -v p="$plugin" '$1 == p { print $2 }' | sort -u)"
  # A shared file changed: run the whole suite once instead of tag by tag.
  if printf '%s\n' "$tags" | grep -qx '\*'; then
    tags='*'
  fi

  for tag in $tags; do
    args=("${common[@]}")
    if [ "$tag" = '*' ]; then
      label="$plugin"
    else
      label="$plugin:$tag"
      if [ ! -d "$root/plugins/$plugin/evals/$tag" ]; then
        echo "warning: $label changed but has no evals in plugins/$plugin/evals/$tag/" >&2
        continue
      fi
      args+=(--tag "$tag")
    fi

    echo "==> evals for $label"
    if [ -n "${KB_EVALS_DRY_RUN:-}" ]; then
      echo "scripts/run-evals-single.sh $plugin ${args[*]}"
    elif ! "$root/scripts/run-evals-single.sh" "$plugin" "${args[@]}"; then
      failed+=" $label"
    fi
  done
done

if [ -n "$failed" ]; then
  echo "evals failed or scored below $threshold:$failed" >&2
  echo "Reports are in plugins/<plugin>/evals/results/." >&2
  exit 1
fi
