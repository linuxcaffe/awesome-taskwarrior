# awesome-taskwarrior API Documentation v2.0.0

## Overview

This document describes the utility functions provided by `tw-common.sh` for creating self-contained installers. These functions are **optional** - installers must work without them, but they provide better user experience and reduce code duplication.

## Architecture Principles

### Installer Independence

The core principle of v2.0.0 is **installer independence**:

```bash
# Each installer MUST work standalone
bash installers/myapp.install install

# tw.py adds convenience, NOT dependency
tw.py install myapp
```

### Optional tw-common.sh Usage

Installers should gracefully handle the presence or absence of `tw-common.sh`:

```bash
#!/usr/bin/env bash

# Optional: Source helpers if available
if [[ -f ~/.task/lib/tw-common.sh ]]; then
    source ~/.task/lib/tw-common.sh
else
    # Fallback: Define minimal functions inline
    tw_msg() { echo "$@"; }
    tw_error() { echo "ERROR: $@" >&2; }
fi

# Rest of installer uses these functions...
```

## Environment Variables

Installers should detect and use these environment variables, or provide sensible defaults:

| Variable | Default | Purpose |
|----------|---------|---------|
| `HOOKS_DIR` | `~/.task/hooks` | Taskwarrior hook scripts |
| `SCRIPTS_DIR` | `~/.task/scripts` | Executable wrapper scripts |
| `CONFIG_DIR` | `~/.task/config` | Configuration files |
| `DOCS_DIR` | `~/.task/docs` | Documentation files |
| `LOGS_DIR` | `~/.task/logs` | Log files |
| `TASKRC` | `~/.taskrc` | Taskwarrior configuration file |

### Environment Detection Pattern

```bash
# Detect environment or use defaults
: ${HOOKS_DIR:=~/.task/hooks}
: ${SCRIPTS_DIR:=~/.task/scripts}
: ${CONFIG_DIR:=~/.task/config}
: ${DOCS_DIR:=~/.task/docs}
: ${LOGS_DIR:=~/.task/logs}
: ${TASKRC:=~/.taskrc}
```

## Messaging Functions

Functions for consistent, colorful output to users.

### tw_msg

Print an informational message.

```bash
tw_msg "Installing hooks..."
# Output: [INFO] Installing hooks...
```

### tw_success

Print a success message.

```bash
tw_success "Installation complete"
# Output: [SUCCESS] Installation complete
```

### tw_warn

Print a warning message to stderr.

```bash
tw_warn "Configuration file already exists"
# Output: [WARNING] Configuration file already exists
```

### tw_error

Print an error message to stderr.

```bash
tw_error "Failed to download file"
# Output: [ERROR] Failed to download file
```

### tw_die

Print an error message and exit with status 1.

```bash
tw_die "Critical error: Taskwarrior not found"
# Output: [ERROR] Critical error: Taskwarrior not found
# Exits with status 1
```

### tw_debug

Print a debug message (only if `TW_DEBUG` is set).

```bash
TW_DEBUG=1 bash myapp.install install
# Debug messages will be shown

tw_debug "Checking file permissions..."
# Output: [DEBUG] Checking file permissions...
```

## Version Checking Functions

Functions to verify system requirements before installation.

### tw_command_exists

Check if a command is available in PATH.

```bash
if tw_command_exists curl; then
    tw_msg "curl is available"
else
    tw_die "curl is required but not found"
fi
```

**Returns:** 0 if command exists, 1 otherwise

### tw_check_taskwarrior_version

Verify Taskwarrior meets minimum version requirement.

```bash
tw_check_taskwarrior_version "2.6.0" || exit 1
```

**Parameters:**
- `$1` - Minimum required version (e.g., "2.6.0")

**Returns:** 0 if version is sufficient, 1 otherwise

**Example:**

```bash
check_requirements() {
    tw_msg "Checking requirements..."
    tw_check_taskwarrior_version "2.6.0" || return 1
    tw_success "Requirements met"
    return 0
}
```

### tw_check_python_version

Verify Python 3 meets minimum version requirement.

```bash
tw_check_python_version "3.6" || exit 1
```

