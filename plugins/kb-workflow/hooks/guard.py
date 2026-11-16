"""PreToolUse guard for the kb-workflow rules.

Runs four groups of checks (see guard_lib/):
  - git_rules:   branch, push, commit and PR rules (main/dev, force, --no-verify, gh pr merge/create)
  - destructive: rm and other commands that delete files, discard work or damage the system
  - secrets:     secrets and env files in commits, GitHub text and source files
  - session:     the Claude session ID or session links in commits, pushes and GitHub text
It also asks before edits to AGENTS.md, CLAUDE.md or ROADMAP.md.

Each finding is "deny" or "ask"; the strictest one wins and all reasons are
shown. Anything it can't parse is allowed through: this is a safety net,
not a sandbox.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from guard_lib import destructive, git_rules, secrets, session  # noqa: E402
from guard_lib.common import ASK, DENY, Finding, iter_commands  # noqa: E402

GUARDED_FILES = {"AGENTS.md", "CLAUDE.md", "ROADMAP.md"}
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def check_bash(command: str, cwd: str, session_id: str | None) -> list[Finding]:
    try:
        cmds = list(iter_commands(command))
    except ValueError:
        return []
    found: list[Finding] = []
    for cmd in cmds:
        found += git_rules.check(cmd, cwd)
        found += destructive.check(cmd, cwd)
    found += secrets.check_bash(cmds, cwd)
    found += session.check_bash(command, cmds, cwd, session_id)
    return found


def check_edit(tool: str, tool_input: dict) -> list[Finding]:
    path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    found: list[Finding] = []
    if os.path.basename(path) in GUARDED_FILES:
        found.append(
            (
                ASK,
                f"{os.path.basename(path)} changes need the maintainer's approval, except marking "
                "the implemented roadmap step [x] or replacing #TBD with the PR link (kb-workflow rule).",
            )
        )
    if tool == "Write":
        text = tool_input.get("content", "")
    elif tool == "MultiEdit":
        text = "\n".join(e.get("new_string", "") for e in tool_input.get("edits", []))
    elif tool == "NotebookEdit":
        text = tool_input.get("new_source", "")
    else:
        text = tool_input.get("new_string", "")
    found += secrets.check_file_write(path, text or "")
    return found


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()

    if tool == "Bash":
        found = check_bash(tool_input.get("command", ""), cwd, data.get("session_id"))
    elif tool in EDIT_TOOLS:
        found = check_edit(tool, tool_input)
    else:
        return
    if not found:
        return

    decision = DENY if any(d == DENY for d, _ in found) else ASK
    reasons = list(dict.fromkeys(r for d, r in found if d == decision))
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason": " ".join(reasons),
                }
            }
        )
    )


if __name__ == "__main__":
    main()
