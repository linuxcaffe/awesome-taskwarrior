# Debug Mode - Complete Guide

## Overview

awesome-taskwarrior includes comprehensive debug capabilities for troubleshooting installations, understanding operations, and developing extensions.

## Quick Start

```bash
# Basic debug
tw --debug --list

# Detailed debug
tw --debug=2 --install tw-recurrence

# Everything + taskwarrior hooks
tw --debug=3 task next
```

## Debug Levels

### Level 1: Basic Operations
**What you see:**
- Major operations (install, remove, update, list)
- Success/failure status
- Error messages
- Installation completion

**When to use:**
- Verifying operations completed
- Basic troubleshooting
- Confirming installations

**Example output:**
```
[debug] 16:45:23.123 | main              | Debug mode enabled (level 1)
[debug] 16:45:23.130 | AppManager.install| Installing tw-recurrence
[debug] 16:45:23.200 | tw-recurrence     | Debug enabled (level 1)
[debug] 16:45:23.202 | tw-recurrence     | Starting installation
[debug] 16:45:28.450 | tw-recurrence     | Installation complete
[debug] 16:45:28.455 | AppManager.install| Installation successful
```

### Level 2: Detailed Operations
**What you see:**
- Everything from level 1
- File paths and locations
- Download operations
- Subprocess calls
- Manifest updates
- Configuration details

**When to use:**
- Debugging installation issues
- Tracking file placements
- Understanding what's happening
- Extension development

**Example output:**
```
[debug] 16:45:23.123 | main              | Debug mode enabled (level 2)
[debug] 16:45:23.124 | main              | Log file: ~/.task/logs/debug/tw_debug_20260123_164523.log
[debug] 16:45:23.130 | AppManager.install| Installing tw-recurrence
[debug] 16:45:23.135 | AppManager.install| Getting installer for tw-recurrence
[debug] 16:45:23.200 | AppManager.install| Installer path: /tmp/tw_installer_xyz.sh
[debug] 16:45:23.201 | AppManager.install| Executing: /tmp/tw_installer_xyz.sh install
[debug] 16:45:23.202 | tw-recurrence     | Debug enabled (level 2)
[debug] 16:45:23.203 | tw-recurrence     | BASE_URL: https://raw.githubusercontent.com/...
[debug] 16:45:23.204 | tw-recurrence     | HOOKS_DIR: ~/.task/hooks
[debug] 16:45:23.210 | tw-recurrence     | Downloading hook: on-add_recurrence.py
[debug] 16:45:25.100 | tw-recurrence     | Installed: ~/.task/hooks/on-add_recurrence.py
```

### Level 3: Everything + Taskwarrior
**What you see:**
- Everything from level 2
- Environment variables
- Temporary file cleanup
- Taskwarrior's debug.hooks output
- Hook execution details

**When to use:**
- Deep debugging
- Hook development
- Understanding full workflow
- Reporting complex bugs

**Example output:**
```
[debug] 16:45:23.201 | AppManager.install| Environment configured for installer
[debug] 16:45:28.446 | AppManager.install| Cleaned up temp installer
[debug] 16:45:30.000 | task_passthrough  | Enabling taskwarrior debug.hooks=2
[debug] 16:45:30.001 | task_passthrough  | Executing: task rc.debug.hooks=2 next
[task 2026-01-23 16:45:30] Hooks: Calling hook 'on-modify'...
[task 2026-01-23 16:45:30] Hooks: Completed hook 'on-modify' (status: 0)
```

## Named Debug Modes

Instead of levels, you can use descriptive names:

```bash
tw --debug=tw <command>       # Same as level 1
tw --debug=hooks <command>    # Same as level 2
tw --debug=task <command>     # Same as level 3
tw --debug=all <command>      # Same as level 3
tw --debug=verbose <command>  # Same as level 3
```

## Debug Output

### Output Locations

**1. Screen (stderr)**
- Color-coded blue
- Timestamped with milliseconds
- Real-time during execution
- Doesn't mix with normal output

**2. tw.py Log File**
- Location: `~/.task/logs/debug/tw_debug_TIMESTAMP.log`
- Contains all tw.py debug output
- Session-based (one per run)
- Auto-cleanup (keeps last 10)

**3. Extension Log Files**
- Location: `~/.task/logs/debug/APPNAME_debug_TIMESTAMP.log`
- One per extension per run
- Contains extension-specific debug
- Created only when installer runs with debug

### Log Format

```
======================================================================
tw.py Debug Session - 2026-01-23 16:45:23
Debug Level: 2
Session ID: 20260123_164523
======================================================================

[debug] 16:45:23.123 | context (30 chars)     | message
[debug] 16:45:23.124 | another_context        | another message
```

**Columns:**
- `[debug]` - Marker
- `16:45:23.123` - Timestamp with milliseconds
- `context` - Where the message came from (function, class, etc.)
- `message` - The actual debug message

## Environment Variables

When debug is enabled, tw.py sets these for installers:

```bash
TW_DEBUG=2                    # Debug level (1-3)
TW_DEBUG_LEVEL=2              # Same as TW_DEBUG
DEBUG_HOOKS=1                 # Set to 1 if level >= 2
TW_DEBUG_LOG=/path/to/debug   # Debug log directory
```

**Installers should check these:**

```bash
if [[ "${TW_DEBUG:-0}" -gt 0 ]]; then
    # Enable debug
    DEBUG_LOG="${TW_DEBUG_LOG}/myapp_debug_$(date +%Y%m%d_%H%M%S).log"
    
    debug_msg() {
        echo "[debug] $(date +%H:%M:%S) | myapp | $1" | tee -a "$DEBUG_LOG" >&2
    }
else
    debug_msg() { :; }  # No-op
fi
```

