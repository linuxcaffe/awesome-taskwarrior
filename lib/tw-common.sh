#!/bin/bash
#
# tw-common.sh - Common library functions for awesome-taskwarrior installers
#
# This library provides standardized functions for:
# - Dependency checking
# - Repository management
# - Hook installation
# - Configuration management
# - Testing utilities
#
# Usage: source "$(dirname "$0")/../lib/tw-common.sh"

# Version
TW_COMMON_VERSION="1.0.0"

# Color output (if terminal supports it)
if [ -t 1 ]; then
    COLOR_RESET='\033[0m'
    COLOR_RED='\033[0;31m'
    COLOR_GREEN='\033[0;32m'
    COLOR_YELLOW='\033[0;33m'
    COLOR_BLUE='\033[0;34m'
else
    COLOR_RESET=''
    COLOR_RED=''
    COLOR_GREEN=''
    COLOR_YELLOW=''
    COLOR_BLUE=''
fi

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Print colored message
tw_msg() {
    local color="$1"
    shift
    echo -e "${color}$*${COLOR_RESET}"
}

# Print error message
tw_error() {
    tw_msg "$COLOR_RED" "Error: $*" >&2
}

# Print warning message
tw_warn() {
    tw_msg "$COLOR_YELLOW" "Warning: $*" >&2
}

# Print info message
tw_info() {
    tw_msg "$COLOR_BLUE" "$*"
}

# Print success message
tw_success() {
    tw_msg "$COLOR_GREEN" "$*"
}

# Debug print (only if TW_DEBUG is set)
tw_debug() {
    [ "$TW_DEBUG" = "1" ] && tw_msg "$COLOR_BLUE" "DEBUG: $*" >&2
}

# =============================================================================
# DEPENDENCY CHECKING
# =============================================================================

# Check Python version
# Usage: tw_check_python_version MAJOR.MINOR
# Example: tw_check_python_version 3.6
tw_check_python_version() {
    local required_version="$1"
    
    if ! command -v python3 >/dev/null 2>&1; then
        tw_error "python3 not found"
        echo "Install with: sudo apt install python3" >&2
        return 1
    fi
    
    local python_version
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    
    tw_debug "Python version: $python_version (required: >=$required_version)"
    
    # Compare versions
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= tuple(map(int, '$required_version'.split('.'))) else 1)"; then
        tw_error "Python $required_version or higher required (found $python_version)"
        return 1
    fi
    
    return 0
}

# Check Taskwarrior version
# Usage: tw_check_taskwarrior_version MAJOR.MINOR.PATCH
# Example: tw_check_taskwarrior_version 2.6.2
tw_check_taskwarrior_version() {
    local required_version="$1"
    
    if ! command -v task >/dev/null 2>&1; then
        tw_error "Taskwarrior not found"
        echo "Install with: tw --install-taskwarrior" >&2
        return 1
    fi
    
    local task_version
    task_version=$(task --version 2>&1 | head -1 | awk '{print $1}')
    
    tw_debug "Taskwarrior version: $task_version (required: >=$required_version)"
    
    # Simple version comparison (works for most cases)
    if [ "$(printf '%s\n' "$required_version" "$task_version" | sort -V | head -n1)" != "$required_version" ]; then
        tw_error "Taskwarrior $required_version or higher required (found $task_version)"
        return 1
    fi
    
    return 0
}

# Check if command exists
# Usage: tw_check_command COMMAND [INSTALL_HINT]
# Example: tw_check_command jq "sudo apt install jq"
tw_check_command() {
    local cmd="$1"
    local hint="${2:-Install $cmd and try again}"
    
    if ! command -v "$cmd" >/dev/null 2>&1; then
        tw_error "$cmd not found"
        echo "$hint" >&2
        return 1
    fi
    
    tw_debug "Found command: $cmd"
    return 0
}

# =============================================================================
# REPOSITORY MANAGEMENT
# =============================================================================

