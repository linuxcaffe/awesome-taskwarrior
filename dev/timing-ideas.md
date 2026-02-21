That is super cool, thanks. As we're running out of context and session, tell me how I would profile a specific hook. It occurred to me that each of these hooks could get some code flag just for timing? Any other notions of hot to extend --timing to get more granular?
9:25 p.m.

Good question to end the session on. A few approaches:

1. Wrap the hook with time — quickest one-off:
bash

time task rc.hooks=off add +test something  # baseline without hooks
# then enable one hook at a time via rc.hooks.on-add_recurrence.py=1 (not a real flag)

Actually task 2.6.2 doesn't have per-hook enable/disable. Better:
bash

# Temporarily disable all but one by moving them out
cd ~/.task/hooks && mkdir /tmp/hooks-bak
mv on-exit_* /tmp/hooks-bak/
time task add +test single-hook-test
mv /tmp/hooks-bak/* .

2. Built-in timing flag in each hook — the cleanest approach. Since you control all your hooks, add to each one:
python

if os.environ.get('TW_TIMING'):
    import time
    _t0 = time.perf_counter()
    # ... at end ...
    elapsed = (time.perf_counter() - _t0) * 1000
    print(f"[timing] {__file__}: {elapsed:.1f}ms", file=sys.stderr)

Then tw --timing could set TW_TIMING=1 in the subprocess env before calling task. Each hook self-reports. This is the right long-term answer — zero overhead normally, opt-in per run.

3. tw --timing could set TW_TIMING=1 — one-line addition to run_with_timing():
python

env = os.environ.copy()
env['TW_TIMING'] = '1'
result = subprocess.run(cmd, ..., env=env)

Then parse [timing] lines from stderr alongside the existing Perf parsing.

The TW_TIMING approach is worth doing — it's consistent with your existing DEBUG_RECURRENCE=1 pattern and gives you the granularity that task's debug output never will. Something to pick up next session.
