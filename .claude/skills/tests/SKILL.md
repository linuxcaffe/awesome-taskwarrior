---
name: tests
description: Fleet test framework orientation — how to write, run, and place tests for awesome-taskwarrior fleet apps. Invoke when writing new tests or debugging existing ones.
triggers:
  - /tests
  - "write a test"
  - "test framework"
  - "how to test hooks"
---

## awesome-taskwarrior Test Framework

**Location:** `~/dev/awesome-taskwarrior/dev/test/`
**Installed to:** `~/.task/awesome-taskwarrior/lib/` (via INSTALL.sh)

### Core files

| File | Purpose |
|------|---------|
| `test_framework.py` | `TaskWarriorTest` + `TaskTestCase` base classes |
| `test_helpers.sh` | Bash test utilities |
| `tw-test` | CLI test runner |
| `templates/test-python-template.py` | Starting point for new tests |
| `templates/test-bash-template.sh` | Starting point for bash tests |
| `examples/test-needs-priority.t` | Full real-world example |

---

### Test file placement

Tests live in the **project's own** `test/` directory, NOT in the framework dir:
```
~/dev/tw-myapp-hook/test/test-myapp-until.py    ← goes here
~/dev/tw-myapp-hook/test/test-myapp-smoke.sh
```

---

### Python test anatomy

```python
#!/usr/bin/env python3
import sys, os, unittest
sys.path.insert(0, os.path.expanduser('~/.task/awesome-taskwarrior/lib'))
from test_framework import TaskTestCase, TAPTestRunner

class TestMyApp(TaskTestCase):
    def get_taskrc_extras(self):
        return {
            'uda.r.type': 'duration',          # UDAs your hook needs
            'uda.r.label': 'Recurrence Period',
            'recurrence': 'no',
        }

    def setUp(self):
        super().setUp()
        os.environ['TW_TASK_DIR'] = self.t.taskdata  # B+C isolation
        hook_dir = os.path.expanduser('~/dev/tw-myapp-hook')
        self.t.link_hook('on-exit_myapp.py', f'{hook_dir}/on-exit_myapp.py')
        self.t.link_hook('recurrence_common_hook.py', f'{hook_dir}/recurrence_common_hook.py')

    def tearDown(self):
        super().tearDown()
        os.environ.pop('TW_TASK_DIR', None)

    def test_something(self):
        """Brief description shown in test output"""
        code, out, err = self.t.task('add', 'test task', '+test')
        self.assertEqual(code, 0)
        tasks = self.t.export()
        self.assertEqual(len(tasks), 1)

if __name__ == "__main__":
    unittest.main(testRunner=TAPTestRunner())
```

---

### TaskTestCase API

```python
self.t.task('add', 'my task', '+test', 'due:today')   # run task command
self.t.export()                                         # all pending tasks as list
self.t.export('uuid:XXX')                              # filter export
self.t.get_task(uuid)                                  # single task dict
self.t.link_hook('hook-name.py', '/path/to/source.py') # install hook via symlink
self.t.add_hook('hook-name.py', script_text)           # install inline hook
self.assertTaskAttribute(uuid, 'priority', 'H')        # convenience assertion
```

---

### Simulating until: auto-expiry

Taskwarrior won't auto-expire tasks in test (no time travel). Simulate it:

```python
def simulate_until_expiry(self, task_id):
    """Force-expire a task by setting until: to past then triggering any task command"""
    self.t.task(str(task_id), 'modify', 'until:2020-01-01')
    self.t.task('next')  # triggers on-exit which sees the now-deleted task
```

**Note:** The auto-expiry itself (TW converting status to deleted) happens when any
task command runs and TW notices until: is in the past. The on-exit hook receives
ZERO lines for this deletion (TW silent behavior). Test the reconciliation pass by
verifying a new instance exists AFTER the task command, not by checking hook stdin.

---

### Writing tests while debugging

When reproducing a bug in the dev sandbox, simultaneously write the equivalent test.
The sandbox confirms the bug; the test framework confirms the fix and prevents regression.

Pattern:
1. Reproduce in sandbox: `TASKRC=~/.taskrc-dev TW_TASK_DIR=~/.task-dev task rc.hooks=on ...`
2. Write the test case capturing the same scenario
3. Run test on broken code → should FAIL
4. Apply fix
5. Run test → should PASS
6. Both the sandbox confirmation and the test live as artifacts

---

### Running tests

```bash
# Run a single test file
python3 ~/dev/tw-myapp-hook/test/test-myapp-until.py

# With TAP output (for CI)
python3 ~/dev/tw-myapp-hook/test/test-myapp-until.py 2>&1

# Via tw-test runner (if installed)
~/.task/awesome-taskwarrior/tw-test ~/dev/tw-myapp-hook/test/
```

---

### Convention: test tagging

All tasks created in tests must use `+test` tag. This matches production convention
and allows cleanup with `task +test delete rc.confirmation=no` if isolation fails.

---

### Known gotchas

**TAPTestRunner shows "ok N - None" (cosmetic, not a failure)**

Python 3.10+ `TestSuite._cleanup=True` replaces test references with `None` after
each test runs. `TAPTestRunner._flatten_suite()` then yields `None` for each top-level
suite slot. Result: "ok 1 - None", "ok 2 - None", "ok 3 - None" — one line per
top-level suite (empty + one per class), regardless of test count. Exit 0 = all
passed. Use `TextTestRunner(verbosity=2)` for proper names during development.

**Recurrence type normalized values are `"chain"` and `"period"` (not `"chained"` / `"periodic"`)**

`normalize_type()` in `recurrence_common_hook.py` returns:
- `ty:c`, `ty:ch`, `ty:chain` → `"chain"`
- `ty:p`, `ty:periodic`, (default) → `"period"`

**`rend:` past date on add is rejected interactively by the hook**

The on-add hook rejects `rend:` dates in the past with an error + TW confirmation
prompt — the subprocess hangs waiting for stdin. Use a future `rend:+Nd` with a
period longer than N days to test rend stop-spawning behaviour instead.

**`task export` filter must come BEFORE the verb**

`self.t.task('status:recurring', 'export')` works.
`self.t.export('status:recurring')` appends filter after verb — TW syntax error.

**`task next` exits 1 with no tasks — use `expect_error=True`**

```python
self.t.task('next', expect_error=True)
```
