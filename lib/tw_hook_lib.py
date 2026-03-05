#!/usr/bin/env python3
"""
tw_hook_lib.py - Shared utilities for Taskwarrior hooks and scripts
Version: 0.1.0

Usage (dev time, from project directory):
    import sys, os
    sys.path.insert(0, os.path.expanduser('~/dev/awesome-taskwarrior/lib'))
    from tw_hook_lib import task_export, read_hook_input, write_hook_output

Usage (installed, via make-awesome.py inline injection):
    Functions are inlined directly into the hook file at build time.

TW_TIMING and TW_DEBUG are NOT handled here — make-awesome.py injects those.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional, Union


# ============================================================================
# Task subprocess wrappers
# rc.hooks=off rc.confirmation=off rc.verbose=nothing baked in (the fix from
# the annn performance work — prevents cascading hook invocations).
# ============================================================================

_TASK_BASE = ['task', 'rc.hooks=off', 'rc.confirmation=off', 'rc.verbose=nothing']


def task_run(*args: str, extra_rc: Optional[list] = None) -> subprocess.CompletedProcess:
    """Run a task command with safe defaults baked in.

    Args:
        *args: task arguments (filter, subcommand, modifications, etc.)
        extra_rc: additional rc overrides, e.g. ['rc.context=none']

    Returns:
        CompletedProcess (check=False — caller decides how to handle errors)
    """
    cmd = _TASK_BASE[:]
    if extra_rc:
        cmd.extend(extra_rc)
    cmd.extend(args)
    return subprocess.run(cmd, capture_output=True, text=True)


def task_export(filter_args: list) -> list:
    """Export tasks matching filter as a list of dicts.

    Args:
        filter_args: list of filter tokens, e.g. ['status:pending', '+mytag']

    Returns:
        list of task dicts (empty list on error or no results)
    """
    cmd = _TASK_BASE[:] + ['rc.context=none'] + list(filter_args) + ['export']
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        return []
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return []


def task_import(tasks: list) -> bool:
    """Import a list of task dicts into Taskwarrior.

    Args:
        tasks: list of task dicts (must have at least 'uuid' and 'description')

    Returns:
        True on success, False on error
    """
    cmd = ['task', 'rc.hooks=off', 'rc.confirmation=off', 'import', '-']
    data = json.dumps(tasks)
    result = subprocess.run(cmd, input=data, capture_output=True, text=True)
    return result.returncode == 0


def task_get(attr: str) -> str:
    """Read a single task DOM attribute via 'task _get'.

    rc.hooks=off prevents cascading hook invocations (the key performance fix
    from the annn work — each bare `task _get` was firing all on-exit hooks).

    Args:
        attr: DOM path, e.g. '42.description', '<uuid>.status', 'system.version'

    Returns:
        String value, or '' if not found / error
    """
    result = subprocess.run(
        ['task', 'rc.hooks=off', 'rc.verbose=nothing', '_get', attr],
        capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else ''


# ============================================================================
# Hook I/O
# Replaces copy-pasted json.loads(sys.stdin.read()) + print(json.dumps(...))
# ============================================================================

def read_hook_input() -> Union[tuple, tuple]:
    """Read hook input from stdin.

    on-add hooks receive one JSON line (new task).
    on-modify hooks receive two JSON lines (original task, then modified task).

    Returns:
        (new_task,)             for on-add
        (original, modified)    for on-modify
    """
    lines = []
    for line in sys.stdin:
        line = line.strip()
        if line:
            lines.append(json.loads(line))
        if len(lines) == 2:
            break

    if len(lines) == 2:
        return (lines[0], lines[1])
    elif len(lines) == 1:
        return (lines[0],)
    else:
        sys.exit(0)  # no input; nothing to do


def write_hook_output(task: dict, feedback: str = '') -> None:
    """Write hook output to stdout.

    Taskwarrior expects a JSON line (the task) followed by optional feedback
    lines. This handles the required format.

    Args:
        task:     task dict to output
        feedback: optional user-visible message (printed after the JSON)
    """
    print(json.dumps(task))
    if feedback:
        print(feedback)


# ============================================================================
# Config reading
# Reads key=value pairs from a .rc config file.
# Handles inline comments (# ...) and surrounding whitespace.
# ============================================================================

def get_config(config_file: Union[str, Path], key: str, default: str = '') -> str:
    """Read a key=value pair from a Taskwarrior-style .rc config file.

    Handles:
      key=value
      key = value   (with spaces)
      key=value  # comment

    Args:
        config_file: path to the .rc file
        key:         key to look up
        default:     returned if key not found or file doesn't exist

    Returns:
        Value string (stripped of whitespace and inline comments), or default.
    """
    path = Path(config_file)
    if not path.exists():
        return default

    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            k, _, v = line.partition('=')
            if k.strip() == key:
                # Strip inline comment
                v = v.split('#')[0].strip()
                return v if v else default

    return default


# ============================================================================
# Description parsing
# Verb/noun extraction from task descriptions.
# First word may be a verb (pay, buy, invoice...); subsequent capitalised
# words form the noun/payee; remainder is the comment/context.
# ============================================================================

def parse_verb_noun(description: str, verbs: set) -> tuple:
    """Split a task description into (verb, noun, remainder).

    Strips a leading verb (if in the provided set), then finds the first run
    of consecutive capitalised words as the noun. Everything after is remainder.

    Args:
        description: raw task description string
        verbs:       set of lowercase trigger verbs, e.g. {'pay', 'buy'}

    Returns:
        (verb, noun, remainder) — any part may be '' if not found.

    Examples:
        'pay Koodo Mobile cel bill', {'pay'}  → ('pay', 'Koodo Mobile', 'cel bill')
        'buy groceries',             {'buy'}  → ('buy', 'groceries', '')
        'Swiss Chalet is open',      set()    → ('', 'Swiss Chalet', 'is open')
        'just do it',                set()    → ('', '', 'just do it')
        '',                          set()    → ('', '', '')
    """
    words = description.strip().split()
    if not words:
        return ('', '', '')

    verb = ''
    rest = words
    if words[0].lower() in verbs:
        verb = words[0]
        rest = words[1:]

    # First consecutive capitalised words → noun
    noun_words = []
    i = 0
    while i < len(rest) and rest[i][0].isupper():
        noun_words.append(rest[i])
        i += 1

    noun      = ' '.join(noun_words)
    remainder = ' '.join(rest[i:])
    return (verb, noun, remainder)


# ============================================================================
# Status reporting
# Prints a standard status block (the --status pattern from annn/tw scripts).
# ============================================================================

def print_status(name: str, version: str, items: dict) -> None:
    """Print a formatted status block to stdout.

    Args:
        name:    script/tool name
        version: version string
        items:   dict of label -> value pairs to display

    Example output:
        [tw-daily-email] v0.1.0
          config:  ~/.task/config/daily-email.rc
          email:   user@example.com
    """
    print(f'[{name}] v{version}')
    for label, value in items.items():
        print(f'  {label:<12} {value}')