## Common Use Cases

### Installation Troubleshooting

```bash
# Extension won't install
tw --debug=2 --install problematic-app

# Check what's happening:
cat ~/.task/logs/debug/tw_debug_*.log
cat ~/.task/logs/debug/problematic-app_debug_*.log

# Look for:
# - Download failures
# - Permission errors
# - Missing directories
# - Manifest issues
```

### Hook Development

```bash
# Test hook with full debug
tw --debug=3 task add "Test task"

# See:
# - When hook is called
# - What it receives
# - What it outputs
# - Exit status
```

### Understanding Workflow

```bash
# See complete installation flow
tw --debug=2 --install tw-recurrence

# Observe:
# 1. Registry fetch
# 2. Installer download
# 3. File downloads
# 4. File placements
# 5. Manifest updates
```

### Bug Reporting

```bash
# Generate comprehensive debug log
tw --debug=3 --install problematic-app 2>&1 | tee debug-output.txt

# Attach to bug report:
# - debug-output.txt
# - ~/.task/logs/debug/tw_debug_*.log
# - ~/.task/logs/debug/problematic-app_debug_*.log
```

## Tips & Tricks

### Redirect Debug to File

```bash
# Capture all debug output
tw --debug=2 --install app 2>&1 | tee debug.log
```

### Watch Logs in Real-Time

```bash
# In one terminal:
tw --debug=2 --install app

# In another terminal:
tail -f ~/.task/logs/debug/tw_debug_*.log
tail -f ~/.task/logs/debug/app_debug_*.log
```

### Debug Only Installers

```bash
# Use environment variable directly
TW_DEBUG=2 bash installers/my-app.install install

# Installer will create debug log even without tw.py
```

### Find Recent Debug Sessions

```bash
# List by timestamp
ls -lt ~/.task/logs/debug/

# Find specific app logs
ls ~/.task/logs/debug/*recurrence*

# View most recent
cat $(ls -t ~/.task/logs/debug/tw_debug_*.log | head -1)
```

### Clean Old Logs

```bash
# Manual cleanup (keeps last 10)
cd ~/.task/logs/debug/
ls -t tw_debug_*.log | tail -n +11 | xargs rm -f

# Or remove all
rm -rf ~/.task/logs/debug/*
```

## Troubleshooting Debug Mode

### Debug Output Not Showing

**Problem:** No debug output even with `--debug`

**Solutions:**
1. Check you're using the updated tw.py
2. Debug goes to **stderr**, not stdout
3. Try: `tw --debug --list 2>&1 | less`
4. Check file: `cat ~/.task/logs/debug/tw_debug_*.log`

### Log Files Not Created

**Problem:** No log files in `~/.task/logs/debug/`

**Solutions:**
1. Check directory exists: `mkdir -p ~/.task/logs/debug`
2. Check permissions: `ls -la ~/.task/logs/`
3. Verify debug is enabled: `tw --debug --version`

### Too Much Output

**Problem:** Debug output is overwhelming

**Solutions:**
1. Use lower level: `--debug` instead of `--debug=3`
2. Redirect stderr: `tw --debug=2 command 2>/dev/null`
3. Only view logs: `tw --debug=2 command >/dev/null 2>&1; cat ~/.task/logs/debug/tw_debug_*.log`

### Colors Not Showing

**Problem:** No color in debug output

**Solutions:**
- This is normal - colors might not work in all terminals
- Functionality is the same
- Check logs - they don't have color codes

## For Extension Developers

### Adding Debug to Your Installer

Use `make-awesome-install.sh` - it automatically adds debug support!

Or manually add this block:

```bash
# After tw_msg/tw_error definitions, before install():

if [[ "${TW_DEBUG:-0}" -gt 0 ]] || [[ "${DEBUG_HOOKS:-0}" == "1" ]]; then
    DEBUG_ENABLED=1
    DEBUG_LEVEL="${TW_DEBUG_LEVEL:-${TW_DEBUG:-1}}"
    DEBUG_LOG_DIR="${TW_DEBUG_LOG:-$HOME/.task/logs/debug}"
    DEBUG_LOG="${DEBUG_LOG_DIR}/myapp_debug_$(date +%Y%m%d_%H%M%S).log"
    
    mkdir -p "$DEBUG_LOG_DIR"
    
    debug_msg() {
        local level="${2:-1}"
        if [[ "$DEBUG_LEVEL" -ge "$level" ]]; then
            local timestamp=$(date +"%H:%M:%S.%N" | cut -c1-12)
            local msg="[debug] $timestamp | myapp | $1"
            echo -e "\033[34m$msg\033[0m" >&2
            echo "$msg" >> "$DEBUG_LOG"
        fi
    }
    
    debug_msg "Debug enabled (level $DEBUG_LEVEL)" 1
else
    debug_msg() { :; }
fi
```

### Debug Best Practices

**Level 1 messages:**
- Start/complete of major operations
- Success/failure status
- Critical errors

**Level 2 messages:**
- File downloads
- File installations
- Configuration updates
- Manifest writes

**Level 3 messages:**
- Environment details
- Temporary file operations
- Detailed state information

## See Also

- [API.md](API.md) - Environment variables reference
- [CONTRIBUTING.md](CONTRIBUTING.md) - Testing with debug
- [QUICKSTART.md](QUICKSTART.md) - Quick debug examples
