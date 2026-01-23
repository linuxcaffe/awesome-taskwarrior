#!/usr/bin/env bash
#
# tw-common.sh - Shared utilities for Taskwarrior app installers
# Version: 2.0.0
#
# This library provides common functions for installers to use, including:
# - Curl-based file downloading
# - Direct file placement and installation
# - Configuration management
# - Checksum verification
# - Manifest tracking
# - Testing utilities
#
# IMPORTANT: v2.0.0 removes git-based operations in favor of curl-based
# direct file placement. See MIGRATION.md for details.
#
# Usage in installers:
#   if [[ -f "${TW_COMMON:-$HOME/.local/share/awesome-taskwarrior/lib/tw-common.sh}" ]]; then
#       source "$TW_COMMON"
#   fi
#

set -euo pipefail

#------------------------------------------------------------------------------
# ENVIRONMENT VARIABLES
#------------------------------------------------------------------------------

: "${INSTALL_DIR:=$HOME/.task}"
: "${HOOKS_DIR:=$INSTALL_DIR/hooks}"
: "${SCRIPTS_DIR:=$INSTALL_DIR/scripts}"
: "${CONFIG_DIR:=$INSTALL_DIR/config}"
: "${DOCS_DIR:=$INSTALL_DIR/docs}"
: "${LOGS_DIR:=$INSTALL_DIR/logs}"
: "${TASKRC:=$HOME/.taskrc}"
: "${TW_DEBUG:=0}"
: "${TW_MANIFEST:=$INSTALL_DIR/.tw_manifest}"

#------------------------------------------------------------------------------
# MESSAGING FUNCTIONS
#------------------------------------------------------------------------------

tw_msg() {
    echo "[tw] $*"
}

tw_success() {
    echo "[tw] ✓ $*"
}

tw_error() {
    echo "[tw] ✗ $*" >&2
}

tw_warn() {
    echo "[tw] ⚠ $*" >&2
}

tw_debug() {
    if [[ "${TW_DEBUG:-0}" == "1" ]]; then
        echo "[tw-debug] $*" >&2
    fi
}

#------------------------------------------------------------------------------
# INITIALIZATION
#------------------------------------------------------------------------------

tw_init_directories() {
    # Create all required directories
    mkdir -p "$HOOKS_DIR" "$SCRIPTS_DIR" "$CONFIG_DIR" "$DOCS_DIR" "$LOGS_DIR"
    tw_debug "Directories initialized: hooks, scripts, config, docs, logs"
}

#------------------------------------------------------------------------------
# CURL-BASED FILE OPERATIONS
#------------------------------------------------------------------------------

tw_curl_file() {
    # Download a file using curl
    # Usage: tw_curl_file URL [OUTPUT_FILE]
    # Returns: 0 on success, 1 on failure
    
    local url="$1"
    local output="${2:-}"
    
    tw_debug "Downloading: $url"
    
    if [[ -z "$output" ]]; then
        # Download to stdout
        if curl -fsSL "$url"; then
            return 0
        else
            tw_error "Failed to download: $url"
            return 1
        fi
    else
        # Download to file
        if curl -fsSL "$url" -o "$output"; then
            tw_debug "Downloaded to: $output"
            return 0
        else
            tw_error "Failed to download $url to $output"
            return 1
        fi
    fi
}

tw_curl_and_place() {
    # Download a file and place it in a specific directory with optional renaming
    # Usage: tw_curl_and_place URL TARGET_DIR [NEW_FILENAME]
    # Returns: 0 on success, 1 on failure
    
    local url="$1"
    local target_dir="$2"
    local new_filename="${3:-}"
    
    # Extract original filename if no new name provided
    if [[ -z "$new_filename" ]]; then
        new_filename=$(basename "$url")
    fi
    
    local target_path="$target_dir/$new_filename"
    
    tw_debug "Downloading $url -> $target_path"
    
    mkdir -p "$target_dir"
    
    if tw_curl_file "$url" "$target_path"; then
        tw_debug "Placed: $target_path"
        return 0
    else
        return 1
    fi
}

