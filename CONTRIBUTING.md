# Contributing to awesome-taskwarrior
**Version:** 2.0.0  
**Updated:** January 2026

Thank you for contributing! This guide will help you package your Taskwarrior extension for the awesome-taskwarrior registry.

## Quick Start

### Option 1: Automated (Recommended)

```bash
# 1. Download the packaging tool
curl -fsSL https://raw.githubusercontent.com/linuxcaffe/awesome-taskwarrior/main/make-awesome-install.sh -o make-awesome-install.sh
chmod +x make-awesome-install.sh

# 2. Run it in your extension directory
cd ~/my-extension
../make-awesome-install.sh

# 3. Follow the prompts
# It will generate:
# - my-extension.meta
# - my-extension.install

# 4. Test it
./my-extension.install install
./my-extension.install remove

# 5. Submit to awesome-taskwarrior (see below)
```

See [MAKE_AWESOME_GUIDE.md](MAKE_AWESOME_GUIDE.md) for detailed usage.

### Option 2: Manual

1. Create `.meta` file with metadata
2. Create `.install` script (self-contained bash)
3. Test standalone
4. Test with tw.py
5. Submit PR

## Understanding the Architecture

awesome-taskwarrior is a **registry** (like npm, PyPI) that points to extension repositories:

```
┌─────────────────────────────────────────┐
│  awesome-taskwarrior (Registry)         │
│  ├── registry.d/*.meta (metadata)       │
│  └── installers/*.install (installers)  │
└─────────────────────────────────────────┘
             ↓ points to
┌─────────────────────────────────────────┐
│  Your Extension Repo                    │
│  ├── hook.py, config.rc, etc           │
│  └── README.md                          │
└─────────────────────────────────────────┘
```

**Key Points:**
- Your files stay in **your repo**
- awesome-taskwarrior hosts **metadata only**
- Installers download files from **your repo**
- No file duplication, no sync issues

## Preparing Your Extension

### 1. Organize Your Repository

Keep it simple - files at root or in obvious locations:

```
my-extension/
├── on-add_myext.py      # Hook file
├── myext.rc             # Config file
├── README.md            # Documentation
├── LICENSE              # License file
├── tests/               # Test suite (not installed)
└── .github/             # CI/CD (not installed)
```

### 2. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/user/my-extension.git
git push -u origin main
```

## Creating the Package

### Using make-awesome-install.sh (Automated)

```bash
cd ~/my-extension
make-awesome-install.sh
```

The script will:
1. ✅ Auto-detect your files (hooks, scripts, configs, docs)
2. ✅ Prompt for metadata (name, version, description)
3. ✅ Calculate SHA256 checksums
4. ✅ Generate `.meta` file
5. ✅ Create complete `.install` script
6. ✅ Provide testing and submission instructions

### Manual Creation

#### Create registry.d/my-extension.meta

```ini
name=My Extension
version=1.0.0
type=hook
description=Brief description of what it does
repo=https://github.com/user/my-extension
base_url=https://raw.githubusercontent.com/user/my-extension/main/
files=on-add_myext.py:hook,myext.rc:config,README.md:doc

# Checksums (SHA256) - generate with: sha256sum file1 file2 file3
checksums=abc123...,def456...,ghi789...

