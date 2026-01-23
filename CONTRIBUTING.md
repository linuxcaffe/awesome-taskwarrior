# Contributing to awesome-taskwarrior
**Version:** 2.0.0

Thank you for your interest in contributing! This guide will help you create installers for Taskwarrior extensions following the v2.0.0 curl-based architecture.

## Quick Start

1. **Prepare your repository** with curl-friendly file layout
2. **Create .meta file** in `registry.d/`
3. **Create .install script** in `installers/`
4. **Test standalone** before testing with tw.py
5. **Submit PR** with both files

## Repository Structure

Organize your files for direct curl downloads:

```
your-project/
├── on-add_myapp.py      # Hook file
├── myapp.rc             # Config file
├── README.md            # Documentation
├── tests/               # Test suite (not installed)
└── .github/             # CI/CD (not installed)
```

**Key Points:**
- All installable files at repository root or in obvious locations
- No need for `installers/` directory in your repo
- Tests and CI files won't be installed (not in .meta files list)

## Creating .meta File

Create `registry.d/yourapp.meta` with this format:

```ini
name=Your Application Name
version=1.0.0
type=hook
description=Brief description of what your application does
repo=https://github.com/yourusername/yourapp
base_url=https://raw.githubusercontent.com/yourusername/yourapp/main/
files=file1.py:hook,file2.rc:config,README.md:doc
checksums=abc123...,def456...,ghi789...
```

**Field Guide:**
- `name` - Human-readable name (can have spaces)
- `version` - Semantic version (X.Y.Z)
- `type` - Primary type: `hook`, `wrapper`, or `config`
- `description` - One-line description
- `repo` - Full GitHub URL
- `base_url` - Raw GitHub URL for file downloads
- `files` - Comma-separated `filename:type` pairs
- `checksums` - Optional SHA256 hashes (comma-separated, same order as files)

**File Types:**
- `hook` - Goes to `~/.task/hooks/`, made executable
- `script` - Goes to `~/.task/scripts/`, made executable
- `config` - Goes to `~/.task/config/`
- `doc` - Goes to `~/.task/docs/`, typically renamed to `appname_README.md`

## Creating .install Script

### Start from Template

Copy the appropriate template:
- `dev/models/hook-template.install` for hooks
- `dev/models/wrapper-template.install` for wrappers

### Key Requirements

Your installer MUST be **self-contained**:

```bash
#!/usr/bin/env bash
set -euo pipefail

APPNAME="yourapp"
VERSION="1.0.0"
BASE_URL="https://raw.githubusercontent.com/user/yourapp/main"

# Environment detection with defaults
: "${HOOKS_DIR:=$HOME/.task/hooks}"
: "${CONFIG_DIR:=$HOME/.task/config}"
: "${DOCS_DIR:=$HOME/.task/docs}"
: "${TASKRC:=$HOME/.taskrc}"

# Optional tw-common.sh sourcing
if [[ -f "${TW_COMMON:-}" ]]; then
    source "$TW_COMMON"
else
    # Fallback functions
    tw_msg() { echo "[tw] $*"; }
    tw_success() { echo "[tw] ✓ $*"; }
    tw_error() { echo "[tw] ✗ $*" >&2; }
fi

install() {
    tw_msg "Installing $APPNAME v$VERSION..."
    
    # Your installation logic here
    
    tw_success "Installed $APPNAME v$VERSION"
}

remove() {
    tw_msg "Removing $APPNAME..."
    
    # Use manifest removal if available
    if type tw_uninstall_app &>/dev/null; then
        tw_uninstall_app "$APPNAME"
    else
        # Fallback manual cleanup
        rm -f "$HOOKS_DIR/file1.py"
        rm -f "$CONFIG_DIR/file2.rc"
    fi
    
    tw_success "Removed $APPNAME"
}

case "${1:-}" in
    install) install ;;
    remove) remove ;;
    *) echo "Usage: $0 {install|remove}"; exit 1 ;;
esac
```

### Installation Best Practices

1. **Download Files**
```bash
# With tw-common.sh
if type tw_curl_and_place &>/dev/null; then
    tw_curl_and_place "$BASE_URL/file.py" "$HOOKS_DIR"
else
    # Fallback
    mkdir -p "$HOOKS_DIR"
    curl -fsSL "$BASE_URL/file.py" -o "$HOOKS_DIR/file.py"
fi
```

2. **Make Executable**
```bash
chmod +x "$HOOKS_DIR/file.py"
```

3. **Rename README**
```bash
# Install README as appname_README.md
if type tw_curl_and_place &>/dev/null; then
    tw_curl_and_place "$BASE_URL/README.md" "$DOCS_DIR" "${APPNAME}_README.md"
else
    curl -fsSL "$BASE_URL/README.md" -o "$DOCS_DIR/${APPNAME}_README.md"
fi
```

4. **Add Config**
```bash
if type tw_add_config &>/dev/null; then
    tw_add_config "include $CONFIG_DIR/$APPNAME.rc"
else
    if ! grep -q "include $CONFIG_DIR/$APPNAME.rc" "$TASKRC"; then
        echo "include $CONFIG_DIR/$APPNAME.rc" >> "$TASKRC"
    fi
fi
```

5. **Track in Manifest**
```bash
if type tw_manifest_add &>/dev/null; then
    tw_manifest_add "$APPNAME" "$VERSION" "$HOOKS_DIR/file.py"
    tw_manifest_add "$APPNAME" "$VERSION" "$CONFIG_DIR/file.rc"
fi
```

