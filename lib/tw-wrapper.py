#!/usr/bin/env python3
"""
tw-wrapper.py - Python library for awesome-taskwarrior wrapper applications

This library provides utilities for creating wrapper applications that
integrate with tw.py's wrapper chain system.

Usage:
    from tw_wrapper import TaskWrapper, main

    class MyWrapper(TaskWrapper):
        def process_args(self, args):
            # Modify arguments as needed
            return modified_args

    if __name__ == '__main__':
        main(MyWrapper)
"""

import os
import sys
import subprocess
import shlex
from typing import List, Optional

__version__ = "1.0.0"


class TaskWrapper:
    """
    Base class for Taskwarrior wrapper applications.
    
    Subclass this and override process_args() to create a custom wrapper.
    """
    
    def __init__(self):
        self.debug = os.environ.get('TW_DEBUG', '0') == '1'
        self.next_wrapper = os.environ.get('TW_NEXT_WRAPPER', 'task')
        
    def debug_print(self, msg: str) -> None:
        """Print debug message if debug mode is enabled."""
        if self.debug:
            print(f"DEBUG [{self.__class__.__name__}]: {msg}", file=sys.stderr)
    
    def process_args(self, args: List[str]) -> List[str]:
        """
        Process and potentially modify arguments before passing to next wrapper.
        
        Override this method in your wrapper subclass.
        
        Args:
            args: List of command-line arguments (excluding program name)
            
        Returns:
            Modified list of arguments
        """
        # Default: pass through unchanged
        return args
    
    def should_bypass(self, args: List[str]) -> bool:
        """
        Check if wrapper should be bypassed for this command.
        
        Override this to bypass wrapper for certain commands.
        
        Args:
            args: List of command-line arguments
            
        Returns:
            True if wrapper should be bypassed
        """
        # Bypass for --help and --version by default
        if args and args[0] in ('--help', '-h', '--version', '-V'):
            return True
        return False
    
    def execute(self, args: List[str]) -> int:
        """
        Execute the next wrapper/task in the chain.
        
        Args:
            args: List of arguments to pass
            
        Returns:
            Exit code from executed command
        """
        cmd = [self.next_wrapper] + args
        
        self.debug_print(f"Executing: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd)
            return result.returncode
        except FileNotFoundError:
            print(f"Error: Command not found: {self.next_wrapper}", file=sys.stderr)
            return 127
        except KeyboardInterrupt:
            return 130
        except Exception as e:
            print(f"Error executing {self.next_wrapper}: {e}", file=sys.stderr)
            return 1
    
    def run(self, args: List[str]) -> int:
        """
        Main entry point for wrapper.
        
        Args:
            args: Command-line arguments (excluding program name)
            
        Returns:
            Exit code
        """
        self.debug_print(f"Input args: {args}")
        
        # Check if we should bypass
        if self.should_bypass(args):
            self.debug_print("Bypassing wrapper")
            return self.execute(args)
        
        # Process arguments
        try:
            processed_args = self.process_args(args)
        except Exception as e:
            print(f"Error processing arguments: {e}", file=sys.stderr)
            return 1
        
        self.debug_print(f"Processed args: {processed_args}")
        
        # Execute
        return self.execute(processed_args)


def main(wrapper_class: type) -> None:
    """
    Main entry point for wrapper applications.
    
    Args:
        wrapper_class: Subclass of TaskWrapper to instantiate and run
    """
    wrapper = wrapper_class()
    args = sys.argv[1:]
    exit_code = wrapper.run(args)
    sys.exit(exit_code)


# Utility functions for common wrapper patterns

def expand_date_shortcuts(args: List[str], shortcuts: dict) -> List[str]:
    """
    Expand date shortcuts in arguments.
    
    Args:
        args: List of arguments
        shortcuts: Dictionary mapping shortcuts to expansions
                  Example: {'tom': 'tomorrow', 'eow': 'eow'}
    
    Returns:
        Arguments with shortcuts expanded
    """
    result = []
    for arg in args:
        # Check if argument is a date specification
        if ':' in arg:
            key, value = arg.split(':', 1)
            if value in shortcuts:
                result.append(f"{key}:{shortcuts[value]}")
                continue
        result.append(arg)
    return result


def parse_compound_filter(filter_str: str) -> List[str]:
    """
    Parse compound filter expressions.
    
    Args:
        filter_str: Filter expression (e.g., "project:work and +urgent")
        
    Returns:
        List of individual filter components
    """
    # Simple implementation - split on 'and' and 'or'
    parts = []
    current = []
    
    for token in shlex.split(filter_str):
        if token.lower() in ('and', 'or'):
            if current:
                parts.append(' '.join(current))
                current = []
        else:
            current.append(token)
    
    if current:
        parts.append(' '.join(current))
    
    return parts


def inject_context(args: List[str], context: str) -> List[str]:
    """
    Inject a context into task arguments.
    
    Args:
        args: List of arguments
        context: Context name to inject
        
    Returns:
        Arguments with context injected
    """
    # Add rc.context=<context> at the beginning
    return [f'rc.context={context}'] + args


def add_default_tags(args: List[str], tags: List[str]) -> List[str]:
    """
    Add default tags to 'add' commands.
    
    Args:
        args: List of arguments
        tags: List of tags to add (without +)
        
    Returns:
        Arguments with tags added if 'add' command detected
    """
    if not args or args[0] != 'add':
        return args
    
    # Add tags after 'add' command
    result = [args[0]]
    result.extend([f'+{tag}' for tag in tags])
    result.extend(args[1:])
    
    return result


class DateParsingWrapper(TaskWrapper):
    """
    Example wrapper that demonstrates date parsing.
    """
    
    def __init__(self):
        super().__init__()
        self.date_shortcuts = {
            'tom': 'tomorrow',
            'tod': 'today',
            'eow': 'eow',
            'eom': 'eom',
            'eoy': 'eoy',
        }
    
    def process_args(self, args: List[str]) -> List[str]:
        return expand_date_shortcuts(args, self.date_shortcuts)


class ContextWrapper(TaskWrapper):
    """
    Example wrapper that automatically sets context based on project.
    """
    
    def __init__(self):
        super().__init__()
        self.project_contexts = {
            'work': 'work',
            'home': 'personal',
            'errands': 'personal',
        }
    
    def process_args(self, args: List[str]) -> List[str]:
        # Look for project specification
        for arg in args:
            if arg.startswith('project:'):
                project = arg.split(':', 1)[1]
                if project in self.project_contexts:
                    context = self.project_contexts[project]
                    return inject_context(args, context)
        return args


# Example usage
if __name__ == '__main__':
    # This is just for testing/demonstration
    print(f"tw-wrapper.py library version {__version__}")
    print("This is a library module. Import it in your wrapper application.")
    print()
    print("Example:")
    print("  from tw_wrapper import TaskWrapper, main")
    print()
    print("  class MyWrapper(TaskWrapper):")
    print("      def process_args(self, args):")
    print("          # Your logic here")
    print("          return args")
    print()
    print("  if __name__ == '__main__':")
    print("      main(MyWrapper)")
