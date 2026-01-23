# awesome-taskwarrior API Reference
**Version:** 2.0.0  
**Library:** lib/tw-common.sh

## Overview

tw-common.sh provides bash utilities for creating self-contained Taskwarrior application installers. Version 2.0.0 introduces a **curl-based architecture** that replaces git operations with direct file downloads and placement.

**Key Changes in v2.0.0:**
- Removed git-based functions (tw_clone_to_project, tw_symlink_hook, etc.)
- Added curl-based file operations
- Added manifest tracking (per-file granularity)
- Added checksum verification
- Added docs_dir support

## Quick Start

```bash
# In your installer script
if [[ -f "${TW_COMMON:-$HOME/.local/share/awesome-taskwarrior/lib/tw-common.sh}" ]]; then
    source "$TW_COMMON"
fi

# Download and install files
tw_curl_and_place "$BASE_URL/on-add_myapp.py" "$HOOKS_DIR"
tw_ensure_executable "$HOOKS_DIR/on-add_myapp.py"

# Track in manifest
tw_manifest_add "myapp" "1.0.0" "$HOOKS_DIR/on-add_myapp.py" "$checksum"
```

## Environment Variables

These variables are automatically set by tw.py or can be overridden:

```bash
INSTALL_DIR=~/.task              # Main Taskwarrior directory
HOOKS_DIR=~/.task/hooks          # Taskwarrior hooks
SCRIPTS_DIR=~/.task/scripts      # Wrapper scripts
CONFIG_DIR=~/.task/config        # Configuration files
DOCS_DIR=~/.task/docs            # Documentation/README files
LOGS_DIR=~/.task/logs            # Debug and test logs
TASKRC=~/.taskrc                 # Taskwarrior config file
TW_DEBUG=0                       # Enable debug output (0 or 1)
TW_MANIFEST=~/.task/.tw_manifest # Installation manifest
```

## Function Reference

### Messaging Functions

#### `tw_msg MESSAGE`
Display an informational message.

```bash
tw_msg "Installing myapp..."
# Output: [tw] Installing myapp...
```

#### `tw_success MESSAGE`
Display a success message with checkmark.

```bash
tw_success "Installation complete"
# Output: [tw] ✓ Installation complete
```

#### `tw_error MESSAGE`
Display an error message to stderr.

```bash
tw_error "File not found"
# Output: [tw] ✗ File not found
```

#### `tw_warn MESSAGE`
Display a warning message to stderr.

```bash
tw_warn "Configuration file already exists"
# Output: [tw] ⚠ Configuration file already exists
```

#### `tw_debug MESSAGE`
Display a debug message (only if TW_DEBUG=1).

```bash
TW_DEBUG=1
tw_debug "Checksum verified"
# Output: [tw-debug] Checksum verified
```

### File Operations

#### `tw_curl_file URL [OUTPUT_FILE]`
Download a file using curl.

**Parameters:**
- `URL` - URL to download from
- `OUTPUT_FILE` - Optional output path (default: stdout)

**Returns:** 0 on success, 1 on failure

**Examples:**
```bash
# Download to stdout
content=$(tw_curl_file "https://example.com/file.txt")

# Download to file
tw_curl_file "https://example.com/file.py" "/tmp/file.py"
```

#### `tw_curl_and_place URL TARGET_DIR [NEW_FILENAME]`
Download a file and place it in a specific directory with optional renaming.

**Parameters:**
- `URL` - URL to download from
- `TARGET_DIR` - Directory to place file in
- `NEW_FILENAME` - Optional new filename (default: basename of URL)

**Returns:** 0 on success, 1 on failure

**Examples:**
```bash
# Download with original name
tw_curl_and_place "$BASE_URL/hook.py" "$HOOKS_DIR"

# Download with renamed file
tw_curl_and_place "$BASE_URL/README.md" "$DOCS_DIR" "myapp_README.md"
```

#### `tw_ensure_executable FILE`
Make a file executable.

**Parameters:**
- `FILE` - Path to file

**Returns:** 0 on success, 1 if file not found

**Example:**
```bash
tw_ensure_executable "$HOOKS_DIR/on-add_myapp.py"
```

#### `tw_backup_file FILE`
Create a timestamped backup of a file.

**Parameters:**
- `FILE` - Path to file

**Returns:** 0 always (creates backup only if file exists)

**Example:**
```bash
tw_backup_file "$TASKRC"
# Creates: ~/.taskrc.backup.20260122_143000
```

### Installation Functions

#### `tw_install_to TYPE SOURCE_FILE [TARGET_NAME]`
Install a file to the appropriate directory based on type.

**Parameters:**
- `TYPE` - File type: hook, script, config, doc
- `SOURCE_FILE` - Source file path
- `TARGET_NAME` - Optional target filename (default: basename of source)

**Returns:** 0 on success, 1 on failure

**File Type Mappings:**
- `hook` → `$HOOKS_DIR` (made executable)
- `script` → `$SCRIPTS_DIR` (made executable)
- `config` → `$CONFIG_DIR`
- `doc` → `$DOCS_DIR`

