---
name: version-check
description: Check that version numbers match across .meta, .install, and .py files. Use before pipeline push, when bumping a version, or when version drift is suspected.
allowed-tools: Bash, Grep, Read
---

Check version consistency across all version-bearing files in this project.

## Versions found

!`echo "--- .meta ---" && grep "^version=" *.meta 2>/dev/null || echo "(no .meta)"`
!`echo "--- .install ---" && grep "^VERSION=" *.install 2>/dev/null || echo "(no .install)"`
!`echo "--- .py ---" && grep -n "^VERSION\s*=" *.py 2>/dev/null || echo "(no .py)"`

## Installer type

!`head -5 *.install 2>/dev/null | grep -i "handcrafted" && echo "⚠ HANDCRAFTED installer" || echo "Generated installer (VERSION set by pipeline)"`

## Instructions

Compare the version strings above and report:

- ✓ **All match** — state the version and confirm ready
- ✗ **Mismatch** — show exactly which files differ, what each says, and the
  precise line edits needed to bring them in line
- ⚠ **HANDCRAFTED installer** — remind that the `.install` VERSION must be
  bumped manually before the pipeline run (the `--install` stage will NOT
  reset it automatically)

Note: for a Generated installer, only `.meta` and `.py` need manual syncing —
the `--install` pipeline stage regenerates the installer from `.meta`.
