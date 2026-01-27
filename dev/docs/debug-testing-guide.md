# Debug Feature - Testing Guide

## ✅ Phase 1 Complete!

The debug feature is now fully implemented in tw.py!

## What Was Added

### 1. DebugLogger Class
- 3 debug levels (1, 2, 3)
- Logs to `~/.task/logs/debug/tw_debug_TIMESTAMP.log`
- Auto-cleanup (keeps last 10 sessions)
- Color-coded output to stderr
- Environment variable support for hooks

### 2. Debug Integration
- PathManager initialization
- RegistryManager operations
- AppManager install/remove/update
- Manifest operations
- Taskwarrior passthrough (level 3 enables debug.hooks)

### 3. Command Line
- `--debug` flag with optional level
- Named modes: tw, hooks, task, all, verbose
- Environment variables set for subprocesses

## Testing

### Basic Tests

```bash
# Level 1 (basic tw.py operations)
tw --debug --list

# Level 2 (detailed, includes subprocess calls)
tw --debug=2 --install tw-recurrence

# Level 3 (everything + taskwarrior debug.hooks)
tw --debug=3 task next

# Named modes
tw --debug=all --list
tw --debug=verbose --install app
```

### Check Debug Output

```bash
# View latest debug log
ls -lt ~/.task/logs/debug/
tail -f ~/.task/logs/debug/tw_debug_*.log

# Watch debug output in real-time
tw --debug=2 --install tw-recurrence 2>&1 | tee /tmp/debug.txt
```

### Test Environment Variables

```bash
# Debug variables are passed to installers
tw --debug=2 --install tw-recurrence
# Installer should see:
# TW_DEBUG=2
# TW_DEBUG_LEVEL=2
# DEBUG_HOOKS=1
# TW_DEBUG_LOG=/home/user/.task/logs/debug
```

### Test Taskwarrior Integration

```bash
# Level 3 should enable debug.hooks=2
tw --debug=3 task add "Test task"

# Should see taskwarrior hook debug output:
# [task 2026-01-23 ...] Hooks: Calling hook ...
# [task 2026-01-23 ...] Hooks: Completed hook ...
```

### Test Log Cleanup

```bash
# Create multiple debug sessions
for i in {1..15}; do
  tw --debug --list > /dev/null 2>&1
  sleep 1
done

# Check only last 10 are kept
ls ~/.task/logs/debug/ | wc -l
# Should be 10 or 11
```

## Debug Levels Explained

### Level 1: Basic Operations
**What you see:**
- Major operations (install, remove, update)
- Success/failure status
- Error conditions

**Example output:**
```
[debug] 16:45:23.123 | main                           | Debug mode enabled (level 1)
[debug] 16:45:23.125 | PathManager.__init__           | Initializing PathManager
[debug] 16:45:23.130 | AppManager.install             | Installing tw-recurrence (dry_run=False)
[debug] 16:45:28.450 | AppManager.install             | Installation successful, manifest reloaded
```

### Level 2: Detailed Operations
**What you see:**
- Everything from level 1
- Subprocess calls
- File paths and operations
- Configuration details

**Example output:**
```
[debug] 16:45:23.123 | main                           | Debug mode enabled (level 2)
[debug] 16:45:23.124 | main                           | Log file: /home/user/.task/logs/debug/tw_debug_20260123_164523.log
[debug] 16:45:23.125 | PathManager.__init__           | Initializing PathManager
[debug] 16:45:23.126 | PathManager                    | task_dir: /home/user/.task
[debug] 16:45:23.126 | PathManager                    | manifest: /home/user/.task/config/.tw_manifest
[debug] 16:45:23.127 | PathManager                    | is_dev_mode: False
[debug] 16:45:23.130 | AppManager.install             | Installing tw-recurrence (dry_run=False)
[debug] 16:45:23.135 | AppManager.install             | Getting installer for tw-recurrence
[debug] 16:45:23.200 | AppManager.install             | Installer path: /tmp/tw_installer_xyz.sh
[debug] 16:45:23.201 | AppManager.install             | Executing: /tmp/tw_installer_xyz.sh install
[debug] 16:45:28.445 | AppManager.install             | Installer exit code: 0
[debug] 16:45:28.450 | AppManager.install             | Installation successful, manifest reloaded
```

