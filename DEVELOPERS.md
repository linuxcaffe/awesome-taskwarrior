# Developer Documentation - awesome-taskwarrior v2.0.0

## Architecture Overview

Version 2.0.0 introduces a fundamental shift from git-based installation to **curl-based direct file placement**. This architecture solves three critical problems:

1. **No nested git repos** - Cloning under `~/.task/` created nested repos
2. **No unnecessary files** - Only needed files are installed
3. **No symlink forests** - Direct placement eliminates fragility

### Core Principles

#### 1. Installer Independence

**Each `.install` script MUST work standalone:**

```bash
# Users can run installers directly
bash installers/myapp.install install

# tw.py adds convenience, not dependency
tw.py install myapp
```

This means:
- No hard dependencies on `tw.py` or `tw-common.sh`
- Installers detect environment or use sensible defaults
- Optional use of utility functions for better UX
- Self-contained logic for install/remove operations

#### 2. Direct File Placement

Files go exactly where Taskwarrior expects them:

```
~/.task/
├── hooks/              # on-*.py files (executable)
├── scripts/            # Wrapper scripts (executable)
├── config/             # *.rc configuration files
└── docs/               # *_README.md documentation
```

**No subdirectories, no symlinks by default.**

#### 3. Curl-Based Downloads

```bash
# Download specific files from raw GitHub URLs
curl -fsSL "$BASE_URL/on-add.py" -o "$HOOKS_DIR/on-add_myapp.py"
```

Benefits:
- No git dependency
- Smaller downloads
- Only needed files
- Faster installation

#### 4. Type-Based Routing

Files are routed to directories based on their type:

| Type | Directory | Examples |
|------|-----------|----------|
| `hook` | `~/.task/hooks/` | `on-add_*.py`, `on-modify_*.py` |
| `script` | `~/.task/scripts/` | Wrapper executables |
| `config` | `~/.task/config/` | `*.rc`, `*.config` |
| `doc` | `~/.task/docs/` | `*_README.md` |

## Creating an Application

### Repository Structure

Organize your repository for curl-friendly installation:

```
myapp-repo/
├── on-add_myapp.py      # Will go to ~/.task/hooks/
├── on-modify_myapp.py   # Will go to ~/.task/hooks/
├── myapp                # Will go to ~/.task/scripts/
├── myapp.rc             # Will go to ~/.task/config/
├── README.md            # Will go to ~/.task/docs/ as myapp_README.md
├── myapp.meta           # For awesome-taskwarrior registry
├── myapp.install        # Self-contained installer
├── tests/               # Your test suite
└── CHANGELOG.md         # Not installed (stays in repo)
```

**Key points:**
- Files to be installed should be in repository root
- File names should include app identifier (e.g., `on-add_myapp.py`)
- Documentation and development files stay in repo

### Creating a .meta File

The `.meta` file describes your application for the registry.

**Format:**

```ini
# Application metadata
name=myapp
version=1.0.0
description=Brief description of what your app does
requires=python3,taskwarrior>=2.6.0

# Files to install (filename:type,filename:type,...)
files=on-add_myapp.py:hook,on-modify_myapp.py:hook,myapp.rc:config,README.md:doc

# Base URL for downloading files
base_url=https://raw.githubusercontent.com/username/myapp/main/

# Optional: SHA256 checksums (sha256:hash,sha256:hash,...)
# Order matches files= field
checksums=sha256:abc123...,sha256:def456...,sha256:789xyz...,sha256:012uvw...
```

**Field Descriptions:**

- **name**: Application identifier (used in commands like `tw.py install myapp`)
- **version**: Semantic version (e.g., "1.0.0", "2.1.3")
- **description**: One-line description shown in listings
- **requires**: Comma-separated list of dependencies
- **files**: Comma-separated list of `filename:type` pairs
  - Types: `hook`, `script`, `config`, `doc`
  - Order matters (matches checksums order)
