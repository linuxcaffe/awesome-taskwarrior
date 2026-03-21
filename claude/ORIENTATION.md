# Claude Code Orientation — awesome-taskwarrior ecosystem

This document is written for Claude Code sessions working in this repo.
Read this before touching any code.

---

## Who you're working with

**djp** (GitHub: linuxcaffe) is the designer of the awesome-taskwarrior ecosystem
and the hooks/extensions within it. He has deep Taskwarrior expertise — treat him
as the domain authority. He almost always invokes Taskwarrior via `tw`, not `task`
directly. He uses `nb` (the Note Bene CLI notebook) alongside Taskwarrior.

---

## What this project is

**awesome-taskwarrior** is two things at once:

1. **`tw`** — a transparent drop-in wrapper for the `task` command, with a package
   manager, interactive shell, context multiplexing, dot-shortcuts, debug
   infrastructure, and pager/attach features.

2. **A registry** of Taskwarrior extensions (hooks, scripts, wrappers, configs).
   The registry points to independent repos; it does not duplicate their files.
   Each extension installs cleanly into `~/.task/` and can be removed without
   residue via the manifest.

**Version target: Taskwarrior 2.6.2 only.** v3.x is a hard boundary — it
introduces massive breaking changes and is out of scope for this project entirely.
Do not suggest or write code targeting v3.x.

---

## The `tw` command — key facts

- Located at `~/dev/awesome-taskwarrior/tw` (dev mode) and installed to
  `~/.task/scripts/tw`
- ~4000 lines of Python 3, currently v2.10.1
- Every `task` command passes through transparently: `tw list` == `task list`
- Has its own flags (`-I`, `-r`, `-u`, `-l`, `-s`, `--debug`, etc.)

### Flag-parsing bug — fixed
tw flags are resolved before pass-through args reach argparse, so task modifier
args like `tw 7 mod -lena` no longer misparse `-l` as `--list`.

### Pager (`-p`) — partial
`tw -p list` routes output through `less`, but Taskwarrior's pipe-detection
truncates output even with `rc.limit=0`. Not critical; workaround is the user's
`tless()` shell function. See `dev/pager-debug-status.md`. Don't re-investigate
this unless specifically asked.

---

## Extension architecture

```
registry.d/<name>.meta       — metadata (version, type, files, checksums, tags)
installers/<name>.install    — standalone bash installer (curl-based, no git)
lib/tw_hook_lib.py           — shared Python utilities for hooks
lib/tw-common.sh             — shared bash utilities for installers
```

Key conventions:
- GitHub repo name: `tw-<name>_<desc>-hook` / `tw-<name>-sh`
- Registry name: `<name>-<desc>` (e.g. `recurrence-overhaul`)
- Install dir: `~/.task/hooks/<name>/` with symlinks from `~/.task/hooks/`
- Every installer works **standalone** (`bash myapp.install install`) without `tw`
- Manifest at `~/.task/.tw_manifest` tracks every installed file for clean removal

### Hook API (Taskwarrior)
Hooks receive JSON on stdin, output JSON on stdout:
```python
import json, sys
task = json.load(sys.stdin)
# ... process ...
json.dump(task, sys.stdout)
```
Hooks fire on `on-launch`, `on-add`, `on-modify`, `on-exit`. Use `rc.hooks=off` when calling
`task` from inside a hook to prevent recursion.

---

## Extension status

### Working / stable
- `recurrence-overhaul` — replaces native recurrence; periodic + chain patterns
- `subtask` — `- [ ] …` annotations become real dependent tasks
- `timelog` — start/stop → hledger-compatible timeclock
- `need-priority` — Maslow's hierarchy replaces pri:H/M/L
- `sanity-check` — interactive fix for overdue, conflicts, broken deps
- `annn` — annotation manager
- `t` — hledger timeclock CLI
- `resched`, `urgency-tweaker`, `agenda-edate`, `tod-filter`, and others

### Not yet ready
- **`nicedates`** — filter wrapper, not finished
- **`tw-vim`** — Vim plugin; see `~/.nb/claude/tw-vim_future_improvements.md`

### Recently worked on (check nb/claude session notes)
- **`tw-gtk`** — GTK UI via YAD, active development; see
  `~/.nb/claude/tw-gtk_session_notes_2026-03-14.md` for recent fixes

---

## Development pipeline: `make-awesome.py`

`make-awesome.py` preps and packages extensions for the registry. Stages:
- `--debug` — injects TW_DEBUG / logging infrastructure into hook scripts
- `--timing` — injects TW_TIMING blocks for per-hook profiling
- `--meta` — generates/updates the `.meta` registry entry
- `--install` — generates the `.install` bash script
- `--push` — git commit + push + registry update

