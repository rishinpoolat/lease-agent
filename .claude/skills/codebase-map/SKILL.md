---
name: codebase-map
description: How and when to update CODEBASE_MAP.md. Use this whenever a feature adds, removes, or renames a top-level folder, changes a module's responsibility, or establishes a new pattern future code should follow — not needed for changes that don't touch project structure.
---

`CODEBASE_MAP.md` (project root) is read every session before exploring the
file tree — it should answer "where does X live" faster than searching. This
skill governs keeping it accurate.

When to update it:
- A top-level folder is added, removed, or renamed
- A module's responsibility changes
- A new pattern is established that future code should follow

How to write entries:
- One folder per heading, 1-2 lines max
- Name the pattern to follow, not just what's there
- Update it in the same step as the code change — don't batch for later

Note: the project is fully built (see the "Status" line at the top of
`CLAUDE.md`) — `CODEBASE_MAP.md` now describes the actual structure, not a
plan. Any feature that adds/removes/renames a folder should update its
section as part of that same change, not leave the map to drift out of
date.

This is a standing rule for the rest of the current task — if more
structural changes happen later in the same session, this still applies.
