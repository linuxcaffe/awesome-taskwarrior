# tw v2.1.3 - Final with Baked-in Debug

## New Feature: TW_DEBUG_WRAPPER Environment Variable

### Overview
The `tw` wrapper now includes built-in debug output that can be enabled via environment variable, similar to taskwarrior's native `TW_DEBUG` for hooks.

### Usage

**Enable debug mode:**
```bash
TW_DEBUG_WRAPPER=1 tw <command>
```

**Examples:**
```bash
# Debug flag validation
TW_DEBUG_WRAPPER=1 tw add test --shell bug

# Debug pass-through behavior  
TW_DEBUG_WRAPPER=1 tw 42 mod -ltag

# Debug tw flag processing
TW_DEBUG_WRAPPER=1 tw --list

# Debug unknown flag handling
TW_DEBUG_WRAPPER=1 tw --random
```

### Debug Output Format

The debug output goes to stderr (so it doesn't interfere with task output) and shows:

```
[tw-debug] sys.argv = ['tw', 'add', 'test', '--shell', 'bug']
[tw-debug] first_arg = 'add'
[tw-debug] is_valid = False, error_msg = None
[tw-debug] First arg not a tw flag, passing through to task
[tw-debug] Executing: task add test --shell bug
```

### What It Shows

1. **Full command line**: Complete sys.argv to see exactly what tw received
2. **First argument**: What tw considers as the "first arg" for validation
3. **Validation result**: Whether first arg is a valid tw flag and any error
4. **Flow path**: Which code path was taken:
   - "passing through to task" - Not a tw flag, goes directly to taskwarrior
   - "processing with argparse" - Valid tw flag, tw handles it
   - "Flag-like but invalid" - Starts with - but unknown (error case)

### Example Sessions

**Case 1: Pass-through (task command)**
```bash
$ TW_DEBUG_WRAPPER=1 tw add +test pro:tw test flags
[tw-debug] sys.argv = ['tw', 'add', '+test', 'pro:tw', 'test', 'flags']
[tw-debug] first_arg = 'add'
[tw-debug] is_valid = False, error_msg = None
[tw-debug] First arg not a tw flag, passing through to task
[tw-debug] Executing: task add +test pro:tw test flags
Created task 71.
```

**Case 2: tw flag (wrapper command)**
```bash
$ TW_DEBUG_WRAPPER=1 tw --version
[tw-debug] sys.argv = ['tw', '--version']
[tw-debug] first_arg = '--version'
[tw-debug] is_valid = True, error_msg = None
[tw-debug] First arg is valid tw flag, processing with argparse
taskwarrior 2.6.2
tw v2.1.3

Installed extensions:
  need-priority v0.3.5
```

**Case 3: Unknown flag (error)**
```bash
$ TW_DEBUG_WRAPPER=1 tw --random
[tw-debug] sys.argv = ['tw', '--random']
[tw-debug] first_arg = '--random'
[tw-debug] is_valid = False, error_msg = Unknown flag: --random
[tw] Error: Unknown flag: --random
[tw] Use 'tw --help' for usage information
```

**Case 4: Embedded flag in task command**
```bash
$ TW_DEBUG_WRAPPER=1 tw 42 mod -lena description
[tw-debug] sys.argv = ['tw', '42', 'mod', '-lena', 'description']
[tw-debug] first_arg = '42'
[tw-debug] is_valid = False, error_msg = None
[tw-debug] First arg not a tw flag, passing through to task
[tw-debug] Executing: task 42 mod -lena description
Modified 1 task.
```

### Benefits

1. **Troubleshooting**: See exactly how tw interprets your commands
2. **Learning**: Understand the difference between tw flags and task arguments
3. **Development**: Test flag validation logic without modifying code
4. **Bug reporting**: Include debug output when reporting issues

### Permanent Enable (optional)

If you want debug always on:

```bash
# In your .bashrc or .zshrc:
export TW_DEBUG_WRAPPER=1

# Or create an alias:
alias twd='TW_DEBUG_WRAPPER=1 tw'
```

### Disable

Simply don't set the variable, or set it to 0:

```bash
TW_DEBUG_WRAPPER=0 tw ...
# Or just:
tw ...
```

### Comparison with --debug Flag

| Feature | TW_DEBUG_WRAPPER | --debug |
|---------|------------------|---------|
| Purpose | Shows tw wrapper logic | Shows extension hook logic |
| Output | Argument parsing flow | Hook execution details |
| Target | tw script itself | Installed extensions |
| Format | Inline stderr | Log files in ~/.task/logs |
| Usage | `TW_DEBUG_WRAPPER=1 tw ...` | `tw --debug=2 ...` |

Both can be used together:
```bash
TW_DEBUG_WRAPPER=1 tw --debug=2 add test
```

This shows:
1. How tw parses arguments (TW_DEBUG_WRAPPER)
2. How hooks process the task (--debug=2)

---

## All Fixes in v2.1.3

### ✅ Fixed: Flags Must Be First Argument
```bash
# Now works correctly:
tw add test --shell bug    # Passes to task, doesn't start shell
tw 42 mod -ltag           # Passes to task, doesn't invoke --list
```

### ✅ Fixed: Flags Must Have Trailing Space  
```bash
# Now works correctly:
tw -l                     # Invokes --list
tw -lena                  # Error: unknown flag
```

### ✅ Fixed: Unknown Flags Throw Errors
```bash
# Now errors properly:
tw --random              # Error: Unknown flag: --random
```

### ✅ Enhanced: Version Output
```bash
tw --version
# Shows taskwarrior version, tw version, and installed extensions
```

### ✅ Added: Wrapper Debug Mode
```bash
TW_DEBUG_WRAPPER=1 tw ...
# Shows argument parsing flow
```

---

## Installation

```bash
# Copy to your scripts directory
cp tw ~/.task/scripts/tw
chmod +x ~/.task/scripts/tw

# Or system-wide
sudo cp tw /usr/local/bin/tw
sudo chmod +x /usr/local/bin/tw

# Verify version
tw --version
```

---

## Quick Reference Card

### Debug Commands
```bash
# Show wrapper debug
TW_DEBUG_WRAPPER=1 tw add test

# Show extension debug  
tw --debug=2 add test

# Show both
TW_DEBUG_WRAPPER=1 tw --debug=2 add test

# Show help
tw --help
```

### Flag Behavior
```bash
# tw flags (first position only)
tw --version              ✅ tw processes
tw --list                 ✅ tw processes
tw -I app-name           ✅ tw processes

# Not tw flags (pass through)
tw add test              ✅ task processes
tw 42 mod description    ✅ task processes
tw add test --shell bug  ✅ task processes (--shell not in position 1)
```

### Error Cases
```bash
tw --random              ❌ Error: Unknown flag
tw -lena                 ❌ Error: Unknown flag
```

---

**tw v2.1.3** - Now with baked-in debug! 🎯
