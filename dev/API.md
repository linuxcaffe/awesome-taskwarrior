# awesome-taskwarrior API Reference
**Version:** 2.0.0  
**Updated:** January 2026

## Overview

awesome-taskwarrior is a **self-contained package manager** for Taskwarrior extensions. Version 2.0.0 features:

- **Self-installing**: Bootstrap with one curl command
- **Self-updating**: `tw --update tw` updates itself
- **Registry-based**: Points to extension repos (like npm, PyPI)
- **No file duplication**: Extensions stay in their own repos
- **Manifest tracking**: Clean installs/uninstalls

## Installation

### Bootstrap Install
```bash
curl -fsSL https://raw.githubusercontent.com/linuxcaffe/awesome-taskwarrior/main/install.sh | bash
```

This installs tw.py to `~/.task/scripts/tw` and adds it to your PATH.

### Manual Install
```bash
mkdir -p ~/.task/scripts
curl -fsSL https://raw.githubusercontent.com/linuxcaffe/awesome-taskwarrior/main/tw.py -o ~/.task/scripts/tw
chmod +x ~/.task/scripts/tw
echo 'export PATH="$HOME/.task/scripts:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## tw.py Commands

### Package Management

```bash
tw --list                  # List all apps (installed + available)
tw --install APP           # Install an app
tw --remove APP            # Remove an app
tw --update APP            # Update an app
tw --info APP              # Show app details
tw --verify APP            # Verify checksums
tw --update tw             # Update tw.py itself
tw --version               # Show versions
tw --help                  # Show help
```

### Debug Mode

```bash
tw --debug <command>           # Enable debug (default level 1)
tw --debug=1 <command>         # Level 1: Basic operations
tw --debug=2 <command>         # Level 2: Detailed + subprocess calls
tw --debug=3 <command>         # Level 3: Everything + taskwarrior debug.hooks

# Named modes
tw --debug=tw <command>        # Same as level 1
tw --debug=hooks <command>     # Same as level 2
tw --debug=task <command>      # Same as level 3
tw --debug=all <command>       # Same as level 3
tw --debug=verbose <command>   # Same as level 3
```

**Debug Levels:**
- **Level 1**: Basic tw.py operations, success/failure
- **Level 2**: Detailed operations, subprocess calls, file paths
- **Level 3**: Everything from level 2 + taskwarrior's `rc.debug.hooks=2`

**Debug Output:**
- Goes to **stderr** (color-coded blue)
- Logs to `~/.task/logs/debug/tw_debug_TIMESTAMP.log`
- Keeps last 10 debug sessions
- Sets environment variables for installers

**Example:**
```bash
tw --debug=2 --install tw-recurrence

# Output:
[debug] 16:45:23.123 | main              | Debug mode enabled (level 2)
[debug] 16:45:23.130 | AppManager.install| Installing tw-recurrence
[debug] 16:45:23.200 | tw-recurrence     | Debug enabled (level 2)
[debug] 16:45:23.211 | tw-recurrence     | Downloading hook: on-add_recurrence.py
[tw] ✓ Successfully installed tw-recurrence

# Check logs:
cat ~/.task/logs/debug/tw_debug_20260123_164523.log
cat ~/.task/logs/debug/tw-recurrence_debug_20260123_164523.log
```

### Pass-through to Taskwarrior

```bash
tw add "Buy milk"          # Same as: task add "Buy milk"
tw list                    # Lists apps (use 'task list' for tasks)
tw next                    # Same as: task next
```

## Directory Structure

Everything lives in `~/.task/`:

```
~/.task/
├── config/
│   ├── .tw_manifest           # Installation tracking
│   └── *.rc                   # Extension configs
├── scripts/
│   ├── tw                     # The package manager
│   └── *                      # Extension scripts
├── hooks/
│   └── *.py                   # Extension hooks
├── docs/
│   ├── tw_README.md           # tw.py documentation
│   └── *_README.md            # Extension docs
└── logs/
    └── *.log                  # Debug logs
