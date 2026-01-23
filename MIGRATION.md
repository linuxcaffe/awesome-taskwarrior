# Migration Guide: v1.3.0 to v2.0.0

## Overview

Version 2.0.0 is a **major architectural change** that replaces git-based installation with curl-based direct file placement. This provides cleaner installations and better control over what gets installed.

**Key Benefits:**
- No nested git repositories under `~/.task/`
- Only needed files installed (no tests, CI configs, etc.)
- Cleaner directory structure
- Better uninstall granularity
- Faster installations

**Breaking Changes:**
- All installers must be rewritten
- Directory structure changed
- Manifest format changed
- Several functions removed from tw-common.sh

## For Users

### Backing Up

Before upgrading, backup your installation:

```bash
# Backup task data
cp -r ~/.task ~/.task.backup

# Backup taskrc
cp ~/.taskrc ~/.taskrc.backup

# Note installed apps
tw.py --list > ~/installed_apps.txt
```

### Upgrading

1. **Remove old installations:**
```bash
# Uninstall all apps with v1.3.0
for app in $(tw.py --list | grep -v "No applications" | awk '{print $1}'); do
    tw.py --remove "$app"
done
```

2. **Update awesome-taskwarrior:**
```bash
cd ~/awesome-taskwarrior
git pull
# or download v2.0.0 release
```

3. **Reinstall apps:**
```bash
# Apps will use v2.0.0 installers
tw.py --install tw-recurrence
tw.py --install tw-priority
# etc.
```

### What Changed for Users

**Directory Structure:**

v1.3.0:
```
~/.task/
├── hooks/
│   ├── on-add_recurrence.py -> recurrence/on-add_recurrence.py
│   └── recurrence/           # Project subdirectory
│       ├── on-add_recurrence.py
│       └── test/
```

v2.0.0:
```
~/.task/
├── hooks/
│   ├── on-add_recurrence.py  # Direct placement
│   └── on-modify_recurrence.py
├── docs/
│   └── recurrence_README.md  # Documentation
```

**No More:**
- Project subdirectories under hooks/ and scripts/
- Nested git repositories
- Unnecessary test files

**New:**
- `~/.task/docs/` directory for README files
- Flatter, cleaner structure
- Per-file manifest tracking

## For Developers

### .meta File Changes

**v1.3.0 Format:**
```ini
name=My App
version=1.0.0
type=hook
short_name=myapp
description=Does something
repo=https://github.com/user/myapp
```

**v2.0.0 Format:**
```ini
name=My App
version=1.0.0
type=hook
description=Does something
repo=https://github.com/user/myapp
base_url=https://raw.githubusercontent.com/user/myapp/main/
files=on-add_myapp.py:hook,myapp.rc:config,README.md:doc
checksums=abc123...,def456...,ghi789...
```

**Changes:**
- ❌ Removed: `short_name` field
- ✅ Added: `base_url` - for curl downloads
- ✅ Added: `files` - list of files with types
- ✅ Added: `checksums` - optional SHA256 hashes

### .install Script Changes

**v1.3.0 Pattern:**
```bash
APPNAME="tw-myapp"
SHORT_NAME="myapp"
REPO_URL="https://github.com/user/myapp"

install() {
    # Clone to project directory
    local project_dir
    project_dir=$(tw_clone_to_project hook "$SHORT_NAME" "$REPO_URL")
    
    # Create symlinks
    tw_symlink_hook "$project_dir" "on-add_myapp.py"
}
```

