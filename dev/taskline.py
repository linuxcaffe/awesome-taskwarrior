#!/usr/bin/env python3
"""
taskline.py - Interactive shell for Taskwarrior with persistent modifiers

Standalone version: prompt shows "task", can be run directly
For tw integration: will show "tw" prompt instead
"""
import subprocess
import shlex
import readline
import os
import sys

# ---- configuration ----
# Can be overridden for integration (e.g., SHELL_NAME = "tw")
SHELL_NAME = "task"

# ---- history ----
HISTFILE = os.path.expanduser("~/.taskline_history")
try:
    readline.read_history_file(HISTFILE)
except FileNotFoundError:
    pass

def save_history():
    readline.write_history_file(HISTFILE)

# ---- state ----
HEAD = []  # Default: no command
PREFIX_STACK = []

TEMPLATES = {
    "meeting": ["proj:meetings", "+work", "pri:M"],
    "bug": ["proj:bugs", "+work", "pri:H"],
}

# ---- helpers ----
def format_prompt():
    """Build prompt showing current state"""
    if HEAD:
        parts = [SHELL_NAME] + HEAD + PREFIX_STACK
    else:
        if PREFIX_STACK:
            parts = [SHELL_NAME] + PREFIX_STACK
        else:
            parts = [SHELL_NAME]
    return " ".join(parts) + "> "

def run_task(args):
    """Execute task command with full passthrough of stdout/stderr"""
    # check=False allows task to return non-zero without raising exception
    # No capture_output means stdout/stderr pass directly to terminal
    subprocess.run(["task"] + args, check=False)

def get_context(name):
    """Activate context and return its filter definition"""
    # Activate the context
    subprocess.run(["task", "context", name], check=False)
    # Fetch its definition
    p = subprocess.run(
        ["task", "_get", f"rc.context.{name}"],
        capture_output=True,
        text=True,
    )
    return shlex.split(p.stdout.strip())

def show_help(detailed=False):
    """Show shell help"""
    if detailed:
        # Show detailed help
        print("""
Interactive Shell (taskline.py)
================================

The interactive shell provides a stateful environment for running Taskwarrior
commands with persistent modifiers and command heads.

Starting the Shell:
  ./taskline.py                 Start with empty state
  Or configure SHELL_NAME variable for custom prompt

Shell Commands:
  :head <cmd>        Set command head (e.g., :head add, :head modify)
  :head              Clear command head (return to base prompt)
  :push <mods...>    Add persistent modifiers (e.g., :push +work proj:foo)
  :pop               Remove last modifier from stack
  :clear             Clear all modifiers
  :reset             Clear both head and modifiers
  :context <n>    Apply Taskwarrior context filters to modifier stack
  :tpl <n>        Apply a template (predefined modifier sets)
  :show              Display current HEAD and PREFIX_STACK state
  :help              Show this quick reference
  :help shell        Show detailed shell documentation
  :q, :quit, :exit   Exit shell

How it Works:
  Every command you type is prepended with HEAD + PREFIX_STACK
  Empty input (just pressing Enter) runs the default report
  
  Example session:
    task> :push +work proj:meetings
    task +work proj:meetings> :head add
    task add +work proj:meetings> Schedule standup for Friday
    # Executes: task add +work proj:meetings Schedule standup for Friday
    
    task add +work proj:meetings> :head
    task +work proj:meetings> list
    # Executes: task +work proj:meetings list
    
    task +work proj:meetings> 
    # Executes: task +work proj:meetings (default report)
    
    task +work proj:meetings> :pop
    task +work> 5 modify +urgent
    # Executes: task +work 5 modify +urgent

Templates:
  Built-in templates provide quick modifier sets:
  - meeting: proj:meetings +work pri:M
  - bug: proj:bugs +work pri:H
  
  Usage: :tpl meeting

History:
  Command history is saved to ~/.taskline_history
  Use arrow keys to navigate previous commands
""")
    else:
        # Show quick reference
        print("""
Commands:
  :head <args...>       set command head (e.g., :head add, :head modify)
  :head                 clear command head (return to base prompt)
  :push <mods...>       push persistent modifiers onto stack
  :pop                  pop last modifier from stack
  :clear                clear all modifiers from stack
  :context <n>       apply task context filters to stack
  :tpl <n>           apply a template to stack
  :show                 show current HEAD and PREFIX_STACK state
  :reset                reset both head and modifiers to empty
  :help                 show this quick reference
  :help shell           show detailed shell documentation
  :q | :quit | :exit    exit shell

Examples:
  :push +work proj:meetings
  :head add
  Schedule the standup
  # Runs: task add +work proj:meetings Schedule the standup

  :head
  list
  # Runs: task +work proj:meetings list
  
  (press Enter on empty line)
  # Runs: task +work proj:meetings (default report)
""".strip())

# ---- main ----
def main():
    global HEAD, PREFIX_STACK

    try:
        while True:
            line = input(format_prompt()).strip()
            
            # Empty input: run default report with current state
            if not line:
                args = HEAD + PREFIX_STACK
                if args:  # Only run if we have some state
                    run_task(args)
                else:  # Completely empty - run bare 'task'
                    run_task([])
                continue

            # Handle meta-commands
            if line.startswith(":"):
                cmd = shlex.split(line[1:])
                if not cmd:
                    continue

                if cmd[0] in ("q", "quit", "exit"):
                    break

                elif cmd[0] == "help":
                    # :help shell shows detailed help, :help shows quick reference
                    detailed = len(cmd) > 1 and cmd[1] == "shell"
                    show_help(detailed=detailed)

                elif cmd[0] == "head":
                    # :head with no args clears HEAD to []
                    HEAD = cmd[1:] if len(cmd) > 1 else []

                elif cmd[0] == "push":
                    PREFIX_STACK.extend(cmd[1:])

                elif cmd[0] == "pop":
                    if PREFIX_STACK:
                        PREFIX_STACK.pop()
                    else:
                        print("PREFIX_STACK is empty")

                elif cmd[0] == "clear":
                    PREFIX_STACK.clear()

                elif cmd[0] == "reset":
                    HEAD = []
                    PREFIX_STACK.clear()

                elif cmd[0] == "show":
                    print("HEAD:", HEAD if HEAD else "(empty)")
                    print("PREFIX_STACK:", PREFIX_STACK if PREFIX_STACK else "(empty)")

                elif cmd[0] == "context":
                    if len(cmd) > 1:
                        context_filters = get_context(cmd[1])
                        PREFIX_STACK.extend(context_filters)
                    else:
                        print("Usage: :context <n>")

                elif cmd[0] == "tpl":
                    if len(cmd) > 1:
                        template = TEMPLATES.get(cmd[1])
                        if template:
                            PREFIX_STACK.extend(template)
                        else:
                            print(f"Unknown template: {cmd[1]}")
                            print(f"Available templates: {', '.join(TEMPLATES.keys())}")
                    else:
                        print("Usage: :tpl <n>")
                        print(f"Available templates: {', '.join(TEMPLATES.keys())}")

                else:
                    print(f"Unknown command: {cmd[0]}")
                    print("Type :help for available commands")

                continue

            # Build and execute task command
            # HEAD + PREFIX_STACK are always prepended to user input
            args = HEAD + PREFIX_STACK + shlex.split(line)
            run_task(args)

    except (EOFError, KeyboardInterrupt):
        print()
    finally:
        save_history()

if __name__ == "__main__":
    main()
