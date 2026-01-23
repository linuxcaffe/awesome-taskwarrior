# awesome-taskwarrior Developer Guide
**Version:** 2.0.0

## Overview

awesome-taskwarrior v2.0.0 introduces a **curl-based architecture** that replaces git operations with direct file downloads. This provides cleaner installations, better control over what gets installed, and eliminates nested git repositories under `~/.task/`.

**Design Philosophy:**
- Self-contained installers (work with or without tw.py)
- Direct file placement (no unnecessary symlinks)
- Per-file manifest tracking
- Checksum verification for integrity
- No git operations required

**Target Platform:**
- Taskwarrior 2.6.2 (and 2.x branch)
- NOT compatible with Taskwarrior 3.x

## Architecture Changes

### What Changed in v2.0.0

**Removed:**
- Git-based installation (`git clone` operations)
- Nested repositories under `~/.task/`
- Complex symlink forests
- `short_name` field in .meta files
- Project subdirectories

**Added:**
- Curl-based file downloads
- Direct file placement
- Per-file manifest tracking (`app|version|file|checksum|date`)
- `docs_dir` for README files
- `files=` field in .meta files
- `base_url=` field for download URLs
- `checksums=` field for verification

### Directory Structure

```
~/.task/
├── hooks/                          # Taskwarrior hooks (direct placement)
│   ├── on-add_recurrence.py
│   ├── on-modify_recurrence.py
│   └── on-exit_recurrence.py
├── scripts/                        # Wrapper scripts (direct placement)
│   ├── tw.py
│   └── nicedates
├── config/                         # Configuration files
│   ├── nicedates.rc
│   ├── priority.rc
│   ├── recurrence.rc
│   └── tw.config
├── docs/                           # README files
│   ├── priority_README.md
│   ├── recurrence_README.md
│   ├── tw_README.md
│   └── nicedates_README.md
├── logs/                           # Debug and test logs
│   └── recurrence/                 
├── .tw_manifest                    # Installation manifest
├── pending.data
├── completed.data
└── undo.data
```

**Key Principles:**
1. **Direct Placement**: Files go directly where Taskwarrior expects them
2. **No Subdirectories**: No `hooks/recurrence/` or `scripts/nicedates/` subdirectories
3. **Flat Structure**: All active hooks and scripts at top level
4. **Manifest Tracking**: Every installed file tracked for clean uninstall

## .meta File Format

Meta files define what gets installed and from where.

**Location:** `registry.d/appname.meta`

**Format:**
```ini
name=My Application
version=1.0.0
type=hook
description=Brief description of the application
repo=https://github.com/user/repo
base_url=https://raw.githubusercontent.com/user/repo/main/
files=file1.py:hook,file2.sh:script,config.rc:config,README.md:doc
checksums=sha256hash1,sha256hash2,sha256hash3,sha256hash4
```

**Required Fields:**
- `name` - Human-readable name
- `version` - Version number (semantic versioning)
- `type` - Primary type: hook, wrapper, or config
- `files` - Comma-separated list of filename:type pairs

**Optional Fields:**
- `description` - Brief description
- `repo` - GitHub repository URL
- `base_url` - Base URL for curl downloads (typically raw.githubusercontent.com)
- `checksums` - Comma-separated SHA256 hashes (same order as files)

**File Types:**
- `hook` - Installed to `~/.task/hooks/` (made executable)
- `script` - Installed to `~/.task/scripts/` (made executable)
- `config` - Installed to `~/.task/config/`
- `doc` - Installed to `~/.task/docs/` (typically renamed with app prefix)

### Example: tw-recurrence.meta

```ini
name=Enhanced Recurrence System
version=2.0.0
type=hook
description=Advanced task recurrence with chained and periodic patterns
repo=https://github.com/linuxcaffe/tw-recurrence_overhaul-hook
base_url=https://raw.githubusercontent.com/linuxcaffe/tw-recurrence_overhaul-hook/main/
files=on-add_recurrence.py:hook,on-modify_recurrence.py:hook,on-exit_recurrence.py:hook,recurrence.rc:config,README.md:doc
checksums=
```

## .install Script Pattern

Installer scripts must be **self-contained** - they work standalone or with tw.py assistance.

**Location:** `installers/appname.install`