**v2.0.0 Pattern:**
```bash
APPNAME="myapp"
VERSION="1.0.0"
BASE_URL="https://raw.githubusercontent.com/user/myapp/main"

: "${HOOKS_DIR:=$HOME/.task/hooks}"
: "${CONFIG_DIR:=$HOME/.task/config}"

install() {
    # Download directly
    if type tw_curl_and_place &>/dev/null; then
        tw_curl_and_place "$BASE_URL/on-add_myapp.py" "$HOOKS_DIR"
    else
        curl -fsSL "$BASE_URL/on-add_myapp.py" -o "$HOOKS_DIR/on-add_myapp.py"
    fi
    
    chmod +x "$HOOKS_DIR/on-add_myapp.py"
    
    # Track in manifest
    if type tw_manifest_add &>/dev/null; then
        tw_manifest_add "$APPNAME" "$VERSION" "$HOOKS_DIR/on-add_myapp.py"
    fi
}
```

**Key Changes:**
1. ❌ No `SHORT_NAME` variable
2. ❌ No `REPO_URL` variable
3. ✅ Add `BASE_URL` for downloads
4. ✅ Add `VERSION` variable
5. ✅ Environment detection: `: "${HOOKS_DIR:=...}"`
6. ✅ Fallback logic for standalone operation
7. ✅ Direct file placement instead of git clone

### Function Changes

#### Removed Functions

These functions no longer exist in tw-common.sh v2.0.0:

```bash
# v1.3.0 - REMOVED in v2.0.0
tw_clone_to_project()    # Use tw_curl_and_place()
tw_clone_or_update()     # Use curl downloads
tw_get_install_dir()     # Use explicit directory variables
tw_symlink_hook()        # Use direct placement
tw_symlink_wrapper()     # Use direct placement
tw_remove_hook()         # Use tw_uninstall_app()
tw_remove_wrapper()      # Use tw_uninstall_app()
```

#### New Functions

```bash
# v2.0.0 - NEW
tw_curl_file()           # Download a file
tw_curl_and_place()      # Download and place file
tw_ensure_executable()   # Make file executable
tw_backup_file()         # Create backup with timestamp
tw_verify_checksum()     # Verify SHA256
tw_calculate_checksum()  # Calculate SHA256
tw_manifest_add()        # Add to manifest
tw_manifest_remove()     # Remove from manifest
tw_manifest_get_files()  # Get installed files
tw_manifest_app_installed() # Check if installed
tw_install_to()          # Install file by type
tw_uninstall_app()       # Uninstall using manifest
```

#### Unchanged Functions

These functions work the same in v2.0.0:

```bash
tw_msg()
tw_success()
tw_error()
tw_warn()
tw_debug()
tw_config_exists()
tw_add_config()
tw_remove_config()
tw_check_version()
tw_check_taskwarrior_version()
tw_check_python_version()
tw_run_tests()
```

### Migration Checklist

To migrate your installer from v1.3.0 to v2.0.0:

#### 1. Update .meta File

- [ ] Remove `short_name` field
- [ ] Add `base_url` field (raw GitHub URL)
- [ ] Add `files` field with filename:type pairs
- [ ] Optionally add `checksums` field

#### 2. Update .install Script

- [ ] Remove `SHORT_NAME` variable
- [ ] Remove `REPO_URL` variable
- [ ] Add `VERSION` variable
- [ ] Add `BASE_URL` variable
- [ ] Add environment detection: `: "${HOOKS_DIR:=...}"`
- [ ] Replace `tw_clone_to_project()` with curl downloads
- [ ] Replace `tw_symlink_hook()` with direct placement
- [ ] Add fallback logic for tw-common.sh functions
- [ ] Update paths (no subdirectories)
- [ ] Use `tw_manifest_add()` for tracking
- [ ] Use `tw_uninstall_app()` for removal

#### 3. Test

- [ ] Test standalone: `bash installers/yourapp.install install`
- [ ] Test with tw.py: `tw.py --install yourapp`
- [ ] Verify file locations
- [ ] Test removal: `tw.py --remove yourapp`
- [ ] Verify clean removal (no leftover files)

### Example Migration

**Before (v1.3.0):**

.meta file:
```ini
name=My Hook
version=1.0.0
type=hook
short_name=myhook
repo=https://github.com/user/myhook
```