# Additional metadata
author=Your Name
license=MIT
requires_taskwarrior=2.6.0
requires_python=3.6
```

**Required Fields:**
- `name` - Human-readable name
- `version` - Semantic version (X.Y.Z)
- `type` - Primary type: `hook`, `script`, `config`, `theme`
- `description` - One-line description
- `repo` - GitHub repository URL
- `base_url` - Raw GitHub URL (for curl downloads)
- `files` - Comma-separated `filename:type` pairs

**File Types:**
- `hook` → `~/.task/hooks/` (made executable)
- `script` → `~/.task/scripts/` (made executable)
- `config` → `~/.task/config/`
- `doc` → `~/.task/docs/` (renamed to `appname_README.md`)

#### Create installers/my-extension.install

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

# Optional tw-common.sh (only in dev mode)
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
    
    # Download hook
    curl -fsSL "$BASE_URL/on-add_myext.py" -o "$HOOKS_DIR/on-add_myext.py" || {
        tw_error "Failed to download hook"
        return 1
    }
    chmod +x "$HOOKS_DIR/on-add_myext.py"
    
    # Download config
    curl -fsSL "$BASE_URL/myext.rc" -o "$CONFIG_DIR/myext.rc" || {
        tw_error "Failed to download config"
        return 1
    }
    
    # Download docs
    curl -fsSL "$BASE_URL/README.md" -o "$DOCS_DIR/myext_README.md" 2>/dev/null || true
    
    # Add config to .taskrc
    local config_line="include $CONFIG_DIR/myext.rc"
    if ! grep -qF "$config_line" "$TASKRC" 2>/dev/null; then
        echo "$config_line" >> "$TASKRC"
        tw_msg "Added config to .taskrc"
    fi
    
    # Track in manifest
    MANIFEST_FILE="${HOME}/.task/config/.tw_manifest"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    mkdir -p "$(dirname "$MANIFEST_FILE")"
    
    echo "$APPNAME|$VERSION|$HOOKS_DIR/on-add_myext.py||$TIMESTAMP" >> "$MANIFEST_FILE"
    echo "$APPNAME|$VERSION|$CONFIG_DIR/myext.rc||$TIMESTAMP" >> "$MANIFEST_FILE"
    echo "$APPNAME|$VERSION|$DOCS_DIR/myext_README.md||$TIMESTAMP" >> "$MANIFEST_FILE"
    
    tw_success "Installed $APPNAME v$VERSION"
    tw_msg "Documentation: $DOCS_DIR/myext_README.md"
    echo ""
    
    return 0
}

remove() {
    tw_msg "Removing $APPNAME..."
    
    # Remove files
    rm -f "$HOOKS_DIR/on-add_myext.py"
    rm -f "$CONFIG_DIR/myext.rc"
    rm -f "$DOCS_DIR/myext_README.md"
    
    # Remove config from .taskrc
    local config_line="include $CONFIG_DIR/myext.rc"
    if [[ -f "$TASKRC" ]]; then
        grep -vF "$config_line" "$TASKRC" > "$TASKRC.tmp" 2>/dev/null || true
        mv "$TASKRC.tmp" "$TASKRC"
    fi
    
    # Remove from manifest
    MANIFEST_FILE="${HOME}/.task/config/.tw_manifest"
    if [[ -f "$MANIFEST_FILE" ]]; then
        grep -v "^$APPNAME|" "$MANIFEST_FILE" > "$MANIFEST_FILE.tmp" 2>/dev/null || true
        mv "$MANIFEST_FILE.tmp" "$MANIFEST_FILE"
    fi
    
    tw_success "Removed $APPNAME"
    echo ""
    
    return 0
}

case "${1:-}" in
    install) install ;;
    remove) remove ;;
    *)
        echo "Usage: $0 {install|remove}"
        echo ""
        echo "This installer is self-contained and can run standalone."
        echo "It also integrates with awesome-taskwarrior (tw.py)."
        exit 1
        ;;
esac
```

**Key Requirements:**
1. ✅ Self-contained (works without tw.py)
2. ✅ Has fallback functions (tw_msg, tw_success, tw_error)
3. ✅ Downloads from your GitHub repo
4. ✅ Writes to `~/.task/config/.tw_manifest`
5. ✅ Handles install and remove

## Generating Checksums

```bash
cd ~/my-extension

# Generate checksums for all files (in same order as .meta files=)
sha256sum on-add_myext.py myext.rc README.md

# Output:
abc123... on-add_myext.py
def456... myext.rc
ghi789... README.md

# Add to .meta file (comma-separated):
checksums=abc123...,def456...,ghi789...
```

## Testing

### 1. Test Standalone (Required)

```bash
# Must work without tw.py
bash installers/my-extension.install install

# Verify files
ls -la ~/.task/hooks/on-add_myext.py
ls -la ~/.task/config/myext.rc
cat ~/.task/config/.tw_manifest

# Test your hook
task add "Test task"

# Test removal
bash installers/my-extension.install remove

# Verify clean removal
ls ~/.task/hooks/on-add_myext.py  # Should be gone
ls ~/.task/config/myext.rc         # Should be gone
grep myext ~/.task/config/.tw_manifest  # Should be empty
```

### 2. Test with Debug (Important!)

Test that your installer respects debug environment variables:

