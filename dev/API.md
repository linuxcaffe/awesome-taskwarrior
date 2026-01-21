# awesome-taskwarrior API Reference

**Version:** 1.3.0  
**Last Updated:** January 2026

This document provides detailed reference for library functions available to installers and wrappers in the awesome-taskwarrior ecosystem.

## Table of Contents

- [Bash Library (tw-common.sh)](#bash-library-tw-commonsh)
  - [Environment Variables](#environment-variables)
  - [Utility Functions](#utility-functions)
  - [Dependency Checking](#dependency-checking)
  - [Project Directory Management](#project-directory-management)
  - [Repository Management](#repository-management)
  - [Hook Management](#hook-management)
  - [Wrapper Management](#wrapper-management)
  - [Configuration Management](#configuration-management)
  - [Testing Utilities](#testing-utilities)
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

### Environment Variables

The following environment variables are available to all installer scripts. They are automatically set by tw.py and can be overridden if needed.

**Available Environment Variables:**
- `$INSTALL_DIR` - Base installation directory (default: `~/.task`)
- `$HOOKS_DIR` - Hook installation directory (default: `~/.task/hooks`)
- `$SCRIPTS_DIR` - Scripts/wrappers directory (default: `~/.task/scripts`)
- `$CONFIG_DIR` - Configuration files directory (default: `~/.task/config`)
- `$LOGS_DIR` - Logs directory (default: `~/.task/logs`)
- `$TASKRC` - Path to .taskrc file (default: `~/.taskrc`)
- `$TW_DEBUG` - Debug flag (`0` or `1`)

**Directory Structure:**
```
~/.task/
├── hooks/          # Hook projects and symlinks
├── scripts/        # Wrapper projects and symlinks
├── config/         # Configuration files
└── logs/           # Debug and test logs
```

**Usage in installers:**
```bash
# These are automatically set when run via tw.py
echo "Installing to: ${INSTALL_DIR}"
echo "Hooks go in: ${HOOKS_DIR}"
echo "Scripts go in: ${SCRIPTS_DIR}"

# You can also set defaults for standalone testing
: ${INSTALL_DIR:=~/.task}
: ${HOOKS_DIR:=~/.task/hooks}
: ${SCRIPTS_DIR:=~/.task/scripts}
: ${CONFIG_DIR:=~/.task/config}
: ${LOGS_DIR:=~/.task/logs}
```

---

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

---

#### tw_error
Print error message to stderr.

**Syntax:**
```bash
tw_error MESSAGE
```

**Parameters:**
- `MESSAGE` - Error message to display

**Returns:**
- Prints to stderr, does not exit

**Example:**
```bash
if [ ! -f "$config_file" ]; then
    tw_error "Configuration file not found: $config_file"
    return 1
fi
```

---

#### tw_warn
Print warning message to stderr.

**Syntax:**
```bash
tw_warn MESSAGE
```

**Parameters:**
- `MESSAGE` - Warning message to display

**Returns:**
- Prints to stderr, does not exit

**Example:**
```bash
if [ -f "$existing_hook" ]; then
    tw_warn "Hook already exists, will be replaced"
fi
```

---

#### tw_info
Print informational message.

**Syntax:**
```bash
tw_info MESSAGE
```

**Parameters:**
- `MESSAGE` - Info message to display

**Example:**
```bash
tw_info "Downloading repository..."
tw_info "Configuration updated successfully"
```

---

#### tw_success
Print success message.

**Syntax:**
```bash
tw_success MESSAGE
```

**Parameters:**
- `MESSAGE` - Success message to display

**Example:**
```bash
tw_success "✓ Installation complete"
tw_success "All tests passed"
```

---

#### tw_debug
Print debug message (only if TW_DEBUG=1).

**Syntax:**
```bash
tw_debug MESSAGE
```

**Parameters:**
- `MESSAGE` - Debug message to display

**Returns:**
- Only prints if `TW_DEBUG=1`

**Example:**
```bash
tw_debug "Processing file: $filename"
tw_debug "Current state: $state"
```

**Usage:**
```bash
# Enable debug output
TW_DEBUG=1 bash installers/yourapp.install install

# Or via tw.py
tw --debug --install yourapp
```

---

### Dependency Checking

#### tw_check_python_version
Check if Python version meets requirements.

**Syntax:**
```bash
tw_check_python_version MAJOR.MINOR
```

**Parameters:**
- `MAJOR.MINOR` - Minimum required Python version (e.g., `3.6`)

**Returns:**
- 0 if version meets requirement
- 1 if version too old or Python not found

**Example:**
```bash
# Require Python 3.6 or higher
tw_check_python_version 3.6 || return 1

# Require Python 3.8 or higher
tw_check_python_version 3.8 || return 1
```

**Error Messages:**
- If python3 not found: Suggests installation command
- If version too old: Shows required vs actual version

---

#### tw_check_taskwarrior_version
Check if Taskwarrior version meets requirements.

**Syntax:**
```bash
tw_check_taskwarrior_version MAJOR.MINOR.PATCH
```

**Parameters:**
- `MAJOR.MINOR.PATCH` - Minimum required version (e.g., `2.6.2`)

**Returns:**
- 0 if version meets requirement
- 1 if version too old or Taskwarrior not found

**Example:**
```bash
# Require Taskwarrior 2.6.2 or higher (always recommended)
tw_check_taskwarrior_version 2.6.2 || return 1

# Require specific version
tw_check_taskwarrior_version 2.6.0 || return 1
```

**Note:**
- awesome-taskwarrior targets Taskwarrior 2.6.2 and the 2.x branch
- Not compatible with Taskwarrior 3.x

---

#### tw_check_command
Check if a command/tool is available in PATH.

**Syntax:**
```bash
tw_check_command COMMAND
```

**Parameters:**
- `COMMAND` - Command name to check (e.g., `jq`, `git`)

**Returns:**
- 0 if command exists
- 1 if command not found

**Example:**
```bash
# Check for jq (JSON processor)
tw_check_command "jq" || {
    tw_error "jq is required but not installed"
    return 1
}

# Check for git
tw_check_command "git" || return 1
```

---

### Project Directory Management

These functions help manage installation to the correct directory based on app type.

#### tw_get_install_dir
Get the correct installation directory based on app type.

**Syntax:**
```bash
tw_get_install_dir TYPE SHORT_NAME
```

**Parameters:**
- `TYPE` - App type: `hook`, `wrapper`, `utility`, or `config`
- `SHORT_NAME` - Short name for the app (e.g., `recurrence`)

**Returns:**
- Echoes the full path to installation directory
- Returns 1 on invalid type

**Example:**
```bash
install_dir=$(tw_get_install_dir hook recurrence)
# Returns: ~/.task/hooks/recurrence

install_dir=$(tw_get_install_dir wrapper nicedates)
# Returns: ~/.task/scripts/nicedates

install_dir=$(tw_get_install_dir config custom)
# Returns: ~/.task/config/custom
```

**Directory Mapping:**
- `hook` → `$HOOKS_DIR/SHORT_NAME`
- `wrapper` → `$SCRIPTS_DIR/SHORT_NAME`
- `utility` → `$SCRIPTS_DIR/SHORT_NAME`
- `config` → `$CONFIG_DIR/SHORT_NAME`

**Usage Pattern:**
```bash
local type="hook"
local short_name="recurrence"
local project_dir=$(tw_get_install_dir "$type" "$short_name")

if [ -d "$project_dir" ]; then
    tw_info "Project already exists at: $project_dir"
fi
```

---

#### tw_clone_to_project
Clone repository to the appropriate location based on app type.

**Syntax:**
```bash
tw_clone_to_project TYPE SHORT_NAME REPO_URL [BRANCH]
```

**Parameters:**
- `TYPE` - App type: `hook`, `wrapper`, `utility`, or `config`
- `SHORT_NAME` - Short name for the app
- `REPO_URL` - Git repository URL
- `BRANCH` - (Optional) Git branch to checkout

**Returns:**
- 0 on success
- 1 on failure (e.g., git error, network issue)

**Example:**
```bash
# Clone a hook project
tw_clone_to_project hook recurrence "https://github.com/linuxcaffe/tw-recurrence_overhaul-hook"
# Clones to: ~/.task/hooks/recurrence/

# Clone a wrapper project on specific branch
tw_clone_to_project wrapper nicedates "https://github.com/user/nicedates" main
# Clones to: ~/.task/scripts/nicedates/ (main branch)

# Clone a utility
tw_clone_to_project utility cmx "https://github.com/user/cmx"
# Clones to: ~/.task/scripts/cmx/
```

**Behavior:**
- Creates parent directory if needed
- If directory exists, runs `git pull` to update
- Checks out specified branch if provided
- Uses `tw_clone_or_update` internally

**Complete Install Example:**
```bash
install() {
    local short_name="recurrence"
    local repo_url="https://github.com/user/tw-recurrence_overhaul-hook"
    
    # Clone to correct location
    tw_clone_to_project hook "$short_name" "$repo_url" || return 1
    
    # Get the project directory
    local project_dir="${HOOKS_DIR}/${short_name}"
    
    # Install hooks from project
    tw_symlink_hook "$project_dir" "on-add_recurrence.py" || return 1
}
```

---

### Repository Management

#### tw_clone_or_update
Clone git repository or update if it exists.

**Syntax:**
```bash
tw_clone_or_update REPO_URL TARGET_DIR [BRANCH]
```

**Parameters:**
- `REPO_URL` - Git repository URL
- `TARGET_DIR` - Target directory for clone
- `BRANCH` - (Optional) Branch to checkout

**Returns:**
- 0 on success
- 1 on failure

**Example:**
```bash
# Clone to specific directory
tw_clone_or_update "https://github.com/user/repo" "${HOOKS_DIR}/myapp"

# Clone specific branch
tw_clone_or_update "https://github.com/user/repo" "${HOOKS_DIR}/myapp" develop
```

**Behavior:**
- If target doesn't exist: Clones repository
- If target exists with .git: Runs `git pull`
- If target exists without .git: Returns error
- Creates parent directories as needed

**Note:**
- Use `tw_clone_to_project` instead for new installers (handles type-based directories)
- This is a lower-level function kept for compatibility

---

### Hook Management

Hook management functions for creating and removing hook symlinks. Updated in v1.3.0 to support project subdirectories.

#### tw_symlink_hook
Create symlink for a hook in the hooks directory root.

**Syntax (v1.3.0):**
```bash
tw_symlink_hook PROJECT_DIR HOOK_FILE
```

**Parameters:**
- `PROJECT_DIR` - Full path to project directory (e.g., `${HOOKS_DIR}/recurrence`)
- `HOOK_FILE` - Hook filename (e.g., `on-add_recurrence.py`)

**Returns:**
- 0 on success
- 1 on failure (file not found, permission error, etc.)

**Example:**
```bash
# Install recurrence hooks
local project_dir="${HOOKS_DIR}/recurrence"
tw_symlink_hook "$project_dir" "on-add_recurrence.py"
tw_symlink_hook "$project_dir" "on-modify_recurrence.py"
tw_symlink_hook "$project_dir" "on-exit_recurrence.py"

# Creates:
# ~/.task/hooks/on-add_recurrence.py -> ~/.task/hooks/recurrence/on-add_recurrence.py
# ~/.task/hooks/on-modify_recurrence.py -> ~/.task/hooks/recurrence/on-modify_recurrence.py
# ~/.task/hooks/on-exit_recurrence.py -> ~/.task/hooks/recurrence/on-exit_recurrence.py
```

**Behavior:**
- Verifies source file exists in project directory
- Makes source executable (`chmod +x`)
- Removes existing symlink/file if present
- Creates symlink in `$HOOKS_DIR` root pointing to file in project subdirectory

**Complete Example:**
```bash
install() {
    # Clone project
    tw_clone_to_project hook recurrence "$REPO_URL" || return 1
    
    local project_dir="${HOOKS_DIR}/recurrence"
    
    # Install all hooks
    for hook in on-add on-modify on-exit; do
        tw_symlink_hook "$project_dir" "${hook}_recurrence.py" || return 1
    done
}
```

**Migration from v1.0.0:**
```bash
# OLD (v1.0.0):
tw_symlink_hook "${HOOKS_DIR}/${APPNAME}/on-add-test.py"

# NEW (v1.3.0):
local project_dir="${HOOKS_DIR}/${SHORT_NAME}"
tw_symlink_hook "$project_dir" "on-add-test.py"
```

---

#### tw_remove_hook
Remove hook symlink from hooks directory.

**Syntax:**
```bash
tw_remove_hook HOOK_FILE
```

**Parameters:**
- `HOOK_FILE` - Hook filename to remove (e.g., `on-add_recurrence.py`)

**Returns:**
- 0 on success
- 1 on failure or if not a symlink (safety check)

**Example:**
```bash
# Remove single hook
tw_remove_hook "on-add_recurrence.py"
# Removes: ~/.task/hooks/on-add_recurrence.py

# Remove multiple hooks
tw_remove_hook "on-add_recurrence.py"
tw_remove_hook "on-modify_recurrence.py"
tw_remove_hook "on-exit_recurrence.py"
```

**Behavior:**
- Only removes symlinks (safety check)
- Warns if file exists but isn't a symlink
- Returns success if symlink doesn't exist

**Complete Uninstall Example:**
```bash
uninstall() {
    # Remove all hooks
    tw_remove_hook "on-add_recurrence.py"
    tw_remove_hook "on-modify_recurrence.py"
    tw_remove_hook "on-exit_recurrence.py"
    
    # Remove configuration
    tw_remove_config "uda.recur_type"
    
    # Remove project directory
    rm -rf "${HOOKS_DIR}/recurrence"
}
```

---

### Wrapper Management

Functions for managing wrapper scripts and utilities in the scripts directory.

#### tw_symlink_wrapper
Create symlink for a wrapper/utility script.

**Syntax:**
```bash
tw_symlink_wrapper PROJECT_DIR SCRIPT_FILE [LINK_NAME]
```

**Parameters:**
- `PROJECT_DIR` - Full path to project directory (e.g., `${SCRIPTS_DIR}/nicedates`)
- `SCRIPT_FILE` - Script filename in project (e.g., `nicedates.py`)
- `LINK_NAME` - (Optional) Name for symlink (default: basename of SCRIPT_FILE)

**Returns:**
- 0 on success
- 1 on failure

**Example:**
```bash
# Install nicedates wrapper
local project_dir="${SCRIPTS_DIR}/nicedates"
tw_symlink_wrapper "$project_dir" "nicedates.py" "nicedates"

# Creates:
# ~/.task/scripts/nicedates -> ~/.task/scripts/nicedates/nicedates.py

# Install with automatic link name (removes .py extension)
tw_symlink_wrapper "$project_dir" "nicedates.py"
# Creates: ~/.task/scripts/nicedates.py -> ~/.task/scripts/nicedates/nicedates.py
```

**Behavior:**
- Verifies source file exists
- Makes source executable (`chmod +x`)
- Removes existing symlink/file if present
- Creates symlink in `$SCRIPTS_DIR` root

**Complete Example:**
```bash
install() {
    local short_name="nicedates"
    
    # Clone wrapper project
    tw_clone_to_project wrapper "$short_name" "$REPO_URL" || return 1
    
    local project_dir="${SCRIPTS_DIR}/${short_name}"
    
    # Create wrapper symlink
    tw_symlink_wrapper "$project_dir" "nicedates.py" "nicedates" || return 1
    
    # Inform user about PATH
    if [[ ":$PATH:" != *":${SCRIPTS_DIR}:"* ]]; then
        tw_info "Add to your ~/.bashrc:"
        tw_info "  export PATH=\"\$HOME/.task/scripts:\$PATH\""
    fi
}
```

---

#### tw_remove_wrapper
Remove wrapper symlink from scripts directory.

**Syntax:**
```bash
tw_remove_wrapper LINK_NAME
```

**Parameters:**
- `LINK_NAME` - Wrapper name to remove (e.g., `nicedates`)

**Returns:**
- 0 on success
- 1 on failure or if not a symlink

**Example:**
```bash
# Remove wrapper symlink
tw_remove_wrapper "nicedates"
# Removes: ~/.task/scripts/nicedates

# Multiple wrappers
tw_remove_wrapper "nicedates"
tw_remove_wrapper "cmx"
```

**Behavior:**
- Only removes symlinks (safety check)
- Warns if file exists but isn't a symlink
- Returns success if symlink doesn't exist

**Complete Uninstall Example:**
```bash
uninstall() {
    # Remove wrapper symlink
    tw_remove_wrapper "nicedates"
    
    # Remove configuration
    tw_remove_config "wrapper.nicedates"
    
    # Remove project directory
    rm -rf "${SCRIPTS_DIR}/nicedates"
}
```

---

### Configuration Management

#### tw_add_config
Add configuration line to .taskrc.

**Syntax:**
```bash
tw_add_config CONFIG_LINE
```

**Parameters:**
- `CONFIG_LINE` - Configuration line to add (key=value format)

**Returns:**
- 0 on success
- 1 on failure

**Example:**
```bash
# Add UDA definition
tw_add_config "uda.recur_type.type=string"
tw_add_config "uda.recur_type.label=Recurrence Type"
tw_add_config "uda.recur_type.values=chained,periodic"

# Add custom report
tw_add_config "report.recurring.description=Recurring tasks"
tw_add_config "report.recurring.columns=id,description,recur"
tw_add_config "report.recurring.filter=+TEMPLATE"

# Add color scheme
tw_add_config "color.active=bold white on red"
```

**Behavior:**
- Checks if configuration already exists (idempotent)
- Appends to user's .taskrc if not present
- Creates .taskrc if it doesn't exist
- Preserves existing configuration

---

#### tw_config_exists
Check if configuration exists in .taskrc.

**Syntax:**
```bash
tw_config_exists CONFIG_KEY
```

**Parameters:**
- `CONFIG_KEY` - Configuration key to check

**Returns:**
- 0 if configuration exists
- 1 if not found

**Example:**
```bash
if tw_config_exists "uda.recur_type.type"; then
    tw_info "Configuration already exists"
else
    tw_add_config "uda.recur_type.type=string"
fi
```

---

#### tw_remove_config
Remove configuration from .taskrc.

**Syntax:**
```bash
tw_remove_config CONFIG_PREFIX
```

**Parameters:**
- `CONFIG_PREFIX` - Configuration prefix to remove (e.g., `uda.recur_type`)

**Returns:**
- 0 on success

**Example:**
```bash
# Remove all uda.recur_type.* lines
tw_remove_config "uda.recur_type"

# Remove custom report
tw_remove_config "report.recurring"

# Remove color configuration
tw_remove_config "color.active"
```

**Behavior:**
- Removes all lines matching the prefix
- Safe to call even if configuration doesn't exist
- Uses sed for atomic operation

**Complete Example:**
```bash
uninstall() {
    # Remove all related configuration
    tw_remove_config "uda.recur_type"
    tw_remove_config "uda.recur_template"
    tw_remove_config "uda.recur_instance"
    tw_remove_config "report.recurring"
}
```

---

### Testing Utilities

#### tw_test_hook
Test if hook is installed and executable.

**Syntax:**
```bash
tw_test_hook HOOK_FILE
```

**Parameters:**
- `HOOK_FILE` - Hook filename to test

**Returns:**
- 0 if hook exists and is executable
- 1 if hook missing or not executable

**Example:**
```bash
test() {
    tw_test_hook "on-add_recurrence.py" || return 1
    tw_test_hook "on-modify_recurrence.py" || return 1
    tw_test_hook "on-exit_recurrence.py" || return 1
    echo "All hooks installed correctly"
}
```

---

#### tw_test_config
Test if configuration has expected value.

**Syntax:**
```bash
tw_test_config CONFIG_KEY EXPECTED_VALUE
```

**Parameters:**
- `CONFIG_KEY` - Configuration key to test
- `EXPECTED_VALUE` - Expected value

**Returns:**
- 0 if value matches
- 1 if value doesn't match or key not found

**Example:**
```bash
test() {
    tw_test_config "uda.recur_type.type" "string" || return 1
    tw_test_config "uda.recur_type.values" "chained,periodic" || return 1
    echo "Configuration correct"
}
```

---

#### tw_test_cmd
Test if task command executes successfully.

**Syntax:**
```bash
tw_test_cmd ARGS...
```

**Parameters:**
- `ARGS...` - Arguments to pass to task command

**Returns:**
- 0 if command succeeds
- 1 if command fails

**Example:**
```bash
test() {
    # Test that task can list
    tw_test_cmd list || return 1
    
    # Test custom report
    tw_test_cmd recurring || return 1
}
```

---

### File Operations

#### tw_backup_file
Create timestamped backup of a file.

**Syntax:**
```bash
tw_backup_file FILE
```

**Parameters:**
- `FILE` - File to backup

**Returns:**
- 0 on success
- 1 on failure

**Example:**
```bash
# Backup .taskrc before modifying
tw_backup_file "$TASKRC"
# Creates: ~/.taskrc.backup.20260121-143022

# Backup hook before replacing
tw_backup_file "${HOOKS_DIR}/on-add-test.py"
```

**Behavior:**
- Creates backup with timestamp: `FILE.backup.YYYYMMDD-HHMMSS`
- Only backs up if file exists
- Preserves original file permissions

---

## Python Library (tw-wrapper.py)

Library for building wrapper applications in Python.

**Include in your script:**
```python
from tw_wrapper import TaskWrapper, main
```

### TaskWrapper Class

Base class for creating Taskwarrior wrappers.

**Basic Structure:**
```python
from tw_wrapper import TaskWrapper, main

class MyWrapper(TaskWrapper):
    def process_args(self, args):
        # Modify arguments before passing to task
        return modified_args

if __name__ == '__main__':
    main(MyWrapper)
```

**Methods:**

#### process_args(args)
Override to modify arguments before passing to task.

**Parameters:**
- `args` - List of command-line arguments

**Returns:**
- Modified list of arguments

**Example:**
```python
def process_args(self, args):
    # Convert natural language dates
    modified = []
    for arg in args:
        if arg.startswith('due:'):
            date_str = arg[4:]
            parsed = parse_natural_date(date_str)
            modified.append(f'due:{parsed}')
        else:
            modified.append(arg)
    return modified
```

---

#### should_bypass()
Override to determine if wrapper should bypass processing.

**Returns:**
- True to bypass (pass directly to task)
- False to process normally

**Example:**
```python
def should_bypass(self):
    # Bypass for version and help
    if '--version' in self.args or '--help' in self.args:
        return True
    return False
```

---

#### execute(args)
Execute task command with modified arguments.

**Parameters:**
- `args` - Arguments to pass to task

**Returns:**
- Exit code from task

**Example:**
```python
# Usually called automatically, but can override
def execute(self, args):
    # Add custom logging
    log_command(args)
    return super().execute(args)
```

---

### Python Utility Functions

#### expand_date_shortcuts(text)
Expand date shortcuts like "tomorrow", "nextweek".

**Example:**
```python
from tw_wrapper import expand_date_shortcuts

date = expand_date_shortcuts("tomorrow")
# Returns: "2026-01-22" (if today is 2026-01-21)
```

---

#### inject_context(args, context)
Inject context into filter arguments.

**Example:**
```python
from tw_wrapper import inject_context

args = inject_context(['list'], '@work')
# Returns: ['list', '+work']
```

---

### Example Wrappers

#### Date Parsing Wrapper
```python
from tw_wrapper import TaskWrapper, main
from dateutil.parser import parse

class DateParsingWrapper(TaskWrapper):
    def process_args(self, args):
        modified = []
        for arg in args:
            if ':' in arg:
                key, value = arg.split(':', 1)
                if key in ['due', 'scheduled', 'wait', 'until']:
                    try:
                        parsed = parse(value)
                        modified.append(f'{key}:{parsed.strftime("%Y-%m-%d")}')
                        continue
                    except:
                        pass
            modified.append(arg)
        return modified

if __name__ == '__main__':
    main(DateParsingWrapper)
```

---

#### Context Wrapper
```python
from tw_wrapper import TaskWrapper, main
import os

class ContextWrapper(TaskWrapper):
    def process_args(self, args):
        context = os.environ.get('TASK_CONTEXT')
        if context and args:
            # Inject context as filter
            args.insert(0, f'+{context}')
        return args

if __name__ == '__main__':
    main(ContextWrapper)
```

---

## Best Practices

### For Bash Installers

1. **Always check dependencies first**
   ```bash
   install() {
       tw_check_python_version 3.6 || return 1
       tw_check_taskwarrior_version 2.6.2 || return 1
       # ... rest of install
   }
   ```

2. **Use SHORT_NAME consistently**
   ```bash
   APPNAME="tw-recurrence"
   SHORT_NAME="recurrence"
   
   tw_clone_to_project hook "$SHORT_NAME" "$REPO_URL"
   local project_dir="${HOOKS_DIR}/${SHORT_NAME}"
   ```

3. **Clean up completely in uninstall()**
   ```bash
   uninstall() {
       tw_remove_hook "on-add-*.py"
       tw_remove_config "uda.myapp"
       rm -rf "${HOOKS_DIR}/${SHORT_NAME}"
   }
   ```

4. **Provide helpful success messages**
   ```bash
   echo "✓ Installed ${APPNAME}"
   echo "  Hooks: ${HOOKS_DIR}/"
   echo "  Files: ${project_dir}"
   echo "  Logs: ${LOGS_DIR}/${SHORT_NAME}/"
   ```

### For Python Wrappers

1. **Support TW_NEXT_WRAPPER for chaining**
   ```python
   next_wrapper = os.environ.get('TW_NEXT_WRAPPER')
   if next_wrapper:
       os.execv(next_wrapper, [next_wrapper] + args)
   ```

2. **Keep wrappers fast**
   - Users notice slow wrappers
   - Cache when possible
   - Avoid expensive operations

3. **Handle errors gracefully**
   ```python
   try:
       result = parse_date(value)
   except ValueError:
       # Pass through unparsed
       result = value
   ```

---

## Version History

**v1.3.0** (January 2026)
- Added `SCRIPTS_DIR`, `CONFIG_DIR`, `LOGS_DIR` environment variables
- Added `tw_get_install_dir()` and `tw_clone_to_project()` functions
- Updated `tw_symlink_hook()` to take two parameters
- Added `tw_symlink_wrapper()` and `tw_remove_wrapper()` functions
- Updated all examples to use new directory structure

**v1.0.0** (December 2024)
- Initial release
- Core hook management functions
- Configuration management
- Testing utilities

---

## See Also

- [DEVELOPERS.md](../DEVELOPERS.md) - Architecture and design patterns
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [dev/models/](../dev/models/) - Template files and examples
- [README.md](../README.md) - User documentation
