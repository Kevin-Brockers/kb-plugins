"""Commands that delete files, discard work or damage the system."""

from __future__ import annotations

import os
from pathlib import Path

from .common import ASK, DENY, SHELLS, Command, Finding, git_subcommand, short_flags

CRITICAL_NAMES = {"/", "~", "~/", ".", "./", "..", "../", "*", "./*", "/*", "~/*", "$HOME", "${HOME}"}
REBUILDABLE_DIRS = {"build", "dist", "node_modules"}  # `rm -r` on these inside the project is allowed
DISK_ERASE ={"eraseDisk", "eraseVolume", "zeroDisk", "randomDisk", "secureErase", "partitionDisk", "reformat"}


def _is_critical(target: str, cwd: str) -> bool:
    """True if deleting `target` recursively would wipe the system, the home
    folder, the project, a parent of the project or its git history."""
    if target in CRITICAL_NAMES:
        return True
    expanded = os.path.expanduser(os.path.expandvars(target))
    if os.path.basename(expanded.rstrip("/")) == ".git":
        return True
    if os.path.basename(expanded) == "*":
        expanded = os.path.dirname(expanded) or "."
    path = Path(os.path.realpath(os.path.join(cwd, expanded)))
    home = Path(os.path.realpath(os.path.expanduser("~")))
    project = Path(os.path.realpath(cwd))
    if len(path.parts) <= 2:  # "/" or a top-level folder like /usr
        return True
    if path == project or path in project.parents:
        return True
    return path == home or path in home.parents or path.parent == home


def _is_rebuildable(target: str, cwd: str) -> bool:
    """True for build/dist/node_modules folders inside the project (no globs)."""
    if any(ch in target for ch in "*?[$~"):
        return False
    path = Path(os.path.realpath(os.path.join(cwd, target)))
    project = Path(os.path.realpath(cwd))
    return path.name in REBUILDABLE_DIRS and project in path.parents


def _rm(cmd: Command, cwd: str) -> list[Finding]:
    recursive = False
    targets: list[str] = []
    end_of_opts = False
    for a in cmd.args:
        if not end_of_opts and a == "--":
            end_of_opts = True
        elif not end_of_opts and a.startswith("--"):
            recursive |= a == "--recursive"
        elif not end_of_opts and a.startswith("-") and len(a) > 1:
            recursive |= bool({"r", "R"} & short_flags([a]))
        else:
            targets.append(a)
    if recursive:
        for t in targets:
            if _is_critical(t, cwd):
                return [(DENY, f"`rm -r {t}` would delete the system, home folder, project or git history.")]
        if targets and all(_is_rebuildable(t, cwd) for t in targets):
            return []
    shown = " ".join(targets[:5]) + (" …" if len(targets) > 5 else "")
    return [(ASK, f"`rm` deletes files permanently: {shown}")]


def _git(cmd: Command, cwd: str) -> list[Finding]:
    sub, args, _ = git_subcommand(cmd, cwd)
    flags = short_flags(args)
    if sub == "reset" and "--hard" in args:
        return [(ASK, "`git reset --hard` discards uncommitted changes.")]
    if sub == "clean" and ("f" in flags or "--force" in args):
        return [(ASK, "`git clean -f` deletes untracked files.")]
    if sub == "branch" and ("D" in flags or ("--delete" in args and "--force" in args)):
        return [(ASK, "`git branch -D` deletes a branch even if it isn't merged.")]
    if sub == "checkout" and ("--" in args or "." in args or "f" in flags or "--force" in args):
        return [(ASK, "This `git checkout` discards uncommitted changes.")]
    if sub == "restore" and ("--staged" not in args or "--worktree" in args or "W" in flags):
        return [(ASK, "`git restore` discards uncommitted changes.")]
    if sub == "stash" and args[:1] in (["drop"], ["clear"]):
        return [(ASK, f"`git stash {args[0]}` deletes stashed changes.")]
    if sub in ("filter-branch", "filter-repo"):
        return [(ASK, f"`git {sub}` rewrites history.")]
    if sub == "reflog" and args[:1] == ["expire"]:
        return [(ASK, "`git reflog expire` removes recovery points.")]
    return []


def check(cmd: Command, cwd: str) -> list[Finding]:
    found: list[Finding] = []
    if cmd.wrappers & {"sudo", "doas"}:
        found.append((ASK, "This command runs with root privileges."))
    prog, args = cmd.prog, cmd.args
    if prog == "rm":
        found += _rm(cmd, cwd)
    elif prog in ("shred", "unlink", "srm"):
        found.append((ASK, f"`{prog}` deletes files permanently."))
    elif prog == "find" and ("-delete" in args or any(a in ("-exec", "-execdir", "-ok") for a in args)):
        if "-delete" in args or "rm" in args:
            found.append((ASK, "This `find` deletes files."))
    elif prog == "dd" and any(a.startswith("of=/dev/") for a in args):
        found.append((DENY, "`dd` writing to a device can destroy a disk."))
    elif prog.startswith("mkfs") or prog in ("fdisk", "sfdisk", "wipefs"):
        found.append((DENY, f"`{prog}` can destroy a disk."))
    elif prog == "diskutil" and args and (args[0] in DISK_ERASE or args[0].startswith("erase")):
        found.append((DENY, "`diskutil` erase commands can destroy a disk."))
    elif prog in ("chmod", "chown", "chgrp") and ("R" in short_flags(args) or "--recursive" in args):
        found.append((ASK, f"Recursive `{prog}` changes many files at once."))
    elif prog in SHELLS and cmd.piped and not [a for a in args if not a.startswith("-")]:
        found.append((ASK, f"This pipes a script straight into `{prog}`."))
    elif prog == "git":
        found += _git(cmd, cwd)
    elif prog == "gh" and args[:2] == ["repo", "delete"]:
        found.append((DENY, "Deleting a GitHub repository is not allowed for agents."))
    elif prog == "gh" and args[:2] == ["release", "delete"]:
        found.append((ASK, "This deletes a GitHub release."))
    return found
