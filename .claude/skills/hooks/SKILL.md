---
name: hooks
description: Taskwarrior hook API knowledge base — behavioral quirks, stdin/stdout contract, isolation, debugging. Reference before writing or debugging any hook.
triggers:
  - /hooks
  - "hook api"
  - "taskwarrior hooks"
  - "hook behavior"
---

## Taskwarrior Hook API — Key Facts

### Hook types and stdin contract

| Hook | stdin | stdout |
|------|-------|--------|
| on-launch | nothing | feedback lines (printed to user) |
| on-add | single task JSON | modified task JSON (required) + feedback |
| on-modify | old task JSON, new task JSON (2 lines) | modified task JSON (required) + feedback |
| on-exit | all tasks modified in this session, one JSON per line | feedback lines only |

**on-exit stdin is NOT the full task database** — only tasks changed in the current session.

---

### Critical: what on-exit does NOT receive

Taskwarrior **silently** auto-deletes tasks whose `until:` date has passed.
**These auto-expired tasks never appear in on-exit stdin.**

This means any hook that reacts to "task deleted" on on-exit will **miss** until:-triggered
deletions entirely. Fix pattern: add a reconciliation pass that scans the database
for orphaned state (e.g. recurring templates with no pending instance).

Bug discovered: 2026-04-02 in tw-recurrence_overhaul-hook v2.7.5.
Fixed by: `reconcile_orphaned_templates()` scanning all `status:recurring` templates
on every on-exit call and spawning the next instance for any with no pending/waiting instance.

---

### taskrc `include` syntax

```
include ~/.task/config/some.rc    # CORRECT — space separator
include=~/.task/config/some.rc    # WRONG — equals silently fails to load included file
```

`=` works for all other config keys but breaks `include`. Included files appear in
`task _show` output (only last one shown) but settings inside them are silently dropped.
Discovered: 2026-04-02 — entire dev .taskrc-dev was failing to load UDAs.

---

### B+C isolation — env var inheritance

Taskwarrior passes its full environment to every hook subprocess. Setting:

```bash
TASKRC=~/.taskrc-dev TW_TASK_DIR=~/.task-dev task rc.hooks=on <cmd>
```

gives hooks both vars for free. `subprocess.run(['task', ...])` calls inside hooks
also inherit them — no need to pass TASKRC/TW_TASK_DIR explicitly.

**BUT**: hardcoded paths like `os.path.expanduser('~/.task/hooks')` break isolation.
Always use:
```python
TASK_DIR = os.environ.get('TW_TASK_DIR', os.path.expanduser('~/.task'))
hooks_dir = os.path.join(TASK_DIR, 'hooks')
```

---

### Diagnosing what a hook received on stdin

Drop a capture wrapper:

```python
#!/usr/bin/env python3
import sys
lines = sys.stdin.readlines()
with open('/tmp/hook-stdin.json', 'w') as f:
    f.write(f"# Lines received: {len(lines)}\n")
    for l in lines:
        f.write(l)
sys.exit(0)
```

Install it as the hook under test, run the triggering command, inspect `/tmp/hook-stdin.json`.
Line count 0 = hook fired but received nothing (silent auto-action, not user modification).

---

### Debug mode activation

Two independent systems exist in the fleet hooks:

| Variable | Effect |
|----------|--------|
| `DEBUG_RECURRENCE=1` | Activates `DEBUG` constant in recurrence_common_hook — controls `if DEBUG:` guards |
| `TW_DEBUG=2` | Activates `debug_active` in make-awesome.py debug-injected hooks — controls local `debug_log()` |

These are separate. `TW_DEBUG=2` alone does NOT activate the `if DEBUG:` guards in hook logic.
Set both when debugging recurrence hooks:
```bash
TASKRC=~/.taskrc-dev TW_TASK_DIR=~/.task-dev DEBUG_RECURRENCE=1 TW_DEBUG=2 task rc.hooks=on <cmd>
```

---

### Subprocess calls inside hooks

Always pass `rc.hooks=off` to prevent recursive hook execution:
```python
subprocess.run(['task', 'rc.hooks=off', 'rc.confirmation=off', uuid, 'export'], ...)
```