```bash
# Test debug level 1
TW_DEBUG=1 bash installers/my-extension.install install

# Should see debug output:
[debug] 16:45:23.123 | my-extension | Debug enabled (level 1)
[debug] 16:45:23.200 | my-extension | Starting installation
[debug] 16:45:28.450 | my-extension | Installation complete

# Check debug log was created
ls -la ~/.task/logs/debug/
cat ~/.task/logs/debug/my-extension_debug_*.log

# Test debug level 2 (more detail)
TW_DEBUG=2 bash installers/my-extension.install install

# Should see detailed output:
[debug] 16:45:23.210 | my-extension | Downloading hook: on-add_myext.py
[debug] 16:45:25.100 | my-extension | Installed: ~/.task/hooks/on-add_myext.py

# Test removal with debug
TW_DEBUG=2 bash installers/my-extension.install remove
```

### 3. Test with tw.py (Local/Dev Mode)

If you've cloned awesome-taskwarrior:

```bash
cd ~/awesome-taskwarrior

# Copy your files
cp ~/my-extension/my-extension.meta registry.d/
cp ~/my-extension/my-extension.install installers/
chmod +x installers/my-extension.install

# Test without debug
./tw.py --list          # Should show your extension
./tw.py --info my-extension
./tw.py --install my-extension
./tw.py --list          # Should show as installed

# Test with debug
./tw.py --debug=2 --install my-extension

# Should see both tw.py AND installer debug output:
[debug] 16:45:23.100 | main              | Debug mode enabled (level 2)
[debug] 16:45:23.110 | AppManager.install| Installing my-extension
[debug] 16:45:23.200 | my-extension      | Debug enabled (level 2)
[debug] 16:45:23.210 | my-extension      | Downloading hook.py
[tw] ✓ Successfully installed my-extension

# Check both log files were created:
ls -la ~/.task/logs/debug/
cat ~/.task/logs/debug/tw_debug_*.log
cat ~/.task/logs/debug/my-extension_debug_*.log

# Test removal
./tw.py --remove my-extension
```

### 4. Test with tw.py (Production Mode)

After submitting PR and it's merged:

```bash
tw --list
tw --install my-extension
tw --verify my-extension  # If checksums provided
tw --info my-extension
tw --update my-extension
tw --remove my-extension
```

## Common Patterns

### Hook with Config
```bash
# Download and install hook
curl -fsSL "$BASE_URL/hook.py" -o "$HOOKS_DIR/hook.py"
chmod +x "$HOOKS_DIR/hook.py"

# Download and add config
curl -fsSL "$BASE_URL/config.rc" -o "$CONFIG_DIR/config.rc"
echo "include $CONFIG_DIR/config.rc" >> "$TASKRC"

# Track both
echo "$APPNAME|$VERSION|$HOOKS_DIR/hook.py||$TIMESTAMP" >> "$MANIFEST_FILE"
echo "$APPNAME|$VERSION|$CONFIG_DIR/config.rc||$TIMESTAMP" >> "$MANIFEST_FILE"
```

### Multiple Hooks
```bash
for hook in on-add on-modify on-exit; do
    curl -fsSL "$BASE_URL/${hook}_app.py" -o "$HOOKS_DIR/${hook}_app.py"
    chmod +x "$HOOKS_DIR/${hook}_app.py"
    echo "$APPNAME|$VERSION|$HOOKS_DIR/${hook}_app.py||$TIMESTAMP" >> "$MANIFEST_FILE"
done
```

### Hook with Symlink
```bash
# Download main hook
curl -fsSL "$BASE_URL/on-add_app.py" -o "$HOOKS_DIR/on-add_app.py"
chmod +x "$HOOKS_DIR/on-add_app.py"

# Create symlink for on-modify
ln -sf "on-add_app.py" "$HOOKS_DIR/on-modify_app.py"

# Track both
echo "$APPNAME|$VERSION|$HOOKS_DIR/on-add_app.py||$TIMESTAMP" >> "$MANIFEST_FILE"
echo "$APPNAME|$VERSION|$HOOKS_DIR/on-modify_app.py||$TIMESTAMP" >> "$MANIFEST_FILE"
```

### Script Only
```bash
curl -fsSL "$BASE_URL/myscript" -o "$SCRIPTS_DIR/myscript"
chmod +x "$SCRIPTS_DIR/myscript"
echo "$APPNAME|$VERSION|$SCRIPTS_DIR/myscript||$TIMESTAMP" >> "$MANIFEST_FILE"

tw_msg "Add $SCRIPTS_DIR to PATH to use 'myscript' command"
```

## Submitting to awesome-taskwarrior

### Step 1: Fork

Go to https://github.com/linuxcaffe/awesome-taskwarrior and click "Fork"

