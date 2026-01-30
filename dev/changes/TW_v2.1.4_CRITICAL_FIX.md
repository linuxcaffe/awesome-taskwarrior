# tw v2.1.4 - CRITICAL ARGPARSE FIX

## The Real Bug: argparse Scanning All Arguments

### The Problem
Even with all our validation, `parse_known_args()` was **scanning the entire argument list** for known flags, not just the consecutive flags at the beginning.

**Example of the bug:**
```bash
tw --debug=2 add +test pro:tw.tw yet another --shell test
```

What happened:
1. Validation: `--debug=2` is first arg → Valid tw flag ✓
2. Goes to argparse ✓  
3. argparse processes `--debug=2` ✓
4. **argparse ALSO finds `--shell` later in args** ✗
5. Sets `args.shell = True` ✗
6. Starts shell mode instead of passing to task! ✗

### Root Cause
`parse_known_args()` behavior:
```python
# This scans ALL arguments:
args, remaining = parser.parse_known_args()

# So with: ['--debug=2', 'add', 'test', '--shell', 'bug']
# argparse finds BOTH --debug=2 AND --shell
# Even though --shell is NOT in first position!
```

### The Fix
Manually split arguments BEFORE argparse sees them:

```python
# Split into consecutive flags and everything else
args_for_parser = []    # Only consecutive flags from start
remaining_args = []     # Everything after first non-flag

for arg in sys.argv[1:]:
    if found_non_flag:
        remaining_args.append(arg)
    elif arg.startswith('-'):
        args_for_parser.append(arg)
    else:
        found_non_flag = True
        remaining_args.append(arg)

# Now argparse only sees the flags we want it to see
args, extra = parser.parse_known_args(args_for_parser)
remaining = extra + remaining_args
```

### How It Works Now

**Example 1: tw flag then task command**
```bash
tw --debug=2 add +test --shell bug
```
- args_for_parser: `['--debug=2']` ← Only this goes to argparse
- remaining_args: `['add', '+test', '--shell', 'bug']` ← Goes to task
- Result: Debug enabled, `--shell` passed to task ✓

**Example 2: Multiple tw flags**
```bash
tw --debug=2 --list
```
- args_for_parser: `['--debug=2', '--list']` ← Both are consecutive flags
- remaining_args: `[]`
- Result: Both flags processed by tw ✓

**Example 3: No tw flags**
```bash
tw add test --shell bug
```
- First arg `add` triggers early return (before argparse)
- Everything goes to task ✓

**Example 4: Shell with args**
```bash
tw --shell add +work
```
- args_for_parser: `['--shell']`
- remaining_args: `['add', '+work']`
- Result: Shell mode with initial command ✓

### Debug Output
With `TW_DEBUG_WRAPPER=1`:
```bash
$ TW_DEBUG_WRAPPER=1 tw --debug=2 add test --shell bug
[tw-debug] sys.argv = ['tw', '--debug=2', 'add', 'test', '--shell', 'bug']
[tw-debug] first_arg = '--debug=2'
[tw-debug] is_valid = True, error_msg = None
[tw-debug] First arg is valid tw flag, processing with argparse
[tw-debug] args_for_parser = ['--debug=2']
[tw-debug] remaining_args = ['add', 'test', '--shell', 'bug']
[tw-debug] Parsed args: {'debug': '2', 'shell': False, ...}
[tw-debug] Final remaining: ['add', 'test', '--shell', 'bug']
[DEBUG-1] Set TW_DEBUG=2
[DEBUG-1] tw v2.1.4 debug session started
Created task 75.
```

Notice:
- `args_for_parser = ['--debug=2']` ← Only the first flag!
- `remaining_args = ['add', 'test', '--shell', 'bug']` ← Rest goes to task
- `'shell': False` ← Shell NOT triggered!

### Testing

**Test 1: Verify --shell doesn't trigger**
```bash
tw --debug=2 add test --shell bug
# Should create task, NOT start shell
# Task description should be: "test --shell bug"
```

**Test 2: Verify --shell DOES work when first**
```bash
tw --shell add test
# Should start shell with initial command "add"
```

**Test 3: Multiple tw flags**
```bash
tw --debug=2 --list
# Should enable debug AND list packages
```

**Test 4: Task command only**
```bash
tw add test --list
# Should create task with description "test --list"
# Should NOT list packages
```

---

## All Fixes in v2.1.4

### ✅ Fixed: argparse now only sees consecutive flags
The critical fix - argparse can no longer find flags that appear after non-flag arguments.

### ✅ Fixed: Flags with = syntax  
`--debug=2` recognized as valid tw flag.

### ✅ All previous fixes still work
- Flags must be first argument
- Unknown flags throw errors
- Enhanced --version output
- TW_DEBUG_WRAPPER support

---

## How the Complete System Works

### 1. First Argument Validation
```bash
tw <first-arg> ...
```
- If `<first-arg>` doesn't start with `-` → Pass ALL args to task immediately
- If `<first-arg>` is unknown flag → Error
- If `<first-arg>` is valid tw flag → Continue to step 2

### 2. Argument Splitting
```bash
tw --flag1 --flag2 non-flag --flag3 ...
```
- Collect consecutive flags: `['--flag1', '--flag2']`
- Everything after first non-flag: `['non-flag', '--flag3', ...]`

### 3. Argparse Processing
- Only sees: `['--flag1', '--flag2']`
- Cannot see: `['non-flag', '--flag3', ...]`
- Processes tw commands or passes remaining to task

### Examples Flow

**tw add test --shell bug**
1. First arg: `add` → not a flag → EARLY RETURN to task
2. Never reaches argparse
3. Task gets: `['add', 'test', '--shell', 'bug']`

**tw --debug=2 add test --shell bug**
1. First arg: `--debug=2` → valid tw flag → continue
2. Split: args=`['--debug=2']`, remaining=`['add', 'test', '--shell', 'bug']`
3. Argparse sees only `['--debug=2']`
4. Enables debug, passes remaining to task
5. Task gets: `['add', 'test', '--shell', 'bug']`

**tw --shell add test**
1. First arg: `--shell` → valid tw flag → continue
2. Split: args=`['--shell']`, remaining=`['add', 'test']`
3. Argparse sees only `['--shell']`
4. Starts shell with remaining as initial command

---

## Installation & Testing

```bash
# Install
cp tw ~/.task/scripts/tw
chmod +x ~/.task/scripts/tw

# Verify version
tw --version | head -2
# Should show: tw v2.1.4

# Test the fix with debug
TW_DEBUG_WRAPPER=1 tw --debug=2 add test --shell bug

# Should show:
# [tw-debug] args_for_parser = ['--debug=2']
# [tw-debug] remaining_args = ['add', 'test', '--shell', 'bug']
# Created task XX.

# Verify task description
tw XX
# Description should be: "test --shell bug"
```

---

**tw v2.1.4** - argparse properly contained! 🎯
