. "$(dirname "$0")/../../_lib/fixtures.sh"
init_repo
printf ".env\\n.env.*\\n!.env.example\\n*.pem\\n*.key\\n__pycache__/\\n" > .gitignore
commit "Add .gitignore" .gitignore
git push -q origin dev