**Examples:**
```bash
# Install hook (will be made executable)
tw_install_to hook "/tmp/on-add_myapp.py"

# Install with renamed target
tw_install_to doc "/tmp/README.md" "myapp_README.md"

# Install config file
tw_install_to config "/tmp/myapp.rc"
```

#### `tw_uninstall_app APP`
Uninstall an app using manifest data.

**Parameters:**
- `APP` - Application name

**Returns:** 0 on success, 1 if app not installed

**Example:**
```bash
tw_uninstall_app "myapp"
# Removes all files tracked in manifest for myapp
# Removes manifest entries for myapp
```

### Manifest Management

#### `tw_manifest_add APP VERSION FILE [CHECKSUM]`
Add an entry to the installation manifest.

**Parameters:**
- `APP` - Application name
- `VERSION` - Application version
- `FILE` - File path that was installed
- `CHECKSUM` - Optional SHA256 checksum

**Format:** `app|version|file|checksum|date`

**Example:**
```bash
tw_manifest_add "myapp" "1.0.0" "$HOOKS_DIR/on-add_myapp.py" "$checksum"
```

#### `tw_manifest_remove APP`
Remove all manifest entries for an app.

**Parameters:**
- `APP` - Application name

**Example:**
```bash
tw_manifest_remove "myapp"
```

#### `tw_manifest_get_files APP`
Get list of files installed by an app.

**Parameters:**
- `APP` - Application name

**Output:** One file path per line

**Example:**
```bash
files=$(tw_manifest_get_files "myapp")
while IFS= read -r file; do
    echo "Installed: $file"
done <<< "$files"
```

#### `tw_manifest_app_installed APP`
Check if an app is in the manifest.

**Parameters:**
- `APP` - Application name

**Returns:** 0 if installed, 1 if not

**Example:**
```bash
if tw_manifest_app_installed "myapp"; then
    tw_msg "Already installed"
fi
```

### Checksum Functions

#### `tw_verify_checksum FILE EXPECTED_CHECKSUM`
Verify SHA256 checksum of a file.

**Parameters:**
- `FILE` - File to verify
- `EXPECTED_CHECKSUM` - Expected SHA256 hash

**Returns:** 0 if matches, 1 if doesn't match or file not found

**Example:**
```bash
if tw_verify_checksum "$file" "$expected"; then
    tw_success "Checksum verified"
else
    tw_error "Checksum mismatch"
fi
```

#### `tw_calculate_checksum FILE`
Calculate SHA256 checksum of a file.

**Parameters:**
- `FILE` - File to calculate checksum for

**Output:** Checksum string

**Example:**
```bash
checksum=$(tw_calculate_checksum "$file")
echo "Checksum: $checksum"
```

### Configuration Management

#### `tw_config_exists "CONFIG_LINE"`
Check if a configuration line exists in .taskrc.

**Parameters:**
- `CONFIG_LINE` - Exact line to search for

**Returns:** 0 if exists, 1 if not

**Example:**
```bash
if tw_config_exists "include ~/.task/config/myapp.rc"; then
    tw_msg "Config already added"
fi
```

#### `tw_add_config "CONFIG_LINE"`
Add a configuration line to .taskrc if not already present.

**Parameters:**
- `CONFIG_LINE` - Line to add

**Example:**
```bash
tw_add_config "include ~/.task/config/myapp.rc"
```

#### `tw_remove_config "CONFIG_LINE"`
Remove a configuration line from .taskrc.

**Parameters:**
- `CONFIG_LINE` - Exact line to remove

**Example:**
```bash
tw_remove_config "include ~/.task/config/myapp.rc"
```

### Version Checking

#### `tw_check_version CURRENT REQUIRED`
Check if a version meets a requirement.

**Parameters:**
- `CURRENT` - Current version (X.Y.Z format)
- `REQUIRED` - Required minimum version

**Returns:** 0 if current >= required, 1 otherwise

**Example:**
```bash
if tw_check_version "2.6.2" "2.5.0"; then
    tw_msg "Version OK"
fi
```

#### `tw_check_taskwarrior_version REQUIRED`
Check if Taskwarrior version meets requirement.

**Parameters:**
- `REQUIRED` - Required minimum version

**Returns:** 0 if meets requirement, 1 otherwise

**Example:**
```bash
if ! tw_check_taskwarrior_version "2.6.0"; then
    tw_error "Requires Taskwarrior >= 2.6.0"
    exit 1
fi
```

#### `tw_check_python_version REQUIRED`
Check if Python version meets requirement.

**Parameters:**
- `REQUIRED` - Required minimum version

**Returns:** 0 if meets requirement, 1 otherwise

**Example:**
```bash
if ! tw_check_python_version "3.6"; then
    tw_error "Requires Python >= 3.6"
    exit 1
fi
```

### Testing Utilities

#### `tw_run_tests APP_DIR`
Run tests for an app if test directory exists.

**Parameters:**
- `APP_DIR` - Application directory path

