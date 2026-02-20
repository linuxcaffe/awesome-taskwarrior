Hey, I have a stack of taskwarrior hooks installed, and SOMETHING if bogging it down. How do I determine which hook is causing performance issues?
Yep — and Taskwarrior hooks are exactly the kind of thing that can quietly turn “task add” into “task add… go make coffee…”.

The trick is to measure hook runtime per hook, and the cleanest way is to temporarily wrap your hooks with timing + logging.

1) First: confirm it’s hooks (and not something else)

Run a simple command with hooks disabled:

task rc.hooks=0 +READY limit:1


Then run the same command normally:

task +READY limit:1


If the first one is snappy and the second one lags, it’s almost certainly hooks.

2) Find where your hooks live

Taskwarrior usually loads hooks from:

~/.task/hooks/

List them:

ls -la ~/.task/hooks

3) Quick “binary search” approach (fastest way)

If you have many hooks, don’t profile yet — disable half, test, repeat.

Taskwarrior treats executable files in ~/.task/hooks/ as hooks.

So you can temporarily remove exec bit from half of them:

chmod -x ~/.task/hooks/on-modify.*


(or pick half by hand)

Test:

time task add test-hook-probe


Then re-enable / disable subsets until you isolate the offender.

This is usually the quickest route.

4) Proper profiling: wrap hooks and log runtimes

This is the most reliable method.

Create a hook wrapper logger

Make a wrapper script:

mkdir -p ~/.task/hook-profiler
cat > ~/.task/hook-profiler/wrap.sh <<'EOF'
#!/usr/bin/env bash
hookname="$1"
shift

log="$HOME/.task/hook-profiler/timings.log"

start_ns=$(date +%s%N 2>/dev/null || python3 -c 'import time; print(int(time.time()*1e9))')

# run the real hook
"$@" 
rc=$?

end_ns=$(date +%s%N 2>/dev/null || python3 -c 'import time; print(int(time.time()*1e9))')

dur_ms=$(( (end_ns - start_ns) / 1000000 ))

printf "%s\t%6dms\t%s\n" "$(date '+%F %T')" "$dur_ms" "$hookname" >> "$log"

exit $rc
EOF

chmod +x ~/.task/hook-profiler/wrap.sh


Now you’ll have a logfile at:

~/.task/hook-profiler/timings.log

5) Wrap each hook

For each executable hook in ~/.task/hooks/, rename it and replace it with a wrapper.

Example for one hook:

cd ~/.task/hooks

mv on-add.foo on-add.foo.real

cat > on-add.foo <<'EOF'
#!/usr/bin/env bash
exec "$HOME/.task/hook-profiler/wrap.sh" "on-add.foo" "$HOME/.task/hooks/on-add.foo.real" "$@"
EOF

chmod +x on-add.foo


Repeat for each hook you suspect (or all of them).

6) Reproduce the slowness and read the timings

Run the slow command a few times:

task add profiling-test +hookprobe
task modify 1 +x
task 1


Then inspect the log:

sort -k2 -n ~/.task/hook-profiler/timings.log | tail -30


That will show the slowest hook calls.

7) Bonus: check for hooks that hang on stdin

Some hooks are slow because they:

read from stdin incorrectly

call external commands that block

do network calls (🤢)

If a hook is sometimes slow, look for things like:

git calls

curl

DNS lookups

python startup overhead

jq + huge JSON parsing

task export inside hooks (very expensive)

8) One-liner “poor man’s profiler”

If you just want a quick “how long does Taskwarrior take” with and without hooks:

time task add "speed test"
time task rc.hooks=0 add "speed test"


If there’s a big gap, you know you’re hunting the right thing.
