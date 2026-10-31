# Fleet conventions

How the awesome-taskwarrior fleet fits together: the contract between Taskwarrior **clients** (tw-web,
tw-gtk, anything that runs `task` without a terminal) and **hooks**, plus the shared rules for
environment, configuration, packaging and tests.

Taskwarrior **2.6.2** is the spec. Nothing here applies to 3.x.

This file is the reference. Hook and client READMEs link here rather than restating it, and tw-web's
`tests/test_contract.py` checks tw-web's side against the examples below.

*Written 2026-10-13. Change it in the same commit as any code that changes the contract.*

---

## 1. Client → hook: the environment

A client that runs `task` **without a terminal** sets these on every call. Hooks read them; they never
set them.

| Variable | Value | Meaning |
|---|---|---|
| `TW_NOINTERACT` | `1` | **No terminal.** The one gate: a hook must not prompt, open `/dev/tty`, or launch an interactive program. |
| `TW_CLIENT` | `web`, `gtk`, `vit`, … | Which client is calling. Informational: for wording or client-specific extras, never to decide whether to prompt. (One extra: tw's `tw.ui=vit` mode stands aside under `TW_CLIENT=vit`, so a `tw` started from inside vit never opens a second vit. That's which program shows a report, not whether to prompt.) |
| `TW_WEB` | `1` | Legacy alias of `TW_NOINTERACT`, set by tw-web only. Hooks written before `TW_NOINTERACT` check it. New hooks check `TW_NOINTERACT`. |
| `TW_SPOOL_DIR` | a directory | Where a hook may leave a deferred command (see §3). Private to the client (mode 0700); never assume a path. |
| `TW_PREFLIGHT_CMD` | `12 done` | The command as the user would type it after `task`. Used in signals so the client can offer to run it in a terminal. |
| `TW_PREFLIGHT_VERB` | `modify` | Bulk-operation check: the command's verb. |
| `TW_PREFLIGHT_FILTER` | `project:home` | Bulk-operation check: the filter, space-separated. |
| `TW_PREFLIGHT_CONFIRMED` | `1` | The user has already confirmed this bulk operation; don't block it again. |
| `TW_PREFLIGHT_THRESHOLD` | `3` | Optional: task count at which a bulk-operation guard blocks. (Its one implementation, nointeract-preflight, was retired 2026-10-26.) |

**A client that gives a command a real terminal clears `TW_NOINTERACT`, `TW_WEB`, `TW_SPOOL_DIR` and
every `TW_PREFLIGHT_*`**, so hooks prompt as they would in a shell. (tw-web's terminal console does this;
it keeps `TW_CLIENT`.)

Gate on `TW_NOINTERACT`:

```python
if os.environ.get('TW_NOINTERACT'):
    ...  # non-interactive path
```

```bash
[ -n "$TW_NOINTERACT" ] && ...  # non-interactive path
```

## 2. Hook → client: signals on stderr

When a hook can't do its job without a terminal, it **aborts** (exits non-zero) and writes **one line of
JSON on stderr**. The client looks for a line that starts with `{` and has the right `type`, and ignores
everything else on stderr.

### `tw_needs_pty`: "run this in a terminal"

```json
{"type": "tw_needs_pty", "cmd": "12 done"}
```

- `cmd` is `TW_PREFLIGHT_CMD` if the client set it, else empty (the client then uses the command it ran).
- `reason` (optional): what needs the terminal, for clients that show it. tw-web doesn't yet.
- The name is `tw_needs_pty`. An older draft of nointeract-preflight's README called it `tw_needs_terminal`;
  no client recognises that name.
- Exit 1. The change is not made; the client offers to run `task <cmd>` in a terminal, where the hook runs
  normally.
- **New hooks use this signal.**

```python
if os.environ.get('TW_NOINTERACT'):
    print(json.dumps({'type': 'tw_needs_pty',
                      'cmd': os.environ.get('TW_PREFLIGHT_CMD', '')}), file=sys.stderr)
    sys.exit(1)
```

