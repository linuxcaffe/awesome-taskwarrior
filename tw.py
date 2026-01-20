#!/usr/bin/env python3
"""
tw.py - Universal wrapper for Taskwarrior with extended functionality

Version: 0.1.5
"""

import sys
import os
import subprocess

# Immediate output to confirm script is running
print("SCRIPT STARTED", file=sys.stderr)

VERSION = "0.1.5"

# MANUAL DEBUG SWITCH - Set to True to enable debug output
DEBUG = True

def debug_print(msg):
    """Print debug message if DEBUG is enabled."""
    if DEBUG:
        print(f"DEBUG: {msg}", file=sys.stderr)

def find_task_binary():
    """Locate the task binary in PATH."""
    # Get PATH and split it
    path_env = os.environ.get('PATH', '')
    paths = path_env.split(os.pathsep)
    
    for path_dir in paths:
        task_path = os.path.join(path_dir, 'task')
        if os.path.isfile(task_path) and os.access(task_path, os.X_OK):
            return task_path
    
    return None

def handle_list():
    """Handle --list flag: show installable projects."""
    debug_print("In handle_list()")
    print("awesome-taskwarrior projects with install scripts:")
    print()
    print("(none available yet - watch this space!)")
    print()
    sys.exit(0)

def handle_version(task_bin):
    """Handle --version flag: show both tw.py and taskwarrior versions."""
    debug_print("In handle_version()")
    print(f"tw.py version {VERSION}")
    
    # Call task --version to get taskwarrior version
    try:
        result = subprocess.run([task_bin, '--version'], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        print(result.stdout.rstrip())
    except subprocess.CalledProcessError as e:
        print(f"Error getting task version: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
    
    sys.exit(0)

def main():
    """Main entry point for tw.py wrapper."""
    
    debug_print(f"sys.argv = {sys.argv}")
    debug_print(f"len(sys.argv) = {len(sys.argv)}")
    
    # Find task binary first (we need it for everything)
    task_bin = find_task_binary()
    if task_bin is None:
        print("Error: 'task' binary not found in PATH", file=sys.stderr)
        print("Please ensure Taskwarrior is installed and in your PATH", file=sys.stderr)
        sys.exit(1)
    
    debug_print(f"task_bin = {task_bin}")
    
    # Check if we have any arguments
    if len(sys.argv) > 1:
        debug_print(f"checking argv[1] = '{sys.argv[1]}'")
        
        # Handle our long-format flags that DON'T pass through
        if sys.argv[1] == '--list':
            debug_print("matched --list")
            handle_list()
        
        # Handle --version (the only flag that passes through to task)
        if sys.argv[1] == '--version':
            debug_print("matched --version")
            handle_version(task_bin)
    
    debug_print("falling through to pass-through")
    
    # All other cases: pass through to task
    # Build the argv list for execv: ['task', arg1, arg2, ...]
    task_argv = ['task'] + sys.argv[1:]
    
    debug_print(f"executing with task_argv = {task_argv}")
    
    # Execute task with all arguments
    try:
        os.execv(task_bin, task_argv)
    except OSError as e:
        print(f"Error executing task: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
