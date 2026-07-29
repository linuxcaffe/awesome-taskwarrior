---
name: fleet
description: Show awesome-taskwarrior fleet status across all managed apps. Use when asked about fleet status, dirty repos, apps needing a push, or what's changed across the suite.
allowed-tools: Bash
---

Show current fleet status across all managed apps.

## Fleet status

!`cd ~/dev/awesome-taskwarrior && python3 make-awesome.py --fleet 2>&1`

## Instructions

Read the output above and give a focused summary:

- **Dirty repos** — which apps have uncommitted changes, and roughly what changed
  (run `git -C <path> diff --stat` for any dirty repo if more detail is needed)
- **Checksum mismatches** — which apps have drifted from their `.meta` checksums
- **Skipped apps** — list them and note why (skip=yes in awesome.rc)
- **Clean apps** — just a count is fine

If the user asked a specific question about the fleet (e.g. "which apps need pushing?"),
answer that directly from the output rather than giving a full summary.