# Clone or update git repository
# Usage: tw_clone_or_update REPO_URL TARGET_DIR [BRANCH]
# Example: tw_clone_or_update "https://github.com/user/repo" "/path/to/dir" "main"
tw_clone_or_update() {
    local repo_url="$1"
    local target_dir="$2"
    local branch="${3:-}"
    
    tw_debug "Repository: $repo_url -> $target_dir"
    
    if [ -d "$target_dir/.git" ]; then
        tw_info "Updating existing repository..."
        cd "$target_dir" || return 1
        git pull || {
            tw_error "Failed to update repository"
            return 1
        }
        cd - >/dev/null || return 1
    else
        tw_info "Cloning repository..."
        
        # Create parent directory if needed
        local parent_dir
        parent_dir=$(dirname "$target_dir")
        mkdir -p "$parent_dir" || return 1
        
        # Clone
        if [ -n "$branch" ]; then
            git clone -b "$branch" "$repo_url" "$target_dir" || {
                tw_error "Failed to clone repository"
                return 1
            }
        else
            git clone "$repo_url" "$target_dir" || {
                tw_error "Failed to clone repository"
                return 1
            }
        fi
    fi
    
    return 0
}

# =============================================================================
# HOOK MANAGEMENT
# =============================================================================

# Create symlink for hook
# Usage: tw_symlink_hook SOURCE_PATH [LINK_NAME]
# Example: tw_symlink_hook "/path/to/on-add-test.py"
# Example: tw_symlink_hook "/path/to/src/hook.py" "on-add-custom.py"
tw_symlink_hook() {
    local source="$1"
    local link_name="${2:-$(basename "$source")}"
    
    # Ensure hooks directory exists
    mkdir -p "$HOOKS_DIR" || return 1
    
    local target="$HOOKS_DIR/$link_name"
    
    # Check if source exists
    if [ ! -f "$source" ]; then
        tw_error "Hook source not found: $source"
        return 1
    fi
    
    # Make source executable
    chmod +x "$source" || {
        tw_warn "Could not make hook executable: $source"
    }
    
    # Remove existing symlink/file if present
    if [ -e "$target" ] || [ -L "$target" ]; then
        tw_debug "Removing existing hook: $target"
        rm -f "$target"
    fi
    
    # Create symlink
    ln -s "$source" "$target" || {
        tw_error "Failed to create hook symlink: $target"
        return 1
    }
    
    tw_debug "Created hook symlink: $link_name"
    return 0
}

# Remove hook symlink
# Usage: tw_remove_hook HOOK_NAME
# Example: tw_remove_hook "on-add-test.py"
tw_remove_hook() {
    local hook_name="$1"
    local target="$HOOKS_DIR/$hook_name"
    
    if [ -L "$target" ]; then
        rm -f "$target" || {
            tw_warn "Could not remove hook: $target"
            return 1
        }
        tw_debug "Removed hook: $hook_name"
    elif [ -e "$target" ]; then
        tw_warn "Hook exists but is not a symlink: $target (not removing)"
        return 1
    fi
    
    return 0
}

# =============================================================================
# CONFIGURATION MANAGEMENT
# =============================================================================

# Add configuration to taskrc
# Usage: tw_add_config "KEY=VALUE"
# Example: tw_add_config "uda.myapp.type=string"
tw_add_config() {
    local config_line="$1"
    
    # Ensure taskrc exists
    touch "$TASKRC" || {
        tw_error "Cannot access taskrc: $TASKRC"
        return 1
    }
    
    # Extract key (everything before =)
    local key="${config_line%%=*}"
    
    # Check if config already exists
    if grep -q "^${key}=" "$TASKRC" 2>/dev/null; then
        tw_debug "Configuration already exists: $key (skipping)"
        return 0
    fi
    
    # Add configuration
    echo "$config_line" >> "$TASKRC" || {
        tw_error "Failed to add configuration: $config_line"
        return 1
    }
    
    tw_debug "Added configuration: $config_line"
    return 0
}

# Remove configuration from taskrc
# Usage: tw_remove_config "KEY_PREFIX"
# Example: tw_remove_config "uda.myapp"
tw_remove_config() {
    local key_prefix="$1"
    
    if [ ! -f "$TASKRC" ]; then
        return 0
    fi
    
    # Create backup
    cp "$TASKRC" "${TASKRC}.bak" || {
        tw_warn "Could not create backup of taskrc"
    }
    
    # Remove lines matching prefix
    sed -i "/^${key_prefix}/d" "$TASKRC" || {
        tw_error "Failed to remove configuration: $key_prefix"
        # Restore backup
        mv "${TASKRC}.bak" "$TASKRC"
        return 1
    }
    
    tw_debug "Removed configuration: $key_prefix.*"
    return 0
}

