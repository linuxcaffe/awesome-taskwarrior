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
  Long output is automatically paged through `less` when it exceeds
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

Verify with:

```bash
tw -v
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
tw .. info                          # .. = last modified task

tw 15 done
tw ... info                         # ... = last completed (by UUID)

tw .... info                        # .... = last deleted (by UUID)
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

- [tw-recurrence](https://github.com/linuxcaffe/tw-recurrence_overhaul-hook) — Advanced recurrence with chained and periodic patterns

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
