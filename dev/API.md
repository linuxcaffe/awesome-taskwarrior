# awesome-taskwarrior API Reference

This document provides detailed reference for library functions available to installers and wrappers.

## Table of Contents

- [Bash Library (tw-common.sh)](#bash-library-tw-commonsh)
  - [Utility Functions](#utility-functions)
  - [Dependency Checking](#dependency-checking)
  - [Repository Management](#repository-management)
  - [Hook Management](#hook-management)
  - [Configuration Management](#configuration-management)
  - [Testing Utilities](#testing-utilities)
  - [Wrapper Management](#wrapper-management)
  - [File Operations](#file-operations)
- [Python Library (tw-wrapper.py)](#python-library-tw-wrapperpy)
  - [TaskWrapper Class](#taskwrapper-class)
  - [Utility Functions](#python-utility-functions)
  - [Example Wrappers](#example-wrappers)

---

## Bash Library (tw-common.sh)

Library for install scripts providing standardized installation, configuration, and testing functions.

**Include in your script:**
```bash
source "$(dirname "$0")/../lib/tw-common.sh"
```

**Available Environment Variables:**
- `$INSTALL_DIR` - Base installation directory (default: `~/.task`)
- `$HOOKS_DIR` - Hook installation directory (default: `~/.task/hooks`)
- `$TASKRC` - Path to .taskrc file (default: `~/.taskrc`)
- `$TW_DEBUG` - Debug flag (`0` or `1`)

### Utility Functions

#### tw_msg
Print colored message to terminal.

**Syntax:**
```bash
tw_msg COLOR MESSAGE
```

**Parameters:**
- `COLOR` - Color code (use built-in variables)
- `MESSAGE` - Message to print

**Example:**
```bash
tw_msg "$COLOR_GREEN" "Installation successful"
```

**Color Variables:**
- `$COLOR_RESET` - Reset to default
- `$COLOR_RED` - Red (errors)
- `$COLOR_GREEN` - Green (success)
- `$COLOR_YELLOW` - Yellow (warnings)
- `$COLOR_BLUE` - Blue (info/debug)

#### tw_error
Print error message to stderr.

**Syntax:**
```bash
tw_error MESSAGE
```

**Example:**
```bash
tw_error "Installation failed"
```

#### tw_warn
Print warning message to stderr.

**Syntax:**
```bash
tw_warn MESSAGE
```

**Example:**
```bash
tw_warn "Configuration already exists"
```

#### tw_info
Print informational message.

**Syntax:**
```bash
tw_info MESSAGE
```

**Example:**
```bash
tw_info "Downloading repository..."
```

#### tw_success
Print success message.

**Syntax:**
```bash
tw_success MESSAGE
```

**Example:**
```bash
tw_success "Installation complete"
```

#### tw_debug
Print debug message (only if `TW_DEBUG=1`).

**Syntax:**
```bash
tw_debug MESSAGE
```

**Example:**
```bash
tw_debug "Processing hook: on-add-test.py"
```

### Dependency Checking

#### tw_check_python_version
Check if Python version meets minimum requirement.

**Syntax:**
```bash
tw_check_python_version MAJOR.MINOR
```

**Parameters:**
- `MAJOR.MINOR` - Minimum required version (e.g., "3.6")

**Returns:**
- `0` - Version requirement met
- `1` - Version requirement not met or Python not found

**Example:**
```bash
tw_check_python_version 3.6 || {
    echo "Python 3.6+ required"
    return 1
}
```

#### tw_check_taskwarrior_version
Check if Taskwarrior version meets minimum requirement.

**Syntax:**
```bash
tw_check_taskwarrior_version MAJOR.MINOR.PATCH
```

**Parameters:**
- `MAJOR.MINOR.PATCH` - Minimum required version (e.g., "2.6.2")

**Returns:**
- `0` - Version requirement met
- `1` - Version requirement not met or Taskwarrior not found

**Example:**
```bash
tw_check_taskwarrior_version 2.6.2 || return 1
```

#### tw_check_command
Check if a command exists in PATH.

**Syntax:**
```bash
tw_check_command COMMAND [INSTALL_HINT]
```

**Parameters:**
- `COMMAND` - Command name to check
- `INSTALL_HINT` - Optional message explaining how to install

**Returns:**
- `0` - Command found
- `1` - Command not found

**Example:**
```bash
tw_check_command jq "Install with: sudo apt install jq" || return 1
```

### Repository Management

#### tw_clone_or_update
Clone a git repository or update if already exists.

**Syntax:**
```bash
tw_clone_or_update REPO_URL TARGET_DIR [BRANCH]
```

**Parameters:**
- `REPO_URL` - Git repository URL
- `TARGET_DIR` - Destination directory
- `BRANCH` - Optional branch name (default: repository default)

**Returns:**
- `0` - Clone/update successful
- `1` - Operation failed

**Example:**
```bash
tw_clone_or_update \
    "https://github.com/user/repo" \
    "$INSTALL_DIR/myapp" \
    "main" || return 1
```

**Notes:**
- Creates parent directories if needed
- Automatically detects existing repository and updates instead of cloning
- Preserves local working directory

### Hook Management

#### tw_symlink_hook
Create symlink for a hook in the hooks directory.

**Syntax:**
```bash
tw_symlink_hook SOURCE_PATH [LINK_NAME]
```

**Parameters:**
- `SOURCE_PATH` - Full path to hook script
- `LINK_NAME` - Optional link name (default: basename of source)

**Returns:**
- `0` - Symlink created
- `1` - Operation failed

**Example:**
```bash
# Simple symlink (uses basename)
tw_symlink_hook "${target_dir}/on-add-test.py" || return 1

# Custom link name
tw_symlink_hook "${target_dir}/src/hook.py" "on-add-custom.py" || return 1
```

**Notes:**
- Automatically makes source file executable
- Removes existing symlink/file if present
- Creates hooks directory if needed

#### tw_remove_hook
Remove hook symlink from hooks directory.

**Syntax:**
```bash
tw_remove_hook HOOK_NAME
```

**Parameters:**
- `HOOK_NAME` - Name of hook to remove

**Returns:**
- `0` - Hook removed or didn't exist
- `1` - Hook exists but couldn't be removed

**Example:**
```bash
tw_remove_hook "on-add-test.py"
```

**Notes:**
- Only removes symlinks, not regular files
- Warns if file exists but is not a symlink

### Configuration Management

#### tw_add_config
Add configuration line to taskrc.

**Syntax:**
```bash
tw_add_config "KEY=VALUE"
```

**Parameters:**
- `KEY=VALUE` - Configuration line in taskrc format

**Returns:**
- `0` - Configuration added
- `1` - Operation failed

**Example:**
```bash
tw_add_config "uda.myapp.type=string"
tw_add_config "uda.myapp.label=My App"
tw_add_config "urgency.uda.myapp.coefficient=5.0"
```

**Notes:**
- Skips if key already exists (idempotent)
- Creates taskrc if it doesn't exist
- Appends to end of file

#### tw_remove_config
Remove configuration lines from taskrc.

**Syntax:**
```bash
tw_remove_config "KEY_PREFIX"
```

**Parameters:**
- `KEY_PREFIX` - Prefix of configuration keys to remove

**Returns:**
- `0` - Configuration removed
- `1` - Operation failed

**Example:**
```bash
# Remove all UDA config
tw_remove_config "uda.myapp"

# Remove specific config
tw_remove_config "uda.myapp.type"
```

**Notes:**
- Removes all lines starting with prefix
- Creates backup before modification
- Restores backup on failure

#### tw_config_exists
Check if configuration key exists in taskrc.

**Syntax:**
```bash
tw_config_exists "KEY"
```

**Parameters:**
- `KEY` - Configuration key to check

**Returns:**
- `0` - Key exists
- `1` - Key doesn't exist or taskrc not found

**Example:**
```bash
if tw_config_exists "uda.myapp.type"; then
    echo "Already configured"
fi
```

### Testing Utilities

#### tw_test_hook
Test if hook exists and is executable.

**Syntax:**
```bash
tw_test_hook "HOOK_NAME"
```

**Parameters:**
- `HOOK_NAME` - Name of hook to test

**Returns:**
- `0` - Hook exists and is executable
- `1` - Hook missing or not executable

**Example:**
```bash
tw_test_hook "on-add-test.py" || return 1
```

#### tw_test_config
Test if configuration value matches expected value.

**Syntax:**
```bash
tw_test_config "KEY" "EXPECTED_VALUE"
```

**Parameters:**
- `KEY` - Configuration key
- `EXPECTED_VALUE` - Expected value

**Returns:**
- `0` - Value matches
- `1` - Value doesn't match or key not found

**Example:**
```bash
tw_test_config "uda.myapp.type" "string" || return 1
```

#### tw_test_cmd
Run a task command and check for success.

**Syntax:**
```bash
tw_test_cmd "COMMAND"
```

**Parameters:**
- `COMMAND` - Full command to execute

**Returns:**
- `0` - Command succeeded
- `1` - Command failed

**Example:**
```bash
tw_test_cmd "task add test task" || return 1
```

**Notes:**
- Suppresses output (both stdout and stderr)
- Use for testing functionality, not output

#### tw_test_cleanup
Clean up test data from Taskwarrior.

**Syntax:**
```bash
tw_test_cleanup
```

**Returns:**
- `0` - Always succeeds

**Example:**
```bash
# After running tests
tw_test_cleanup
```

**Notes:**
- Removes tasks with "test" or "TEST" in description
- Safe to call even if no test data exists

#### tw_test_setup
Setup test environment and verify it's safe to test.

**Syntax:**
```bash
tw_test_setup
```

**Returns:**
- `0` - Safe to proceed with testing
- `1` - User aborted or unsafe

**Example:**
```bash
test() {
    tw_test_setup || return 1
    
    # Run tests...
    
    tw_test_cleanup
}
```

**Notes:**
- Checks for `TW_TEST_ENV=1` environment variable
- Prompts user if testing with production data

### Wrapper Management

#### tw_add_to_wrapper_stack
Add application to wrapper stack in tw.config.

**Syntax:**
```bash
tw_add_to_wrapper_stack "APP_NAME"
```

**Parameters:**
- `APP_NAME` - Name of wrapper application

**Returns:**
- `0` - Added to stack (or already present)
- `1` - Operation failed

**Example:**
```bash
tw_add_to_wrapper_stack "nicedates"
```

**Notes:**
- Currently displays manual instructions
- Full implementation pending proper INI parsing

### File Operations

#### tw_backup_file
Create timestamped backup of a file.

**Syntax:**
```bash
tw_backup_file "FILE_PATH"
```

**Parameters:**
- `FILE_PATH` - File to backup

**Returns:**
- `0` - Backup created
- `1` - Backup failed

**Example:**
```bash
tw_backup_file "$TASKRC" || return 1
```

**Notes:**
- Backup filename: `<original>.bak.YYYYMMDD-HHMMSS`
- No-op if file doesn't exist

---

## Python Library (tw-wrapper.py)

Library for creating wrapper applications that integrate with tw.py's wrapper chain.

**Import in your wrapper:**
```python
from tw_wrapper import TaskWrapper, main
```

### TaskWrapper Class

Base class for wrapper applications.

#### Constructor

```python
def __init__(self)
```

**Attributes:**
- `self.debug` - Debug mode flag (from `TW_DEBUG` environment variable)
- `self.next_wrapper` - Next wrapper/task in chain (from `TW_NEXT_WRAPPER`)

**Example:**
```python
class MyWrapper(TaskWrapper):
    def __init__(self):
        super().__init__()
        # Your initialization
```

#### debug_print

```python
def debug_print(self, msg: str) -> None
```

Print debug message if debug mode is enabled.

**Parameters:**
- `msg` - Debug message

**Example:**
```python
self.debug_print("Processing arguments")
```

#### process_args

```python
def process_args(self, args: List[str]) -> List[str]
```

Process and modify arguments. **Override this method** in your wrapper.

**Parameters:**
- `args` - List of command-line arguments

**Returns:**
- Modified list of arguments

**Example:**
```python
def process_args(self, args):
    # Replace date shortcuts
    return [arg.replace('tom', 'tomorrow') for arg in args]
```

#### should_bypass

```python
def should_bypass(self, args: List[str]) -> bool
```

Check if wrapper should be bypassed for this command.

**Parameters:**
- `args` - Command-line arguments

**Returns:**
- `True` if wrapper should be bypassed

**Example:**
```python
def should_bypass(self, args):
    # Bypass for help/version
    if args and args[0] in ('--help', '--version'):
        return True
    return False
```

**Default behavior:**
- Bypasses for `--help`, `-h`, `--version`, `-V`

#### execute

```python
def execute(self, args: List[str]) -> int
```

Execute next wrapper/task in chain.

**Parameters:**
- `args` - Arguments to pass

**Returns:**
- Exit code from executed command

**Example:**
```python
# Usually called automatically, but can be used manually:
return self.execute(modified_args)
```

#### run

```python
def run(self, args: List[str]) -> int
```

Main entry point. Usually not overridden.

**Parameters:**
- `args` - Command-line arguments

**Returns:**
- Exit code

**Flow:**
1. Check if should bypass
2. Call `process_args()`
3. Execute next in chain
4. Return exit code

### Python Utility Functions

#### expand_date_shortcuts

```python
def expand_date_shortcuts(args: List[str], shortcuts: dict) -> List[str]
```

Expand date shortcuts in arguments.

**Parameters:**
- `args` - Argument list
- `shortcuts` - Dictionary mapping shortcuts to expansions

**Returns:**
- Arguments with shortcuts expanded

**Example:**
```python
shortcuts = {
    'tom': 'tomorrow',
    'eow': 'eow',
    'eom': 'eom'
}
args = expand_date_shortcuts(args, shortcuts)
```

#### inject_context

```python
def inject_context(args: List[str], context: str) -> List[str]
```

Inject context into arguments.

**Parameters:**
- `args` - Argument list
- `context` - Context name

**Returns:**
- Arguments with context injected

**Example:**
```python
args = inject_context(args, 'work')
# Result: ['rc.context=work', 'list']
```

#### add_default_tags

```python
def add_default_tags(args: List[str], tags: List[str]) -> List[str]
```

Add default tags to 'add' commands.

**Parameters:**
- `args` - Argument list
- `tags` - List of tag names (without `+`)

**Returns:**
- Arguments with tags added

**Example:**
```python
args = add_default_tags(args, ['urgent', 'work'])
# For 'add' command, adds +urgent +work
```

### Example Wrappers

#### DateParsingWrapper

Demonstrates date shortcut expansion.

```python
from tw_wrapper import TaskWrapper, expand_date_shortcuts, main

class DateParsingWrapper(TaskWrapper):
    def __init__(self):
        super().__init__()
        self.date_shortcuts = {
            'tom': 'tomorrow',
            'tod': 'today',
            'eow': 'eow',
        }
    
    def process_args(self, args):
        return expand_date_shortcuts(args, self.date_shortcuts)

if __name__ == '__main__':
    main(DateParsingWrapper)
```

#### ContextWrapper

Demonstrates automatic context setting.

```python
from tw_wrapper import TaskWrapper, inject_context, main

class ContextWrapper(TaskWrapper):
    def __init__(self):
        super().__init__()
        self.project_contexts = {
            'work': 'work',
            'home': 'personal',
        }
    
    def process_args(self, args):
        for arg in args:
            if arg.startswith('project:'):
                project = arg.split(':', 1)[1]
                if project in self.project_contexts:
                    return inject_context(args, self.project_contexts[project])
        return args

if __name__ == '__main__':
    main(ContextWrapper)
```

---

## Usage Patterns

### Installer Script Template

```bash
#!/bin/bash
source "$(dirname "$0")/../lib/tw-common.sh"

install() {
    tw_check_python_version 3.6 || return 1
    tw_clone_or_update "$REPO_URL" "$INSTALL_DIR/myapp" || return 1
    tw_symlink_hook "$INSTALL_DIR/myapp/on-add.py" || return 1
    tw_add_config "uda.myapp.type=string"
    tw_success "Installed myapp"
    return 0
}

uninstall() {
    tw_remove_hook "on-add.py"
    tw_remove_config "uda.myapp"
    rm -rf "$INSTALL_DIR/myapp"
    tw_success "Uninstalled myapp"
    return 0
}
```

### Wrapper Script Template

```python
#!/usr/bin/env python3
from tw_wrapper import TaskWrapper, main

class MyWrapper(TaskWrapper):
    def process_args(self, args):
        # Your processing logic
        return args

if __name__ == '__main__':
    main(MyWrapper)
```

---

## Error Handling Best Practices

1. **Always check return codes:**
   ```bash
   tw_check_python_version 3.6 || return 1
   ```

2. **Provide helpful error messages:**
   ```bash
   tw_check_command jq "Install with: sudo apt install jq" || return 1
   ```

3. **Clean up on failure:**
   ```bash
   install() {
       tw_clone_or_update "$REPO" "$DIR" || {
           tw_error "Clone failed"
           cleanup_partial_install
           return 1
       }
   }
   ```

4. **Use debug output:**
   ```bash
   tw_debug "Processing hook: $hook_name"
   ```

---

## Version Information

- `tw-common.sh` version: 1.0.0
- `tw-wrapper.py` version: 1.0.0

For issues or questions, see DEVELOPERS.md or open an issue on GitHub.