# Check if configuration exists
# Usage: tw_config_exists "KEY"
# Example: tw_config_exists "uda.myapp.type"
tw_config_exists() {
    local key="$1"
    
    if [ ! -f "$TASKRC" ]; then
        return 1
    fi
    
    grep -q "^${key}=" "$TASKRC" 2>/dev/null
}

# =============================================================================
# TESTING UTILITIES
# =============================================================================

# Test if hook exists and is executable
# Usage: tw_test_hook "HOOK_NAME"
# Example: tw_test_hook "on-add-test.py"
tw_test_hook() {
    local hook_name="$1"
    local hook_path="$HOOKS_DIR/$hook_name"
    
    if [ ! -e "$hook_path" ]; then
        tw_error "Hook not found: $hook_name"
        return 1
    fi
    
    if [ ! -x "$hook_path" ]; then
        tw_error "Hook not executable: $hook_name"
        return 1
    fi
    
    tw_debug "Hook OK: $hook_name"
    return 0
}

# Test if configuration value matches expected
# Usage: tw_test_config "KEY" "EXPECTED_VALUE"
# Example: tw_test_config "uda.myapp.type" "string"
tw_test_config() {
    local key="$1"
    local expected="$2"
    
    if [ ! -f "$TASKRC" ]; then
        tw_error "Taskrc not found: $TASKRC"
        return 1
    fi
    
    local actual
    actual=$(grep "^${key}=" "$TASKRC" | cut -d= -f2-)
    
    if [ "$actual" != "$expected" ]; then
        tw_error "Config mismatch for $key: expected '$expected', got '$actual'"
        return 1
    fi
    
    tw_debug "Config OK: $key=$actual"
    return 0
}

# Run a task command and check for success
# Usage: tw_test_cmd "TASK_COMMAND"
# Example: tw_test_cmd "task add test task"
tw_test_cmd() {
    local cmd="$1"
    
    tw_debug "Testing command: $cmd"
    
    if ! eval "$cmd" >/dev/null 2>&1; then
        tw_error "Command failed: $cmd"
        return 1
    fi
    
    return 0
}

# Clean up test data
# Usage: tw_test_cleanup
tw_test_cleanup() {
    tw_debug "Cleaning up test data..."
    
    # Remove test tasks (those with 'test' in description)
    task rc.confirmation=no '(/test/i or /TEST/i)' delete >/dev/null 2>&1 || true
    
    return 0
}

# Setup test environment
# Usage: tw_test_setup
tw_test_setup() {
    tw_debug "Setting up test environment..."
    
    # Ensure we're not using production data
    if [ "$TW_TEST_ENV" != "1" ]; then
        tw_warn "TW_TEST_ENV not set, are you sure you want to test with production data?"
        read -p "Continue? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi
    
    return 0
}

# =============================================================================
# WRAPPER MANAGEMENT
# =============================================================================

# Add app to wrapper stack in tw.config
# Usage: tw_add_to_wrapper_stack "APP_NAME"
# Example: tw_add_to_wrapper_stack "nicedates"
tw_add_to_wrapper_stack() {
    local app_name="$1"
    local config_file="${INSTALL_DIR}/tw.config"
    
    # Create config if doesn't exist
    if [ ! -f "$config_file" ]; then
        cat > "$config_file" <<EOF
[wrappers]
stack=$app_name
EOF
        tw_debug "Created tw.config with wrapper: $app_name"
        return 0
    fi
    
    # Check if already in stack
    if grep -q "stack=.*$app_name" "$config_file"; then
        tw_debug "Wrapper already in stack: $app_name"
        return 0
    fi
    
    # Add to stack
    # This is simplified - real implementation would parse INI properly
    tw_warn "Auto-add to wrapper stack not fully implemented"
    tw_info "Manually add '$app_name' to [wrappers] stack in $config_file"
    
    return 0
}

