"""Branch, push, commit and pull-request rules of the kb workflow."""

from __future__ import annotations

from .common import ASK, DENY, Command, Finding, current_branch, git_subcommand, has_head, short_flags

PROTECTED = {"main", "dev"}
PUSH_OPTS_WITH_VALUE = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}


def _ref_name(ref: str) -> str:
    for prefix in ("refs/heads/", "refs/remotes/origin/"):
        if ref.startswith(prefix):
            return ref[len(prefix) :]
    return ref


def _push(args: list[str], cwd: str) -> list[Finding]:
    found: list[Finding] = []
    positional: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--":
            positional.extend(args[i + 1 :])
            break
        if a in PUSH_OPTS_WITH_VALUE:
            i += 2
            continue
        if a.startswith("--force") or a == "--mirror" or "f" in short_flags([a]):
            found.append((DENY, "Force pushes are not allowed (kb-workflow rule)."))
        if a in ("--all", "--branches"):
            found.append((DENY, "Pushing all branches would include main/dev (kb-workflow rule)."))
        if a == "--delete" or "d" in short_flags([a]):
            found.append((ASK, "This deletes a branch on GitHub."))
        if not a.startswith("-"):
            positional.append(a)
        i += 1

    refspecs = positional[1:]  # positional[0] is the remote
    branch = current_branch(cwd)
    if not refspecs and branch in PROTECTED:
        found.append((DENY, f"Never push to `{branch}`; it changes only through PRs (kb-workflow rule)."))
    for spec in refspecs:
        if spec.startswith("+"):
            found.append((DENY, "Force pushes (`+refspec`) are not allowed (kb-workflow rule)."))
        if spec.startswith(":"):
            found.append((ASK, "This deletes a branch on GitHub."))
        dst = spec.split(":", 1)[1] if ":" in spec else spec
        if dst == "HEAD":
            dst = branch or ""
        if _ref_name(dst.lstrip("+")) in PROTECTED:
            found.append(
                (DENY, f"Never push to `{_ref_name(dst.lstrip('+'))}`; it changes only through PRs (kb-workflow rule).")
            )
    return found


def _commit(args: list[str], cwd: str) -> list[Finding]:
    found: list[Finding] = []
    if "--no-verify" in args or "n" in short_flags(args, stop_at="mFCcSt"):
        found.append((DENY, "Never bypass git hooks (--no-verify / -n) unless the maintainer says so (kb-workflow rule)."))
    branch = current_branch(cwd)
    if branch in PROTECTED and has_head(cwd):
        found.append(
            (DENY, f"Never commit to `{branch}`. Create a feature/fix/docs/chore branch from dev first (kb-workflow rule).")
        )
    return found


def _gh(cmd: Command) -> list[Finding]:
    args = cmd.args
    if args[:2] == ["pr", "merge"]:
        return [(DENY, "Only the maintainer merges pull requests (kb-workflow rule).")]
    if args[:2] == ["pr", "create"]:
        base = None
        rest = args[2:]
        for i, a in enumerate(rest):
            if a in ("--base", "-B") and i + 1 < len(rest):
                base = rest[i + 1]
            elif a.startswith("--base="):
                base = a.split("=", 1)[1]
        if base is None:
            return [(DENY, "Pass `--base dev` explicitly; PRs go against dev (kb-workflow rule).")]
        if base == "main":
            return [(DENY, "PRs go against dev, never main. Only the maintainer opens dev → main PRs (kb-workflow rule).")]
    return []


def check(cmd: Command, cwd: str) -> list[Finding]:
    if cmd.prog == "git":
        sub, args, where = git_subcommand(cmd, cwd)
        if sub == "push":
            return _push(args, where)
        if sub == "commit":
            return _commit(args, where)
    elif cmd.prog == "gh":
        return _gh(cmd)
    return []
