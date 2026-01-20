# awesome-taskwarrior Developer Guide

## Overview

awesome-taskwarrior is a curated collection of Taskwarrior extensions with a unified installation and management system. At its heart is `tw.py`, a universal wrapper that acts as both a transparent pass-through to Taskwarrior and a comprehensive package manager for Taskwarrior-related projects.

**Design Philosophy:**
- One tool does one thing well (Unix philosophy)
- Configuration in plain text files
- Composable components
- No magic - predictable, debuggable behavior
- Sub-projects maintain independence

**Target Platform:**
- Taskwarrior 2.6.2 (and 2.x branch)
- NOT compatible with Taskwarrior 3.x
- Well-made PRs for 3.x compatibility considered but not guaranteed

## Architecture

### Core Components

```
awesome-taskwarrior/
├── tw.py                      # Main wrapper/manager
├── tw.config                  # User settings (simple key=value)
├── registry.d/                # App metadata (one file per app)
│   ├── tw-recurrence.meta
│   ├── tw-priority.meta
│   └── nicedates.meta
├── installers/                # Install scripts (one per app)
│   ├── tw-recurrence.install
│   ├── tw-priority.install
│   └── nicedates.install
├── bin/                       # Taskwarrior binaries (optional)
│   └── task-2.6.2
├── installed/                 # Installation tracking
│   └── .manifest             # List of installed apps with versions
├── lib/                       # Shared utilities
│   ├── tw-common.sh          # Bash library for installers
│   └── tw-wrapper.py         # Python library for wrapper apps
└── dev/                       # Development resources
    ├── models/               # Templates and examples
    └── API.md                # Function reference
```

### Component Responsibilities

**tw.py**
- Transparent pass-through to `task` for normal operations
- Package management (install/update/remove)
- Wrapper bridge (argument passing to wrapper apps)
- Built-in Taskwarrior 2.6.2 installer
- Dependency checking coordination
- Version tracking and updates

**Registry (.meta files)**
- Declare app metadata (name, version, description)
- Specify dependencies and conflicts
- Define installation requirements
- Track checksums for integrity

**Installers (.install scripts)**
- Handle git clone/update of source repos
- Create symlinks (hooks, executables)
- Modify taskrc configuration
- Verify installation
- Provide uninstall capability
- Optional: test suite

**Manifest**
- Track what's installed
- Record versions and checksums
- Enable update detection
- Support dependency resolution

## File Format Specifications

### Registry Metadata (.meta)

Location: `registry.d/<app-name>.meta`

Format: INI-style key=value pairs

```ini
# Required fields
name=tw-recurrence
short_desc=One-line description
version=1.0.0
repo=https://github.com/user/repo
type=hook|wrapper|utility|web
install_script=tw-recurrence.install

# Optional fields
long_desc=Multi-line description of functionality.
  Continuation lines must be indented.
author=username
requires=python3>=3.6,taskwarrior>=2.6.2
conflicts=other-app
provides=on-add-recurrence.py,on-modify-recurrence.py
wrapper=yes|no
checksum_type=sha256
checksum=abc123...
tags=hook,recurrence,scheduling
```

**Field Descriptions:**