# =============================================================================
# FILE OPERATIONS
# =============================================================================

# Backup a file
# Usage: tw_backup_file "FILE_PATH"
# Example: tw_backup_file "$TASKRC"
tw_backup_file() {
    local file="$1"
    
    if [ ! -f "$file" ]; then
        return 0
    fi
    
    local backup="${file}.bak.$(date +%Y%m%d-%H%M%S)"
    cp "$file" "$backup" || {
        tw_error "Failed to create backup: $backup"
        return 1
    }
    
    tw_debug "Created backup: $backup"
    return 0
}

# =============================================================================
# INITIALIZATION
# =============================================================================

# Set default paths if not already set
: ${INSTALL_DIR:=~/.task}
: ${HOOKS_DIR:=${INSTALL_DIR}/hooks}
: ${TASKRC:=~/.taskrc}
: ${TW_DEBUG:=0}

# Ensure critical directories exist
mkdir -p "$INSTALL_DIR" 2>/dev/null || true
mkdir -p "$HOOKS_DIR" 2>/dev/null || true

tw_debug "tw-common.sh loaded (version $TW_COMMON_VERSION)"
tw_debug "INSTALL_DIR=$INSTALL_DIR"
tw_debug "HOOKS_DIR=$HOOKS_DIR"
tw_debug "TASKRC=$TASKRC"

# =============================================================================
# PROJECT DIRECTORY MANAGEMENT (added in v1.1.0)
# =============================================================================

# Get installation directory based on app type
# Usage: tw_get_install_dir TYPE SHORT_NAME
# Example: tw_get_install_dir hook recurrence
# Returns: ~/.task/hooks/recurrence
tw_get_install_dir() {
    local type="$1"
    local short_name="$2"
    
    case "$type" in
        hook)
            echo "${HOOKS_DIR}/${short_name}"
            ;;
        wrapper|utility)
            echo "${SCRIPTS_DIR}/${short_name}"
            ;;
        config)
            echo "${CONFIG_DIR}/${short_name}"
            ;;
        *)
            tw_error "Unknown app type: $type"
            return 1
            ;;
    esac
}

# Clone repository to proper location based on type
# Usage: tw_clone_to_project TYPE SHORT_NAME REPO_URL [BRANCH]
# Example: tw_clone_to_project hook recurrence "https://github.com/user/tw-recurrence_overhaul-hook"
tw_clone_to_project() {
    local type="$1"
    local short_name="$2"
    local repo_url="$3"
    local branch="${4:-}"
    
    local target_dir
    target_dir=$(tw_get_install_dir "$type" "$short_name") || return 1
    
    tw_debug "Cloning $short_name to $target_dir"
    
    tw_clone_or_update "$repo_url" "$target_dir" "$branch"
}

# =============================================================================
# UPDATED HOOK MANAGEMENT (with project subdirectories)
# =============================================================================

# Create symlink for hook (updated to handle project subdirectories)
# Usage: tw_symlink_hook PROJECT_DIR HOOK_FILE
# Example: tw_symlink_hook "${HOOKS_DIR}/recurrence" "on-add_recurrence.py"
# Creates: ~/.task/hooks/on-add_recurrence.py -> ~/.task/hooks/recurrence/on-add_recurrence.py
#
# NOTE: This is the NEW signature. Old code using tw_symlink_hook "path/to/file"
# should be updated to tw_symlink_hook "path/to/dir" "filename"
tw_symlink_hook() {
    local project_dir="$1"
    local hook_file="$2"
    
    local source="${project_dir}/${hook_file}"
    local target="${HOOKS_DIR}/${hook_file}"
    
    # Check if source exists
    if [ ! -f "$source" ]; then
        tw_error "Hook source not found: $source"
        return 1
    fi
    
    # Make source executable
    chmod +x "$source" || {
        tw_warn "Could not make hook executable: $source"
    }
    
    # Remove existing symlink/file if present
    if [ -e "$target" ] || [ -L "$target" ]; then
        tw_debug "Removing existing hook: $target"
        rm -f "$target"
    fi
    
    # Create symlink
    ln -s "$source" "$target" || {
        tw_error "Failed to create hook symlink: $target"
        return 1
    }
    
    tw_debug "Created hook symlink: $hook_file"
    return 0
}