### `tw_preflight`: "bulk operation, confirm first"

```json
{"type": "tw_preflight", "count": 7, "verb": "modify", "filter": "project:home", "cmd": "project:home modify +x", "threshold": 3}
```

Reserved: **no hook emits it since 2026-10-26**, when its one emitter, the nointeract-preflight on-launch
hook, was retired (no client ever used it). It meant a mutating command would touch `count` tasks or
more (`threshold`). The client asks the user, then re-runs the same command with
`TW_PREFLIGHT_CONFIRMED=1`. No client does this today: tw-web runs bulk commands in its terminal
console, where `TW_NOINTERACT` is cleared and Taskwarrior asks for confirmation itself (2026-10-15).

### `TW_INTERACTIVE_REQUIRED`: legacy marker

The plain string `TW_INTERACTIVE_REQUIRED` anywhere on stderr of a failed command means the same as
`tw_needs_pty`, without a `cmd`. Clients keep recognising it, and treat it exactly like `tw_needs_pty`
(tw-web opens its console with the command it ran); **hooks don't emit it any more** (none does today).

## 3. Spool: defer a command, let the change through

For a hook that wants to run something interactive *after* the change (hledger-add, an editor) without
blocking it:

1. If `TW_SPOOL_DIR` is set, write the shell command, one line, to `$TW_SPOOL_DIR/<unique>.cmd`
   (for example a UUID).
2. Print the task JSON and exit 0 as usual: the change goes through.
3. After the command, the client reads and deletes every `*.cmd` file and offers each command
   ("Run in terminal"). It runs the line as a **shell** command (`$SHELL -c`), not as `task` arguments.

Quote arguments with `shlex.quote`. Optionally annotate the task ("queued: run hledger add") so the
deferred action leaves a trail.

## 4. Questions from a hook (yes/no in the client): not settled

tw-web can show a yes/no question from a hook and return the answer (files `<id>.prompt` /
`<id>.answer`, delivered to the browser over SSE). **It doesn't work end to end today; don't build on
it.**

- tw-web reads prompts from its private runtime folder (`$XDG_RUNTIME_DIR/tw-web/prompts/`), but tells
  hooks no path, and the helper `~/.task/scripts/tw-web-prompt.py` still writes to `/tmp/tw-web-prompts/`.
- The helper's file name has a hyphen, so `from tw_web_prompt import …` (deps-mgmt) has never imported.

To be designed with hook interaction, together with hooks in test fixtures. Until then a hook that needs
an answer uses `tw_needs_pty`, or skips the question under `TW_NOINTERACT` with a safe default.

## 5. Rules for hooks

- **Never block without a terminal.** Under `TW_NOINTERACT`: signal (§2), spool (§3), or take a safe
  default. A hook that waits on input hangs the client until its timeout (tw-web: 15 s).
- **Fail open.** An unexpected error in an optional feature must not stop the user's command: catch it,
  print the task JSON, exit 0.
- **on-exit hooks run for reads too.** Keep the no-op path cheap (read stdin first; return when it's
  empty). Clients run reads with `rc.hooks=off`, but terminal users don't.
- **Paths from the environment.** `TW_TASK_DIR` (default `~/.task`) and `TASKRC` (default `~/.taskrc`),
  never a hard-coded `~/.task`. That's what `envar_ready = yes` in `awesome.rc` records.
- **Debug and timing.** `TW_DEBUG=<level>` (set by `tw --debug=N`) and `TW_TIMING=1` (set by
  `tw --timing`) as injected by `make-awesome.py --debug` / `--timing`.

## 6. Rules for clients

- Set §1 on every call; clear it for a real terminal.
- `rc.confirmation=no` on every call; `rc.hooks=off` on every read.
- After every **write**, look for `tw_needs_pty` (and the legacy marker) on stderr and drain the spool;
  look for `tw_preflight` too if the client offers bulk confirmation itself.
