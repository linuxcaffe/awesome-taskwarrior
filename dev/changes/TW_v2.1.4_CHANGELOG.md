# tw v2.1.4 - Flag Syntax Fix

## Bug Fix: --flag=value Syntax Not Recognized

### Problem
Flags with equals syntax (like `--debug=2`) were not being recognized as valid tw flags, causing them to be treated as unknown flags.

```bash
# This worked:
tw --debug 2

# This didn't work:
tw --debug=2
# Error: Unknown flag: --debug=2
```

### Root Cause
The validation function only checked for exact matches against the known flags list. It didn't handle the `--flag=value` syntax where the flag and value are combined with `=`.

**Lines 1365-1367 (before fix):**
```python
# Check if it's a known flag
if first_arg in known_short or first_arg in known_long:
    return (True, None)
```

This only matched `--debug`, not `--debug=2`.

### Fix Applied
Added handling for `=` syntax by splitting the argument and checking the flag part:

```python
# Check if it's a known flag (exact match)
if first_arg in known_short or first_arg in known_long:
    return (True, None)

# Check for flags with = syntax (e.g., --debug=2)
if '=' in first_arg:
    flag_part = first_arg.split('=')[0]
    if flag_part in known_long:
        return (True, None)
```

### Now Works
```bash
# Both syntaxes work:
tw --debug 2         ✅ Works
tw --debug=2         ✅ Works

# Can be used with other flags:
tw --debug=2 --list  ✅ Works
tw --debug=2 -I app  ✅ Works
```

### Testing
```bash
# Test debug with = syntax:
tw --debug=2 --version

# Should show:
# [tw-debug] sys.argv = ['tw', '--debug=2', '--version']
# [tw-debug] first_arg = '--debug=2'
# [tw-debug] is_valid = True, error_msg = None
# [tw-debug] First arg is valid tw flag, processing with argparse
# taskwarrior 2.6.2
# tw v2.1.4
# ...
```

---

## All Changes in v2.1.4

### ✅ Fixed: Flags with = syntax
- `--debug=2` now recognized as valid tw flag
- `--install=app` would work (if argparse supported it)
- Any `--flag=value` syntax properly validated

### Test Cases
```bash
tw --debug=2 --list              ✅ Valid
tw --debug=2 -I app             ✅ Valid  
tw --verify=app                 ✅ Valid
tw --random=value               ❌ Error (unknown flag)
```

---

## Version History

### v2.1.4 (Current)
- ✅ Fixed: Flags with = syntax now recognized

### v2.1.3
- ✅ Fixed: Flags must be first argument only
- ✅ Fixed: Flags must have trailing space
- ✅ Fixed: Unknown flags throw errors
- ✅ Enhanced: --version output
- ✅ Added: TW_DEBUG_WRAPPER

---

## Installation

```bash
# Copy to your scripts directory
cp tw ~/.task/scripts/tw
chmod +x ~/.task/scripts/tw

# Verify version
tw --version
# Should show: tw v2.1.4
```

---

## Quick Test

```bash
# Enable wrapper debug and extension debug:
TW_DEBUG_WRAPPER=1 tw --debug=2 add test

# Should show:
# [tw-debug] sys.argv = ['tw', '--debug=2', 'add', 'test']
# [tw-debug] first_arg = '--debug=2'
# [tw-debug] is_valid = True, error_msg = None
# [tw-debug] First arg is valid tw flag, processing with argparse
# [tw] Debug log: ~/.task/logs/debug/tw_debug_TIMESTAMP.log
# ... task execution with debug enabled ...
```

---

**tw v2.1.4** - Now with proper --flag=value support! 🎯