tw_ensure_executable() {
    # Make a file executable
    # Usage: tw_ensure_executable FILE
    
    local file="$1"
    
    if [[ -f "$file" ]]; then
        chmod +x "$file"
        tw_debug "Made executable: $file"
        return 0
    else
        tw_error "File not found: $file"
        return 1
    fi
}

tw_backup_file() {
    # Create a backup of a file before modifying it
    # Usage: tw_backup_file FILE
    
    local file="$1"
    
    if [[ -f "$file" ]]; then
        local backup="${file}.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$file" "$backup"
        tw_debug "Backed up: $file -> $backup"
        return 0
    else
        tw_debug "No backup needed (file doesn't exist): $file"
        return 0
    fi
}

#------------------------------------------------------------------------------
# CHECKSUM VERIFICATION
#------------------------------------------------------------------------------

tw_verify_checksum() {
    # Verify SHA256 checksum of a file
    # Usage: tw_verify_checksum FILE EXPECTED_CHECKSUM
    # Returns: 0 if matches, 1 if doesn't match
    
    local file="$1"
    local expected="$2"
    
    if [[ -z "$expected" ]]; then
        tw_debug "No checksum provided, skipping verification"
        return 0
    fi
    
    if [[ ! -f "$file" ]]; then
        tw_error "Cannot verify checksum: file not found: $file"
        return 1
    fi
    
    local actual
    if command -v sha256sum &>/dev/null; then
        actual=$(sha256sum "$file" | awk '{print $1}')
    elif command -v shasum &>/dev/null; then
        actual=$(shasum -a 256 "$file" | awk '{print $1}')
    else
        tw_warn "No SHA256 utility found, skipping checksum verification"
        return 0
    fi
    
    if [[ "$actual" == "$expected" ]]; then
        tw_debug "Checksum verified: $file"
        return 0
    else
        tw_error "Checksum mismatch for $file"
        tw_error "  Expected: $expected"
        tw_error "  Actual:   $actual"
        return 1
    fi
}

tw_calculate_checksum() {
    # Calculate SHA256 checksum of a file
    # Usage: tw_calculate_checksum FILE
    # Outputs: checksum string
    
    local file="$1"
    
    if [[ ! -f "$file" ]]; then
        tw_error "Cannot calculate checksum: file not found: $file"
        return 1
    fi
    
    if command -v sha256sum &>/dev/null; then
        sha256sum "$file" | awk '{print $1}'
    elif command -v shasum &>/dev/null; then
        shasum -a 256 "$file" | awk '{print $1}'
    else
        tw_error "No SHA256 utility found"
        return 1
    fi
}

#------------------------------------------------------------------------------
# MANIFEST MANAGEMENT
#------------------------------------------------------------------------------

tw_manifest_add() {
    # Add an entry to the installation manifest
    # Usage: tw_manifest_add APP VERSION FILE [CHECKSUM]
    # Format: app|version|file|checksum|date
    
    local app="$1"
    local version="$2"
    local file="$3"
    local checksum="${4:-}"
    local date
    date=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    mkdir -p "$(dirname "$TW_MANIFEST")"
    
    # Remove any existing entry for this file
    if [[ -f "$TW_MANIFEST" ]]; then
        grep -v "^${app}|${version}|${file}|" "$TW_MANIFEST" > "${TW_MANIFEST}.tmp" || true
        mv "${TW_MANIFEST}.tmp" "$TW_MANIFEST"
    fi
    
    # Add new entry
    echo "${app}|${version}|${file}|${checksum}|${date}" >> "$TW_MANIFEST"
    tw_debug "Manifest: added $app $version $file"
}

