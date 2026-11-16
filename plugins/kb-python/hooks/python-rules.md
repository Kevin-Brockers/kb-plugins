# kb-python: Python project conventions

This project has a `pyproject.toml`; these conventions from the kb-python
plugin apply on top of the kb-workflow rules. The project's own `AGENTS.md`
or `CLAUDE.md` wins where it says something different.

## Tooling

- Use `uv` for everything: `uv run …` to run tools, `uv add` /
  `uv add --dev` to add dependencies (after the maintainer approved them).
- Before every commit run lint, format and tests; all must pass. The `check`
  skill runs them: `uv run ruff check --fix`, `uv run ruff format`,
  `uv run pytest`.
- The prek pre-commit config also runs ruff lint (with auto-fix) and ruff
  format, from `https://github.com/astral-sh/ruff-pre-commit` (hooks
  `ruff-check` with `args: [--fix]` and `ruff-format`; latest tag via
  `gh api repos/astral-sh/ruff-pre-commit/releases/latest --jq .tag_name`).

## Code style

- Follow ruff's defaults; let `ruff format` decide formatting.
- Type hints on all public functions; prefer `dataclasses` for data types.
- Keep functions small and side effects (file I/O) at the edges.

## Tests

- Every new behavior or bug fix comes with pytest tests; for a bug fix, a
  test that fails before the fix.
- Tests that touch files use pytest's `tmp_path`, never real directories.
- Tests never touch the real home folder or config files. If the project
  reads anything from the home folder, `tests/conftest.py` should point
  `HOME` (and `USERPROFILE`) at an empty temporary folder for every test.

## CI and releases (when the project ships a tool or package)

- CI runs on GitHub Actions for pull requests into and pushes to `dev` and
  `main`: ruff check, ruff format --check and pytest on the supported Python
  versions. It doesn't replace the local runs before every commit.
- The version lives in `pyproject.toml`. Set it with `uv version <version>`,
  which updates `uv.lock` too. Development versions look like `0.2.0.dev0`.
- A release workflow, if present, runs on a `v<version>` tag: it checks the
  tagged commit is on `main`, the tag matches `pyproject.toml` and
  `CHANGELOG.md` has a section with entries for that version, then builds with
  `uv build` and creates the GitHub Release. Only the maintainer pushes tags.