**Structure:**
```bash
#!/usr/bin/env bash
set -euo pipefail

# App metadata
APPNAME="appname"
VERSION="1.0.0"
BASE_URL="https://raw.githubusercontent.com/user/repo/main"

# Environment detection (defaults for standalone use)
: "${HOOKS_DIR:=$HOME/.task/hooks}"
: "${SCRIPTS_DIR:=$HOME/.task/scripts}"
: "${CONFIG_DIR:=$HOME/.task/config}"
: "${DOCS_DIR:=$HOME/.task/docs}"
: "${TASKRC:=$HOME/.taskrc}"

# Optional: source tw-common.sh for helpers
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
    
    # Download and install files
    # ... implementation ...
    
    tw_success "Installed $APPNAME v$VERSION"
    return 0
}

remove() {
    tw_msg "Removing $APPNAME..."
    
    # Use manifest-based removal if available, otherwise manual cleanup
    if type tw_uninstall_app &>/dev/null; then
        tw_uninstall_app "$APPNAME"
    else
        # Manual cleanup for standalone use
        rm -f "$HOOKS_DIR/on-add_$APPNAME.py"
        # ... etc ...
    fi
    
    tw_success "Removed $APPNAME"
    return 0
}

# Main entry
case "${1:-}" in
    install) install ;;
    remove) remove ;;
    *) echo "Usage: $0 {install|remove}"; exit 1 ;;
esac
```

**Key Requirements:**
1. **Standalone Capability**: Must work without tw.py or tw-common.sh
2. **Environment Detection**: Use `: "${VAR:=default}"` pattern
3. **Optional Helpers**: Check for tw-common.sh functions with `type`
4. **Fallback Logic**: Provide fallback for all helper functions
5. **Clean Uninstall**: Remove all installed files

## Installer Independence Principle

**Critical:** Each installer MUST work independently:

```bash
# Users can run installers directly
bash installers/myapp.install install
bash installers/myapp.install remove

# tw.py adds convenience, not dependency
tw.py --install myapp
tw.py --remove myapp
```

**This means:**
- No hard requirement on tw.py being installed
- No hard requirement on tw-common.sh being available
- Installer detects environment or uses defaults
- Optional use of helper functions for better UX
- Fallback implementations for standalone use

## Creating a New Application

### 1. Prepare Your Repository

Organize files for curl-friendly downloads:

```
your-repo/
├── on-add_myapp.py      # Will go to ~/.task/hooks/
├── myapp                # Will go to ~/.task/scripts/
├── myapp.rc             # Will go to ~/.task/config/
├── README.md            # Will go to ~/.task/docs/myapp_README.md
└── tests/               # Your test suite (not installed)
```

### 2. Create .meta File

```ini
name=My Application
version=1.0.0
type=hook
description=Does something useful
repo=https://github.com/user/myapp
base_url=https://raw.githubusercontent.com/user/myapp/main/
files=on-add_myapp.py:hook,myapp.rc:config,README.md:doc
checksums=
```

### 3. Create .install Script

Use the template from `dev/models/hook-template.install` or `dev/models/wrapper-template.install` as a starting point.

Key implementation steps:
```bash
install() {
    # 1. Download files
    if type tw_curl_and_place &>/dev/null; then
        tw_curl_and_place "$BASE_URL/on-add_myapp.py" "$HOOKS_DIR"
    else
        mkdir -p "$HOOKS_DIR"
        curl -fsSL "$BASE_URL/on-add_myapp.py" -o "$HOOKS_DIR/on-add_myapp.py"
    fi
    
    # 2. Make executable (hooks/scripts only)
    chmod +x "$HOOKS_DIR/on-add_myapp.py"
    
    # 3. Add config (if any)
    if type tw_add_config &>/dev/null; then
        tw_add_config "include $CONFIG_DIR/myapp.rc"
    else
        echo "include $CONFIG_DIR/myapp.rc" >> "$TASKRC"
    fi
    
    # 4. Track in manifest (if available)
    if type tw_manifest_add &>/dev/null; then
        tw_manifest_add "$APPNAME" "$VERSION" "$HOOKS_DIR/on-add_myapp.py"
        tw_manifest_add "$APPNAME" "$VERSION" "$CONFIG_DIR/myapp.rc"
    fi
}
```

### 4. Generate Checksums (Optional but Recommended)

```bash
# Generate checksums for your files
sha256sum on-add_myapp.py myapp.rc README.md

# Add to .meta file
checksums=abc123...,def456...,ghi789...
```

### 5. Test

```bash
# Test standalone
bash installers/myapp.install install
bash installers/myapp.install remove

# Test with tw.py
tw.py --dry-run --install myapp
tw.py --install myapp
tw.py --info myapp
tw.py --verify myapp
tw.py --remove myapp
```

## Best Practices

1. **Keep It Simple**: One hook/script per file, clear names
2. **Standalone First**: Always test installers without tw.py
3. **Fallback Logic**: Provide alternatives for tw-common.sh functions
4. **Document Well**: README in your repo, good .meta description
5. **Version Carefully**: Use semantic versioning
6. **Test Thoroughly**: Install, use, uninstall, verify cleanup
7. **Checksum**: Generate and include checksums for security

## See Also

- [API.md](dev/API.md) - Function reference for tw-common.sh
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution workflow
- [MIGRATION.md](MIGRATION.md) - Migrating from v1.3.0
