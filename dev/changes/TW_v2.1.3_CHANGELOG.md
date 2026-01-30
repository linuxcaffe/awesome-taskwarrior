# tw v2.1.3 - Bug Fixes and Enhancements

## Summary
Fixed critical flag parsing issues and enhanced version output. Renamed all references from "tw.py" to "tw" to reflect actual command usage.

---

## Bug Fixes

### 1. **Flags Must Be First Argument Only** 🔴 CRITICAL

#### Problem
Flags were recognized anywhere in the command line, causing false positives:
```bash
# WRONG - this would start shell mode:
tw add fix the --shell bug

# WRONG - this would trigger list:
tw list +work --install something
```

#### Root Cause
No validation that flags must be the first argument. The `parse_known_args()` method would find flags anywhere in sys.argv.

#### Fix Applied
Added `validate_first_arg_flag()` function that checks:
- Flag must be in position 0 (first argument)
- If first arg starts with `-`, it must be a known flag
- Unknown flags throw errors immediately

**New behavior:**
```bash
# Correct - flag is first:
tw --shell

# Correct - passes through to task:
tw add fix the --shell bug

# Error - unknown flag:
tw --random
# Output: [tw] Error: Unknown flag: --random
```

---

### 2. **Flags Must Have Trailing Space** 🔴 CRITICAL

#### Problem
Flags were partially matched even when embedded in other text:
```bash
# WRONG - this would match "-l" flag:
tw 42 mod -lena

# WRONG - this would match "-I":
tw list -Important tasks
```

#### Root Cause
No check that flags are standalone arguments with proper spacing.

#### Fix Applied
The `validate_first_arg_flag()` function now checks:
- If arg starts with a known flag but has more characters, treat as unknown
- Example: `-lena` starts with `-l` but is longer, so it's an unknown flag

**New behavior:**
```bash
# Correct - flag is standalone:
tw -l

# Correct - passes through to task:
tw 42 mod -lena
# (taskwarrior gets: 42 mod -lena)

# Error - partial match of flag:
tw -lena
# Output: [tw] Error: Unknown flag: -lena
```

---

### 3. **Unknown Flags Must Throw Errors** 🔴 CRITICAL

#### Problem
Unknown flags were silently ignored:
```bash
# WRONG - no error, just confusing behavior:
tw --random
tw --xyz
tw --foobar
```

#### Root Cause
Used `parse_known_args()` which silently ignores unknown arguments.

#### Fix Applied
Pre-validation in `validate_first_arg_flag()` before argparse runs:
- Checks against list of known flags
- Returns error message for unknown flags
- Displays help hint

**New behavior:**
```bash
tw --random
# Output:
# [tw] Error: Unknown flag: --random
# [tw] Use 'tw --help' for usage information
```

---

## Enhancements

### 4. **Enhanced --version Output** ✨

#### Before
```bash
tw --version
# Output: tw.py version 2.1.2
```

#### After
```bash
tw --version
# Output:
# taskwarrior 2.6.2
# tw v2.1.3
#
# Installed extensions:
#   agenda-edate v1.0.0
#   need-priority v0.3.5
#   recurrence v2.0.0
```

Shows:
- Taskwarrior version (from `task --version`)
- tw version
- All installed extensions with versions (from manifest)

---

### 5. **Renamed tw.py → tw Throughout** ✨

All references updated:
- **Docstring header**: "tw - awesome-taskwarrior..."
- **Debug logs**: "tw Debug Session"
- **Comments**: "Handle tw commands"
- **Help text**: "--version: Show tw version"
- **Error messages**: All updated

The file should now be installed as `tw` (no extension):
```bash
# Installation:
cp tw /usr/local/bin/tw
chmod +x /usr/local/bin/tw

# Usage:
tw --help
tw --version
tw -I agenda-edate
```

---

## Implementation Details

### New Helper Functions

**`validate_first_arg_flag(args)`**
```python
def validate_first_arg_flag(args):
    """
    Validate that flags are only recognized when:
    1. They are the first argument
    2. They have a trailing space (not part of another word)
    3. They are known flags
    
    Returns: (is_valid_flag, error_message)
    """
```

**`get_taskwarrior_version()`**
```python
def get_taskwarrior_version():
    """Get taskwarrior version"""
    # Runs: task --version
    # Returns: "2.6.2"
```

**`get_installed_extensions(paths)`**
```python
def get_installed_extensions(paths):
    """Get list of installed extensions with versions from manifest"""
    # Reads: ~/.task/config/.tw_manifest
    # Returns: {'app-name': 'version', ...}
```