```

## Environment Variables

Installers receive these from tw.py (or use defaults):

```bash
INSTALL_DIR=~/.task              # Main Taskwarrior directory
HOOKS_DIR=~/.task/hooks          # Taskwarrior hooks
SCRIPTS_DIR=~/.task/scripts      # Wrapper scripts  
CONFIG_DIR=~/.task/config        # Configuration files
DOCS_DIR=~/.task/docs            # Documentation files
LOGS_DIR=~/.task/logs            # Debug/test logs
TASKRC=~/.taskrc                 # Taskwarrior config
TW_COMMON=path/to/tw-common.sh   # Helper library (dev mode only)
TW_DRY_RUN=1                     # Set if --dry-run
```

### Debug Environment Variables

When `tw --debug` is used, these are also set:

```bash
TW_DEBUG=<level>                 # Debug level (1-3)
TW_DEBUG_LEVEL=<level>           # Same as TW_DEBUG
DEBUG_HOOKS=1                    # Set to 1 if level >= 2
TW_DEBUG_LOG=/path/to/logs       # Directory for debug logs
```

**Installers should check these and enable their own debug output:**

```bash
if [[ "${TW_DEBUG:-0}" -gt 0 ]] || [[ "${DEBUG_HOOKS:-0}" == "1" ]]; then
    DEBUG_ENABLED=1
    DEBUG_LEVEL="${TW_DEBUG_LEVEL:-${TW_DEBUG:-1}}"
    DEBUG_LOG="${TW_DEBUG_LOG:-$HOME/.task/logs/debug}/myapp_debug_$(date +%Y%m%d_%H%M%S).log"
    
    debug_msg() {
        if [[ "$DEBUG_LEVEL" -ge "${2:-1}" ]]; then
            echo "[debug] $(date +%H:%M:%S) | myapp | $1" | tee -a "$DEBUG_LOG" >&2
        fi
    }
else
    debug_msg() { :; }  # No-op
fi

# Use in installer:
debug_msg "Starting installation" 1
debug_msg "Downloading from $BASE_URL" 2
```

## Manifest Format

Location: `~/.task/config/.tw_manifest`

Format: `app|version|filepath|checksum|date`

Example:
```
tw-recurrence|2.0.0|/home/user/.task/hooks/on-add_recurrence.py||2026-01-23T12:00:00Z
tw-recurrence|2.0.0|/home/user/.task/hooks/on-exit_recurrence.py||2026-01-23T12:00:00Z
tw-recurrence|2.0.0|/home/user/.task/config/recurrence.rc||2026-01-23T12:00:00Z
```

## Creating an Installer

### Automated with make-awesome-install.sh

```bash
# Download the tool
curl -fsSL https://raw.githubusercontent.com/linuxcaffe/awesome-taskwarrior/main/make-awesome-install.sh -o make-awesome-install.sh
chmod +x make-awesome-install.sh

# Run in your project directory
cd ~/my-extension
../make-awesome-install.sh

# Follow prompts - it generates:
# - appname.meta
# - appname.install
```

See [MAKE_AWESOME_GUIDE.md](MAKE_AWESOME_GUIDE.md) for details.

### Manual Installer Template

```bash
#!/usr/bin/env bash
set -euo pipefail

APPNAME="my-extension"
VERSION="1.0.0"
BASE_URL="https://raw.githubusercontent.com/user/my-extension/main"

# Environment detection (works standalone or with tw.py)
: "${HOOKS_DIR:=$HOME/.task/hooks}"
: "${CONFIG_DIR:=$HOME/.task/config}"
: "${DOCS_DIR:=$HOME/.task/docs}"
: "${TASKRC:=$HOME/.taskrc}"

# Optional tw-common.sh (only available in dev mode)
if [[ -f "${TW_COMMON:-}" ]]; then
    source "$TW_COMMON"
else
    # Fallback functions for standalone use
    tw_msg() { echo "[tw] $*"; }
    tw_success() { echo "[tw] ✓ $*"; }
    tw_error() { echo "[tw] ✗ $*" >&2; }
fi

