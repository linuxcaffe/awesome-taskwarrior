#!/usr/bin/env bash
# tw-runtime.sh - Shared runtime utilities for Taskwarrior Bash scripts
# Version: 0.1.0
#
# Installation:
#   Each extension's .install script runs:
#     tw_install_to scripts tw-runtime.sh   # idempotent
#
# Usage in scripts:
#   source "${HOME}/.task/scripts/tw-runtime.sh" \
#       || { echo "tw-runtime.sh not found — re-run installer" >&2; exit 1; }

# ============================================================================
# Messaging
# ============================================================================

die() {
    echo "ERROR: $*" >&2
    exit 1
}

msg() {
    echo "$*"
}

warn() {
    echo "WARNING: $*" >&2
}

# ============================================================================
# Task subprocess wrapper
# rc.hooks=off prevents cascading hook invocations — the key performance fix
# from the annn work (each bare `task _get` was firing all on-exit hooks).
# ============================================================================

task_get() {
    # Read a single task DOM attribute via 'task _get'.
    # Usage: task_get <attr>   e.g. task_get "42.description"
    task rc.hooks=off rc.verbose=nothing _get "$@" 2>/dev/null
}

# ============================================================================
# Config reading
# Reads key=value pairs from a .rc config file.
# Handles inline comments (# ...) and surrounding whitespace.
# Usage: get_config <file> <key> [default]
# ============================================================================

get_config() {
    local file="$1" key="$2" default="${3:-}"
    local val
    val=$(grep -E "^[[:space:]]*${key}[[:space:]]*=" "$file" 2>/dev/null \
        | head -1 | cut -d= -f2- \
        | sed 's/^[[:space:]]*//; s/[[:space:]]*#.*$//; s/[[:space:]]*$//')
    echo "${val:-$default}"
}

# ============================================================================
# Validators
# ============================================================================

is_integer() {
    # Returns 0 (true) if $1 is a plain non-negative integer.
    [[ "$1" =~ ^[0-9]+$ ]]
}

is_uuid() {
    # Returns 0 (true) if $1 matches Taskwarrior UUID format.
    [[ "$1" =~ ^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$ ]]
}

sanitize_for_filename() {
    # Lowercase, replace non-alphanumeric with hyphens, collapse runs, trim ends.
    # Usage: sanitize_for_filename "My Task Description"
    echo "$1" | tr '[:upper:]' '[:lower:]' \
              | sed 's/[^a-z0-9]/-/g; s/--*/-/g; s/^-//; s/-$//' \
              | cut -c1-40
}