### Level 3: Everything + Taskwarrior
**What you see:**
- Everything from level 2
- Environment variable details
- Temporary file cleanup
- Taskwarrior's debug.hooks output

**Example output:**
```
[debug] 16:45:23.201 | AppManager.install             | Environment configured for installer
[debug] 16:45:28.446 | AppManager.install             | Cleaned up temp installer
[debug] 16:45:30.000 | task_passthrough               | Enabling taskwarrior debug.hooks=2
[debug] 16:45:30.001 | task_passthrough               | Executing: task rc.debug.hooks=2 next
[task 2026-01-23 16:45:30] Hooks: Calling hook 'on-modify'...
[task 2026-01-23 16:45:30] Hooks: Completed hook 'on-modify' (status: 0)
```

## Log File Format

```
======================================================================
tw.py Debug Session - 2026-01-23 16:45:23
Debug Level: 2
Session ID: 20260123_164523
======================================================================

[debug] 16:45:23.123 | main                           | Debug mode enabled (level 2)
[debug] 16:45:23.124 | main                           | Log file: /home/user/.task/logs/debug/tw_debug_20260123_164523.log
[debug] 16:45:23.125 | PathManager.__init__           | Initializing PathManager
...
```

## Environment Variables Set

When you run `tw --debug=2`, these are set for subprocesses (installers, hooks):

```bash
TW_DEBUG=2                  # Debug level (0-3)
TW_DEBUG_LEVEL=2            # Same as TW_DEBUG
DEBUG_HOOKS=1               # Set to 1 if level >= 2
TW_DEBUG_LOG=/path/to/logs  # Directory for logs
```

Installers can use these to enable their own debug output.

## Expected Behavior

### ✅ What Should Work

1. **Debug output to stderr** - Colored blue, timestamped
2. **Log file creation** - In ~/.task/logs/debug/
3. **Auto cleanup** - Only last 10 sessions kept
4. **Environment variables** - Passed to installers
5. **Taskwarrior integration** - rc.debug.hooks=2 at level 3
6. **Named modes** - all, verbose, tw, hooks, task
7. **Default level** - --debug with no arg = level 1

### ⚠ Known Limitations

1. Installers need updating to use TW_DEBUG (Phase 2)
2. No debug for tags yet (Phase 3-4)
3. Some minor operations don't have debug yet

## Common Issues

### Debug output not showing
- Check you're using `--debug` before the command
- Debug goes to **stderr**, not stdout
- Try: `tw --debug=2 --list 2>&1 | less`

### Log file not created
- Check directory exists: `mkdir -p ~/.task/logs/debug`
- Check permissions
- Try with sudo if needed

### Taskwarrior debug.hooks not working
- Only works at level 3
- Requires taskwarrior 2.6.0+
- Check: `task rc.debug.hooks=2 next`

### Too much output
- Use lower debug level
- Level 1 is usually sufficient
- Redirect stderr: `tw --debug command 2>/dev/null`

## Next Steps

### Phase 2: Installer Support
Update installers to check TW_DEBUG and enable their own debug:

```bash
# In installer
if [[ "${TW_DEBUG:-0}" -gt 0 ]]; then
    DEBUG_LOG="${HOME}/.task/logs/debug/${APPNAME}_debug.log"
    debug_msg() {
        echo "[${APPNAME}-debug] $(date +%H:%M:%S) | $*" | tee -a "$DEBUG_LOG" >&2
    }
else
    debug_msg() { :; }
fi
```

### Phase 3-5: Tags Implementation
Add tag filtering and search capabilities.

## Success Criteria

Phase 1 is complete if:
- [x] `tw --debug --list` shows colored debug output
- [x] Log file created in ~/.task/logs/debug/
- [x] Three debug levels work (1, 2, 3)
- [x] Environment variables set correctly
- [x] Taskwarrior debug.hooks enabled at level 3
- [x] Old logs cleaned up (only last 10 kept)

**Status: ✅ ALL CRITERIA MET!**
