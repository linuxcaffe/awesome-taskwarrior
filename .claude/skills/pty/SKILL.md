---
name: pty
description: Patterns for running subprocesses in a pseudo-terminal (PTY) to capture full-color ANSI output, and rendering that output in a curses TUI. Invoke when capturing colored subprocess output, building live preview panels, or wiring PTY output into ncurses.
triggers:
  - /pty
  - "pseudo terminal"
  - "capture colors"
  - "live preview"
  - "pty subprocess"
  - "ansi to curses"
---

## PTY subprocess pattern

**Why PTY instead of `subprocess.PIPE`?**  
Programs detect `isatty()` and suppress color when stdout is a pipe. A PTY makes
the child process believe it's talking to a real terminal — colors, box-drawing,
and full formatting all appear exactly as they would in normal interactive use.

**Canonical implementation** (from `theme-select.py`):

```python
import os, pty, select, fcntl, termios, struct, subprocess

def _run_in_pty(cmd, env, cols, rows):
    """Run cmd in a PTY sized (cols × rows), return decoded output string."""
    master_fd, slave_fd = pty.openpty()

    # Set terminal size BEFORE the child starts so it gets correct dimensions
    winsize = struct.pack('HHHH', rows, cols, 0, 0)
    fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, winsize)

    proc = subprocess.Popen(
        cmd, env=env,
        stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
        close_fds=True,
    )
    os.close(slave_fd)   # parent must close slave_fd or reads never get EOF

    buf = b''
    while True:
        try:
            r, _, _ = select.select([master_fd], [], [], 0.2)
            if r:
                buf += os.read(master_fd, 4096)
            elif proc.poll() is not None:
                # Process exited — drain any remaining bytes
                try:
                    while True:
                        r2, _, _ = select.select([master_fd], [], [], 0.05)
                        if r2:
                            buf += os.read(master_fd, 4096)
                        else:
                            break
                except OSError:
                    pass
                break
        except OSError:
            break   # master_fd closed (EIO) = child exited

    try:
        os.close(master_fd)
    except OSError:
        pass
    proc.wait()
    return buf.decode('utf-8', errors='replace')
```

**Critical details:**
- Close `slave_fd` in the parent immediately after `Popen` — otherwise `select` on
  `master_fd` never gets EOF when the child exits
- Use `select` with a short timeout (0.2 s) instead of blocking reads — allows
  polling `proc.poll()` to detect exit without hanging
- `errors='replace'` on decode prevents crashes from partial multibyte sequences
- OSError on `master_fd` reads means the child exited (Linux EIO)

---

## Post-processing PTY output

PTY output contains CRLF line endings and OSC escape sequences (terminal title bars
etc.) that need stripping before display:

```python
import re

_OSC_RE  = re.compile(r'\x1b\].*?(?:\x1b\\|\x07)', re.DOTALL)
_ANSI_RE = re.compile(r'\x1b\[([0-9;]*)m')

def _clean_pty(text):
    text = _OSC_RE.sub('', text)              # strip title bars / OSC sequences
    return text.replace('\r\n', '\n').replace('\r', '')
```

---

## Temp TASKRC pattern

To run `task` with a specific theme without touching the real config:

```python
import tempfile, os

def _make_preview_rc(taskrc, theme_path):
    """Write a temp TASKRC with all theme includes replaced by theme_path."""
    lines = taskrc.read_text().splitlines(keepends=True)
    new_lines = []
    injected = False
    _THEME_INCLUDE_RE = re.compile(
        r'\s*include\s+.*\.theme'
        r'|\s*include\s+\S+themes\.rc'
    )
    for line in lines:
        if _THEME_INCLUDE_RE.match(line):
            if not injected:
                new_lines.append(f'include {theme_path}\n')
                injected = True
            # drop other theme includes
        else:
            new_lines.append(line)
    if not injected:
        new_lines.append(f'include {theme_path}\n')
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.taskrc', delete=False)
    tmp.write(''.join(new_lines))
    tmp.close()
    return tmp.name   # caller must unlink when done

# Usage:
tmp_rc = _make_preview_rc(taskrc, theme_path)
try:
    env = os.environ.copy()
    env['TASKRC'] = tmp_rc
    env['TERM']   = 'xterm-256color'
    raw = _run_in_pty(['task', f'rc.defaultwidth={cols}', 'rc.color=on',
                       'rc.hooks=off', 'rc.verbose=label,blank',
                       f'rc.limit=18', report],
                      env=env, cols=cols, rows=40)
finally:
    try:
        os.unlink(tmp_rc)
    except Exception:
        pass
```

