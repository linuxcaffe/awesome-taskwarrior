---
name: awesomeness
description: Project orientation for awesome-taskwarrior — vision, philosophy, fleet status, and dev environment overview. Invoke at the start of a session or when orienting a new collaborator.
triggers:
  - /awesomeness
  - "what is awesome-taskwarrior"
  - "project overview"
  - "orient me"
---

## awesome-taskwarrior — Project Vision

**What it is:** A personal, opinionated ecosystem of Taskwarrior hooks, wrappers, scripts, and integrations — built by one person, for one person, and shared freely with anyone it fits.

**Core philosophy:**
- Taskwarrior is already powerful. The goal is to *extend* it, not replace it.
- Every tool should do one thing well and compose cleanly with the others.
- "Dogfood first" — the dev/test environment runs the latest version of every app.
- Hooks are small, fast, and non-destructive by default.
- The fleet is managed by `make-awesome.py` — a single pipeline tool: `--meta --install --push`.

**What it is NOT:**
- Not a product to sell or aggressively promote.
- Not a rewrite of Taskwarrior.
- Not designed for mass deployment or enterprise use.
- Not finished (and that's fine).

---

## Fleet Overview

!`
MANIFEST=~/.task/config/.tw_manifest
if [ ! -f "$MANIFEST" ]; then
    echo "(manifest not found at $MANIFEST)"
    exit 0
fi

echo "=== INSTALLED FLEET (from .tw_manifest) ==="
# Extract unique app|version pairs, latest version per app
python3 - "$MANIFEST" << 'PYEOF'
import sys
from pathlib import Path

manifest = Path(sys.argv[1]).read_text().splitlines()
apps = {}
for line in manifest:
    parts = line.split('|')
    if len(parts) < 3:
        continue
    name, version = parts[0], parts[1]
    apps[name] = version  # last entry wins = most recent

for name, version in sorted(apps.items()):
    print(f"  {name:<30} v{version}")
PYEOF

echo ""
echo "=== DEV ENVIRONMENT ==="
echo "  TASKRC:      ~/.taskrc-dev"
echo "  TASKDATA:    ~/.task-dev/"
echo "  Git tracked: $(cd ~/.task-dev && git log --oneline | wc -l) commits"
echo "  Hooks:       $(ls ~/.task-dev/hooks/ | wc -l) files (hooks=off by default)"
echo "  Scripts:     $(ls ~/.task-dev/scripts/ | wc -l) files"
echo ""
echo "  td = TASKRC=~/.taskrc-dev task   (use for dev ops)"
echo "  tw  = ~/.task/scripts/tw          (production wrapper)"

echo ""
echo "=== FLEET SOURCE REPOS ==="
ls ~/dev/ | grep tw- | sed 's/^/  /'
`

---

## Key Paths

| Purpose | Path |
|---------|------|
| Production task data | `~/.task/` |
| Dev/test task data | `~/.task-dev/` |
| Production taskrc | `~/.taskrc` |
| Dev taskrc | `~/.taskrc-dev` |
| Fleet manager | `~/dev/awesome-taskwarrior/make-awesome.py` |
| Fleet registry (dev) | `~/dev/awesome-taskwarrior/registry.d/` |
| Fleet registry (installed) | `~/.task/awesome-taskwarrior/registry.d/` |
| Fleet ops config | `~/dev/awesome-taskwarrior/awesome.rc` |
| Consolidated includes | `~/.task/config/included.rc` |
| Skills | `~/.claude/skills/` |

## Key Skills

| Skill | Purpose |
|-------|---------|
| `/deploy` | Copy project files to `~/.task/` for live testing |
| `/ready` | Pre-pipeline checklist |
| `/version-check` | Verify version consistency |
| `/fleet` | Fleet-wide status |
| `/task-context` | Load active Taskwarrior task as session context |
| `/pty` | PTY subprocess patterns for capturing color output in curses TUI |
| `/awesomeness` | This overview |

## Pipeline Stage Order

```
gitignore → debug → testing → timing → envar → stdhelp → meta → install → push
```

- `make-awesome.py "message"` — full pipeline, no flags needed
- `make-awesome.py --envar --dry-run` — preview isolation patches safely before applying
- `StageReport` prints a structured report only when a stage encounters deviations or flags

## Dev Workflow Loop

```
td add "task description" +dev pro:tw   # create task in dev db (isolated)
td start <id>                            # make it active
/task-context                            # load it as session context
# ... hack, iterate ...
/deploy                                  # copy to ~/.task/ for live test
/ready                                   # pre-push checklist
make-awesome.py "commit message"         # full pipeline (no flags needed)
```

`td` sets `TASKRC=~/.taskrc-dev TW_TASK_DIR=~/.task-dev` — every op is a git commit in `~/.task-dev/`.
Run `TASKRC=~/.taskrc-dev task rc.hooks=on <cmd>` to test hooks against dev data.

## Registry and Fleet Architecture

### registry.d is canonical

`~/dev/awesome-taskwarrior/registry.d/*.meta` is the authoritative fleet index.
`awesome.rc` is a fleet **ops overlay** — it adds path, timing/debug flags, skip,
envar_ready, and status on top of what the registry already knows.

**Installed** registry lives at `~/.task/awesome-taskwarrior/registry.d/`.
Install status for `--fleet --list` is read from `~/.task/config/.tw_manifest` — that is the source of truth for what is installed and at what version.

### Naming convention

- GitHub repos: `tw-programname-type` (e.g. `tw-hook-ctrl`, `tw-agenda-hook`)
- Dev dirs: inherit repo name → `~/dev/tw-hook-ctrl`
- Canonical app name: `name=` field in `.meta` (e.g. `hook-ctrl`) — **no `tw-` prefix**
- `awesome.rc` section name **must** match `name=` in .meta; `path=` absorbs the `tw-` prefix

### awesome.rc fields

```ini
[canonical-name]                 # must match name= in .meta
path         = ~/dev/tw-appname  # dev dir — absorbs tw- naming prefix
type         = hook | script | wrapper | ui | core
timing       = yes | no          # eligible for --timing injection
debug        = yes | no          # eligible for --debug injection
skip         = yes               # exclude from ALL fleet ops
status       = release | testing | wip | suspended | archived
envar_ready  = yes | no          # updated for TW_TASK_DIR isolation
skip_testing = yes               # exempt from --fleet --testing gate only
tw_web       = yes | no | partial  # web context compatibility (see below)
```

**`tw_web` field** — tw-web sets `TW_WEB=1` in every subprocess (15s timeout).
- `yes` — fully compatible, no interactive elements
- `no` — uses `/dev/tty`, `fzf`, `hledger-add`, etc.; hook must guard with:
  ```python
  if os.environ.get('TW_WEB'):
      print(json.dumps(new_task)); sys.exit(0)
  ```
- `partial` — won't hang but some output doesn't reach web user (e.g. desktop notify)

Current `no` apps: `subtask`, `hledger-add`, `deps-mgmt` (guards already added), `theme-select`, `gtk`, `tw-tui`
Current `partial` apps: `smart-nag`, `gtk-notify`, `powerline-taskwarrior`

### Fleet list commands

```bash
make-awesome.py --fleet --list              # registry.d list with install status + update indicators
make-awesome.py --fleet --list hook         # filter by name pattern
make-awesome.py --fleet --query type=hook   # rich query (field=val, field:text, field!=val, freetext)
make-awesome.py --fleet --query tw_web=no   # find all web-incompatible hooks
make-awesome.py --fleet --discover          # find registry apps missing from awesome.rc
make-awesome.py --fleet --discover --apply  # write found entries into awesome.rc
make-awesome.py --fleet --grep PATTERN      # grep source files across fleet
make-awesome.py --fleet --ipush "message"  # interactive push: prompts version/tags per app
```

`--fleet --list` output columns: `[↑]/[*]/[ ]  NAME  TYPE  VER  STATUS  TAGS`

| Indicator | Meaning |
|-----------|---------|
| `[*]` | installed, up to date |
| `[↑]` cyan | installed, update available in registry |
| `[ ]` | not installed |

Footer: `(N) Available applications  ·  M installed  ·  K update(s) available`
Apps with `(no rc)` in status have a registry entry but no awesome.rc entry.
Install status is read from `~/.task/config/.tw_manifest` (not from registry.d files).

`tw -l` (the user-facing wrapper) shows the same indicators with `vINST→REGISTRY` version diff.

### New App: Cradle to Fleet

The full lifecycle for a new fleet app — from idea to `tw -I`:

```
1.  mkdir ~/dev/tw-<appname> && cd ~/dev/tw-<appname>
    git init && git remote add origin git@github.com:linuxcaffe/tw-<appname>.git

2.  Write the app. Write a minimal .meta file (name/version/type/description/files/tags)
    — pipeline will regenerate it with checksums, no need to be perfect

3.  git add -A && git commit -m "init: v0.1.0" && git push

4.  cd ~/dev/tw-<appname>
    python3 ~/dev/awesome-taskwarrior/make-awesome.py "init v0.1.0"
    — full pipeline (no flags): debug→test→meta→install→push
    — --push auto-copies .meta to registry.d/ and commits the registry repo

5.  tw -I <appname>
    — installs from GitHub into ~/.task/

6.  Add to awesome.rc fleet ops:
    python3 ~/dev/awesome-taskwarrior/make-awesome.py --add <appname>
    — or run --discover --apply if the dir already exists
```

**The `.meta` file is the handshake:**
- Local project: `~/dev/tw-<appname>/<appname>.meta` — pipeline input/output
- Registry: `~/dev/awesome-taskwarrior/registry.d/<appname>.meta` — pushed here by `--push`
- Installed: `~/.task/awesome-taskwarrior/registry.d/<appname>.meta`

## tw Wrapper Architecture

Wrappers extend `tw` without modifying its core. Registered in `~/.task/config/.tw_wrappers`:

```
keyword|script|description|type
```

**Three types:**

| Type | Trigger | How it works |
|------|---------|--------------|
| `command` | keyword found in args | `tw 42 ann` → dispatches to `annn 42` |
| `filter` | any report invocation | task runs via PTY → output piped through script |
| `pre-exec` | every pass-through | script called before task, then again after for cleanup |

**Design principle: never add app-specific code to `tw` core.** If a new app needs special behaviour at task invocation time, the right answer is a new generic wrapper type — not a one-off block in `pass_through_to_task()`.

### pre-exec protocol

`tw` calls the script twice per invocation via env vars (no positional args):

| Env var | Value |
|---------|-------|
| `TW_PRE_EXEC_PHASE` | `pre` (before task) or `post` (after, always — in `finally`) |
| `TW_REPORT` | detected report name, or `''` for non-report commands |
| `TW_PRE_EXEC_SESSION` | unique 12-char hex ID — use for state temp files |

- Exit non-zero on `pre` → task is aborted
- Multiple pre-exec wrappers run in registration order; post runs in reverse
- State between phases: write to `/tmp/tw-pre-exec-<session>.state`

**Example** (`theme-wrap.py`):
- `pre`: reads `report.list.theme=dark-green-256` from `themes.rc`, patches include line, saves original to state file
- `post`: reads state file, restores `themes.rc`, deletes state file

### themes.rc

`~/.task/config/themes.rc` — managed by `theme-select`. Two kinds of lines coexist:

```
# Per-report theme overrides (tw reads; task ignores unknown keys):
report.list.theme=dark-green-256

# theme-select manages these:
#include /path/to/dark-16.theme
include /path/to/dark-256.theme     ← active theme
```

`theme-select apply_theme()` preserves all non-include preamble lines when rewriting.

### Registering a wrapper app

Add to `~/.task/config/.tw_wrappers` (done automatically by the `.install` script):
```
theme|theme-wrap.py|Per-report theme switching|pre-exec
```

Remove on uninstall via `sed -i "/^theme|/d" .tw_wrappers`.

---

## included.rc — consolidated config includes (2026-04)

`~/.task/config/included.rc` is the preferred single place for all `include=` lines,
replacing scattered entries in `.taskrc`.

- `hook-ctrl` right panel shows the full include tree and toggles lines on/off
- `make-awesome.py --install` generates bash that checks for `included.rc` first,
  falls back to `.taskrc` — avoids duplicate includes
- Migration: `hook-ctrl` → right panel → `m` to migrate `.taskrc` includes to `included.rc`

## Recent app milestones (2026-04)

**hook-ctrl** (v0.3.2, `~/dev/tw-hook-ctrl`) — Three-panel ncurses TUI dashboard:
- Left: hooks (`~/.task/hooks/`) — chmod toggle enable/disable, symlink target shown
- Middle: scripts (`~/.task/scripts/`) — chmod toggle
- Right: include tree — walks `include=` lines in `.taskrc` / `included.rc` (depth=1),
  Space toggles comment char, `m` migrates includes to `included.rc`
- Tab cycles focus; `e`/`d` for hooks+scripts; `m` for includes panel

**theme-select** (v0.6.2, `~/dev/tw-theme-select`) — additions:
- `tw theme -l` / `--list` — numbered list of all discovered themes
- `tw theme N [task-args]` — one-shot theme override by number (no TUI)
- `:reportname` in TUI to change preview report live; `:q` to quit
- `theme-wrap.py` report detection: uses `TW_TASK_ARGS` (JSON list from `tw`)
  to positively match last bare word against configured `report.X.theme=` keys

**make-awesome.py** fleet improvements:
- `--fleet --list` now registry.d-driven: shows version, tags, install status
- `--fleet --list` shows `[↑]` (cyan) for update available; footer with app/install/update counts
- Install status read from `~/.task/config/.tw_manifest` (not registry.d presence)
- `--fleet --discover [--apply]` — easter egg hunt for dev dirs of registry apps
  missing from awesome.rc; `--apply` writes entries to awesome.rc
- `--fleet --query` now uses shared `_load_meta()` module-level helper
- `--fleet --ipush "message"` — interactive per-app push: prompts for version bump and
  tags before committing; hit Enter to accept defaults, skip unchanged apps
- Routing fix: all fleet sub-commands (`--list`, `--query`, `--discover`) work
  without explicit `--fleet` flag

**tw wrapper** (`~/dev/awesome-taskwarrior/tw`) — `tw -l` / `--list` updates:
- Shows `[↑]` cyan when an installed app has a newer version in the registry
- Version diff shown as `vINST→REGISTRY` for at-a-glance diff
- Footer: `(N) Available  ·  M installed  ·  K update(s) available  · [↑] = update`

**gittw** (`~/dev/gittw`) — git-based Taskwarrior sync:
- Replaces `task sync` (taskd) for single-user local+remote git workflow
- `on-exit_gittw.py` hook: auto-commits `~/.task/` after every task op
- "Do no harm" guards: skips if mid-merge/rebase, skips if working tree clean,
  all git errors swallowed silently — never surfaces to Taskwarrior
- `tw sync` → `gittw sync` via `tw-sync.sh` command wrapper (registered in `.tw_wrappers`)
- `git-crypt` for encrypted credential sync: `*.creds filter=git-crypt diff=git-crypt`
  in `~/.task/.gitattributes`; key distributed out-of-band

**tw-web** (`~/dev/WebTaskManager`) — hook/web compatibility (`TW_WEB=1`):
- Flask sets `TW_WEB=1` in every subprocess env (`_TW_ENV`) and enforces a 15s timeout
- Interactive hooks must guard: `if os.environ.get('TW_WEB'): print(json.dumps(new_task)); return 0`
- Affected apps with guards added: `subtask`, `hledger-add`, `deps-mgmt`
- Sync dialog: `/api/sync` POST → `gittw sync` (falls back to `task sync` if gittw absent)
- `/api/sync/info` GET → tells the UI which sync method is active
- Service worker cache key: `CACHE = 'tw-web-vN'` in `sw.js` — **must be bumped** on
  every JS/CSS change; stale SW is the #1 cause of "changes not showing up"
  - Firefox: `about:serviceworkers` → Unregister
  - Epiphany/GNOME Web: delete `~/.local/share/gnome-web/serviceworkers/` and restart

## make-awesome.py: Known Gotchas

### Branch verification probe file (chicken-and-egg)

`--meta` verifies the GitHub branch exists by probing a file via `curl`. The probe
now uses the **first file in `info.files`** (e.g. `hook-ctrl.py`) rather than
`README.md`, which may not exist on first pipeline run.

- `info.files` is a list of **tuples** `(name, ftype, dest)` — index with `[0][0]`
  (not `.split(':')[0]` which only works on raw strings from the `.meta` text)
- Both the main branch check and the alternatives loop use the same `probe_file`
- Fix location: `prompt_for_metadata()` ~line 1569

### `skip_testing` in `awesome.rc`

Apps can be exempted from the `--fleet --testing` gate (but not other stages) with:

```ini
skip_testing = yes
```

Shown as `NOTST` in `--fleet --list`. Useful for apps with no tests yet.

---

## Hook & Script Environment API

Every hook and script in the fleet may encounter any of these environment signals.
New apps must handle the full set; `envar_ready` in `awesome.rc` tracks compliance.

### Environment variables

| Var | Set by | Meaning |
|-----|--------|---------|
| `TW_WEB` | tw-web Flask (`_TW_ENV`) | Running inside web context (15s timeout, no TTY) |
| `TW_TASK_DIR` | `td` alias, test harness, envar stage | Override task data dir (isolation) |
| `TASKRC` | `td` alias, test harness | Override taskrc file |
| `TW_DEBUG` | `tw --debug=N` or `make-awesome.py --debug` | Debug verbosity level (int; `>= 2` = verbose) |
| `TW_TIMING` | `make-awesome.py --timing` | Enable atexit timing report |
| `TW_TASK_ARGS` | `tw` wrapper | JSON list of args passed to task (used by theme-select, filter wrappers) |
| `TW_PRE_EXEC_PHASE` | `tw` wrapper | `pre` or `post` phase signal for pre-exec wrappers |
| `TW_REPORT` | `tw` wrapper | Detected report name, or `''` |
| `TW_PRE_EXEC_SESSION` | `tw` wrapper | Unique 12-char hex — use as temp file key |
| `TIMELOG` | user | Override timeclock ledger path (used by timeclock hook) |

### Standard boilerplate patterns

**TW_WEB guard** (any hook that does interactive I/O or has side effects requiring a TTY):
```python
if os.environ.get('TW_WEB'):
    print(json.dumps(new_task))
    sys.exit(0)
```

**TW_TIMING atexit block** (injected by `--timing` pipeline stage — already in all fleet hooks):
```python
import os as _os_timing, time as _time_module
if _os_timing.environ.get('TW_TIMING'):
    import atexit as _atexit
    _t0 = _time_module.perf_counter()
    def _report_timing(_f=__file__):
        elapsed = (_time_module.perf_counter() - _t0) * 1000
        import os.path as _osp
        print(f"[timing] {_osp.basename(_f)}: {elapsed:.1f}ms", file=__import__('sys').stderr)
    _atexit.register(_report_timing)
```

**TW_DEBUG / TW_TASK_DIR** (injected by `--debug` / `--envar` pipeline stages — already in fleet hooks).
The `--envar` stage patches hardcoded `~/.task/` paths to respect `TW_TASK_DIR`:
```python
TASK_DIR = os.environ.get('TW_TASK_DIR', os.path.expanduser('~/.task'))
```

### Common pitfalls

- **File encoding**: always open ledger/log files as text with explicit `encoding="utf-8"` —
  never call `.encode('utf-8')` on the string and pass bytes to a text-mode file handle.
- **stdout discipline**: hooks communicate with Taskwarrior via `print(json.dumps(task))`.
  Any other `print()` goes to stderr (Taskwarrior shows it as a warning). When `TW_WEB=1`,
  stderr is swallowed; use `TW_DEBUG` log files for diagnostics instead.
- **Timeout awareness**: tw-web enforces a 15s hard timeout. Hooks that shell out to
  external tools (hledger, fzf, notify-send) must guard with `TW_WEB` or they will hang.

### Testing hooks called non-interactively

`TaskTestCase` runs `task` via subprocess — exactly as tw-web does. Side effects
(file writes, ledger entries) are testable; `print()` output is captured and ignored.
Pattern:
```python
self.t.task('1', 'start')
self.t.task('1', 'stop')          # triggers on-modify hook
ledger = Path(self.t.taskdata) / 'timelog' / 'tw.timeclock'
self.assertIn(' i ', ledger.read_text())   # assert side effect, not stdout
```
For hooks that check `TW_WEB`, set it in the test environment:
```python
os.environ['TW_WEB'] = '1'
# ... run task command ...
os.environ.pop('TW_WEB', None)
```

---

## Guiding Constraints

1. **Never touch production taskd sync** — no WingTask credentials in dev config
2. **hooks=off by default** in dev — enable explicitly: `TASKRC=~/.taskrc-dev task rc.hooks=on ...`
3. **`~/.task-dev/` is git-tracked** — every state change is auditable
4. **`tw` script reads from GitHub** — local changes need a push to be picked up by `tw`
5. **`.tw_manifest` is the source of truth** for what's installed and when
