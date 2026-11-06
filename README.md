- Project: https://github.com/linuxcaffe/awesome-taskwarrior
- Issues:  https://github.com/linuxcaffe/awesome-taskwarrior/issues

# awesome-taskwarrior

A handy shortcut for task (`tw`) that features a shell mode, debug utility,
and package manager for Taskwarrior extensions.

---

## TL;DR

- Drop-in wrapper for `task` — all task commands pass through transparently
- Package manager for hooks, scripts, configs, and docs
- Interactive shell with persistent modifiers and context multiplexing
- Dot-shortcuts, context shortcuts, file attachments, auto-paging
- Self-installing, self-updating, self-contained under `~/.task/`
- Taskwarrior 2.6.2 — not compatible with v3.x

---

## Why this exists

Taskwarrior is powerful out of the box, but extending it means managing hook
scripts, configuration snippets, documentation, and directory structures by
hand. Installing someone else's hook usually means reading a README, copying
files, setting permissions, editing `.taskrc`, and hoping nothing breaks.

`tw` wraps `task` transparently — every command you'd normally give `task` works
identically — while adding a registry-based package manager, an interactive
shell, and a growing set of shortcuts that make daily use faster.

---

## Features

- **Package manager**
  Install, update, remove, and verify Taskwarrior extensions from a central
  registry. Each extension is self-contained and independently installable.

- **Transparent wrapper**
  `tw list`, `tw add`, `tw 42 done` — everything passes straight through to
  `task`. You don't give anything up by using `tw` instead.

- **Interactive shell**
  Persistent modifiers, readline history, context multiplexing, and shell
  command execution without leaving the session.

- **Context multiplexing**
  Combine multiple Taskwarrior contexts simultaneously with `@+` and `@-`,
  or use one-shot overrides with `@:` and `@_`.

- **Dot-shortcuts**
  Refer to recent tasks without looking up IDs — `.` for last added,
  `..` for last modified, `...` for last completed, `....` for last deleted.

- **Auto-paging**
  Long output can be automatically paged through `less` when it exceeds
  terminal height.

- **File attachments**
  Attach files to tasks via the ranger file browser, stored as annotations.

- **Debug infrastructure**
  Three debug levels with color-coded output, file logging, and per-session
  log files under `~/.task/logs/debug/`.

- **Shell completions**
  Tab completion for bash, zsh, and fish — auto-generated or manually
  installable.

- **Safe updates**
  `tw -u` preflight-downloads new files before touching the old version.
  If anything fails, the working version stays intact.

---

## Quick install

```bash
curl -fsSL https://raw.githubusercontent.com/linuxcaffe/awesome-taskwarrior/main/install.sh | bash
```

This installs `tw` to `~/.task/scripts/tw`, adds the scripts directory
to your PATH, and sets up documentation in `~/.task/docs/`.