# Debug support - automatically added by make-awesome-install.sh
if [[ "${TW_DEBUG:-0}" -gt 0 ]] || [[ "${DEBUG_HOOKS:-0}" == "1" ]]; then
    DEBUG_ENABLED=1
    DEBUG_LEVEL="${TW_DEBUG_LEVEL:-${TW_DEBUG:-1}}"
    DEBUG_LOG_DIR="${TW_DEBUG_LOG:-$HOME/.task/logs/debug}"
    DEBUG_LOG="${DEBUG_LOG_DIR}/${APPNAME}_debug_$(date +%Y%m%d_%H%M%S).log"
    
    mkdir -p "$DEBUG_LOG_DIR"
    
    debug_msg() {
        local level="${2:-1}"
        if [[ "$DEBUG_LEVEL" -ge "$level" ]]; then
            local timestamp=$(date +"%H:%M:%S.%N" | cut -c1-12)
            local msg="[debug] $timestamp | $APPNAME | $1"
            echo -e "\033[34m$msg\033[0m" >&2
            echo "$msg" >> "$DEBUG_LOG"
        fi
    }
    
    debug_msg "Debug enabled (level $DEBUG_LEVEL)" 1
    debug_msg "Log file: $DEBUG_LOG" 2
else
    debug_msg() { :; }  # No-op when debug disabled
fi

install() {
    tw_msg "Installing $APPNAME v$VERSION..."
    debug_msg "Starting installation" 1
    debug_msg "BASE_URL: $BASE_URL" 2
    
    # Create directories
    mkdir -p "$HOOKS_DIR" "$CONFIG_DIR" "$DOCS_DIR"
    
    # Download files
    debug_msg "Downloading hook.py" 2
    curl -fsSL "$BASE_URL/hook.py" -o "$HOOKS_DIR/hook.py" || {
        tw_error "Failed to download hook"
        debug_msg "Download failed: hook.py" 1
        return 1
    }
    chmod +x "$HOOKS_DIR/hook.py"
    debug_msg "Installed: $HOOKS_DIR/hook.py" 2
    
    debug_msg "Downloading config.rc" 2
    curl -fsSL "$BASE_URL/config.rc" -o "$CONFIG_DIR/config.rc" || {
        tw_error "Failed to download config"
        debug_msg "Download failed: config.rc" 1
        return 1
    }
    debug_msg "Installed: $CONFIG_DIR/config.rc" 2
    
    # Add config to .taskrc
    local config_line="include $CONFIG_DIR/config.rc"
    if ! grep -qF "$config_line" "$TASKRC" 2>/dev/null; then
        echo "$config_line" >> "$TASKRC"
        debug_msg "Added config to .taskrc" 2
    fi
    
    # Track in manifest
    debug_msg "Writing to manifest" 2
    MANIFEST_FILE="${HOME}/.task/config/.tw_manifest"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    mkdir -p "$(dirname "$MANIFEST_FILE")"
    
    echo "$APPNAME|$VERSION|$HOOKS_DIR/hook.py||$TIMESTAMP" >> "$MANIFEST_FILE"
    echo "$APPNAME|$VERSION|$CONFIG_DIR/config.rc||$TIMESTAMP" >> "$MANIFEST_FILE"
    
    debug_msg "Installation complete" 1
    tw_success "Installed $APPNAME v$VERSION"
    return 0
}

remove() {
    tw_msg "Removing $APPNAME..."
    debug_msg "Starting removal" 1
    
    # Remove files
    rm -f "$HOOKS_DIR/hook.py"
    debug_msg "Removed: $HOOKS_DIR/hook.py" 2
    rm -f "$CONFIG_DIR/config.rc"
    debug_msg "Removed: $CONFIG_DIR/config.rc" 2
    
    # Remove config from .taskrc
    local config_line="include $CONFIG_DIR/config.rc"
    grep -vF "$config_line" "$TASKRC" > "$TASKRC.tmp" 2>/dev/null || true
    mv "$TASKRC.tmp" "$TASKRC"
    
    # Remove from manifest
    debug_msg "Removing from manifest" 2
    MANIFEST_FILE="${HOME}/.task/config/.tw_manifest"
    if [[ -f "$MANIFEST_FILE" ]]; then
        grep -v "^$APPNAME|" "$MANIFEST_FILE" > "$MANIFEST_FILE.tmp" 2>/dev/null || true
        mv "$MANIFEST_FILE.tmp" "$MANIFEST_FILE"
    fi
    
    debug_msg "Removal complete" 1
    tw_success "Removed $APPNAME"
    return 0
}