### Known Flags List
```python
known_short = ['-I', '-r', '-u', '-l', '-i', '-v', '-h', '-s']
known_long = ['--install', '--remove', '--update', '--list', '--info', 
              '--verify', '--tags', '--dry-run', '--debug', 
              '--version', '--help', '--shell']
```

---

## Testing Examples

### Test 1: Flag Position Validation
```bash
# Should work - flag first:
tw --shell
tw -l
tw --version

# Should pass through to task - flag not first:
tw add fix --shell bug
tw 42 mod +urgent
tw list +work

# Should error - unknown flag first:
tw --random
# [tw] Error: Unknown flag: --random
# [tw] Use 'tw --help' for usage information
```

### Test 2: Flag Spacing Validation
```bash
# Should work - proper spacing:
tw -l
tw -I agenda-edate

# Should pass through - embedded in text:
tw 42 mod -lena description
tw add -Important task

# Should error - flag without space:
tw -lena
# [tw] Error: Unknown flag: -lena
```

### Test 3: Unknown Flag Detection
```bash
# All of these should error:
tw --foobar
tw --xyz
tw -z
tw --random-flag

# Output:
# [tw] Error: Unknown flag: --foobar
# [tw] Use 'tw --help' for usage information
```

### Test 4: Enhanced Version Output
```bash
tw --version

# Expected output:
# taskwarrior 2.6.2
# tw v2.1.3
#
# Installed extensions:
#   agenda-edate v1.0.0
#   need-priority v0.3.5
```

---

## Migration from v2.1.2

### File Rename
```bash
# Old installation:
/usr/local/bin/tw.py

# New installation:
/usr/local/bin/tw

# Update:
sudo rm /usr/local/bin/tw.py
sudo cp tw /usr/local/bin/tw
sudo chmod +x /usr/local/bin/tw
```

### Behavior Changes

**1. Stricter Flag Parsing**
If you had scripts that relied on flags anywhere in arguments, they will now fail:
```bash
# Old: worked (incorrectly)
tw add +work --list tasks

# New: passes through to task correctly
tw add +work --list tasks
```

**2. Unknown Flags Now Error**
If you used undefined flags, they now throw errors:
```bash
# Old: silently ignored
tw --my-custom-flag

# New: errors
tw --my-custom-flag
# [tw] Error: Unknown flag: --my-custom-flag
```

**3. Version Output Changed**
```bash
# Old:
tw.py version 2.1.2

# New:
taskwarrior 2.6.2
tw v2.1.3

Installed extensions:
  agenda-edate v1.0.0
```

---

## Compatibility

### Backward Compatible ✅
- All existing valid flag usage works unchanged
- Pass-through to taskwarrior unchanged
- Package management commands unchanged
- Shell mode unchanged
- Manifest format unchanged

### Breaking Changes ⚠️
1. **Unknown flags now error** (previously silently ignored)
2. **Flags must be first argument** (previously worked anywhere)
3. **File should be named `tw`** (not `tw.py`)
4. **Version output format changed** (now multi-line with extensions)

---

## Version History

### v2.1.3 (Current)
- ✅ Fixed: Flags must be first argument only
- ✅ Fixed: Flags must have trailing space
- ✅ Fixed: Unknown flags throw errors
- ✅ Enhanced: --version shows taskwarrior and extensions
- ✅ Renamed: All tw.py references to tw

### v2.1.2 (Previous)
- Dev mode indicator
- Unicode symbols → ASCII
- PathManager.registry_dir property

### v2.1.0
- Short command flags (-I, -r, -u, -l, -i)
- Enhanced debug capabilities
- Tag filtering improvements

### v2.0.0
- Curl-based installation (removed git)
- Per-file manifest tracking
- Installer independence

---

## Known Issues
None at this time. v2.1.3 is considered stable for production use.

---

## Quick Reference Card

### Valid Flag Usage
```bash
tw --help              # ✅ Flag first
tw --version           # ✅ Flag first
tw -l                  # ✅ Flag first
tw -I app-name         # ✅ Flag first
tw --shell             # ✅ Flag first

tw add fix --shell     # ✅ Not a tw flag, passes through
tw 42 mod -lena        # ✅ Not a tw flag, passes through
```

### Invalid Flag Usage
```bash
tw --random            # ❌ Unknown flag
tw -xyz                # ❌ Unknown flag
tw -lena               # ❌ Unknown flag (partial match)
tw add --list work     # ✅ Not first, passes through correctly
```

### Version Information
```bash
tw --version
# Shows:
# - Taskwarrior version
# - tw version
# - All installed extensions
```

---

**tw v2.1.3** - Smart coding over quick fixes! 🎯
