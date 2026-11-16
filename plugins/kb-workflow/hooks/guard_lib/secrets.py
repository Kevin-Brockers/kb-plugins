"""Keep secrets and env files out of commits, GitHub text and source files.

Known token formats and sensitive file names are denied; generic
`password = "…"`-style assignments and credentials in URLs ask first.
A line containing `allow-secret` is skipped (for test fixtures).
"""

from __future__ import annotations

import os
import re

from .common import ASK, DENY, Command, Finding, git_out, git_subcommand, short_flags

SPECIFIC = [
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}")),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("OpenAI API key", re.compile(r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}")),
    ("Stripe live key", re.compile(r"\b[rs]k_live_[0-9A-Za-z]{20,}")),
    ("private key", re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----")),
]
GENERIC = re.compile(
    r"(?i)[\w.-]*(?:api[_-]?key|secret|token|passw(?:or)?d|pwd|private[_-]?key|access[_-]?key|credential)[\w.-]*"
    r"""["']?\s*[:=]\s*["']([^\s"']{12,})["']"""
)
URL_CREDENTIALS = re.compile(r"\b[a-z][a-z0-9+.-]*://[^/\s:@'\"]+:([^/\s:@'\"]{3,})@")
PLACEHOLDER = re.compile(r"(?i)example|sample|dummy|placeholder|changeme|change_me|your[_-]|<|\*\*\*|xxx|fake|\$\{|\{\{")
PRAGMA = "allow-secret"
SENSITIVE_FILE = re.compile(
    r"(?i)^(?:\.env(?:\..+)?|\.envrc|id_(?:rsa|dsa|ecdsa|ed25519)|\.netrc|\.pypirc|\.git-credentials"
    r"|credentials(?:\.json)?|service[-_]account.*\.json|secrets?\.(?:ya?ml|json|toml)"
    r"|.*\.(?:pem|key|p12|pfx|jks|keystore|ppk))$"
)
SAFE_ENV_SUFFIX = (".example", ".sample", ".template", ".dist", ".defaults")
MAX_FILE_BYTES = 1_000_000
GH_TEXT_COMMANDS = {"pr", "issue", "release", "api", "gist", "discussion"}


def is_sensitive_file(path: str) -> bool:
    name = os.path.basename(path)
    if name.lower().endswith(SAFE_ENV_SUFFIX):
        return False
    return bool(SENSITIVE_FILE.match(name))


def _mask(value: str) -> str:
    return value[:4] + "…" if len(value) > 4 else "…"


def scan_text(text: str, where: str, generic: bool = True) -> list[Finding]:
    found: list[Finding] = []
    for line in text.splitlines():
        if PRAGMA in line:
            continue
        for kind, pattern in SPECIFIC:
            m = pattern.search(line)
            if m:
                found.append((DENY, f"{where}: possible {kind} (`{_mask(m.group(0))}`)."))
        if not generic or PLACEHOLDER.search(line):
            continue
        m = GENERIC.search(line)
        if m and re.search(r"\d", m.group(1)) and re.search(r"[A-Za-z]", m.group(1)):
            found.append((ASK, f"{where}: possible hard-coded secret (`{_mask(m.group(0))}`)."))
        m = URL_CREDENTIALS.search(line)
        if m:
            found.append((ASK, f"{where}: URL with a password in it."))
    return found


def added_lines(diff: str) -> list[tuple[str, str]]:
    """(file, added line) pairs from a unified diff."""
    out: list[tuple[str, str]] = []
    current = "?"
    for line in diff.splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else line[4:]
        elif line.startswith("+") and not line.startswith("+++"):
            out.append((current, line[1:]))
    return out


def read_text(path: str) -> str | None:
    try:
        if os.path.getsize(path) > MAX_FILE_BYTES:
            return None
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError:
        return None
    if b"\0" in data:
        return None
    return data.decode("utf-8", errors="replace")


def _pending_commit(cmds: list[Command], cwd: str) -> list[Finding]:
    """Scan what a `git commit` in this Bash call would commit."""
    pending = pending_commit(cmds, cwd)
    if pending is None:
        return []
    new_files, added, messages = pending
    found: list[Finding] = []
    for f in sorted(set(new_files)):
        if is_sensitive_file(f):
            found.append((DENY, f"`{f}` looks like a secrets/env file and must not be committed. Add it to .gitignore."))
    by_file: dict[str, list[str]] = {}
    for f, line in added:
        by_file.setdefault(f, []).append(line)
    for f, lines in by_file.items():
        found += scan_text("\n".join(lines), f)
    for message in messages:
        found += scan_text(message, "commit message")
    return found