case "${1:-}" in
    install) install ;;
    remove) remove ;;
    *) echo "Usage: $0 {install|remove}"; exit 1 ;;
esac
```

## Metadata File Format

Create `registry.d/appname.meta`:

```ini
name=My Extension Name
version=1.0.0
type=hook
description=Brief description of what it does
repo=https://github.com/user/my-extension
base_url=https://raw.githubusercontent.com/user/my-extension/main/
files=hook.py:hook,config.rc:config,README.md:doc

# Checksums (SHA256) - comma-separated, same order as files
checksums=abc123...,def456...,ghi789...

# Additional metadata
author=Your Name
license=MIT
requires_taskwarrior=2.6.0
requires_python=3.6
```

### Required Fields
- `name` - Human-readable name
- `version` - Semantic version (X.Y.Z)
- `type` - Primary type: hook, script, config, theme
- `description` - One-line description
- `repo` - GitHub repository URL
- `base_url` - Raw GitHub URL for downloads
- `files` - Comma-separated filename:type pairs

### File Types
- `hook` → `~/.task/hooks/` (executable)
- `script` → `~/.task/scripts/` (executable)
- `config` → `~/.task/config/`
- `doc` → `~/.task/docs/` (renamed to appname_README.md)

### Optional Fields
- `checksums` - SHA256 hashes (comma-separated)
- `author` - Author name
- `license` - License type
- `requires_taskwarrior` - Minimum Taskwarrior version
- `requires_python` - Minimum Python version

## Architecture

### Registry-Based (Like npm, PyPI)

```
┌─────────────────────────────────────────┐
│  awesome-taskwarrior (Registry)         │
│  ├── tw.py (package manager)            │
│  ├── registry.d/*.meta (metadata)       │
│  └── installers/*.install (installers)  │
└─────────────────────────────────────────┘
             ↓ points to
┌─────────────────────────────────────────┐
│  Extension Repos                        │
│  (tw-recurrence, tw-priority, etc)      │
│  ├── hooks, scripts, configs            │
│  └── documentation                      │
└─────────────────────────────────────────┘
```

### Installation Flow

1. User runs `tw --install tw-recurrence`
2. tw.py downloads installer from awesome-taskwarrior
3. Installer downloads files from tw-recurrence repo
4. Files placed in `~/.task/`
5. Manifest updated in `~/.task/config/.tw_manifest`

### Benefits

✅ **No duplication** - Extensions stay in their repos  
✅ **No sync issues** - One source of truth  
✅ **Lightweight** - Registry is just metadata  
✅ **Direct from source** - Always fresh  
✅ **Self-updating** - tw.py updates itself  

## Operating Modes

### Production Mode (Normal)
- tw.py installed to `~/.task/scripts/tw`
- Fetches registry from GitHub
- Downloads installers from GitHub
- No local awesome-taskwarrior repo needed

### Dev Mode (For Development)
- tw.py in awesome-taskwarrior repo
- Uses local `registry.d/` and `installers/`
- Fast iteration during development
- Auto-detected if directories exist

## Common Patterns

### Hook with Config
```bash
install() {
    curl -fsSL "$BASE_URL/hook.py" -o "$HOOKS_DIR/hook.py"
    chmod +x "$HOOKS_DIR/hook.py"
    
    curl -fsSL "$BASE_URL/config.rc" -o "$CONFIG_DIR/config.rc"
    echo "include $CONFIG_DIR/config.rc" >> "$TASKRC"
    
    # Manifest tracking
    MANIFEST_FILE="$HOME/.task/config/.tw_manifest"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "$APPNAME|$VERSION|$HOOKS_DIR/hook.py||$TIMESTAMP" >> "$MANIFEST_FILE"
    echo "$APPNAME|$VERSION|$CONFIG_DIR/config.rc||$TIMESTAMP" >> "$MANIFEST_FILE"
}
```

### Multiple Hooks
```bash
install() {
    for hook in on-add on-exit on-modify; do
        curl -fsSL "$BASE_URL/${hook}_app.py" -o "$HOOKS_DIR/${hook}_app.py"
        chmod +x "$HOOKS_DIR/${hook}_app.py"
        echo "$APPNAME|$VERSION|$HOOKS_DIR/${hook}_app.py||$TIMESTAMP" >> "$MANIFEST_FILE"
    done
}
```

### Hook with Symlink
```bash
install() {
    # Download base hook
    curl -fsSL "$BASE_URL/on-add_app.py" -o "$HOOKS_DIR/on-add_app.py"
    chmod +x "$HOOKS_DIR/on-add_app.py"
    
    # Create symlink for on-modify
    ln -sf "on-add_app.py" "$HOOKS_DIR/on-modify_app.py"
    
    # Track both
    echo "$APPNAME|$VERSION|$HOOKS_DIR/on-add_app.py||$TIMESTAMP" >> "$MANIFEST_FILE"
    echo "$APPNAME|$VERSION|$HOOKS_DIR/on-modify_app.py||$TIMESTAMP" >> "$MANIFEST_FILE"
}
```

## Testing

### Test Standalone First
```bash
# Must work without tw.py
bash installers/my-extension.install install

# Verify
ls -la ~/.task/hooks/
cat ~/.task/config/.tw_manifest

# Test removal
bash installers/my-extension.install remove
```

### Test with tw.py (Dev Mode)
```bash
cd ~/awesome-taskwarrior
./tw.py --list
./tw.py --install my-extension
./tw.py --info my-extension
./tw.py --remove my-extension
```

### Test with tw.py (Production Mode)
```bash
# After pushing to GitHub
tw --install my-extension
tw --verify my-extension
tw --update my-extension
tw --remove my-extension
```

## Generating Checksums

```bash
cd ~/my-extension
sha256sum hook.py config.rc README.md

# Output:
# abc123... hook.py
# def456... config.rc
# ghi789... README.md

# Add to .meta (comma-separated, same order):
checksums=abc123...,def456...,ghi789...
```

## Submitting Extensions

1. **Create extension** in its own repo
2. **Push to GitHub**
3. **Run make-awesome-install.sh** in extension repo
4. **Test installers** standalone and with tw.py
5. **Fork awesome-taskwarrior**
6. **Add files**:
   - Copy `appname.meta` to `registry.d/`
   - Copy `appname.install` to `installers/`
7. **Submit PR**

## Self-Updating tw.py

tw.py can update itself:

```bash
tw --update tw
```

This downloads the latest tw.py from GitHub and replaces itself.

## Troubleshooting

### PATH not set
```bash
echo 'export PATH="$HOME/.task/scripts:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Manifest location changed
Old: `~/.task/.tw_manifest`  
New: `~/.task/config/.tw_manifest`

Installers must write to new location.

### Extension won't install
1. Check it's listed: `tw --list`
2. Verify GitHub repo is accessible
3. Try standalone: `bash installers/app.install install`
4. Check manifest path in installer

## Migration from v1.x

Key changes:
- Manifest moved to `~/.task/config/.tw_manifest`
- tw.py self-installs to `~/.task/scripts/tw`
- No tw-common.sh in production (optional in dev)
- Installers must have fallback logic
- Registry is metadata only (no file hosting)

## See Also

- [CONTRIBUTING.md](CONTRIBUTING.md) - How to create installers
- [QUICKSTART.md](QUICKSTART.md) - Quick start for users
- [MAKE_AWESOME_GUIDE.md](MAKE_AWESOME_GUIDE.md) - Automated packaging tool
- [README.md](README.md) - Project overview