- A client that can't give the command a terminal never writes it into a shell script: run it as argv.
- Time-limit every `task` call, so a misbehaving hook can't hang the client.
- Free text goes after `--` (`task add -- <description>`): in 2.6.2 any argument starting with `rc.` is
  an override wherever it appears.

## 7. Configuration and switches

- **Settings:** `~/.task/config/<app>.rc`, keys `<app>.<setting>` (`gittw.autocommit = yes`), included
  from `~/.task/config/included.rc`. A hook reads its own file directly; calling `task _get` from a hook
  is slow.
- **Never leave a dangling `include`.** Taskwarrior refuses to start if an included file is missing, and so
  does every client. An installer's `remove` deletes the include with the file, or keeps both. `tw -r`
  (2.10.2+) comments out any include left dangling after a remove, as a safety net; `taskutil config check`
  (daily timer, tw-web launch) reports one with its file and line. Generated installers re-enable a
  commented-out include on reinstall.
- **Generated installers overwrite config files on every reinstall** (`tw -u` included) and have no
  post-install step. Settings a user edits shouldn't ship as a `:config` file: have the app write them
  itself (tw-events' `events init` writes `events.rc`, keeps what's there, and adds its own includes only
  after the files they name exist).
- **On/off:** a hook runs only when executable. `hook-ctrl` toggles the bit, scripts' bits, and
  `include` lines. Prefer a setting when the user may want the feature "paused but installed".

## 8. Packaging and the fleet list

- **The registry is the fleet list.** `registry.d/<app>.meta` + `installers/<app>.install`, installed with
  `tw -I <app>`, which records files in `~/.task/config/.tw_manifest` (what `tw -l` shows).
- **Stations share `~/.task`** (gittw), so an app installed on one is installed on all. The manifest
  records `~/.task/…` paths (tw 2.18.0) so every station writes the same lines; tw hands installers
  absolute paths while they run. What *runs* differs per station: a station's own `hooks.location`
  (tw-mobilize, `hooks.d/<station>`), `hooks`, and `tw.platforms` (desktop or mobile) live in its
  untracked `local.rc`. **`platforms=`** in `.meta` (`desktop`, `mobile`, comma-separated; absent = any)
  says which kinds suit an app: set it for an app that needs a desktop (systemd units, GUI popups,
  `notify-send`). `tw -l` marks an app not at work on this station `[~]`.
- **`awesome.rc`** is the developer side: where each app's repo lives, and its flags
  (`envar_ready`, `tw_web`, `status`, …) for `make-awesome.py --fleet`.
- **Checksums are checked.** `tw -I` refuses a file whose SHA-256 differs from `.meta`, so a change to any
  listed file (README included) goes out through `make-awesome.py`: the full pipeline
  (`make-awesome.py "message"`), `--fleet --push`, or a plain `--push`: since 4.16.2 it recomputes the
  `.meta`'s checksums first, and pushes commits already made (before, a clean tree pushed nothing and
  the registry named a version GitHub didn't have). `--dry-run` works on every stage and the full pipeline
  (4.14.0): it says what would change and touches nothing.
- **Handcrafted installers.** An installer make-awesome must never regenerate says so in its header: a
  `# HANDCRAFTED` comment line within its first 12 lines (say why on the next lines). make-awesome then
  only syncs its `VERSION=` with the `.meta`. It's found under the app's name from the `.meta`, not the
  repo folder's (`tw-smart-nag-hook` holds `smart-nag.install`). Write one when the app needs what the
  generator can't do: keep a user's config over `tw -u`, systemd units, wrapper keywords, includes.
- **`tw_web` in `awesome.rc`:** `yes` = safe under `TW_NOINTERACT`; `partial` = won't hang, some features
  off; `no` = needs a terminal (must signal §2).
- **tw-web is not in the registry,** on purpose: a GUI app, larger than the rest combined. It's the
  reference client for this document. `tw-taskutil` (`taskutil`) is how it joins the fleet's tooling.
- **Wrapper keywords** (`wrapper.N.keyword` in `.meta`, `.tw_wrappers`) dispatch only before task's command
  word and `--`, never after a tw flag (tw 2.11.0), so `tw add sync …` adds a task and a keyword may
  equal its app's name (`events`).