# Remove hook symlink (updated for compatibility)
# Usage: tw_remove_hook HOOK_FILE
# Example: tw_remove_hook "on-add_recurrence.py"
tw_remove_hook() {
    local hook_file="$1"
    local target="${HOOKS_DIR}/${hook_file}"
    
    if [ -L "$target" ]; then
        rm -f "$target" || {
            tw_warn "Could not remove hook: $target"
            return 1
        }
        tw_debug "Removed hook: $hook_file"
    elif [ -e "$target" ]; then
        tw_warn "Hook exists but is not a symlink: $target (not removing)"
        return 1
    fi
    
    return 0
}

# =============================================================================
# WRAPPER/SCRIPT MANAGEMENT
# =============================================================================

# Create symlink for wrapper/script
# Usage: tw_symlink_wrapper PROJECT_DIR SCRIPT_FILE [LINK_NAME]
# Example: tw_symlink_wrapper "${SCRIPTS_DIR}/nicedates" "nicedates.py" "nicedates"
# Creates: ~/.task/scripts/nicedates -> ~/.task/scripts/nicedates/nicedates.py
tw_symlink_wrapper() {
    local project_dir="$1"
    local script_file="$2"
    local link_name="${3:-$(basename "$script_file")}"
    
    local source="${project_dir}/${script_file}"
    local target="${SCRIPTS_DIR}/${link_name}"
    
    # Check if source exists
    if [ ! -f "$source" ]; then
        tw_error "Script source not found: $source"
        return 1
    fi
    
    # Make source executable
    chmod +x "$source" || {
        tw_warn "Could not make script executable: $source"
    }
    
    # Remove existing symlink/file if present
    if [ -e "$target" ] || [ -L "$target" ]; then
        tw_debug "Removing existing script: $target"
        rm -f "$target"
    fi
    
    # Create symlink
    ln -s "$source" "$target" || {
        tw_error "Failed to create script symlink: $target"
        return 1
    }
    
    tw_debug "Created script symlink: $link_name"
    return 0
}

# Remove wrapper symlink
# Usage: tw_remove_wrapper LINK_NAME
# Example: tw_remove_wrapper "nicedates"
tw_remove_wrapper() {
    local link_name="$1"
    local target="${SCRIPTS_DIR}/${link_name}"
    
    if [ -L "$target" ]; then
        rm -f "$target" || {
            tw_warn "Could not remove script: $target"
            return 1
        }
        tw_debug "Removed script: $link_name"
    elif [ -e "$target" ]; then
        tw_warn "Script exists but is not a symlink: $target (not removing)"
        return 1
    fi
    
    return 0
}

# =============================================================================
# INITIALIZATION - Set default paths and create directories
# =============================================================================

# Set default paths if not already set
: ${INSTALL_DIR:=~/.task}
: ${HOOKS_DIR:=${INSTALL_DIR}/hooks}
: ${SCRIPTS_DIR:=${INSTALL_DIR}/scripts}
: ${CONFIG_DIR:=${INSTALL_DIR}/config}
: ${LOGS_DIR:=${INSTALL_DIR}/logs}
: ${TASKRC:=~/.taskrc}
: ${TW_DEBUG:=0}

# Ensure critical directories exist
mkdir -p "$HOOKS_DIR" 2>/dev/null || true
mkdir -p "$SCRIPTS_DIR" 2>/dev/null || true
mkdir -p "$CONFIG_DIR" 2>/dev/null || true
mkdir -p "$LOGS_DIR" 2>/dev/null || true

tw_debug "tw-common.sh v${TW_COMMON_VERSION} loaded"
tw_debug "INSTALL_DIR=$INSTALL_DIR"
tw_debug "HOOKS_DIR=$HOOKS_DIR"
tw_debug "SCRIPTS_DIR=$SCRIPTS_DIR"
tw_debug "CONFIG_DIR=$CONFIG_DIR"
tw_debug "LOGS_DIR=$LOGS_DIR"
