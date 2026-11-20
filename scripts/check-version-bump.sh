#!/usr/bin/env bash
# Pre-commit hook: a commit that changes a plugin's skills, agents or hooks
# must also bump that plugin's version in .claude-plugin/plugin.json, or
# installs won't pick up the change.
#
# The staged version is compared with the version on the base ref (the
# merge-base of HEAD and origin/main), not with HEAD, so a branch needs one
# bump per plugin, not one per commit. It must be exactly one step up:
#
#   1.2.3 -> 1.2.4 (patch), 1.3.0 (minor) or 2.0.0 (major)
#
# A plugin that is new since the base ref is skipped. Change the base ref
# with KB_VERSION_BASE (e.g. KB_VERSION_BASE=HEAD to require a bump in
# every commit). Skip the hook for one commit with
# SKIP=plugin-version-bump git commit ...
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

base_ref="${KB_VERSION_BASE:-origin/main}"
if git rev-parse -q --verify "$base_ref^{commit}" >/dev/null &&
  git rev-parse -q --verify HEAD >/dev/null; then
  base="$(git merge-base HEAD "$base_ref" 2>/dev/null || git rev-parse HEAD)"
elif git rev-parse -q --verify HEAD >/dev/null; then
  base="$(git rev-parse HEAD)"
else
  exit 0 # first commit: nothing to compare with
fi

# Plugins whose skills, agents or hooks the commit touches, deletions
# included (pre-commit doesn't pass deleted files, so ask git directly).
plugins="$(git diff --cached --name-only --no-renames HEAD 2>/dev/null |
  sed -nE 's#^plugins/([^/]+)/(skills|agents|hooks)/.*#\1#p' | sort -u)"

# Prints the "version" of a plugin.json read from stdin, or nothing.
read_version() {
  python3 -c 'import json, sys; print(json.load(sys.stdin).get("version", ""))' 2>/dev/null || true
}

failed=0
for plugin in $plugins; do
  manifest="plugins/$plugin/.claude-plugin/plugin.json"
  git cat-file -e "$base:$manifest" 2>/dev/null || continue # new plugin
  if ! git cat-file -e ":$manifest" 2>/dev/null; then
    continue # plugin removed in this commit
  fi

  old="$(git show "$base:$manifest" | read_version)"
  new="$(git show ":$manifest" | read_version)"
  semver='^[0-9]+\.[0-9]+\.[0-9]+$'

  if ! [[ "$new" =~ $semver ]]; then
    echo "$plugin: version \"$new\" in $manifest is not MAJOR.MINOR.PATCH" >&2
    failed=1
    continue
  fi
  if ! [[ "$old" =~ $semver ]]; then
    continue # can't judge the bump from a non-semver base version
  fi

  IFS=. read -r major minor patch <<<"$old"
  patch_bump="$major.$minor.$((patch + 1))"
  minor_bump="$major.$((minor + 1)).0"
  major_bump="$((major + 1)).0.0"

  case "$new" in
    "$patch_bump" | "$minor_bump" | "$major_bump") ;;
    "$old")
      echo "$plugin: skills, agents or hooks changed but the version is still $old." >&2
      echo "  Bump it in $manifest to $patch_bump, $minor_bump or $major_bump and stage it." >&2
      failed=1
      ;;
    *)
      echo "$plugin: version $old -> $new is not a single step." >&2
      echo "  Use $patch_bump (patch), $minor_bump (minor) or $major_bump (major) in $manifest." >&2
      failed=1
      ;;
  esac
done

exit "$failed"