**Returns:** 0 if tests pass or no tests, 1 if tests fail

**Example:**
```bash
if tw_run_tests "$HOOKS_DIR/myapp"; then
    tw_success "Tests passed"
fi
```

## Complete Installer Example

Here's a complete self-contained installer using tw-common.sh:

```bash
#!/usr/bin/env bash
set -euo pipefail

APPNAME="myapp"
VERSION="1.0.0"
BASE_URL="https://raw.githubusercontent.com/user/myapp/main"

# Environment detection (works standalone or with tw.py)
: "${HOOKS_DIR:=$HOME/.task/hooks}"
: "${CONFIG_DIR:=$HOME/.task/config}"
: "${DOCS_DIR:=$HOME/.task/docs}"
: "${TASKRC:=$HOME/.taskrc}"

# Optional: source tw-common.sh for helpers
if [[ -f "${TW_COMMON:-}" ]]; then
    source "$TW_COMMON"
else
    # Fallback messaging for standalone use
    tw_msg() { echo "[tw] $*"; }
    tw_success() { echo "[tw] ✓ $*"; }
    tw_error() { echo "[tw] ✗ $*" >&2; }
fi

install() {
    tw_msg "Installing $APPNAME v$VERSION..."
    
    # Download files
    if type tw_curl_and_place &>/dev/null; then
        tw_curl_and_place "$BASE_URL/on-add_myapp.py" "$HOOKS_DIR" || return 1
        tw_curl_and_place "$BASE_URL/myapp.rc" "$CONFIG_DIR" || return 1
        tw_curl_and_place "$BASE_URL/README.md" "$DOCS_DIR" "myapp_README.md" || return 1
    else
        # Fallback for standalone use
        mkdir -p "$HOOKS_DIR" "$CONFIG_DIR" "$DOCS_DIR"
        curl -fsSL "$BASE_URL/on-add_myapp.py" -o "$HOOKS_DIR/on-add_myapp.py" || return 1
        curl -fsSL "$BASE_URL/myapp.rc" -o "$CONFIG_DIR/myapp.rc" || return 1
        curl -fsSL "$BASE_URL/README.md" -o "$DOCS_DIR/myapp_README.md" || return 1
    fi
    
    # Make hook executable
    chmod +x "$HOOKS_DIR/on-add_myapp.py"
    
    # Add config to taskrc
    if type tw_add_config &>/dev/null; then
        tw_add_config "include $CONFIG_DIR/myapp.rc"
    else
        if ! grep -q "include $CONFIG_DIR/myapp.rc" "$TASKRC" 2>/dev/null; then
            echo "include $CONFIG_DIR/myapp.rc" >> "$TASKRC"
        fi
    fi
    
    # Track in manifest (if tw-common.sh available)
    if type tw_manifest_add &>/dev/null; then
        tw_manifest_add "$APPNAME" "$VERSION" "$HOOKS_DIR/on-add_myapp.py"
        tw_manifest_add "$APPNAME" "$VERSION" "$CONFIG_DIR/myapp.rc"
        tw_manifest_add "$APPNAME" "$VERSION" "$DOCS_DIR/myapp_README.md"
    fi
    
    tw_success "Installed $APPNAME v$VERSION"
    return 0
}

remove() {
    tw_msg "Removing $APPNAME..."
    
    # Use manifest-based removal if available
    if type tw_uninstall_app &>/dev/null; then
        tw_uninstall_app "$APPNAME"
    else
        # Fallback for standalone use
        rm -f "$HOOKS_DIR/on-add_myapp.py"
        rm -f "$CONFIG_DIR/myapp.rc"
        rm -f "$DOCS_DIR/myapp_README.md"
        
        # Remove config line
        if [[ -f "$TASKRC" ]]; then
            grep -v "include $CONFIG_DIR/myapp.rc" "$TASKRC" > "$TASKRC.tmp" || true
            mv "$TASKRC.tmp" "$TASKRC"
        fi
    fi
    
    tw_success "Removed $APPNAME"
    return 0
}

# Main entry point
case "${1:-}" in
    install)
        install
        ;;
    remove)
        remove
        ;;
    *)
        echo "Usage: $0 {install|remove}"
        exit 1
        ;;
esac
```

## Migration from v1.3.0

See [MIGRATION.md](../MIGRATION.md) for complete migration guide.

**Removed Functions:**
- `tw_clone_to_project()` - Use `tw_curl_and_place()`
- `tw_clone_or_update()` - No longer needed
- `tw_get_install_dir()` - Use explicit directory variables
- `tw_symlink_hook()` - Use direct placement
- `tw_symlink_wrapper()` - Use direct placement
- `tw_remove_hook()` - Use `tw_uninstall_app()`
- `tw_remove_wrapper()` - Use `tw_uninstall_app()`

## See Also

- [DEVELOPERS.md](../DEVELOPERS.md) - Architecture and .meta file format
- [CONTRIBUTING.md](../CONTRIBUTING.md) - How to create installers
- [MIGRATION.md](../MIGRATION.md) - Migrating from v1.3.0