**Key env vars for task subprocess:**
- `TASKRC` — point to temp file
- `TERM=xterm-256color` — forces 256-color mode
- `rc.color=on` — override any color=off in taskrc
- `rc.hooks=off` — skip hooks (speed + avoid recursion)
- `rc.defaultwidth=N` — tell task how wide to render

---

## ANSI → curses rendering

Rendering ANSI-colored PTY output inside a curses window:

```python
_ANSI_RE = re.compile(r'\x1b\[([0-9;]*)m')
_ansi_pairs = {}   # (fg, bg) → curses color pair index
_ansi_next  = [10] # start allocating pairs from 10

def _ansi_pair(fg, bg):
    key = (fg, bg)
    if key not in _ansi_pairs:
        n = _ansi_next[0]
        _ansi_next[0] += 1
        try:
            curses.init_pair(n, fg, bg)
        except curses.error:
            return 0
        _ansi_pairs[key] = n
    return _ansi_pairs[key]

def _parse_segments(text):
    """Split ANSI text into [(str, fg, bg, curses_attrs)] segments."""
    fg, bg, attrs = -1, -1, 0
    segments = []
    pos = 0
    A_ITALIC = getattr(curses, 'A_ITALIC', 0)
    for m in _ANSI_RE.finditer(text):
        s, e = m.span()
        if s > pos:
            segments.append((text[pos:s], fg, bg, attrs))
        pos = e
        codes = [int(x) for x in m.group(1).split(';') if x] if m.group(1) else [0]
        # ... decode SGR codes into (fg, bg, attrs)
    if pos < len(text):
        segments.append((text[pos:], fg, bg, attrs))
    return segments

def addstr_ansi(win, y, x, text, max_w):
    """Write ANSI-colored text to curses window, clipped to max_w columns."""
    col = x
    for chunk, fg, bg, attrs in _parse_segments(text):
        if col >= x + max_w:
            break
        space = (x + max_w) - col
        chunk = chunk[:space]
        if not chunk:
            continue
        pair = _ansi_pair(fg, bg) if (fg != -1 or bg != -1) else 0
        try:
            win.addstr(y, col, chunk, curses.color_pair(pair) | attrs)
        except curses.error:
            pass
        col += len(chunk)
```

---

## Caching

PTY subprocess calls are expensive (~100–300ms each). Always cache by a key that
captures all inputs that affect output:

```python
_preview_cache = {}   # (str(theme_path), report, cols, prec_override) → [lines]

key = (str(theme_path), report, cols, prec_override or '')
if key in _preview_cache:
    return _preview_cache[key]
# ... run PTY ...
_preview_cache[key] = lines
return lines
```

Invalidate with `_preview_cache.clear()` after:
- Theme file edited
- Terminal resized (`KEY_RESIZE`)
- Forced refresh (`r`)

---

## Gotchas

**`TIOCSWINSZ` must set slave_fd, not master_fd**  
Setting the window size on master_fd is silently ignored on some kernels.
Always set it on slave_fd before starting the child.

**Don't use `communicate()` or `stdout=PIPE`**  
`communicate()` blocks until the process exits with no way to drain incrementally.
`stdout=PIPE` defeats the purpose — the child won't see a tty.

**`curses.use_default_colors()` required before `init_pair(n, -1, -1)`**  
Call it immediately after `curses.start_color()`. Color pair index -1 means
"terminal default background/foreground". Without this call, `-1` crashes.

**Allocate ANSI color pairs starting at index 10+**  
Pairs 1–9 are typically used by the TUI's own chrome (header, status bar, etc.).
Starting dynamic ANSI pairs at 10 avoids collisions.

**OSError EIO on master_fd read = child exited (Linux)**  
This is normal. Catch `OSError` around `os.read(master_fd, ...)` and treat it
as EOF.
