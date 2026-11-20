. "$(dirname "$0")/../../_lib/fixtures.sh"
# Everything the skill sets up is already there.
init_repo
printf ".env\\n.env.*\\n!.env.example\\n*.pem\\n*.key\\n__pycache__/\\n" > .gitignore
cat > .pre-commit-config.yaml <<'YAML'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-merge-conflict
      - id: check-added-large-files
      - id: detect-private-key
      - id: no-commit-to-branch
        args: [--branch, main, --branch, dev]
YAML
commit "Add pre-commit config and .gitignore" .gitignore .pre-commit-config.yaml
git push -q origin dev