### Step 2: Clone Your Fork

```bash
git clone https://github.com/YOUR_USERNAME/awesome-taskwarrior.git
cd awesome-taskwarrior
```

### Step 3: Add Your Files

```bash
# Copy generated files
cp ~/my-extension/my-extension.meta registry.d/
cp ~/my-extension/my-extension.install installers/

# Make installer executable
chmod +x installers/my-extension.install
```

### Step 4: Test Locally

```bash
./tw.py --list
./tw.py --install my-extension
./tw.py --info my-extension
./tw.py --remove my-extension
```

### Step 5: Commit and Push

```bash
git add registry.d/my-extension.meta installers/my-extension.install
git commit -m "Add my-extension v1.0.0

- Brief description of what it does
- Key features
- Tested standalone and with tw.py"

git push origin main
```

### Step 6: Create Pull Request

1. Go to your fork on GitHub
2. Click "Pull Request"
3. Add description:
   - What the extension does
   - Why it's useful
   - Link to your extension repo
   - Testing you've done
   - Any special requirements

## Naming Conventions

**Hook Files:**
- Format: `on-<event>_<appname>.py`
- Examples: `on-add_recurrence.py`, `on-modify_priority.py`

**Config Files:**
- Format: `<appname>.rc`
- Examples: `recurrence.rc`, `priority.rc`

**Script Files:**
- Format: `<appname>` (no extension)
- Examples: `taskopen`, `nicedates`

**Documentation:**
- In your repo: `README.md`
- Installed as: `<appname>_README.md` in `~/.task/docs/`

## Submission Checklist

Before submitting your PR:

- [ ] Extension files pushed to GitHub
- [ ] `.meta` file created with all required fields
- [ ] `.install` script created with fallback logic
- [ ] **Debug support added** (use make-awesome-install.sh)
- [ ] Checksums generated (optional but recommended)
- [ ] Tested standalone: `bash installers/my-extension.install install`
- [ ] **Tested with debug**: `TW_DEBUG=2 bash installers/my-extension.install install`
- [ ] Tested with tw.py: `./tw.py --install my-extension`
- [ ] **Tested tw.py debug**: `./tw.py --debug=2 --install my-extension`
- [ ] Verified all files install correctly
- [ ] Verified debug logs created in `~/.task/logs/debug/`
- [ ] Tested removal cleans up completely
- [ ] Documentation in your repo explains usage
- [ ] LICENSE file in your repo
- [ ] Naming follows conventions

## Updating Your Extension

When releasing a new version:

1. **Update files in your repo**
2. **Push to GitHub**
3. **Re-run make-awesome-install.sh** (updates version and checksums)
4. **Submit PR to awesome-taskwarrior** with updated `.meta` and `.install`

## Tips for Success

### Good Extension Candidates
- Custom hooks (priority, context, sync)
- Helper scripts (reporting, migration)
- Configuration sets (themes, workflows)
- Integration tools

### Documentation
- Clear README with usage examples
- Installation instructions
- Configuration options
- Troubleshooting section

### Testing
- Test on clean system if possible
- Test install → use → uninstall cycle
- Test with and without tw.py
- Check manifest tracking

### Code Quality
- Follow bash best practices
- Use `set -euo pipefail`
- Add error handling
- Provide helpful messages

## Getting Help

- **Documentation**: [API.md](API.md), [QUICKSTART.md](QUICKSTART.md)
- **Examples**: Browse existing installers in `installers/`
- **Tool**: [MAKE_AWESOME_GUIDE.md](MAKE_AWESOME_GUIDE.md)
- **Issues**: https://github.com/linuxcaffe/awesome-taskwarrior/issues
- **Community**: https://taskwarrior.org

## Migration from v1.x

Key changes in v2.0.0:

- **Manifest location**: `~/.task/.tw_manifest` → `~/.task/config/.tw_manifest`
- **Self-contained installers**: Must work without tw.py
- **Registry-based**: No file hosting in awesome-taskwarrior
- **Fallback functions**: Required for standalone operation
- **New directory**: `~/.task/scripts/` for tw.py and scripts

Update your installers:
1. Change manifest path
2. Add fallback functions
3. Test standalone operation
4. Submit updated files

## Questions?

Feel free to:
- Open an issue for questions
- Submit draft PR for feedback
- Check existing extensions as examples
- Use make-awesome-install.sh to automate packaging

Thank you for contributing to awesome-taskwarrior! 🎉