**Parameters:**
- `$1` - Minimum required version (e.g., "3.6")

**Returns:** 0 if version is sufficient, 1 otherwise

### tw_check_bash_version

Verify Bash meets minimum version requirement.

```bash
tw_check_bash_version "4.0" || exit 1
```

**Parameters:**
- `$1` - Minimum required version (e.g., "4.0")

**Returns:** 0 if version is sufficient, 1 otherwise

## File Operations

Functions for downloading and managing files.

### tw_curl_and_place

Download a file from URL and place it in target directory.

```bash
tw_curl_and_place \
    "https://raw.githubusercontent.com/user/repo/main/hook.py" \
    "$HOOKS_DIR"
```

**Parameters:**
- `$1` - URL to download from
- `$2` - Target directory
- `$3` - Optional: Filename (defaults to basename of URL)

**Returns:** 0 on success, 1 on failure

**Features:**
- Creates target directory if needed
- Downloads to temp file first (atomic operation)
- Verifies download succeeded before moving to final location
- Shows success/error messages

**Example:**

```bash
install_hooks() {
    local base_url="https://raw.githubusercontent.com/user/repo/main"
    
    tw_curl_and_place "$base_url/on-add.py" "$HOOKS_DIR" "on-add_myapp.py" || return 1
    tw_curl_and_place "$base_url/on-modify.py" "$HOOKS_DIR" "on-modify_myapp.py" || return 1
    
    return 0
}
```

### tw_ensure_executable

Make a file executable (chmod +x).

```bash
tw_ensure_executable "$HOOKS_DIR/on-add_myapp.py"
```

**Parameters:**
- `$1` - Path to file

**Returns:** 0 on success, 1 on failure

**Example:**

```bash
# After downloading hooks
for hook in "$HOOKS_DIR"/on-*_myapp.py; do
    tw_ensure_executable "$hook" || return 1
done
```

### tw_backup_file

Create a timestamped backup of a file.

```bash
tw_backup_file "$CONFIG_DIR/myapp.rc"
# Creates: myapp.rc.backup.20260122_143022
```

**Parameters:**
- `$1` - Path to file

**Returns:** 0 on success, 1 on failure

**Features:**
- Only backs up if file exists
- Timestamped backups prevent overwrites
- Shows success message with backup location

### tw_remove_file

Safely remove a file.

```bash
tw_remove_file "$HOOKS_DIR/on-add_myapp.py"
```

**Parameters:**
- `$1` - Path to file

**Returns:** 0 on success, 1 on failure

**Features:**
- Handles non-existent files gracefully
- Shows success message when removed

## Configuration Management

Functions for managing .taskrc configuration.

### tw_add_config

Add a configuration line to .taskrc if it doesn't already exist.

```bash
tw_add_config "include $CONFIG_DIR/myapp.rc"
```

**Parameters:**
- `$1` - Configuration line to add

**Returns:** 0 on success, 1 on failure

**Features:**
- Checks for exact match before adding (no duplicates)
- Uses `$TASKRC` environment variable if set
- Shows success message when added

**Example:**

```bash
configure_taskwarrior() {
    tw_msg "Configuring Taskwarrior..."
    
    tw_add_config "include $CONFIG_DIR/myapp.rc" || return 1
    tw_add_config "uda.myapp.type=string" || return 1
    
    tw_success "Configuration complete"
    return 0
}
```

### tw_remove_config

Remove a configuration line from .taskrc.

```bash
tw_remove_config "include $CONFIG_DIR/myapp.rc"
```

**Parameters:**
- `$1` - Configuration line to remove

**Returns:** 0 on success, 1 on failure

**Features:**
- Handles missing .taskrc gracefully
- Only removes exact matches
- Uses temp file for safe removal
- Shows success message when removed

### tw_config_exists

Check if a configuration line exists in .taskrc.

```bash
if tw_config_exists "include $CONFIG_DIR/myapp.rc"; then
    tw_msg "Configuration already present"
fi
```

**Parameters:**
- `$1` - Configuration line to check

**Returns:** 0 if exists, 1 otherwise

## Testing Helpers

Functions for creating isolated test environments.

