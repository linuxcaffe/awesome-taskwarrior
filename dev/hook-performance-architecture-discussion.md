# Hook Performance — Architecture Discussion

*2026-03-08 — notes from conversation with Claude*

## The problem

Every `task` command fires multiple on-modify/on-exit hooks. Each hook is a new
Python process. Startup cost dominates:

```
Python interpreter startup:   ~35ms   ← main cost
stdlib imports (all):         ~15ms   ← partially avoidable
subprocess task export call:  ~50ms   ← unavoidable
hook logic:                    ~5ms
```

With 5–10 hooks firing per command, total lag can reach 300–500ms even before
any real work is done.

## Approach 1 — Lazy / two-phase imports (low effort)

Load only `sys` and `json` first. Determine whether the hook applies.
If passthrough: exit immediately without importing `subprocess`, `termios`,
`re`, `pathlib`, `datetime`, etc.

Saves ~10–20ms per passthrough invocation. Easy to retrofit. Worth doing.

```python
import sys, json
lines = sys.stdin.read().splitlines()
old, new = json.loads(lines[0]), json.loads(lines[1])
if old.get('status') == new.get('status'):
    print(lines[1]); sys.exit(0)   # never touched heavy imports

import subprocess, termios, re    # only loaded when hook actually fires
from pathlib import Path
```

## Approach 2 — Hook daemon (high effort, addresses root cause)

A persistent Python process pre-loads all modules and listens on a Unix socket
(e.g. `~/.task/hookd.sock`). Each installed hook script becomes a thin
wrapper that pipes JSON in/out to the daemon.

- Saves the ~35ms interpreter startup on every invocation
- Same pattern as language servers (LSP), `blackd`, etc.
- Complexity: daemon lifecycle, crash recovery, socket auth, restart on upgrade
- Big win if hook count grows or commands feel sluggish

## Approach 3 — Compiled hooks (overkill for now)

Nuitka or Cython → native binary. No interpreter startup at all.
Probably not worth it given stdlib-only dependencies.

## Current status

Timing instrumentation (`TW_TIMING` env var) not yet deployed to most
installed hooks — accurate baseline numbers pending. Revisit once timing
data collected across a full `task next` invocation.

## Related

- make-awesome.py `--timing` flag injects timing wrapper at top of each script
- `tw --timing <cmd>` sets `TW_TIMING=1` for a single invocation
- See also: hook-timer-notes.txt in this dir
