"""Shell command parsing and git helpers shared by the guard checks."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass, field

DENY = "deny"
ASK = "ask"
Finding = tuple[str, str]  # (decision, reason)

OPERATORS = {";", "&&", "||", "|", "&", ";;", "|&", "(", ")", "\n"}
PIPES = {"|", "|&"}
REDIRECT = re.compile(r"^[<>&]+$")
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
WRAPPERS = {"env", "command", "exec", "time", "nohup", "sudo", "doas", "nice"}
WRAPPER_OPTS_WITH_VALUE = {"-u", "-g", "-n", "-C"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh"}
XARGS_OPTS_WITH_VALUE = {"-n", "-I", "-L", "-P", "-d", "-E", "-s", "-a"}
GIT_GLOBAL_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
MAX_DEPTH = 3


@dataclass
class Command:
    tokens: list[str]
    wrappers: set[str] = field(default_factory=set)
    piped: bool = False  # reads stdin from a pipe

    @property
    def prog(self) -> str:
        return os.path.basename(self.tokens[0])

    @property
    def args(self) -> list[str]:
        return self.tokens[1:]


def _segments(command: str) -> list[tuple[list[str], bool]]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars="();<>|&\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    segments: list[tuple[list[str], bool]] = [([], False)]
    for tok in lexer:
        if tok in OPERATORS:
            segments.append(([], tok in PIPES))
        else:
            segments[-1][0].append(tok)
    result = []
    for tokens, piped in segments:
        cleaned: list[str] = []
        skip = False
        for tok in tokens:
            if skip:
                skip = False
                continue
            if REDIRECT.match(tok):
                if cleaned and cleaned[-1].isdigit():
                    cleaned.pop()  # the fd in `2>file`
                skip = True  # the redirect target
                continue
            cleaned.append(tok)
        if cleaned:
            result.append((cleaned, piped))
    return result


def _unwrap(tokens: list[str], piped: bool, wrappers: set[str], depth: int) -> Iterator[Command]:
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if ASSIGNMENT.match(tok):
            i += 1
        elif os.path.basename(tok) in WRAPPERS:
            wrappers = wrappers | {os.path.basename(tok)}
            i += 1
            while i < len(tokens) and tokens[i].startswith("-"):
                i += 2 if tokens[i] in WRAPPER_OPTS_WITH_VALUE else 1
        else:
            break
    rest = tokens[i:]
    if not rest:
        return
    prog = os.path.basename(rest[0])
    if prog in SHELLS and "-c" in rest:
        idx = rest.index("-c")
        if idx + 1 < len(rest):
            yield from iter_commands(rest[idx + 1], depth + 1, wrappers)
        return
    if prog == "eval" and len(rest) > 1:
        yield from iter_commands(" ".join(rest[1:]), depth + 1, wrappers)
        return
    if prog == "xargs":
        j = 1
        while j < len(rest) and rest[j].startswith("-"):
            j += 2 if rest[j] in XARGS_OPTS_WITH_VALUE else 1
        yield from _unwrap(rest[j:], piped, wrappers | {"xargs"}, depth)
        return
    yield Command(rest, wrappers, piped)


def iter_commands(command: str, depth: int = 0, wrappers: set[str] | None = None) -> Iterator[Command]:
    """Yield every simple command in a shell string, looking inside
    `bash -c`, `eval` and `xargs`. Raises ValueError on unparsable input."""
    if depth > MAX_DEPTH:
        return
    for tokens, piped in _segments(command):
        yield from _unwrap(tokens, piped, set(wrappers or ()), depth)


def git_subcommand(cmd: Command, cwd: str) -> tuple[str | None, list[str], str]:
    """Return (subcommand, its args, effective working dir) for a git call."""
    tokens = cmd.tokens
    i, where = 1, cwd
    while i < len(tokens) and tokens[i].startswith("-"):
        if tokens[i] in GIT_GLOBAL_WITH_VALUE:
            if tokens[i] == "-C" and i + 1 < len(tokens):
                where = os.path.join(cwd, os.path.expanduser(tokens[i + 1]))
            i += 2
        else:
            i += 1
    if i >= len(tokens):
        return None, [], where
    return tokens[i], tokens[i + 1 :], where


def short_flags(args: list[str], stop_at: str = "") -> set[str]:
    """Collect single-letter flags from clusters like `-nm`, stopping inside a
    cluster at the first letter that takes a value (listed in stop_at)."""
    flags: set[str] = set()
    for a in args:
        if a == "--":
            break
        if a.startswith("-") and not a.startswith("--") and len(a) > 1:
            for ch in a[1:]:
                flags.add(ch)
                if ch in stop_at:
                    break
    return flags


def git_out(cwd: str, *args: str, strip: bool = True) -> str | None:
    try:
        res = subprocess.run(
            ["git", "-C", cwd, *args],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if res.returncode != 0:
        return None
    return res.stdout.strip() if strip else res.stdout


def current_branch(cwd: str) -> str | None:
    return git_out(cwd, "symbolic-ref", "--quiet", "--short", "HEAD")


def has_head(cwd: str) -> bool:
    return git_out(cwd, "rev-parse", "--verify", "--quiet", "HEAD") is not None
