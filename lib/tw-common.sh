#!/usr/bin/env bash
#
# tw-common.sh - Common utilities for Taskwarrior awesome-taskwarrior project
# Version: 2.0.0
# Architecture: Curl-based direct file placement
#
# This is a PURE UTILITY LIBRARY with no dependencies on tw.py or manifest operations.
# Installers can optionally source this for better UX but must work without it.
#
# Usage in installers:
#   if [[ -f ~/.task/lib/tw-common.sh ]]; then
#       source ~/.task/lib/tw-common.sh
#   else
#       # Fallback: define minimal functions inline
#       tw_msg() { echo "$@"; }
#   fi

set -euo pipefail

# Version
TW_COMMON_VERSION="2.0.0"

#=============================================================================
# MESSAGING FUNCTIONS
#=============================================================================

# Print info message
tw_msg() {
    echo "[INFO] $*"
}

# Print success message
tw_success() {
    echo "[SUCCESS] $*"
}

# Print warning message
tw_warn() {
    echo "[WARNING] $*" >&2
}

# Print error message
tw_error() {
    echo "[ERROR] $*" >&2
}

# Print error and exit
tw_die() {
    tw_error "$@"
    exit 1
}

# Print debug message (only if TW_DEBUG is set)
tw_debug() {
    if [[ -n "${TW_DEBUG:-}" ]]; then
        echo "[DEBUG] $*" >&2
    fi
}

#=============================================================================
# VERSION CHECKING FUNCTIONS
#=============================================================================

# Check if a command exists
# Usage: tw_command_exists curl
tw_command_exists() {
    command -v "$1" &>/dev/null
}

# Check Taskwarrior version meets minimum requirement
# Usage: tw_check_taskwarrior_version "2.6.0"
tw_check_taskwarrior_version() {
    local required="$1"
    
    if ! tw_command_exists task; then
        tw_error "Taskwarrior not found. Please install Taskwarrior first."
        return 1
    fi
    
    local installed
    installed=$(task --version | grep -oP '\d+\.\d+\.\d+' | head -1)
    
    if [[ -z "$installed" ]]; then
        tw_warn "Could not determine Taskwarrior version"
        return 0  # Don't fail, just warn
    fi
    
    # Simple version comparison (assumes semantic versioning)
    if [[ "$(printf '%s\n' "$required" "$installed" | sort -V | head -1)" != "$required" ]]; then
        tw_error "Taskwarrior $required or higher required (found $installed)"
        return 1
    fi
    
    tw_debug "Taskwarrior version check passed: $installed >= $required"
    return 0
}

# Check Python version meets minimum requirement
# Usage: tw_check_python_version "3.6"
tw_check_python_version() {
    local required="$1"
    
    if ! tw_command_exists python3; then
        tw_error "Python 3 not found. Please install Python 3."
        return 1
    fi
    
    local installed
    installed=$(python3 --version | grep -oP '\d+\.\d+')
    
    if [[ -z "$installed" ]]; then
        tw_warn "Could not determine Python version"
        return 0  # Don't fail, just warn
    fi
    
    # Simple version comparison
    if [[ "$(printf '%s\n' "$required" "$installed" | sort -V | head -1)" != "$required" ]]; then
        tw_error "Python $required or higher required (found $installed)"
        return 1
    fi
    
    tw_debug "Python version check passed: $installed >= $required"
    return 0
}

# Check Bash version meets minimum requirement
# Usage: tw_check_bash_version "4.0"
tw_check_bash_version() {
    local required="$1"
    local installed="${BASH_VERSINFO[0]}.${BASH_VERSINFO[1]}"
    
    if [[ "$(printf '%s\n' "$required" "$installed" | sort -V | head -1)" != "$required" ]]; then
        tw_error "Bash $required or higher required (found $installed)"
        return 1
    fi
    
    tw_debug "Bash version check passed: $installed >= $required"
    return 0
}

#=============================================================================
# FILE OPERATIONS
#=============================================================================

# Download a file and place it in target directory
# Usage: tw_curl_and_place URL TARGET_DIR [FILENAME]
tw_curl_and_place() {
    local url="$1"
    local target_dir="$2"
    local filename="${3:-$(basename "$url")}"
    local target_path="$target_dir/$filename"
    
    tw_debug "Downloading $url to $target_path"
    
    # Ensure target directory exists
    if [[ ! -d "$target_dir" ]]; then
        mkdir -p "$target_dir" || {
            tw_error "Failed to create directory: $target_dir"
            return 1
        }
    fi
    
    # Download to temp file first
    local tmp_file
    tmp_file=$(mktemp) || {
        tw_error "Failed to create temporary file"
        return 1
    }
    
    if ! curl -fsSL "$url" -o "$tmp_file"; then
        tw_error "Failed to download: $url"
        rm -f "$tmp_file"
        return 1
    fi
    
    # Move to final location
    if ! mv "$tmp_file" "$target_path"; then
        tw_error "Failed to move file to: $target_path"
        rm -f "$tmp_file"
        return 1
    fi
    
    tw_success "Downloaded: $filename"
    return 0
}

