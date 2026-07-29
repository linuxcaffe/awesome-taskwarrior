---
name: task-context
description: Load the active Taskwarrior task as session context. Use at the start of a dev session, or when the user says "what am I working on", "load task context", "task context", or "what's the task".
allowed-tools: Bash, Read, Glob
argument-hint: "[task-id] (optional — load a specific task instead of active)"
---

Load development task context for this session.

## Working directory

!`pwd && git branch --show-current 2>/dev/null && echo ""`

## Task context

!`
# Use dev taskrc if it exists, otherwise fall back to default
if [ -f ~/.taskrc-dev ]; then
    export TASKRC=~/.taskrc-dev
fi
TW="task rc.hooks=off rc.color=off rc.context=none"

TASKARGS="${ARGUMENTS:-}"
if [ -n "$TASKARGS" ]; then
    # Specific task ID requested
    $TW "$TASKARGS" information 2>/dev/null \
        || echo "Task '$TASKARGS' not found."
else
    # Try active task first
    ACTIVE=$($TW rc.verbose=nothing +ACTIVE export 2>/dev/null)
    if [ "$ACTIVE" != "[]" ] && [ -n "$ACTIVE" ]; then
        echo "=== ACTIVE TASK ==="
        $TW rc.verbose=label,blank +ACTIVE information 2>/dev/null
    else
        echo "(no active task)"
        echo ""
        echo "=== NEXT TASKS ==="
        $TW rc.verbose=label,blank limit:5 next 2>/dev/null \
            || echo "(no pending tasks found)"
    fi
fi
`

## Recent commits here

!`git log --oneline -6 2>/dev/null || echo "(not in a git repo)"`

## Uncommitted changes

!`git diff --stat 2>/dev/null | head -15; git diff --cached --stat 2>/dev/null | head -10`

## Instructions

Read the above and orient the session:

1. **State the task** — one sentence: what needs doing and why (use description +
   annotations if present; be concrete, not vague)

2. **Identify the work** — which files, hooks, or scripts are relevant based on
   the project/tags/description; note anything already changed in the diff

3. **Propose a start** — suggest the first concrete action unless the task
   makes it obvious, then just begin

If no active task was found:
- Suggest `task start <id>` on one of the next tasks shown, if any look like
  dev work
- Or suggest `task add "description" +dev` to create a new dev task
- Note that tagging dev tasks with `+dev` makes `/fleet` and `/task-context`
  more useful over time

If a specific task ID was given via argument, focus entirely on that task.