- `name`: Unique identifier (no spaces)
- `short_desc`: One-line description for list view
- `long_desc`: Detailed description (optional)
- `version`: Current version (app's own versioning scheme)
- `author`: Maintainer username or name
- `repo`: Git repository URL
- `type`: Category (hook, wrapper, utility, web)
- `requires`: Comma-separated dependencies with optional version constraints
- `conflicts`: Apps that can't coexist
- `provides`: Files/commands this app installs
- `wrapper`: Whether this app wraps task commands
- `install_script`: Name of installer script in installers/ directory
- `checksum_type`: Hash algorithm (sha256 recommended)
- `checksum`: Hash of installation for verification
- `tags`: Comma-separated keywords for searching

### Install Scripts (.install)

Location: `installers/<app-name>.install`

Format: Bash script with required functions

```bash
#!/bin/bash
# Source common library
source "$(dirname "$0")/../lib/tw-common.sh"

# REQUIRED: Install function
install() {
    # Check dependencies (using tw-common.sh functions)
    tw_check_python_version 3.6 || return 1
    
    # Clone or update repository
    tw_clone_or_update "$REPO_URL" "$INSTALL_DIR/tw-recurrence" || return 1
    
    # Create symlinks for hooks
    tw_symlink_hook "on-add-recurrence.py" || return 1
    
    # Add taskrc configuration
    tw_add_config "uda.recur_template.type=string" || return 1
    
    echo "✓ Installed tw-recurrence"
    return 0
}

# REQUIRED: Uninstall function
uninstall() {
    # Remove hooks
    tw_remove_hook "on-add-recurrence.py"
    
    # Remove configuration
    tw_remove_config "uda.recur_template"
    
    # Remove installation directory
    rm -rf "$INSTALL_DIR/tw-recurrence"
    
    echo "✓ Uninstalled tw-recurrence"
    return 0
}

# OPTIONAL: Update function (if different from reinstall)
update() {
    cd "$INSTALL_DIR/tw-recurrence" || return 1
    git pull || return 1
    echo "✓ Updated tw-recurrence"
    return 0
}

# OPTIONAL: Test function
test() {
    echo "Testing tw-recurrence..."
    
    # Run basic tests
    tw_test_cmd "task add test recur:daily" || return 1
    tw_test_hook "on-add-recurrence.py" || return 1
    
    # Cleanup test data
    tw_test_cleanup
    
    echo "✓ All tests passed"
    return 0
}

# OPTIONAL: Dependency check (custom beyond standard checks)
check_deps() {
    # Standard checks are automatic, this is for special cases
    command -v jq >/dev/null 2>&1 || {
        echo "Error: jq is required but not installed"
        return 1
    }
    return 0
}
```

**Function Requirements:**

- All functions must return 0 on success, non-zero on failure
- Use `tw-common.sh` library functions (see API.md)
- Check dependencies before modifying system
- Provide clear error messages
- Clean up on failure when possible

**Environment Variables Available:**

- `$INSTALL_DIR`: Base installation directory (~/.task or system)
- `$TASKRC`: Path to user's .taskrc file
- `$HOOKS_DIR`: Hook installation directory
- `$TW_DEBUG`: Set to "1" when --debug flag used

### Configuration File (tw.config)

Location: `~/.task/tw.config` or alongside tw.py

Format: INI-style with sections

```ini
# Core settings
[paths]
executable_dir=~/bin
taskwarrior_bin=auto                    # or explicit path
install_root=~/.task
hooks_dir=~/.task/hooks
data_dir=~/.task/data

# System-wide installation (requires sudo)
[paths.system]
executable_dir=/usr/local/bin
install_root=/usr/share/taskwarrior

# General behavior
[settings]
prefer_system_task=yes                  # Use system task if available
auto_update=no                          # Don't auto-update on --check
verbose=yes                             # Show detailed output
confirm_dangerous=yes                   # Confirm remove/update operations

# Wrapper configuration
[wrappers]
# Stack order (bottom to top, applied in sequence)
stack=nicedates,cmx

# Per-command wrapper overrides
[wrappers.commands]
next=nicedates
list=cmx
span=cmx

# Debug settings
[debug]
enable=no                               # Global debug flag
propagate=yes                           # Pass --debug to sub-projects
log_dir=~/.task/logs                    # Debug log location
```

### Manifest File (.manifest)

Location: `installed/.manifest`

Format: Pipe-delimited records

```
name|version|checksum|install_date|repo_url
tw-recurrence|1.0.0|sha256:abc123...|2026-01-19T12:34:56|https://github.com/...
tw-priority|0.3.5|sha256:def456...|2026-01-19T13:45:00|https://github.com/...
nicedates|2.1.0|sha256:789abc...|2026-01-19T14:00:00|https://github.com/...
```

**Fields:**
1. App name (matches .meta file)
2. Installed version
3. Checksum (format:hash)
4. Installation timestamp (ISO 8601)
5. Source repository URL

## tw.py Command Reference

### Management Commands

```bash
# List available/installed apps
tw --list                    # Show all available apps
tw --list-installed          # Show only installed apps
tw --info <app>              # Detailed info about specific app

# Installation
tw --install <app>           # Install an app
tw --install-taskwarrior     # Install Taskwarrior 2.6.2 from repo

# Updates
tw --update <app>            # Update specific app
tw --update-all              # Update all installed apps
tw --check                   # Check for available updates

# Removal
tw --remove <app>            # Remove an app
tw --purge <app>             # Remove app and all its data

# Maintenance
tw --repair                  # Fix broken installations
tw --clean                   # Remove orphaned files
tw --verify                  # Verify checksums of installed apps

# Information
tw --version                 # Show tw.py and taskwarrior versions
tw --help                    # Show help message
```

### Wrapper Bridge Commands

```bash
# Execute wrapper directly
tw --exec <wrapper> [args...]    # One-off wrapper execution
tw --with <wrapper> <cmd>        # Override wrapper for command

# Wrapper management
tw --wrap <wrapper>              # Set default wrapper
tw --no-wrap <cmd>               # Bypass wrappers for command
tw --list-wrappers               # Show wrapper stack configuration
```

### Debug Commands

```bash
tw --debug <command>         # Enable debug mode for command
tw --debug --install <app>   # Debug installation process
```

### Pass-through (Normal Operation)

```bash
tw <any-task-command>        # Transparent pass-through to task
```

## Wrapper Stacking System

Wrappers can be chained to process commands in sequence:

```
User types: tw next
         ↓
    tw.py reads config
         ↓
    Stack: [nicedates → cmx → task]
         ↓
    Executes: nicedates.py next → cmx.sh next → task next
```

### Wrapper Requirements

For an app to participate in the wrapper stack:

1. **Accept standard arguments**: Must handle all task commands
2. **Pass-through capability**: Must forward to next wrapper or task
3. **Exit code propagation**: Must preserve task's exit codes
4. **Environment preservation**: Must not corrupt environment

### Wrapper Implementation Patterns

**Python wrapper:**
```python
#!/usr/bin/env python3
import sys
import subprocess

def process_args(args):
    # Modify args as needed
    return modified_args

def main():
    args = sys.argv[1:]
    modified = process_args(args)
    
    # Get next wrapper or task from environment
    next_cmd = os.environ.get('TW_NEXT_WRAPPER', 'task')
    
    # Execute and preserve exit code
    result = subprocess.run([next_cmd] + modified)
    sys.exit(result.returncode)

if __name__ == '__main__':
    main()
```

**Bash wrapper:**
```bash
#!/bin/bash
# Process arguments
args=("$@")
# ... modify args ...

# Get next wrapper or task
next_cmd="${TW_NEXT_WRAPPER:-task}"

# Execute and preserve exit code
exec "$next_cmd" "${args[@]}"
```

### Symlink Bridge

For wrappers that need special handling (like `nn span 2`):

```bash
# tw.py creates during install:
~/bin/nn -> tw --exec nn
~/bin/cmx -> tw --exec cmx

# Usage:
nn span 2           # tw.py handles argument passing correctly
cmx list            # tw.py handles argument passing correctly
```

## Adding a New App to the Registry

### Step-by-Step Process

1. **Create .meta file** in `registry.d/`
   - Use `dev/models/hook-template.meta` or `wrapper-template.meta`
   - Fill in all required fields
   - Add optional fields as appropriate

2. **Create .install script** in `installers/`
   - Use appropriate template from `dev/models/`
   - Implement required functions: `install()`, `uninstall()`
   - Add optional functions: `update()`, `test()`, `check_deps()`
   - Make executable: `chmod +x installers/yourapp.install`

3. **Test installation**
   ```bash
   tw --install yourapp
   tw --check yourapp
   tw --remove yourapp
   ```

4. **Add documentation**
   - Create README in the app's repository
   - Document dependencies
   - Provide usage examples
   - Note any taskrc changes required

5. **Submit to registry**
   - Fork awesome-taskwarrior
   - Add .meta and .install files
   - Create pull request
   - Include test results

### Quality Guidelines

**Required:**
- Installation must be non-destructive (check before modifying)
- Uninstallation must be clean (remove all traces)
- Dependencies must be clearly documented
- Conflicts must be declared
- Error messages must be helpful

**Recommended:**
- Include test function for --check
- Support both user and system installation
- Handle updates gracefully (preserve user data)
- Provide verbose mode output
- Log important operations

**Best Practices:**
- Use tw-common.sh library functions
- Follow existing naming conventions
- Version your app consistently
- Keep install scripts simple and readable
- Document any non-standard behavior

## Testing Framework

### Test Levels

1. **Unit tests**: Individual function testing (installer responsibility)
2. **Integration tests**: Installation + operation (required)
3. **System tests**: Interaction with other apps (recommended)

### Testing with tw.py

```bash
# Test specific app
tw --check yourapp              # Runs app's test() function

# Test all installed apps
tw --check                      # Runs tests for everything

# Test in isolation (doesn't affect main .task)
TW_TEST_ENV=1 tw --install yourapp
TW_TEST_ENV=1 tw --check yourapp
```

### Writing Test Functions

```bash
test() {
    echo "Testing yourapp..."
    
    # Use test utilities from tw-common.sh
    tw_test_setup || return 1
    
    # Test basic functionality
    tw_test_cmd "task add test" || return 1
    
    # Test hook execution
    tw_test_hook "on-add-yourapp.sh" || return 1
    
    # Test configuration
    tw_test_config "uda.yourapp.type" "string" || return 1
    
    # Clean up
    tw_test_cleanup
    
    echo "✓ All tests passed"
    return 0
}
```

## Versioning Strategy

### tw.py Versioning

- **Semantic versioning**: MAJOR.MINOR.PATCH
- **Major**: Breaking changes to tw.py interface
- **Minor**: New features, new flags
- **Patch**: Bug fixes, documentation

### Sub-project Versioning

- **Independent**: Each project maintains its own version scheme
- **No enforcement**: Can be semver, date-based, or custom
- **Tracked only**: tw.py records versions but doesn't mandate format

### Registry Versioning

- **Date-based snapshots**: `2026.01` for monthly releases (optional)
- **Git-based**: Commit hashes are canonical
- **Manifest tracks individuals**: Each app version recorded separately

## Debug System

### Debug Propagation

When `tw --debug` is used:

1. tw.py sets `TW_DEBUG=1` environment variable
2. Install scripts can check `$TW_DEBUG` and increase verbosity
3. Sub-projects can implement their own `--debug` handling
4. All debug output goes to stderr
5. Log files written to `~/.task/logs/` if configured

### Implementing Debug Support

**In install scripts:**
```bash
install() {
    if [ "$TW_DEBUG" = "1" ]; then
        set -x  # Enable bash debug mode
    fi
    
    debug_msg "Installing to $INSTALL_DIR"
    # ... rest of installation
}

debug_msg() {
    [ "$TW_DEBUG" = "1" ] && echo "DEBUG: $*" >&2
}
```

**In wrapper apps:**
```python
import os

DEBUG = os.environ.get('TW_DEBUG') == '1'

def debug_print(msg):
    if DEBUG:
        print(f"DEBUG: {msg}", file=sys.stderr)
```

## Common Development Patterns

### Dependency Checking

```bash
# Check Python version
tw_check_python_version 3.6 || {
    echo "Error: Python 3.6+ required"
    return 1
}

# Check command availability
command -v jq >/dev/null 2>&1 || {
    echo "Error: jq not found. Install with: sudo apt install jq"
    return 1
}

# Check Taskwarrior version
tw_check_taskwarrior_version 2.6.2 || {
    echo "Error: Taskwarrior 2.6.2+ required"
    return 1
}
```

### Hook Installation

```bash
# Simple symlink
tw_symlink_hook "on-add-yourapp.py" || return 1

# From subdirectory
tw_symlink_hook "src/on-add-yourapp.py" "on-add-yourapp.py" || return 1

# Multiple hooks
for hook in on-add on-modify on-exit; do
    tw_symlink_hook "${hook}-yourapp.py" || return 1
done
```

### Configuration Management

```bash
# Add UDA
tw_add_config "uda.yourapp.type=string"
tw_add_config "uda.yourapp.label=Your App"

# Remove UDA
tw_remove_config "uda.yourapp"

# Check if config exists
tw_config_exists "uda.yourapp.type" && echo "Already configured"
```

### Repository Management

```bash
# Clone or update
tw_clone_or_update "https://github.com/user/repo" "$INSTALL_DIR/yourapp" || return 1

# Clone specific branch
tw_clone_or_update "https://github.com/user/repo" "$INSTALL_DIR/yourapp" "develop"

# Update existing
cd "$INSTALL_DIR/yourapp" && git pull || return 1
```

## Contribution Guidelines

### Code Style

- **Bash scripts**: Follow Google Shell Style Guide
- **Python scripts**: Follow PEP 8
- **Comments**: Explain why, not what
- **Functions**: One purpose, well-named
- **Error handling**: Always check return codes

### Documentation

- Update DEVELOPERS.md for architectural changes
- Update API.md for new library functions
- Create/update model templates as needed
- Document breaking changes prominently

### Pull Request Process

1. Test thoroughly on clean Taskwarrior installation
2. Verify uninstallation removes all traces
3. Run existing tests: `tw --check`
4. Update relevant documentation
5. Follow existing file naming conventions
6. Include example usage in PR description

### Review Criteria

- Does it work with Taskwarrior 2.6.2?
- Does it follow the architecture?
- Are dependencies clearly stated?
- Does uninstall clean up completely?
- Is error handling robust?
- Are error messages helpful?

## Security Considerations

### Install Script Safety

- **Never execute arbitrary code** from remote sources
- **Verify checksums** before installation
- **Use HTTPS** for all git operations
- **Validate input** in install scripts
- **Fail safely** on errors

### User Data Protection

- **Never modify user data** without explicit permission
- **Backup before destructive operations**
- **Isolate test environments** from production
- **Clear sensitive data** from logs

### Permissions

- **Request minimum necessary permissions**
- **Default to user installation** (no sudo)
- **Document system installation requirements**
- **Never require root** for normal operation

## Troubleshooting

### Common Issues

**Installation fails:**
- Check dependencies with `tw --check`
- Verify git access to repository
- Check disk space and permissions
- Review install script debug output

**Hook not executing:**
- Verify symlink exists: `ls -la ~/.task/hooks/`
- Check permissions: hook must be executable
- Test hook manually: `~/.task/hooks/on-add-test.py`
- Check Taskwarrior hook execution: `task diagnostics`

**Wrapper not working:**
- Verify wrapper is in stack: `tw --list-wrappers`
- Test wrapper directly: `tw --exec wrapper command`
- Check environment: `echo $TW_NEXT_WRAPPER`
- Review wrapper script for errors

**Updates failing:**
- Check git repository access
- Verify no local modifications: `git status`
- Try clean reinstall: `tw --remove app && tw --install app`

## Resources

- **API Reference**: See `dev/API.md` for library functions
- **Templates**: See `dev/models/` for working examples
- **Taskwarrior Docs**: https://taskwarrior.org/docs/
- **Main Repository**: https://github.com/linuxcaffe/awesome-taskwarrior

## Maintenance

This document is maintained by the awesome-taskwarrior project. Last updated: 2026-01-19.

For questions or clarifications, open an issue on GitHub.