- **Install folders:** hooks `~/.task/hooks/`, commands `~/.task/scripts/` (on `PATH`), settings
  `~/.task/config/`, docs `~/.task/docs/<app>_README.md`, man pages `~/.task/docs/man/man<N>/`.
- **Man pages** (tw 2.20.0, make-awesome 4.17.0): a `:doc` file named `<name>.<1-9>` (`vit.1`, `vitrc.5`)
  is a man page. It installs to `~/.task/docs/man/man<N>/` (`MAN_DIR` in an installer) and **keeps its
  own name**: `man vit` looks for `vit.1`, so it never gets the `<app>_` prefix a README does. The
  section folder sorts pages by kind (1 commands, 5 file formats), not by app; the manifest records
  which app owns each page. A page another app already owns **stops the install** rather than being
  overwritten (a page shares its name with a command or file, which two apps can't both ship either).
  `man` finds them through `MANPATH="$MANPATH:$HOME/.task/docs/man"` (the leading colon of an unset
  MANPATH keeps the system's folders; man-db and mandoc alike), which tw's `install.sh` offers beside
  the PATH line. `tw -R` lists them and opens one with `man -l` either way. Pages that a build installs
  beside its own binary stay with it: Taskwarrior's `task.1`, `taskrc.5`… are under the prefix `task`
  lives in, not the fleet's to move.

## 9. Tests

- Tests never touch `~/.task`: point `TASKRC` and `TASKDATA` (and `TW_TASK_DIR`) at a temp folder.
- **Layout: not settled.** `make-awesome.py --testing` runs `test/test-*.py` (scripts); gittw, tw-taskutil
  and tw-web use pytest (`tests/test_*.py`).

## 10. Who does what (2026-10-15)

| | Gate | Emits | Notes |
|---|---|---|---|
| tw-web | sets all of §1 | — | reads `tw_needs_pty` and the legacy marker on every task write and opens its in-page console; drains the spool on every write; doesn't read `tw_preflight` (command mode runs in the console, where Taskwarrior confirms bulk changes) |
| ~~nointeract-preflight~~ | `TW_NOINTERACT` | `tw_preflight` | retired 2026-10-26: no client read its signal |
| hledger-add | `TW_NOINTERACT` | `tw_needs_pty` | on done |
| subtask | `TW_NOINTERACT` | `tw_needs_pty` | on start with dormant subtasks |
| deps-mgmt | `TW_NOINTERACT` (and `TW_WEB`) | `tw_needs_pty` | 0.3.0: a delete with dependents (its cascade questions); other changes go through |
| annn | `TW_NOINTERACT` | spool | 0.7.1: on-exit, a `+ann` task done or deleted: spools its editor step (`on-exit_annn.py --annotate UUID EVENT`); in a terminal the editor gets `/dev/tty` |
| gittw | — | — | never prompts (`tw_web = yes`) |
| vit | sets §1 on captured writes (`TW_CLIENT=vit`) | — | a terminal client that captures writes: `tw_needs_pty` and the legacy marker offer the same command in its terminal (§1 cleared there); drains the spool after every write, offering each command; `rc.hooks=off` on reads; captured calls run in their own session (`setsid`), so a hook that ignores `TW_NOINTERACT` finds no `/dev/tty` there, as under tw-web (1.4.3); doesn't read `tw_preflight` (2026-10-26). 1.4.1: uses `tw` when installed (report, writes, terminal commands), and `tw.ui=vit` opens tw's reports in it (tw 2.19.0) |

## 11. Open

- §4 questions from hooks, and hooks in test fixtures: with hook interaction.
- §9 test layout.
- deps-mgmt 0.3.0 and annn 0.7.1: through make-awesome, then `tw -u` (the installed copies predate both).
- deps-mgmt: its cascade writes from inside on-modify are lost (review: `tw:docs/deps-mgmt-review.md`).