tw_manifest_remove() {
    # Remove entries from manifest for a specific app
    # Usage: tw_manifest_remove APP
    
    local app="$1"
    
    if [[ -f "$TW_MANIFEST" ]]; then
        grep -v "^${app}|" "$TW_MANIFEST" > "${TW_MANIFEST}.tmp" || true
        mv "${TW_MANIFEST}.tmp" "$TW_MANIFEST"
        tw_debug "Manifest: removed all entries for $app"
    fi
}

tw_manifest_get_files() {
    # Get list of files installed by an app
    # Usage: tw_manifest_get_files APP
    # Outputs: one file path per line
    
    local app="$1"
    
    if [[ -f "$TW_MANIFEST" ]]; then
        grep "^${app}|" "$TW_MANIFEST" | cut -d'|' -f3
    fi
}

tw_manifest_app_installed() {
    # Check if an app is in the manifest
    # Usage: tw_manifest_app_installed APP
    # Returns: 0 if installed, 1 if not
    
    local app="$1"
    
    if [[ -f "$TW_MANIFEST" ]] && grep -q "^${app}|" "$TW_MANIFEST"; then
        return 0
    else
        return 1
    fi
}

#------------------------------------------------------------------------------
# INSTALLATION HELPERS
#------------------------------------------------------------------------------

tw_install_to() {
    # Install a file to the appropriate directory based on type
    # Usage: tw_install_to TYPE FILE [TARGET_NAME]
    # TYPE: hook, script, config, doc
    # Returns: 0 on success, 1 on failure
    
    local file_type="$1"
    local source_file="$2"
    local target_name="${3:-$(basename "$source_file")}"
    
    local target_dir
    case "$file_type" in
        hook)
            target_dir="$HOOKS_DIR"
            ;;
        script)
            target_dir="$SCRIPTS_DIR"
            ;;
        config)
            target_dir="$CONFIG_DIR"
            ;;
        doc)
            target_dir="$DOCS_DIR"
            ;;
        *)
            tw_error "Unknown file type: $file_type"
            return 1
            ;;
    esac
    
    mkdir -p "$target_dir"
    
    if [[ -f "$source_file" ]]; then
        cp "$source_file" "$target_dir/$target_name"
        tw_debug "Installed: $target_name -> $target_dir/"
        
        # Make hooks and scripts executable
        if [[ "$file_type" == "hook" ]] || [[ "$file_type" == "script" ]]; then
            chmod +x "$target_dir/$target_name"
            tw_debug "Made executable: $target_dir/$target_name"
        fi
        
        return 0
    else
        tw_error "Source file not found: $source_file"
        return 1
    fi
}

tw_uninstall_app() {
    # Uninstall an app using manifest data
    # Usage: tw_uninstall_app APP
    # Returns: 0 on success, 1 if app not installed
    
    local app="$1"
    
    if ! tw_manifest_app_installed "$app"; then
        tw_warn "App not installed: $app"
        return 1
    fi
    
    # Get list of files and remove them
    local files
    files=$(tw_manifest_get_files "$app")
    
    if [[ -n "$files" ]]; then
        while IFS= read -r file; do
            if [[ -f "$file" ]]; then
                rm -f "$file"
                tw_debug "Removed: $file"
            elif [[ -L "$file" ]]; then
                rm -f "$file"
                tw_debug "Removed symlink: $file"
            else
                tw_debug "File not found (already removed?): $file"
            fi
        done <<< "$files"
    fi
    
    # Remove from manifest
    tw_manifest_remove "$app"
    
    tw_success "Uninstalled: $app"
    return 0
}

#------------------------------------------------------------------------------
# CONFIGURATION MANAGEMENT
#------------------------------------------------------------------------------

tw_config_exists() {
    # Check if a configuration line exists in .taskrc
    # Usage: tw_config_exists "config line"
    # Returns: 0 if exists, 1 if not
    
    local config_line="$1"
    
    if [[ -f "$TASKRC" ]] && grep -Fq "$config_line" "$TASKRC"; then
        return 0
    else
        return 1
    fi
}

