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

install() {
    tw_msg "Installing $APPNAME v$VERSION..."
    
    # Create directories
    mkdir -p "$HOOKS_DIR" "$CONFIG_DIR" "$DOCS_DIR"
    
    # Download files
    curl -fsSL "$BASE_URL/hook.py" -o "$HOOKS_DIR/hook.py" || {
        tw_error "Failed to download hook"
        return 1
    }
    chmod +x "$HOOKS_DIR/hook.py"
    
    curl -fsSL "$BASE_URL/config.rc" -o "$CONFIG_DIR/config.rc" || {
        tw_error "Failed to download config"
        return 1
    }
    
    # Add config to .taskrc
    local config_line="include $CONFIG_DIR/config.rc"
    if ! grep -qF "$config_line" "$TASKRC" 2>/dev/null; then
        echo "$config_line" >> "$TASKRC"
    fi
    
    # Track in manifest
    MANIFEST_FILE="${HOME}/.task/config/.tw_manifest"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    mkdir -p "$(dirname "$MANIFEST_FILE")"
    
    echo "$APPNAME|$VERSION|$HOOKS_DIR/hook.py||$TIMESTAMP" >> "$MANIFEST_FILE"
    echo "$APPNAME|$VERSION|$CONFIG_DIR/config.rc||$TIMESTAMP" >> "$MANIFEST_FILE"
    
    tw_success "Installed $APPNAME v$VERSION"
    return 0
}

remove() {
    tw_msg "Removing $APPNAME..."
    
    # Remove files
    rm -f "$HOOKS_DIR/hook.py"
    rm -f "$CONFIG_DIR/config.rc"
    
    # Remove config from .taskrc
    local config_line="include $CONFIG_DIR/config.rc"
    grep -vF "$config_line" "$TASKRC" > "$TASKRC.tmp" 2>/dev/null || true
    mv "$TASKRC.tmp" "$TASKRC"
    
    # Remove from manifest
    MANIFEST_FILE="${HOME}/.task/config/.tw_manifest"
    if [[ -f "$MANIFEST_FILE" ]]; then
        grep -v "^$APPNAME|" "$MANIFEST_FILE" > "$MANIFEST_FILE.tmp" 2>/dev/null || true
        mv "$MANIFEST_FILE.tmp" "$MANIFEST_FILE"
    fi
    
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
