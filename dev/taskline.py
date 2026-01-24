#!/usr/bin/env python3
import subprocess
import shlex
import readline
import os

# ---- history ----
HISTFILE = os.path.expanduser("~/.taskline_history")
try:
    readline.read_history_file(HISTFILE)
except FileNotFoundError:
    pass

def save_history():
    readline.write_history_file(HISTFILE)

# ---- state ----
HEAD = ["add"]
PREFIX_STACK = []

TEMPLATES = {
    "meeting": ["proj:meetings", "+work", "pri:M"],
    "bug": ["proj:bugs", "+work", "pri:H"],
}

# ---- helpers ----
def format_prompt():
    parts = ["task"] + HEAD + PREFIX_STACK
    return " ".join(parts) + " > "

def run_task(args):
    subprocess.run(["task"] + args, check=False)

def get_context(name):
    # activate context
    subprocess.run(["task", "context", name], check=False)
    # fetch its definition
    p = subprocess.run(
        ["task", "_get", f"rc.context.{name}"],
        capture_output=True,
        text=True,
    )
    return shlex.split(p.stdout.strip())

def show_help():
    print("""
:head <args...>        set command head (default: add)
:push <mods...>        push persistent modifiers
:pop                  pop last modifier
:clear                clear all modifiers
:context <name>       apply task context
:tpl <name>           apply a template
:show                 show current state
:reset                reset head and modifiers
:q | :quit | :exit    exit
""".strip())

# ---- main ----
def main():
    global HEAD, PREFIX_STACK

    try:
        while True:
            line = input(format_prompt()).strip()
            if not line:
                continue

            if line.startswith(":"):
                cmd = shlex.split(line[1:])
                if not cmd:
                    continue

                if cmd[0] in ("q", "quit", "exit"):
                    break

                elif cmd[0] == "help":
                    show_help()

                elif cmd[0] == "head":
                    HEAD = cmd[1:] or ["add"]

                elif cmd[0] == "push":
                    PREFIX_STACK.extend(cmd[1:])

                elif cmd[0] == "pop":
                    if PREFIX_STACK:
                        PREFIX_STACK.pop()

                elif cmd[0] == "clear":
                    PREFIX_STACK.clear()

                elif cmd[0] == "reset":
                    HEAD = ["add"]
                    PREFIX_STACK.clear()

                elif cmd[0] == "show":
                    print("HEAD:", HEAD)
                    print("PREFIX:", PREFIX_STACK)

                elif cmd[0] == "context" and len(cmd) > 1:
                    PREFIX_STACK.extend(get_context(cmd[1]))

                elif cmd[0] == "tpl" and len(cmd) > 1:
                    PREFIX_STACK.extend(TEMPLATES.get(cmd[1], []))

                else:
                    print(f"Unknown command: {cmd[0]}")

                continue

            args = HEAD + PREFIX_STACK + shlex.split(line)
            run_task(args)

    except (EOFError, KeyboardInterrupt):
        print()
    finally:
        save_history()

if __name__ == "__main__":
    main()