- **base_url**: Base URL for curl downloads (usually GitHub raw)
- **checksums**: Optional SHA256 checksums for file integrity

**Example .meta files:**

<details>
<summary>Simple hook application</summary>

```ini
name=tw-simple
version=1.0.0
description=Simple task modification hook
requires=python3
files=on-modify_simple.py:hook
base_url=https://raw.githubusercontent.com/user/tw-simple/main/
```
</details>

<details>
<summary>Complex multi-file application</summary>

```ini
name=tw-recurrence
version=2.0.0
description=Enhanced recurrence system with chained and periodic modes
requires=python3,taskwarrior>=2.6.2
files=on-add_recurrence.py:hook,on-modify_recurrence.py:hook,on-exit_recurrence.py:hook,recurrence.rc:config,README.md:doc
base_url=https://raw.githubusercontent.com/linuxcaffe/tw-recurrence_overhaul-hook/main/
checksums=
```
</details>

### Creating a .install Script

The `.install` script is a self-contained bash script that handles installation and removal.

**Template Structure:**

```bash
#!/usr/bin/env bash
#
# myapp.install - Installer for myapp
# Can be run standalone or via tw.py

set -euo pipefail

# === CONFIGURATION ===

APP_NAME="myapp"
APP_VERSION="1.0.0"
BASE_URL="https://raw.githubusercontent.com/user/myapp/main"

# === OPTIONAL HELPER SOURCING ===

if [[ -f ~/.task/lib/tw-common.sh ]]; then
    source ~/.task/lib/tw-common.sh
else
    # Fallback: Define minimal functions inline
    tw_msg() { echo "[INFO] $*"; }
    tw_success() { echo "[SUCCESS] $*"; }
    tw_error() { echo "[ERROR] $*" >&2; }
    tw_die() { tw_error "$@"; exit 1; }
fi

# === ENVIRONMENT DETECTION ===

: ${HOOKS_DIR:=~/.task/hooks}
: ${SCRIPTS_DIR:=~/.task/scripts}
: ${CONFIG_DIR:=~/.task/config}
: ${DOCS_DIR:=~/.task/docs}
: ${TASKRC:=~/.taskrc}

# === REQUIREMENTS CHECK ===

check_requirements() {
    tw_msg "Checking requirements..."
    
    # Check for required commands
    if ! command -v curl &>/dev/null; then
        tw_die "curl is required but not found"
    fi
    
    # Optional: Use version checks if available
    if type tw_check_taskwarrior_version &>/dev/null; then
        tw_check_taskwarrior_version "2.6.0" || return 1
    fi
    
    tw_success "Requirements met"
    return 0
}

# === INSTALL FUNCTION ===

install() {
    tw_msg "Installing $APP_NAME v$APP_VERSION..."
    
    # Check requirements
    check_requirements || return 1
    
    # Create directories
    mkdir -p "$HOOKS_DIR" "$CONFIG_DIR" "$DOCS_DIR"
    
    # Download files
    download_files || return 1
    
    # Make hooks executable
    chmod +x "$HOOKS_DIR"/on-*_$APP_NAME.py
    
    # Configure Taskwarrior
    configure_taskwarrior || return 1
    
    tw_success "Installed $APP_NAME v$APP_VERSION"
    return 0
}

download_files() {
    # Use tw_curl_and_place if available, else basic curl
    if type tw_curl_and_place &>/dev/null; then
        tw_curl_and_place "$BASE_URL/on-add.py" "$HOOKS_DIR" "on-add_$APP_NAME.py" || return 1
        tw_curl_and_place "$BASE_URL/myapp.rc" "$CONFIG_DIR" || return 1
        tw_curl_and_place "$BASE_URL/README.md" "$DOCS_DIR" "${APP_NAME}_README.md" || return 1
    else
        curl -fsSL "$BASE_URL/on-add.py" -o "$HOOKS_DIR/on-add_$APP_NAME.py" || return 1
        curl -fsSL "$BASE_URL/myapp.rc" -o "$CONFIG_DIR/myapp.rc" || return 1
        curl -fsSL "$BASE_URL/README.md" -o "$DOCS_DIR/${APP_NAME}_README.md" || return 1
    fi
    
    return 0
}

configure_taskwarrior() {
    local config_line="include $CONFIG_DIR/myapp.rc"
    
    # Use tw_add_config if available, else manual add
    if type tw_add_config &>/dev/null; then
        tw_add_config "$config_line" || return 1
    else
        if ! grep -Fxq "$config_line" "$TASKRC"; then
            echo "$config_line" >> "$TASKRC"
            tw_msg "Added config to .taskrc"
        fi
    fi
    
    return 0
}

# === REMOVE FUNCTION ===

remove() {
    tw_msg "Removing $APP_NAME..."
    
    # Remove files
    rm -f "$HOOKS_DIR/on-add_$APP_NAME.py"
    rm -f "$CONFIG_DIR/myapp.rc"
    rm -f "$DOCS_DIR/${APP_NAME}_README.md"
    
    # Remove config from .taskrc
    local config_line="include $CONFIG_DIR/myapp.rc"
    
    if type tw_remove_config &>/dev/null; then
        tw_remove_config "$config_line"
    else
        if [[ -f "$TASKRC" ]]; then
            grep -Fxv "$config_line" "$TASKRC" > "$TASKRC.tmp" 2>/dev/null || true
            mv "$TASKRC.tmp" "$TASKRC"
        fi
    fi
    
    tw_success "Removed $APP_NAME"
    return 0
}

# === MAIN DISPATCHER ===

case "${1:-}" in
    install)
        install
        ;;
    remove|uninstall)
        remove
        ;;
    *)
        echo "Usage: $0 {install|remove}"
        exit 1
        ;;
esac
```