Reads are fine from any hook. **Writes from on-add/on-modify are lost:** a nested `task modify`
or `delete` runs, then the outer command saves its own copy of the data over it (2.6.2, verified
2026-10-31: deps-mgmt's cascade "Deleted [2]" left the task pending). Leave the change in a file and
apply it from on-exit (see: `recurrence_propagate.json` in the recurrence hook), or change the task
in the JSON you print. CONVENTIONS §5.

### Interactive programs need `/dev/tty`

Even in a terminal, a hook's stdin and stdout are pipes to task, so an editor started with them runs
blind. Hand it the terminal (hledger-add, annn):
```python
tty = open('/dev/tty', 'r+b', buffering=0)   # binary, unbuffered: text mode fails on a tty
subprocess.run([editor, path], stdin=tty, stdout=tty, stderr=tty)
```
No `/dev/tty` (OSError: a client's captured call, cron) → take the non-interactive path.

---

### Testing hooks

Use the fleet test framework (`~/dev/awesome-taskwarrior/dev/test/`).
See `/tests` skill for framework usage. Key setup for hooks:

```python
def setUp(self):
    super().setUp()
    os.environ['TW_TASK_DIR'] = self.t.taskdata  # B+C isolation
    hook_dir = os.path.expanduser('~/dev/tw-myapp-hook')
    self.t.link_hook('on-exit_myapp.py', f'{hook_dir}/on-exit_myapp.py')
```

Always use `+test` tag on all tasks created in tests.

---

### Non-interactive client protocol — fleet-wide conventions

> **Canonical reference: `~/dev/awesome-taskwarrior/CONVENTIONS.md`** (env vars, the `tw_needs_pty` /
> `tw_preflight` signal formats, spool, rules for hooks and clients). Read it before writing or changing
> a hook's non-interactive path; this section is a summary and may lag. New hooks gate on
> `TW_NOINTERACT` and emit `tw_needs_pty`; `TW_INTERACTIVE_REQUIRED` is legacy.

Non-terminal clients (tw-web, tw-gtk, Electron apps, etc.) cannot handle interactive
hooks. Three env vars form the standard protocol — set by the client on every subprocess:

| Variable | Value | Purpose |
|----------|-------|---------|
| `TW_NOINTERACT` | `1` | Any non-interactive client — primary gate |
| `TW_CLIENT` | `web`, `gtk`, … | Client identity for client-specific behaviour |
| `TW_WEB` | `1` | Legacy alias for tw-web (keep for backward compat) |
| `TW_SPOOL_DIR` | client-private dir (tw-web: `$XDG_RUNTIME_DIR/tw-web/spool`) | Where hooks write deferred commands; never assume a path |

**Gate pattern** — check `TW_NOINTERACT` first, not `TW_WEB`:
```python
if os.environ.get('TW_NOINTERACT'):
    ...  # non-interactive path
```
```bash
[ -n "$TW_NOINTERACT" ] && ...  # non-interactive path
```

**Refuse and ask for a terminal** (the change is not made; the client runs the command again in a
terminal, where the hook asks as usual). Give a `reason`: one line, the hook's name first. vit shows
it in its question:
```python
if os.environ.get('TW_NOINTERACT'):
    print(json.dumps(old_task))   # on-modify: the unchanged task
    print(json.dumps({'type': 'tw_needs_pty',
                      'cmd': os.environ.get('TW_PREFLIGHT_CMD', ''),
                      'reason': "deps-mgmt: deleting 'Plan' asks about its dependents"}),
          file=sys.stderr)
    sys.exit(1)
```

---

### Spool protocol — deferring interactive programs

Used for hooks that launch a fully interactive program (hledger-add, editor, fzf).
The hook writes a shell command to `TW_SPOOL_DIR` and exits immediately. The client
drains the spool after each write command and offers "Run in terminal" to the user.

**Hook side** (Python):
```python
import shlex, uuid, os
from pathlib import Path

spool_dir = os.environ.get('TW_SPOOL_DIR', '')
if spool_dir:
    cmd_parts = ['hledger', 'add', date, description, account]
    name = str(uuid.uuid4())
    # optional: what it's for, asked in the client's question (write it before the .cmd)
    (Path(spool_dir) / f'{name}.reason').write_text(f"hledger-add: record '{description}'\n")
    (Path(spool_dir) / f'{name}.cmd').write_text(' '.join(shlex.quote(p) for p in cmd_parts))
    print(json.dumps(modified))   # required: emit task JSON before exit
    return 0
# else: run interactively as normal
```

**Client side** (tw-web, app.py):
```python
_SPOOL_DIR = _private_dir(_RUN_DIR / 'spool')   # $XDG_RUNTIME_DIR/tw-web/spool, mode 0700
_TW_ENV = {..., 'TW_SPOOL_DIR': str(_SPOOL_DIR)}

def _drain_spool():
    cmds = []
    for f in sorted(_SPOOL_DIR.glob('*.cmd')):
        cmds.append(f.read_text().strip())
        f.unlink()
    return cmds

# After every non-readonly task command:
spooled = _drain_spool()
if spooled:
    result['deferred_cmds'] = spooled
# Include first in JSON response as 'deferred_cmd'; frontend calls offerTerminal()
```

**When to use spool vs `tw_needs_pty`:**
- **Spool**: the change can go through, and the interactive part can come after it (hledger-add's
  entry, annn's closing note, an editor, fzf). Required in on-exit, where the change is already made.
- **`tw_needs_pty`**: the questions decide whether or how the change is made (deps cascade, subtask
  activation). The change is refused and run again in a terminal.
- **Not `tw_web_confirm`:** the yes/no channel to tw-web doesn't work end to end (CONVENTIONS §4).

**Annotating the deferred action** — recommended pattern:
```python
ann = {
    'entry': datetime.utcnow().strftime('%Y%m%dT%H%M%SZ'),
    'description': f'ledger: {payee} {date} (queued — run hledger add)',
}
modified.setdefault('annotations', []).append(ann)
```
This leaves a visible trail in the task so the user knows an action is pending.

---

### tw-web integration — fleet-wide conventions

**`TW_WEB=1` environment variable** (legacy — prefer `TW_NOINTERACT`)
Flask sets `TW_WEB=1` on all task subprocess calls. Hooks MUST check this before any
interactive operation. Terminal-interactive code (opening `/dev/tty`, `input()`, `getch()`)
silently hangs or appears in the launch terminal when `TW_WEB=1`.

> **Not working end to end (2026-10-13), see CONVENTIONS.md §4:** the helper writes to `/tmp/tw-web-prompts`
> but tw-web now reads a private runtime dir, and the hyphenated file name means `from tw_web_prompt
> import …` never imports. Don't build on it until hook interaction is redesigned.

**Tier 2 prompt helper** — `~/.task/scripts/tw-web-prompt.py` (Python) / `tw-web-prompt.sh` (Bash)

Standard import pattern for Python hooks:
```python
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path.home() / '.task' / 'scripts'))
try:
    from tw_web_prompt import tw_web_confirm, tw_web_info
    _TW_WEB_PROMPTS = True
except ImportError:
    _tw_web_confirm = None
    _TW_WEB_PROMPTS = False
```

**`tw_web_confirm(question, context='', default='no', timeout=30)`** — shows a yes/no
dialog in the browser, blocks until answered or timeout. Returns `'yes'` or `'no'`.
Falls back to `input()` when `TW_WEB != '1'`.

**`tw_web_info(message, context='')`** — fires a non-blocking notification in the browser.
No answer needed. Falls back to `sys.stderr` print.

**Gate pattern** (hooks that launch a fully interactive program like hledger-add):
```python
# Ask before launching the interactive session
if tw_web_confirm('Record hledger transaction?', context=payee, default='yes') != 'yes':
    print(json.dumps(modified))
    return 0
run_hledger_add(...)   # still runs in launch terminal when TW_WEB=1
```

**Replace pattern** (hooks with inline y/n prompts — deps-mgmt, subtask cascade):
```python
def prompt(msg):
    if os.environ.get('TW_WEB') == '1' and _TW_WEB_PROMPTS:
        answer = _tw_web_confirm(msg.strip(), default='n')
        ch = 'Y' if answer == 'yes' else 'n'
        sys.stderr.write(msg + ch + '\n')
        return ch
    # original getch() / tty path unchanged below
    ...
```

**Protocol**: prompts are JSON files in `/tmp/tw-web-prompts/{id}.prompt`; answers come back
as `/tmp/tw-web-prompts/{id}.answer`. Flask watcher thread picks up prompts within 300ms and
broadcasts via SSE to all connected browser tabs. Any tab can answer.

**Timeout behaviour**: hook always gets a default answer after `timeout` seconds — it never
hangs. Default should reflect the safe/conservative choice (usually `'no'`).

**`rc.confirmation=no`** is injected by Flask on every `run_task_command` call — hooks must
NOT rely on TW's own confirmation prompts being suppressed; they are, but don't depend on it.

---

### tw-web + threaded Flask: on-exit hook race condition

**Problem:** `on-exit` hooks fire on **every** `task` subprocess call — including read-only
`export`, `projects`, `stats`, `_show`, etc. Flask runs with `threaded=True`, so concurrent
requests each trigger their own hook invocation simultaneously.

Any `on-exit` hook that does a **check-then-act** (query DB → no match found → spawn/create)
is vulnerable: two concurrent hook runs both pass the check before either has committed its
action, producing duplicates.

**Observed:** `reconcile_orphaned_templates()` in recurrence hook v2.7.5 — a daily task with
`until:23:00` expired silently (not in stdin), reconcile fired on every request, concurrent
page-load + SSE keepalive both saw no pending instance, both called `spawn_instance` → 3 copies.

**Fix in tw-web:** inject `rc.hooks=off` for all read-only commands. Hooks only need to fire
on genuine write commands (done, modify, delete, add, annotate, sync, undo).

```python
def run_task_command(args, readonly=False):
    overrides = ['rc.confirmation=no']
    if readonly:
        overrides.append('rc.hooks=off')
    args = [args[0]] + overrides + args[1:]
    ...
```

Apply `readonly=True` to: all `export` calls (including secondary export-after-write),
`projects`, `_projects`, `_tags`, `stats`, `_show`, `_get`, `version`.

**Rule of thumb:** if the command doesn't change task data, pass `readonly=True`. The write
command that precedes any "read back result" export has already fired hooks — the export is
just fetching the updated state and does not need to re-trigger hooks.

**Hook-side hardening (future):** a lock file around `query_instances` + `spawn_instance`
in `reconcile_orphaned_templates` would make the hook itself race-safe, independent of
whether the caller suppresses hooks on reads.