Run the full pipeline:
```bash
python3 make-awesome.py "Commit message here"
```

Stages can be run individually. `--testing` and `--stdhelp` are stubs (not yet
implemented).

---

## Directory layout (this repo)

```
tw                  — main script (package manager + wrapper)
make-awesome.py     — dev pipeline tool
registry.d/         — .meta files (one per extension)
installers/         — .install bash scripts (one per extension)
lib/                — tw_hook_lib.py, tw-common.sh, tw_condition_lib.py
dev/                — development notes, old versions, debug tools
  Claude_notes.txt  — quick bug/issue notes from sessions
  DEVELOPERS.md     — full architecture guide
  API.md            — hook and wrapper API reference
  make-awesome-py-GUIDE.md — pipeline tool guide
claude/             — Claude Code session docs (this dir)
QUICKSTART.md       — user quickstart
CONTRIBUTING.md     — contribution workflow
```

---

## Session history / nb notes

Past Claude Code sessions leave notes in `~/.nb/claude/`. Always check there
for context before starting work on a component:

```bash
nb claude:list      # see all notes
nb claude:show <id> # read a note
```

Current notes:
- `nb_plugin_development_—_hard-won_patterns.md` — nb plugin pitfalls (bash TUI,
  set -e gotchas, ANSI encoding, .index file format)
- `tw-gtk_session_notes_2026-03-14.md` — tw-gtk bug fixes and pending work
- `tw-vim_future_improvements.md` — lazy-load startup, launcher arg passing

### Note format convention

Every nb/claude note should include the Claude Code **session/chat ID** at the
top, so sessions can potentially be resumed:

```markdown
# <title>

session: <chat-id>
date: YYYY-MM-DD

...
```

Get the current session ID from the CLI with:

```bash
cat ~/.claude/sessions/*.json
```

Including it means a future session can reference exactly which conversation
produced the notes.

---

## Development & testing workflow

1. **Edit files in `~/dev/<project>/`** — that's the source of truth
2. **Copy changed files to `~/.task/` for immediate testing** — find the installed
   path with `find ~/.task -name <filename>`, then `cp dev/file ~/.task/path/file`
3. **When ready for a version bump**, tell the user: "run the pipeline"
   - User runs: `cd ~/dev/<project> && ../awesome-taskwarrior/make-awesome.py "msg"`
   - This handles debug injection, meta generation, installer generation, git push
4. **User installs the new version**: `tw -u <appname>`
5. **Never skip the copy step** — the user tests against installed files, not dev files

---

## Starting a session

At the start of every Claude Code session working in this ecosystem:

1. Get the session ID: `cat ~/.claude/sessions/*.json`
2. Read this file and any relevant nb/claude notes
3. At the end of the session (or when significant work is done), create a note
   in `~/.nb/claude/` that includes the session ID, date, what was done,
   artefacts created, and **any technical problems solved** — bugs hit, root
   causes found, non-obvious fixes, API gotchas, design decisions made. Future
   sessions on the same app should start by reading its note.

This ensures sessions can be cross-referenced even when resume fails.

---

## How to approach work here

- **Read before writing.** djp designs; Claude implements. Understand the existing
  pattern before proposing changes.
- **Standalone installers first.** Any new extension must have a working
  `bash myapp.install install` path that doesn't depend on `tw`.
- **Never `git clone` into `~/.task/`.** `~/.task` must not contain nested
  git repos — Taskwarrior owns that directory. All installers use `cp` to
  place files there. `git clone` is fine for nb plugins (`~/.nb/.plugins/`)
  and vim plugins, but not for anything going under `~/.task/`. The
  `#HANDCRAFTED` installer pattern exists precisely to enforce this: files
  are fetched/copied from outside, then installed via plain file copy.
- **No TW 3.x code, ever.** Not even a comment about it unless asked.
- **ASCII over unicode** in user-facing output. Past unicode corruption forced a
  full pass replacing `✓` with `[+]`, `✗` with `[X]`, etc.
- **Minimal subprocesses.** tw v2.10+ moved to direct `.taskrc` parsing. Don't
  reintroduce subprocess spawns where direct file reads work.
- **Check dev/ docs** before assuming — there are detailed notes on architecture
  decisions, timing, registry design, and naming conventions.
- **Save session notes to nb** when significant patterns or bugs are found:
  `nb add --notebook claude "title"` then edit.
