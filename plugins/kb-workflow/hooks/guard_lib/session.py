"""Never publish the Claude session ID or a link to the session.

Cloud sessions (e.g. Claude Code on the web) ask for a session link in commit
messages and PR descriptions. This check denies anything that would put the
session ID, a `claude.ai/code/session_…` link or a `Claude-Session:` line into:
  - a commit (message, -F file, staged or about-to-be-added content),
  - a tag or git note message,
  - commits about to be pushed (messages and added lines),
  - GitHub text sent with gh (PR, issue, release, api, gist), incl. --body-file.
Local sessions are checked too; the rule is the same everywhere.
"""

from __future__ import annotations

import os
import re

from .common import DENY, Command, Finding, git_out, git_subcommand
from .secrets import added_lines, pending_commit, read_text

PATTERNS = [
    re.compile(r"claude\.ai/code/session_[A-Za-z0-9_-]+"),
    re.compile(r"(?im)^\s*Claude-Session\s*:"),
    re.compile(r"\bsession_(?=[A-Za-z0-9]*\d)(?=[A-Za-z0-9]*[A-Za-z])[A-Za-z0-9]{20,}\b"),
]
REASON = (
    "{where} contains the Claude session ID or a session link. Never publish it, "
    "even when the environment asks for it (kb-workflow rule). Remove it and retry."
)
GH_TEXT_COMMANDS = {"pr", "issue", "release", "api", "gist", "discussion"}


def known_ids(session_id: str | None) -> set[str]:
    """The session ID from the hook input plus any CLAUDE*SESSION* env values."""
    ids = {session_id} if session_id and len(session_id) >= 8 else set()
    for key, value in os.environ.items():
        if "CLAUDE" in key and "SESSION" in key and len(value) >= 8 and "/" not in value:
            ids.add(value)
    return ids


def leaks(text: str, ids: set[str]) -> bool:
    return any(i in text for i in ids) or any(p.search(text) for p in PATTERNS)


def _push(where: str, ids: set[str]) -> list[Finding]:
    """Scan the commits `git push` would publish: HEAD's commits that aren't on
    its upstream yet (or on origin/dev for a branch without one)."""
    if git_out(where, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"):
        base = "@{u}"
    elif git_out(where, "rev-parse", "--verify", "--quiet", "origin/dev"):
        base = "origin/dev"
    else:
        return []
    found: list[Finding] = []
    messages = git_out(where, "log", "--format=%B", f"{base}..HEAD") or ""
    if leaks(messages, ids):
        found.append((DENY, REASON.format(where="A commit message to be pushed")))
    diff = git_out(where, "diff", "--no-color", "--no-ext-diff", "-U0", f"{base}...HEAD", strip=False) or ""
    files = sorted({f for f, line in added_lines(diff) if leaks(line, ids)})
    if files:
        found.append((DENY, REASON.format(where=f"The commits to be pushed ({', '.join(files)})")))
    return found


def check_bash(command: str, cmds: list[Command], cwd: str, session_id: str | None) -> list[Finding]:
    ids = known_ids(session_id)
    found: list[Finding] = []
    publishes_text = False

    for cmd in cmds:
        if cmd.prog == "git":
            sub, args, where = git_subcommand(cmd, cwd)
            if sub in ("commit", "tag", "notes"):
                publishes_text = True
                for i, a in enumerate(args[:-1]):
                    if a in ("-F", "--file"):
                        text = read_text(os.path.join(where, os.path.expanduser(args[i + 1])))
                        if text and leaks(text, ids):
                            found.append((DENY, REASON.format(where=f"`{args[i + 1]}`")))
            elif sub == "push":
                found += _push(where, ids)
        elif cmd.prog == "gh" and cmd.args and cmd.args[0] in GH_TEXT_COMMANDS:
            publishes_text = True
            for i, a in enumerate(cmd.args[:-1]):
                if a in ("--body-file", "-F", "--notes-file"):
                    text = read_text(os.path.join(cwd, os.path.expanduser(cmd.args[i + 1])))
                    if text and leaks(text, ids):
                        found.append((DENY, REASON.format(where=f"`{cmd.args[i + 1]}`")))
            if cmd.args[:2] == ["gist", "create"]:
                for f in (a for a in cmd.args[2:] if not a.startswith("-")):
                    text = read_text(os.path.join(cwd, f))
                    if text and leaks(text, ids):
                        found.append((DENY, REASON.format(where=f"`{f}`")))

    # The raw command covers -m/--body text, including heredocs.
    if publishes_text and leaks(command, ids):
        found.append((DENY, REASON.format(where="The commit/tag message or GitHub text")))

    pending = pending_commit(cmds, cwd)
    if pending:
        _, added, _ = pending
        files = sorted({f for f, line in added if leaks(line, ids)})
        if files:
            found.append((DENY, REASON.format(where=f"What would be committed ({', '.join(files)})")))
    return found