.install file:
```bash
APPNAME="tw-myhook"
SHORT_NAME="myhook"
REPO_URL="https://github.com/user/myhook"

install() {
    local project_dir
    project_dir=$(tw_clone_to_project hook "$SHORT_NAME" "$REPO_URL")
    tw_symlink_hook "$project_dir" "on-add_myhook.py"
}

remove() {
    tw_remove_hook "on-add_myhook.py"
}
```

**After (v2.0.0):**

.meta file:
```ini
name=My Hook
version=1.0.0
type=hook
repo=https://github.com/user/myhook
base_url=https://raw.githubusercontent.com/user/myhook/main/
files=on-add_myhook.py:hook,README.md:doc
checksums=
```

.install file:
```bash
APPNAME="myhook"
VERSION="1.0.0"
BASE_URL="https://raw.githubusercontent.com/user/myhook/main"

: "${HOOKS_DIR:=$HOME/.task/hooks}"
: "${DOCS_DIR:=$HOME/.task/docs}"

if [[ -f "${TW_COMMON:-}" ]]; then
    source "$TW_COMMON"
else
    tw_msg() { echo "[tw] $*"; }
    tw_success() { echo "[tw] ✓ $*"; }
    tw_error() { echo "[tw] ✗ $*" >&2; }
fi

install() {
    tw_msg "Installing $APPNAME v$VERSION..."
    
    if type tw_curl_and_place &>/dev/null; then
        tw_curl_and_place "$BASE_URL/on-add_myhook.py" "$HOOKS_DIR"
        tw_curl_and_place "$BASE_URL/README.md" "$DOCS_DIR" "myhook_README.md"
    else
        mkdir -p "$HOOKS_DIR" "$DOCS_DIR"
        curl -fsSL "$BASE_URL/on-add_myhook.py" -o "$HOOKS_DIR/on-add_myhook.py"
        curl -fsSL "$BASE_URL/README.md" -o "$DOCS_DIR/myhook_README.md"
    fi
    
    chmod +x "$HOOKS_DIR/on-add_myhook.py"
    
    if type tw_manifest_add &>/dev/null; then
        tw_manifest_add "$APPNAME" "$VERSION" "$HOOKS_DIR/on-add_myhook.py"
        tw_manifest_add "$APPNAME" "$VERSION" "$DOCS_DIR/myhook_README.md"
    fi
    
    tw_success "Installed $APPNAME v$VERSION"
}

remove() {
    tw_msg "Removing $APPNAME..."
    
    if type tw_uninstall_app &>/dev/null; then
        tw_uninstall_app "$APPNAME"
    else
        rm -f "$HOOKS_DIR/on-add_myhook.py"
        rm -f "$DOCS_DIR/myhook_README.md"
    fi
    
    tw_success "Removed $APPNAME"
}

case "${1:-}" in
    install) install ;;
    remove) remove ;;
    *) echo "Usage: $0 {install|remove}"; exit 1 ;;
esac
```

## Common Issues

### Issue: Installer fails standalone

**Problem:** Installer requires tw-common.sh functions

**Solution:** Add fallback implementations:
```bash
if [[ -f "${TW_COMMON:-}" ]]; then
    source "$TW_COMMON"
else
    tw_msg() { echo "[tw] $*"; }
    tw_success() { echo "[tw] ✓ $*"; }
    # etc.
fi
```

### Issue: Files not found after installation

**Problem:** Using old subdirectory paths

**Solution:** Update to flat structure:
```bash
# OLD
$HOOKS_DIR/myapp/on-add_myapp.py

# NEW
$HOOKS_DIR/on-add_myapp.py
```

### Issue: Manifest not working

**Problem:** Not calling tw_manifest_add()

**Solution:** Track all installed files:
```bash
if type tw_manifest_add &>/dev/null; then
    tw_manifest_add "$APPNAME" "$VERSION" "$file_path"
fi
```

## Questions?

See [DEVELOPERS.md](DEVELOPERS.md) for architecture details or open an issue for help with migration.
