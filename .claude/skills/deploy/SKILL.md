---
name: deploy
description: Copy current project files to ~/.task/ for live testing. Use when the user says "deploy", "copy to task", "ready to test", or "cp to hooks".
allowed-tools: Bash, Read, Glob
argument-hint: "[filename] (optional — deploy one file only)"
---

Deploy the current project to `~/.task/` for live testing.

## Project state

Project: !`basename $(pwd)`

Meta file:
!`ls *.meta 2>/dev/null | head -1 | xargs cat 2>/dev/null || echo "(no .meta found — are you in the right project directory?)"`

## Instructions

Parse the `files=` line from the meta above. Each entry is `filename:type`.

Destination rules:
- `:hook`   → `~/.task/hooks/`    (also `chmod +x` after copy)
- `:script` → `~/.task/scripts/`
- `:config` → `~/.task/config/`   (only if file doesn't already exist there — don't overwrite user config)
- `:doc`    → `~/.task/docs/`

If `$ARGUMENTS` names a specific file, deploy only that file.
Otherwise deploy all files listed in `files=` **except** `:config` entries
(config files are set up once at install time and should not be overwritten during development).

For each file deployed:
1. Run `cp <file> <destination>`
2. For hooks: `chmod +x <destination>/<file>`
3. Confirm with the full destination path

After deploying, remind the user to test (e.g. `task add "test deploy" +test` for an on-add hook)
and to say "ready for pipeline push" when satisfied.