### Key Implementation Patterns

#### 1. Environment Detection

Always provide defaults for directory variables:

```bash
: ${HOOKS_DIR:=~/.task/hooks}
: ${SCRIPTS_DIR:=~/.task/scripts}
: ${CONFIG_DIR:=~/.task/config}
: ${DOCS_DIR:=~/.task/docs}
: ${TASKRC:=~/.taskrc}
```

#### 2. Graceful Degradation

Support operation with or without tw-common.sh:

```bash
if type tw_curl_and_place &>/dev/null; then
    # Use helper if available
    tw_curl_and_place "$URL" "$TARGET_DIR" "$FILENAME"
else
    # Fallback to basic curl
    curl -fsSL "$URL" -o "$TARGET_DIR/$FILENAME"
fi
```

#### 3. Symlink Creation (when needed)

Some apps need symlinks (e.g., when on-add and on-modify are the same file):

```bash
# Create symlink within same directory
ln -sf "on-modify_$APP_NAME.py" "$HOOKS_DIR/on-add_$APP_NAME.py"
```

#### 4. README Renaming

Rename README.md to avoid conflicts:

```bash
# Download as appname_README.md
curl -fsSL "$BASE_URL/README.md" -o "$DOCS_DIR/${APP_NAME}_README.md"
```

#### 5. Configuration Management

Add/remove includes from .taskrc:

```bash
# Add (avoid duplicates)
config_line="include $CONFIG_DIR/myapp.rc"
if ! grep -Fxq "$config_line" "$TASKRC"; then
    echo "$config_line" >> "$TASKRC"
fi

# Remove (exact match)
grep -Fxv "$config_line" "$TASKRC" > "$TASKRC.tmp"
mv "$TASKRC.tmp" "$TASKRC"
```

## Integration with awesome-taskwarrior

### Registry Structure

Place your `.meta` file in `awesome-taskwarrior/registry.d/`:

```
awesome-taskwarrior/
├── registry.d/
│   ├── tw-myapp.meta
│   ├── tw-recurrence.meta
│   └── tw-another.meta
└── installers/
    ├── tw-myapp.install
    ├── tw-recurrence.install
    └── tw-another.install
```

### Installation Flow

When a user runs `tw.py install myapp`:

1. **tw.py** reads `registry.d/myapp.meta`
2. **tw.py** sets environment variables (`HOOKS_DIR`, etc.)
3. **tw.py** runs `bash installers/myapp.install install`
4. **Installer** downloads files using curl
5. **Installer** places files in appropriate directories
6. **Installer** configures .taskrc
7. **tw.py** updates manifest with installed files

### Manifest Tracking

tw.py maintains `~/.task/.tw_manifest` with per-file tracking:

```
myapp|1.0.0|/home/user/.task/hooks/on-add_myapp.py|abc123...|2026-01-22T14:30:00
myapp|1.0.0|/home/user/.task/config/myapp.rc|def456...|2026-01-22T14:30:00
myapp|1.0.0|/home/user/.task/docs/myapp_README.md||2026-01-22T14:30:00
```

Format: `app|version|file|checksum|date`

## Testing Your Application

### Standalone Testing

Test your installer independently first:

```bash
# Set test environment
export HOOKS_DIR=/tmp/test-task/hooks
export CONFIG_DIR=/tmp/test-task/config
export DOCS_DIR=/tmp/test-task/docs
export TASKRC=/tmp/test-task/.taskrc

# Create test structure
mkdir -p /tmp/test-task/{hooks,config,docs}
touch /tmp/test-task/.taskrc

# Test installation
bash myapp.install install

# Verify files were created
ls -la $HOOKS_DIR
ls -la $CONFIG_DIR
cat $TASKRC

# Test removal
bash myapp.install remove

# Clean up
rm -rf /tmp/test-task
```

### Testing with tw.py

After standalone testing works:

```bash
# Copy files to awesome-taskwarrior
cp myapp.meta awesome-taskwarrior/registry.d/
cp myapp.install awesome-taskwarrior/installers/

# Test with tw.py
cd awesome-taskwarrior
./tw.py install myapp
./tw.py info myapp
./tw.py verify myapp
./tw.py remove myapp
```

### Test Checklist

- [ ] Installer works standalone (no tw.py)
- [ ] All files downloaded correctly
- [ ] Files placed in correct directories
- [ ] Hooks are executable
- [ ] Configuration added to .taskrc
- [ ] README renamed appropriately
- [ ] Removal cleans up all files
- [ ] Removal removes .taskrc includes
- [ ] Works with tw.py
- [ ] Manifest tracking accurate

## Generating Checksums

Generate SHA256 checksums for your files:

```bash
# Generate checksums
sha256sum on-add_myapp.py on-modify_myapp.py myapp.rc README.md

# Format for .meta file (remove filenames, add sha256: prefix)
checksums=sha256:abc123...,sha256:def456...,sha256:789xyz...,sha256:012uvw...
```

Or use a helper script:

```bash
#!/bin/bash
# generate-checksums.sh

files=("on-add_myapp.py" "myapp.rc" "README.md")
checksums=""

for file in "${files[@]}"; do
    sum=$(sha256sum "$file" | cut -d' ' -f1)
    if [[ -n "$checksums" ]]; then
        checksums+=","
    fi
    checksums+="sha256:$sum"
done

echo "checksums=$checksums"
```

## Best Practices

### 1. Naming Conventions

- **Hooks**: `on-{event}_{appname}.py` (e.g., `on-add_recurrence.py`)
- **Scripts**: `{appname}` or `{appname}-{function}` (e.g., `nicedates`)
- **Configs**: `{appname}.rc` (e.g., `recurrence.rc`)
- **Docs**: `{appname}_README.md` (auto-renamed from `README.md`)

### 2. File Organization

