# tw Tab Completion

**Version:** 2.2.0  
**Feature:** Shell completion for bash, zsh, and fish

## Overview

tw now includes built-in shell completion generation, following the same pattern as taskwarrior's native completion scripts. This provides intelligent tab completion for tw commands while seamlessly integrating with task's existing completion system.

## Quick Start

### Easy Installation (Recommended)

The easiest way to install completions is to let tw do it for you:

```bash
# Bash users
tw --install-completion bash

# Zsh users  
tw --install-completion zsh

# Fish users
tw --install-completion fish
```

tw will:
1. Create the necessary directories
2. Generate and install the completion script
3. Tell you what to add to your shell config file (if needed)
4. Show you how to activate it immediately

### Manual Installation

If you prefer manual installation or need more control:

```bash
# Bash
tw --generate-completion bash > ~/.bash_completion.d/tw.sh
source ~/.bash_completion.d/tw.sh
echo 'source ~/.bash_completion.d/tw.sh' >> ~/.bashrc

# Zsh
mkdir -p ~/.zsh/completion
tw --generate-completion zsh > ~/.zsh/completion/_tw
# Add to ~/.zshrc:
# fpath=(~/.zsh/completion $fpath)
# autoload -Uz compinit && compinit

# Fish
tw --generate-completion fish > ~/.config/fish/completions/tw.fish
# Fish auto-loads completions
```

## What Gets Completed

### tw-specific Commands
- All tw flags: `-I`, `--install`, `-r`, `--remove`, `-u`, `--update`, etc.
- App names from registry (for `--install`, `--info`)
- Installed app names from manifest (for `--remove`, `--update`, `--verify`)
- Help topics (for `--help <topic>`)
- Shell types (for `--generate-completion`)
- Debug levels (for `--debug`)

### Task Pass-Through
- All task commands (when no tw flag is detected)
- Tags with `+`/`-` prefixes
- Projects with `project:` prefix
- Task IDs for `--attach`
- All standard task filters and attributes

## Examples

```bash
# Install completion (recommended - does everything for you)
tw --install-completion bash
tw --install-completion zsh
tw --install-completion fish

# Generate completion (manual approach)
tw --generate-completion bash > ~/.bash_completion.d/tw.sh

# Complete tw commands
tw --i<TAB>           # → --install or --info

# Complete app names
tw --install <TAB>    # → shows available apps from registry
tw --remove <TAB>     # → shows installed apps from manifest

# Complete help topics
tw --help <TAB>       # → shell, install, remove, verify, list, info

# Pass through to task
tw add +<TAB>         # → shows task tags
tw project:<TAB>      # → shows task projects
tw <TAB>              # → shows both tw flags and task commands
```

## How It Works

### Architecture

The completion system uses a two-tier approach:

1. **tw-specific completion**: Handles tw's own flags and commands
2. **task pass-through**: Delegates to task's native completion for task commands

### Dynamic Data Sources

Completion scripts query live data:

- **Available apps**: Scanned from registry directory (`~/.task/registry` or `~/dev/awesome-taskwarrior/registry.d`)
- **Installed apps**: Read from manifest file (`~/.task/.tw_manifest`)
- **Task commands**: Retrieved via `task _commands`
- **Tags**: Retrieved via `task _tags`
- **Projects**: Retrieved via `task _projects`

### Registry Detection

Completion scripts automatically detect the registry location using the same logic as tw:

1. Check `TW_REGISTRY_DIR` environment variable
2. Check for dev mode: `~/dev/awesome-taskwarrior/registry.d`
3. Fall back to default: `~/.task/registry`

## Testing

Run the included test script to verify completion generation:

```bash
./test_completion.sh
```

This will:
- Generate completions for all three shells
- Verify output format
- Check error handling
- Display installation instructions

## Features

### Intelligent Context Detection

Completions are context-aware:
- After `--install`: Only show available (not yet installed) apps
- After `--remove`: Only show installed apps
- After `--help`: Only show help topics
- After `tw` with no flags: Show both tw flags and task commands

### Standalone Scripts

Generated completion scripts are standalone:
- No runtime dependency on tw
- Can be distributed separately
- Work offline (except for dynamic task data)
- Can be regenerated anytime tw is updated

### Environment Awareness

Scripts respect environment variables:
- `TW_REGISTRY_DIR`: Custom registry location
- `HOME`: User's home directory

## Install vs Generate

tw provides two commands for completion setup:

