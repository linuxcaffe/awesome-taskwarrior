# ORIENTATION — Working with Claude on this project

## Dev/Deploy Workflow

**Claude's role:**
- Write and edit code in `~/dev/<project>/`
- Suggest `cp` to `~/.task/` for live testing when appropriate
- Signal when code is ready: _"ready for pipeline push"_
- Do NOT run `make-awesome.py` pipeline stages
- Do NOT run `git push` on project repos (except awesome-taskwarrior registry syncs when explicitly asked)

**djp's role:**
- Run the pipeline: `make-awesome.py --meta --install --push "message"`
- Update version numbers in `.meta` and `.install` during pipeline run
- Spot-check the human-facing parts of install/update/remove
- Catch weirdnesses before they go to GitHub

## Why This Split

The pipeline (`--meta → --install → --push`) has interactive prompts and
human judgement calls (version bump size, description wording, tags). It
also catches things like the installer VERSION= drift we hit — the user
sees "Installing v0.1.2" when meta says v0.1.5 and can catch it immediately.

Running it yourself also tests the actual install UX that end users see.

## Version Sync Rule

When bumping a version, three places must match:

| File | Key |
|------|-----|
| `appname.meta` | `version=X.Y.Z` |
| `appname.install` | `VERSION="X.Y.Z"` (and comment on line above) |
| `appname.py` (if script) | `VERSION = 'X.Y.Z'` |

The pipeline `--meta` stage sets the meta version interactively.
The `--install` stage regenerates the installer — which resets VERSION correctly.
If using a HANDCRAFTED installer, bump VERSION manually before pushing.

## Installer: Generated vs HANDCRAFTED

- **Generated** (by `make-awesome.py --install`): VERSION is auto-set from meta. Safe.
- **HANDCRAFTED** (header comment says so): VERSION must be manually kept in sync.
  When in doubt, check the header comment at the top of the `.install` file.

## Live Testing Pattern

```
# Claude edits ~/dev/matrix-taskbot/matrix-taskbot.py
cp ~/dev/matrix-taskbot/matrix-taskbot.py ~/.task/scripts/
# restart bot, test
# iterate until working
# Claude says: "ready for pipeline push"
# djp runs: cd ~/dev/matrix-taskbot && make-awesome.py --meta --install --push "message"
```

## Registry Sync

After a successful pipeline push on a project repo, the registry
(`awesome-taskwarrior/registry.d/` and `installers/`) needs syncing.
This is handled automatically by `make-awesome.py --fleet --push` for
fleet apps. For standalone project pushes, sync manually or ask Claude
to do it after you confirm the project push succeeded.

## Where Claude's Notes Live

| Location | Type | Purpose |
|----------|------|---------|
| `~/.claude/projects/-home-djp/memory/` | Auto-memory | Persists across conversations: user profile, feedback rules, project context, references. Indexed by `MEMORY.md`. Claude reads/writes this automatically. |
| `~/.nb/claude/` (= `~/dev/awesome-taskwarrior/claude/`) | nb notebook | Session notes, hard-won patterns, future improvement lists. Written during or after sessions. nb mirrors both paths. |
| `~/dev/awesome-taskwarrior/dev/Claude_notes.txt` | Ad-hoc scratch | Quick one-off notes, bug snippets, things that didn't fit elsewhere. |
| `~/dev/awesome-taskwarrior/dev/ORIENTATION.md` | This file | Workflow rules and conventions. |
| `~/dev/CLAUDE.md` | Claude Code config | Project-wide instructions loaded automatically by Claude Code at session start. Authoritative for build commands, architecture, conventions. |
| `~/dev/<project>/claude/` | Per-project notes | Occasional deep-dive notes scoped to a specific project. |

**Priority order when they conflict:** CLAUDE.md > memory/ > ORIENTATION.md > nb notes

**Claude should check** `memory/MEMORY.md` at the start of any session involving this project,
and write new session notes to `nb claude:` for anything worth preserving long-term.

## Known Gotchas

- `rstrip('.git')` bug in `--meta` repo name prompt — **fixed** in make-awesome.py
  (use exact match, not substring, for duplicate import detection)
- Debug re-injection eating `import os as _os_timing` — **fixed** in make-awesome.py
- HANDCRAFTED installer VERSION drift — catch at pipeline time by reading the
  "Installing appname vX.Y.Z..." line in the output