### tw_is_test_mode

Check if running in test mode.

```bash
if tw_is_test_mode; then
    tw_msg "Running in test mode"
fi
```

**Returns:** 0 if `TW_TEST_MODE` is set, 1 otherwise

### tw_get_test_dir

Get the test environment directory path.

```bash
test_dir=$(tw_get_test_dir)
echo "Test directory: $test_dir"
```

**Returns:** Path to test directory (from `TW_TEST_DIR` or `/tmp/tw-test-$$`)

### tw_init_test_env

Initialize isolated test environment with directory structure.

```bash
TW_TEST_DIR=/tmp/my-test tw_init_test_env
```

**Returns:** 0 on success, 1 on failure

**Creates:**
- `$TW_TEST_DIR/hooks/`
- `$TW_TEST_DIR/scripts/`
- `$TW_TEST_DIR/config/`
- `$TW_TEST_DIR/docs/`
- `$TW_TEST_DIR/lib/`

### tw_cleanup_test_env

Remove test environment directory.

```bash
tw_cleanup_test_env
```

**Returns:** 0 on success, 1 on failure

## Complete Installer Example

Here's a complete self-contained installer using tw-common.sh utilities:

```bash
#!/usr/bin/env bash
#
# myapp.install - Installer for myapp
# Can be run standalone or via tw.py

set -euo pipefail

# Application metadata
APP_NAME="myapp"
APP_VERSION="1.0.0"
BASE_URL="https://raw.githubusercontent.com/user/myapp/main"

# Optional: Source helpers if available
if [[ -f ~/.task/lib/tw-common.sh ]]; then
    source ~/.task/lib/tw-common.sh
else
    # Fallback: Define minimal functions
    tw_msg() { echo "[INFO] $*"; }
    tw_success() { echo "[SUCCESS] $*"; }
    tw_error() { echo "[ERROR] $*" >&2; }
    tw_die() { tw_error "$@"; exit 1; }
fi

# Environment detection
: ${HOOKS_DIR:=~/.task/hooks}
: ${SCRIPTS_DIR:=~/.task/scripts}
: ${CONFIG_DIR:=~/.task/config}
: ${DOCS_DIR:=~/.task/docs}
: ${TASKRC:=~/.taskrc}

# Check requirements
check_requirements() {
    tw_msg "Checking requirements..."
    
    if ! command -v curl &>/dev/null; then
        tw_die "curl is required but not found"
    fi
    
    if type tw_check_taskwarrior_version &>/dev/null; then
        tw_check_taskwarrior_version "2.6.0" || return 1
    fi
    
    tw_success "Requirements met"
    return 0
}

# Install function
install() {
    tw_msg "Installing $APP_NAME v$APP_VERSION..."
    
    # Check requirements
    check_requirements || return 1
    
    # Create directories
    mkdir -p "$HOOKS_DIR" "$CONFIG_DIR" "$DOCS_DIR"
    
    # Download files (with or without tw-common.sh)
    if type tw_curl_and_place &>/dev/null; then
        tw_curl_and_place "$BASE_URL/on-add.py" "$HOOKS_DIR" "on-add_$APP_NAME.py" || return 1
        tw_curl_and_place "$BASE_URL/myapp.rc" "$CONFIG_DIR" || return 1
    else
        curl -fsSL "$BASE_URL/on-add.py" -o "$HOOKS_DIR/on-add_$APP_NAME.py" || return 1
        curl -fsSL "$BASE_URL/myapp.rc" -o "$CONFIG_DIR/myapp.rc" || return 1
    fi
    
    # Make hooks executable
    chmod +x "$HOOKS_DIR/on-add_$APP_NAME.py"
    
    # Configure Taskwarrior
    if type tw_add_config &>/dev/null; then
        tw_add_config "include $CONFIG_DIR/myapp.rc" || return 1
    else
        if ! grep -Fxq "include $CONFIG_DIR/myapp.rc" "$TASKRC"; then
            echo "include $CONFIG_DIR/myapp.rc" >> "$TASKRC"
        fi
    fi
    
    tw_success "Installed $APP_NAME v$APP_VERSION"
    return 0
}

# Remove function
remove() {
    tw_msg "Removing $APP_NAME..."
    
    # Remove files
    rm -f "$HOOKS_DIR/on-add_$APP_NAME.py"
    rm -f "$CONFIG_DIR/myapp.rc"
    rm -f "$DOCS_DIR/myapp_README.md"
    
    # Remove config from .taskrc
    if type tw_remove_config &>/dev/null; then
        tw_remove_config "include $CONFIG_DIR/myapp.rc"
    else
        if [[ -f "$TASKRC" ]]; then
            grep -Fxv "include $CONFIG_DIR/myapp.rc" "$TASKRC" > "$TASKRC.tmp"
            mv "$TASKRC.tmp" "$TASKRC"
        fi
    fi
    
    tw_success "Removed $APP_NAME"
    return 0
}

# Main dispatcher
case "${1:-}" in
    install)
        install
        ;;
    remove|uninstall)
        remove
        ;;
    *)
        echo "Usage: $0 {install|remove}"
        exit 1
        ;;
esac
```

