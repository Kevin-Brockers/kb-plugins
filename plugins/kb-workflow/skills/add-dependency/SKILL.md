---
name: add-dependency
description: Ask the maintainer before adding a runtime or dev dependency, a pre-commit hook or a hook version bump, with a short justification. Use whenever a new package, tool or hook seems needed.
---

# add-dependency

No dependency (runtime or dev) is added without the maintainer's approval.
Changes to `.pre-commit-config.yaml` (new hooks, version bumps) count too.

1. **Check alternatives first**: can the standard library or an existing
   dependency do it? Look at the project's dependency list, don't guess.
2. **Ask the maintainer**, in a few lines:
   - the package and the version you'd use (look it up, don't invent it);
   - what it's for, and whether it's a runtime or dev dependency;
   - why the standard library or the existing dependencies aren't enough;
   - its license, if it isn't permissive (MIT, BSD, Apache-2.0).
3. **Wait** for an explicit yes. Without it, find another way or stop.
4. **Add it** with the project's tool (for Python: `uv add <pkg>` or
   `uv add --dev <pkg>`), so the lockfile is updated too.
5. **Changelog**: add an entry (`changelog-entry` skill) if the dependency is
   user-visible or developer-relevant.
