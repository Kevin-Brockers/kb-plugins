. "$(dirname "$0")/../../_lib/fixtures.sh"
init_repo
commit_file() { echo "$2" >> "$1"; commit "$3" "$1"; }
commit_file README.md "Usage: python3 todo.py add <title>" "Document the add command"
commit_file README.md "Todos are stored in todos.json." "Explain where todos are stored"
commit_file AGENTS.md "- Python 3.9 or newer." "Note the minimum Python version"