Keep installed files minimal:
- ✅ Include: hooks, scripts, configs, README
- ❌ Exclude: tests, development docs, .git, build files

### 3. Error Handling

Always check return codes:

```bash
download_files() {
    curl -fsSL "$URL" -o "$TARGET" || {
        tw_error "Failed to download: $URL"
        return 1
    }
    return 0
}
```

### 4. Idempotence

Make operations idempotent (safe to run multiple times):

```bash
# Check before adding to .taskrc
if ! grep -Fxq "$config_line" "$TASKRC"; then
    echo "$config_line" >> "$TASKRC"
fi
```

### 5. Clean Uninstall

Remove everything that was installed:

```bash
remove() {
    # Remove all files
    rm -f "$HOOKS_DIR/on-add_$APP_NAME.py"
    rm -f "$HOOKS_DIR/on-modify_$APP_NAME.py"
    rm -f "$CONFIG_DIR/$APP_NAME.rc"
    rm -f "$DOCS_DIR/${APP_NAME}_README.md"
    
    # Remove symlinks if created
    rm -f "$HOOKS_DIR/on-exit_$APP_NAME.py"
    
    # Remove config
    tw_remove_config "include $CONFIG_DIR/$APP_NAME.rc"
}
```

### 6. Documentation

Document your installer's behavior:

```bash
#!/usr/bin/env bash
#
# myapp.install - Installer for myapp
#
# USAGE:
#   bash myapp.install install   - Install myapp
#   bash myapp.install remove    - Remove myapp
#
# ENVIRONMENT:
#   HOOKS_DIR    - Target directory for hooks (default: ~/.task/hooks)
#   CONFIG_DIR   - Target directory for configs (default: ~/.task/config)
#   DOCS_DIR     - Target directory for docs (default: ~/.task/docs)
#   TASKRC       - Taskwarrior config file (default: ~/.taskrc)
#
# DEPENDENCIES:
#   - curl (required)
#   - taskwarrior >= 2.6.0 (required)
#   - python3 >= 3.6 (required)
```

## Troubleshooting

### Installer Doesn't Work Standalone

**Problem**: Installer fails when run directly

**Solution**: Check for hard dependencies on tw.py or tw-common.sh. Use fallbacks:

```bash
if type tw_msg &>/dev/null; then
    tw_msg "Message"
else
    echo "[INFO] Message"
fi
```

### Files Not Found After Installation

**Problem**: Files not in expected locations

**Solution**: Verify environment variables are set correctly:

```bash
echo "HOOKS_DIR: $HOOKS_DIR"
echo "CONFIG_DIR: $CONFIG_DIR"
ls -la "$HOOKS_DIR"
```

### Hooks Not Executable

**Problem**: Taskwarrior doesn't run hooks

**Solution**: Ensure chmod +x is applied:

```bash
chmod +x "$HOOKS_DIR"/on-*_myapp.py
```

### Duplicate .taskrc Entries

**Problem**: Multiple includes added to .taskrc

**Solution**: Check before adding:

```bash
if ! grep -Fxq "$config_line" "$TASKRC"; then
    echo "$config_line" >> "$TASKRC"
fi
```

## Future Tools

### make-awesome-installer.py (Planned)

A future tool will automate installer creation:

```bash
# Generate installer from template
make-awesome-installer.py \
    --name myapp \
    --version 1.0.0 \
    --repo https://github.com/user/myapp \
    --files "on-add.py:hook,myapp.rc:config,README.md:doc"

# Creates myapp.install and myapp.meta
```

This tool will:
- Use templates from `dev/models/`
- Generate checksums automatically
- Validate installer independence
- Create test suite stubs

## See Also

- [API.md](API.md) - tw-common.sh utility functions
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [MIGRATION.md](MIGRATION.md) - Migrating from v1.3.0
- Templates: `dev/models/hook-template.install`, `dev/models/wrapper-template.install`