No Taskwarrior 2.6.2 yet (or a 3.x your distribution brought)? `tw -I taskwarrior` installs it: the
`task2` deb on Termux, a build into `~/.local` on Linux, from
[taskwarrior-2.6](https://github.com/linuxcaffe/taskwarrior-2.6). The web UI: `tw -I tw-web`.

Verify with:

```bash
tw -v
```
View the available options with
```bash
tw -h
```

---

## Usage

### As a task wrapper

Anything you'd type after `task`, you can type after `tw`:

```bash
tw list                     # same as: task list
tw add Fix login bug +work  # same as: task add ...
tw 42 done                  # same as: task 42 done
```

### Package manager

```bash
tw -l                       # List available extensions
tw -I recurrence-overhaul   # Install an extension
tw -u recurrence-overhaul   # Update (safe: preflight staging)
tw -r recurrence-overhaul   # Remove an extension
tw -i recurrence-overhaul   # Show extension info
tw --verify recurrence-overhaul  # Verify checksums
```

### Context shortcuts

```bash
tw @                        # List availble contexts
tw @ work                   # Switch to work context
tw @0                       # Context none (clear)
tw @?                       # Context show (details)
tw @: personal list         # One-shot: list with personal context
tw @_ next                  # One-shot: next with no context
tw @+ work                  # Add work to context multiplexing set
tw @- morning               # Remove morning from cmx set
```

### Dot-shortcuts

```bash
tw add Fix the login bug +work
tw . annotate "See ticket #1234"    # . = last added task
tw . start

tw 42 modify priority:H
tw .. due:tomorrow                  # .. = last modified task

tw 15 done
tw ... (w. no args runs info)       # ... = last completed (by UUID)

tw ....                             # .... = last deleted (by UUID)
```

### Interactive shell

```bash
tw -s                       # Start shell
tw> list +work              # Task commands
tw> :push +work proj:acme   # Persistent modifiers
tw +work proj:acme> next    # Modifiers applied automatically
tw +work proj:acme> !ls     # Shell commands with ! or exec
tw +work proj:acme> !!      # Repeat last shell command
tw +work proj:acme> :pop    # Remove modifiers
tw> :q                      # Quit
```

### Pager and attachments

```bash
tw -p list                  # Auto-page long output
tw -A 42                    # Attach file to task 42 (via ranger)
```

### Debug

```bash
tw --debug list             # Level 1: basic operations
tw --debug=2 -I myapp       # Level 2: detailed + file ops
tw --debug=3 next           # Level 3: everything + TW hooks
```

Logs are written to `~/.task/logs/debug/`.

---

## Directory structure

After installation:

```
~/.task/
├── hooks/                  # Taskwarrior hooks
│   ├── on-add_recurrence.py
│   └── on-exit_recurrence.py
├── scripts/                # Wrapper scripts
│   ├── tw                  # The package manager / wrapper
│   └── rr                  # Extension scripts
├── config/                 # Configuration files
│   ├── .tw_manifest        # Installation tracking
│   └── recurrence.rc       # Extension configs
├── docs/                   # README files
│   └── recurrence_README.md
└── logs/
    └── debug/              # Debug session logs
```

---

## How it works

awesome-taskwarrior is a **registry** that points to extension repositories.
Extension files stay in their own repos — no duplication, no sync issues.

When you install an extension:

1. `tw` fetches the `.install` script from the registry
2. The installer downloads files from the extension's own repo via curl
3. Files are placed directly where Taskwarrior expects them
4. A manifest tracks every installed file for clean removal

Each installer is **standalone** — it works with or without `tw` installed.
Users can always run `bash myapp.install install` directly.

Updates use **preflight staging**: all new files are downloaded and verified
in a temp directory before the old version is touched. If anything fails,
the working version is restored automatically.

---

## Available extensions

Run `tw -l` to see the current registry, or browse:

<!-- extensions: written by make-awesome.py --index from registry.d/*.meta; edit those, not this list -->

### Hooks

- [agenda-edate](https://github.com/linuxcaffe/tw-agenda-hook) v1.1.1 — Creates "effective date" from due, sched, wait and until, Adds new agenda reports
- [daily-email](https://github.com/linuxcaffe/tw-daily-email) v0.1.1 — Send a daily Taskwarrior report by email via msmtp and systemd timer
- [gittw](https://github.com/linuxcaffe/gittw) v0.3.8 — Git-based sync and history for ~/.task across stations (merge by task UUID, station-tagged commits, last seen, gc at sync): gittw sync/push/pull/undo/status/setup, plus an on-exit hook that commits after every change (gittw.autocommit in config/gittw.rc; hook-ctrl to remove it)
- [hledger-add](https://github.com/linuxcaffe/tw-hledger-add-hook) v0.1.3 — Fires hledger add interactively on completion of +txn/+acct tasks or tasks starting with a trigger verb (pay, buy). Pre-fills date and payee from task description; maps TW project/priority/tags to hledger inline tags. Annotates task with ledger reference on success.
- [nb-plugins](https://github.com/linuxcaffe/nb-plugins) v1.3.0 — nb plugins: cal (a calendar), grep, send, and tw (Taskwarrior task notes: nb tw). Installs them into nb when nb is here
- [nbnotes](https://github.com/linuxcaffe/tw-nbnotes-hook) v1.0.1 — Task notes in nb: a bare `nb:` annotation (or `nb: <notebook>:`) gets the task its note, made at once; a task that links a note keeps the note's status current. Calls nb-plugins' tw.nb-plugin.
- [need-priority](https://github.com/linuxcaffe/tw-need_priority-hook) v0.6.3 — Replace pri:H,M,L with pri:1-6, Mazlow's Human Needs, and filter accordingly
- [recurrence-overhaul](https://github.com/linuxcaffe/tw-recurrence_overhaul-hook) v3.1.1 — Replaces task recurrence, offers periodic and chain type recurrences, supporting due, sched, wait and until attributes
- [smart-nag](https://github.com/linuxcaffe/tw-smart-nag-hook) v1.3.3 — Dynamically generated nag massages, based on configurable conditions
- [stop-started](https://github.com/linuxcaffe/tw-stop-started-hook) v1.1.0 — Stop other active tasks when a new task is started — enforces one active task at a time
- [subtask](https://github.com/linuxcaffe/tw-subtask-hook) v1.2.5 — Activates subtask annotations (- [ ] …) as real dependent tasks when a parent task is started; updates annotation state when children complete or are deleted
- [time-defaults](https://github.com/linuxcaffe/tw-time-defaults-hook) v1.0.2 — Apply configurable default times to date-only due, scheduled, wait, and until fields
- [timelog](https://github.com/linuxcaffe/tw-timelog-hook) v2.2.0 — Records task start/ stop times to an hledger-compatible timeclock file
- [tod-filter](https://github.com/linuxcaffe/tod-filter) v0.1.2 — Define blocks of time, add corresponding filters, apply context tod, hide non-matching tags
- [tw2ical](https://github.com/linuxcaffe/tw-ical-hook) v0.2.0 — Export Taskwarrior tasks to VTODO .ics files for CalDAV/khal/Radicale
- [tw2nb](https://github.com/linuxcaffe/tw2nb) v1.5.1 — Archives Taskwarrior task events (done, log, delete, annotate) to nb as todos and running journal entries. Works with nb tw tasknotes: the tasknote is the archive (the nbnotes hook makes and updates task notes).
- [wikitags](https://github.com/linuxcaffe/tw-wikitags-hook) v1.0.0 — task add :tags: :in-line: with desc - same as task add tags in-line with desc +tags +in-line

### Wrappers

- [annn](https://github.com/linuxcaffe/tw-ann-hook) v0.8.0 — Opens annotations in your editor, add, list or remove them with easy syntax
- [deps-mgmt](https://github.com/linuxcaffe/tw-deps-mgmt-hook) v0.3.0 — Manage completion and deletion of tasks with dependencies and display dep trees
- [events](https://github.com/linuxcaffe/tw-events) v0.4.0 — The calendar's non-task entries as Taskwarrior holiday.* entries (task calendar, tw-web): holidays from holidata.net, moon phases, solstices and equinoxes, clock changes, your own events and ghosts of tasks; events init/refresh/show/check/add, task events
- [mobilize](https://github.com/linuxcaffe/tw-mobilize) v0.10.3 — Set up a Taskwarrior 2.6.2 station (Android in Termux, or Linux) from your gittw repo, with tw-web on it: mobilize init/check/hooks/stations/android/-e; mobilize.rc (shared) and local.rc (per station)
- [theme-select](https://github.com/linuxcaffe/tw-theme-select) v0.6.3 — ncurses TUI for previewing and selecting Taskwarrior color themes, with per-report theme switching

### Scripts

- [gtk](https://github.com/linuxcaffe/tw-gtk) v1.2.2 — GTK GUI library and extensions for Taskwarrior, powered by YAD
- [hook-ctrl](https://github.com/linuxcaffe/tw-hook-ctrl) v0.3.3 — Three-panel TUI dashboard: toggle hooks (chmod), scripts (chmod), and config includes (comment toggle) — unified control over all installed Taskwarrior capabilities
- [matrix-taskbot](https://github.com/linuxcaffe/tw-matrix-bot) v0.2.0 — Matrix bot for Taskwarrior — query and add tasks from any Matrix client
- [powerline-taskwarrior](https://github.com/linuxcaffe/powerline-taskwarrior) v2.0.2 — Powerline segments for Taskwarrior — context, active task, next task, pending count
- [resched](https://github.com/linuxcaffe/tw-sched-sh) v1.0.0 — Review and update stale-dated tasks
- [sanity-check](https://github.com/linuxcaffe/tw-sanity-check) v0.6.1 — Interactively review and fix common Taskwarrior problems (overdue, stale deps, date conflicts) with hotkeys to select (configurable) options, or edit the task directly.
- [t](https://github.com/linuxcaffe/t) v1.4.0 — t is for timelog. A handy script to track your time using hledger timelog files
- [taskwarrior](https://github.com/linuxcaffe/taskwarrior-2.6) v2.6.2-2 — Taskwarrior 2.6.2 on this station, from the taskwarrior-2.6 repo: the task2 deb on Termux (pkg upgrade never swaps it for 3.x), a build of the 2.6.2 release into ~/.local on Linux (no sudo); a 3.x is replaced only on a yes, its tasks saved first. taskwarrior-2.6 does it again on any station sharing ~/.task
- [tw-tui](https://github.com/linuxcaffe/tw-tui) v25.4-tw26 — Terminal UI for Taskwarrior 2.6.x — fork of taskwarrior-tui pinned to last TW2 compatible version
- [tw-web](https://codeberg.org/linuxcaffe/tw-web) v2.0.0 — tw-web, the web and phone UI for Taskwarrior 2.6.2 (List, Kanban, Agenda, Calendar; a PWA): a git clone from Codeberg (else GitHub) in ~/.local/share/tw-web with its Python packages (a venv where pip is refused), updated in place by tw -u (fast-forward, clean main); a checkout named in local.rc (tw-web.dir) is used as it is
- [urgency-tweaker](https://github.com/linuxcaffe/urgency-tweaker) v1.0.0 — ncurses app to help you understand and tweak your urgency coefficients
- [vit](https://github.com/linuxcaffe/vit) v1.4.5 — Full-screen terminal interface for Taskwarrior 2.6.x with Vim key bindings: any report in curses, a key per change, acts by UUID, no shell between vit and task, the fleet's client contract (VIT 1.x, Perl/Curses)

<!-- /extensions -->

---

## For developers

See [DEVELOPERS.md](DEVELOPERS.md) for the full guide on creating extensions,
the `.meta` file format, installer templates, and the curl-based architecture.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution workflow.

The development pipeline tool `make-awesome.py` handles debug enhancement,
installer generation, and git/registry push in a single command.

---

## Project status

Active development. Core functionality is stable and in daily use.

The package manager, wrapper, shell, and context multiplexing are working.
Extensions are being added to the registry as they reach stable status.

---

## Metadata

- License: MIT
- Language: Python
- Requires: Taskwarrior 2.6.2, Python 3.6+, curl, bash
- Optional: ranger (for file attachments), less (for paging)
- Version: 2.7.0