### `--install-completion` (Recommended)

**What it does:**
- Creates necessary directories
- Writes the completion script to the standard location
- Shows you what to add to your shell config
- Provides immediate activation instructions

**When to use:**
- First-time setup
- You want the simplest experience
- Standard installation paths are fine

**Example:**
```bash
tw --install-completion bash
# Output:
# [tw] Wrote completion script to: ~/.bash_completion.d/tw.sh
# [tw] Add this line to ~/.bashrc:
# [tw]   source ~/.bash_completion.d/tw.sh
# [tw] To activate now: source ~/.bash_completion.d/tw.sh
```

### `--generate-completion` (Manual)

**What it does:**
- Outputs the completion script to stdout
- You control where it goes
- No automatic setup

**When to use:**
- Custom installation paths
- System-wide installation (need sudo)
- Integration with package managers
- Testing or inspection

**Example:**
```bash
tw --generate-completion bash > /usr/share/bash-completion/completions/tw
# or
tw --generate-completion zsh | sudo tee /usr/local/share/zsh/site-functions/_tw
```

## Compatibility

### Shells
- **Bash**: 4.0+ (tested on 5.x)
- **Zsh**: 5.0+ (tested on 5.x)
- **Fish**: 3.0+ (tested on 3.x)

### Task Integration
- Compatible with taskwarrior 2.6.2
- Works alongside task's native completion
- No conflicts with existing task.sh, _task, or task.fish

## Troubleshooting

### Completion not working

1. **Verify installation**:
   ```bash
   # Bash
   declare -F _tw
   
   # Zsh
   which _tw
   
   # Fish
   complete -c tw
   ```

2. **Check file locations**:
   - Bash: `~/.bash_completion.d/tw.sh`
   - Zsh: `~/.zsh/completion/_tw` (and verify `fpath`)
   - Fish: `~/.config/fish/completions/tw.fish`

3. **Reload shell**:
   ```bash
   # Bash
   source ~/.bashrc
   
   # Zsh
   exec zsh
   
   # Fish
   exec fish
   ```

### No app names showing

1. **Check registry location**:
   ```bash
   ls ~/.task/registry/*.meta
   # or
   ls ~/dev/awesome-taskwarrior/registry.d/*.meta
   ```

2. **Verify registry has .meta files**:
   The completion looks for `*.meta` files in the registry directory.

3. **Check TW_REGISTRY_DIR** (if set):
   ```bash
   echo $TW_REGISTRY_DIR
   ```

### Pass-through to task not working

1. **Verify task completion is installed**:
   ```bash
   # Bash
   declare -F _task
   
   # Zsh  
   which _task
   
   # Fish
   complete -c task
   ```

2. **Install task completion** if missing:
   - Most package managers include task completion
   - Or manually install from taskwarrior source

## Implementation Details

### Bash Completion

Uses bash's `complete` builtin with a custom `_tw` function:
- `COMPREPLY` array for completion options
- `compgen` for generating matches
- Function detection via `declare -f _task`

### Zsh Completion

Uses zsh's `_arguments` system:
- Structured argument specifications
- Helper functions for app/topic completion
- Integration with `_describe` and `_task`

### Fish Completion

Uses fish's declarative completion system:
- `complete` commands with conditions
- Helper functions for dynamic data
- Condition functions for context detection

## Regenerating Completions

After updating tw, regenerate completions:

```bash
# Easy way - just re-run install
tw --install-completion bash
tw --install-completion zsh
tw --install-completion fish

# Or manually
tw --generate-completion bash > ~/.bash_completion.d/tw.sh
source ~/.bash_completion.d/tw.sh

tw --generate-completion zsh > ~/.zsh/completion/_tw
exec zsh

tw --generate-completion fish > ~/.config/fish/completions/tw.fish
exec fish
```

## Future Enhancements

Potential improvements for future versions:
- Context name completion for `@` commands
- Config file path completion
- UDA name completion
- Dynamic task report detection
- Auto-install completion script option

## Credits

- **Design**: Following taskwarrior's completion pattern
- **Implementation**: David (linuxcaffe) + Claude (Anthropic)
- **Based on**: task.sh, _task, task.fish from taskwarrior 2.6.2

## See Also

- [tw README](../README.md)
- [DEVELOPERS.md](../DEVELOPERS.md) - For extension authors
- [Taskwarrior Documentation](https://taskwarrior.org/docs/)