## Best Practices

### 1. Always Check Requirements

```bash
check_requirements() {
    tw_msg "Checking requirements..."
    
    # Check for required commands
    for cmd in curl task python3; do
        if ! command -v "$cmd" &>/dev/null; then
            tw_die "$cmd is required but not found"
        fi
    done
    
    # Check versions if tw-common.sh available
    if type tw_check_taskwarrior_version &>/dev/null; then
        tw_check_taskwarrior_version "2.6.0" || return 1
    fi
    
    return 0
}
```

### 2. Create Directories Before Use

```bash
install() {
    # Always ensure directories exist
    mkdir -p "$HOOKS_DIR" "$SCRIPTS_DIR" "$CONFIG_DIR" "$DOCS_DIR"
    
    # Then proceed with installation
    # ...
}
```

### 3. Make Hooks Executable

```bash
# After downloading hooks
chmod +x "$HOOKS_DIR"/on-*_myapp.py
```

### 4. Handle README Renaming

```bash
# Download README with renamed filename
if type tw_curl_and_place &>/dev/null; then
    tw_curl_and_place "$BASE_URL/README.md" "$DOCS_DIR" "${APP_NAME}_README.md"
else
    curl -fsSL "$BASE_URL/README.md" -o "$DOCS_DIR/${APP_NAME}_README.md"
fi
```

### 5. Clean Uninstall

```bash
remove() {
    # Remove all files that were installed
    rm -f "$HOOKS_DIR/on-add_$APP_NAME.py"
    rm -f "$HOOKS_DIR/on-modify_$APP_NAME.py"
    rm -f "$CONFIG_DIR/$APP_NAME.rc"
    rm -f "$DOCS_DIR/${APP_NAME}_README.md"
    
    # Remove from .taskrc
    if type tw_remove_config &>/dev/null; then
        tw_remove_config "include $CONFIG_DIR/$APP_NAME.rc"
    fi
    
    return 0
}
```

## Migration from v1.3.0

v2.0.0 removes git-based functions and introduces curl-based utilities:

### Removed Functions

- `tw_clone_to_project()` - No longer needed (use `tw_curl_and_place`)
- `tw_symlink_hook()` - No longer needed (direct placement)
- `tw_symlink_wrapper()` - No longer needed (direct placement)
- `tw_get_install_dir()` - No longer needed (explicit directories)

### New Pattern

```bash
# OLD (v1.3.0)
tw_clone_to_project hook myapp "$REPO_URL"
tw_symlink_hook "$INSTALL_DIR/myapp" "on-add.py"

# NEW (v2.0.0)
tw_curl_and_place "$BASE_URL/on-add.py" "$HOOKS_DIR" "on-add_myapp.py"
tw_ensure_executable "$HOOKS_DIR/on-add_myapp.py"
```

## See Also

- [DEVELOPERS.md](DEVELOPERS.md) - Architecture and .meta file format
- [CONTRIBUTING.md](CONTRIBUTING.md) - How to create installers
- [MIGRATION.md](MIGRATION.md) - Migrating from v1.3.0 to v2.0.0
