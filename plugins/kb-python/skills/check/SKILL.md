---
name: check
description: Run lint, format and tests for a Python project with uv - ruff check --fix, ruff format and pytest - and report the results. Use before every commit, before opening a PR, or when asked to check, lint or test the project.
---

# check

Run all three, in this order, from the repository root:

1. `uv run ruff check --fix`
2. `uv run ruff format`
3. `uv run pytest`

Then report:

- whether each one passed;
- the files ruff fixed or reformatted (`git status --short`), so they can be
  reviewed and staged;
- for failures, the relevant output: the ruff messages that weren't
  auto-fixable, and the failing tests with their error.

Don't fix failing tests by weakening or skipping them. If a failure is
unrelated to the current change, say so and ask how to proceed. If `uv`,
`ruff` or `pytest` isn't available, report that instead of installing
anything; adding a dev dependency needs the maintainer's approval.