def pending_commit(
    cmds: list[Command], cwd: str
) -> tuple[list[str], list[tuple[str, str]], list[str]] | None:
    """What a `git commit` in this Bash call would commit, including files a
    `git add` earlier in the same call would stage: (new files, (file, added
    line) pairs, commit message texts). None if there's no commit."""
    commits, adds = [], []
    for cmd in cmds:
        if cmd.prog != "git":
            continue
        sub, args, where = git_subcommand(cmd, cwd)
        if sub == "commit":
            commits.append((args, where))
        elif sub == "add":
            adds.append((args, where))
    if not commits:
        return None

    where = commits[0][1]
    root = git_out(where, "rev-parse", "--show-toplevel") or where
    diff_args = ["diff", "--no-color", "--no-ext-diff", "-U0"]

    # 1. already staged
    added = added_lines(git_out(where, *diff_args, "--cached", strip=False) or "")
    new_files = (git_out(where, "diff", "--cached", "--name-only", "--diff-filter=A") or "").splitlines()

    # 2. tracked changes that `commit -a` or `git add` would stage
    commit_all = any("--all" in a or "a" in short_flags(a, stop_at="mFCcSt") for a, _ in commits)
    add_paths: list[str] = []
    force_add = False
    for args, _ in adds:
        paths = [a for a in args if not a.startswith("-")]
        add_paths += paths or (["."] if {"-A", "--all", "-u", "--update"} & set(args) else [])
        force_add |= "-f" in args or "--force" in args
    if commit_all or add_paths:
        spec = ["--", *add_paths] if add_paths and not commit_all else []
        added += added_lines(git_out(where, *diff_args, *spec, strip=False) or "")

    # 3. untracked files a `git add` would pick up
    if add_paths:
        ls = ["ls-files", "--others", "--full-name"]
        if not force_add:
            ls.append("--exclude-standard")
        untracked = (git_out(where, *ls, "--", *add_paths) or "").splitlines()
        new_files += untracked
        for rel in untracked:
            text = read_text(os.path.join(root, rel))
            if text:
                added += [(rel, line) for line in text.splitlines()]

    # 4. the commit message: -m text and -F files
    messages = []
    for args, at in commits:
        messages.append(" ".join(args))
        for i, a in enumerate(args[:-1]):
            if a in ("-F", "--file"):
                text = read_text(os.path.join(at, os.path.expanduser(args[i + 1])))
                if text:
                    messages.append(text)
    return new_files, added, messages


def _gh(cmd: Command, cwd: str) -> list[Finding]:
    args = cmd.args
    if not args or args[0] not in GH_TEXT_COMMANDS or args[:2] == ["secret", "set"]:
        return []
    found = scan_text(" ".join(args), f"gh {args[0]} text")
    for i, a in enumerate(args[:-1]):
        if a in ("--body-file", "-F", "--notes-file"):
            text = read_text(os.path.join(cwd, os.path.expanduser(args[i + 1])))
            if text:
                found += scan_text(text, args[i + 1])
    if args[:2] == ["gist", "create"]:
        files = [a for a in args[2:] if not a.startswith("-")]
        found.append((ASK, "`gh gist create` uploads files to GitHub."))
        for f in files:
            if is_sensitive_file(f):
                found.append((DENY, f"`{f}` looks like a secrets/env file and must not be uploaded."))
            text = read_text(os.path.join(cwd, f))
            if text:
                found += scan_text(text, f)
    return found


def check_bash(cmds: list[Command], cwd: str) -> list[Finding]:
    found = _pending_commit(cmds, cwd)
    for cmd in cmds:
        if cmd.prog == "gh":
            found += _gh(cmd, cwd)
    return found


def check_file_write(path: str, text: str) -> list[Finding]:
    """Writing a known token format into a source file asks first. Env and
    other secrets files (which must be gitignored) are left alone."""
    if is_sensitive_file(path):
        return []
    found = scan_text(text, os.path.basename(path), generic=False)
    return [(ASK, reason + " Keep secrets in a gitignored .env file instead.") for _, reason in found]
