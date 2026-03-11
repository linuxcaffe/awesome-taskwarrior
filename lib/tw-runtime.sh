#!/usr/bin/env bash
# tw-runtime.sh - Shared runtime utilities for Taskwarrior Bash scripts
# Version: 0.2.0
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
# Verbosity profiles
# Always set rc.verbose= explicitly — never rely on the user's default.
# The 'override' token (announces rc.X=Y overrides) belongs only in
# interactive use; exclude it from all script/hook calls.
#
#   VERBOSE_NOTHING  — hooks and silent mutations
#   VERBOSE_AFFECTED — mutations where "N tasks affected" is useful
#   VERBOSE_REPORT   — report display: headers + spacing, no noise
# ============================================================================

VERBOSE_NOTHING='nothing'
VERBOSE_AFFECTED='affected'
VERBOSE_REPORT='label,blank'

# Path to the cmx stale marker.  Any app that modifies a context definition
# should call cmx_mark_stale so tw rebuilds the combined filter on next run.
CMX_STALE_MARKER="${HOME}/.task/config/.cmx_stale"

cmx_mark_stale() {
    # Signal tw to rebuild the cmx combined filter.
    # Call this after writing any context.X.read / context.X.write definition.
    touch "${CMX_STALE_MARKER}" 2>/dev/null || true
}


# ============================================================================
# Task subprocess wrappers
# rc.hooks=off prevents cascading hook invocations — the key performance fix
# from the annn work (each bare `task _get` was firing all on-exit hooks).
# ============================================================================

task_run() {
    # Safe task wrapper: hooks off, confirmation off, verbose nothing.
    # Usage: task_run [filter] subcommand [mods]
    # For report display use: task_run rc.verbose="$VERBOSE_REPORT" ...
    task rc.hooks=off rc.confirmation=off rc.verbose=nothing "$@"
}

task_get() {
    # Read a single task DOM attribute via 'task _get'.
    # Usage: task_get <attr>   e.g. task_get "42.description"
    task rc.hooks=off rc.verbose=nothing _get "$@" 2>/dev/null
}


# ============================================================================
# on-exit hook helper
# on-exit hooks receive the full task command as 'command:<verb>' in $@.
# ============================================================================

get_tw_command() {
    # Extract the command verb from on-exit hook arguments.
    # Usage: cmd=$(get_tw_command "$@")
    # Returns e.g. "start", "stop", "done", "modify", ""
    local arg
    for arg in "$@"; do
        if [[ "${arg:0:8}" == "command:" ]]; then
            echo "${arg:8}"
            return
        fi
    done
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


# ============================================================================
# Interactive terminal helpers (for scripts with menus or keypresses)
# ============================================================================

# _SAVED_STTY: captured at source time so getch() can always restore cleanly.
_SAVED_STTY="$(stty -g 2>/dev/null)"

getch() {
    # Read a single keypress from /dev/tty without echoing it.
    # Stores result in global _GETCH_KEY.
    # Returns 0 always (safe to use in conditions).
    # Handles Enter variants (empty, \r, \n) uniformly — all stored as ''.
    #
    # Usage:
    #   getch
    #   case "$_GETCH_KEY" in
    #     '')  : enter ;;
    #     'q') : quit ;;
    #   esac
    local _raw_key
    stty raw -echo </dev/tty
    _raw_key=$(dd bs=1 count=1 2>/dev/null </dev/tty)
    stty "$_SAVED_STTY" </dev/tty
    # Normalise Enter variants to empty string
    case "$_raw_key" in
        $'\r'|$'\n') _GETCH_KEY='' ;;
        *) _GETCH_KEY="$_raw_key" ;;
    esac
    return 0
}

restore_terminal() {
    # Restore terminal to the state captured at source time.
    # Call in EXIT trap or after any raw-mode block.
    [[ -n "$_SAVED_STTY" ]] && stty "$_SAVED_STTY" </dev/tty 2>/dev/null || true
}
