. "$(dirname "$0")/../../_lib/fixtures.sh"
init_repo
pyproject_version 0.2.0.dev0
commit "Add pyproject.toml" pyproject.toml AGENTS.md
git push -q origin dev
cat > .pre-commit-config.yaml <<'YAML'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: no-commit-to-branch
        args: [--branch, main, --branch, dev]
YAML
mkdir -p .github/workflows
cat > .github/workflows/ci.yml <<'YAML'
name: CI
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: sh check.sh
YAML
commit "Add pre-commit config and CI" .pre-commit-config.yaml .github/workflows/ci.yml
git push -q origin dev
branch_from_dev chore/yaml_checks