tw_add_config() {
    # Add a configuration line to .taskrc if not already present
    # Usage: tw_add_config "config line"
    
    local config_line="$1"
    
    if ! tw_config_exists "$config_line"; then
        echo "$config_line" >> "$TASKRC"
        tw_debug "Added to .taskrc: $config_line"
    else
        tw_debug "Already in .taskrc: $config_line"
    fi
}

tw_remove_config() {
    # Remove a configuration line from .taskrc
    # Usage: tw_remove_config "config line"
    
    local config_line="$1"
    
    if [[ -f "$TASKRC" ]]; then
        tw_backup_file "$TASKRC"
        grep -Fv "$config_line" "$TASKRC" > "${TASKRC}.tmp" || true
        mv "${TASKRC}.tmp" "$TASKRC"
        tw_debug "Removed from .taskrc: $config_line"
    fi
}

#------------------------------------------------------------------------------
# VERSION CHECKING
#------------------------------------------------------------------------------

tw_check_version() {
    # Check if a version meets a requirement
    # Usage: tw_check_version CURRENT REQUIRED
    # Returns: 0 if current >= required, 1 otherwise
    
    local current="$1"
    local required="$2"
    
    # Simple version comparison (works for X.Y.Z format)
    if [[ "$(printf '%s\n' "$required" "$current" | sort -V | head -n1)" == "$required" ]]; then
        return 0
    else
        return 1
    fi
}

tw_check_taskwarrior_version() {
    # Check if Taskwarrior version meets requirement
    # Usage: tw_check_taskwarrior_version REQUIRED_VERSION
    # Returns: 0 if meets requirement, 1 otherwise
    
    local required="$1"
    
    if ! command -v task &>/dev/null; then
        tw_error "Taskwarrior not found"
        return 1
    fi
    
    local current
    current=$(task --version | head -n1 | awk '{print $2}')
    
    if tw_check_version "$current" "$required"; then
        tw_debug "Taskwarrior version OK: $current >= $required"
        return 0
    else
        tw_error "Taskwarrior version $current < $required"
        return 1
    fi
}

tw_check_python_version() {
    # Check if Python version meets requirement
    # Usage: tw_check_python_version REQUIRED_VERSION
    # Returns: 0 if meets requirement, 1 otherwise
    
    local required="$1"
    
    if ! command -v python3 &>/dev/null; then
        tw_error "Python 3 not found"
        return 1
    fi
    
    local current
    current=$(python3 --version | awk '{print $2}')
    
    if tw_check_version "$current" "$required"; then
        tw_debug "Python version OK: $current >= $required"
        return 0
    else
        tw_error "Python version $current < $required"
        return 1
    fi
}

#------------------------------------------------------------------------------
# TESTING UTILITIES
#------------------------------------------------------------------------------

tw_run_tests() {
    # Run tests for an app if test directory exists
    # Usage: tw_run_tests APP_DIR
    # Returns: 0 if tests pass, 1 if tests fail
    
    local app_dir="$1"
    local test_dir="$app_dir/test"
    
    if [[ ! -d "$test_dir" ]]; then
        tw_debug "No test directory found: $test_dir"
        return 0
    fi
    
    tw_msg "Running tests..."
    
    if [[ -f "$test_dir/run_tests.sh" ]]; then
        if bash "$test_dir/run_tests.sh"; then
            tw_success "Tests passed"
            return 0
        else
            tw_error "Tests failed"
            return 1
        fi
    else
        tw_warn "No run_tests.sh found in $test_dir"
        return 0
    fi
}

#------------------------------------------------------------------------------
# INITIALIZATION ON LOAD
#------------------------------------------------------------------------------

# Create directories when library is sourced
tw_init_directories

tw_debug "tw-common.sh v2.0.0 loaded"