## Generating Checksums

```bash
# Generate checksums for all files
sha256sum on-add_myapp.py myapp.rc README.md

# Output format (copy hashes to .meta file):
abc123... on-add_myapp.py
def456... myapp.rc
ghi789... README.md

# Add to .meta file (same order as files=):
checksums=abc123...,def456...,ghi789...
```

## Testing Workflow

### 1. Test Standalone First

```bash
# This MUST work without tw.py
bash installers/yourapp.install install

# Verify files installed
ls -la ~/.task/hooks/
ls -la ~/.task/config/
ls -la ~/.task/docs/

# Test removal
bash installers/yourapp.install remove

# Verify clean removal
ls -la ~/.task/hooks/
```

### 2. Test with tw.py

```bash
# Dry run first
tw.py --dry-run --install yourapp

# Real installation
tw.py --install yourapp

# Verify
tw.py --info yourapp
tw.py --list

# Test checksums (if provided)
tw.py --verify yourapp

# Test removal
tw.py --remove yourapp
```

### 3. Test Update

```bash
# Install old version
tw.py --install yourapp

# Update to new version
tw.py --update yourapp

# Verify new version
tw.py --info yourapp
```

## Common Patterns

### Hook with Config

```bash
install() {
    # Download hook
    tw_curl_and_place "$BASE_URL/on-add_myapp.py" "$HOOKS_DIR"
    chmod +x "$HOOKS_DIR/on-add_myapp.py"
    
    # Download config
    tw_curl_and_place "$BASE_URL/myapp.rc" "$CONFIG_DIR"
    tw_add_config "include $CONFIG_DIR/myapp.rc"
    
    # Track files
    tw_manifest_add "$APPNAME" "$VERSION" "$HOOKS_DIR/on-add_myapp.py"
    tw_manifest_add "$APPNAME" "$VERSION" "$CONFIG_DIR/myapp.rc"
}
```

### Multiple Hooks

```bash
install() {
    # Download all hooks
    for hook in on-add on-modify on-exit; do
        tw_curl_and_place "$BASE_URL/${hook}_${APPNAME}.py" "$HOOKS_DIR"
        chmod +x "$HOOKS_DIR/${hook}_${APPNAME}.py"
        tw_manifest_add "$APPNAME" "$VERSION" "$HOOKS_DIR/${hook}_${APPNAME}.py"
    done
}
```

### Hook with Symlink

```bash
install() {
    # Download base hook
    tw_curl_and_place "$BASE_URL/on-modify_myapp.py" "$HOOKS_DIR"
    chmod +x "$HOOKS_DIR/on-modify_myapp.py"
    
    # Create symlink for on-add (same behavior)
    ln -sf "on-modify_myapp.py" "$HOOKS_DIR/on-add_myapp.py"
    
    # Track both
    tw_manifest_add "$APPNAME" "$VERSION" "$HOOKS_DIR/on-modify_myapp.py"
    tw_manifest_add "$APPNAME" "$VERSION" "$HOOKS_DIR/on-add_myapp.py"
}
```

### Wrapper Script

```bash
install() {
    # Download wrapper
    tw_curl_and_place "$BASE_URL/mywrapper" "$SCRIPTS_DIR"
    chmod +x "$SCRIPTS_DIR/mywrapper"
    
    tw_manifest_add "$APPNAME" "$VERSION" "$SCRIPTS_DIR/mywrapper"
    
    tw_msg "Add $SCRIPTS_DIR to your PATH to use 'mywrapper' command"
}
```

## Submission Checklist

Before submitting your PR:

- [ ] Tested installer standalone: `bash installers/yourapp.install install`
- [ ] Tested with tw.py: `tw.py --install yourapp`
- [ ] Verified all files installed correctly
- [ ] Tested removal cleans up completely
- [ ] Generated checksums (optional but recommended)
- [ ] .meta file has all required fields
- [ ] .install script has fallback logic
- [ ] README in your repo documents usage
- [ ] Follows naming conventions (on-add_appname.py, not on-add-appname.py)

## Naming Conventions

**Hook Files:**
- Format: `on-<event>_<appname>.py`
- Examples: `on-add_recurrence.py`, `on-modify_priority.py`

**Config Files:**
- Format: `<appname>.rc`
- Examples: `recurrence.rc`, `priority.rc`

**Wrapper Scripts:**
- Format: `<appname>` (no extension)
- Examples: `nicedates`, `taskopen`

**Documentation:**
- In repo: `README.md`
- Installed as: `<appname>_README.md`
- Location: `~/.task/docs/`

## Breaking Changes from v1.3.0

If migrating an existing installer:

1. Remove `short_name` field from .meta
2. Remove `SHORT_NAME` variable from .install
3. Replace `tw_clone_to_project()` with curl downloads
4. Replace `tw_symlink_hook()` with direct placement
5. Update paths (no subdirectories under hooks/ or scripts/)
6. Add fallback logic for standalone operation

See [MIGRATION.md](MIGRATION.md) for detailed migration guide.

## Getting Help

- Check [API.md](dev/API.md) for function reference
- Check [DEVELOPERS.md](DEVELOPERS.md) for architecture details
- Review existing installers in `installers/` directory
- Use templates in `dev/models/` as starting points
- Open an issue for questions

## Questions?

Feel free to open an issue or submit a draft PR for feedback!