# Make a file executable
# Usage: tw_ensure_executable FILE
tw_ensure_executable() {
    local file="$1"
    
    if [[ ! -f "$file" ]]; then
        tw_error "File not found: $file"
        return 1
    fi
    
    chmod +x "$file" || {
        tw_error "Failed to make executable: $file"
        return 1
    }
    
    tw_debug "Made executable: $file"
    return 0
}

# Create a backup of a file
# Usage: tw_backup_file FILE
tw_backup_file() {
    local file="$1"
    
    if [[ ! -f "$file" ]]; then
        tw_debug "No file to backup: $file"
        return 0
    fi
    
    local backup="${file}.backup.$(date +%Y%m%d_%H%M%S)"
    
    if cp "$file" "$backup"; then
        tw_success "Backed up: $file -> $backup"
        return 0
    else
        tw_error "Failed to backup: $file"
        return 1
    fi
}

# Remove a file safely (with confirmation if interactive)
# Usage: tw_remove_file FILE
tw_remove_file() {
    local file="$1"
    
    if [[ ! -f "$file" ]]; then
        tw_debug "File does not exist: $file"
        return 0
    fi
    
    if rm "$file"; then
        tw_success "Removed: $file"
        return 0
    else
        tw_error "Failed to remove: $file"
        return 1
    fi
}

#=============================================================================
# TASKRC CONFIGURATION MANAGEMENT
#=============================================================================

# Add a config line to .taskrc if it doesn't exist
# Usage: tw_add_config "include ~/.task/config/myapp.rc"
tw_add_config() {
    local config_line="$1"
    local taskrc="${TASKRC:-$HOME/.taskrc}"
    
    if [[ ! -f "$taskrc" ]]; then
        tw_error ".taskrc not found: $taskrc"
        return 1
    fi
    
    # Check if config already exists
    if grep -Fxq "$config_line" "$taskrc"; then
        tw_debug "Config already exists in .taskrc: $config_line"
        return 0
    fi
    
    # Add config line
    if echo "$config_line" >> "$taskrc"; then
        tw_success "Added to .taskrc: $config_line"
        return 0
    else
        tw_error "Failed to add to .taskrc: $config_line"
        return 1
    fi
}

# Remove a config line from .taskrc
# Usage: tw_remove_config "include ~/.task/config/myapp.rc"
tw_remove_config() {
    local config_line="$1"
    local taskrc="${TASKRC:-$HOME/.taskrc}"
    
    if [[ ! -f "$taskrc" ]]; then
        tw_warn ".taskrc not found: $taskrc"
        return 0
    fi
    
    # Check if config exists
    if ! grep -Fxq "$config_line" "$taskrc"; then
        tw_debug "Config not found in .taskrc: $config_line"
        return 0
    fi
    
    # Remove config line (using temp file for safety)
    local tmp_file
    tmp_file=$(mktemp) || {
        tw_error "Failed to create temporary file"
        return 1
    }
    
    if grep -Fxv "$config_line" "$taskrc" > "$tmp_file" && mv "$tmp_file" "$taskrc"; then
        tw_success "Removed from .taskrc: $config_line"
        return 0
    else
        tw_error "Failed to remove from .taskrc: $config_line"
        rm -f "$tmp_file"
        return 1
    fi
}

# Check if a config line exists in .taskrc
# Usage: tw_config_exists "include ~/.task/config/myapp.rc"
tw_config_exists() {
    local config_line="$1"
    local taskrc="${TASKRC:-$HOME/.taskrc}"
    
    if [[ ! -f "$taskrc" ]]; then
        return 1
    fi
    
    grep -Fxq "$config_line" "$taskrc"
}

#=============================================================================
# TESTING HELPERS
#=============================================================================

# Check if running in test mode
# Usage: if tw_is_test_mode; then ... fi
tw_is_test_mode() {
    [[ -n "${TW_TEST_MODE:-}" ]]
}

# Get test environment directory
# Usage: test_dir=$(tw_get_test_dir)
tw_get_test_dir() {
    echo "${TW_TEST_DIR:-/tmp/tw-test-$$}"
}

# Initialize test environment
# Usage: tw_init_test_env
tw_init_test_env() {
    local test_dir
    test_dir=$(tw_get_test_dir)
    
    if [[ -d "$test_dir" ]]; then
        tw_warn "Test directory already exists: $test_dir"
        return 0
    fi
    
    mkdir -p "$test_dir"/{hooks,scripts,config,docs,lib} || {
        tw_error "Failed to create test directory structure"
        return 1
    }
    
    tw_success "Initialized test environment: $test_dir"
    return 0
}

# Clean up test environment
# Usage: tw_cleanup_test_env
tw_cleanup_test_env() {
    local test_dir
    test_dir=$(tw_get_test_dir)
    
    if [[ ! -d "$test_dir" ]]; then
        tw_debug "Test directory does not exist: $test_dir"
        return 0
    fi
    
    if rm -rf "$test_dir"; then
        tw_success "Cleaned up test environment: $test_dir"
        return 0
    else
        tw_error "Failed to clean up test environment: $test_dir"
        return 1
    fi
}

#=============================================================================
# LIBRARY INITIALIZATION
#=============================================================================

tw_debug "tw-common.sh v${TW_COMMON_VERSION} loaded"
